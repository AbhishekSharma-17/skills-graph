# Nuxt — Server Engine (Nitro)

> Source: [nuxt.com/docs/guide/directory-structure/server](https://nuxt.com/docs/guide/directory-structure/server)

## Table of Contents

- [Overview](#overview)
- [API Routes](#api-routes)
- [File Naming Conventions](#file-naming-conventions)
- [Request Handling](#request-handling)
- [Server Middleware](#server-middleware)
- [Server Plugins](#server-plugins)
- [Server Utilities](#server-utilities)
- [Server Storage](#server-storage)
- [Error Handling](#error-handling)
- [Streaming and Advanced Patterns](#streaming-and-advanced-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Nuxt uses **Nitro** as its server engine, powered by the **H3** HTTP framework. Nitro provides:

- Universal deployment (Node.js, serverless, edge, static)
- File-based API route scanning with HMR
- Auto-imported server utilities
- Cross-platform storage layer
- Route caching rules

The `server/` directory contains all backend code, completely separated from the Vue application in `app/`.

## API Routes

Each file in `server/api/` exports a default event handler and creates an API endpoint prefixed with `/api`:

```typescript
// server/api/hello.ts → GET /api/hello
export default defineEventHandler(() => {
  return { message: 'Hello from the API!' }
})
```

```typescript
// server/api/users.ts → /api/users (all methods)
export default defineEventHandler(async (event) => {
  const method = getMethod(event)

  if (method === 'GET') {
    return await db.users.findMany()
  }

  if (method === 'POST') {
    const body = await readBody(event)
    return await db.users.create(body)
  }
})
```

### Routes Without /api Prefix

Files in `server/routes/` create routes without the `/api` prefix:

```typescript
// server/routes/health.ts → GET /health
export default defineEventHandler(() => {
  return { status: 'ok', timestamp: Date.now() }
})
```

## File Naming Conventions

### Method-Specific Files

Append HTTP method as a suffix:

```
server/api/
├── users.get.ts            → GET /api/users
├── users.post.ts           → POST /api/users
├── users.put.ts            → PUT /api/users
└── users.delete.ts         → DELETE /api/users
```

### Dynamic Parameters

Use bracket notation:

```
server/api/
├── users/[id].ts           → /api/users/:id
├── users/[id].get.ts       → GET /api/users/:id
├── users/[id].patch.ts     → PATCH /api/users/:id
└── posts/[...slug].ts      → /api/posts/* (catch-all)
```

Access parameters:

```typescript
// server/api/users/[id].get.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  return await db.users.findById(id)
})
```

### Catch-All Routes

```typescript
// server/api/proxy/[...path].ts
export default defineEventHandler((event) => {
  const path = getRouterParam(event, 'path')
  // path = 'foo/bar/baz' for /api/proxy/foo/bar/baz
})
```

## Request Handling

### Reading Request Body

```typescript
// Plain body reading
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  return { received: body }
})

// Validated body with Zod
import { z } from 'zod'

const CreateUserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email()
})

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, CreateUserSchema.parse)
  return await db.users.create(body)
})
```

### Query Parameters

```typescript
export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  // /api/users?page=2&limit=10 → { page: '2', limit: '10' }

  // Validated query
  const validated = await getValidatedQuery(event, schema.parse)
})
```

### Request Headers

```typescript
export default defineEventHandler((event) => {
  const auth = getHeader(event, 'authorization')
  const contentType = getHeader(event, 'content-type')
})
```

### Cookies

```typescript
export default defineEventHandler((event) => {
  // Read
  const sessionId = getCookie(event, 'session-id')

  // Set
  setCookie(event, 'session-id', 'abc123', {
    httpOnly: true,
    secure: true,
    maxAge: 60 * 60 * 24 * 7 // 7 days
  })

  // Delete
  deleteCookie(event, 'old-cookie')
})
```

### Setting Response Status and Headers

```typescript
export default defineEventHandler((event) => {
  setResponseStatus(event, 201) // Created
  setHeader(event, 'X-Custom-Header', 'value')
  return { created: true }
})
```

### Redirects

```typescript
export default defineEventHandler((event) => {
  return sendRedirect(event, '/new-location', 301)
})
```

## Server Middleware

Server middleware runs on **every request** before any route handler. Place files in `server/middleware/`:

```typescript
// server/middleware/log.ts
export default defineEventHandler((event) => {
  console.log(`[${new Date().toISOString()}] ${event.method} ${event.path}`)
  // Don't return a value — middleware should not send a response
})
```

```typescript
// server/middleware/auth.ts
export default defineEventHandler((event) => {
  const token = getHeader(event, 'authorization')
  if (token) {
    event.context.user = verifyToken(token)
  }
})
```

Access middleware-set context in API routes:

```typescript
// server/api/profile.get.ts
export default defineEventHandler((event) => {
  const user = event.context.user
  if (!user) {
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  }
  return user
})
```

## Server Plugins

Nitro plugins hook into server lifecycle events. Place in `server/plugins/`:

```typescript
// server/plugins/database.ts
export default defineNitroPlugin(async (nitroApp) => {
  // Initialize database connection on server start
  const db = await connectDatabase()

  nitroApp.hooks.hook('request', (event) => {
    event.context.db = db
  })

  nitroApp.hooks.hook('close', async () => {
    await db.disconnect()
  })
})
```

### Available Hooks

| Hook | When |
|------|------|
| `request` | Every incoming request |
| `beforeResponse` | Before sending the response |
| `afterResponse` | After the response is sent |
| `close` | Server shutdown |
| `error` | Unhandled error |
| `render:html` | Before HTML rendering (SSR) |
| `render:response` | Before sending rendered response |

## Server Utilities

Auto-imported utility functions in `server/utils/`:

```typescript
// server/utils/db.ts
import { drizzle } from 'drizzle-orm/...'

export const db = drizzle(...)
```

```typescript
// server/utils/auth.ts
export function requireAuth(event: H3Event) {
  const user = event.context.user
  if (!user) {
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  }
  return user
}
```

Use in API routes without importing:

```typescript
// server/api/admin/stats.get.ts
export default defineEventHandler((event) => {
  const user = requireAuth(event) // Auto-imported from server/utils/
  return db.stats.getForUser(user.id)
})
```

## Server Storage

Nitro provides a cross-platform key-value storage layer:

```typescript
export default defineEventHandler(async (event) => {
  // Default storage (in-memory in dev, filesystem in production)
  await useStorage().setItem('cache:latest', { data: 'value' })
  const cached = await useStorage().getItem('cache:latest')

  // Named storage mount
  const assets = useStorage('assets:server')
})
```

Configure storage drivers in `nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  nitro: {
    storage: {
      redis: {
        driver: 'redis',
        port: 6379,
        host: '127.0.0.1'
      }
    }
  }
})
```

## Error Handling

### Throwing Errors

```typescript
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id')

  if (!id || isNaN(Number(id))) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Invalid ID',
      data: { field: 'id', reason: 'Must be a number' }
    })
  }

  const user = db.users.findById(id)
  if (!user) {
    throw createError({
      statusCode: 404,
      statusMessage: 'User not found'
    })
  }

  return user
})
```

### Global Error Handler

```typescript
// server/plugins/error-handler.ts
export default defineNitroPlugin((nitroApp) => {
  nitroApp.hooks.hook('error', (error) => {
    console.error('Server error:', error)
  })
})
```

## Streaming and Advanced Patterns

### Background Tasks

```typescript
export default defineEventHandler(async (event) => {
  const data = await readBody(event)

  event.waitUntil(
    sendNotificationEmail(data.email)
  )

  return { status: 'accepted' }
})
```

### Sending Files

```typescript
export default defineEventHandler(async (event) => {
  const stream = createReadStream('/path/to/file.pdf')
  setHeader(event, 'Content-Type', 'application/pdf')
  return sendStream(event, stream)
})
```

### Server-Sent Events

```typescript
export default defineEventHandler(async (event) => {
  const eventStream = createEventStream(event)

  const interval = setInterval(async () => {
    await eventStream.push({ data: JSON.stringify({ time: Date.now() }) })
  }, 1000)

  eventStream.onClosed(() => clearInterval(interval))

  return eventStream.send()
})
```

## Common Pitfalls

- **Returning from middleware** — Server middleware should NOT return a value. Returning data sends a response and stops further processing.
- **Using Vue APIs in server/** — The `server/` directory runs in Node.js. Vue composables (`ref`, `computed`, `useFetch`) are not available.
- **Forgetting method suffix** — `users.ts` handles ALL methods. Use `users.get.ts` to restrict to GET only.
- **Not validating input** — Always validate `readBody` and `getQuery` results. Use Zod or similar for type-safe validation.
- **Missing error handling** — Unhandled errors in event handlers result in 500 responses. Use `createError()` for structured error responses.
