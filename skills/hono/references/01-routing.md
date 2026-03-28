# Hono — Routing

> Source: [hono.dev/docs/api/routing](https://hono.dev/docs/api/routing)

## Table of Contents

- [HTTP Methods](#http-methods)
- [Path Parameters](#path-parameters)
- [Wildcards](#wildcards)
- [Regular Expressions](#regular-expressions)
- [Chaining Routes](#chaining-routes)
- [Route Grouping with app.route()](#route-grouping)
- [Base Path](#base-path)
- [Multiple Methods and Paths](#multiple-methods-and-paths)
- [Router Selection](#router-selection)
- [Common Pitfalls](#common-pitfalls)

## HTTP Methods

Hono supports all standard HTTP methods:

```typescript
import { Hono } from 'hono'

const app = new Hono()

app.get('/', (c) => c.text('GET /'))
app.post('/', (c) => c.text('POST /'))
app.put('/', (c) => c.text('PUT /'))
app.delete('/', (c) => c.text('DELETE /'))
app.patch('/', (c) => c.text('PATCH /'))
app.options('/', (c) => c.text('OPTIONS /'))

// Match any HTTP method
app.all('/hello', (c) => c.text('Any Method /hello'))

// Custom HTTP methods
app.on('PURGE', '/cache', (c) => c.text('PURGE Method /cache'))
```

## Path Parameters

Use `:param` syntax to capture path segments:

```typescript
// Single parameter
app.get('/users/:id', (c) => {
  const id = c.req.param('id')
  return c.json({ id })
})

// Multiple parameters
app.get('/posts/:postId/comments/:commentId', (c) => {
  const { postId, commentId } = c.req.param()
  return c.json({ postId, commentId })
})
```

Parameters are fully typed when chaining routes for RPC.

### Optional Parameters

Use `?` to make a parameter optional:

```typescript
app.get('/api/animals/:type?', (c) => {
  const type = c.req.param('type') ?? 'all'
  return c.json({ type })
})
// Matches: /api/animals, /api/animals/dog
```

## Wildcards

The `*` wildcard matches any path segment:

```typescript
app.get('/wild/*/card', (c) => {
  return c.text('GET /wild/*/card')
})
// Matches: /wild/foo/card, /wild/bar/card

// Catch-all at the end
app.get('/api/*', (c) => {
  return c.text('Catch all under /api')
})
```

## Regular Expressions

Use regex patterns for advanced matching:

```typescript
// Match numeric IDs only
app.get('/post/:date{[0-9]+}/:title{[a-z]+}', (c) => {
  const { date, title } = c.req.param()
  return c.json({ date, title })
})
```

## Chaining Routes

Chain route definitions for RPC type inference:

```typescript
// CORRECT — Types are inferred for RPC
const route = app
  .get('/api/posts', (c) => c.json({ posts: [] }))
  .post('/api/posts', (c) => c.json({ created: true }))
  .get('/api/posts/:id', (c) => c.json({ id: c.req.param('id') }))

export type AppType = typeof route

// WRONG — Types are NOT inferred for RPC
app.get('/api/posts', handler1)
app.post('/api/posts', handler2)
```

## Route Grouping

### app.route()

Split routes across multiple files for larger applications:

```typescript
// routes/users.ts
import { Hono } from 'hono'

const users = new Hono()

users.get('/', (c) => c.json({ users: [] }))
users.get('/:id', (c) => c.json({ id: c.req.param('id') }))
users.post('/', (c) => c.json({ created: true }))

export default users
```

```typescript
// routes/posts.ts
import { Hono } from 'hono'

const posts = new Hono()

posts.get('/', (c) => c.json({ posts: [] }))
posts.post('/', (c) => c.json({ created: true }))

export default posts
```

```typescript
// index.ts
import { Hono } from 'hono'
import users from './routes/users'
import posts from './routes/posts'

const app = new Hono()

app.route('/api/users', users)
app.route('/api/posts', posts)

export default app
```

## Base Path

Set a base path for the entire app:

```typescript
const app = new Hono().basePath('/api/v1')

app.get('/posts', (c) => c.json({ posts: [] }))
// Matches: /api/v1/posts
```

## Multiple Methods and Paths

Handle multiple methods or paths with `app.on()`:

```typescript
// Multiple methods for the same path
app.on(['PUT', 'DELETE'], '/post', (c) =>
  c.text('PUT or DELETE /post')
)

// Multiple paths for the same method
app.on('GET', ['/hello', '/ja/hello', '/en/hello'], (c) =>
  c.text('Hello')
)
```

## Router Selection

Hono provides multiple router implementations:

| Router | Use Case |
|--------|----------|
| `SmartRouter` | Default — auto-selects the best router |
| `RegExpRouter` | Fastest — for static and simple patterns |
| `TrieRouter` | Supports all patterns including complex regex |
| `LinearRouter` | Fastest registration — ideal for one-shot environments |
| `PatternRouter` | Smallest — good for resource-constrained environments |

```typescript
import { Hono } from 'hono'
import { RegExpRouter } from 'hono/router/reg-exp-router'

const app = new Hono({ router: new RegExpRouter() })
```

The default `SmartRouter` works well for most cases.

## Common Pitfalls

1. **Route order matters** — Routes are matched in registration order; more specific routes should come first
2. **Forgetting to chain for RPC** — Separate `app.get()` calls don't preserve types for RPC client
3. **Base path vs route prefix** — `basePath()` applies to all routes; `app.route()` applies to a sub-app
4. **Trailing slashes** — `/foo` and `/foo/` are different routes by default
5. **Wildcard position** — `*` only matches within its segment unless at the end of the path
