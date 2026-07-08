# ElysiaJS — State, Decorate, Derive & Resolve

> Source: [elysiajs.com](https://elysiajs.com/) · Version 1.4.x

## Table of Contents

- [Overview](#overview)
- [State](#state)
- [Decorate](#decorate)
- [Derive](#derive)
- [Resolve](#resolve)
- [Comparison Matrix](#comparison-matrix)
- [Patterns](#patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

ElysiaJS provides four mechanisms for adding properties to the handler context. They differ in timing (when they execute), mutability, and scope (per-request vs. global).

| Method | Timing | Scope | Mutable | Accessed Via |
|--------|--------|-------|---------|-------------|
| `state()` | Setup | Global (all requests) | Yes | `store` |
| `decorate()` | Setup | Global (all requests) | Read-only convention | Direct context |
| `derive()` | Per request, before validation | Per request | Yes | Direct context |
| `resolve()` | Per request, after validation | Per request | Yes | Direct context |

## State

`state()` adds values to `Context.store`, a global mutable object shared across all requests. Use it for app-level counters, config, or shared caches.

### Basic Usage

```typescript
const app = new Elysia()
    .state('version', '1.0.0')
    .state('requestCount', 0)
    .get('/', ({ store }) => {
        store.requestCount++
        return {
            version: store.version,
            requests: store.requestCount
        }
    })
```

### Object State

```typescript
app.state({
    config: { debug: false, maxRetries: 3 },
    cache: new Map<string, unknown>()
})

app.get('/config', ({ store }) => store.config)
```

### Type Safety

State is fully typed. TypeScript will error if you access an undeclared state key:

```typescript
app.state('count', 0)
   .get('/', ({ store }) => {
       store.count++      // OK — typed as number
       store.missing       // Error — 'missing' not declared
   })
```

## Decorate

`decorate()` adds immutable (by convention) properties directly to the context. Use it for services, database connections, and utilities that are the same for every request.

### Basic Usage

```typescript
const app = new Elysia()
    .decorate('db', new Database())
    .decorate('logger', createLogger())
    .get('/users', ({ db }) => db.users.findMany())
    .post('/log', ({ logger, body }) => {
        logger.info(body)
        return 'logged'
    })
```

### Object Decorate

```typescript
app.decorate({
    db: new Database(),
    cache: new RedisClient(),
    mailer: new MailService()
})
```

### Difference from State

- `decorate` → accessed directly on context (`{ db }`)
- `state` → accessed via `store` property (`{ store: { count } }`)
- Both are global, but `decorate` signals "don't mutate this per-request"

## Derive

`derive()` creates new per-request context properties. It runs before validation and each invocation is fresh per request — no shared state.

### Basic Usage

```typescript
app.derive(({ headers }) => {
    return {
        bearer: headers.authorization?.split(' ')[1] ?? null
    }
})

app.get('/protected', ({ bearer }) => {
    if (!bearer) return status(401)
    return `Token: ${bearer}`
})
```

### Async Derive

```typescript
app.derive(async ({ headers }) => {
    const token = headers.authorization?.split(' ')[1]
    if (!token) return { user: null }

    const user = await db.users.findByToken(token)
    return { user }
})
```

### Derive with Request Context

```typescript
app.derive(({ request, server }) => ({
    ip: server?.requestIP(request)?.address ?? '0.0.0.0',
    userAgent: request.headers.get('user-agent') ?? 'unknown',
    requestId: crypto.randomUUID()
}))
```

### Scoped Derive

By default, `derive` is local. Promote to parent scope:

```typescript
const plugin = new Elysia()
    .derive({ as: 'scoped' }, ({ headers }) => ({
        apiKey: headers['x-api-key']
    }))

app.use(plugin)
   .get('/key', ({ apiKey }) => apiKey)  // Works — scoped to parent
```

## Resolve

`resolve()` is similar to `derive` but executes after validation. This means the data it accesses has already been validated, making it safer for security-sensitive operations.

### Basic Usage

```typescript
app.resolve(({ headers }) => {
    const token = headers.authorization?.split(' ')[1]
    if (!token) throw new Error('No token')
    return { user: decodeJwt(token) }
})
```

### Resolve After Validation

```typescript
app.post('/checkout', ({ user, body }) => {
    return processOrder(user.id, body)
}, {
    headers: t.Object({
        authorization: t.String()
    }),
    body: t.Object({
        items: t.Array(t.Object({
            id: t.Number(),
            quantity: t.Number()
        }))
    }),
    resolve({ headers }) {
        const token = headers.authorization.split(' ')[1]
        return { user: verifyJwt(token) }
    }
})
```

### Resolve vs Derive

| Aspect | `derive()` | `resolve()` |
|--------|-----------|------------|
| Timing | Before validation | After validation |
| Queue | Same as `transform` | Same as `beforeHandle` |
| Input data | Raw, unvalidated | Validated by schema |
| Use case | Parse auth headers, add request IDs | Decode verified tokens, load user |

## Comparison Matrix

```
Setup time (run once):
  state()     → store.key     → Mutable global counter/config
  decorate()  → context.key   → Immutable services/utilities

Per request (run every request):
  derive()    → context.key   → Before validation — raw parsing
  resolve()   → context.key   → After validation — secure resolution
```

### Decision Guide

```
Need it for every request, same value? → decorate()
Need mutable shared state?             → state()
Need per-request data from raw input?  → derive()
Need per-request data from validated input? → resolve()
```

## Patterns

### Service Layer Pattern

```typescript
const services = new Elysia({ name: 'services' })
    .decorate('userService', new UserService(db))
    .decorate('postService', new PostService(db))
    .decorate('emailService', new EmailService(smtp))

const app = new Elysia()
    .use(services)
    .post('/users', ({ userService, emailService, body }) => {
        const user = userService.create(body)
        emailService.sendWelcome(user.email)
        return user
    })
```

### Request Context Pattern

```typescript
const requestContext = new Elysia({ name: 'request-context' })
    .derive({ as: 'global' }, ({ request, server }) => ({
        requestId: crypto.randomUUID(),
        ip: server?.requestIP(request)?.address ?? 'unknown',
        startTime: performance.now()
    }))
    .onAfterResponse({ as: 'global' }, ({ requestId, startTime, path }) => {
        console.log(`[${requestId}] ${path} ${(performance.now() - startTime).toFixed(1)}ms`)
    })
```

### Auth Chain Pattern

```typescript
const auth = new Elysia({ name: 'auth' })
    .derive({ as: 'scoped' }, ({ headers }) => ({
        bearer: headers.authorization?.replace('Bearer ', '') ?? null
    }))
    .resolve({ as: 'scoped' }, async ({ bearer }) => {
        if (!bearer) return { user: null, role: null }
        const payload = await verifyJwt(bearer)
        return {
            user: payload,
            role: payload.role as 'admin' | 'user'
        }
    })
```

### Config + State Pattern

```typescript
const app = new Elysia()
    .state({
        hitCount: 0,
        startedAt: Date.now()
    })
    .decorate({
        config: {
            apiVersion: 'v1',
            rateLimit: 100
        }
    })
    .get('/stats', ({ store, config }) => ({
        hits: store.hitCount,
        uptime: Date.now() - store.startedAt,
        version: config.apiVersion
    }))
    .onRequest(({ store }) => {
        store.hitCount++
    })
```

## Common Pitfalls

1. **Mutating decorate values** — `decorate` values are shared across all requests. Mutating them causes race conditions. Use `state` for mutable globals or `derive` for per-request data.

2. **Derive accessing body** — `derive` runs before body parsing in some cases. For body-dependent logic, use `resolve` (runs after validation) or `beforeHandle`.

3. **Order of derive/resolve** — `derive` and `resolve` add to context in registration order. A second `derive` can access properties from the first.

4. **Global state thread safety** — Bun is single-threaded, so `store` mutations are safe in a single process. But with clustering, use external state (Redis, DB) instead.

5. **Type inference chain** — Each `derive`/`resolve`/`state`/`decorate` extends the context type. Breaking the chain (e.g., extracting handlers into separate functions without proper typing) loses type inference.
