# Fastify — Decorators

> Source: [fastify.dev/docs/latest/Reference/Decorators](https://fastify.dev/docs/latest/Reference/Decorators/)

## Overview

Decorators customize core Fastify objects (server instance, request, reply) by attaching properties and methods. The API is synchronous and designed to optimize JavaScript engine performance by defining object shapes before instantiation.

## Server Instance Decorators

### decorate(name, value, [dependencies])

Adds properties or methods to the Fastify instance:

```javascript
// Function decorator
fastify.decorate('authenticate', async (request) => {
  const token = request.headers.authorization
  return verifyJwt(token)
})

// Object decorator
fastify.decorate('config', {
  db: 'postgres://localhost/mydb',
  port: 3000,
  env: 'production'
})

// Simple value
fastify.decorate('appVersion', '2.1.0')
```

### Accessing Decorators in Handlers

```javascript
fastify.decorate('greet', function (name) {
  return `Hello, ${name}!`
})

fastify.get('/', function (request, reply) {
  // Access via `this` (regular function required)
  reply.send(this.greet('World'))
})
```

Arrow functions break `this` binding — always use regular functions when accessing decorators via `this`.

### Dependencies

Declare required decorators to ensure boot-time validation:

```javascript
import fp from 'fastify-plugin'

export default fp(async function greetPlugin(fastify) {
  fastify.decorate('greet', () => 'hello')
}, {
  dependencies: ['database', 'cache']  // must exist before this plugin loads
})
```

## Request Decorators

### decorateRequest(name, value)

Adds properties to every Request object:

```javascript
// Declare the decorator shape
fastify.decorateRequest('user', null)

// Populate per-request via hook
fastify.addHook('preHandler', async (request) => {
  request.user = await authenticate(request)
})

// Use in handlers
fastify.get('/profile', async (request) => {
  return { name: request.user.name }
})
```

### Reference Type Restriction

You CANNOT use objects or arrays as default values — they would be shared across all requests:

```javascript
// WRONG — shared state across requests!
fastify.decorateRequest('data', { items: [] })

// CORRECT — use null, then set per-request in a hook
fastify.decorateRequest('data', null)
fastify.addHook('onRequest', async (request) => {
  request.data = { items: [] }
})
```

### Shape Initialization

Initialize decorators with shapes matching future values for V8 optimization:

```javascript
fastify.decorateRequest('startTime', 0)        // will be a number
fastify.decorateRequest('tenantId', '')         // will be a string
fastify.decorateRequest('user', null)           // will be an object
fastify.decorateRequest('permissions', null)    // will be an array
```

## Reply Decorators

### decorateReply(name, value)

Same rules as request decorators — no reference types as defaults:

```javascript
fastify.decorateReply('sendSuccess', function (data) {
  this.code(200).send({ success: true, data })
})

fastify.decorateReply('sendError', function (statusCode, message) {
  this.code(statusCode).send({ success: false, error: message })
})

// Usage
fastify.get('/users/:id', async (request, reply) => {
  const user = await getUser(request.params.id)
  if (!user) {
    return reply.sendError(404, 'User not found')
  }
  return reply.sendSuccess(user)
})
```

## Utility Methods

### hasDecorator / hasRequestDecorator / hasReplyDecorator

```javascript
if (fastify.hasDecorator('db')) {
  // db decorator exists on the instance
}

if (fastify.hasRequestDecorator('user')) {
  // user decorator exists on Request
}

if (fastify.hasReplyDecorator('sendSuccess')) {
  // sendSuccess decorator exists on Reply
}
```

### getDecorator / setDecorator

Type-safe access without relying on declaration merging:

```javascript
// Get with explicit type (TypeScript)
const db = fastify.getDecorator<Database>('db')

// Set decorator value
fastify.setDecorator('appVersion', '2.2.0')
```

`getDecorator` throws `FST_ERR_DEC_UNDECLARED` if the decorator doesn't exist.

## Getter/Setter Pattern

Define computed properties:

```javascript
fastify.decorate('currentTime', {
  getter() {
    return new Date().toISOString()
  }
})

// Access
console.log(fastify.currentTime)  // '2026-07-30T...'
```

Per-request computed values:

```javascript
fastify.decorateRequest('elapsed', {
  getter() {
    return Date.now() - this.startTime
  }
})
```

## Encapsulation

Decorators follow the same encapsulation rules as plugins:

```javascript
fastify.register(async function pluginA(instance) {
  instance.decorate('onlyInA', true)
  // onlyInA is visible here and in child plugins
})

fastify.register(async function pluginB(instance) {
  // instance.onlyInA is undefined — sibling scope
})
```

To share decorators across scopes, wrap the plugin with `fastify-plugin`:

```javascript
import fp from 'fastify-plugin'

export default fp(async function shared(fastify) {
  fastify.decorate('db', await connectDb())
  // db is now visible in parent and all siblings
})
```

### Redeclaration Rules

Redefining a decorator with the same name in the same encapsulated context throws an exception. However, child scopes can shadow parent decorators.

## TypeScript Declaration Merging

Extend Fastify interfaces to get type safety for decorators:

```typescript
declare module 'fastify' {
  interface FastifyInstance {
    db: Database
    config: AppConfig
    authenticate: (request: FastifyRequest) => Promise<User>
  }

  interface FastifyRequest {
    user: User | null
    tenantId: string
  }

  interface FastifyReply {
    sendSuccess: (data: unknown) => void
    sendError: (code: number, message: string) => void
  }
}
```

## Real-World Example: Auth + Database Plugin

```javascript
import fp from 'fastify-plugin'

export default fp(async function corePlugin(fastify, opts) {
  // Database
  const pool = await createPool(opts.dbUrl)
  fastify.decorate('db', pool)

  // Request decorators
  fastify.decorateRequest('user', null)
  fastify.decorateRequest('tenantId', '')

  // Auth decorator
  fastify.decorate('authenticate', async function (request, reply) {
    const token = request.headers.authorization?.split(' ')[1]
    if (!token) {
      reply.code(401).send({ error: 'No token' })
      return reply
    }
    const payload = await verifyJwt(token)
    request.user = payload.user
    request.tenantId = payload.tenantId
  })

  // Cleanup
  fastify.addHook('onClose', async () => {
    await pool.end()
  })
})
```

## Common Pitfalls

1. **Reference type defaults** — objects/arrays as decorator defaults are shared across all requests, causing data leakage between requests
2. **Arrow functions and `this`** — arrow functions in handlers/hooks cannot access decorators via `this`; use regular functions
3. **Decorator before registration** — decorators from plugins aren't available until the plugin finishes loading; use `after()` or `ready()`
4. **Duplicate names** — redefining a decorator in the same scope throws; check with `hasDecorator()` first
5. **Missing TypeScript augmentation** — without declaration merging, TypeScript won't know about your custom decorators
