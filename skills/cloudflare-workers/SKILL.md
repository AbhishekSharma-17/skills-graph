---
name: cloudflare-workers
description: "Cloudflare Workers edge computing platform with D1, R2, KV, Durable Objects, Queues, and Workers AI. MANDATORY TRIGGERS: cloudflare workers, cloudflare worker, wrangler, cloudflare d1, cloudflare r2, cloudflare kv, durable objects, workers ai, cloudflare queues, cloudflare pages functions, WorkerEntrypoint, miniflare. Also trigger when user wants to deploy serverless functions to Cloudflare edge, build full-stack apps on Cloudflare, use SQLite at the edge, store objects with S3-compatible API, or run AI models on Cloudflare. When in doubt about whether to use this skill for edge computing or Cloudflare tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["cloudflare", "workers", "edge-computing", "serverless", "d1", "r2", "kv", "durable-objects", "queues", "workers-ai", "wrangler"]
---

# Cloudflare Workers — Skill Router

> Build full-stack applications on Cloudflare's global edge network — serverless compute, databases, storage, queues, and AI in one platform.

**Source:** [developers.cloudflare.com](https://developers.cloudflare.com/workers/) | **CLI:** `wrangler` | **License:** BSD-3-Clause

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, Wrangler CLI, project scaffolding, C3, deployment |
| **Workers Fundamentals** | `references/01-workers-fundamentals.md` | Fetch handler, Request/Response, ExecutionContext, routing, env bindings |
| **Configuration** | `references/02-configuration.md` | wrangler.toml / wrangler.jsonc, bindings, compatibility dates, environments |
| **KV Storage** | `references/03-kv-storage.md` | Key-value store: get, put, delete, list, metadata, TTL, caching |
| **D1 Database** | `references/04-d1-database.md` | SQLite database: prepare, batch, exec, migrations, sessions, Time Travel |
| **R2 Object Storage** | `references/05-r2-object-storage.md` | S3-compatible storage: get, put, delete, list, multipart uploads |
| **Durable Objects** | `references/06-durable-objects.md` | Stateful edge compute: storage, alarms, WebSocket hibernation, SQL |
| **Queues** | `references/07-queues.md` | Message queues: producer/consumer, batching, retries, dead-letter |
| **Workers AI** | `references/08-workers-ai.md` | AI inference: text generation, embeddings, image, speech, Vectorize |
| **Service Bindings & RPC** | `references/09-service-bindings-rpc.md` | Inter-Worker communication, WorkerEntrypoint, named entrypoints, RPC |
| **Pages & Static Assets** | `references/10-pages-static-assets.md` | Pages Functions, static assets, _routes.json, middleware |
| **Testing** | `references/11-testing.md` | Vitest integration, @cloudflare/vitest-pool-workers, Miniflare |
| **Deployment & CI/CD** | `references/12-deployment-cicd.md` | wrangler deploy, environments, secrets, GitHub Actions, rollbacks |

## Installation

```bash
# Create a new Workers project
npm create cloudflare@latest my-app

# Or install Wrangler globally
npm install -g wrangler

# Login to Cloudflare
wrangler login
```

## Quick Reference

- **Docs:** https://developers.cloudflare.com/workers/
- **GitHub:** https://github.com/cloudflare/workers-sdk
- **npm:** https://www.npmjs.com/package/wrangler
- **Discord:** https://discord.cloudflare.com
