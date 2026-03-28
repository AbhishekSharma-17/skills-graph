# Hono — Overview & Setup

> Source: [hono.dev](https://hono.dev) | Version: 4.12.0

## What is Hono?

Hono (meaning "flame" in Japanese) is a small, simple, and ultrafast web framework built on Web Standards. It runs on any JavaScript runtime:

- **Cloudflare Workers** — Edge compute on Cloudflare's CDN
- **Deno** — Secure JavaScript/TypeScript runtime
- **Bun** — Fast all-in-one JavaScript runtime
- **Node.js** — Via `@hono/node-server` adapter
- **Fastly Compute** — Edge compute on Fastly
- **AWS Lambda** — Serverless compute
- **Lambda@Edge** — CloudFront edge functions
- **Vercel** — Serverless/edge functions

The same code runs on all platforms with zero or minimal changes.

## Key Features

- **Ultrafast** — RegExpRouter doesn't use linear loops, making it one of the fastest routers
- **Tiny** — `hono/tiny` preset is under 14kB
- **Web Standards** — Built on `Request`, `Response`, and `fetch` — no proprietary APIs
- **First-class TypeScript** — Full type inference for routes, params, validators, and RPC
- **Rich middleware** — Built-in CORS, JWT, logger, compress, etag, and more
- **Multi-runtime** — Write once, deploy anywhere
- **JSX support** — Server-side rendering without React
- **RPC client** — End-to-end type safety between server and client

## Installation

### Create a New Project (Recommended)

```bash
npm create hono@latest my-app
```

Select your target runtime during project creation:
- `cloudflare-workers`
- `cloudflare-pages`
- `deno`
- `bun`
- `nodejs`
- `vercel`
- `aws-lambda`
- `fastly`

### Manual Installation

```bash
# Core package
npm install hono

# For Node.js (required adapter)
npm install @hono/node-server

# Common extras
npm install @hono/zod-validator zod  # Validation
npm install @hono/swagger-ui         # OpenAPI docs
```

### Package Managers

```bash
# npm
npm install hono

# yarn
yarn add hono

# pnpm
pnpm add hono

# bun
bun add hono
```

## Quickstart

### Minimal Example

```typescript
import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => {
  return c.text('Hello Hono!')
})

export default app
```

### Node.js

```typescript
import { Hono } from 'hono'
import { serve } from '@hono/node-server'

const app = new Hono()

app.get('/', (c) => c.text('Hello Node.js!'))

serve(app, (info) => {
  console.log(`Server running at http://localhost:${info.port}`)
})
```

### Cloudflare Workers

```typescript
import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => c.text('Hello Cloudflare Workers!'))

export default app
```

### Bun

```typescript
import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => c.text('Hello Bun!'))

export default app
```

### Deno

```typescript
import { Hono } from 'npm:hono'

const app = new Hono()

app.get('/', (c) => c.text('Hello Deno!'))

Deno.serve(app.fetch)
```

## TypeScript Configuration

For JSX support, update `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "jsxImportSource": "hono/jsx",
    "strict": true
  }
}
```

## Hono Stacks

Hono is the center of the "Hono Stacks" ecosystem:

- **Server** — Hono framework for API/server logic
- **Validator** — Zod + `@hono/zod-validator` for request validation
- **RPC** — `hc` client for end-to-end type-safe API calls
- **Client** — Any frontend framework (React, Vue, SolidJS, etc.)

This stack gives you full type safety from database to UI without code generation.

## Comparison with Other Frameworks

| Feature | Hono | Express | Fastify |
|---------|------|---------|---------|
| Runtime | Multi-runtime | Node.js only | Node.js only |
| TypeScript | First-class | Bolted on | Good |
| Size | ~14kB | ~200kB | ~100kB |
| Web Standards | Yes | No | No |
| Edge support | Native | No | No |
| Built-in middleware | Yes | Separate | Plugins |
| RPC client | Yes | No | No |

## Common Pitfalls

1. **Forgetting `@hono/node-server`** — Hono doesn't include a Node.js server by default; install the adapter
2. **Using Express patterns** — Hono uses Web Standard `Request`/`Response`, not `req`/`res` objects
3. **Not chaining routes for RPC** — The RPC client needs chained method calls to infer types correctly
4. **Importing from wrong path** — Use `hono/cors` not `@hono/cors` for built-in middleware
