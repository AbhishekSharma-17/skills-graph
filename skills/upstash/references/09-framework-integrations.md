# Upstash — Framework Integrations

Upstash Redis uses HTTP/REST, making it compatible with every JavaScript runtime and serverless platform without TCP connections or connection pooling.

## Table of Contents

- [Next.js](#nextjs)
- [Vercel Edge Functions](#vercel-edge-functions)
- [Cloudflare Workers](#cloudflare-workers)
- [AWS Lambda](#aws-lambda)
- [Hono](#hono)
- [Deno / Deno Deploy](#deno--deno-deploy)
- [Express.js](#expressjs)
- [FastAPI (Python)](#fastapi-python)
- [SvelteKit](#sveltekit)
- [Astro](#astro)
- [BullMQ Integration](#bullmq-integration)
- [Vercel Integration (One-Click)](#vercel-integration-one-click)
- [Terraform / Pulumi](#terraform--pulumi)
- [Common Pitfalls](#common-pitfalls)

## Next.js

### App Router Setup

```typescript
// app/api/route.ts
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();

export async function GET() {
  const visits = await redis.incr("page-visits");
  return Response.json({ visits });
}
```

`Redis.fromEnv()` reads `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` from `process.env`.

### Rate Limiting Middleware

```typescript
// middleware.ts
import { NextRequest, NextResponse } from "next/server";
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "10 s"),
  analytics: true,
});

export const config = { matcher: "/api/:path*" };

export async function middleware(request: NextRequest) {
  const ip = request.headers.get("x-forwarded-for") ?? "127.0.0.1";
  const { success, limit, reset, remaining } = await ratelimit.limit(ip);

  if (!success) {
    return new NextResponse("Too Many Requests", {
      status: 429,
      headers: {
        "X-RateLimit-Limit": limit.toString(),
        "X-RateLimit-Remaining": remaining.toString(),
        "X-RateLimit-Reset": reset.toString(),
      },
    });
  }
  return NextResponse.next();
}
```

### Session Storage

```typescript
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();

export async function getSession(sessionId: string) {
  return redis.get<Session>(`session:${sessionId}`);
}

export async function setSession(sessionId: string, data: Session) {
  await redis.set(`session:${sessionId}`, data, { ex: 86400 });
}

export async function deleteSession(sessionId: string) {
  await redis.del(`session:${sessionId}`);
}
```

### Server Actions with Caching

```typescript
"use server";
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();

export async function getProducts() {
  const cached = await redis.get<Product[]>("products:all");
  if (cached) return cached;

  const products = await db.query("SELECT * FROM products");
  await redis.set("products:all", products, { ex: 300 });
  return products;
}
```

## Vercel Edge Functions

```typescript
import { Redis } from "@upstash/redis";

export const config = { runtime: "edge" };

export default async function handler(req: Request) {
  const redis = Redis.fromEnv();
  const count = await redis.incr("edge-visits");
  return new Response(JSON.stringify({ count }));
}
```

Environment variables are set in Vercel dashboard or auto-provisioned via the Upstash Vercel Integration.

## Cloudflare Workers

Must use the `/cloudflare` import path:

```typescript
import { Redis } from "@upstash/redis/cloudflare";

interface Env {
  UPSTASH_REDIS_REST_URL: string;
  UPSTASH_REDIS_REST_TOKEN: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const redis = Redis.fromEnv(env);
    const data = await redis.get("key");
    return new Response(JSON.stringify(data));
  },
};
```

Environment variables are set in `wrangler.toml` or Workers dashboard. For secrets, use `wrangler secret put`.

### Cloudflare Workers with Rate Limiting

```typescript
import { Redis } from "@upstash/redis/cloudflare";
import { Ratelimit } from "@upstash/ratelimit";

export default {
  async fetch(request: Request, env: Env, context: ExecutionContext): Promise<Response> {
    const redis = Redis.fromEnv(env);
    const ratelimit = new Ratelimit({
      redis,
      limiter: Ratelimit.slidingWindow(10, "10 s"),
      analytics: true,
    });

    const ip = request.headers.get("cf-connecting-ip") ?? "unknown";
    const { success, pending } = await ratelimit.limit(ip);
    context.waitUntil(pending); // Don't block response for analytics

    if (!success) return new Response("Rate limited", { status: 429 });
    return new Response("OK");
  },
};
```

## AWS Lambda

```typescript
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv(); // Outside handler for reuse

export const handler = async (event: any) => {
  await redis.set("lambda-key", "value");
  const result = await redis.get("lambda-key");
  return {
    statusCode: 200,
    body: JSON.stringify({ result }),
  };
};
```

Cold starts are minimal — HTTP-based, no connection pool to warm up.

### Python Lambda

```python
from upstash_redis import Redis

redis = Redis.from_env()

def handler(event, context):
    redis.set("key", "value")
    return {"statusCode": 200, "body": redis.get("key")}
```

## Hono

```typescript
import { Hono } from "hono";
import { Redis } from "@upstash/redis/cloudflare";

const app = new Hono<{ Bindings: { UPSTASH_REDIS_REST_URL: string; UPSTASH_REDIS_REST_TOKEN: string } }>();

app.get("/api/data", async (c) => {
  const redis = Redis.fromEnv(c.env);
  const data = await redis.get("key");
  return c.json({ data });
});

export default app;
```

When deploying Hono to Node.js or Bun, use `@upstash/redis` instead of `/cloudflare`.

## Deno / Deno Deploy

```typescript
import { Redis } from "https://deno.land/x/upstash_redis/mod.ts";

const redis = new Redis({
  url: Deno.env.get("UPSTASH_REDIS_REST_URL")!,
  token: Deno.env.get("UPSTASH_REDIS_REST_TOKEN")!,
});

Deno.serve(async () => {
  const visits = await redis.incr("visits");
  return new Response(`Visits: ${visits}`);
});
```

## Express.js

```typescript
import express from "express";
import { Redis } from "@upstash/redis";

const app = express();
const redis = Redis.fromEnv();

app.get("/api/data", async (req, res) => {
  const cached = await redis.get("data");
  if (cached) return res.json(cached);

  const data = await fetchExpensiveData();
  await redis.set("data", data, { ex: 3600 });
  res.json(data);
});
```

## FastAPI (Python)

```python
from fastapi import FastAPI, Request, HTTPException
from upstash_redis import Redis
from upstash_ratelimit import Ratelimit, SlidingWindow

app = FastAPI()
redis = Redis.from_env()
ratelimit = Ratelimit(
    redis=redis,
    limiter=SlidingWindow(max_requests=10, window=60),
)

@app.get("/api/data")
async def get_data(request: Request):
    ip = request.client.host
    response = ratelimit.limit(ip)
    if not response.allowed:
        raise HTTPException(status_code=429, detail="Rate limited")

    cached = redis.get("data")
    if cached:
        return cached

    data = fetch_data()
    redis.set("data", data, ex=3600)
    return data
```

Install: `pip install upstash-redis upstash-ratelimit`

## SvelteKit

```typescript
// src/routes/api/data/+server.ts
import { Redis } from "@upstash/redis";
import { json } from "@sveltejs/kit";
import { UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN } from "$env/static/private";

const redis = new Redis({
  url: UPSTASH_REDIS_REST_URL,
  token: UPSTASH_REDIS_REST_TOKEN,
});

export async function GET() {
  const cached = await redis.get("svelte-data");
  if (cached) return json(cached);

  const data = await fetchFromDatabase();
  await redis.set("svelte-data", data, { ex: 300 });
  return json(data);
}
```

SvelteKit uses `$env/static/private` for server-side env vars, validated at build time and never exposed to the client.

## Astro

Requires `output: "server"` or `output: "hybrid"` in `astro.config.mjs`:

```typescript
// src/pages/api/visits.ts
import type { APIRoute } from "astro";
import { Redis } from "@upstash/redis";

const redis = new Redis({
  url: import.meta.env.UPSTASH_REDIS_REST_URL,
  token: import.meta.env.UPSTASH_REDIS_REST_TOKEN,
});

export const GET: APIRoute = async () => {
  const visits = await redis.incr("astro-visits");
  return new Response(JSON.stringify({ visits }));
};
```

## BullMQ Integration

BullMQ requires a TCP connection, not HTTP REST. Use `ioredis` with the Upstash TCP endpoint:

```typescript
import { Redis as IORedis } from "ioredis";
import { Queue, Worker } from "bullmq";

// TCP endpoint: rediss://default:<password>@<host>:<port>
const connection = new IORedis(process.env.UPSTASH_REDIS_URL!, {
  maxRetriesPerRequest: null, // Required by BullMQ
  tls: {},                    // Upstash requires TLS
});

const queue = new Queue("tasks", { connection });
const worker = new Worker("tasks", async (job) => {
  // process job
}, { connection });
```

The TCP endpoint URL is in the Upstash Console under database details. Note `rediss://` (double s) for TLS.

## Vercel Integration (One-Click)

1. Navigate to Vercel Marketplace and find Upstash Redis
2. Click **Add Integration** and select your project
3. Upstash automatically provisions a Redis database
4. `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` are auto-injected

After installation, `Redis.fromEnv()` works immediately without manual configuration.

## Terraform / Pulumi

### Terraform

```hcl
resource "upstash_redis_database" "main" {
  database_name = "my-app"
  region        = "us-east-1"
  tls           = true
}

output "redis_url" {
  value     = upstash_redis_database.main.endpoint
  sensitive = true
}

output "redis_token" {
  value     = upstash_redis_database.main.rest_token
  sensitive = true
}
```

### Pulumi

```typescript
import * as upstash from "@upstash/pulumi";

const db = new upstash.RedisDatabase("main", {
  databaseName: "my-app",
  region: "us-east-1",
  tls: true,
});

export const redisUrl = db.endpoint;
export const redisToken = db.restToken;
```

## Common Pitfalls

**Import paths** — Cloudflare Workers must use `@upstash/redis/cloudflare`. The standard import uses Node.js `fetch` unavailable in Workers. Deno uses `https://deno.land/x/upstash_redis/mod.ts`.

**Environment variable names** — The SDK expects exactly `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`. Using `UPSTASH_REDIS_URL` (missing `_REST_`) points to the TCP endpoint, not HTTP.

**Client initialization** — Always initialize outside the handler for reuse across warm invocations. Creating a new client per request adds unnecessary overhead.

**Edge runtime limitations** — Vercel Edge Functions cannot use TCP. Only HTTP-based libraries work. Other Redis clients (`ioredis`, `node-redis`) will fail in edge runtimes.

**BullMQ requires TCP** — BullMQ cannot use HTTP REST. Connect via `ioredis` with the Upstash TCP endpoint and set `maxRetriesPerRequest: null`.

**Rate limiting pending promise** — Always handle the `pending` promise from `ratelimit.limit()`. In Cloudflare Workers use `context.waitUntil(pending)`. Failing to handle it drops analytics data.

**Cloudflare Workers env binding** — Workers pass env vars via the `env` parameter, not `process.env`. Use `Redis.fromEnv(env)` with the argument — `Redis.fromEnv()` without it will fail.
