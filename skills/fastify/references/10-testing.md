# Fastify — Testing

> Source: [fastify.dev/docs/latest/Guides/Testing](https://fastify.dev/docs/latest/Guides/Testing/)

## Table of Contents

- [Application Architecture for Testing](#application-architecture-for-testing)
- [The inject() Method](#the-inject-method)
- [Testing with Node Test Runner](#testing-with-node-test-runner)
- [Testing with Vitest](#testing-with-vitest)
- [Testing Plugins](#testing-plugins)
- [Testing with Authentication](#testing-with-authentication)
- [Testing with Running Server](#testing-with-running-server)
- [Parallel Testing](#parallel-testing)
- [Common Pitfalls](#common-pitfalls)

## Overview

Fastify provides built-in HTTP injection via the `.inject()` method, powered by `light-my-request`. This allows testing routes without starting a server or opening network connections.

## Application Architecture for Testing

Separate application setup from server startup:

```javascript
// app.js — builds the application
import Fastify from 'fastify'
import userRoutes from './routes/users.js'
import dbPlugin from './plugins/database.js'

export function buildApp(opts = {}) {
  const app = Fastify(opts)
  app.register(dbPlugin)
  app.register(userRoutes, { prefix: '/api/users' })
  return app
}
```

```javascript
// server.js — starts listening
import { buildApp } from './app.js'

const app = buildApp({ logger: true })
await app.listen({ port: 3000 })
```

This enables testing via `inject()` without starting a server.

## The inject() Method

```javascript
const response = await app.inject({
  method: 'GET',
  url: '/api/users',
  query: { page: '1', limit: '10' },
  headers: {
    authorization: 'Bearer token123',
    'content-type': 'application/json'
  },
  payload: { name: 'Alice', email: 'alice@example.com' },
  cookies: { session: 'abc123' }
})
```

### Response Object

```javascript
response.statusCode      // 200
response.headers         // response headers object
response.body            // raw response body (string)
response.json()          // parsed JSON response
response.cookies         // parsed cookies array
```

## Testing with Node Test Runner

```javascript
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buildApp } from '../app.js'

test('GET / returns hello world', async (t) => {
  const app = buildApp()

  const response = await app.inject({
    method: 'GET',
    url: '/'
  })

  assert.strictEqual(response.statusCode, 200)
  assert.deepStrictEqual(response.json(), { hello: 'world' })

  await app.close()
})
```

## Testing with Vitest

```javascript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { buildApp } from '../app.js'

describe('User API', () => {
  let app

  beforeEach(() => {
    app = buildApp({ logger: false })
  })

  afterEach(async () => {
    await app.close()
  })

  it('creates a user', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/api/users',
      payload: {
        name: 'Alice',
        email: 'alice@example.com'
      }
    })

    expect(response.statusCode).toBe(201)
    const body = response.json()
    expect(body).toHaveProperty('id')
    expect(body.name).toBe('Alice')
  })

  it('returns 400 for invalid body', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/api/users',
      payload: { name: '' }  // missing required email
    })

    expect(response.statusCode).toBe(400)
  })

  it('returns 404 for unknown user', async () => {
    const response = await app.inject({
      method: 'GET',
      url: '/api/users/nonexistent'
    })

    expect(response.statusCode).toBe(404)
  })
})
```

## Testing Plugins

Test plugins by creating a mock Fastify instance and verifying behavior:

```javascript
import { test } from 'node:test'
import assert from 'node:assert/strict'
import Fastify from 'fastify'
import myPlugin from '../plugins/my-plugin.js'

test('plugin decorates request with helloRequest', async () => {
  const app = Fastify()
  app.register(myPlugin)

  // Add a test route that uses the decorator
  app.get('/test', async (request) => {
    return { message: request.helloRequest }
  })

  const response = await app.inject({
    method: 'GET',
    url: '/test'
  })

  assert.strictEqual(response.statusCode, 200)
  assert.strictEqual(response.json().message, 'Hello from plugin!')

  await app.close()
})

test('plugin adds instance decorator', async () => {
  const app = Fastify()
  app.register(myPlugin)

  await app.ready()

  assert.ok(app.hasDecorator('myUtility'))
  assert.strictEqual(typeof app.myUtility, 'function')

  await app.close()
})
```

## Testing with Authentication

```javascript
describe('Protected Routes', () => {
  it('returns 401 without auth header', async () => {
    const app = buildApp()
    const response = await app.inject({
      method: 'GET',
      url: '/api/admin/dashboard'
    })
    expect(response.statusCode).toBe(401)
    await app.close()
  })

  it('returns 200 with valid token', async () => {
    const app = buildApp()
    const token = generateTestToken({ role: 'admin' })
    const response = await app.inject({
      method: 'GET',
      url: '/api/admin/dashboard',
      headers: {
        authorization: `Bearer ${token}`
      }
    })
    expect(response.statusCode).toBe(200)
    await app.close()
  })
})
```

## Testing with Running Server

When you need actual HTTP (e.g., testing WebSockets or SSE):

### Using fetch

```javascript
test('test with real HTTP', async () => {
  const app = buildApp()
  await app.listen({ port: 0 })  // random port
  const port = app.server.address().port

  const response = await fetch(`http://localhost:${port}/api/users`)
  const data = await response.json()

  assert.strictEqual(response.status, 200)
  assert.ok(Array.isArray(data))

  await app.close()
})
```

### Using SuperTest

```javascript
import supertest from 'supertest'

test('test with supertest', async () => {
  const app = buildApp()
  await app.ready()

  const response = await supertest(app.server)
    .get('/api/users')
    .expect(200)
    .expect('content-type', /json/)

  assert.ok(response.body.length >= 0)

  await app.close()
})
```

## Testing Schema Validation

```javascript
test('validates request body schema', async () => {
  const app = buildApp()

  // Missing required field
  const response = await app.inject({
    method: 'POST',
    url: '/api/users',
    payload: { name: 'Alice' }  // email is required
  })

  expect(response.statusCode).toBe(400)
  const body = response.json()
  expect(body.message).toContain('email')

  await app.close()
})

test('strips unknown properties', async () => {
  const app = buildApp()

  const response = await app.inject({
    method: 'POST',
    url: '/api/users',
    payload: {
      name: 'Alice',
      email: 'alice@example.com',
      secretField: 'should be stripped'  // not in schema
    }
  })

  expect(response.statusCode).toBe(201)
  const body = response.json()
  expect(body).not.toHaveProperty('secretField')

  await app.close()
})
```

## Testing Response Serialization

```javascript
test('response schema strips internal fields', async () => {
  const app = buildApp()

  const response = await app.inject({
    method: 'GET',
    url: '/api/users/1'
  })

  const body = response.json()
  // password_hash should not appear due to response schema
  expect(body).not.toHaveProperty('password_hash')
  expect(body).toHaveProperty('name')

  await app.close()
})
```

## Testing Hooks

```javascript
test('onRequest hook sets requestId', async () => {
  const app = buildApp()

  const response = await app.inject({
    method: 'GET',
    url: '/api/users',
    headers: {
      'x-request-id': 'custom-id-123'
    }
  })

  expect(response.headers['x-request-id']).toBe('custom-id-123')

  await app.close()
})
```

## Parallel Testing

Each test should create its own Fastify instance to avoid shared state:

```javascript
// Each test gets its own app — safe for parallel execution
test('test A', async () => {
  const app = buildApp()
  // ...
  await app.close()
})

test('test B', async () => {
  const app = buildApp()
  // ...
  await app.close()
})
```

## Cleanup

Always close the app in test teardown to release database connections, timers, and file handles:

```javascript
// With test hooks
afterEach(async () => {
  await app.close()
})

// Or inline
test('my test', async () => {
  const app = buildApp()
  try {
    // test logic
  } finally {
    await app.close()
  }
})
```

## Common Pitfalls

1. **Forgetting `.close()`** — unclosed instances leak connections and cause test hangs
2. **Shared app instances** — sharing one Fastify instance across tests causes state pollution; create fresh instances
3. **Logger noise** — pass `{ logger: false }` to `buildApp()` in tests to suppress log output
4. **Port conflicts** — when using real HTTP, use `port: 0` for random port assignment
5. **Async readiness** — if testing decorators, call `await app.ready()` before accessing them
