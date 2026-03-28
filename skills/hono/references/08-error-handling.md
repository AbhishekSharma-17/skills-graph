# Hono — Error Handling

> Source: [hono.dev/docs/api/exception](https://hono.dev/docs/api/exception)

## Overview

Hono provides structured error handling through `HTTPException`, global error handlers (`app.onError`), and not-found handlers (`app.notFound`). Errors propagate up through the middleware chain and can be caught at any level.

## HTTPException

The primary way to throw HTTP errors:

```typescript
import { HTTPException } from 'hono/http-exception'

app.get('/protected', (c) => {
  const token = c.req.header('Authorization')
  if (!token) {
    throw new HTTPException(401, { message: 'Unauthorized' })
  }
  return c.json({ data: 'secret' })
})
```

### Constructor

```typescript
new HTTPException(statusCode, options?)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `statusCode` | `number` | HTTP status code (400, 401, 403, 404, 500, etc.) |
| `options.message` | `string` | Error message |
| `options.res` | `Response` | Custom Response object to return |
| `options.cause` | `Error` | Original error for debugging |

### Custom Response

Return a custom response with specific headers or body format:

```typescript
app.get('/api/resource', (c) => {
  const item = findItem(c.req.param('id'))
  if (!item) {
    const errorResponse = new Response(
      JSON.stringify({
        error: 'Not Found',
        code: 'RESOURCE_NOT_FOUND',
        details: 'The requested resource does not exist',
      }),
      {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      }
    )
    throw new HTTPException(404, { res: errorResponse })
  }
  return c.json(item)
})
```

### Wrapping Original Errors

Preserve the original error for logging:

```typescript
app.get('/api/data', async (c) => {
  try {
    const data = await externalService.fetch()
    return c.json(data)
  } catch (err) {
    throw new HTTPException(502, {
      message: 'External service unavailable',
      cause: err as Error,
    })
  }
})
```

## Global Error Handler

### app.onError

Catch all unhandled errors:

```typescript
import { HTTPException } from 'hono/http-exception'

app.onError((err, c) => {
  // Handle HTTPException
  if (err instanceof HTTPException) {
    return err.getResponse()
  }

  // Log unexpected errors
  console.error('Unexpected error:', err)

  // Return generic error response
  return c.json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined,
  }, 500)
})
```

### Structured Error Handling

```typescript
// Custom error types
class ValidationError extends Error {
  constructor(public details: Record<string, string[]>) {
    super('Validation failed')
    this.name = 'ValidationError'
  }
}

class NotFoundError extends Error {
  constructor(public resource: string, public id: string) {
    super(`${resource} ${id} not found`)
    this.name = 'NotFoundError'
  }
}

// Global handler
app.onError((err, c) => {
  if (err instanceof HTTPException) {
    return err.getResponse()
  }

  if (err instanceof ValidationError) {
    return c.json({
      error: 'Validation Error',
      details: err.details,
    }, 422)
  }

  if (err instanceof NotFoundError) {
    return c.json({
      error: 'Not Found',
      resource: err.resource,
      id: err.id,
    }, 404)
  }

  console.error(err)
  return c.json({ error: 'Internal Server Error' }, 500)
})
```

## Not Found Handler

### app.notFound

Customize the 404 response for unmatched routes:

```typescript
app.notFound((c) => {
  return c.json({
    error: 'Not Found',
    message: `Route ${c.req.method} ${c.req.path} not found`,
    docs: 'https://api.example.com/docs',
  }, 404)
})
```

### HTML 404 Page

```tsx
app.notFound((c) => {
  return c.html(
    <html>
      <body>
        <h1>404 — Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Go Home</a>
      </body>
    </html>,
    404
  )
})
```

## Error Handling in Middleware

Catch errors within middleware:

```typescript
import { createMiddleware } from 'hono/factory'
import { HTTPException } from 'hono/http-exception'

const errorBoundary = createMiddleware(async (c, next) => {
  try {
    await next()
  } catch (err) {
    if (err instanceof HTTPException) {
      throw err // Re-throw HTTP exceptions
    }

    // Log and wrap unexpected errors
    console.error('Middleware caught error:', err)
    throw new HTTPException(500, {
      message: 'An unexpected error occurred',
      cause: err as Error,
    })
  }
})

app.use('/api/*', errorBoundary)
```

## Error Handling Patterns

### Consistent API Error Format

```typescript
interface ApiError {
  error: string
  code: string
  message: string
  details?: unknown
}

const apiError = (c: any, status: number, code: string, message: string, details?: unknown) => {
  return c.json<ApiError>({
    error: status >= 500 ? 'Server Error' : 'Client Error',
    code,
    message,
    details,
  }, status)
}

app.get('/api/users/:id', async (c) => {
  const id = c.req.param('id')
  const user = await db.findUser(id)
  if (!user) {
    return apiError(c, 404, 'USER_NOT_FOUND', `User ${id} not found`)
  }
  return c.json(user)
})
```

### Try-Catch in Handlers

```typescript
app.post('/api/process', async (c) => {
  const data = await c.req.json()

  try {
    const result = await processData(data)
    return c.json({ result })
  } catch (err) {
    if (err instanceof SomeExpectedError) {
      throw new HTTPException(400, { message: err.message })
    }
    throw err // Let global handler catch unexpected errors
  }
})
```

## Common Pitfalls

1. **Not calling `getResponse()`** — In `app.onError`, use `err.getResponse()` for HTTPException to get its custom response
2. **Swallowing errors silently** — Always log unexpected errors before returning a generic response
3. **Exposing error details in production** — Only include `err.message` in development mode
4. **Not re-throwing HTTPException in middleware** — Middleware error handlers should re-throw HTTPException for the global handler
5. **Using `throw` instead of `return`** — In middleware guards, `return c.json(...)` is clearer than throwing for expected conditions
