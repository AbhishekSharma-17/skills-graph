# Fastify — Error Handling

> Source: [fastify.dev/docs/latest/Reference/Errors](https://fastify.dev/docs/latest/Reference/Errors/)

## Table of Contents

- [Automatic Error Catching](#automatic-error-catching)
- [Custom Error Handler](#custom-error-handler)
- [Creating Custom Errors](#creating-custom-errors)
- [FST Error Codes](#fst-error-codes)
- [Not Found Handler](#not-found-handler)
- [Production Error Pattern](#production-error-pattern)
- [Common Pitfalls](#common-pitfalls)

## Automatic Error Catching

Fastify automatically catches errors in both sync and async handlers:

```javascript
// Sync throw
fastify.get('/sync', () => {
  throw new Error('kaboom')
})

// Async throw
fastify.get('/async', async () => {
  throw new Error('kaboom')
})

// Both produce: { statusCode: 500, error: "Internal Server Error", message: "kaboom" }
```

## Default Error Response Format

```json
{
  "statusCode": 500,
  "error": "Internal Server Error",
  "message": "kaboom"
}
```

For validation errors:

```json
{
  "statusCode": 400,
  "code": "FST_ERR_VALIDATION",
  "error": "Bad Request",
  "message": "body/email must match format \"email\""
}
```

## Custom Error Handler

Set a custom handler with `setErrorHandler()`:

```javascript
fastify.setErrorHandler((error, request, reply) => {
  request.log.error(error)

  // Validation errors
  if (error.validation) {
    reply.status(422).send({
      error: 'Validation Failed',
      details: error.validation.map(v => ({
        field: v.instancePath,
        message: v.message
      }))
    })
    return
  }

  // Custom application errors
  if (error.statusCode) {
    reply.status(error.statusCode).send({
      error: error.message
    })
    return
  }

  // Unexpected errors
  reply.status(500).send({
    error: 'Internal Server Error'
  })
})
```

### Encapsulated Error Handlers

Error handlers are scoped — a `setErrorHandler()` in a plugin only applies to that plugin's routes:

```javascript
// Root error handler
fastify.setErrorHandler((error, request, reply) => {
  reply.status(500).send({ error: 'Server error' })
})

fastify.register(async function apiPlugin(app) {
  // API-specific error handler
  app.setErrorHandler((error, request, reply) => {
    reply.status(error.statusCode || 500).send({
      error: error.message,
      requestId: request.id
    })
  })

  app.get('/api/data', async () => {
    throw new Error('API error')  // handled by API error handler
  })
})

fastify.get('/web', async () => {
  throw new Error('Web error')  // handled by root error handler
})
```

### Error Propagation

When re-throwing errors in a custom handler, always throw `Error` instances:

```javascript
fastify.setErrorHandler((error, request, reply) => {
  if (error.code === 'CUSTOM_ERROR') {
    // Handle locally
    reply.status(400).send({ error: error.message })
    return
  }
  // Re-throw to parent handler — must be an Error instance
  throw error
})
```

Throwing non-Error values (strings, objects) bypasses parent handlers and reaches the default handler directly.

## Creating Custom Errors

### With Status Codes

```javascript
class NotFoundError extends Error {
  constructor(resource, id) {
    super(`${resource} with id '${id}' not found`)
    this.statusCode = 404
  }
}

class ForbiddenError extends Error {
  constructor(message = 'Forbidden') {
    super(message)
    this.statusCode = 403
  }
}

// Usage in handlers
fastify.get('/users/:id', async (request) => {
  const user = await db.findUser(request.params.id)
  if (!user) throw new NotFoundError('User', request.params.id)
  return user
})
```

### With Additional Properties

Errors can include custom properties like `headers`:

```javascript
class RateLimitError extends Error {
  constructor(retryAfter) {
    super('Too many requests')
    this.statusCode = 429
    this.headers = {
      'retry-after': retryAfter,
      'x-ratelimit-limit': '100'
    }
  }
}
```

### Status Code Rules

- Errors with `statusCode < 400` are automatically elevated to 500
- The `statusCode` property on the error takes precedence
- Use `reply.code()` in the error handler to override

## FST Error Codes

Fastify defines 70+ error codes accessible via:

```javascript
import { errorCodes } from 'fastify'
// or
const { errorCodes } = require('fastify')
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `FST_ERR_NOT_FOUND` | 404 | Route not found |
| `FST_ERR_VALIDATION` | 400 | Request failed schema validation |
| `FST_ERR_CTP_BODY_TOO_LARGE` | 413 | Request body exceeds limit |
| `FST_ERR_CTP_INVALID_MEDIA_TYPE` | 415 | Unsupported Content-Type |
| `FST_ERR_BAD_STATUS_CODE` | 500 | Invalid status code provided |
| `FST_ERR_HANDLER_TIMEOUT` | 503 | Request handler timed out |
| `FST_ERR_DEC_ALREADY_PRESENT` | 500 | Decorator name already used |
| `FST_ERR_DEC_UNDECLARED` | 500 | Decorator not found |
| `FST_ERR_PLUGIN_TIMEOUT` | — | Plugin failed to load in time |

### Checking Error Types

```javascript
fastify.setErrorHandler((error, request, reply) => {
  if (error instanceof errorCodes.FST_ERR_VALIDATION) {
    reply.status(422).send({ validation: error.validation })
    return
  }
  if (error instanceof errorCodes.FST_ERR_NOT_FOUND) {
    reply.status(404).send({ error: 'Not found' })
    return
  }
  reply.status(500).send({ error: 'Server error' })
})
```

## Not Found Handler

Customize the 404 response:

```javascript
fastify.setNotFoundHandler({
  preHandler: async (request, reply) => {
    // Optional pre-processing
  }
}, async (request, reply) => {
  reply.code(404).send({
    error: 'Not Found',
    message: `Route ${request.method} ${request.url} not found`,
    statusCode: 404
  })
})
```

### Prefixed Not Found

```javascript
fastify.register(async function apiRoutes(app) {
  app.setNotFoundHandler(async (request, reply) => {
    reply.code(404).send({
      error: 'API endpoint not found',
      path: request.url
    })
  })
}, { prefix: '/api' })
```

## Error Handling in Hooks

Errors thrown in hooks are caught by the error handler:

```javascript
fastify.addHook('preHandler', async (request, reply) => {
  const isValid = await validateApiKey(request.headers['x-api-key'])
  if (!isValid) {
    const err = new Error('Invalid API key')
    err.statusCode = 401
    throw err
  }
})
```

## Error Serialization

In custom error handlers, `reply.send(data)` behaves like regular handlers:
- Objects are serialized with `preSerialization` lifecycle
- Strings, buffers, and streams are sent directly

When an error handler throws a new error, the parent `errorHandler` receives it. The `onError` hook fires once for the first error, preventing infinite loops.

## Production Error Pattern

```javascript
import fp from 'fastify-plugin'

export default fp(async function errorPlugin(fastify) {
  fastify.setErrorHandler((error, request, reply) => {
    // Log full error with context
    request.log.error({
      err: error,
      url: request.url,
      method: request.method,
      requestId: request.id
    })

    // Validation errors — expose details
    if (error.validation) {
      return reply.status(400).send({
        statusCode: 400,
        error: 'Bad Request',
        message: 'Validation failed',
        details: error.validation
      })
    }

    // Known application errors — expose message
    if (error.statusCode && error.statusCode < 500) {
      return reply.status(error.statusCode).send({
        statusCode: error.statusCode,
        error: error.message
      })
    }

    // Unknown errors — hide details in production
    reply.status(500).send({
      statusCode: 500,
      error: 'Internal Server Error',
      message: process.env.NODE_ENV === 'production'
        ? 'An unexpected error occurred'
        : error.message
    })
  })

  fastify.setNotFoundHandler(async (request, reply) => {
    reply.code(404).send({
      statusCode: 404,
      error: 'Not Found',
      message: `Route ${request.method}:${request.url} not found`
    })
  })
})
```

## Common Pitfalls

1. **Throwing strings** — `throw 'error message'` bypasses parent error handlers; always throw `Error` instances
2. **Forgotten error handler in plugins** — without a scoped error handler, plugin errors bubble to the root handler
3. **Status code elevation** — errors with `statusCode < 400` become 500; explicitly set 4xx codes for client errors
4. **onError is read-only** — the `onError` hook cannot modify the error response; use `setErrorHandler()` for that
5. **Infinite loop risk** — if an error handler throws, it propagates to the parent handler; if the root handler throws, Fastify's built-in handler takes over
