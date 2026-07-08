# ElysiaJS — Error Handling

> Source: [elysiajs.com/patterns/error-handling](https://elysiajs.com/patterns/error-handling) · Version 1.4.x

## Table of Contents

- [Error Handling Overview](#error-handling-overview)
- [Built-in Error Codes](#built-in-error-codes)
- [The onError Hook](#the-onerror-hook)
- [Custom Error Classes](#custom-error-classes)
- [Status Utility](#status-utility)
- [Throw vs Return](#throw-vs-return)
- [Validation Errors](#validation-errors)
- [Custom Error Responses](#custom-error-responses)
- [Error Handling Patterns](#error-handling-patterns)
- [Production Safety](#production-safety)
- [Common Pitfalls](#common-pitfalls)

---

## Error Handling Overview

ElysiaJS handles errors through the `onError` lifecycle hook, which catches exceptions thrown from any lifecycle phase. The framework provides built-in error codes for automatic type narrowing and supports custom error classes for domain-specific error handling.

```typescript
import { Elysia } from 'elysia'

const app = new Elysia()
    .onError(({ code, error, set }) => {
        if (code === 'NOT_FOUND') {
            set.status = 404
            return { error: 'Not found' }
        }
    })
    .get('/', () => 'Hello')
    .listen(3000)
```

## Built-in Error Codes

| Code | Status | Trigger |
|------|--------|---------|
| `NOT_FOUND` | 404 | No matching route |
| `VALIDATION` | 400 | Schema validation failure |
| `PARSE` | 400 | Body parsing failure |
| `INTERNAL_SERVER_ERROR` | 500 | Unhandled exception |
| `UNKNOWN` | 500 | Custom/unclassified errors |

### Type-Narrowed Error Handling

```typescript
app.onError(({ code, error }) => {
    switch (code) {
        case 'NOT_FOUND':
            return { error: 'Resource not found', path: error.message }

        case 'VALIDATION':
            return {
                error: 'Invalid input',
                details: error.all.map(e => ({
                    field: e.path,
                    message: e.message
                }))
            }

        case 'PARSE':
            return { error: 'Could not parse request body' }

        case 'INTERNAL_SERVER_ERROR':
            console.error('Unhandled:', error)
            return { error: 'Internal server error' }
    }
})
```

## The onError Hook

### Global Error Handler

```typescript
app.onError(({ code, error, set, request }) => {
    console.error(`[${code}] ${request.method} ${request.url}: ${error.message}`)

    set.status = error.status ?? 500

    return {
        error: error.message,
        code
    }
})
```

### Scoped Error Handler

```typescript
const apiPlugin = new Elysia({ prefix: '/api' })
    .onError({ as: 'scoped' }, ({ code, error }) => {
        return {
            success: false,
            error: error.message,
            code
        }
    })
```

### Route-Level Error Handler

```typescript
app.get('/risky', handler, {
    error({ code, error }) {
        if (code === 'INTERNAL_SERVER_ERROR') {
            return { fallback: 'default value' }
        }
    }
})
```

## Custom Error Classes

Register custom error classes for type-safe error handling:

```typescript
class AuthError extends Error {
    status = 401

    constructor(public message: string = 'Unauthorized') {
        super(message)
    }
}

class NotFoundError extends Error {
    status = 404

    constructor(public resource: string) {
        super(`${resource} not found`)
    }
}

class RateLimitError extends Error {
    status = 429

    constructor(public retryAfter: number) {
        super('Too many requests')
    }
}

const app = new Elysia()
    .error({
        AuthError,
        NotFoundError,
        RateLimitError
    })
    .onError(({ code, error, set }) => {
        switch (code) {
            case 'AuthError':
                set.status = 401
                return { error: error.message }

            case 'NotFoundError':
                set.status = 404
                return { error: error.message, resource: error.resource }

            case 'RateLimitError':
                set.status = 429
                set.headers['Retry-After'] = String(error.retryAfter)
                return { error: error.message }
        }
    })
    .get('/users/:id', ({ params }) => {
        const user = db.find(params.id)
        if (!user) throw new NotFoundError('User')
        return user
    })
```

### Custom Status Code on Error Class

```typescript
class PaymentError extends Error {
    status = 402

    constructor(public message: string, public code: string) {
        super(message)
    }
}
```

Elysia automatically uses the `status` property as the HTTP status code.

## Status Utility

The `status()` function sets HTTP status codes with proper type narrowing for Eden:

```typescript
import { status } from 'elysia'

// Return with status code
app.get('/users/:id', ({ params }) => {
    const user = findUser(params.id)
    if (!user) return status(404, { error: 'Not found' })
    return user
})

// With response schema for type narrowing
app.post('/users', ({ body }) => {
    if (emailTaken(body.email)) {
        return status(409, { error: 'Email already exists' })
    }
    return status(201, createUser(body))
}, {
    response: {
        201: t.Object({ id: t.Number(), name: t.String() }),
        409: t.Object({ error: t.String() })
    }
})
```

## Throw vs Return

The distinction between `throw` and `return` determines whether `onError` is invoked:

```typescript
// THROW — caught by onError middleware
app.get('/throw', () => {
    throw status(418, "I'm a teapot")
})

// RETURN — bypasses onError, goes directly to response
app.get('/return', () => {
    return status(418, "I'm a teapot")
})
```

Use `throw` when you want centralized error handling via `onError`. Use `return` when you want to send an error response directly without triggering error middleware.

### Throwing Custom Errors

```typescript
app.get('/protected', ({ bearer }) => {
    if (!bearer) throw new AuthError('Token required')
    if (!isValid(bearer)) throw new AuthError('Invalid token')
    return getProtectedData()
})
```

## Validation Errors

Validation errors provide structured access to all failures:

```typescript
app.onError(({ code, error }) => {
    if (code === 'VALIDATION') {
        return {
            error: 'Validation failed',
            fields: error.all.map(e => ({
                path: e.path,
                value: e.value,
                message: e.message,
                type: e.type
            }))
        }
    }
})
```

### Per-Field Error Messages

```typescript
app.post('/register', handler, {
    body: t.Object({
        email: t.String({
            format: 'email',
            error: 'Please provide a valid email address'
        }),
        password: t.String({
            minLength: 8,
            error: 'Password must be at least 8 characters'
        }),
        age: t.Number({
            minimum: 13,
            error({ value }) {
                return `Age ${value} is too young. Minimum age is 13.`
            }
        })
    })
})
```

## Custom Error Responses

Implement `toResponse()` for full control over the HTTP response:

```typescript
class ApiError extends Error {
    status: number

    constructor(
        message: string,
        status: number,
        public details?: unknown
    ) {
        super(message)
        this.status = status
    }

    toResponse() {
        return Response.json(
            {
                error: this.message,
                status: this.status,
                details: this.details,
                timestamp: new Date().toISOString()
            },
            { status: this.status }
        )
    }
}
```

When an error has `toResponse()`, Elysia calls it to generate the full HTTP response.

## Error Handling Patterns

### Centralized Error Handler

```typescript
const errorHandler = new Elysia({ name: 'error-handler' })
    .error({
        AuthError,
        NotFoundError,
        ValidationError: class extends Error { status = 422 }
    })
    .onError({ as: 'global' }, ({ code, error, set }) => {
        const status = (error as any).status ?? 500

        if (status >= 500) {
            console.error(`[FATAL] ${error.message}`, error.stack)
        }

        set.status = status
        return {
            success: false,
            error: error.message,
            code
        }
    })
```

### Try-Catch in Handlers

```typescript
app.get('/external', async () => {
    try {
        const data = await fetchExternalApi()
        return data
    } catch (err) {
        throw new Error(`External API failed: ${err.message}`)
    }
})
```

### Error Boundary per Route Group

```typescript
const adminRoutes = new Elysia({ prefix: '/admin' })
    .onError(({ error }) => {
        auditLog.error('Admin error:', error)
        return { error: 'Admin operation failed' }
    })
    .get('/users', adminListUsers)
    .delete('/users/:id', adminDeleteUser)
```

## Production Safety

Elysia hides validation error details in production by default:

```typescript
// Development — full error details shown
// Production — details omitted to prevent schema leakage

// Override in production (NOT recommended for public APIs)
Elysia.allowUnsafeValidationDetails = true
```

## Common Pitfalls

1. **onError catches throws only** — `return status(400)` does NOT trigger `onError`. Only `throw` and unhandled exceptions are caught.

2. **Error handler order** — Like other hooks, `onError` only applies to routes registered after it. Place error handlers before route definitions.

3. **Custom error must be registered** — Using `.error({ MyError })` is required for type-narrowed `code` matching. Unregistered errors get `code: 'UNKNOWN'`.

4. **Status on error class** — If your error class has a `status` property, Elysia uses it automatically. No need to set `set.status` separately.

5. **Production validation details** — Detailed validation errors are hidden in production. If your frontend depends on field-level errors, configure accordingly or build custom error messages.
