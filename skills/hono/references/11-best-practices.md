# Hono — Best Practices

> Source: [hono.dev/docs/guides/best-practices](https://hono.dev/docs/guides/best-practices)

## Project Structure

### Small Projects

```
src/
├── index.ts          # App entry point with routes
├── middleware/
│   └── auth.ts       # Custom middleware
└── lib/
    └── db.ts         # Database utilities
```

### Medium Projects

```
src/
├── index.ts          # Entry point, mounts routes
├── routes/
│   ├── posts.ts      # Post routes
│   ├── users.ts      # User routes
│   └── auth.ts       # Auth routes
├── middleware/
│   ├── auth.ts       # Auth middleware
│   └── logger.ts     # Custom logger
├── schemas/
│   ├── post.ts       # Zod schemas
│   └── user.ts       # Zod schemas
├── lib/
│   ├── db.ts         # Database client
│   └── email.ts      # Email service
└── types/
    └── env.ts        # Environment type definitions
```

### Large Projects

```
src/
├── index.ts
├── routes/
│   ├── v1/
│   │   ├── posts.ts
│   │   └── users.ts
│   └── v2/
│       └── posts.ts
├── middleware/
├── schemas/
├── services/
│   ├── post.service.ts
│   └── user.service.ts
├── repositories/
│   ├── post.repo.ts
│   └── user.repo.ts
├── lib/
└── types/
```

## Route Organization

### Avoid Controller Classes

Hono recommends **against** traditional controller patterns because they break type inference:

```typescript
// BAD — Loses path parameter type inference
class PostController {
  static getPost(c: Context) {
    const id = c.req.param('id') // id is string | undefined (no type info)
    return c.json({ id })
  }
}
app.get('/posts/:id', PostController.getPost)
```

```typescript
// GOOD — Inline handlers preserve type inference
app.get('/posts/:id', (c) => {
  const id = c.req.param('id') // id is string (typed from route)
  return c.json({ id })
})
```

### Factory Pattern for Reusable Handlers

When you need separation, use `createHandlers` from `hono/factory`:

```typescript
import { createFactory } from 'hono/factory'

type Env = {
  Bindings: { DATABASE_URL: string }
  Variables: { user: { id: string } }
}

const factory = createFactory<Env>()

const getPost = factory.createHandlers((c) => {
  const id = c.req.param('id') // Properly typed
  return c.json({ id })
})

app.get('/posts/:id', ...getPost)
```

### Use app.route() for Modularity

```typescript
// routes/posts.ts
import { Hono } from 'hono'

type Env = { Bindings: { DB: D1Database } }

const posts = new Hono<Env>()
  .get('/', async (c) => {
    const results = await c.env.DB.prepare('SELECT * FROM posts').all()
    return c.json(results)
  })
  .post('/', async (c) => {
    const data = await c.req.json()
    return c.json({ created: true }, 201)
  })

export default posts
```

```typescript
// index.ts
import posts from './routes/posts'
import users from './routes/users'

const app = new Hono()
  .route('/api/posts', posts)
  .route('/api/users', users)

export type AppType = typeof app
export default app
```

## Type Safety

### Define Environment Types

Always define types for bindings and variables:

```typescript
// types/env.ts
export type Env = {
  Bindings: {
    DATABASE_URL: string
    JWT_SECRET: string
    MY_KV: KVNamespace
  }
  Variables: {
    user: { id: string; role: string }
    requestId: string
  }
}
```

```typescript
// Use everywhere
import type { Env } from './types/env'

const app = new Hono<Env>()
```

### Type-Safe Middleware

```typescript
import { createMiddleware } from 'hono/factory'
import type { Env } from './types/env'

export const requireAuth = createMiddleware<Env>(async (c, next) => {
  const token = c.req.header('Authorization')?.split(' ')[1]
  if (!token) {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  const user = await verifyToken(token, c.env.JWT_SECRET)
  c.set('user', user)
  await next()
})
```

## Performance

### Choose the Right Router

| Runtime | Recommended Router |
|---------|-------------------|
| Long-lived server (Node.js, Bun) | `SmartRouter` (default) |
| Edge/serverless (Workers, Lambda) | `SmartRouter` or `LinearRouter` |
| Memory-constrained | `PatternRouter` |

```typescript
import { Hono } from 'hono'
import { LinearRouter } from 'hono/router/linear-router'

// Faster registration for serverless cold starts
const app = new Hono({ router: new LinearRouter() })
```

### Response Streaming

Use streaming for large responses:

```typescript
app.get('/large-data', (c) => {
  return c.stream(async (stream) => {
    for await (const chunk of dataSource) {
      await stream.write(JSON.stringify(chunk) + '\n')
    }
  })
})
```

### Avoid Unnecessary Middleware

Only apply middleware to routes that need it:

```typescript
// GOOD — Scoped middleware
app.use('/api/*', cors())
app.use('/api/*', authMiddleware)

// BAD — Global middleware for everything
app.use(cors())
app.use(authMiddleware) // Public routes don't need auth
```

## Security

### Always Use secureHeaders

```typescript
import { secureHeaders } from 'hono/secure-headers'

app.use(secureHeaders())
```

### Validate All Input

```typescript
import { zValidator } from '@hono/zod-validator'

// Validate params, query, body — not just body
app.get('/users/:id',
  zValidator('param', z.object({ id: z.string().uuid() })),
  handler
)
```

### Environment Secrets

```typescript
// Never hardcode secrets
app.use('/api/*', (c, next) => {
  return jwt({
    secret: c.env.JWT_SECRET, // From environment
    alg: 'HS256',
  })(c, next)
})
```

### Rate Limiting

```typescript
// Combine with Cloudflare Rate Limiting or custom middleware
app.use('/api/*', rateLimiter({
  max: 100,
  windowMs: 60_000,
}))
```

## Deployment

### CI/CD with GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm test
      - uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

### Health Check Endpoint

```typescript
app.get('/health', (c) => {
  return c.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
  })
})
```

### Graceful Error Handling in Production

```typescript
app.onError((err, c) => {
  // Log to error tracking service
  console.error({
    error: err.message,
    stack: err.stack,
    path: c.req.path,
    method: c.req.method,
  })

  if (err instanceof HTTPException) {
    return err.getResponse()
  }

  return c.json({ error: 'Internal Server Error' }, 500)
})
```

## Common Anti-Patterns

1. **Controller classes** — Use inline handlers or factory pattern instead
2. **Monolithic route file** — Split routes with `app.route()`
3. **Untyped env access** — Always define `Bindings` and `Variables` types
4. **Global middleware for auth** — Scope auth middleware to protected routes only
5. **Ignoring error handling** — Always set up `app.onError` and `app.notFound`
6. **Not using RPC** — If your client is TypeScript, use the `hc` client for free type safety
7. **Express patterns** — Don't use `req.body`, `res.send()` — use Hono's Context API
