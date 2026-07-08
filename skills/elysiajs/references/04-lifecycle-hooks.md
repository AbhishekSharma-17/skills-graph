# ElysiaJS — Lifecycle Hooks

> Source: [elysiajs.com/essential/life-cycle](https://elysiajs.com/essential/life-cycle) · Version 1.4.x

## Table of Contents

- [Lifecycle Overview](#lifecycle-overview)
- [Request Phase](#request-phase)
- [Parse Phase](#parse-phase)
- [Transform Phase](#transform-phase)
- [Derive](#derive)
- [Before Handle Phase](#before-handle-phase)
- [Resolve](#resolve)
- [Handler Execution](#handler-execution)
- [After Handle Phase](#after-handle-phase)
- [Map Response Phase](#map-response-phase)
- [On Error Phase](#on-error-phase)
- [After Response Phase](#after-response-phase)
- [Hook Scoping](#hook-scoping)
- [Hook Ordering](#hook-ordering)
- [Common Pitfalls](#common-pitfalls)

---

## Lifecycle Overview

ElysiaJS processes each request through an ordered pipeline of lifecycle events. Each phase can inspect, modify, or short-circuit the request.

```
Request → Parse → Transform → beforeHandle → Handler → afterHandle → mapResponse
                                                                          ↓
                                                              afterResponse
                     onError ←── (catches errors from any phase)
```

Lifecycle hooks come in two forms:
- **Local hooks** — inline on a specific route
- **Interceptor hooks** — registered via `.on*()` methods, apply to routes registered after them

## Request Phase

`onRequest` is the first lifecycle event and the only truly global hook — it runs before route matching.

```typescript
app.onRequest(({ request, set }) => {
    console.log(`${request.method} ${request.url}`)
})
```

`onRequest` receives a minimal `PreContext` (no body, params, or query) to minimize overhead.

**Use cases:** Logging, rate limiting, CORS, analytics, caching.

**Short-circuit:** Returning a value from `onRequest` skips all remaining lifecycle phases:

```typescript
app.onRequest(({ request }) => {
    if (isBlocked(request)) return new Response('Forbidden', { status: 403 })
})
```

## Parse Phase

Parses the request body into `Context.body`. Elysia auto-detects JSON, form-data, and plain text.

### Custom Parser

```typescript
app.onParse(({ request, contentType }) => {
    if (contentType === 'application/xml') {
        return parseXml(request)
    }
})
```

### Named Parser

```typescript
app.parser('csv', async ({ request }) => {
    const text = await request.text()
    return text.split('\n').map(row => row.split(','))
})

app.post('/import', ({ body }) => body, {
    parse: 'csv'
})
```

### Skip Parsing

```typescript
app.post('/raw', ({ request }) => request.text(), {
    parse: 'none'
})
```

## Transform Phase

Mutates context before validation. Executes in the same queue as `derive`.

```typescript
app.onTransform(({ query }) => {
    // Normalize query parameters before validation
    if (query.page) query.page = Math.max(1, Number(query.page))
})
```

### Use Cases

- Normalize data before validation
- Add computed fields to the context
- Convert between formats

## Derive

Adds new properties to the context before validation without sharing state across requests. Each call creates fresh values per request.

```typescript
app.derive(({ headers }) => {
    const auth = headers.authorization?.split(' ')[1]
    return {
        bearer: auth
    }
})

app.get('/protected', ({ bearer }) => {
    // bearer is typed and available
    return `Token: ${bearer}`
})
```

### Derive with Async

```typescript
app.derive(async ({ headers }) => {
    const token = headers.authorization?.split(' ')[1]
    const user = token ? await verifyToken(token) : null
    return { user }
})
```

`derive` runs in the same queue as `transform`, before validation.

## Before Handle Phase

Executes after validation. Ideal for authorization, permission checks, and custom validation.

```typescript
app.onBeforeHandle(({ bearer, set }) => {
    if (!bearer) {
        set.status = 401
        return { error: 'Unauthorized' }
    }
})
```

**Short-circuit:** Returning a value from `beforeHandle` skips the route handler and subsequent `beforeHandle` hooks:

```typescript
app.onBeforeHandle(({ query }) => {
    const cached = cache.get(query.key)
    if (cached) return cached  // Skip handler, return cached value
})
```

### Guard with beforeHandle

```typescript
app.guard({
    beforeHandle({ cookie: { session } }) {
        if (!session.value) return status(401, 'Login required')
    }
}, (app) =>
    app
        .get('/dashboard', getDashboard)
        .get('/settings', getSettings)
)
```

## Resolve

Similar to `derive` but executes after validation, providing type-safe access to validated data:

```typescript
app.resolve(({ headers }) => {
    const token = headers.authorization?.split(' ')[1]
    return {
        user: decodeJwt(token)
    }
})

app.get('/me', ({ user }) => user)
```

`resolve` shares the execution queue with `beforeHandle`. The key difference from `derive`: `resolve` runs after validation, so the data it accesses is guaranteed valid.

## Handler Execution

The route handler executes after all `beforeHandle` hooks pass without returning a value.

```typescript
app.get('/users/:id', async ({ params: { id } }) => {
    const user = await db.users.findById(id)
    if (!user) return status(404, { error: 'Not found' })
    return user
})
```

## After Handle Phase

Transforms the handler's return value. Useful for response wrapping, compression headers, or content negotiation.

```typescript
app.onAfterHandle(({ response, set }) => {
    if (typeof response === 'object') {
        set.headers['Content-Type'] = 'application/json; charset=utf-8'
    }
})
```

**Key behavior:** Returning `undefined` preserves the original response. Unlike `beforeHandle`, all `afterHandle` hooks execute even if one returns a value.

### Response Wrapping

```typescript
app.onAfterHandle(({ response }) => {
    return {
        success: true,
        data: response,
        timestamp: Date.now()
    }
})
```

## Map Response Phase

Final transformation before sending. Receives the value that will become the HTTP response.

```typescript
app.mapResponse(({ response, set }) => {
    if (typeof response === 'object') {
        return new Response(JSON.stringify(response), {
            headers: { 'Content-Type': 'application/json' }
        })
    }
})
```

**Use cases:** Compression, format conversion, response envelope.

Returning a value from `mapResponse` skips subsequent `mapResponse` hooks.

## On Error Phase

Catches errors thrown from any lifecycle phase:

```typescript
app.onError(({ code, error, set }) => {
    switch (code) {
        case 'NOT_FOUND':
            set.status = 404
            return { error: 'Resource not found' }
        case 'VALIDATION':
            set.status = 422
            return { error: 'Invalid input', details: error.message }
        case 'INTERNAL_SERVER_ERROR':
            console.error(error)
            set.status = 500
            return { error: 'Internal error' }
    }
})
```

### Error Codes

| Code | Trigger |
|------|---------|
| `NOT_FOUND` | No matching route |
| `VALIDATION` | Schema validation failure |
| `PARSE` | Body parsing failure |
| `INTERNAL_SERVER_ERROR` | Unhandled exception |
| `UNKNOWN` | Custom or unclassified error |
| Custom codes | Registered via `.error()` |

## After Response Phase

Executes after the response is sent to the client. Ideal for cleanup, logging, and metrics.

```typescript
app.onAfterResponse(({ request, set, path }) => {
    const duration = performance.now() - startTime
    logger.info({
        method: request.method,
        path,
        status: set.status,
        duration
    })
})
```

Cannot modify the response — it's already sent. Access `set` for status and headers that were used.

## Hook Scoping

Hooks have three scope levels controlling propagation:

| Scope | Applies To | Use Case |
|-------|-----------|----------|
| `local` (default) | Current instance only | Standard middleware |
| `scoped` | Parent + current + descendants | Family-chain middleware |
| `global` | All instances using this plugin | Cross-cutting concerns |

### Setting Scope

```typescript
// Inline — per hook
app.onBeforeHandle({ as: 'global' }, authCheck)

// Instance-level — all hooks in plugin
const authPlugin = new Elysia()
    .onBeforeHandle(authCheck)
    .as('scoped')

// Guard — all hooks in guard
app.guard({ as: 'scoped', beforeHandle: authCheck })
```

## Hook Ordering

**Critical rule:** Hooks only apply to routes registered *after* the hook declaration.

```typescript
app.get('/public', () => 'Anyone')       // No auth check

app.onBeforeHandle(authCheck)             // Registered here

app.get('/private', () => 'Authorized')   // Auth check applies
```

Exception: `onRequest` is global and applies to all routes regardless of registration order, since it executes before route matching.

## Common Pitfalls

1. **Hook registration order** — Hooks must be registered *before* the routes they protect. A common mistake is placing `onBeforeHandle` after route definitions.

2. **derive vs resolve timing** — `derive` runs before validation (access raw data), `resolve` runs after validation (access validated data). Choose based on whether you need validated input.

3. **Short-circuit semantics differ** — `beforeHandle` stops on first return; `afterHandle` continues all hooks even after a return. This is by design.

4. **Scope propagation** — Hooks are `local` by default. If a hook in a plugin doesn't apply to routes in the parent, you forgot to set `as: 'scoped'` or `as: 'global'`.

5. **onError catches throws, not returns** — `throw status(418)` is caught by `onError`; `return status(418)` bypasses error handling entirely.
