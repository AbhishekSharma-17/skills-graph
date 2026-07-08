# ElysiaJS — Handler & Context

> Source: [elysiajs.com/essential/handler](https://elysiajs.com/essential/handler) · Version 1.4.x

## Table of Contents

- [Handlers](#handlers)
- [Context Properties](#context-properties)
- [Response Types](#response-types)
- [Status Codes](#status-codes)
- [Headers](#headers)
- [Redirects](#redirects)
- [Cookies](#cookies)
- [File Responses](#file-responses)
- [Streaming Responses](#streaming-responses)
- [Server-Sent Events](#server-sent-events)
- [Common Pitfalls](#common-pitfalls)

---

## Handlers

A handler is a function that receives a `Context` object and returns a response. Handlers can also be inline literal values for AOT-optimized responses.

```typescript
// Function handler — receives context
app.get('/hello', ({ query }) => `Hello ${query.name}`)

// Inline literal — AOT-optimized, fastest possible
app.get('/version', '1.0.0')

// Object literal — serialized as JSON
app.get('/config', { debug: false, version: '1.0.0' })
```

Inline literals enable Elysia's ahead-of-time compiler to generate optimized response code at startup.

## Context Properties

Every handler receives a `Context` object with request-specific data:

| Property | Type | Description |
|----------|------|-------------|
| `body` | `unknown` | Parsed request body (JSON, form-data, text) |
| `query` | `Record<string, string>` | URL query parameters |
| `params` | `Record<string, string>` | Path parameters |
| `headers` | `Record<string, string>` | Request headers (lowercase keys) |
| `cookie` | `Record<string, Cookie>` | Reactive cookie proxy |
| `path` | `string` | Request pathname |
| `request` | `Request` | Web Standard Request object |
| `store` | `object` | Global mutable state (shared across requests) |
| `set` | `object` | Mutable response configuration |
| `server` | `Server` | Bun server instance (Bun-only) |

### Destructuring Pattern

```typescript
app.post('/users', ({ body, headers, query, params, cookie, set }) => {
    const authToken = headers.authorization
    const page = query.page
    const userId = params.id
    const session = cookie.session.value

    set.status = 201
    set.headers['X-Request-Id'] = crypto.randomUUID()

    return createUser(body)
})
```

### The `set` Property

`set` is a mutable object for configuring the response:

```typescript
app.get('/example', ({ set }) => {
    set.status = 201                          // Status code
    set.headers['Content-Type'] = 'text/xml'  // Response headers
    set.redirect = '/other-path'              // Redirect
    return '<data>hello</data>'
})
```

## Response Types

ElysiaJS automatically serializes return values based on their type:

| Return Type | Content-Type | Behavior |
|-------------|-------------|----------|
| `string` | `text/plain` | Sent as-is |
| `object` / `array` | `application/json` | JSON.stringify |
| `number` / `boolean` | `text/plain` | String conversion |
| `Response` | From Response | Pass-through |
| `Blob` / `File` | From content | Binary response |
| `ReadableStream` | Streamed | Chunked transfer |
| Generator (`yield`) | Streamed | Auto-streaming |

### JSON Response

```typescript
app.get('/user', () => ({
    id: 1,
    name: 'Elysia',
    role: 'admin'
}))
```

### Web Standard Response

```typescript
app.get('/custom', () => {
    return new Response('Custom', {
        status: 200,
        headers: { 'X-Custom': 'value' }
    })
})
```

## Status Codes

### Using `status()` Utility

The `status()` function sets the HTTP status and enables type narrowing with Eden:

```typescript
import { Elysia, status, t } from 'elysia'

app.post('/users', ({ body }) => {
    const user = createUser(body)
    if (!user) return status(400, { error: 'Invalid input' })
    return status(201, user)
}, {
    body: t.Object({ name: t.String() }),
    response: {
        201: t.Object({ id: t.Number(), name: t.String() }),
        400: t.Object({ error: t.String() })
    }
})
```

### Using `set.status`

```typescript
app.post('/users', ({ body, set }) => {
    set.status = 201
    return createUser(body)
})
```

### Status Code Constants

```typescript
app.get('/teapot', () => status(418, "I'm a teapot"))
app.get('/gone', () => status(410, 'Resource removed'))
```

## Headers

### Setting Response Headers

```typescript
app.get('/api', ({ set }) => {
    set.headers['X-Powered-By'] = 'Elysia'
    set.headers['Cache-Control'] = 'max-age=3600'
    return { data: 'value' }
})
```

Elysia auto-completes header names in lowercase for consistency.

## Redirects

```typescript
// Simple redirect (302)
app.get('/old', ({ redirect }) => redirect('/new'))

// Redirect with status code
app.get('/moved', ({ redirect }) => redirect('/new-location', 301))

// Using set
app.get('/alt', ({ set }) => {
    set.redirect = '/destination'
})
```

## Cookies

Elysia provides a reactive cookie proxy — no get/set methods:

```typescript
app.get('/session', ({ cookie: { session } }) => {
    // Read
    const value = session.value

    // Write (automatically sets Set-Cookie header)
    session.value = { userId: 1, role: 'admin' }

    // Configure
    session.httpOnly = true
    session.maxAge = 60 * 60 * 24  // 1 day
    session.sameSite = 'strict'

    return value
})

// Remove a cookie
app.get('/logout', ({ cookie: { session } }) => {
    session.remove()
    return 'Logged out'
})
```

## File Responses

### Using `file()` Utility

```typescript
import { Elysia, file } from 'elysia'

app.get('/image', () => file('public/logo.png'))
app.get('/download', () => file('reports/q4.pdf'))
```

### Using `Bun.file()`

```typescript
app.get('/asset', () => Bun.file('public/style.css'))
```

### Form Data with Files

```typescript
import { Elysia, form } from 'elysia'

app.get('/form-data', () =>
    form({
        name: 'Elysia',
        avatar: Bun.file('public/avatar.png')
    })
)
```

## Streaming Responses

### Generator Functions

Return a generator to stream responses:

```typescript
app.get('/stream', function* () {
    yield 'Hello '
    yield 'World '
    yield '!'
})

// Async generator
app.get('/live', async function* () {
    for (let i = 0; i < 10; i++) {
        yield `data: ${JSON.stringify({ count: i })}\n\n`
        await new Promise(r => setTimeout(r, 1000))
    }
})
```

Headers must be set before the first `yield`. If a generator returns a value without yielding, it's treated as a normal response.

### Client-Side Streaming with Eden

Eden interprets streaming responses as `AsyncGenerator`:

```typescript
const stream = await app.stream.get()

for await (const chunk of stream) {
    console.log(chunk)
}
```

## Server-Sent Events

Use the `sse()` utility for SSE with proper formatting:

```typescript
app.get('/events', function* ({ sse }) {
    yield sse({ data: 'connected', event: 'open' })

    for (let i = 0; i < 100; i++) {
        yield sse({
            data: JSON.stringify({ count: i }),
            event: 'update',
            id: String(i)
        })
        await Bun.sleep(1000)
    }
})
```

## Common Pitfalls

1. **Headers after yield** — Setting headers or status codes after the first `yield` in a stream has no effect. Configure `set` before yielding.

2. **Store is shared** — `context.store` is global mutable state shared across all requests. Use it for app-level config, not request-scoped data. Use `derive()` for per-request state.

3. **Cookie proxy is always defined** — Accessing `cookie.name` never returns `undefined`; the proxy always exists. Check `.value` for actual cookie content.

4. **Body is undefined for GET** — GET requests have no body. Accessing `body` on a GET handler returns `undefined` unless explicitly parsed.

5. **Literal values skip hooks** — Inline literal responses still go through lifecycle hooks but skip body parsing since there's no request processing.
