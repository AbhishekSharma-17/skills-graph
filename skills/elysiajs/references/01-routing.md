# ElysiaJS — Routing

> Source: [elysiajs.com/essential/route](https://elysiajs.com/essential/route) · Version 1.4.x

## Table of Contents

- [Route Basics](#route-basics)
- [HTTP Methods](#http-methods)
- [Path Types](#path-types)
- [Path Priority](#path-priority)
- [Route Grouping](#route-grouping)
- [Guards](#guards)
- [Custom Methods](#custom-methods)
- [Inline Route Configuration](#inline-route-configuration)
- [Chaining Pattern](#chaining-pattern)
- [Common Pitfalls](#common-pitfalls)

---

## Route Basics

Routes in ElysiaJS are defined by pairing an HTTP method with a path and a handler function. All route methods return the same Elysia instance, enabling method chaining.

```typescript
import { Elysia } from 'elysia'

const app = new Elysia()
    .get('/', () => 'Hello World')
    .post('/users', ({ body }) => createUser(body))
    .put('/users/:id', ({ params, body }) => updateUser(params.id, body))
    .delete('/users/:id', ({ params }) => deleteUser(params.id))
    .listen(3000)
```

Handlers receive a `Context` object with request data (params, query, body, headers, cookies) and can return any serializable value.

## HTTP Methods

ElysiaJS provides methods for all standard HTTP verbs:

| Method | Usage | Typical Use |
|--------|-------|-------------|
| `.get()` | `app.get('/path', handler)` | Read resources |
| `.post()` | `app.post('/path', handler)` | Create resources |
| `.put()` | `app.put('/path', handler)` | Full resource update |
| `.patch()` | `app.patch('/path', handler)` | Partial resource update |
| `.delete()` | `app.delete('/path', handler)` | Remove resources |
| `.options()` | `app.options('/path', handler)` | CORS preflight |
| `.head()` | `app.head('/path', handler)` | Headers only |
| `.all()` | `app.all('/path', handler)` | Match any HTTP method |

### Custom HTTP Methods

Use `.route()` for non-standard HTTP methods:

```typescript
app.route('M-SEARCH', '/m-search', ({ body }) => handleSearch(body))
app.route('PURGE', '/cache/:key', ({ params }) => purgeCache(params.key))
```

HTTP verbs are case-sensitive per RFC 7231 — use uppercase.

## Path Types

### Static Paths

Exact string matches with highest priority:

```typescript
app.get('/hello', () => 'Hello')
    .get('/api/v1/users', () => 'Users list')
```

### Dynamic Paths (Parameters)

Capture URL segments with `:paramName`:

```typescript
app.get('/users/:id', ({ params: { id } }) => `User ${id}`)
   .get('/users/:id/posts/:postId', ({ params }) => {
       return `User ${params.id}, Post ${params.postId}`
   })
```

Parameters are automatically typed as strings. Use validation schemas for type coercion:

```typescript
app.get('/users/:id', ({ params: { id } }) => getUserById(id), {
    params: t.Object({
        id: t.Numeric()  // Coerces string to number
    })
})
```

### Optional Parameters

Append `?` to make a segment optional:

```typescript
app.get('/users/:id?', ({ params: { id } }) => {
    if (id) return getUserById(id)
    return getAllUsers()
})
```

### Wildcards

Capture remaining path segments with `*`:

```typescript
app.get('/files/*', ({ params }) => {
    const filePath = params['*']  // e.g., "docs/readme.md"
    return serveFile(filePath)
})
```

## Path Priority

When multiple routes match, ElysiaJS resolves in this order:

1. **Static paths** — `/users/profile` (highest priority)
2. **Dynamic paths** — `/users/:id`
3. **Wildcards** — `/users/*` (lowest priority)

```typescript
app.get('/users/me', () => 'Current user')        // Matches first
   .get('/users/:id', ({ params }) => params.id)   // Matches second
   .get('/users/*', () => 'Wildcard catch-all')    // Matches last
```

## Route Grouping

### Using `.group()`

Group routes under a common prefix with shared configuration:

```typescript
app.group('/api/v1', (app) =>
    app
        .get('/users', () => 'List users')
        .get('/users/:id', ({ params }) => `User ${params.id}`)
        .post('/users', ({ body }) => createUser(body))
)
```

Groups can include validation and hooks:

```typescript
app.group(
    '/admin',
    {
        beforeHandle: ({ headers }) => {
            if (!headers.authorization) return new Response('Unauthorized', { status: 401 })
        }
    },
    (app) =>
        app
            .get('/dashboard', () => 'Admin dashboard')
            .get('/settings', () => 'Admin settings')
)
```

### Using Plugin Prefix

Create reusable route modules:

```typescript
// routes/users.ts
const userRoutes = new Elysia({ prefix: '/users' })
    .get('/', () => 'List users')
    .get('/:id', ({ params }) => `User ${params.id}`)
    .post('/', ({ body }) => createUser(body))

// index.ts
app.use(userRoutes)  // Routes mount at /users/*
```

### Nested Groups

```typescript
app.group('/api', (app) =>
    app.group('/v1', (app) =>
        app.get('/users', () => 'API v1 users')  // /api/v1/users
    )
)
```

## Guards

Guards apply shared validation and hooks to multiple routes:

```typescript
import { Elysia, t } from 'elysia'

app.guard(
    {
        body: t.Object({
            username: t.String(),
            password: t.String()
        })
    },
    (app) =>
        app
            .post('/sign-up', ({ body }) => signUp(body))
            .post('/sign-in', ({ body }) => signIn(body))
)
```

### Guard with Lifecycle Hooks

```typescript
app.guard(
    {
        beforeHandle({ cookie: { session } }) {
            if (!session.value) return status(401, 'Unauthorized')
        },
        response: t.Object({
            id: t.Number(),
            name: t.String()
        })
    },
    (app) =>
        app
            .get('/profile', getProfile)
            .put('/profile', updateProfile)
)
```

### Standalone Guard (No Callback)

Applies to all subsequent routes on the instance:

```typescript
app.guard({
    headers: t.Object({
        authorization: t.String()
    })
})
.get('/protected-1', handler1)
.get('/protected-2', handler2)
```

## Inline Route Configuration

Each route method accepts an optional third argument for route-specific configuration:

```typescript
app.post('/users', ({ body }) => createUser(body), {
    body: t.Object({
        name: t.String(),
        email: t.String({ format: 'email' })
    }),
    response: {
        201: t.Object({ id: t.Number() }),
        400: t.Object({ error: t.String() })
    },
    detail: {
        summary: 'Create a user',
        tags: ['users']
    },
    beforeHandle({ headers }) {
        if (!headers.authorization) return status(401)
    }
})
```

## Chaining Pattern

All methods return the Elysia instance, enabling fluent APIs:

```typescript
const app = new Elysia()
    .state('version', '1.0.0')
    .decorate('db', database)
    .onBeforeHandle(authMiddleware)
    .get('/', () => 'Home')
    .group('/api', apiRoutes)
    .use(userPlugin)
    .listen(3000)
```

## Common Pitfalls

1. **Path parameters vs query strings** — `:id` captures path segments, not query params. Use `{ query }` for `?key=value` access.

2. **Group callback must return** — The group callback receives the app and its return value is used. Always chain routes on the passed app parameter.

3. **Prefix trailing slashes** — ElysiaJS does not auto-normalize trailing slashes. `/users` and `/users/` are different routes.

4. **Dynamic imports in groups** — When splitting routes across files, use the plugin prefix pattern rather than `.group()` for better type inference.

5. **Route order within a priority tier** — Among routes at the same priority level (e.g., all dynamic), first-registered wins.
