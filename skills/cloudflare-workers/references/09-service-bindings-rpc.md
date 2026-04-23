# Cloudflare Workers — Service Bindings & RPC

> Source: [developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings](https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/)

## Table of Contents

- [What Are Service Bindings](#what-are-service-bindings)
- [Basic Service Bindings](#basic-service-bindings)
- [RPC with WorkerEntrypoint](#rpc-with-workerentrypoint)
- [Named Entrypoints](#named-entrypoints)
- [Durable Objects as RPC](#durable-objects-as-rpc)
- [RPC Type Safety](#rpc-type-safety)
- [Lifecycle and Stubs](#lifecycle-and-stubs)
- [Common Patterns](#common-patterns)

## What Are Service Bindings

Service bindings allow Workers to call each other **without going through the public internet**. Communication happens entirely within Cloudflare's network — zero latency overhead, no public URL needed.

**Best for:** Microservices, shared authentication, internal APIs, multi-service architectures.

Two modes:
1. **HTTP-style** — One Worker calls another's `fetch()` handler
2. **RPC** — One Worker calls another's methods directly (recommended)

## Basic Service Bindings

### HTTP-Style (Legacy)

```toml
# wrangler.toml (caller Worker)
[[services]]
binding = "AUTH_SERVICE"
service = "auth-worker"
```

```typescript
// Caller Worker
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Calls auth-worker's fetch() handler
    const authResponse = await env.AUTH_SERVICE.fetch(
      new Request("https://internal/verify", {
        method: "POST",
        headers: { Authorization: request.headers.get("Authorization")! },
      }),
    );

    if (!authResponse.ok) {
      return new Response("Unauthorized", { status: 401 });
    }

    return new Response("Authenticated!");
  },
};
```

The URL hostname in `fetch()` calls via service bindings is ignored — it always routes to the bound Worker.

## RPC with WorkerEntrypoint

The recommended approach — call methods directly instead of crafting HTTP requests:

### Target Worker (Callee)

```typescript
// auth-worker/src/index.ts
import { WorkerEntrypoint } from "cloudflare:workers";

export default class extends WorkerEntrypoint {
  async fetch(request: Request): Promise<Response> {
    return new Response("Auth Service");
  }

  // RPC methods — callable from other Workers
  async verifyToken(token: string): Promise<{ userId: string; role: string } | null> {
    try {
      const payload = await this.env.JWT.verify(token);
      return { userId: payload.sub, role: payload.role };
    } catch {
      return null;
    }
  }

  async createUser(email: string, name: string): Promise<{ id: string }> {
    const result = await this.env.DB.prepare(
      "INSERT INTO users (email, name) VALUES (?, ?) RETURNING id",
    ).bind(email, name).first();
    return result as { id: string };
  }

  async hasPermission(userId: string, permission: string): Promise<boolean> {
    const result = await this.env.DB.prepare(
      "SELECT 1 FROM permissions WHERE user_id = ? AND permission = ?",
    ).bind(userId, permission).first();
    return result !== null;
  }
}
```

### Caller Worker

```toml
# wrangler.toml
[[services]]
binding = "AUTH"
service = "auth-worker"
```

```typescript
// api-worker/src/index.ts
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const token = request.headers.get("Authorization")?.replace("Bearer ", "");
    if (!token) return new Response("Unauthorized", { status: 401 });

    // Direct RPC call — no HTTP, no serialization overhead
    const user = await env.AUTH.verifyToken(token);
    if (!user) return new Response("Invalid token", { status: 401 });

    const canWrite = await env.AUTH.hasPermission(user.userId, "write");
    if (!canWrite) return new Response("Forbidden", { status: 403 });

    return Response.json({ user });
  },
};
```

### WorkerEntrypoint Properties

```typescript
import { WorkerEntrypoint } from "cloudflare:workers";

export default class extends WorkerEntrypoint {
  // Available properties:
  // this.env  — Bindings (same as env parameter in fetch)
  // this.ctx  — ExecutionContext (waitUntil, etc.)

  async doWork() {
    // Access bindings
    const db = this.env.DB;
    const kv = this.env.MY_KV;

    // Background work
    this.ctx.waitUntil(this.logEvent("work_done"));
  }
}
```

## Named Entrypoints

Export multiple entrypoints from a single Worker for role-based access:

### Target Worker

```typescript
import { WorkerEntrypoint } from "cloudflare:workers";

// Default entrypoint (handles fetch + general RPC)
export default class extends WorkerEntrypoint {
  async fetch() {
    return new Response("API Service");
  }

  async getPublicData() {
    return { version: "1.0" };
  }
}

// Admin entrypoint — only bound by authorized Workers
export class AdminEntrypoint extends WorkerEntrypoint {
  async createUser(email: string, role: string) {
    return this.env.DB.prepare("INSERT INTO users (email, role) VALUES (?, ?) RETURNING *")
      .bind(email, role)
      .first();
  }

  async deleteUser(id: number) {
    await this.env.DB.prepare("DELETE FROM users WHERE id = ?").bind(id).run();
  }
}

// Readonly entrypoint — safe for public-facing Workers
export class ReadonlyEntrypoint extends WorkerEntrypoint {
  async getUser(id: number) {
    return this.env.DB.prepare("SELECT id, name, email FROM users WHERE id = ?")
      .bind(id)
      .first();
  }

  async listUsers(limit: number = 50) {
    return (await this.env.DB.prepare("SELECT id, name FROM users LIMIT ?")
      .bind(limit)
      .all()).results;
  }
}
```

### Binding to Named Entrypoints

```toml
# admin-dashboard/wrangler.toml — gets admin access
[[services]]
binding = "API_ADMIN"
service = "api-worker"
entrypoint = "AdminEntrypoint"

# public-site/wrangler.toml — gets read-only access
[[services]]
binding = "API"
service = "api-worker"
entrypoint = "ReadonlyEntrypoint"
```

```typescript
// admin-dashboard
const user = await env.API_ADMIN.createUser("alice@example.com", "admin");

// public-site (can only read)
const user = await env.API.getUser(123);
```

## Durable Objects as RPC

Durable Objects also support RPC (they extend `DurableObject` which works like `WorkerEntrypoint`):

```typescript
import { DurableObject } from "cloudflare:workers";

export class Counter extends DurableObject {
  private count = 0;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    ctx.blockConcurrencyWhile(async () => {
      this.count = (await ctx.storage.get<number>("count")) ?? 0;
    });
  }

  // RPC methods — called from any Worker with the binding
  async increment(): Promise<number> {
    this.count++;
    await this.ctx.storage.put("count", this.count);
    return this.count;
  }

  async getCount(): Promise<number> {
    return this.count;
  }
}

// Caller
const id = env.COUNTER.idFromName("global");
const stub = env.COUNTER.get(id);
const count = await stub.increment();  // RPC call
```

## RPC Type Safety

Share types between Workers for full type safety:

```typescript
// shared-types/index.ts (shared package or path import)
export interface AuthRPC {
  verifyToken(token: string): Promise<{ userId: string; role: string } | null>;
  hasPermission(userId: string, permission: string): Promise<boolean>;
}

// auth-worker — implements the interface
export default class extends WorkerEntrypoint implements AuthRPC {
  async verifyToken(token: string) { /* ... */ }
  async hasPermission(userId: string, permission: string) { /* ... */ }
}

// caller — types the binding
interface Env {
  AUTH: Service<AuthRPC>;
}
```

## Lifecycle and Stubs

- A new `WorkerEntrypoint` instance is created per RPC call
- Instances are stateless — they exist only for the call duration
- Multiple RPC calls to the same binding may create multiple instances
- `this.ctx.waitUntil()` extends the instance lifetime for background work
- Durable Object stubs persist as long as the caller holds a reference

## Common Patterns

### API Gateway

```typescript
// gateway-worker
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Route to different backend services
    if (url.pathname.startsWith("/api/users")) {
      return env.USER_SERVICE.fetch(request);
    }
    if (url.pathname.startsWith("/api/orders")) {
      return env.ORDER_SERVICE.fetch(request);
    }
    if (url.pathname.startsWith("/api/ai")) {
      return env.AI_SERVICE.fetch(request);
    }

    return new Response("Not Found", { status: 404 });
  },
};
```

### Shared Auth Middleware

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const token = request.headers.get("Authorization")?.slice(7);
    if (!token) return Response.json({ error: "Missing token" }, { status: 401 });

    const user = await env.AUTH.verifyToken(token);
    if (!user) return Response.json({ error: "Invalid token" }, { status: 401 });

    // Attach user to request via headers for downstream services
    const authedRequest = new Request(request);
    authedRequest.headers.set("X-User-Id", user.userId);
    authedRequest.headers.set("X-User-Role", user.role);

    return env.BACKEND.fetch(authedRequest);
  },
};
```

## Common Pitfalls

- **New instance per call** — `WorkerEntrypoint` instances are ephemeral. Don't store state in instance variables between calls.
- **No public URL needed** — The target Worker doesn't need a route or custom domain to be called via service bindings.
- **Same account only** — Service bindings work within the same Cloudflare account by default.
- **Serialization** — RPC parameters and return values must be serializable (structured clone algorithm). Functions, classes, and symbols can't be passed.
- **Named entrypoints** — Must be explicitly exported as named classes extending `WorkerEntrypoint`. Regular function exports don't work.
