# Upstash Redis SDK — TypeScript

HTTP-based Redis client for serverless and edge runtimes. Every command is a
single HTTP request — no persistent connections, no connection pooling.

## Table of Contents

- [Installation](#installation)
- [Initialization](#initialization)
- [Environment Variables](#environment-variables)
- [Configuration Options](#configuration-options)
- [Basic Operations](#basic-operations)
- [Type Safety](#type-safety)
- [Data Structure Operations](#data-structure-operations)
- [Pipelines](#pipelines)
- [Transactions (MULTI/EXEC)](#transactions-multiexec)
- [Auto-Pipelining](#auto-pipelining)
- [Error Handling and Retries](#error-handling-and-retries)
- [Scan and Iteration](#scan-and-iteration)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Installation

```bash
npm install @upstash/redis
```

```bash
# Deno
import { Redis } from "https://deno.land/x/upstash_redis/mod.ts"
```

## Initialization

### From Environment Variables (Recommended)

```typescript
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();
```

Reads `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` from the
environment automatically.

### Direct Configuration

```typescript
import { Redis } from "@upstash/redis";

const redis = new Redis({
  url: "https://us1-example.upstash.io",
  token: "AX...",
});
```

### Cloudflare Workers

```typescript
import { Redis } from "@upstash/redis/cloudflare";

export default {
  async fetch(request: Request, env: Env) {
    const redis = Redis.fromEnv(env);
    const value = await redis.get("key");
    return new Response(value);
  },
};
```

Cloudflare Workers must use the `/cloudflare` import path. The `env` parameter
is passed to `fromEnv()` because Workers do not expose process-level environment
variables.

### Fastly Compute

```typescript
import { Redis } from "@upstash/redis/fastly";

const redis = new Redis({
  url: "https://us1-example.upstash.io",
  token: "AX...",
  backend: "upstash-redis",
});
```

The `backend` field must match the backend name configured in your Fastly
service.

## Environment Variables

| Variable                    | Description              |
| --------------------------- | ------------------------ |
| `UPSTASH_REDIS_REST_URL`    | REST API endpoint URL    |
| `UPSTASH_REDIS_REST_TOKEN`  | Authentication token     |

## Configuration Options

```typescript
const redis = new Redis({
  url: "https://us1-example.upstash.io",
  token: "AX...",

  // Auto-parse JSON responses (default: true)
  automaticDeserialization: true,

  // Send anonymous usage statistics (default: true)
  enableTelemetry: false,

  // Retry configuration
  retry: {
    retries: 5,
    backoff: (retryCount) => Math.exp(retryCount) * 50,
  },

  // Auto-batch concurrent calls in Promise.all (default: false)
  enableAutoPipelining: false,
});
```

| Option                       | Type                                         | Default | Description                                      |
| ---------------------------- | -------------------------------------------- | ------- | ------------------------------------------------ |
| `url`                        | `string`                                     | —       | REST API endpoint                                |
| `token`                      | `string`                                     | —       | Authentication token                             |
| `automaticDeserialization`   | `boolean`                                    | `true`  | Auto-parse JSON values on read                   |
| `enableTelemetry`            | `boolean`                                    | `true`  | Send anonymous usage stats                       |
| `retry`                      | `{ retries: number; backoff: Function }`     | —       | Retry failed requests with backoff               |
| `enableAutoPipelining`       | `boolean`                                    | `false` | Auto-batch `Promise.all()` calls                 |

## Basic Operations

### Strings

```typescript
// Set a string value
await redis.set("greeting", "hello");

// Set a JSON object (auto-serialized)
await redis.set("user:1", { name: "Alice", age: 30 });

// Get a value
const greeting = await redis.get("greeting");
// greeting: "hello"

// Get with type parameter
const user = await redis.get<{ name: string; age: number }>("user:1");
// user: { name: "Alice", age: 30 } | null
```

### Expiration

```typescript
// Set with TTL in seconds
await redis.set("session:abc", { userId: 42 }, { ex: 3600 });

// Set with TTL in milliseconds
await redis.set("temp", "data", { px: 60000 });

// Set only if key does not exist
await redis.set("lock:resource", "owner-1", { nx: true, ex: 30 });

// Set only if key already exists
await redis.set("counter", 10, { xx: true });
```

### Counters and Key Operations

```typescript
// Counters: incr, incrby, decr, decrby, incrbyfloat
await redis.incr("visits");          // +1, returns new value
await redis.incrby("score", 10);     // +N
await redis.decrby("score", 5);      // -N

// Key operations: exists, del, expire, ttl, rename, type
await redis.exists("user:1");        // 1 or 0
await redis.del("key1", "key2");
await redis.expire("session:abc", 1800);
const ttl = await redis.ttl("session:abc");
```

See `02-redis-commands.md` for the full command reference.

## Type Safety

```typescript
type User = {
  name: string;
  email: string;
  plan: "free" | "pro";
};

// Typed get — returns User | null
const user = await redis.get<User>("user:1");

if (user) {
  console.log(user.name); // type-safe access
}

// Typed list range
const users = await redis.lrange<User>("users:recent", 0, 9);

// Typed hash
const profile = await redis.hgetall<User>("profile:1");

// Typed sorted set
const leaders = await redis.zrange<User>("leaderboard", 0, 4);
```

## Data Structure Operations

Hash, list, set, and sorted set commands are fully documented in `02-redis-commands.md`.
Key SDK usage notes:

```typescript
// Hashes — pass objects directly
await redis.hset("product:1", { name: "Widget", price: 29.99 });
const product = await redis.hgetall<{ name: string; price: number }>("product:1");

// Lists — lpush/rpush accept variadic args
await redis.lpush("queue", "task-3", "task-2", "task-1");
const items = await redis.lrange<string>("queue", 0, 9);

// Sets
await redis.sadd("tags:post:1", "typescript", "redis", "serverless");
const tags = await redis.smembers("tags:post:1");

// Sorted sets — array of { score, member }
await redis.zadd("leaderboard", [
  { score: 100, member: "alice" },
  { score: 85, member: "bob" },
]);
const top = await redis.zrange("leaderboard", 0, 2, { withScores: true });
```

## Pipelines

Batch multiple commands into a single HTTP request. Reduces round trips.

```typescript
const pipeline = redis.pipeline();
pipeline.set("key1", "value1");
pipeline.set("key2", "value2");
pipeline.get("key1");
pipeline.incr("counter");

const results = await pipeline.exec();
// results: ["OK", "OK", "value1", 1]
```

Results are ordered to match commands. Use a type parameter for typed results:

```typescript
const p = redis.pipeline();
p.get<string>("name");
p.get<number>("age");
p.smembers("tags");
const [name, age, tags] = await p.exec<[string, number, string[]]>();
```

## Transactions (MULTI/EXEC)

Execute commands atomically. All commands succeed or none do.

```typescript
const tx = redis.multi();
tx.set("balance", 100);
tx.decrby("balance", 25);
tx.get("balance");

const results = await tx.exec<["OK", number, string]>();
// results: ["OK", 75, "75"]
```

Unlike pipelines, transactions guarantee atomicity — no other client can
interleave commands between the MULTI and EXEC.

## Auto-Pipelining

Automatically batch concurrent requests made within the same event loop tick.

```typescript
const redis = new Redis({
  url: "https://us1-example.upstash.io",
  token: "AX...",
  enableAutoPipelining: true,
});

// These three calls are automatically batched into one HTTP request
const [user, posts, likes] = await Promise.all([
  redis.get("user:1"),
  redis.lrange("posts:1", 0, 9),
  redis.get("likes:1"),
]);
```

When `enableAutoPipelining` is `true`, all commands issued in the same tick
are combined into a single pipeline request. This is transparent to the
caller — each promise resolves with its own result.

## Encoding and Serialization

Objects/arrays are auto-serialized to JSON on write and deserialized on read
(when `automaticDeserialization: true`, the default). Set it to `false` to get
raw strings instead.

## Error Handling and Retries

Configure `retry` in the constructor (see Configuration Options above). The
`backoff` function receives the retry count (starting at 0) and returns delay
in ms. Without `retry`, failed requests are **not** retried.

```typescript
try {
  await redis.get("key");
} catch (error) {
  if (error instanceof Error) {
    console.error("Redis error:", error.message);
  }
}
```

## Telemetry

Disable with `enableTelemetry: false` in config or `UPSTASH_DISABLE_TELEMETRY=1`
env var. No keys/values/PII are collected.

## Scan and Iteration

```typescript
let cursor = 0;
const allKeys: string[] = [];
do {
  const [nextCursor, keys] = await redis.scan(cursor, { match: "user:*", count: 100 });
  cursor = nextCursor;
  allKeys.push(...keys);
} while (cursor !== 0);
```

## Common Patterns

### Rate Limiting

```typescript
async function isRateLimited(ip: string, limit: number): Promise<boolean> {
  const key = `rate:${ip}`;
  const current = await redis.incr(key);

  if (current === 1) {
    await redis.expire(key, 60); // 60-second window
  }

  return current > limit;
}
```

### Session Storage

```typescript
type Session = { userId: string; role: string };

async function createSession(sessionId: string, data: Session) {
  await redis.set(`session:${sessionId}`, data, { ex: 86400 });
}

async function getSession(sessionId: string): Promise<Session | null> {
  return redis.get<Session>(`session:${sessionId}`);
}
```

### Caching with Stale-While-Revalidate

```typescript
async function cachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number,
): Promise<T> {
  const cached = await redis.get<T>(key);
  if (cached !== null) return cached;

  const fresh = await fetcher();
  await redis.set(key, fresh, { ex: ttl });
  return fresh;
}
```

## Common Pitfalls

**No connection pooling needed.** Each command is an independent HTTP request.
There are no persistent connections to manage or pools to configure.

**JSON auto-serialization.** Objects passed to `set` are serialized to JSON
automatically. If you need to store raw strings that look like JSON, disable
`automaticDeserialization` or be aware that `get` will parse them.

**Pipeline results are ordered.** Results from `pipeline.exec()` correspond
to commands in the order they were added. Skipping a result by index can lead
to type mismatches.

**Cloudflare Workers import path.** Always import from `@upstash/redis/cloudflare`
in Workers. Using the default import path will fail because it relies on
Node.js APIs not available in the Workers runtime.

**Fastly requires a backend.** The `backend` option is mandatory for Fastly
Compute and must match the backend name in your Fastly service configuration.

**Large values.** The REST API has a request body limit (typically 1 MB). Avoid
storing very large values — split them or use a different storage strategy.

**Scan is not atomic.** The `scan` command may return duplicate keys across
iterations. Deduplicate results if exactness matters.
