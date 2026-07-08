# ElysiaJS — Validation

> Source: [elysiajs.com/essential/validation](https://elysiajs.com/essential/validation) · Version 1.4.x

## Table of Contents

- [Validation Overview](#validation-overview)
- [Elysia.t Schema Builder](#elysiat-schema-builder)
- [Request Validation](#request-validation)
- [Response Validation](#response-validation)
- [Type Coercion](#type-coercion)
- [File Uploads](#file-uploads)
- [Reference Models](#reference-models)
- [Standard Schema Support](#standard-schema-support)
- [Guard Validation](#guard-validation)
- [Error Messages](#error-messages)
- [Type Inference](#type-inference)
- [Common Pitfalls](#common-pitfalls)

---

## Validation Overview

ElysiaJS validates data at both runtime and compile-time using a single source of truth. Schema definitions simultaneously:
- Validate incoming requests at runtime
- Infer TypeScript types at compile-time
- Generate OpenAPI documentation automatically

```typescript
import { Elysia, t } from 'elysia'

app.post('/users', ({ body }) => {
    // body is typed as { name: string, email: string }
    return createUser(body)
}, {
    body: t.Object({
        name: t.String(),
        email: t.String({ format: 'email' })
    })
})
```

## Elysia.t Schema Builder

`Elysia.t` extends TypeBox with additional runtime validations. Import `t` from `elysia`:

### Primitive Types

```typescript
t.String()                    // string
t.String({ minLength: 1 })    // non-empty string
t.String({ maxLength: 255 })  // max length
t.String({ format: 'email' }) // email format
t.String({ pattern: '^[a-z]+$' }) // regex pattern

t.Number()                    // number
t.Number({ minimum: 0 })     // min value
t.Number({ maximum: 100 })   // max value
t.Number({ multipleOf: 2 })  // even numbers

t.Integer()                   // integer only
t.Boolean()                   // boolean
t.Null()                      // null
t.Literal('active')           // exact value
```

### Numeric (String Coercion)

```typescript
t.Numeric()                   // Coerces "42" → 42
t.Numeric({ minimum: 1 })    // With constraints
```

### Object Types

```typescript
t.Object({
    name: t.String(),
    age: t.Number(),
    role: t.Optional(t.String())  // Optional field
})

t.Object({
    id: t.Number(),
    metadata: t.Record(t.String(), t.Any())  // Dynamic keys
})
```

### Array Types

```typescript
t.Array(t.String())                // string[]
t.Array(t.Number(), { minItems: 1 })  // Non-empty array
t.Array(t.Object({ id: t.Number() })) // Object array
```

### Union & Intersection

```typescript
t.Union([t.String(), t.Number()])  // string | number
t.Union([t.Literal('a'), t.Literal('b')])  // 'a' | 'b'

t.Intersect([
    t.Object({ name: t.String() }),
    t.Object({ age: t.Number() })
])  // { name: string } & { age: number }
```

### Enums

```typescript
t.Enum({ Active: 'active', Inactive: 'inactive' })
```

### Tuples

```typescript
t.Tuple([t.String(), t.Number()])  // [string, number]
```

## Request Validation

### Body Validation

```typescript
app.post('/users', ({ body }) => body, {
    body: t.Object({
        username: t.String({ minLength: 3, maxLength: 32 }),
        password: t.String({ minLength: 8 }),
        role: t.Optional(t.Union([
            t.Literal('admin'),
            t.Literal('user')
        ]))
    })
})
```

### Query Validation

```typescript
app.get('/search', ({ query }) => {
    // query.q is string, query.page is number
    return search(query.q, query.page)
}, {
    query: t.Object({
        q: t.String(),
        page: t.Numeric({ minimum: 1, default: 1 }),
        limit: t.Optional(t.Numeric({ maximum: 100 }))
    })
})
```

Query arrays support both comma-delimited (`?tags=a,b,c`) and HTML form format (`?tags=a&tags=b&tags=c`).

### Params Validation

```typescript
app.get('/users/:id', ({ params }) => {
    // params.id is number (coerced from string)
    return getUserById(params.id)
}, {
    params: t.Object({
        id: t.Numeric()
    })
})
```

### Headers Validation

```typescript
app.get('/protected', handler, {
    headers: t.Object({
        authorization: t.String()
    })
})
```

Headers allow additional properties by default — only specified headers are validated.

### Cookie Validation

```typescript
app.get('/dashboard', handler, {
    cookie: t.Cookie({
        session: t.Object({
            userId: t.Number(),
            role: t.String()
        })
    })
})
```

## Response Validation

### Single Response Schema

```typescript
app.get('/user/:id', handler, {
    response: t.Object({
        id: t.Number(),
        name: t.String()
    })
})
```

### Per-Status-Code Schemas

```typescript
app.post('/users', handler, {
    response: {
        200: t.Object({ id: t.Number(), name: t.String() }),
        400: t.Object({ error: t.String() }),
        409: t.Object({ error: t.String(), existing: t.Number() })
    }
})
```

Response validation runs in development and can be disabled in production for performance.

## Type Coercion

ElysiaJS automatically coerces types for query parameters and path parameters, which are inherently strings in HTTP:

```typescript
t.Numeric()        // "42" → 42  (string → number)
t.BooleanString()  // "true" → true  (string → boolean)
```

## File Uploads

```typescript
app.post('/upload', ({ body: { file, name } }) => {
    Bun.write(`uploads/${name}`, file)
    return { success: true }
}, {
    body: t.Object({
        file: t.File({
            type: 'image',           // MIME prefix filter
            maxSize: '5m'            // Max 5 MB
        }),
        name: t.String()
    })
})

// Multiple files
app.post('/gallery', ({ body: { images } }) => {
    return { count: images.length }
}, {
    body: t.Object({
        images: t.Files({
            type: 'image',
            maxSize: '10m'
        })
    })
})
```

Elysia auto-detects `multipart/form-data` when `t.File()` or `t.Files()` schemas are present.

## Reference Models

Define reusable schemas with `.model()`:

```typescript
const app = new Elysia()
    .model({
        user: t.Object({
            id: t.Number(),
            name: t.String(),
            email: t.String({ format: 'email' })
        }),
        createUser: t.Object({
            name: t.String(),
            email: t.String({ format: 'email' })
        }),
        error: t.Object({
            error: t.String()
        })
    })
    .post('/users', ({ body }) => createUser(body), {
        body: 'createUser',        // Reference by name
        response: {
            201: 'user',
            400: 'error'
        }
    })
    .get('/users/:id', ({ params }) => getUser(params.id), {
        response: 'user'
    })
```

Models auto-complete in your IDE and generate named OpenAPI schema references.

## Standard Schema Support

ElysiaJS supports any Standard Schema-compliant library alongside or instead of TypeBox:

### Zod

```typescript
import { z } from 'zod'

app.post('/users', ({ body }) => body, {
    body: z.object({
        name: z.string().min(3),
        email: z.string().email()
    })
})
```

### Valibot

```typescript
import * as v from 'valibot'

app.post('/users', ({ body }) => body, {
    body: v.object({
        name: v.pipe(v.string(), v.minLength(3)),
        email: v.pipe(v.string(), v.email())
    })
})
```

### Mixed Schemas

You can use different schema libraries within the same handler:

```typescript
app.post('/mixed', handler, {
    body: z.object({ name: z.string() }),      // Zod for body
    query: t.Object({ page: t.Numeric() }),    // TypeBox for query
    response: v.object({ ok: v.boolean() })    // Valibot for response
})
```

## Guard Validation

Apply schemas to multiple routes:

```typescript
app.guard({
    headers: t.Object({
        authorization: t.String()
    }),
    response: t.Object({
        data: t.Any()
    })
}, (app) =>
    app
        .get('/profile', getProfile)
        .get('/settings', getSettings)
        .put('/settings', updateSettings)
)
```

## Error Messages

### Inline Error Messages

```typescript
app.post('/users', handler, {
    body: t.Object({
        name: t.String({
            minLength: 3,
            error: 'Name must be at least 3 characters'
        }),
        age: t.Number({
            minimum: 18,
            error: 'Must be at least 18 years old'
        })
    })
})
```

### Dynamic Error Functions

```typescript
body: t.Object({
    email: t.String({
        format: 'email',
        error({ value }) {
            return `"${value}" is not a valid email address`
        }
    })
})
```

### Global Validation Error Handler

```typescript
app.onError(({ code, error }) => {
    if (code === 'VALIDATION') {
        return {
            error: 'Validation failed',
            details: error.all.map(e => ({
                path: e.path,
                message: e.message
            }))
        }
    }
})
```

## Type Inference

Extract TypeScript types from schemas using `.static`:

```typescript
const UserSchema = t.Object({
    id: t.Number(),
    name: t.String(),
    email: t.String()
})

type User = typeof UserSchema.static
// { id: number; name: string; email: string }
```

## Common Pitfalls

1. **Query values are strings** — Without `t.Numeric()` or `t.BooleanString()`, query parameters remain strings even with `t.Number()`. Use coercion types for query/params.

2. **Headers allow extras** — Header validation does not reject unknown headers by default. Only specified headers are validated.

3. **File validation needs multipart** — `t.File()` auto-detects `multipart/form-data`. Don't manually set Content-Type when uploading with Eden.

4. **Reference model names are global** — Model names must be unique within an Elysia instance tree. Name collisions cause runtime errors.

5. **Production validation detail** — Validation error details are hidden in production by default to prevent schema leakage. Set `Elysia.allowUnsafeValidationDetails = true` to override.
