# Cloudflare Durable Objects — Stateful Edge Compute

> Source: [developers.cloudflare.com/durable-objects](https://developers.cloudflare.com/durable-objects/)

## Table of Contents

- [What Are Durable Objects](#what-are-durable-objects)
- [Setup and Configuration](#setup-and-configuration)
- [Durable Object Class](#durable-object-class)
- [Calling Durable Objects](#calling-durable-objects)
- [Storage API — Key-Value](#storage-api--key-value)
- [Storage API — SQL (SQLite)](#storage-api--sql-sqlite)
- [Alarms](#alarms)
- [WebSocket Hibernation](#websocket-hibernation)
- [Lifecycle and Concurrency](#lifecycle-and-concurrency)
- [Limits and Pricing](#limits-and-pricing)
- [Common Patterns](#common-patterns)

## What Are Durable Objects

Durable Objects provide **stateful, single-threaded compute** at the edge. Each Durable Object instance has:

- A globally unique ID
- Private persistent storage (KV or SQLite)
- Single-threaded execution (no race conditions)
- A lifecycle tied to activity (evicted when idle)

**Best for:** Counters, rate limiters, chat rooms, collaborative editing, WebSocket servers, game state, leader election.

## Setup and Configuration

```toml
# wrangler.toml
[durable_objects]
bindings = [
  { name = "COUNTER", class_name = "Counter" },
]

# Migration (required on first deploy)
[[migrations]]
tag = "v1"
new_sqlite_classes = ["Counter"]   # SQLite-backed (recommended)
# OR: new_classes = ["Counter"]    # KV-backed (legacy)
```

```typescript
interface Env {
  COUNTER: DurableObjectNamespace;
}
```

## Durable Object Class

```typescript
import { DurableObject } from "cloudflare:workers";

export class Counter extends DurableObject {
  private count: number = 0;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
  }

  async initialize() {
    this.count = (await this.ctx.storage.get<number>("count")) ?? 0;
  }

  async increment(): Promise<number> {
    this.count++;
    await this.ctx.storage.put("count", this.count);
    return this.count;
  }

  async getCount(): Promise<number> {
    return this.count;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/increment") {
      const newCount = await this.increment();
      return Response.json({ count: newCount });
    }

    return Response.json({ count: this.count });
  }
}
```

The class extends `DurableObject` (from `cloudflare:workers`) and receives `ctx` (DurableObjectState) and `env` in the constructor.

## Calling Durable Objects

### From a Worker (via RPC — Recommended)

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Get a DO stub by name (deterministic ID)
    const id = env.COUNTER.idFromName("global-counter");
    const stub = env.COUNTER.get(id);

    // Call RPC methods directly
    const count = await stub.increment();
    return Response.json({ count });
  },
};
```

### ID Generation

```typescript
// From a name (deterministic — same name = same DO)
const id = env.COUNTER.idFromName("user:123");

// Generate unique ID
const id = env.COUNTER.newUniqueId();

// From string (restore a previously generated ID)
const id = env.COUNTER.idFromString("abc123...");
```

### Location Hints

```typescript
// Suggest where the DO should run (nearest to user)
const id = env.COUNTER.newUniqueId({ jurisdiction: "eu" });
const stub = env.COUNTER.get(id, { locationHint: "weur" });
```

## Storage API — Key-Value

The async KV storage API works on both SQLite and KV-backed Durable Objects:

```typescript
// Read
const value = await this.ctx.storage.get<string>("key");
const values = await this.ctx.storage.get<string>(["key1", "key2"]); // Map

// Write
await this.ctx.storage.put("key", "value");
await this.ctx.storage.put({ key1: "val1", key2: "val2" }); // Batch

// Delete
await this.ctx.storage.delete("key");
await this.ctx.storage.delete(["key1", "key2"]); // Returns count deleted

// List
const allData = await this.ctx.storage.list(); // Map<string, unknown>
const prefixed = await this.ctx.storage.list({ prefix: "user:" });
const ranged = await this.ctx.storage.list({
  start: "a",
  end: "z",
  limit: 100,
  reverse: true,
});

// Delete everything
await this.ctx.storage.deleteAll();

// Transaction (KV-backed)
await this.ctx.storage.transaction(async (txn) => {
  const val = await txn.get<number>("counter");
  await txn.put("counter", (val ?? 0) + 1);
});
```

### Storage Options

```typescript
// Performance options (trade durability for speed)
await this.ctx.storage.put("key", "val", {
  allowUnconfirmed: true,   // Don't wait for disk confirmation
  noCache: true,            // Don't cache in memory
});

await this.ctx.storage.get("key", {
  allowConcurrency: true,   // Allow concurrent reads
  noCache: true,
});
```

## Storage API — SQL (SQLite)

SQLite-backed DOs have direct SQL access via `this.ctx.storage.sql`:

```typescript
export class UserStore extends DurableObject {
  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    // Create tables in constructor
    this.ctx.storage.sql.exec(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
      )
    `);
  }

  async addUser(name: string, email: string) {
    return this.ctx.storage.sql
      .exec("INSERT INTO users (name, email) VALUES (?, ?) RETURNING *", name, email)
      .one();
  }

  async getUser(id: number) {
    return this.ctx.storage.sql
      .exec("SELECT * FROM users WHERE id = ?", id)
      .one();
  }

  async listUsers() {
    return this.ctx.storage.sql
      .exec("SELECT * FROM users ORDER BY name")
      .toArray();
  }
}
```

### SqlStorageCursor Methods

```typescript
const cursor = this.ctx.storage.sql.exec("SELECT * FROM users");

cursor.toArray();       // All rows as objects
cursor.one();           // Exactly one row (throws if 0 or >1)
cursor.raw();           // Rows as arrays instead of objects
cursor.columnNames;     // Column name strings
cursor.rowsRead;        // Billing: rows scanned
cursor.rowsWritten;     // Billing: rows modified
```

### Synchronous Transactions

```typescript
this.ctx.storage.transactionSync(() => {
  this.ctx.storage.sql.exec("UPDATE accounts SET balance = balance - ? WHERE id = ?", 100, 1);
  this.ctx.storage.sql.exec("UPDATE accounts SET balance = balance + ? WHERE id = ?", 100, 2);
});
```

## Alarms

Schedule a callback for future execution:

```typescript
export class ReminderDO extends DurableObject {
  async setReminder(delayMs: number) {
    await this.ctx.storage.setAlarm(Date.now() + delayMs);
  }

  async alarm() {
    // Called when the alarm fires
    console.log("Alarm triggered!");
    await this.doWork();

    // Optionally set next alarm for recurring work
    await this.ctx.storage.setAlarm(Date.now() + 60_000);
  }

  async cancelReminder() {
    await this.ctx.storage.deleteAlarm();
  }
}
```

Only one alarm per DO at a time. Setting a new alarm replaces the existing one.

## WebSocket Hibernation

Efficiently handle thousands of WebSocket connections with minimal memory:

```typescript
export class ChatRoom extends DurableObject {
  async fetch(request: Request): Promise<Response> {
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);

    // Accept with hibernation + tags
    this.ctx.acceptWebSocket(server, ["user:123"]);

    return new Response(null, { status: 101, webSocket: client });
  }

  // Called when a hibernated DO receives a message
  async webSocketMessage(ws: WebSocket, message: string | ArrayBuffer) {
    const data = JSON.parse(message as string);

    // Broadcast to all connected clients
    for (const client of this.ctx.getWebSockets()) {
      if (client !== ws) {
        client.send(JSON.stringify(data));
      }
    }
  }

  async webSocketClose(ws: WebSocket, code: number, reason: string, wasClean: boolean) {
    ws.close(code, reason);
  }

  async webSocketError(ws: WebSocket, error: unknown) {
    ws.close(1011, "Unexpected error");
  }
}
```

Key hibernation benefits:
- DO can be evicted from memory while WebSocket connections remain open
- Only billed for active processing time, not idle connections
- Supports up to 32,768 concurrent connections per DO
- Auto ping/pong with `this.ctx.setWebSocketAutoResponse()`

## Lifecycle and Concurrency

- **Single-threaded** — Only one event processes at a time (no data races)
- **Constructor** — Runs on first access or after eviction
- **Eviction** — Idle DOs are evicted from memory (storage persists)
- **`blockConcurrencyWhile`** — Blocks all events during initialization:

```typescript
constructor(ctx: DurableObjectState, env: Env) {
  super(ctx, env);
  ctx.blockConcurrencyWhile(async () => {
    this.state = await ctx.storage.get("state") ?? {};
  });
}
```

## Limits and Pricing

| Limit | Free | Paid |
|-------|------|------|
| Requests | 100,000/day | 1M/mo + $0.15/million |
| Duration | 13,000 GB-s/day | 400K GB-s/mo + $12.50/million GB-s |
| Storage (SQLite) | 1 GB | Included + $0.20/GB-mo |
| Max storage per DO | 1 GB (SQLite), 256 MB (KV) | — |
| WebSocket connections per DO | 32,768 | 32,768 |
| Storage ops per request | 1,000 | 1,000 |
| Alarm precision | ±30s | ±30s |

## Common Patterns

### Rate Limiter

```typescript
export class RateLimiter extends DurableObject {
  async checkLimit(key: string, maxRequests: number, windowMs: number): Promise<boolean> {
    const now = Date.now();
    const windowStart = now - windowMs;

    this.ctx.storage.sql.exec("DELETE FROM requests WHERE timestamp < ?", windowStart);

    const count = this.ctx.storage.sql
      .exec("SELECT count(*) as c FROM requests WHERE key = ?", key)
      .one() as { c: number };

    if (count.c >= maxRequests) return false;

    this.ctx.storage.sql.exec("INSERT INTO requests (key, timestamp) VALUES (?, ?)", key, now);
    return true;
  }
}
```

## Common Pitfalls

- **One alarm at a time** — `setAlarm()` replaces any existing alarm. For multiple timers, manage a queue in storage.
- **Constructor runs on every wake** — Don't assume constructor state persists. Always load from storage.
- **SQLite vs KV backends** — Use `new_sqlite_classes` in migrations. SQLite is recommended for all new DOs.
- **`blockConcurrencyWhile` timeout** — Has a 30-second limit. Keep initialization fast.
- **Billing** — Duration is billed in GB-seconds. A DO with 128MB RAM active for 1 second = 0.125 GB-s.
