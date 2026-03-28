# Hono — Validation

> Source: [hono.dev/docs/guides/validation](https://hono.dev/docs/guides/validation)

## Overview

Hono has a built-in validation system and first-class integration with Zod via `@hono/zod-validator`. Validated data is fully typed and accessible through `c.req.valid()`.

## Built-in Validator

Hono provides a `validator` function for manual validation:

```typescript
import { Hono } from 'hono'
import { validator } from 'hono/validator'

const app = new Hono()

app.post('/posts',
  validator('json', (value, c) => {
    const { title, body } = value
    if (!title || typeof title !== 'string') {
      return c.text('Invalid title', 400)
    }
    if (!body || typeof body !== 'string') {
      return c.text('Invalid body', 400)
    }
    return { title, body } // Return parsed data
  }),
  (c) => {
    const { title, body } = c.req.valid('json')
    return c.json({ title, body }, 201)
  }
)
```

### Validation Targets

| Target | Description | Example |
|--------|-------------|---------|
| `'json'` | JSON request body | `validator('json', ...)` |
| `'form'` | Form/multipart data | `validator('form', ...)` |
| `'query'` | Query parameters | `validator('query', ...)` |
| `'header'` | Request headers | `validator('header', ...)` |
| `'param'` | Path parameters | `validator('param', ...)` |
| `'cookie'` | Cookies | `validator('cookie', ...)` |

## Zod Validator (Recommended)

The `@hono/zod-validator` package provides seamless Zod integration:

### Installation

```bash
npm install @hono/zod-validator zod
```

### Basic Usage

```typescript
import { Hono } from 'hono'
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'

const app = new Hono()

const createPostSchema = z.object({
  title: z.string().min(1).max(200),
  body: z.string().min(1),
  tags: z.array(z.string()).optional(),
})

app.post('/posts',
  zValidator('json', createPostSchema),
  (c) => {
    const data = c.req.valid('json')
    // data is typed as { title: string; body: string; tags?: string[] }
    return c.json({ ...data, id: 'new-id' }, 201)
  }
)
```

### Multiple Validators

Validate multiple parts of the request:

```typescript
const paramsSchema = z.object({
  id: z.string().uuid(),
})

const bodySchema = z.object({
  title: z.string().min(1),
  body: z.string().min(1),
})

app.put('/posts/:id',
  zValidator('param', paramsSchema),
  zValidator('json', bodySchema),
  (c) => {
    const { id } = c.req.valid('param')
    const data = c.req.valid('json')
    return c.json({ id, ...data })
  }
)
```

### Query Parameter Validation

```typescript
const searchSchema = z.object({
  q: z.string().min(1),
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sort: z.enum(['asc', 'desc']).default('desc'),
})

app.get('/search',
  zValidator('query', searchSchema),
  (c) => {
    const { q, page, limit, sort } = c.req.valid('query')
    return c.json({ q, page, limit, sort })
  }
)
```

### Header Validation

```typescript
const headerSchema = z.object({
  'x-api-version': z.enum(['v1', 'v2']),
  'x-request-id': z.string().uuid().optional(),
})

app.use('/api/*',
  zValidator('header', headerSchema),
)
```

### Form Data Validation

```typescript
const formSchema = z.object({
  title: z.string(),
  body: z.string(),
})

app.post('/posts',
  zValidator('form', formSchema),
  (c) => {
    const data = c.req.valid('form')
    return c.json({ message: 'Created!', ...data }, 201)
  }
)
```

### Custom Error Handling

Override the default error response:

```typescript
app.post('/posts',
  zValidator('json', createPostSchema, (result, c) => {
    if (!result.success) {
      return c.json({
        error: 'Validation failed',
        details: result.error.flatten(),
      }, 422)
    }
  }),
  (c) => {
    const data = c.req.valid('json')
    return c.json(data, 201)
  }
)
```

### Reusable Error Handler

```typescript
import type { ZodSchema } from 'zod'
import type { ValidationTargets } from 'hono'

const zodHook = (result: { success: boolean; error?: any }, c: any) => {
  if (!result.success) {
    return c.json({
      success: false,
      errors: result.error.flatten().fieldErrors,
    }, 422)
  }
}

// Use consistently
app.post('/posts',
  zValidator('json', createPostSchema, zodHook),
  handler
)

app.put('/posts/:id',
  zValidator('param', paramsSchema, zodHook),
  zValidator('json', updatePostSchema, zodHook),
  handler
)
```

## Validation with RPC

Validators work seamlessly with the RPC client — validated input types are inferred on the client:

```typescript
// Server
const route = app.post('/posts',
  zValidator('json', createPostSchema),
  (c) => {
    const data = c.req.valid('json')
    return c.json({ ok: true, post: { id: '1', ...data } }, 201)
  }
)

export type AppType = typeof route
```

```typescript
// Client — input types are inferred from Zod schema
import { hc } from 'hono/client'
import type { AppType } from './server'

const client = hc<AppType>('http://localhost:8787')

const res = await client.posts.$post({
  json: {
    title: 'Hello',  // TypeScript knows this is required
    body: 'World',   // TypeScript knows this is required
    tags: ['test'],   // TypeScript knows this is optional string[]
  }
})
```

## Common Pitfalls

1. **Forgetting `z.coerce` for query params** — Query parameters are always strings; use `z.coerce.number()` for numbers
2. **Not installing `@hono/zod-validator`** — It's a separate package, not included in `hono`
3. **Wrong validation target** — Use `'json'` for JSON body, `'form'` for form data, `'query'` for URL params
4. **Not handling validation errors** — Default behavior returns 400; use the hook callback for custom error format
5. **Importing from wrong package** — Use `@hono/zod-validator`, not `hono/zod-validator`
