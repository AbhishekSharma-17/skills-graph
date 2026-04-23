# Cloudflare Workers — Overview & Setup

> Source: [developers.cloudflare.com/workers](https://developers.cloudflare.com/workers/) | Wrangler CLI

## Table of Contents

- [What Are Cloudflare Workers](#what-are-cloudflare-workers)
- [Platform Services](#platform-services)
- [Getting Started](#getting-started)
- [Wrangler CLI](#wrangler-cli)
- [Project Structure](#project-structure)
- [Hello World Worker](#hello-world-worker)
- [Pricing Overview](#pricing-overview)
- [Limits](#limits)

## What Are Cloudflare Workers

Cloudflare Workers is a serverless execution environment that runs JavaScript/TypeScript on Cloudflare's global edge network (300+ cities). Workers use the V8 JavaScript engine (same as Chrome/Node) via the `workerd` runtime — not Node.js, not Deno.

Key characteristics:
- **0ms cold starts** — no container spin-up, V8 isolates boot instantly
- **Global deployment** — code runs in every Cloudflare datacenter
- **Web Standards API** — fetch, Request, Response, Streams, Web Crypto
- **ES modules** — standard `export default { ... }` syntax
- **No servers to manage** — fully serverless, auto-scaling

## Platform Services

Workers integrate with Cloudflare's full developer platform:

| Service | Purpose | Binding |
|---------|---------|---------|
| **KV** | Global key-value store (eventually consistent) | `env.MY_KV` |
| **D1** | SQLite database at the edge | `env.MY_DB` |
| **R2** | S3-compatible object storage (zero egress fees) | `env.MY_BUCKET` |
| **Durable Objects** | Stateful edge compute with storage | `env.MY_DO` |
| **Queues** | Message queue (producer/consumer) | `env.MY_QUEUE` |
| **Workers AI** | ML inference on Cloudflare's GPU network | `env.AI` |
| **Vectorize** | Vector database for embeddings | `env.MY_INDEX` |
| **Hyperdrive** | Connection pooler for external databases | `env.MY_HYPERDRIVE` |
| **Analytics Engine** | Time-series analytics | `env.MY_AE` |
| **Browser Rendering** | Headless Chrome instances | `env.MY_BROWSER` |

## Getting Started

### Prerequisites

- Node.js 16.17.0+
- Cloudflare account (free tier available)

### Create a Project with C3 (create-cloudflare-cli)

```bash
npm create cloudflare@latest my-worker
# Prompts: template selection, TypeScript, git init, deploy

cd my-worker
```

### Or Initialize Manually

```bash
mkdir my-worker && cd my-worker
npm init -y
npm install wrangler --save-dev

# Create wrangler.toml
cat > wrangler.toml << 'EOF'
name = "my-worker"
main = "src/index.ts"
compatibility_date = "2026-04-23"
EOF
```

## Wrangler CLI

Wrangler is the official CLI for building, testing, and deploying Workers.

```bash
npm install -g wrangler    # Global install
npm install wrangler -D    # Project-local (preferred)
```

### Essential Commands

```bash
# Authentication
wrangler login              # OAuth browser flow
wrangler whoami             # Show current user

# Development
wrangler dev                # Local dev server (http://localhost:8787)
wrangler dev --remote       # Dev against real Cloudflare services

# Deployment
wrangler deploy             # Deploy to production
wrangler deploy --dry-run   # Preview without deploying

# Resource Management
wrangler d1 create my-db                 # Create D1 database
wrangler r2 bucket create my-bucket      # Create R2 bucket
wrangler kv namespace create MY_KV       # Create KV namespace
wrangler queues create my-queue          # Create a Queue

# Secrets
wrangler secret put MY_SECRET            # Set a secret (prompted)
wrangler secret list                     # List secrets

# Logs
wrangler tail                            # Stream live logs

# Database
wrangler d1 execute my-db --command "SELECT 1"  # Run SQL
wrangler d1 migrations apply my-db               # Apply migrations
```

## Project Structure

```
my-worker/
├── src/
│   └── index.ts         # Worker entry point
├── wrangler.toml        # Configuration (bindings, env, compat)
├── package.json
├── tsconfig.json
└── test/
    └── index.spec.ts    # Vitest tests
```

### TypeScript Configuration

```jsonc
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "types": ["@cloudflare/workers-types"]
  }
}
```

Install types:

```bash
npm install @cloudflare/workers-types --save-dev
```

## Hello World Worker

```typescript
// src/index.ts
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return new Response("Hello from Cloudflare Workers!");
  },
} satisfies ExportedHandler<Env>;

interface Env {
  // Bindings are typed here
}
```

### Run Locally

```bash
npx wrangler dev
# Server running at http://localhost:8787
```

### Deploy

```bash
npx wrangler deploy
# Published my-worker (https://my-worker.<subdomain>.workers.dev)
```

## Pricing Overview

### Free Plan

| Resource | Limit |
|----------|-------|
| Worker requests | 100,000/day |
| CPU time | 10ms/invocation |
| KV reads | 100,000/day |
| KV writes | 1,000/day |
| KV storage | 1 GB |
| D1 rows read | 5 million/day |
| D1 rows written | 100,000/day |
| D1 storage | 5 GB total |
| Durable Objects requests | 100,000/day |
| R2 storage | 10 GB |
| Queues operations | 10,000/day |

### Paid Plan ($5/month)

| Resource | Included | Overage |
|----------|----------|---------|
| Worker requests | 10M/month | $0.30/million |
| CPU time | 30M ms/month | $0.02/million ms |
| KV reads | 10M/month | $0.50/million |
| KV writes | 1M/month | $5.00/million |
| D1 rows read | 25B/month | $0.001/million |
| D1 rows written | 50M/month | $1.00/million |
| D1 storage | 5 GB | $0.75/GB-mo |
| R2 storage | 10 GB | $0.015/GB-mo |
| R2 egress | Unlimited free | — |
| Queues ops | 1M/month | $0.40/million |

## Limits

| Limit | Free | Paid |
|-------|------|------|
| Script size (compressed) | 1 MB | 10 MB |
| Script size (uncompressed) | 5 MB | 30 MB |
| Environment variables | 64 | 128 |
| CPU time per invocation | 10 ms | 30s (up to 5 min) |
| Subrequests per invocation | 50 | 1,000 |
| KV value size | 25 MB | 25 MB |
| KV key size | 512 bytes | 512 bytes |
| D1 max DB size | 500 MB | 10 GB |
| R2 object size | 5 GB | 5 GB |

## Common Pitfalls

- **Not Node.js** — `fs`, `path`, `child_process` don't exist. Use Web APIs instead.
- **CPU vs wall-clock time** — Billing uses CPU time, not total request duration. Awaiting `fetch()` doesn't count as CPU time.
- **Compatibility dates** — Always set `compatibility_date` to the current date when starting a new project. This opts into the latest runtime behavior.
- **Local vs remote dev** — `wrangler dev` runs locally with Miniflare. Add `--remote` to test against real Cloudflare services.
- **Types package** — Always install `@cloudflare/workers-types` for proper TypeScript support.
