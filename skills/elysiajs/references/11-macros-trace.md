# ElysiaJS — Macros & Trace

> Source: [elysiajs.com/patterns/macro](https://elysiajs.com/patterns/macro), [elysiajs.com/patterns/trace](https://elysiajs.com/patterns/trace) · Version 1.4.x

## Table of Contents

- [Macros Overview](#macros-overview)
- [Creating Macros](#creating-macros)
- [Auth Macro Pattern](#auth-macro-pattern)
- [Schema Macros](#schema-macros)
- [Macro Composition](#macro-composition)
- [Trace Overview](#trace-overview)
- [Tracing Lifecycle Events](#tracing-lifecycle-events)
- [Monitoring Children](#monitoring-children)
- [OpenTelemetry Integration](#opentelemetry-integration)
- [Common Pitfalls](#common-pitfalls)

---

## Macros Overview

Macros are reusable functions that encapsulate lifecycle hooks, validation schemas, and context management behind a simple boolean or parameter flag in route configuration. They act as declarative cross-cutting concerns.

```typescript
// Instead of repeating auth logic in every route...
app.get('/profile', handler, {
    beforeHandle({ headers }) {
        if (!headers.authorization) return status(401)
    }
})

// ...define a macro once and activate it with a flag
app.get('/profile', handler, { requireAuth: true })
```

## Creating Macros

### Basic Macro

```typescript
import { Elysia } from 'elysia'

const app = new Elysia()
    .macro({
        log: (message: string) => ({
            beforeHandle() {
                console.log(`[LOG] ${message}`)
            }
        })
    })
    .get('/', () => 'Hello', { log: 'Home page accessed' })
    .get('/api', () => 'API', { log: 'API called' })
```

### Macro with Resolve

Macros can inject properties into the handler context:

```typescript
const app = new Elysia()
    .macro({
        withTimestamp: {
            resolve() {
                return { timestamp: Date.now() }
            }
        }
    })
    .get('/time', ({ timestamp }) => ({ time: timestamp }), {
        withTimestamp: true
    })
```

### Boolean Shorthand (Elysia 1.2.10+)

Object-style macros accept booleans and auto-convert to conditional execution:

```typescript
.macro({
    requireAuth: {
        resolve({ headers }) {
            const token = headers.authorization?.split(' ')[1]
            if (!token) return status(401, 'Unauthorized')
            return { user: verifyJwt(token) }
        }
    }
})

// Activate with boolean
.get('/me', ({ user }) => user, { requireAuth: true })
```

## Auth Macro Pattern

A complete authentication macro with role-based access:

```typescript
const authPlugin = new Elysia({ name: 'auth' })
    .macro({
        requireAuth: {
            resolve({ headers }) {
                const token = headers.authorization?.split(' ')[1]
                if (!token) return status(401, 'Token required')

                try {
                    const user = verifyJwt(token)
                    return { user }
                } catch {
                    return status(401, 'Invalid token')
                }
            }
        },
        requireRole: (role: string) => ({
            resolve({ headers }) {
                const token = headers.authorization?.split(' ')[1]
                if (!token) return status(401, 'Token required')

                const user = verifyJwt(token)
                if (user.role !== role) {
                    return status(403, `Requires ${role} role`)
                }
                return { user }
            }
        })
    })

// Usage
const app = new Elysia()
    .use(authPlugin)
    .get('/profile', ({ user }) => user, { requireAuth: true })
    .get('/admin', ({ user }) => user, { requireRole: 'admin' })
    .delete('/users/:id', deleteUser, { requireRole: 'admin' })
```

## Schema Macros

Macros can inject validation schemas:

```typescript
.macro({
    paginated: {
        query: t.Object({
            page: t.Numeric({ minimum: 1, default: 1 }),
            limit: t.Numeric({ minimum: 1, maximum: 100, default: 20 }),
            sort: t.Optional(t.String())
        })
    }
})

// Routes automatically get pagination query params
.get('/users', ({ query }) => {
    return db.users.findMany({
        skip: (query.page - 1) * query.limit,
        take: query.limit,
        orderBy: query.sort
    })
}, { paginated: true })

.get('/posts', ({ query }) => {
    return db.posts.findMany({
        skip: (query.page - 1) * query.limit,
        take: query.limit
    })
}, { paginated: true })
```

## Macro Composition

Macros can use multiple lifecycle hooks:

```typescript
.macro({
    cached: (ttl: number) => ({
        beforeHandle({ path, query }) {
            const key = `${path}:${JSON.stringify(query)}`
            const cached = cache.get(key)
            if (cached) return cached
        },
        afterHandle({ response, path, query }) {
            const key = `${path}:${JSON.stringify(query)}`
            cache.set(key, response, { ttl })
        }
    })
})

.get('/expensive', expensiveQuery, { cached: 60 })  // Cache 60 seconds
```

### Error Handling in Macros

Return `status()` instead of throwing for proper HTTP responses:

```typescript
.macro({
    rateLimit: (max: number) => ({
        resolve({ request, server }) {
            const ip = server?.requestIP(request)?.address ?? 'unknown'
            const count = rateLimiter.increment(ip)
            if (count > max) {
                return status(429, 'Rate limit exceeded')
            }
        }
    })
})
```

## Trace Overview

Trace enables performance debugging by injecting monitoring code into lifecycle events. It requires `aot: true` (ahead-of-time compilation, the default).

```typescript
const app = new Elysia()
    .trace(async ({ onHandle }) => {
        onHandle(({ begin, onStop }) => {
            onStop(({ end }) => {
                console.log('Handler took', end - begin, 'ms')
            })
        })
    })
    .get('/', () => 'Hi')
    .listen(3000)
```

## Tracing Lifecycle Events

Nine lifecycle phases can be traced:

```typescript
app.trace(async ({
    onRequest,
    onParse,
    onTransform,
    onBeforeHandle,
    onHandle,
    onAfterHandle,
    onMapResponse,
    onError,
    onAfterResponse
}) => {
    onRequest(({ begin, onStop }) => {
        onStop(({ end }) => {
            console.log(`Request phase: ${end - begin}ms`)
        })
    })

    onBeforeHandle(({ begin, onStop }) => {
        onStop(({ end }) => {
            console.log(`Auth/validation: ${end - begin}ms`)
        })
    })

    onHandle(({ begin, onStop }) => {
        onStop(({ end }) => {
            console.log(`Handler: ${end - begin}ms`)
        })
    })
})
```

### Trace Parameters

Each traced event callback receives:

| Parameter | Description |
|-----------|-------------|
| `id` | Unique request identifier |
| `begin` | Start timestamp (ms) |
| `end` | End timestamp (available in `onStop`) |
| `context` | Request context |
| `onStop` | Callback for phase completion |

## Monitoring Children

For phases with multiple hooks (e.g., multiple `beforeHandle` middlewares):

```typescript
.trace(async ({ onBeforeHandle }) => {
    onBeforeHandle(({ total, onEvent }) => {
        console.log(`Total beforeHandle hooks: ${total}`)

        onEvent(({ onStop }) => {
            onStop(({ elapsed }) => {
                console.log(`Hook took ${elapsed}ms`)
            })
        })
    })
})
```

### Setting Headers from Trace

```typescript
.trace(async ({ onHandle }) => {
    onHandle(({ onStop, set }) => {
        const start = performance.now()
        onStop(() => {
            set.headers['X-Handler-Duration'] = 
                `${(performance.now() - start).toFixed(2)}ms`
        })
    })
})
```

## OpenTelemetry Integration

For production observability, use the OpenTelemetry plugin:

```bash
bun add @elysia/tracing @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node
```

```typescript
import { Elysia } from 'elysia'
import { tracing } from '@elysia/tracing'

const app = new Elysia()
    .use(tracing())
    .get('/', () => 'Hello')
    .listen(3000)
```

This exports spans for each lifecycle phase to your configured OpenTelemetry collector.

## Common Pitfalls

1. **Macro name collisions** — Macro property names must not conflict with existing route config keys (`body`, `query`, `beforeHandle`, etc.). Use descriptive names like `requireAuth` not `auth`.

2. **Trace requires AOT** — `trace()` only works with `aot: true` (the default). It won't function with dynamic mode since it needs static functions known at compile time.

3. **Return status, don't throw in macros** — Using `return status(401, ...)` in a macro's `resolve` gives proper HTTP responses and type inference. `throw` works but loses type narrowing for Eden.

4. **Macro deduplication** — Elysia deduplicates lifecycle events from macros using property values as seeds. If two routes use the same macro with different parameters, they get separate instances.

5. **Trace performance overhead** — Trace adds measurement overhead. Use it for development debugging and consider the tracing plugin (OpenTelemetry) for production monitoring.
