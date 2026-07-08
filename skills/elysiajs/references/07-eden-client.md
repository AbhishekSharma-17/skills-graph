# ElysiaJS — Eden Client

> Source: [elysiajs.com/eden/overview](https://elysiajs.com/eden/overview) · Version 1.4.x

## Table of Contents

- [What Is Eden](#what-is-eden)
- [Eden Treaty Setup](#eden-treaty-setup)
- [Making Requests](#making-requests)
- [Response Handling](#response-handling)
- [Dynamic Path Parameters](#dynamic-path-parameters)
- [Headers and Configuration](#headers-and-configuration)
- [File Uploads](#file-uploads)
- [Streaming](#streaming)
- [WebSocket](#websocket)
- [Eden Fetch](#eden-fetch)
- [Unit Testing with Eden](#unit-testing-with-eden)
- [Common Pitfalls](#common-pitfalls)

---

## What Is Eden

Eden is an RPC-like client that connects to Elysia servers with end-to-end type safety using only TypeScript's type inference. It weighs under 2KB and requires no code generation — types flow directly from server route definitions to the client at compile time.

Eden has two modules:
- **Eden Treaty** (recommended) — Object-like API mapping paths to methods
- **Eden Fetch** — Fetch-style API with path strings

## Eden Treaty Setup

### Server Side

Export the app type from your server:

```typescript
// server.ts
import { Elysia, t } from 'elysia'

const app = new Elysia()
    .get('/hello', () => 'Hi Elysia')
    .get('/users/:id', ({ params: { id } }) => getUser(id), {
        params: t.Object({ id: t.Numeric() }),
        response: t.Object({
            id: t.Number(),
            name: t.String()
        })
    })
    .post('/users', ({ body }) => createUser(body), {
        body: t.Object({
            name: t.String(),
            email: t.String()
        }),
        response: {
            201: t.Object({ id: t.Number() }),
            400: t.Object({ error: t.String() })
        }
    })
    .listen(3000)

export type App = typeof app
```

### Client Side

```typescript
// client.ts
import { treaty } from '@elysia/eden'
import type { App } from './server'

const api = treaty<App>('localhost:3000')
```

Install: `bun add @elysia/eden`

The `type` import ensures no server code is bundled into the client — only TypeScript types are used.

## Making Requests

Eden Treaty maps URL paths to JavaScript property chains:

| HTTP | Path | Eden Treaty |
|------|------|-------------|
| GET | `/hello` | `api.hello.get()` |
| POST | `/users` | `api.users.post({ ... })` |
| PUT | `/users/:id` | `api.users({ id: 1 }).put({ ... })` |
| DELETE | `/users/:id` | `api.users({ id: 1 }).delete()` |

### Examples

```typescript
// GET /hello
const { data } = await api.hello.get()
// data: 'Hi Elysia'

// POST /users
const { data, error } = await api.users.post({
    name: 'Elysia',
    email: 'elysia@example.com'
})

// Nested paths: GET /api/v1/users
const { data } = await api.api.v1.users.get()
```

## Response Handling

Every Eden call returns `{ data, error, status, headers, response }`:

```typescript
const { data, error, status } = await api.users.post({
    name: 'Test',
    email: 'test@example.com'
})

if (error) {
    // error is typed based on response schema
    switch (error.status) {
        case 400:
            console.error(error.value.error)  // Typed as { error: string }
            break
        case 422:
            console.error('Validation error')
            break
    }
    return
}

// data is typed as { id: number } (status 201)
console.log(`Created user: ${data.id}`)
```

### Type Narrowing

Error checking narrows the type of `data`:

```typescript
const { data, error } = await api.users({ id: 1 }).get()

if (error) {
    // error is narrowed to the error response types
    return handleError(error)
}

// data is narrowed to the success response type
console.log(data.name)  // TypeScript knows this is valid
```

## Dynamic Path Parameters

Dynamic path segments use function call syntax:

```typescript
// Route: /users/:id
const { data } = await api.users({ id: 42 }).get()

// Route: /users/:id/posts/:postId
const { data } = await api.users({ id: 42 }).posts({ postId: 7 }).get()
```

The function syntax clearly indicates dynamic values vs. static path segments.

## Headers and Configuration

### Per-Request Headers

```typescript
const { data } = await api.protected.get({
    headers: {
        authorization: `Bearer ${token}`
    }
})
```

### Global Configuration

```typescript
const api = treaty<App>('localhost:3000', {
    headers: {
        authorization: `Bearer ${getToken()}`
    },
    // Or use a function for dynamic headers
    headers: () => ({
        authorization: `Bearer ${getToken()}`
    }),
    fetch: {
        credentials: 'include'
    },
    onRequest(path, options) {
        // Intercept before each request
        console.log(`Requesting: ${path}`)
    },
    onResponse(response) {
        // Intercept after each response
        if (response.status === 401) refreshToken()
    }
})
```

### Query Parameters

```typescript
// GET /search?q=elysia&page=1&limit=10
const { data } = await api.search.get({
    query: {
        q: 'elysia',
        page: 1,
        limit: 10
    }
})
```

## File Uploads

Eden handles file uploads with automatic multipart form-data:

```typescript
// Server
app.post('/upload', ({ body: { file } }) => saveFile(file), {
    body: t.Object({
        file: t.File()
    })
})

// Client
const { data } = await api.upload.post({
    file: new File(['content'], 'test.txt', { type: 'text/plain' })
})
```

## Streaming

Eden interprets streaming responses as `AsyncGenerator`:

```typescript
// Server
app.get('/stream', function* () {
    yield 'Hello '
    yield 'World'
})

// Client
const response = await api.stream.get()

for await (const chunk of response) {
    process.stdout.write(chunk)
}
```

## WebSocket

Eden Treaty supports type-safe WebSocket connections:

```typescript
// Server
app.ws('/chat', {
    body: t.Object({ message: t.String() }),
    message(ws, { message }) {
        ws.send({ reply: message.toUpperCase() })
    }
})

// Client
const ws = api.chat.subscribe()

ws.on('message', ({ data }) => {
    console.log(data.reply)  // Typed!
})

ws.send({ message: 'hello' })  // Typed!

ws.close()
```

Eden Fetch does NOT support WebSocket — use Eden Treaty for WS.

## Eden Fetch

An alternative fetch-style API for developers who prefer explicit path strings:

```typescript
import { edenFetch } from '@elysia/eden'
import type { App } from './server'

const fetch = edenFetch<App>('http://localhost:3000')

const { data, error } = await fetch('/users/:id', {
    method: 'GET',
    params: { id: '42' }
})

const { data } = await fetch('/users', {
    method: 'POST',
    body: {
        name: 'Elysia',
        email: 'elysia@example.com'
    }
})
```

### Treaty vs Fetch

| Feature | Eden Treaty | Eden Fetch |
|---------|-------------|------------|
| API style | Object notation | Path strings |
| WebSocket | Supported | Not supported |
| File upload | Automatic | Manual |
| DX | Better autocomplete | More explicit |

## Unit Testing with Eden

Eden Treaty can connect directly to an Elysia instance (no network):

```typescript
import { describe, expect, it } from 'bun:test'
import { treaty } from '@elysia/eden'
import { Elysia, t } from 'elysia'

describe('User API', () => {
    const app = new Elysia()
        .post('/users', ({ body }) => ({ id: 1, ...body }), {
            body: t.Object({ name: t.String() })
        })

    const api = treaty(app)  // Direct instance, no URL

    it('creates a user', async () => {
        const { data, error } = await api.users.post({ name: 'Test' })

        expect(error).toBeNull()
        expect(data?.id).toBe(1)
        expect(data?.name).toBe('Test')
    })
})
```

This approach tests the full request pipeline (validation, hooks, handlers) without network overhead.

## Common Pitfalls

1. **Type-only import** — Always use `import type { App }` to prevent bundling server code into the client.

2. **Eden needs exported type** — The server must export `typeof app`. Not exporting it (or exporting a subtype) breaks type inference.

3. **Path segments are property names** — `api.hello.world.get()` maps to `/hello/world`. Use dynamic params for variable segments: `api.users({ id: 1 })`.

4. **Error is null, not undefined** — When there's no error, `error` is `null`. Check with `if (error)`, not `if (error !== undefined)`.

5. **WebSocket only in Treaty** — Eden Fetch does not support WebSocket. Use `treaty()` if you need WS connections.

6. **Streaming auto-detection** — Eden automatically detects streaming responses. If a response that should stream comes back as a single value, ensure the server handler uses `yield`.
