# Fastify — Lifecycle Hooks

> Source: [fastify.dev/docs/latest/Reference/Hooks](https://fastify.dev/docs/latest/Reference/Hooks/)

## Table of Contents

- [Request/Reply Hooks](#requestreply-hooks-execution-order)
- [Application Hooks](#application-hooks)
- [Early Response from Hooks](#early-response-from-hooks)
- [Error Handling in Hooks](#error-handling-in-hooks)
- [Hook Scope and Encapsulation](#hook-scope-and-encapsulation)
- [Route-Level Hooks](#route-level-hooks)
- [Diagnostics Channel Hooks](#diagnostics-channel-hooks)
- [Common Pitfalls](#common-pitfalls)

## Overview

Hooks let you listen to specific lifecycle events in the request/response cycle and at the application level. Register them with `fastify.addHook(name, fn)`. Hooks must be registered before their events trigger.

## Request/Reply Hooks (Execution Order)

### 1. onRequest

First hook in the cycle. Body has not been parsed yet.

```javascript
fastify.addHook('onRequest', async (request, reply) => {
  // request.body is always undefined here
  request.log.info('incoming request')
})
```

### 2. preParsing

Runs before body parsing. Can transform the request payload stream. Must return a stream.

```javascript
fastify.addHook('preParsing', async (request, reply, payload) => {
  // Decompress, decrypt, or transform the raw stream
  const decompressed = payload.pipe(zlib.createGunzip())
  decompressed.receivedEncodedLength = parseInt(
    request.headers['content-length'], 10
  )
  return decompressed
})
```

The returned stream must have a `receivedEncodedLength` property for Content-Length validation.

### 3. preValidation

Runs after parsing, before schema validation. Can modify `request.body`.

```javascript
fastify.addHook('preValidation', async (request, reply) => {
  // Inject defaults or transform before validation
  if (request.body) {
    request.body.timestamp = Date.now()
  }
})
```

### 4. preHandler

Runs after validation, before the route handler. Common for auth checks.

```javascript
fastify.addHook('preHandler', async (request, reply) => {
  const user = await verifyToken(request.headers.authorization)
  if (!user) {
    reply.code(401).send({ error: 'Unauthorized' })
    return reply
  }
  request.user = user
})
```

### 5. preSerialization

Runs before response serialization. Can modify the payload object. NOT called if payload is a string, Buffer, stream, or null.

```javascript
fastify.addHook('preSerialization', async (request, reply, payload) => {
  return {
    data: payload,
    meta: { requestId: request.id }
  }
})
```

### 6. onSend

Final chance to modify the payload before sending. Payload can only be changed to string, Buffer, stream, ReadableStream, Response, or null.

```javascript
fastify.addHook('onSend', async (request, reply, payload) => {
  // Add response wrapper or modify headers
  reply.header('x-response-time', reply.elapsedTime)
  return payload
})
```

### 7. onError

Called when an error occurs. Cannot modify the error or call `reply.send()`. Useful for error logging/monitoring.

```javascript
fastify.addHook('onError', async (request, reply, error) => {
  // Send to error tracking service
  await errorTracker.report(error, {
    url: request.url,
    method: request.method,
    requestId: request.id
  })
})
```

### 8. onResponse

Called after the response has been sent. Cannot send additional data. Useful for metrics/cleanup.

```javascript
fastify.addHook('onResponse', async (request, reply) => {
  request.log.info({
    statusCode: reply.statusCode,
    responseTime: reply.elapsedTime
  }, 'request completed')
})
```

### 9. onTimeout

Triggered when a request times out at the socket level (set via `connectionTimeout`). Cannot send data to client.

```javascript
fastify.addHook('onTimeout', async (request, reply) => {
  request.log.warn('request timed out')
})
```

### 10. onRequestAbort

Fires when the client closes the connection mid-request.

```javascript
fastify.addHook('onRequestAbort', async (request) => {
  request.log.warn('client disconnected')
  // Clean up resources
})
```

## Lifecycle Flow Diagram

```
Incoming Request
  │
  ├─▶ onRequest
  ├─▶ preParsing
  ├─▶ [Body Parsing]
  ├─▶ preValidation
  ├─▶ [Schema Validation]
  ├─▶ preHandler
  ├─▶ [Handler]
  ├─▶ preSerialization
  ├─▶ onSend
  ├─▶ [Response Sent]
  └─▶ onResponse
         │
     (on error) ──▶ onError
     (on timeout) ──▶ onTimeout
     (client abort) ──▶ onRequestAbort
```

## Application Hooks

### onReady

Fires before the server starts listening and when `.ready()` is invoked. Runs serially. Cannot modify routes or add hooks.

```javascript
fastify.addHook('onReady', async () => {
  await database.connect()
  await cache.warmup()
})
```

### onListen

Fires when the server starts listening. Errors are logged but don't prevent startup. Does NOT fire with `fastify.inject()` or `fastify.ready()`.

```javascript
fastify.addHook('onListen', async () => {
  console.log('Server is now listening')
})
```

### onClose

Fires when `fastify.close()` is called, after HTTP connections are drained. Ideal for cleanup.

```javascript
fastify.addHook('onClose', async (instance) => {
  await instance.db.close()
  await instance.cache.disconnect()
})
```

Child-plugin `onClose` hooks run before parent-plugin hooks.

### preClose

Fires when `fastify.close()` is called but before the HTTP server stops listening. Useful for cleaning up state attached to the HTTP server (e.g., open WebSocket connections).

```javascript
fastify.addHook('preClose', async () => {
  await wsServer.closeAllConnections()
})
```

### onRoute

Fires synchronously when a new route is registered. Receives the route options object.

```javascript
fastify.addHook('onRoute', (routeOptions) => {
  console.log(`Registered: ${routeOptions.method} ${routeOptions.url}`)
})
```

### onRegister

Fires when a new plugin registers (before executing plugin code). NOT called for plugins wrapped in `fastify-plugin`.

```javascript
fastify.addHook('onRegister', (instance, opts) => {
  console.log(`Plugin registered with prefix: ${opts.prefix}`)
})
```

## Early Response from Hooks

### Async Pattern

```javascript
fastify.addHook('preHandler', async (request, reply) => {
  if (!request.headers.authorization) {
    reply.code(401).send({ error: 'Missing auth' })
    return reply  // MUST return reply to stop lifecycle
  }
})
```

### Callback Pattern

```javascript
fastify.addHook('preHandler', (request, reply, done) => {
  if (!request.headers.authorization) {
    reply.code(401).send({ error: 'Missing auth' })
    // Do NOT call done() when sending a response
    return
  }
  done()
})
```

## Error Handling in Hooks

```javascript
// Async — just throw
fastify.addHook('preHandler', async (request, reply) => {
  throw new Error('Something failed')
})

// Callback — pass error to done
fastify.addHook('preHandler', (request, reply, done) => {
  done(new Error('Something failed'))
})

// With custom status code
fastify.addHook('preHandler', async (request, reply) => {
  reply.code(403)
  throw new Error('Forbidden')
})
```

## Hook Scope and Encapsulation

All hooks except `onClose` are encapsulated — they apply only to routes registered in the same scope and child scopes.

```javascript
fastify.addHook('onRequest', async () => {
  // Applies to ALL routes (registered at root)
})

fastify.register(async function adminPlugin(app) {
  app.addHook('preHandler', async (request, reply) => {
    // Applies ONLY to routes in this plugin
    await checkAdminRole(request)
  })

  app.get('/admin/dashboard', handler)  // has the admin hook
})

fastify.get('/public', handler)  // does NOT have the admin hook
```

## Route-Level Hooks

Specify hooks directly on route definitions — they run as the last hook in their category:

```javascript
fastify.get('/resource', {
  onRequest: async (request) => { /* ... */ },
  preHandler: [
    async (request) => { /* first */ },
    async (request) => { /* second */ }
  ],
  preSerialization: async (request, reply, payload) => {
    return { ...payload, cached: true }
  }
}, handler)
```

## Accessing Fastify Context in Hooks

Use regular functions (not arrow functions) to access `this`:

```javascript
fastify.addHook('onRequest', function (request, reply, done) {
  // this === the scoped Fastify instance
  this.log.info('plugin-scoped hook')
  done()
})
```

## Diagnostics Channel Hooks

Node.js `diagnostics_channel` integration for APM/tracing:

```javascript
import { subscribe } from 'node:diagnostics_channel'

subscribe('tracing:fastify.request.handler:start', (msg) => {
  console.log(`Request started: ${msg.route.url}`)
})

subscribe('tracing:fastify.request.handler:end', (msg) => {
  console.log(`Request ended: ${msg.route.url}`)
})
```

Available channels: `fastify.initialization`, `tracing:fastify.request.handler:start/end/asyncStart/asyncEnd/error`.

## Common Pitfalls

1. **Forgetting `return reply`** — in async hooks that send a response, always `return reply` to prevent the lifecycle from continuing
2. **Arrow functions lose `this`** — use regular functions when you need access to the Fastify instance via `this`
3. **Hook registration timing** — hooks must be registered before routes; hooks added after `listen()` won't apply to existing routes
4. **preSerialization skips primitives** — this hook is not called when the payload is a string, Buffer, stream, or null
5. **onError cannot modify** — the onError hook is read-only; use `setErrorHandler()` to change error responses
