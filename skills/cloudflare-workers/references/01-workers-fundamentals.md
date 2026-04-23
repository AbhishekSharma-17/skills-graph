# Cloudflare Workers — Fundamentals

> Source: [developers.cloudflare.com/workers/runtime-apis](https://developers.cloudflare.com/workers/runtime-apis/)

## Table of Contents

- [Worker Entry Point](#worker-entry-point)
- [Fetch Handler](#fetch-handler)
- [Request Object](#request-object)
- [Response Object](#response-object)
- [ExecutionContext](#executioncontext)
- [Environment Bindings](#environment-bindings)
- [Routing Patterns](#routing-patterns)
- [Headers and CORS](#headers-and-cors)
- [Streaming Responses](#streaming-responses)
- [Scheduled Handler](#scheduled-handler)
- [Email Handler](#email-handler)
- [Common Patterns](#common-patterns)

## Worker Entry Point

Workers use the ES modules syntax with a default export:

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return new Response("Hello!");
  },
} satisfies ExportedHandler<Env>;
```

The `ExportedHandler` interface supports multiple event handlers:

```typescript
interface ExportedHandler<Env> {
  fetch?(request: Request, env: Env, ctx: ExecutionContext): Response | Promise<Response>;
  scheduled?(controller: ScheduledController, env: Env, ctx: ExecutionContext): void | Promise<void>;
  queue?(batch: MessageBatch, env: Env, ctx: ExecutionContext): void | Promise<void>;
  email?(message: EmailMessage, env: Env, ctx: ExecutionContext): void | Promise<void>;
  tail?(events: TraceItem[], env: Env, ctx: ExecutionContext): void | Promise<void>;
}
```

## Fetch Handler

The primary handler for HTTP requests:

```typescript
async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
  const url = new URL(request.url);

  if (url.pathname === "/api/health") {
    return Response.json({ status: "ok" });
  }

  if (request.method === "POST" && url.pathname === "/api/data") {
    const body = await request.json<{ name: string }>();
    return Response.json({ received: body.name });
  }

  return new Response("Not Found", { status: 404 });
}
```

## Request Object

Workers use the standard Web API `Request` with Cloudflare-specific extensions:

```typescript
// Standard properties
request.method              // "GET", "POST", etc.
request.url                 // Full URL string
request.headers             // Headers object
request.body                // ReadableStream | null
request.bodyUsed            // boolean

// Body parsing
const text = await request.text();
const json = await request.json();
const form = await request.formData();
const buffer = await request.arrayBuffer();
const blob = await request.blob();

// Cloudflare-specific (request.cf)
request.cf?.country         // "US", "GB", etc.
request.cf?.city            // "San Francisco"
request.cf?.continent       // "NA"
request.cf?.latitude        // "37.7749"
request.cf?.longitude       // "-122.4194"
request.cf?.region          // "California"
request.cf?.timezone        // "America/Los_Angeles"
request.cf?.postalCode      // "94107"
request.cf?.asn             // 13335
request.cf?.colo            // "SFO" — datacenter code
request.cf?.httpProtocol    // "HTTP/2"
request.cf?.tlsVersion      // "TLSv1.3"
request.cf?.tlsCipher       // cipher suite
request.cf?.botManagement   // Bot detection data (Enterprise)
```

## Response Object

Standard Web API `Response` with helpers:

```typescript
// Basic responses
new Response("Hello");                                       // 200 text
new Response(null, { status: 204 });                         // No content
new Response("Not Found", { status: 404 });                  // Error
new Response(readableStream);                                // Streaming body

// JSON helper
Response.json({ key: "value" });                             // Content-Type auto-set
Response.json({ error: "bad" }, { status: 400 });            // JSON with status

// Redirect
Response.redirect("https://example.com", 301);               // Permanent redirect
Response.redirect("https://example.com", 302);               // Temporary redirect

// Custom headers
new Response("OK", {
  headers: {
    "Content-Type": "text/html",
    "Cache-Control": "public, max-age=3600",
    "X-Custom": "value",
  },
});
```

## ExecutionContext

The `ctx` parameter provides lifecycle management:

```typescript
export default {
  async fetch(request, env, ctx) {
    // waitUntil — run async work after response is sent
    ctx.waitUntil(logToAnalytics(request));

    // passThroughOnException — if Worker throws, forward to origin
    ctx.passThroughOnException();

    return new Response("OK");
  },
};
```

`ctx.waitUntil(promise)` keeps the Worker alive to complete background work (logging, analytics, cache writes) without blocking the response.

## Environment Bindings

All bindings are accessed via the `env` parameter. Define them in your `Env` interface:

```typescript
interface Env {
  // Variables
  API_KEY: string;

  // KV Namespace
  MY_KV: KVNamespace;

  // D1 Database
  DB: D1Database;

  // R2 Bucket
  ASSETS: R2Bucket;

  // Durable Object
  COUNTER: DurableObjectNamespace;

  // Queue
  MY_QUEUE: Queue;

  // Service Binding
  AUTH_SERVICE: Service;

  // Workers AI
  AI: Ai;

  // Secrets (same as variables at runtime)
  JWT_SECRET: string;
}
```

## Routing Patterns

### URL-Based Router

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // Static routes
    if (path === "/") return new Response("Home");
    if (path === "/about") return new Response("About");

    // Pattern matching with regex
    const userMatch = path.match(/^\/users\/(\d+)$/);
    if (userMatch) {
      const userId = userMatch[1];
      return Response.json({ userId });
    }

    // Method + path routing
    if (request.method === "POST" && path === "/api/items") {
      const body = await request.json();
      return Response.json({ created: true });
    }

    return new Response("Not Found", { status: 404 });
  },
};
```

### Using Hono (Recommended for Complex Routing)

```typescript
import { Hono } from "hono";

type Bindings = { DB: D1Database; MY_KV: KVNamespace };
const app = new Hono<{ Bindings: Bindings }>();

app.get("/", (c) => c.text("Hello Hono!"));
app.get("/users/:id", (c) => {
  const id = c.req.param("id");
  return c.json({ id });
});
app.post("/api/items", async (c) => {
  const body = await c.req.json();
  return c.json({ created: true }, 201);
});

export default app;
```

## Headers and CORS

```typescript
function corsHeaders(origin: string = "*"): Headers {
  return new Headers({
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    const response = await handleRequest(request, env);
    const headers = corsHeaders();
    for (const [key, value] of response.headers) {
      headers.set(key, value);
    }
    return new Response(response.body, { ...response, headers });
  },
};
```

## Streaming Responses

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();

    (async () => {
      for (let i = 0; i < 10; i++) {
        await writer.write(encoder.encode(`Chunk ${i}\n`));
        await new Promise((r) => setTimeout(r, 100));
      }
      await writer.close();
    })();

    return new Response(readable, {
      headers: { "Content-Type": "text/plain" },
    });
  },
};
```

## Scheduled Handler

Cron-triggered Workers (no HTTP request):

```typescript
export default {
  async scheduled(
    controller: ScheduledController,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<void> {
    ctx.waitUntil(doCleanup(env));
  },
};

// wrangler.toml
// [triggers]
// crons = ["0 * * * *", "*/5 * * * *"]
```

`controller.scheduledTime` is the epoch ms of the trigger, `controller.cron` is the cron expression.

## Email Handler

Process incoming emails:

```typescript
export default {
  async email(message: EmailMessage, env: Env, ctx: ExecutionContext) {
    const { from, to } = message;
    const rawEmail = await new Response(message.raw).text();

    if (to === "support@example.com") {
      await message.forward("team@example.com");
    }
  },
};
```

## Common Patterns

### Subrequest to External API

```typescript
const response = await fetch("https://api.example.com/data", {
  headers: { Authorization: `Bearer ${env.API_KEY}` },
});
const data = await response.json();
```

### Cache API

```typescript
const cache = caches.default;
const cacheKey = new Request(request.url, request);
let response = await cache.match(cacheKey);

if (!response) {
  response = await fetch(request);
  response = new Response(response.body, response);
  response.headers.set("Cache-Control", "s-maxage=3600");
  ctx.waitUntil(cache.put(cacheKey, response.clone()));
}
return response;
```

### Error Handling Pattern

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    try {
      return await handleRequest(request, env, ctx);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      return Response.json({ error: message }, { status: 500 });
    }
  },
};
```
