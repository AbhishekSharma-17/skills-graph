---
name: upstash
description: "Serverless data platform with Redis, QStash messaging, Workflow orchestration, and Vector database — all over HTTP. MANDATORY TRIGGERS: Upstash, upstash-redis, @upstash/redis, QStash, @upstash/qstash, Upstash Vector, @upstash/vector, @upstash/ratelimit, @upstash/workflow, serverless Redis. Also trigger when user needs HTTP-based Redis for edge/serverless, rate limiting for serverless, durable workflow steps, serverless message queues, or vector search without connection pooling. When in doubt about whether to use this skill for serverless data tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["serverless", "redis", "messaging", "vector-database", "rate-limiting", "workflow", "edge-computing"]
---

# Upstash — Serverless Data Platform

> **Version:** @upstash/redis 1.38.0, upstash-redis (Python) 1.7.0 | **Source:** https://upstash.com/docs

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview** | `references/00-overview.md` | "what is Upstash", "getting started", "which Upstash product" |
| **Redis SDK (TypeScript)** | `references/01-redis-sdk-typescript.md` | "@upstash/redis", "TypeScript Redis", "Redis SDK setup" |
| **Redis Commands** | `references/02-redis-commands.md` | "Redis command", "strings", "hashes", "sorted sets", "JSON", "streams" |
| **Redis REST API** | `references/03-redis-rest-api.md` | "REST API", "HTTP Redis", "pipeline API", "transaction API" |
| **Rate Limiting** | `references/04-rate-limiting.md` | "@upstash/ratelimit", "rate limit", "sliding window", "token bucket" |
| **QStash Messaging** | `references/05-qstash-messaging.md` | "QStash", "message queue", "scheduling", "background jobs", "DLQ" |
| **Workflow** | `references/06-workflow.md` | "@upstash/workflow", "durable functions", "workflow steps", "context.run" |
| **Vector Database** | `references/07-vector-database.md` | "Upstash Vector", "vector search", "embeddings", "similarity" |
| **Python SDKs** | `references/08-python-sdks.md` | "upstash-redis Python", "Python SDK", "qstash Python", "upstash-vector" |
| **Framework Integrations** | `references/09-framework-integrations.md` | "Next.js Upstash", "Cloudflare Workers", "Vercel", "AWS Lambda" |
| **Patterns & Recipes** | `references/10-patterns-recipes.md` | "caching pattern", "session store", "leaderboard", "pub/sub", "best practices" |
| **Search & Realtime** | `references/11-search-realtime.md` | "Upstash Search", "Realtime", "full-text search", "channels" |

## Installation

```bash
npm install @upstash/redis          # Redis SDK
npm install @upstash/ratelimit      # Rate limiting
npm install @upstash/qstash         # QStash messaging
npm install @upstash/workflow       # Durable workflows
npm install @upstash/vector         # Vector database
pip install upstash-redis           # Python Redis SDK
```

## Quick Reference

- **Docs:** https://upstash.com/docs
- **Console:** https://console.upstash.com
- **GitHub:** https://github.com/upstash
