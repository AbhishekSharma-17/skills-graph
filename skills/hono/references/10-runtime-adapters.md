# Hono — Runtime Adapters

> Source: [hono.dev/docs/getting-started](https://hono.dev/docs/getting-started)

## Table of Contents

- [Node.js](#nodejs)
- [Cloudflare Workers](#cloudflare-workers)
- [Cloudflare Pages](#cloudflare-pages)
- [Bun](#bun)
- [Deno](#deno)
- [AWS Lambda](#aws-lambda)
- [Vercel](#vercel)
- [Static Files](#static-files)
- [Common Pitfalls](#common-pitfalls)

## Node.js

Requires the `@hono/node-server` adapter (Node.js 18.14.1+).

### Installation

```bash
npm install hono @hono/node-server
```

### Basic Server

```typescript
import { Hono } from 'hono'
import { serve } from '@hono/node-server'

const app = new Hono()

app.get('/', (c) => c.text('Hello Node.js!'))

serve(app, (info) => {
  console.log(`Listening on http://localhost:${info.port}`)
})
```

### Custom Port

```typescript
serve({
  fetch: app.fetch,
  port: 3000,
})
```

### Graceful Shutdown

```typescript
const server = serve(app)

const shutdown = () => {
  server.close(() => {
    console.log('Server closed')
    process.exit(0)
  })
}

process.on('SIGINT', shutdown)
process.on('SIGTERM', shutdown)
```

### Accessing Node.js APIs

```typescript
import type { HttpBindings } from '@hono/node-server'

const app = new Hono<{ Bindings: HttpBindings }>()

app.get('/', (c) => {
  const address = c.env.incoming.socket.remoteAddress
  return c.text(`Your IP: ${address}`)
})
```

### HTTP/2 Support

```typescript
import { createSecureServer } from 'node:http2'
import { readFileSync } from 'node:fs'

serve({
  fetch: app.fetch,
  createServer: createSecureServer,
  serverOptions: {
    key: readFileSync('localhost-key.pem'),
    cert: readFileSync('localhost-cert.pem'),
  },
})
```

## Cloudflare Workers

Hono's native runtime — no adapter needed.

### Project Setup

```bash
npm create hono@latest my-app
# Select: cloudflare-workers
```

### wrangler.toml

```toml
name = "my-hono-app"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[vars]
MY_VARIABLE = "production_value"
```

### Environment Bindings

```typescript
type Bindings = {
  MY_VARIABLE: string
  MY_KV: KVNamespace
  MY_BUCKET: R2Bucket
  MY_DB: D1Database
  MY_DO: DurableObjectNamespace
}

const app = new Hono<{ Bindings: Bindings }>()

app.get('/', (c) => {
  const value = c.env.MY_VARIABLE
  return c.text(value)
})
```

### KV Storage

```typescript
app.get('/kv/:key', async (c) => {
  const key = c.req.param('key')
  const value = await c.env.MY_KV.get(key)
  if (!value) return c.notFound()
  return c.text(value)
})

app.put('/kv/:key', async (c) => {
  const key = c.req.param('key')
  const value = await c.req.text()
  await c.env.MY_KV.put(key, value)
  return c.text('OK')
})
```

### Local Development

```bash
# Uses wrangler dev server
npm run dev

# Create .dev.vars for local env variables
echo 'API_KEY=dev-key-123' > .dev.vars
```

### Deploy

```bash
npx wrangler deploy
```

## Cloudflare Pages

Use the `hono/cloudflare-pages` adapter:

```typescript
// functions/api/[[route]].ts
import { Hono } from 'hono'
import { handle } from 'hono/cloudflare-pages'

const app = new Hono().basePath('/api')

app.get('/hello', (c) => c.json({ message: 'Hello from Pages!' }))

export const onRequest = handle(app)
```

## Bun

Hono works natively with Bun — no adapter needed.

### Installation

```bash
bun create hono@latest my-app
# Or manually:
bun add hono
```

### Server

```typescript
import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => c.text('Hello Bun!'))

export default app
// Bun automatically serves the default export
```

### Custom Port

```typescript
export default {
  port: 3000,
  fetch: app.fetch,
}
```

### Bun-Specific APIs

```typescript
app.get('/file', async (c) => {
  const file = Bun.file('./data.json')
  const data = await file.json()
  return c.json(data)
})
```

## Deno

### Installation

```typescript
// No install needed — import from npm
import { Hono } from 'npm:hono'
```

### Server

```typescript
import { Hono } from 'npm:hono'

const app = new Hono()

app.get('/', (c) => c.text('Hello Deno!'))

Deno.serve(app.fetch)
```

### Custom Port

```typescript
Deno.serve({ port: 8000 }, app.fetch)
```

### Deno Deploy

```bash
# Install deployctl
deno install -Arf jsr:@deno/deployctl

# Deploy
deployctl deploy --project=my-project src/index.ts
```

## AWS Lambda

Use the `hono/aws-lambda` adapter:

```typescript
import { Hono } from 'hono'
import { handle } from 'hono/aws-lambda'

const app = new Hono()

app.get('/', (c) => c.text('Hello Lambda!'))

export const handler = handle(app)
```

### Lambda@Edge

```typescript
import { handle } from 'hono/lambda-edge'

export const handler = handle(app)
```

### With API Gateway Event

```typescript
import type { LambdaEvent } from 'hono/aws-lambda'

app.get('/', (c) => {
  const event = c.env.event as LambdaEvent
  return c.json({
    requestContext: event.requestContext,
  })
})
```

## Vercel

### Edge Functions

```typescript
import { Hono } from 'hono'
import { handle } from 'hono/vercel'

const app = new Hono().basePath('/api')

app.get('/hello', (c) => c.json({ message: 'Hello Vercel!' }))

export const GET = handle(app)
export const POST = handle(app)
```

### Serverless Functions

```typescript
import { handle } from '@hono/node-server/vercel'

export default handle(app)
```

## Static Files

### Node.js

```typescript
import { serveStatic } from '@hono/node-server/serve-static'

app.use('/static/*', serveStatic({ root: './public' }))

// Serve a single file
app.get('/favicon.ico', serveStatic({ path: './public/favicon.ico' }))

// Rewrite paths
app.use('/assets/*', serveStatic({
  root: './dist',
  rewriteRequestPath: (path) => path.replace(/^\/assets/, ''),
}))
```

### Cloudflare Workers

```typescript
import { serveStatic } from 'hono/cloudflare-workers'

app.use('/static/*', serveStatic({ root: './' }))
```

### Bun

```typescript
import { serveStatic } from 'hono/bun'

app.use('/static/*', serveStatic({ root: './public' }))
```

## Common Pitfalls

1. **Using `@hono/node-server` on Cloudflare** — Don't install the Node adapter for Workers/Pages
2. **Forgetting `export default app`** — Bun and Workers require the default export
3. **Static file paths** — Node.js resolves relative to CWD, not the source file
4. **Lambda cold starts** — Use `LinearRouter` for faster route registration in Lambda
5. **Deno permissions** — Deno requires `--allow-net` for serving and `--allow-read` for static files
6. **Vercel route conflicts** — Use `basePath('/api')` to avoid conflicts with Next.js/frontend routes
