# Upstash Rate Limiting — @upstash/ratelimit

The only connectionless, HTTP-based rate limiting library. Built on top of Upstash Redis, designed for serverless, edge, Cloudflare Workers, Vercel Edge, Deno Deploy, and AWS Lambda.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Basic Setup](#basic-setup)
- [Algorithms](#algorithms)
- [Window Duration Format](#window-duration-format)
- [Core Methods](#core-methods)
- [Configuration Options](#configuration-options)
- [Caching with Ephemeral Cache](#caching-with-ephemeral-cache)
- [Timeout Handling](#timeout-handling)
- [Multiple Rate Limits](#multiple-rate-limits)
- [Dynamic Rate Limits](#dynamic-rate-limits)
- [Multi-Region Rate Limiting](#multi-region-rate-limiting)
- [Traffic Protection and Deny Lists](#traffic-protection-and-deny-lists)
- [Analytics Dashboard](#analytics-dashboard)
- [Next.js Middleware Example](#nextjs-middleware-example)
- [Cloudflare Workers Example](#cloudflare-workers-example)
- [Common Pitfalls](#common-pitfalls)

## Overview

Traditional rate limiters rely on in-memory state or TCP connections to Redis. `@upstash/ratelimit` communicates over HTTP, making it the only rate limiter that works in every JavaScript runtime without persistent connections.

- **Connectionless** — HTTP/REST, no TCP sockets or connection pools
- **Serverless-native** — Cloudflare Workers, Vercel Edge, Deno Deploy, AWS Lambda, Node.js
- **Three algorithms** — fixed window, sliding window, and token bucket
- **Built-in analytics** — dashboard in the Upstash Console for allowed vs. blocked requests
- **Ephemeral caching** — in-memory cache to reduce Redis calls for blocked identifiers
- **Multi-region** — distribute state across multiple Redis instances globally

## Installation

```bash
npm install @upstash/ratelimit @upstash/redis
```

For Deno:

```typescript
import { Ratelimit } from "https://cdn.skypack.dev/@upstash/ratelimit@latest";
import { Redis } from "https://cdn.skypack.dev/@upstash/redis@latest";
```

## Basic Setup

```typescript
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "10 s"),
  analytics: true,
  prefix: "@upstash/ratelimit",
});
```

`Redis.fromEnv()` reads `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` from environment variables.

## Algorithms

### Fixed Window

```typescript
Ratelimit.fixedWindow(maxRequests, window)
// Example: 10 requests per 10 seconds
Ratelimit.fixedWindow(10, "10 s")
```

Divides time into fixed intervals. Counter resets at each interval boundary. Simplest algorithm, but allows bursts at window boundaries — a user can send `maxRequests` at the end of one window and `maxRequests` at the start of the next.

### Sliding Window

```typescript
Ratelimit.slidingWindow(maxRequests, window)
// Example: 10 requests per 10 seconds
Ratelimit.slidingWindow(10, "10 s")
```

Smooths out burst traffic by weighting previous and current window counts. The effective count is: `previousWindowCount * (1 - elapsed/windowSize) + currentWindowCount`. This is the **recommended default** for most use cases.

### Token Bucket

```typescript
Ratelimit.tokenBucket(refillRate, interval, maxTokens)
// Example: refill 5 tokens per 10 seconds, max 10 tokens
Ratelimit.tokenBucket(5, "10 s", 10)
```

Maintains a bucket that refills at a steady rate. Allows controlled bursts up to `maxTokens` while enforcing a sustained rate. A new user starts with `maxTokens` available. Best for APIs that allow occasional bursts.

## Window Duration Format

Supported units: `"ms"`, `"s"`, `"m"`, `"h"`, `"d"`

```typescript
Ratelimit.fixedWindow(100, "1 h")       // 100 per hour
Ratelimit.slidingWindow(10, "10 s")     // 10 per 10 seconds
Ratelimit.slidingWindow(1000, "1 d")    // 1000 per day
Ratelimit.tokenBucket(1, "500 ms", 5)   // 1 token per 500ms, max 5
```

## Core Methods

### limit(identifier)

Checks whether a request should be allowed and increments the counter atomically.

```typescript
const { success, limit, remaining, reset, pending } = await ratelimit.limit("user:123");

if (!success) {
  return new Response("Too Many Requests", { status: 429 });
}
```

**Return fields:**

| Field       | Type            | Description                                           |
|-------------|-----------------|-------------------------------------------------------|
| `success`   | `boolean`       | Whether the request should be allowed                 |
| `limit`     | `number`        | Maximum requests allowed in the window                |
| `remaining` | `number`        | Remaining requests in the current window              |
| `reset`     | `number`        | Unix timestamp (ms) when the window resets            |
| `pending`   | `Promise<void>` | Resolves when analytics are sent — await in serverless |

### blockUntilReady(identifier, timeout)

Blocks until a token is available or the timeout (in ms) is reached.

```typescript
const { success } = await ratelimit.blockUntilReady("user:123", 30_000);
// Blocks up to 30 seconds until a token is available
if (!success) {
  return new Response("Service Unavailable", { status: 503 });
}
```

### resetUsedTokens(identifier)

Resets the rate limit counter for an identifier. Useful for admin actions or plan upgrades.

```typescript
await ratelimit.resetUsedTokens("user:123");
```

### getRemaining(identifier)

Returns remaining requests without consuming a token (read-only).

```typescript
const remaining = await ratelimit.getRemaining("user:123");
```

## Configuration Options

```typescript
const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),                        // Required
  limiter: Ratelimit.slidingWindow(10, "10 s"),   // Required
  analytics: true,                                // Enable dashboard
  prefix: "@upstash/ratelimit",                   // Redis key prefix
  ephemeralCache: new Map(),                      // In-memory denial cache
  timeout: 1000,                                  // Fail-open timeout (ms)
});
```

| Option           | Type      | Default                 | Description                                        |
|------------------|-----------|-------------------------|----------------------------------------------------|
| `redis`          | `Redis`   | —                       | Upstash Redis instance (required)                  |
| `limiter`        | `Algorithm` | —                     | Algorithm configuration (required)                 |
| `analytics`      | `boolean` | `false`                 | Send analytics for the Upstash Console             |
| `prefix`         | `string`  | `"@upstash/ratelimit"` | Prefix for all Redis keys                          |
| `ephemeralCache` | `Map`     | `undefined`             | In-memory cache for blocked identifiers            |
| `timeout`        | `number`  | `undefined`             | Ms before auto-allowing if Redis is slow           |

## Caching with Ephemeral Cache

Caches denied identifiers in memory to avoid unnecessary Redis calls for already-blocked users.

```typescript
const cache = new Map();
const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "10 s"),
  ephemeralCache: cache,
});
```

When `limit()` returns `success: false`, the identifier and reset time are stored in the `Map`. Subsequent calls skip Redis and return a denial from memory until the window resets. The cache only stores **denials**, never approvals — approved requests always hit Redis to keep counters accurate.

## Timeout Handling

Implements a fail-open pattern. If Redis does not respond in time, the request is automatically allowed.

```typescript
const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "10 s"),
  timeout: 1000, // Allow request if Redis doesn't respond within 1s
});
```

This prevents rate limiting from becoming a single point of failure during Redis outages.

## Multiple Rate Limits

Apply multiple limits simultaneously. A request is denied if **any** limit is exceeded.

```typescript
const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: [
    Ratelimit.slidingWindow(100, "1 h"),   // 100 per hour
    Ratelimit.slidingWindow(10, "10 s"),   // 10 per 10 seconds
  ],
});
```

All limits are checked atomically in a single Redis call.

## Dynamic Rate Limits

Override the configured limit at call time for specific identifiers, enabling per-tier limits without multiple instances.

```typescript
const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "10 s"),
});

// Premium user gets a higher limit
const { success } = await ratelimit.limit("user:premium-456", { rate: 100 });

// Free user uses the default (10 per 10s)
const { success: freeSuccess } = await ratelimit.limit("user:free-789");
```

## Multi-Region Rate Limiting

Use `RegionRatelimit` to replicate state across multiple Redis instances for global applications.

```typescript
import { RegionRatelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new RegionRatelimit({
  redis: [
    new Redis({ url: "https://us-east-1.upstash.io", token: "us-east-token" }),
    new Redis({ url: "https://eu-west-1.upstash.io", token: "eu-west-token" }),
  ],
  limiter: RegionRatelimit.slidingWindow(10, "10 s"),
});
```

Each `limit()` call writes to all Redis instances. The effective limit is split across regions.

## Traffic Protection and Deny Lists

Block known bad actors outright without consuming rate limit tokens.

```typescript
const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "10 s"),
  denyList: {
    ip: ["1.2.3.4"],
    userAgent: ["BadBot"],
    country: ["XX"],
  },
});
```

Matching requests are immediately rejected before the rate limit algorithm runs.

## Analytics Dashboard

Enable with `analytics: true`. View in the Upstash Console under the Ratelimit section. Shows requests allowed vs. blocked over time, top rate-limited identifiers, and utilization by endpoint.

You must handle the `pending` promise in serverless environments to ensure analytics data is flushed before the function terminates.

## Next.js Middleware Example

```typescript
// middleware.ts
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";
import { NextRequest, NextResponse } from "next/server";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(20, "10 s"),
  analytics: true,
});

export async function middleware(request: NextRequest) {
  const ip = request.ip ?? "127.0.0.1";
  const { success, limit, remaining, reset, pending } = await ratelimit.limit(ip);

  const response = success
    ? NextResponse.next()
    : new NextResponse("Too Many Requests", { status: 429 });

  response.headers.set("X-RateLimit-Limit", limit.toString());
  response.headers.set("X-RateLimit-Remaining", remaining.toString());
  response.headers.set("X-RateLimit-Reset", reset.toString());

  await pending;
  return response;
}

export const config = { matcher: "/api/:path*" };
```

## Cloudflare Workers Example

Use `context.waitUntil(pending)` to flush analytics without blocking the response.

```typescript
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis/cloudflare";

export default {
  async fetch(request: Request, env: Env, context: ExecutionContext): Promise<Response> {
    const ratelimit = new Ratelimit({
      redis: Redis.fromEnv(env),
      limiter: Ratelimit.slidingWindow(10, "10 s"),
      analytics: true,
    });

    const ip = request.headers.get("cf-connecting-ip") ?? "127.0.0.1";
    const { success, pending } = await ratelimit.limit(ip);

    context.waitUntil(pending);

    if (!success) {
      return new Response("Too Many Requests", { status: 429 });
    }

    return new Response("OK");
  },
};
```

Import `Redis` from `@upstash/redis/cloudflare` for the Cloudflare-specific build.

## Common Pitfalls

- **Always await `pending` in edge/serverless environments.** The function may terminate before analytics are sent. Use `context.waitUntil(pending)` in Cloudflare Workers or `await pending` in Next.js middleware.

- **Use the Cloudflare-specific Redis import for Workers.** Import from `@upstash/redis/cloudflare`, not `@upstash/redis`.

- **ephemeralCache only caches denials, not approvals.** Every approved request still hits Redis to keep counters accurate across instances.

- **Multiple limits: request is denied if ANY limit is exceeded.** All limits must pass for the request to be allowed.

- **Prefix should be unique per ratelimiter instance.** If you have separate limiters for API routes and auth, use different prefixes to avoid counter collisions.

- **`timeout: 0` means no timeout (wait indefinitely).** Set an explicit timeout in production to prevent cascading failures.

- **Identifier granularity matters.** IP addresses fail behind shared NATs. User IDs are more accurate. Combine them (e.g., `user:123:POST:/api/upload`) for endpoint-specific limits.

- **Rate limits are not shared across Redis instances** unless using `RegionRatelimit`. Switching Redis instances resets all counters.
