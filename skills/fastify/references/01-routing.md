# Fastify — Routing

> Source: [fastify.dev/docs/latest/Reference/Routes](https://fastify.dev/docs/latest/Reference/Routes/)

## Table of Contents

- [Route Declaration](#route-declaration)
- [URL Patterns](#url-patterns)
- [Route Options](#route-options)
- [Route-Level Hooks](#route-level-hooks)
- [Async Handlers](#asyncawait-handlers)
- [Route Prefixing](#route-prefixing)
- [Constraints](#constraints)
- [Custom Route Config](#custom-route-config)
- [Common Pitfalls](#common-pitfalls)

## Route Declaration

### Shorthand Methods

```javascript
fastify.get(path, [options], handler)
fastify.post(path, [options], handler)
fastify.put(path, [options], handler)
fastify.delete(path, [options], handler)
fastify.patch(path, [options], handler)
fastify.head(path, [options], handler)
fastify.options(path, [options], handler)
fastify.all(path, [options], handler)  // all HTTP methods
```

### Full Declaration

```javascript
fastify.route({
  method: 'GET',
  url: '/users/:id',
  schema: {
    params: {
      type: 'object',
      properties: {
        id: { type: 'string' }
      }
    },
    response: {
      200: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          email: { type: 'string' }
        }
      }
    }
  },
  handler: async (request, reply) => {
    const user = await getUser(request.params.id)
    return user
  }
})
```

### Multiple Methods on One Route

```javascript
fastify.route({
  method: ['GET', 'HEAD'],
  url: '/status',
  handler: async () => ({ status: 'ok' })
})
```

## URL Patterns

### Static Routes

Static routes are matched first, before parametric or wildcard routes:

```javascript
fastify.get('/users/me', handler)        // matched before /users/:id
fastify.get('/users/:id', otherHandler)
```

### Parametric Routes

Use colons for URL parameters:

```javascript
fastify.get('/users/:userId', async (request) => {
  return { id: request.params.userId }
})

fastify.get('/users/:userId/posts/:postId', async (request) => {
  const { userId, postId } = request.params
  return { userId, postId }
})
```

### Multi-Parameter Segments

Separate parameters with dashes within a single segment:

```javascript
fastify.get('/near/:lat-:lng/radius/:r', async (request) => {
  const { lat, lng, r } = request.params
  return { lat, lng, radius: r }
})
```

### RegExp Parameters

Add patterns in parentheses (incurs a performance cost):

```javascript
fastify.get('/file/:name(^\\d+).png', handler)
// matches /file/123.png but not /file/abc.png

fastify.get('/at/:hour(^\\d{2})h:minute(^\\d{2})m', handler)
// matches /at/08h30m
```

### Optional Parameters

Append `?` to make a parameter optional:

```javascript
fastify.get('/posts/:id?', async (request) => {
  if (request.params.id) {
    return getPost(request.params.id)
  }
  return listPosts()
})
```

### Wildcard Routes

Use `*` for catch-all matching:

```javascript
fastify.get('/assets/*', async (request) => {
  return { path: request.params['*'] }
})
// /assets/css/style.css → params['*'] = 'css/style.css'
```

### Escaped Colons

Double colons produce literal colons:

```javascript
fastify.post('/name::verb')
// matches POST /name:verb
```

## Route Options

| Option | Type | Description |
|--------|------|-------------|
| `method` | string / string[] | HTTP method(s) |
| `url` / `path` | string | Route path |
| `schema` | object | Validation schemas (body, query, params, headers, response) |
| `handler` | function | Request handler |
| `bodyLimit` | number | Max request body in bytes (default: 1,048,576) |
| `logLevel` | string | Route-specific log level |
| `config` | object | Custom config accessible via `reply.routeOptions.config` |
| `constraints` | object | Version, host, or custom constraints |
| `exposeHeadRoute` | boolean | Auto-create HEAD for GET routes (default: true) |
| `prefixTrailingSlash` | string | `'both'` / `'slash'` / `'no-slash'` |
| `handlerTimeout` | number | Max handler execution time in ms |
| `errorHandler` | function | Route-specific error handler |

## Route-Level Hooks

Attach hooks directly to routes — they execute last in their category:

```javascript
fastify.route({
  method: 'GET',
  url: '/protected',
  onRequest: async (request, reply) => {
    await authenticate(request)
  },
  preHandler: [
    async (request) => { await authorize(request) },
    async (request) => { await rateLimit(request) }
  ],
  handler: async (request) => {
    return { data: 'secret' }
  }
})
```

## Async Handlers

### Return Value (Preferred)

```javascript
fastify.get('/', async (request, reply) => {
  const data = await fetchData()
  return data  // automatically serialized and sent
})
```

### Using reply.send()

```javascript
fastify.get('/', async (request, reply) => {
  const data = await fetchData()
  reply.send(data)
  return reply  // MUST return reply to avoid double-send
})
```

### Rules

1. Returning a value sends it as the response — do not also call `reply.send()`
2. If you call `reply.send()` in an async handler, you must `return reply`
3. The first resolved value wins — subsequent sends are ignored
4. Returning `undefined` is an error

## Route Prefixing

Group routes under a prefix via plugin registration:

```javascript
// routes/users.js
export default async function userRoutes(fastify) {
  fastify.get('/', async () => listUsers())       // GET /api/v1/users
  fastify.get('/:id', async (req) => getUser(req.params.id))  // GET /api/v1/users/:id
  fastify.post('/', async (req) => createUser(req.body))       // POST /api/v1/users
}

// app.js
fastify.register(userRoutes, { prefix: '/api/v1/users' })
```

### Nested Prefixes

```javascript
fastify.register(async function v1(app) {
  app.register(userRoutes, { prefix: '/users' })
  app.register(postRoutes, { prefix: '/posts' })
}, { prefix: '/api/v1' })

// Creates: /api/v1/users, /api/v1/users/:id, /api/v1/posts, etc.
```

## Constraints

### Version Constraints

Serve different handlers based on the `Accept-Version` header:

```javascript
fastify.route({
  method: 'GET',
  url: '/api/data',
  constraints: { version: '1.0.0' },
  handler: async () => ({ version: 1, data: 'v1' })
})

fastify.route({
  method: 'GET',
  url: '/api/data',
  constraints: { version: '2.0.0' },
  handler: async () => ({ version: 2, data: 'v2' })
})
// Client sends: Accept-Version: 1.x → gets v1 handler
```

Set `Vary: Accept-Version` header to prevent cache poisoning.

### Host Constraints

```javascript
fastify.route({
  method: 'GET',
  url: '/',
  constraints: { host: 'api.example.com' },
  handler: async () => ({ service: 'api' })
})

fastify.route({
  method: 'GET',
  url: '/',
  constraints: { host: /.*\.example\.com/ },
  handler: async () => ({ service: 'wildcard' })
})
```

## Custom Route Config

Store arbitrary data accessible in handlers:

```javascript
fastify.get('/en', {
  config: { lang: 'en', greeting: 'Hello!' }
}, async (request, reply) => {
  return { message: reply.routeOptions.config.greeting }
})
```

## Per-Route Logging

```javascript
fastify.get('/health', { logLevel: 'warn' }, async () => {
  return { status: 'ok' }
})
// Only logs warnings and above for this route
```

## Common Pitfalls

1. **Param naming conflicts** — `/users/:id` and `/users/:userId` on the same method conflict; use consistent names
2. **Wildcard precedence** — wildcard routes are matched last; static and parametric routes always win
3. **RegExp performance** — regex parameters add overhead per match; use only when needed
4. **Prefix with trailing slash** — `{ prefix: '/api/' }` creates routes starting with `/api/`, while `{ prefix: '/api' }` creates routes starting with `/api` (and matches both `/api/route` and `/apiroute` in some edge cases)
5. **Version constraint performance** — versioning degrades router throughput; avoid on hot paths unless necessary
