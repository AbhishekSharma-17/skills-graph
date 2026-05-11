# Upstash — Serverless Data Platform Overview

## Table of Contents

- [Products Overview](#products-overview)
- [When to Use Upstash](#when-to-use-upstash)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [AI Agent Quick Database](#ai-agent-quick-database)
- [Architecture](#architecture)
- [Pricing Model](#pricing-model)
- [Common Pitfalls](#common-pitfalls)

---

Upstash is a serverless data platform built for modern cloud architectures. Every service communicates over HTTP/REST, eliminating the need for persistent TCP connections, connection pools, or long-lived sockets. This makes Upstash uniquely suited to serverless functions, edge runtimes, and environments where traditional databases struggle.

All services follow a pay-per-request pricing model and scale to zero when idle, so you only pay for what you use.

## Products Overview

Upstash provides six core products:

- **Redis** — Serverless Redis compatible with 200+ commands. Offers a REST API alongside optional TCP access, global replication across multiple regions, and sub-millisecond latency. Ideal for caching, session management, rate limiting, and real-time leaderboards.

- **QStash** — An HTTP-based message queue and task scheduler. Supports scheduled messages, automatic retries with exponential backoff, dead letter queues (DLQ), callbacks, and batch publishing. No infrastructure to manage.

- **Workflow** — Durable serverless function orchestration. Automatically retries failed steps, supports long delays (hours or days) between steps, parallel execution, and human-in-the-loop patterns. Built on top of QStash.

- **Vector** — Serverless vector database with built-in embedding models (no external embedding API needed). Supports metadata filtering, hybrid search (combining vector similarity with keyword matching), and namespaces for multi-tenant isolation.

- **Search** — Lightweight AI-powered full-text search engine. Supports typo tolerance, faceted search, and relevance tuning. Designed as a simpler alternative to Elasticsearch for common use cases.

- **Realtime** — Channel-based publish/subscribe messaging over HTTP and WebSockets. Supports presence detection and message history.

> **Note:** Upstash Kafka was deprecated in 2024. Existing Kafka workloads should migrate to QStash for messaging and Workflow for orchestration.

## When to Use Upstash

Upstash is the right choice when:

- You run on **serverless platforms** (AWS Lambda, Vercel Serverless Functions, Cloudflare Workers, Netlify Functions) and need data services that match the serverless model.
- You deploy to **edge runtimes** (Vercel Edge, Cloudflare Workers, Deno Deploy) where TCP connections are unavailable or unreliable.
- You need **Redis** but want to avoid connection pooling complexity, idle connection costs, and cold start issues.
- You need **background job processing** without managing a message broker or worker infrastructure.
- You are building **AI/RAG applications** and need vector search with built-in embeddings, without running a separate embedding service.
- You want **zero operational overhead** — no provisioning, patching, scaling, or capacity planning.

## Quick Start

### 1. Create a Database

Go to [https://console.upstash.com](https://console.upstash.com), create an account, and create a new Redis database. Choose your preferred region and optional read replicas.

### 2. Get Credentials

After creating the database, copy two values from the dashboard:

- `UPSTASH_REDIS_REST_URL` — the HTTPS endpoint for your database
- `UPSTASH_REDIS_REST_TOKEN` — the authentication token

### 3. TypeScript Quick Start

```typescript
import { Redis } from "@upstash/redis";

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

// Basic operations
await redis.set("user:1:name", "Alice");
const name = await redis.get("user:1:name");
console.log(name); // "Alice"

// JSON objects are auto-serialized
await redis.set("user:1", { name: "Alice", score: 100 });
const user = await redis.get<{ name: string; score: number }>("user:1");
console.log(user?.name); // "Alice"

// Expiration
await redis.set("session:abc", "data", { ex: 3600 }); // expires in 1 hour
```

### 4. Python Quick Start

```python
from upstash_redis import Redis

redis = Redis(
    url="https://...",  # or os.environ["UPSTASH_REDIS_REST_URL"]
    token="...",        # or os.environ["UPSTASH_REDIS_REST_TOKEN"]
)

# Basic operations
redis.set("user:1:name", "Alice")
name = redis.get("user:1:name")
print(name)  # "Alice"

# With expiration
redis.set("session:abc", "data", ex=3600)

# Hash operations
redis.hset("user:2", {"name": "Bob", "score": "200"})
user = redis.hgetall("user:2")
print(user)  # {"name": "Bob", "score": "200"}
```

### 5. REST API (No SDK Needed)

```bash
curl -X POST https://YOUR_ENDPOINT.upstash.io \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '["SET", "key", "value"]'
```

## Environment Variables

### Redis
```
UPSTASH_REDIS_REST_URL=https://<database>.upstash.io
UPSTASH_REDIS_REST_TOKEN=<token>
```

### QStash
```
QSTASH_TOKEN=<token>
QSTASH_CURRENT_SIGNING_KEY=<key>
QSTASH_NEXT_SIGNING_KEY=<key>
```

### Vector
```
UPSTASH_VECTOR_REST_URL=https://<index>.upstash.io
UPSTASH_VECTOR_REST_TOKEN=<token>
```

### Workflow
Workflow uses QStash credentials plus your application URL:
```
QSTASH_TOKEN=<token>
UPSTASH_WORKFLOW_URL=https://your-app.com/api/workflow
```

## Installation

### JavaScript / TypeScript (npm)

```bash
# Redis
npm install @upstash/redis

# QStash
npm install @upstash/qstash

# Workflow
npm install @upstash/workflow

# Vector
npm install @upstash/vector

# Rate Limiting (built on Redis)
npm install @upstash/ratelimit
```

### Python (pip / uv)

```bash
# Redis
pip install upstash-redis

# QStash
pip install qstash-py

# Vector
pip install upstash-vector

# Rate Limiting
pip install upstash-ratelimit
```

## AI Agent Quick Database

Upstash provides a special endpoint for AI agents and development tools that creates a free temporary Redis database with no signup required:

```bash
curl -X POST https://upstash.com/start-redis
```

This returns a JSON response with `url` and `token` fields. The database expires after 72 hours. This is useful for:

- AI agents that need scratch storage during a session
- Quick prototyping without creating an account
- CI/CD pipelines that need ephemeral Redis
- Demos and tutorials

```typescript
// Example: AI agent creating its own database
const res = await fetch("https://upstash.com/start-redis", { method: "POST" });
const { url, token } = await res.json();
const redis = new Redis({ url, token });
await redis.set("agent:state", JSON.stringify({ step: 1, context: "..." }));
```

## Architecture

### HTTP/REST Foundation

Every Upstash SDK communicates over HTTP/REST. There are no persistent TCP connections to manage:

```
Your App  --HTTP-->  Upstash Edge  --internal-->  Upstash Storage
```

This architecture provides several advantages:

- **No connection pooling** — each request is independent, no pool exhaustion
- **Edge compatible** — works in any runtime that supports `fetch()`
- **No cold start penalty** — no connection establishment overhead
- **Auto-retry** — SDKs include built-in retry logic with exponential backoff

### Auto-Serialization

JavaScript/TypeScript SDKs automatically serialize and deserialize JSON:

```typescript
// Objects are serialized to JSON transparently
await redis.set("config", { maxRetries: 3, timeout: 5000 });

// Retrieved as typed objects
const config = await redis.get<{ maxRetries: number; timeout: number }>("config");
// config.maxRetries === 3
```

### Platform Compatibility

Upstash SDKs work across all modern runtimes:

| Runtime              | Support |
|----------------------|---------|
| Node.js              | Full    |
| Deno                 | Full    |
| Bun                  | Full    |
| Cloudflare Workers   | Full    |
| Vercel Edge          | Full    |
| Vercel Serverless    | Full    |
| AWS Lambda           | Full    |
| Fastly Compute       | Full    |
| Netlify Edge/Functions| Full   |
| Browser (client-side)| Redis read-only recommended |

## Pricing Model

All Upstash products follow a consumption-based pricing model:

- **Free Tier** — available for every product. Redis free tier includes 10,000 commands/day. Vector free tier includes 10,000 query/day with a single index.
- **Pay-as-you-go** — billed per request (command, message, query). No minimum commitments.
- **Pro Plans** — higher limits, priority support, advanced features like global replication, larger storage, and enhanced SLAs.
- **Fixed Plans** — predictable monthly pricing for teams that want cost certainty.

There are no charges when services are idle. Scale to zero is a core design principle.

## Common Pitfalls

### Eventual Consistency with Read Replicas

When using global replication, read replicas are eventually consistent. A write to the primary region may take a few milliseconds to propagate. If you need strong consistency, read from the primary region:

```typescript
const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
  readYourWrites: true,  // forces reads from primary after writes
});
```

### REST Latency Overhead

The HTTP/REST protocol adds approximately 1-2ms of overhead compared to raw TCP Redis. This is negligible for serverless workloads where connection establishment alone costs 5-50ms with traditional Redis. Do not micro-optimize for this difference.

### Request Body Size Limits

- **QStash**: default maximum request body is 1MB, configurable up to 10MB on Pro plans
- **Redis**: maximum value size is 256MB, but practical limit for REST is lower due to HTTP overhead
- **Vector**: embedding dimensions are configured at index creation and cannot be changed

### Do Not Use Connection Pooling

Upstash REST clients are stateless. Using connection pooling libraries (like `ioredis` pools or `generic-pool`) provides no benefit and may cause issues:

```typescript
// WRONG: Do not pool Upstash clients
const pool = createPool(() => new Redis({ url, token }), { max: 10 });

// RIGHT: Create a single client, reuse it
const redis = new Redis({ url, token });
// Each call is an independent HTTP request — no connection to pool
```

### Pipeline and Transaction Limits

Pipelines and transactions batch multiple commands into a single HTTP request. Keep batches reasonable:

```typescript
const pipeline = redis.pipeline();
// Add commands — aim for under 1000 per pipeline
pipeline.set("a", 1);
pipeline.set("b", 2);
pipeline.incr("counter");
const results = await pipeline.exec();
```

### Type Safety in TypeScript

Always use generics when reading data to maintain type safety:

```typescript
// Without generics — returns unknown
const data = await redis.get("user:1");

// With generics — returns typed object
interface User {
  name: string;
  email: string;
}
const user = await redis.get<User>("user:1");
```

### Environment Variable Naming

Use the exact variable names that Upstash SDKs expect. The SDKs auto-detect these environment variables when no explicit configuration is provided:

```typescript
// When env vars are set correctly, no config needed
const redis = Redis.fromEnv();
const qstash = new Client(); // reads QSTASH_TOKEN automatically
```
