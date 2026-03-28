# Hono — RPC & Type Safety

> Source: [hono.dev/docs/guides/rpc](https://hono.dev/docs/guides/rpc)

## Overview

Hono's RPC feature provides end-to-end type safety between server and client without code generation. By exporting your app's type and using the `hc` client, TypeScript infers request/response types automatically.

## Server Setup

### Chaining Routes (Critical for RPC)

Routes **must be chained** for type inference to work:

```typescript
import { Hono } from 'hono'
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'

const app = new Hono()

// CORRECT: Chain route definitions
const route = app
  .get('/api/posts', (c) => {
    return c.json({
      posts: [
        { id: '1', title: 'Hello', body: 'World' }
      ]
    })
  })
  .post('/api/posts',
    zValidator('json', z.object({
      title: z.string(),
      body: z.string(),
    })),
    (c) => {
      const data = c.req.valid('json')
      return c.json({ ok: true, post: { id: '2', ...data } }, 201)
    }
  )
  .get('/api/posts/:id', (c) => {
    const id = c.req.param('id')
    return c.json({ id, title: 'Hello', body: 'World' })
  })

// Export the type
export type AppType = typeof route
```

### Using app.route() with RPC

When splitting routes across files, chain within each sub-app:

```typescript
// routes/posts.ts
import { Hono } from 'hono'

const posts = new Hono()
  .get('/', (c) => c.json({ posts: [] }))
  .post('/', (c) => c.json({ created: true }, 201))
  .get('/:id', (c) => c.json({ id: c.req.param('id') }))

export default posts
```

```typescript
// routes/users.ts
import { Hono } from 'hono'

const users = new Hono()
  .get('/', (c) => c.json({ users: [] }))
  .get('/:id', (c) => c.json({ id: c.req.param('id') }))

export default users
```

```typescript
// index.ts
import { Hono } from 'hono'
import posts from './routes/posts'
import users from './routes/users'

const app = new Hono()
  .route('/api/posts', posts)
  .route('/api/users', users)

export type AppType = typeof app
```

## Client Setup

### Installation

The `hc` client is included in the `hono` package:

```typescript
import { hc } from 'hono/client'
import type { AppType } from './server'

const client = hc<AppType>('http://localhost:8787')
```

### Making Requests

```typescript
// GET request
const res = await client.api.posts.$get()
const data = await res.json()
// data is typed as { posts: { id: string; title: string; body: string }[] }

// POST request with JSON body
const res = await client.api.posts.$post({
  json: {
    title: 'New Post',
    body: 'Content here',
  }
})
const result = await res.json()
// result is typed as { ok: boolean; post: { id: string; title: string; body: string } }

// GET with path parameters
const res = await client.api.posts[':id'].$get({
  param: { id: '123' }
})
```

### Request with Query Parameters

```typescript
// Server
const route = app.get('/api/search',
  zValidator('query', z.object({
    q: z.string(),
    page: z.coerce.number().optional(),
  })),
  (c) => {
    const { q, page } = c.req.valid('query')
    return c.json({ results: [], query: q, page })
  }
)

// Client
const res = await client.api.search.$get({
  query: { q: 'hono', page: '1' }
})
```

### Request with Headers

```typescript
const res = await client.api.posts.$get(undefined, {
  headers: {
    Authorization: 'Bearer my-token',
    'X-Custom-Header': 'value',
  }
})
```

### Request with Form Data

```typescript
const res = await client.api.posts.$post({
  form: {
    title: 'Hello',
    body: 'World',
  }
})
```

## Using with SWR/TanStack Query

### With SWR

```typescript
import useSWR from 'swr'
import { hc } from 'hono/client'
import type { AppType } from './server'

const client = hc<AppType>('http://localhost:8787')

function PostList() {
  const { data, error } = useSWR('/api/posts', async () => {
    const res = await client.api.posts.$get()
    return await res.json()
  })

  if (error) return <div>Error</div>
  if (!data) return <div>Loading...</div>

  return (
    <ul>
      {data.posts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  )
}
```

### With TanStack Query

```typescript
import { useQuery } from '@tanstack/react-query'
import { hc } from 'hono/client'
import type { AppType } from './server'

const client = hc<AppType>('http://localhost:8787')

function PostList() {
  const { data, isLoading } = useQuery({
    queryKey: ['posts'],
    queryFn: async () => {
      const res = await client.api.posts.$get()
      return res.json()
    },
  })

  return data ? (
    <ul>{data.posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>
  ) : null
}
```

## Generating URL Strings

Use the `$url()` method to get typed URLs without making requests:

```typescript
const url = client.api.posts.$url()
// URL { href: 'http://localhost:8787/api/posts' }

const url = client.api.posts[':id'].$url({
  param: { id: '123' }
})
// URL { href: 'http://localhost:8787/api/posts/123' }
```

## Custom Fetch

Pass a custom fetch function for interceptors:

```typescript
const client = hc<AppType>('http://localhost:8787', {
  fetch: async (input, init) => {
    // Add auth header
    const headers = new Headers(init?.headers)
    headers.set('Authorization', `Bearer ${getToken()}`)
    return fetch(input, { ...init, headers })
  }
})
```

## Common Pitfalls

1. **Not chaining routes** — `app.get()` followed by `app.post()` separately loses type info; chain with `.get().post()`
2. **Importing the app value instead of type** — Use `import type { AppType }` to avoid bundling server code
3. **Declaring route variable separately** — The variable must capture the chained result: `const route = app.get()...`
4. **Forgetting to export AppType** — The client needs the type export to infer endpoints
5. **Query params as numbers** — The `hc` client sends query params as strings; use `z.coerce` on the server
6. **Wrong client path structure** — Client paths mirror the route structure: `/api/posts/:id` becomes `client.api.posts[':id']`
