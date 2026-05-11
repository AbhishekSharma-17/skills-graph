# Upstash — Patterns & Recipes

Common patterns, recipes, and production-ready code examples for building
applications with Upstash Redis, QStash, and Workflow.

## Table of Contents

- [Caching Pattern](#caching-pattern)
  - [Cache Invalidation](#cache-invalidation)
- [Session Storage](#session-storage)
- [Leaderboard](#leaderboard)
- [Feature Flags](#feature-flags)
- [Job Queue Pattern](#job-queue-pattern)
- [Pub/Sub Messaging](#pubsub-messaging)
- [Distributed Lock](#distributed-lock)
- [Counting & Analytics](#counting--analytics)
- [Email Queue with Workflow](#email-queue-with-workflow)
- [API Response Caching with Stale-While-Revalidate](#api-response-caching-with-stale-while-revalidate)
- [Common Pitfalls](#common-pitfalls)

---

## Caching Pattern

Cache-aside (lazy loading) — check the cache first, fall back to the source,
and populate the cache on miss.

```typescript
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();

async function cachedFetch<T>(key: string, fetcher: () => Promise<T>, ttl = 3600): Promise<T> {
  const cached = await redis.get<T>(key);
  if (cached !== null) return cached;

  const data = await fetcher();
  await redis.set(key, data, { ex: ttl });
  return data;
}

// Usage
const user = await cachedFetch(`user:${id}`, () => db.users.findById(id));
```

### Cache Invalidation

```typescript
// Invalidate single key
await redis.del("user:123");

// Invalidate by pattern (use scan)
const keys = await redis.keys("user:*");
if (keys.length > 0) await redis.del(...keys);

// Cache-aside with TTL (simplest invalidation)
await redis.set("data", value, { ex: 300 }); // Auto-expire in 5 min
```

---

## Session Storage

```typescript
import { Redis } from "@upstash/redis";
import crypto from "crypto";

const redis = Redis.fromEnv();

interface Session {
  userId: string;
  role: string;
  createdAt: number;
}

async function createSession(userId: string, role: string): Promise<string> {
  const sessionId = crypto.randomUUID();
  const session: Session = { userId, role, createdAt: Date.now() };
  await redis.set(`session:${sessionId}`, session, { ex: 86400 }); // 24h
  return sessionId;
}

async function getSession(sessionId: string): Promise<Session | null> {
  return redis.get<Session>(`session:${sessionId}`);
}

async function deleteSession(sessionId: string): Promise<void> {
  await redis.del(`session:${sessionId}`);
}

// Extend session TTL on activity
async function touchSession(sessionId: string): Promise<void> {
  await redis.expire(`session:${sessionId}`, 86400);
}
```

---

## Leaderboard

Sorted sets provide efficient ranking with O(log N) insertions and lookups.

```typescript
const redis = Redis.fromEnv();

// Add/update score
await redis.zadd("leaderboard", { score: 1500, member: "player1" });
await redis.zadd("leaderboard", { score: 2200, member: "player2" });

// Increment score
await redis.zincrby("leaderboard", 100, "player1");

// Top 10 players (highest score first)
const top10 = await redis.zrange("leaderboard", 0, 9, { rev: true, withScores: true });

// Player rank (0-indexed, highest = 0)
const rank = await redis.zrevrank("leaderboard", "player1");

// Player score
const score = await redis.zscore("leaderboard", "player1");

// Players within score range
const tier = await redis.zrangebyscore("leaderboard", 1000, 2000);
```

---

## Feature Flags

```typescript
const redis = Redis.fromEnv();

// Set feature flags
await redis.hset("features", {
  "dark-mode": "true",
  "beta-dashboard": "false",
  "max-upload-mb": "50",
});

// Check a flag
async function isFeatureEnabled(flag: string): Promise<boolean> {
  const value = await redis.hget("features", flag);
  return value === "true";
}

// Get all flags
const allFlags = await redis.hgetall("features");

// Flag with percentage rollout
async function isEnabledForUser(flag: string, userId: string, percentage: number): Promise<boolean> {
  const hash = Buffer.from(userId).reduce((acc, b) => acc + b, 0);
  return (hash % 100) < percentage;
}
```

---

## Job Queue Pattern

Using QStash for background jobs:

```typescript
import { Client } from "@upstash/qstash";

const qstash = new Client({ token: process.env.QSTASH_TOKEN! });

// Enqueue a job
async function enqueueJob(type: string, payload: any) {
  await qstash.publishJSON({
    url: `${process.env.APP_URL}/api/jobs/${type}`,
    body: payload,
    retries: 3,
  });
}

// Delayed job
async function scheduleJob(type: string, payload: any, delaySec: number) {
  await qstash.publishJSON({
    url: `${process.env.APP_URL}/api/jobs/${type}`,
    body: payload,
    delay: delaySec,
  });
}

// Recurring job
async function createRecurringJob(type: string, payload: any, cron: string) {
  await qstash.schedules.create({
    destination: `${process.env.APP_URL}/api/jobs/${type}`,
    cron,
    body: JSON.stringify(payload),
  });
}
```

Job handler with idempotency and signature verification:

```typescript
import { verifySignatureAppRouter } from "@upstash/qstash/nextjs";

export const POST = verifySignatureAppRouter(async (req: Request) => {
  const messageId = req.headers.get("Upstash-Message-Id")!;
  const body = await req.json();

  // Check if already processed (idempotency)
  const processed = await redis.get(`processed:${messageId}`);
  if (processed) return new Response("Already processed", { status: 200 });

  await processJob(body);

  // Mark as processed with TTL
  await redis.set(`processed:${messageId}`, 1, { ex: 86400 });
  return new Response("OK");
});
```

---

## Pub/Sub Messaging

Using Upstash Redis pub/sub via REST API:

```typescript
// Publish
await redis.publish("notifications", JSON.stringify({
  type: "user.created",
  userId: "123",
}));

// Subscribe (via REST SSE endpoint)
const response = await fetch(`${UPSTASH_REDIS_REST_URL}/subscribe/notifications`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${UPSTASH_REDIS_REST_TOKEN}`,
    Accept: "text/event-stream",
  },
});
```

---

## Distributed Lock

```typescript
const redis = Redis.fromEnv();

async function acquireLock(key: string, ttl = 10): Promise<string | null> {
  const lockId = crypto.randomUUID();
  const acquired = await redis.set(`lock:${key}`, lockId, { nx: true, ex: ttl });
  return acquired === "OK" ? lockId : null;
}

async function releaseLock(key: string, lockId: string): Promise<boolean> {
  const script = `
    if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("del", KEYS[1])
    else
      return 0
    end
  `;
  const result = await redis.eval(script, ["lock:" + key], [lockId]);
  return result === 1;
}

// Usage
const lockId = await acquireLock("resource:123");
if (lockId) {
  try {
    await doExclusiveWork();
  } finally {
    await releaseLock("resource:123", lockId);
  }
}
```

---

## Counting & Analytics

```typescript
const redis = Redis.fromEnv();

// Page views per day
const today = new Date().toISOString().slice(0, 10);
await redis.incr(`pageviews:${today}`);

// Unique visitors (HyperLogLog)
await redis.pfadd(`visitors:${today}`, visitorId);
const uniqueVisitors = await redis.pfcount(`visitors:${today}`);

// Sliding window counter
await redis.zadd("events", { score: Date.now(), member: `event:${crypto.randomUUID()}` });
// Count events in last hour
const oneHourAgo = Date.now() - 3600000;
const count = await redis.zcount("events", oneHourAgo, "+inf");
// Cleanup old events
await redis.zremrangebyscore("events", "-inf", oneHourAgo);
```

---

## Email Queue with Workflow

Multi-step email sequences with delays, conditions, and retry guarantees.

```typescript
import { serve } from "@upstash/workflow/nextjs";

export const { POST } = serve(async (context) => {
  const { userId, type } = context.requestPayload;

  const user = await context.run("fetch-user", async () => {
    return await db.users.findById(userId);
  });

  await context.run("send-welcome", async () => {
    await sendEmail(user.email, "Welcome!", welcomeTemplate(user));
  });

  await context.sleep("wait-3-days", 60 * 60 * 24 * 3);

  const hasActivated = await context.run("check-activation", async () => {
    return await db.users.hasActivated(userId);
  });

  if (!hasActivated) {
    await context.run("send-reminder", async () => {
      await sendEmail(user.email, "Don't forget!", reminderTemplate(user));
    });
  }
});
```

---

## API Response Caching with Stale-While-Revalidate

Serve stale data immediately while refreshing in the background:

```typescript
async function swr<T>(key: string, fetcher: () => Promise<T>, opts = { ttl: 300, stale: 60 }): Promise<T> {
  const cached = await redis.get<{ data: T; timestamp: number }>(key);

  if (cached) {
    const age = (Date.now() - cached.timestamp) / 1000;
    if (age < opts.ttl) return cached.data;

    // Stale but within grace period — return stale, revalidate in background
    if (age < opts.ttl + opts.stale) {
      qstash.publishJSON({
        url: `${APP_URL}/api/revalidate`,
        body: { key },
      });
      return cached.data;
    }
  }

  const data = await fetcher();
  await redis.set(key, { data, timestamp: Date.now() }, { ex: opts.ttl + opts.stale });
  return data;
}
```

---

## Common Pitfalls

**Lock Safety**
- Always use `NX` flag for distributed locks to prevent race conditions.
- Use `EVAL` for atomic check-and-delete operations (lock release).
  A simple `GET` then `DEL` is not safe under concurrency.
- Set a reasonable TTL on locks to prevent deadlocks if the holder crashes.

**Data Structures**
- HyperLogLog (`PFADD`/`PFCOUNT`) has ~0.81% standard error.
- Sorted set leaderboards use `ZREVRANGE` for descending order.
- Hash fields are strings — parse numeric values explicitly when reading.

**Memory Management**
- Set appropriate TTLs to prevent Redis memory growth.
- Use `LTRIM` after `LPUSH` to cap list length.
- Clean up sorted sets periodically with `ZREMRANGEBYSCORE`.

**Performance**
- Use `pipeline()` for bulk operations to reduce HTTP round trips.
- Avoid `KEYS` in production on large keyspaces — use `SCAN` instead.
- Cache serialized objects, not class instances.

**QStash & Workflow**
- Always verify QStash signatures in job handlers.
- Use idempotency keys (message ID) to prevent duplicate processing.
- Each `context.run()` step in Workflow is individually retriable.
- `context.sleep()` is durable — persisted across restarts and deploys.

**General**
- Upstash Redis uses REST over HTTPS — each command is an HTTP request,
  so batch with pipelines wherever possible.
- JSON values are auto-serialized/deserialized by `@upstash/redis`.
- `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` are required
  for `Redis.fromEnv()`.
