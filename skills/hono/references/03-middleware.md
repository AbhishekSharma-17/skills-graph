# Hono — Middleware

> Source: [hono.dev/docs/guides/middleware](https://hono.dev/docs/guides/middleware)

## Table of Contents

- [Overview](#overview)
- [Middleware Basics](#middleware-basics)
- [Built-in Middleware](#built-in-middleware)
- [Custom Middleware](#custom-middleware)
- [Middleware Ordering](#middleware-ordering)
- [Path-Scoped Middleware](#path-scoped-middleware)
- [Third-Party Middleware](#third-party-middleware)
- [Common Pitfalls](#common-pitfalls)

## Overview

Middleware in Hono works like an onion model — each middleware wraps the handler, executing code before and after `await next()`. Middleware can modify requests, responses, set context variables, or short-circuit the chain.

## Middleware Basics

```typescript
import { Hono } from 'hono'

const app = new Hono()

// Middleware function
app.use(async (c, next) => {
  console.log(`[${c.req.method}] ${c.req.url}`)
  const start = Date.now()
  await next()
  const elapsed = Date.now() - start
  c.header('X-Response-Time', `${elapsed}ms`)
})

app.get('/', (c) => c.text('Hello'))
```

Key rules:
- Always call `await next()` to pass control to the next middleware/handler
- Code before `next()` runs on the way in
- Code after `next()` runs on the way out
- Return a response to short-circuit the chain

## Built-in Middleware

### Logger

Logs incoming requests and response status:

```typescript
import { logger } from 'hono/logger'

app.use(logger())
// Output: <-- GET / 200 3ms
```

### CORS

Configure Cross-Origin Resource Sharing:

```typescript
import { cors } from 'hono/cors'

// Allow all origins
app.use('/api/*', cors())

// Custom configuration
app.use('/api/*', cors({
  origin: ['https://example.com', 'https://app.example.com'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  exposeHeaders: ['X-Total-Count'],
  maxAge: 600,
  credentials: true,
}))

// Dynamic origin
app.use('/api/*', cors({
  origin: (origin) => {
    return origin.endsWith('.example.com')
      ? origin
      : 'https://example.com'
  },
}))
```

### ETag

Automatic ETag generation for caching:

```typescript
import { etag } from 'hono/etag'

app.use(etag())
```

### Compress

Compress responses with gzip/deflate:

```typescript
import { compress } from 'hono/compress'

app.use(compress())
```

### Secure Headers

Add security-related HTTP headers:

```typescript
import { secureHeaders } from 'hono/secure-headers'

app.use(secureHeaders())
// Sets: X-Frame-Options, X-Content-Type-Options,
//       Strict-Transport-Security, etc.
```

### Timing

Add Server-Timing headers for performance measurement:

```typescript
import { timing, startTime, endTime } from 'hono/timing'

app.use(timing())

app.get('/', async (c) => {
  startTime(c, 'db')
  const data = await db.query('SELECT * FROM users')
  endTime(c, 'db')
  return c.json(data)
})
```

### Pretty JSON

Format JSON responses with indentation:

```typescript
import { prettyJSON } from 'hono/pretty-json'

app.use(prettyJSON())
// Add ?pretty to any endpoint to get formatted JSON
```

### Cache

Set cache control headers:

```typescript
import { cache } from 'hono/cache'

app.get('/static/*', cache({
  cacheName: 'my-app',
  cacheControl: 'max-age=3600',
}))
```

### Request ID

Add unique request IDs:

```typescript
import { requestId } from 'hono/request-id'

app.use(requestId())

app.get('/', (c) => {
  const id = c.get('requestId')
  return c.json({ requestId: id })
})
```

### Body Limit

Limit request body size:

```typescript
import { bodyLimit } from 'hono/body-limit'

app.post('/upload', bodyLimit({
  maxSize: 50 * 1024 * 1024, // 50MB
  onError: (c) => c.text('File too large', 413),
}))
```

## Custom Middleware

### Inline Middleware

```typescript
app.use(async (c, next) => {
  const apiKey = c.req.header('X-API-Key')
  if (!apiKey || apiKey !== 'secret') {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  await next()
})
```

### Factory Middleware (Reusable)

Use `createMiddleware` for type-safe, reusable middleware:

```typescript
import { createMiddleware } from 'hono/factory'

type Env = {
  Variables: {
    user: { id: string; role: string }
  }
}

const authMiddleware = createMiddleware<Env>(async (c, next) => {
  const token = c.req.header('Authorization')?.split(' ')[1]
  if (!token) {
    return c.json({ error: 'Missing token' }, 401)
  }

  const user = await verifyToken(token)
  c.set('user', user)
  await next()
})

// Use it
app.use('/api/*', authMiddleware)

app.get('/api/me', (c) => {
  const user = c.get('user') // Fully typed
  return c.json(user)
})
```

### Middleware with Options

```typescript
import { createMiddleware } from 'hono/factory'

interface RateLimitOptions {
  max: number
  windowMs: number
}

const rateLimit = (options: RateLimitOptions) => {
  const store = new Map<string, { count: number; reset: number }>()

  return createMiddleware(async (c, next) => {
    const key = c.req.header('CF-Connecting-IP') ?? 'unknown'
    const now = Date.now()
    const record = store.get(key)

    if (record && now < record.reset) {
      if (record.count >= options.max) {
        return c.json({ error: 'Too many requests' }, 429)
      }
      record.count++
    } else {
      store.set(key, { count: 1, reset: now + options.windowMs })
    }

    await next()
  })
}

app.use('/api/*', rateLimit({ max: 100, windowMs: 60_000 }))
```

## Middleware Ordering

Middleware executes in registration order:

```typescript
app.use(logger())        // 1st: logs request
app.use(cors())          // 2nd: handles CORS
app.use(secureHeaders()) // 3rd: adds security headers
app.use(authMiddleware)  // 4th: authenticates

app.get('/', handler)    // 5th: route handler
```

The response flows back in reverse order (onion model).

## Path-Scoped Middleware

Apply middleware to specific paths:

```typescript
// All routes
app.use(logger())

// Only /api/* routes
app.use('/api/*', cors())
app.use('/api/*', authMiddleware)

// Specific method + path
app.use('POST', '/api/upload', bodyLimit({ maxSize: 10_000_000 }))
```

## Third-Party Middleware

Popular packages from the `@hono` scope:

| Package | Purpose |
|---------|---------|
| `@hono/zod-validator` | Zod-based request validation |
| `@hono/swagger-ui` | Swagger UI for OpenAPI docs |
| `@hono/graphql-server` | GraphQL integration |
| `@hono/sentry` | Sentry error tracking |
| `@hono/clerk-auth` | Clerk authentication |
| `@hono/auth-js` | Auth.js (NextAuth) integration |
| `@hono/trpc-server` | tRPC server adapter |

## Common Pitfalls

1. **Forgetting `await next()`** — Without it, downstream middleware and handlers won't execute
2. **Not returning responses in guard middleware** — Return `c.json(...)` to short-circuit; don't just set headers
3. **Middleware after routes** — Middleware must be registered before the routes it should apply to
4. **Creating middleware without `createMiddleware`** — Use the factory for proper type inference in separate files
5. **Mutating the response after next()** — Setting headers works, but you can't replace the response body after `next()`
