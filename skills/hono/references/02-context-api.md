# Hono — Context API

> Source: [hono.dev/docs/api/context](https://hono.dev/docs/api/context)

## Table of Contents

- [Overview](#overview)
- [Response Methods](#response-methods)
- [Request Access](#request-access)
- [Context Variables](#context-variables)
- [Environment Bindings](#environment-bindings)
- [Headers](#headers)
- [Status Codes](#status-codes)
- [Redirect](#redirect)
- [Streaming](#streaming)
- [Common Pitfalls](#common-pitfalls)

## Overview

Every route handler and middleware receives a `Context` object (`c`) that provides access to the request, response helpers, variables, and environment bindings.

```typescript
app.get('/hello', (c) => {
  // c is the Context object
  return c.text('Hello!')
})
```

## Response Methods

### c.text()

Return plain text responses:

```typescript
app.get('/', (c) => c.text('Hello World'))

// With status code
app.get('/created', (c) => c.text('Created', 201))
```

### c.json()

Return JSON responses (automatically sets `Content-Type: application/json`):

```typescript
app.get('/api/user', (c) => {
  return c.json({ id: 1, name: 'Hono' })
})

// With status code
app.post('/api/user', (c) => {
  return c.json({ message: 'Created' }, 201)
})

// Type inference works with RPC
app.get('/api/user', (c) => {
  return c.json({
    ok: true,
    message: 'Success',
  } as const)
})
```

### c.html()

Return HTML responses:

```typescript
app.get('/', (c) => {
  return c.html('<h1>Hello Hono!</h1>')
})
```

### c.body()

Return raw body with custom content type:

```typescript
app.get('/image', async (c) => {
  const image = await fetchImage()
  return c.body(image, {
    headers: { 'Content-Type': 'image/png' },
  })
})
```

### c.notFound()

Return 404 response:

```typescript
app.get('/item/:id', (c) => {
  const item = findItem(c.req.param('id'))
  if (!item) return c.notFound()
  return c.json(item)
})
```

### c.redirect()

Return redirect responses:

```typescript
// 302 (temporary) redirect — default
app.get('/old', (c) => c.redirect('/new'))

// 301 (permanent) redirect
app.get('/old', (c) => c.redirect('/new', 301))
```

## Request Access

### c.req.param()

Get path parameters:

```typescript
app.get('/users/:id', (c) => {
  const id = c.req.param('id')
  return c.json({ id })
})

// All params as object
app.get('/posts/:postId/comments/:commentId', (c) => {
  const params = c.req.param()
  // { postId: '...', commentId: '...' }
  return c.json(params)
})
```

### c.req.query()

Get query string parameters:

```typescript
// GET /search?q=hono&limit=10
app.get('/search', (c) => {
  const q = c.req.query('q')       // 'hono'
  const limit = c.req.query('limit') // '10'
  return c.json({ q, limit })
})

// All query params
app.get('/search', (c) => {
  const queries = c.req.queries('tags')
  // For /search?tags=a&tags=b => ['a', 'b']
  return c.json({ tags: queries })
})
```

### c.req.header()

Get request headers:

```typescript
app.get('/', (c) => {
  const userAgent = c.req.header('User-Agent')
  const accept = c.req.header('Accept')
  return c.json({ userAgent, accept })
})
```

### c.req.parseBody()

Parse form data or multipart form data:

```typescript
app.post('/upload', async (c) => {
  const body = await c.req.parseBody()
  const file = body['file'] // File object for multipart
  const name = body['name'] // string for form fields
  return c.json({ name })
})
```

### c.req.json()

Parse JSON request body:

```typescript
app.post('/api/data', async (c) => {
  const data = await c.req.json()
  return c.json({ received: data })
})
```

### c.req.text()

Parse request body as text:

```typescript
app.post('/webhook', async (c) => {
  const text = await c.req.text()
  return c.text(`Received: ${text}`)
})
```

### c.req.url and c.req.path

Access the full URL and path:

```typescript
app.get('/info', (c) => {
  return c.json({
    url: c.req.url,     // Full URL including query
    path: c.req.path,   // Path without query
    method: c.req.method,
  })
})
```

### c.req.valid()

Get validated data (used with validation middleware):

```typescript
app.post('/posts',
  zValidator('json', schema),
  (c) => {
    const data = c.req.valid('json') // Type-safe validated data
    return c.json(data)
  }
)
```

## Context Variables

Set and get values scoped to the current request — useful for passing data between middleware and handlers:

```typescript
// Type-safe variables
type Variables = {
  user: { id: string; name: string }
  requestId: string
}

const app = new Hono<{ Variables: Variables }>()

// Set in middleware
app.use(async (c, next) => {
  c.set('requestId', crypto.randomUUID())
  await next()
})

// Get in handler
app.get('/', (c) => {
  const requestId = c.get('requestId')
  return c.json({ requestId })
})
```

Variables are scoped to the request — they cannot be shared across requests.

## Environment Bindings

Access environment variables and platform bindings:

```typescript
// Cloudflare Workers bindings
type Bindings = {
  MY_BUCKET: R2Bucket
  MY_KV: KVNamespace
  DATABASE_URL: string
}

const app = new Hono<{ Bindings: Bindings }>()

app.get('/', (c) => {
  const dbUrl = c.env.DATABASE_URL
  const bucket = c.env.MY_BUCKET
  return c.text('OK')
})
```

```typescript
// Node.js — access raw HTTP objects
import type { HttpBindings } from '@hono/node-server'

const app = new Hono<{ Bindings: HttpBindings }>()

app.get('/', (c) => {
  const incoming = c.env.incoming // IncomingMessage
  const outgoing = c.env.outgoing // ServerResponse
  return c.text('OK')
})
```

## Headers

### Setting Response Headers

```typescript
app.get('/', (c) => {
  c.header('X-Request-Id', '123')
  c.header('X-Custom', 'value')
  return c.text('OK')
})
```

### Appending Headers

```typescript
app.get('/', (c) => {
  c.header('X-Values', 'a', { append: true })
  c.header('X-Values', 'b', { append: true })
  return c.text('OK')
})
```

## Status Codes

Set status code explicitly:

```typescript
app.post('/api/resource', (c) => {
  c.status(201)
  return c.json({ created: true })
})

// Or inline with response methods
app.post('/api/resource', (c) => {
  return c.json({ created: true }, 201)
})
```

## Streaming

### c.stream()

Stream response data:

```typescript
app.get('/stream', (c) => {
  return c.stream(async (stream) => {
    for (let i = 0; i < 5; i++) {
      await stream.write(`chunk ${i}\n`)
      await stream.sleep(1000)
    }
  })
})
```

### c.streamText()

Stream text with proper content type:

```typescript
app.get('/stream-text', (c) => {
  return c.streamText(async (stream) => {
    await stream.writeln('Line 1')
    await stream.sleep(500)
    await stream.writeln('Line 2')
  })
})
```

## Common Pitfalls

1. **Forgetting to `await` body parsing** — `c.req.json()`, `c.req.parseBody()`, and `c.req.text()` are async
2. **Setting headers after response** — Headers must be set before calling `c.json()`, `c.text()`, etc.
3. **Not typing Variables/Bindings** — Pass generics to `new Hono<{ Variables, Bindings }>()` for type safety
4. **Using c.set/get without types** — Always define a `Variables` type for compile-time safety
5. **Accessing c.env in Node.js** — `c.env` contains `incoming`/`outgoing` on Node.js, not env vars (use `process.env`)
