# Hono — Testing

> Source: [hono.dev/docs/guides/testing](https://hono.dev/docs/guides/testing)

## Overview

Testing Hono apps is straightforward because Hono is built on Web Standards. You don't need to start a server — just pass a `Request` to `app.request()` and assert on the `Response`. The recommended test runner is Vitest.

## Setup

### Install Vitest

```bash
npm install -D vitest
```

### Package.json Script

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

## Basic Testing with app.request()

### GET Request

```typescript
import { describe, it, expect } from 'vitest'
import app from '../src/index'

describe('GET /', () => {
  it('should return 200', async () => {
    const res = await app.request('/')
    expect(res.status).toBe(200)
    expect(await res.text()).toBe('Hello Hono!')
  })
})
```

### JSON Response

```typescript
describe('GET /api/posts', () => {
  it('should return posts', async () => {
    const res = await app.request('/api/posts')
    expect(res.status).toBe(200)

    const data = await res.json()
    expect(data).toHaveProperty('posts')
    expect(Array.isArray(data.posts)).toBe(true)
  })
})
```

### POST Request

```typescript
describe('POST /api/posts', () => {
  it('should create a post', async () => {
    const res = await app.request('/api/posts', {
      method: 'POST',
      body: JSON.stringify({
        title: 'Test Post',
        body: 'Test body content',
      }),
      headers: new Headers({
        'Content-Type': 'application/json',
      }),
    })

    expect(res.status).toBe(201)
    const data = await res.json()
    expect(data.ok).toBe(true)
  })
})
```

### PUT Request

```typescript
describe('PUT /api/posts/:id', () => {
  it('should update a post', async () => {
    const res = await app.request('/api/posts/123', {
      method: 'PUT',
      body: JSON.stringify({ title: 'Updated Title' }),
      headers: new Headers({
        'Content-Type': 'application/json',
      }),
    })

    expect(res.status).toBe(200)
  })
})
```

### DELETE Request

```typescript
describe('DELETE /api/posts/:id', () => {
  it('should delete a post', async () => {
    const res = await app.request('/api/posts/123', {
      method: 'DELETE',
    })
    expect(res.status).toBe(204)
  })
})
```

## Using Request Object

Pass a full `Request` object for more control:

```typescript
it('should handle request with custom URL', async () => {
  const req = new Request('http://localhost/api/posts?page=2', {
    method: 'GET',
    headers: {
      Authorization: 'Bearer test-token',
    },
  })
  const res = await app.request(req)
  expect(res.status).toBe(200)
})
```

## Testing with FormData

```typescript
it('should handle form submission', async () => {
  const formData = new FormData()
  formData.append('title', 'Test Post')
  formData.append('body', 'Test content')

  const res = await app.request('/api/posts', {
    method: 'POST',
    body: formData,
  })

  expect(res.status).toBe(201)
})
```

## Testing Headers

```typescript
it('should set custom headers', async () => {
  const res = await app.request('/api/data')
  expect(res.headers.get('X-Custom-Header')).toBe('custom-value')
  expect(res.headers.get('Content-Type')).toContain('application/json')
})
```

## Environment Mocking

Pass mock environment variables as the third argument to `app.request()`:

```typescript
// For Cloudflare Workers bindings
describe('with env bindings', () => {
  const mockEnv = {
    DATABASE_URL: 'postgresql://test:test@localhost:5432/test',
    API_KEY: 'test-api-key',
    MY_KV: {
      get: async (key: string) => 'mocked-value',
      put: async (key: string, value: string) => {},
    },
  }

  it('should use env bindings', async () => {
    const res = await app.request('/api/data', {}, mockEnv)
    expect(res.status).toBe(200)
  })
})
```

## Testing Middleware

Test middleware by creating a minimal app with the middleware:

```typescript
import { Hono } from 'hono'
import { authMiddleware } from '../src/middleware/auth'

describe('authMiddleware', () => {
  const app = new Hono()

  app.use('/protected/*', authMiddleware)
  app.get('/protected/data', (c) => c.json({ secret: 'data' }))

  it('should reject without token', async () => {
    const res = await app.request('/protected/data')
    expect(res.status).toBe(401)
  })

  it('should accept with valid token', async () => {
    const res = await app.request('/protected/data', {
      headers: { Authorization: 'Bearer valid-token' },
    })
    expect(res.status).toBe(200)
  })
})
```

## Testing Validation

```typescript
describe('POST /api/posts with validation', () => {
  it('should reject invalid input', async () => {
    const res = await app.request('/api/posts', {
      method: 'POST',
      body: JSON.stringify({ title: '' }), // Missing required 'body'
      headers: new Headers({
        'Content-Type': 'application/json',
      }),
    })
    expect(res.status).toBe(400)
  })

  it('should accept valid input', async () => {
    const res = await app.request('/api/posts', {
      method: 'POST',
      body: JSON.stringify({
        title: 'Valid Title',
        body: 'Valid body content',
      }),
      headers: new Headers({
        'Content-Type': 'application/json',
      }),
    })
    expect(res.status).toBe(201)
  })
})
```

## Cloudflare Workers Testing

Use `@cloudflare/vitest-pool-workers` for testing with Cloudflare bindings:

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    pool: '@cloudflare/vitest-pool-workers',
    poolOptions: {
      workers: {
        wrangler: { configPath: './wrangler.toml' },
      },
    },
  },
})
```

## Testing Patterns

### Test Helpers

```typescript
// test/helpers.ts
import app from '../src/index'

export async function apiGet(path: string, headers?: Record<string, string>) {
  return app.request(path, {
    headers: new Headers(headers),
  })
}

export async function apiPost(path: string, body: unknown, headers?: Record<string, string>) {
  return app.request(path, {
    method: 'POST',
    body: JSON.stringify(body),
    headers: new Headers({
      'Content-Type': 'application/json',
      ...headers,
    }),
  })
}
```

### Test Organization

```
tests/
├── routes/
│   ├── posts.test.ts
│   ├── users.test.ts
│   └── auth.test.ts
├── middleware/
│   ├── auth.test.ts
│   └── validation.test.ts
├── helpers.ts
└── setup.ts
```

## Common Pitfalls

1. **Not awaiting `app.request()`** — It returns a `Promise<Response>`; always `await` it
2. **Forgetting Content-Type for JSON** — Set `Content-Type: application/json` for POST/PUT with JSON body
3. **Testing against running server** — Use `app.request()` directly; no server needed
4. **Not passing env for Workers** — Cloudflare bindings need to be mocked via the third argument
5. **Using node-fetch** — Hono uses Web Standard `Request`/`Response`; use the global `Request` constructor
