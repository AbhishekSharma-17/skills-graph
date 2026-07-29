# Fastify — TypeScript Support

> Source: [fastify.dev/docs/latest/Reference/TypeScript](https://fastify.dev/docs/latest/Reference/TypeScript/)

## Table of Contents

- [Setup](#setup)
- [Type Providers](#type-providers)
- [Generic Type Parameters](#generic-type-parameters)
- [Route Handler Typing](#route-handler-typing)
- [Plugin Typing](#plugin-typing)
- [Hook Typing](#hook-typing)
- [Common Pitfalls](#common-pitfalls)

## Overview

Fastify has first-class TypeScript support with a generic-based type system and official type providers. Types cascade through the framework — from server instantiation down to route handlers.

## Setup

```bash
npm i fastify
npm i -D typescript @types/node
```

**tsconfig.json requirements:**
- `target`: `ES2022` or higher
- `module`: `NodeNext` or `Node16`
- `moduleResolution`: `NodeNext` or `Node16`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "outDir": "./dist"
  }
}
```

## Type Providers

Type providers bridge JSON Schema validation with TypeScript types — define your schema once and get both validation and type inference.

### TypeBox (Recommended)

```bash
npm i @fastify/type-provider-typebox @sinclair/typebox
```

```typescript
import Fastify from 'fastify'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'
import { Type, Static } from '@sinclair/typebox'

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>()

const UserSchema = Type.Object({
  name: Type.String({ minLength: 1 }),
  email: Type.String({ format: 'email' }),
  age: Type.Optional(Type.Integer({ minimum: 0 }))
})

type User = Static<typeof UserSchema>

app.post('/users', {
  schema: {
    body: UserSchema,
    response: {
      201: Type.Object({
        id: Type.String(),
        ...UserSchema.properties
      })
    }
  }
}, async (request, reply) => {
  // request.body is typed as User
  const { name, email, age } = request.body
  reply.code(201)
  return { id: generateId(), name, email, age }
})
```

### json-schema-to-ts

```bash
npm i @fastify/type-provider-json-schema-to-ts
```

```typescript
import Fastify from 'fastify'
import { JsonSchemaToTsProvider } from '@fastify/type-provider-json-schema-to-ts'

const app = Fastify().withTypeProvider<JsonSchemaToTsProvider>()

app.post('/users', {
  schema: {
    body: {
      type: 'object',
      required: ['name', 'email'],
      properties: {
        name: { type: 'string' },
        email: { type: 'string' }
      }
    } as const  // 'as const' is required for type inference
  }
}, async (request) => {
  // request.body is typed as { name: string; email: string }
  return { name: request.body.name }
})
```

### Zod (Community)

```bash
npm i fastify-type-provider-zod zod
```

```typescript
import Fastify from 'fastify'
import { ZodTypeProvider } from 'fastify-type-provider-zod'
import { z } from 'zod'

const app = Fastify().withTypeProvider<ZodTypeProvider>()

app.post('/users', {
  schema: {
    body: z.object({
      name: z.string().min(1),
      email: z.string().email()
    })
  }
}, async (request) => {
  // request.body typed via Zod inference
  return { name: request.body.name }
})
```

## Generic Type Parameters

The Fastify instance accepts four primary generics:

| Generic | Default | Purpose |
|---------|---------|---------|
| `RawServer` | `http.Server` | HTTP/HTTPS/HTTP2 server type |
| `RawRequest` | `http.IncomingMessage` | Raw request type |
| `RawReply` | `http.ServerResponse` | Raw response type |
| `Logger` | `FastifyLoggerOptions` | Logger type |

```typescript
import Fastify from 'fastify'
import { FastifyInstance } from 'fastify'

// HTTP (default)
const http: FastifyInstance = Fastify()

// HTTPS
const https = Fastify({ https: { key: '...', cert: '...' } })

// HTTP/2
const http2 = Fastify({ http2: true })
```

## Route Handler Typing

### RequestGenericInterface

Define types for request components:

```typescript
interface CreateUserRequest {
  Body: {
    name: string
    email: string
  }
  Querystring: {
    notify?: boolean
  }
  Params: {
    orgId: string
  }
  Headers: {
    'x-api-key': string
  }
}

app.post<CreateUserRequest>('/orgs/:orgId/users', async (request) => {
  request.body.name      // string
  request.query.notify   // boolean | undefined
  request.params.orgId   // string
  request.headers['x-api-key']  // string
})
```

### With Schema and Type Provider

When using a type provider, explicit generics are usually unnecessary — types are inferred from the schema:

```typescript
app.post('/users', {
  schema: {
    body: Type.Object({
      name: Type.String(),
      email: Type.String()
    })
  }
}, async (request) => {
  // Automatically typed from schema — no generic needed
  request.body.name  // string
})
```

## Plugin Typing

### Plugin Definition

```typescript
import { FastifyPluginAsync, FastifyPluginCallback } from 'fastify'

// Async plugin (recommended)
const myPlugin: FastifyPluginAsync<{ dbUrl: string }> = async (fastify, opts) => {
  const db = await connect(opts.dbUrl)
  fastify.decorate('db', db)
}

// Callback plugin
const legacyPlugin: FastifyPluginCallback<{ port: number }> = (fastify, opts, done) => {
  fastify.decorate('port', opts.port)
  done()
}
```

### Declaration Merging

Extend Fastify interfaces to type custom decorators:

```typescript
declare module 'fastify' {
  interface FastifyInstance {
    db: Database
    config: AppConfig
  }

  interface FastifyRequest {
    user: User | null
    tenantId: string
  }

  interface FastifyReply {
    sendSuccess(data: unknown): void
  }
}
```

### Scoped Type Provider

Apply type providers at the plugin level:

```typescript
import fp from 'fastify-plugin'
import { TypeBoxTypeProvider } from '@fastify/type-provider-typebox'

export default fp(async function routes(app) {
  const typed = app.withTypeProvider<TypeBoxTypeProvider>()

  typed.get('/typed', {
    schema: {
      response: {
        200: Type.Object({ message: Type.String() })
      }
    }
  }, async () => {
    return { message: 'typed!' }
  })
})
```

## Hook Typing

Hooks receive the same generics cascaded from server instantiation:

```typescript
import { FastifyRequest, FastifyReply } from 'fastify'

app.addHook('preHandler', async (
  request: FastifyRequest,
  reply: FastifyReply
) => {
  // request and reply are fully typed
})
```

### Typed Hook with Route Generics

```typescript
app.addHook<{ Querystring: { token: string } }>(
  'preValidation',
  async (request) => {
    request.query.token  // string
  }
)
```

## getDecorator / setDecorator

Type-safe decorator access without declaration merging side effects:

```typescript
// Get with explicit type parameter
const db = fastify.getDecorator<Database>('db')

// Set with type safety
fastify.setDecorator<string>('appVersion', '2.0.0')
```

## TypeScript with fastify-cli

```bash
fastify generate my-app --lang=ts
```

Generates a project with:
- TypeScript configuration
- Type provider setup
- Plugin and route templates with proper typing
- Test configuration

## Vanilla JavaScript with JSDoc

TypeScript types work in JavaScript via JSDoc annotations:

```javascript
/** @type {import('fastify').FastifyPluginAsync} */
const myPlugin = async (fastify) => {
  fastify.get('/', async () => {
    return { hello: 'world' }
  })
}
```

## Common Pitfalls

1. **`require()` breaks types** — ES6 `import` is required for proper type resolution; `require('fastify')` doesn't load type definitions
2. **Missing `as const`** — json-schema-to-ts requires `as const` assertion on schema objects for type inference
3. **Low tsconfig target** — `target` below `ES2017` generates deprecation warnings
4. **Type provider scope** — `withTypeProvider()` returns a new typed instance; store it or chain immediately
5. **Declaration merging side effects** — augmenting `FastifyRequest` in one file affects all files; use `getDecorator<T>()` for localized typing
6. **Plugin options typing** — always define an options interface for plugins to get typed `opts` in the plugin function
