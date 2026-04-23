# Cloudflare Workers KV — Key-Value Storage

> Source: [developers.cloudflare.com/kv](https://developers.cloudflare.com/kv/)

## Table of Contents

- [What Is Workers KV](#what-is-workers-kv)
- [Setup and Configuration](#setup-and-configuration)
- [Reading Values](#reading-values)
- [Writing Values](#writing-values)
- [Deleting Values](#deleting-values)
- [Listing Keys](#listing-keys)
- [Metadata](#metadata)
- [Expiration and TTL](#expiration-and-ttl)
- [Consistency Model](#consistency-model)
- [Limits and Pricing](#limits-and-pricing)
- [Common Patterns](#common-patterns)

## What Is Workers KV

Workers KV is a global, low-latency key-value store. Data is written centrally and cached at Cloudflare's edge locations worldwide.

**Best for:** Configuration, feature flags, user sessions, URL shorteners, static content caching, API key lookups.

**Not ideal for:** Frequently updated data (eventual consistency), counters (use Durable Objects), relational data (use D1).

## Setup and Configuration

```bash
# Create a KV namespace
wrangler kv namespace create MY_KV
# => Created namespace "worker-MY_KV" (id: abc123)

# Create preview namespace (for local dev)
wrangler kv namespace create MY_KV --preview
```

```toml
# wrangler.toml
[[kv_namespaces]]
binding = "MY_KV"
id = "abc123"
preview_id = "preview456"
```

```typescript
interface Env {
  MY_KV: KVNamespace;
}
```

## Reading Values

### get() — Single Key

```typescript
// Returns string by default
const value = await env.MY_KV.get("user:123");
// => string | null

// Parse as JSON
const user = await env.MY_KV.get("user:123", "json");
// => object | null

// Binary data
const data = await env.MY_KV.get("file:avatar", "arrayBuffer");
// => ArrayBuffer | null

// Streaming (most efficient for large values)
const stream = await env.MY_KV.get("file:large", "stream");
// => ReadableStream | null

// With options object
const value = await env.MY_KV.get("key", { type: "json", cacheTtl: 120 });
```

### get() — Multiple Keys (Batch)

```typescript
// Read up to 100 keys at once
const values = await env.MY_KV.get(["key1", "key2", "key3"], "json");
// => Map<string, object | null>

for (const [key, value] of values) {
  console.log(key, value);
}
```

### getWithMetadata() — Value + Metadata

```typescript
// Single key
const { value, metadata } = await env.MY_KV.getWithMetadata("user:123", "json");
// value: object | null
// metadata: object | null

// Multiple keys
const results = await env.MY_KV.getWithMetadata(["k1", "k2"], "json");
// => Map<string, { value: object | null, metadata: object | null }>
```

### cacheTtl Option

Controls how long KV values are cached at the edge (seconds). Default: 60s. Minimum: 30s.

```typescript
// Cache for 5 minutes at the edge
const value = await env.MY_KV.get("config", { type: "json", cacheTtl: 300 });
```

## Writing Values

### put() — Write a Key-Value Pair

```typescript
// String value
await env.MY_KV.put("greeting", "Hello, World!");

// JSON (must stringify)
await env.MY_KV.put("user:123", JSON.stringify({ name: "Alice", role: "admin" }));

// Binary (ArrayBuffer or ReadableStream)
await env.MY_KV.put("image:avatar", imageArrayBuffer);

// With options
await env.MY_KV.put("session:abc", sessionData, {
  expirationTtl: 3600,                              // Expire in 1 hour
  metadata: { userId: "123", createdAt: Date.now() },  // Attached metadata
});

// With absolute expiration
await env.MY_KV.put("token:xyz", tokenValue, {
  expiration: Math.floor(Date.now() / 1000) + 86400,  // Unix seconds
});
```

### Write Limits

- Key size: max 512 bytes
- Value size: max 25 MB
- Metadata: max 1024 bytes (JSON-serialized)
- Rate: max 1 write per key per second (429 on violation)

## Deleting Values

```typescript
await env.MY_KV.delete("user:123");
// Returns Promise<void> — no error if key doesn't exist
```

## Listing Keys

```typescript
// List all keys
const result = await env.MY_KV.list();
// => { keys: [{ name, expiration?, metadata? }], list_complete: boolean, cursor: string }

// Filter by prefix
const userKeys = await env.MY_KV.list({ prefix: "user:" });

// Limit results
const batch = await env.MY_KV.list({ prefix: "session:", limit: 100 });

// Pagination
let cursor: string | undefined;
const allKeys: string[] = [];

do {
  const result = await env.MY_KV.list({ prefix: "item:", cursor });
  allKeys.push(...result.keys.map((k) => k.name));
  cursor = result.list_complete ? undefined : result.cursor;
} while (cursor);
```

### KVNamespaceListResult

```typescript
interface KVNamespaceListResult {
  keys: Array<{
    name: string;
    expiration?: number;   // Unix timestamp (seconds)
    metadata?: unknown;
  }>;
  list_complete: boolean;  // true = no more keys
  cursor: string;          // Use for next page if list_complete is false
}
```

## Metadata

Attach up to 1024 bytes of JSON metadata to any key:

```typescript
// Write with metadata
await env.MY_KV.put("doc:readme", content, {
  metadata: {
    contentType: "text/markdown",
    author: "alice",
    version: 3,
  },
});

// Read metadata without reading the value
const { value, metadata } = await env.MY_KV.getWithMetadata("doc:readme");

// Metadata also appears in list results
const result = await env.MY_KV.list({ prefix: "doc:" });
for (const key of result.keys) {
  console.log(key.name, key.metadata);
}
```

## Expiration and TTL

Two ways to set expiration:

```typescript
// Relative: expirationTtl (seconds from now, minimum 60)
await env.MY_KV.put("cache:data", value, { expirationTtl: 300 }); // 5 minutes

// Absolute: expiration (Unix timestamp in seconds)
const oneHourFromNow = Math.floor(Date.now() / 1000) + 3600;
await env.MY_KV.put("temp:token", value, { expiration: oneHourFromNow });
```

Expired keys are lazily cleaned up — they may appear in `list()` briefly but `get()` returns `null`.

## Consistency Model

KV is **eventually consistent**:

- Writes are durably stored centrally within seconds
- Reads at other edge locations may see stale data for up to 60 seconds (or `cacheTtl`)
- Writes to the same key from the same location are immediately visible
- There are no transactions or atomic operations across keys

If you need strong consistency, use **Durable Objects** or **D1** instead.

## Limits and Pricing

| Limit | Free | Paid |
|-------|------|------|
| Key size | 512 bytes | 512 bytes |
| Value size | 25 MB | 25 MB |
| Metadata size | 1024 bytes | 1024 bytes |
| Reads/day | 100,000 | 10M/mo ($0.50/million) |
| Writes/day | 1,000 | 1M/mo ($5.00/million) |
| Deletes/day | 1,000 | 1M/mo ($5.00/million) |
| List ops/day | 1,000 | 1M/mo ($5.00/million) |
| Storage | 1 GB | 1 GB + $0.50/GB-mo |
| Ops per Worker invocation | 1,000 | 1,000 |
| Batch get keys | 100 | 100 |

## Common Patterns

### Feature Flags

```typescript
async function isFeatureEnabled(env: Env, flag: string): Promise<boolean> {
  const value = await env.MY_KV.get(`flag:${flag}`, "json");
  return value?.enabled ?? false;
}
```

### URL Shortener

```typescript
export default {
  async fetch(request: Request, env: Env) {
    const url = new URL(request.url);
    const slug = url.pathname.slice(1);

    if (request.method === "GET" && slug) {
      const target = await env.LINKS.get(slug);
      if (target) return Response.redirect(target, 302);
      return new Response("Not found", { status: 404 });
    }

    if (request.method === "POST") {
      const { slug, url: target } = await request.json<{ slug: string; url: string }>();
      await env.LINKS.put(slug, target, {
        metadata: { createdAt: Date.now() },
      });
      return Response.json({ slug, url: target }, { status: 201 });
    }

    return new Response("Method not allowed", { status: 405 });
  },
};
```

### Session Store

```typescript
async function getSession(env: Env, sessionId: string): Promise<Session | null> {
  return env.SESSIONS.get(`sess:${sessionId}`, "json");
}

async function setSession(env: Env, sessionId: string, data: Session): Promise<void> {
  await env.SESSIONS.put(`sess:${sessionId}`, JSON.stringify(data), {
    expirationTtl: 86400, // 24 hours
  });
}
```

## Common Pitfalls

- **Don't use KV for counters** — Eventually consistent reads mean concurrent increments will lose writes. Use Durable Objects for counters.
- **JSON storage** — `put()` doesn't auto-serialize. Always `JSON.stringify()` objects. But `get("key", "json")` does auto-parse.
- **Rate limiting** — Max 1 write/key/second. Batch writes to different keys are fine.
- **List doesn't return values** — `list()` returns keys and metadata only, not values. You must `get()` each key separately.
- **Eventual consistency window** — Writes in one region may not be visible in another for up to 60s. Design accordingly.
