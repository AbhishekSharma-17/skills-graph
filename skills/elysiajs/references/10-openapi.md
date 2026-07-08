# ElysiaJS — OpenAPI Documentation

> Source: [elysiajs.com/patterns/openapi](https://elysiajs.com/patterns/openapi) · Version 1.4.x

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Route Documentation](#route-documentation)
- [Tags and Grouping](#tags-and-grouping)
- [Reference Models](#reference-models)
- [Security Schemes](#security-schemes)
- [Response Headers](#response-headers)
- [Hiding Routes](#hiding-routes)
- [Type-Based Generation](#type-based-generation)
- [Standard Schema Mapping](#standard-schema-mapping)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

ElysiaJS generates OpenAPI 3.0 documentation automatically from your route schemas and type definitions. The `@elysia/openapi` plugin provides a Scalar UI interface at the `/openapi` endpoint, serving as both documentation and interactive API explorer.

Key advantages:
- No manual annotations required — schemas ARE the documentation
- Runtime validation and docs from a single source of truth
- Supports TypeBox, Zod, Valibot, and other Standard Schema libraries

## Setup

### Installation

```bash
bun add @elysia/openapi
```

### Basic Configuration

```typescript
import { Elysia } from 'elysia'
import { openapi } from '@elysia/openapi'

const app = new Elysia()
    .use(openapi())
    .get('/hello', () => 'Hello World')
    .listen(3000)

// Documentation available at: http://localhost:3000/openapi
```

### Custom Configuration

```typescript
.use(openapi({
    path: '/docs',               // Custom docs URL (default: /openapi)
    documentation: {
        info: {
            title: 'My API',
            version: '1.0.0',
            description: 'API documentation for My Service',
            contact: {
                name: 'API Support',
                email: 'support@example.com'
            }
        },
        servers: [
            { url: 'https://api.example.com', description: 'Production' },
            { url: 'http://localhost:3000', description: 'Development' }
        ]
    }
}))
```

## Route Documentation

### Detail Property

Add descriptions, summaries, and metadata to individual routes:

```typescript
app.post('/users', ({ body }) => createUser(body), {
    body: t.Object({
        name: t.String({ description: 'User full name' }),
        email: t.String({
            format: 'email',
            description: 'User email address'
        }),
        password: t.String({
            minLength: 8,
            description: 'Password (min 8 characters)'
        })
    }),
    response: {
        201: t.Object({
            id: t.Number(),
            name: t.String()
        }),
        400: t.Object({
            error: t.String()
        })
    },
    detail: {
        summary: 'Create a new user',
        description: 'Register a new user account with email and password.',
        tags: ['Users'],
        operationId: 'createUser',
        deprecated: false
    }
})
```

### Schema Descriptions

Add descriptions to individual schema fields:

```typescript
body: t.Object({
    amount: t.Number({
        minimum: 0.01,
        description: 'Payment amount in USD'
    }),
    currency: t.String({
        default: 'USD',
        description: 'ISO 4217 currency code'
    }),
    metadata: t.Optional(t.Record(t.String(), t.String(), {
        description: 'Key-value pairs for additional data'
    }))
})
```

## Tags and Grouping

### Define Tags

```typescript
.use(openapi({
    documentation: {
        tags: [
            { name: 'Users', description: 'User management endpoints' },
            { name: 'Auth', description: 'Authentication endpoints' },
            { name: 'Posts', description: 'Blog post CRUD' },
            { name: 'Admin', description: 'Administrative operations' }
        ]
    }
}))
```

### Apply Tags to Routes

```typescript
// Per-route tag
app.get('/users', listUsers, {
    detail: { tags: ['Users'] }
})

// Per-instance tag (all routes in this instance)
const authRoutes = new Elysia({ tags: ['Auth'] })
    .post('/login', login)
    .post('/register', register)
    .post('/logout', logout)

// Per-group tag
app.group('/admin', { detail: { tags: ['Admin'] } }, (app) =>
    app
        .get('/stats', getStats)
        .get('/users', listAllUsers)
)
```

## Reference Models

Define reusable schemas that appear as named references in OpenAPI:

```typescript
const app = new Elysia()
    .use(openapi())
    .model({
        User: t.Object({
            id: t.Number(),
            name: t.String(),
            email: t.String({ format: 'email' }),
            role: t.Union([t.Literal('admin'), t.Literal('user')])
        }),
        CreateUser: t.Object({
            name: t.String({ minLength: 1 }),
            email: t.String({ format: 'email' }),
            password: t.String({ minLength: 8 })
        }),
        Error: t.Object({
            error: t.String(),
            code: t.Optional(t.String())
        }),
        Paginated: t.Object({
            data: t.Array(t.Any()),
            total: t.Number(),
            page: t.Number(),
            pageSize: t.Number()
        })
    })
    .get('/users/:id', handler, {
        response: { 200: 'User', 404: 'Error' }
    })
    .post('/users', handler, {
        body: 'CreateUser',
        response: { 201: 'User', 400: 'Error' }
    })
```

Models generate `$ref` entries in the OpenAPI spec, keeping it DRY.

## Security Schemes

### Define Security Schemes

```typescript
.use(openapi({
    documentation: {
        components: {
            securitySchemes: {
                bearerAuth: {
                    type: 'http',
                    scheme: 'bearer',
                    bearerFormat: 'JWT',
                    description: 'JWT Bearer token'
                },
                apiKey: {
                    type: 'apiKey',
                    in: 'header',
                    name: 'X-API-Key',
                    description: 'API key for service-to-service auth'
                },
                oauth2: {
                    type: 'oauth2',
                    flows: {
                        authorizationCode: {
                            authorizationUrl: 'https://auth.example.com/authorize',
                            tokenUrl: 'https://auth.example.com/token',
                            scopes: {
                                'read:users': 'Read user data',
                                'write:users': 'Modify user data'
                            }
                        }
                    }
                }
            }
        }
    }
}))
```

### Apply Security to Routes

```typescript
// Per-route security
app.get('/me', getProfile, {
    detail: {
        security: [{ bearerAuth: [] }]
    }
})

// Per-instance security (all routes)
const protectedRoutes = new Elysia({
    prefix: '/api',
    detail: {
        security: [{ bearerAuth: [] }]
    }
})
```

## Response Headers

Document response headers using `withHeader`:

```typescript
import { withHeader } from '@elysia/openapi'

app.get('/data', ({ set }) => {
    set.headers['x-request-id'] = crypto.randomUUID()
    set.headers['x-rate-limit-remaining'] = '99'
    return { data: 'value' }
}, {
    response: withHeader(
        t.Object({ data: t.String() }),
        {
            'x-request-id': t.String({ description: 'Unique request identifier' }),
            'x-rate-limit-remaining': t.String({ description: 'Remaining rate limit' })
        }
    )
})
```

## Hiding Routes

Exclude routes from documentation:

```typescript
// Hide a single route
app.get('/internal', handler, {
    detail: { hide: true }
})

// Hide health check endpoints
app.get('/health', () => 'ok', {
    detail: { hide: true }
})
```

## Type-Based Generation

Generate OpenAPI specs from TypeScript types without runtime schemas:

```typescript
import { openapi, fromTypes } from '@elysia/openapi'

const app = new Elysia()
    .use(openapi({
        references: fromTypes()  // Reads TypeScript source
    }))
```

### Production Setup

```typescript
.use(openapi({
    references: fromTypes(
        process.env.NODE_ENV === 'production'
            ? 'dist/index.d.ts'     // Pre-built declarations
            : 'src/index.ts'        // Source files
    )
}))
```

## Standard Schema Mapping

For non-TypeBox schemas (Zod, Valibot), provide JSON Schema mappers:

```typescript
import { z } from 'zod'

.use(openapi({
    mapJsonSchema: {
        zod: z.toJSONSchema
    }
}))
```

This ensures Zod schemas appear correctly in the OpenAPI spec.

## Common Pitfalls

1. **Schemas are documentation** — If you skip `body`/`response` schemas on a route, it won't appear in the docs with type information. Add schemas to document endpoints.

2. **Model names must be unique** — Duplicate model names cause conflicts. Use descriptive names like `CreateUser` and `UpdateUser` rather than just `User`.

3. **Security is per-route opt-in** — Defining `securitySchemes` doesn't auto-apply them. You must add `security: [{ schemeName: [] }]` to routes or instances.

4. **Headers need withHeader** — Standard `response` schemas don't document response headers. Use `withHeader()` to annotate them in the OpenAPI spec.

5. **Zod needs mapJsonSchema** — Zod schemas don't auto-convert to OpenAPI. Add `mapJsonSchema: { zod: z.toJSONSchema }` to the plugin config.
