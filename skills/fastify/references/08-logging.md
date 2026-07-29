# Fastify — Logging

> Source: [fastify.dev/docs/latest/Reference/Logging](https://fastify.dev/docs/latest/Reference/Logging/)

## Table of Contents

- [Enabling Logging](#enabling-logging)
- [Using the Logger](#using-the-logger)
- [Request ID Tracking](#request-id-tracking)
- [Serializers](#serializers)
- [Log Redaction](#log-redaction)
- [Custom Logger Instance](#custom-logger-instance)
- [Common Pitfalls](#common-pitfalls)

## Overview

Fastify uses Pino as its default logger, chosen for its extremely low overhead. Logging is disabled by default and produces structured JSON output when enabled.

## Enabling Logging

### Basic

```javascript
import Fastify from 'fastify'
const fastify = Fastify({ logger: true })
```

### With Options

```javascript
const fastify = Fastify({
  logger: {
    level: 'info',
    transport: {
      target: 'pino-pretty',
      options: {
        translateTime: 'HH:MM:ss Z',
        ignore: 'pid,hostname'
      }
    }
  }
})
```

Install `pino-pretty` as a dev dependency for human-readable output.

### Environment-Specific Configuration

```javascript
const envToLogger = {
  development: {
    transport: {
      target: 'pino-pretty',
      options: {
        translateTime: 'HH:MM:ss Z',
        ignore: 'pid,hostname'
      }
    }
  },
  production: {
    level: 'info'
    // JSON output by default — no transport
  },
  test: false  // disabled
}

const fastify = Fastify({
  logger: envToLogger[process.env.NODE_ENV] ?? true
})
```

### File Output

```javascript
const fastify = Fastify({
  logger: {
    level: 'info',
    file: '/var/log/app.log'
  }
})
```

### Custom Stream

```javascript
import split from 'split2'
const stream = split(JSON.parse)

const fastify = Fastify({
  logger: {
    level: 'info',
    stream
  }
})
```

## Using the Logger

### In Route Handlers

```javascript
fastify.get('/users/:id', async (request, reply) => {
  request.log.info('fetching user')
  request.log.debug({ userId: request.params.id }, 'query params')

  const user = await getUser(request.params.id)
  if (!user) {
    request.log.warn({ userId: request.params.id }, 'user not found')
  }
  return user
})
```

`request.log` is a Pino child logger that automatically includes the request ID.

### Outside Handlers

```javascript
fastify.log.info('server starting')
fastify.log.error({ err: someError }, 'startup failed')
```

### Log Levels

| Level | Priority | Use For |
|-------|----------|---------|
| `fatal` | 60 | Unrecoverable errors, process must exit |
| `error` | 50 | Error events that might still be handled |
| `warn` | 40 | Unusual situations, potential issues |
| `info` | 30 | General informational messages |
| `debug` | 20 | Detailed debugging information |
| `trace` | 10 | Very detailed tracing information |
| `silent` | ∞ | Disables logging |

### Per-Route Log Level

```javascript
fastify.get('/health', { logLevel: 'warn' }, async () => {
  return { status: 'ok' }
})
// Only warnings and above are logged for this route

fastify.get('/debug-endpoint', { logLevel: 'trace' }, async (request) => {
  request.log.trace('detailed trace info')
  return { ok: true }
})
```

### Per-Plugin Log Level

```javascript
fastify.register(adminRoutes, {
  prefix: '/admin',
  logLevel: 'debug'  // all admin routes log at debug level
})
```

## Request ID Tracking

Fastify assigns a unique ID to every request for correlation:

```javascript
fastify.get('/', async (request) => {
  request.log.info('processing')
  // Log output includes: { reqId: "req-1", msg: "processing" }
  return { requestId: request.id }
})
```

### Custom Request ID Header

```javascript
const fastify = Fastify({
  requestIdHeader: 'x-request-id'
  // Uses the client-provided header value if present
})
```

### Custom ID Generator

```javascript
import { randomUUID } from 'node:crypto'

const fastify = Fastify({
  genReqId: (req) => randomUUID()
})
```

## Serializers

Fastify includes default serializers for `req`, `res`, and `err` objects to control what gets logged.

### Custom Request Serializer

```javascript
const fastify = Fastify({
  logger: {
    serializers: {
      req(request) {
        return {
          method: request.method,
          url: request.url,
          path: request.routeOptions.url,
          parameters: request.params,
          headers: request.headers
        }
      }
    }
  }
})
```

### Custom Response Serializer

```javascript
const fastify = Fastify({
  logger: {
    serializers: {
      res(reply) {
        return {
          statusCode: reply.statusCode,
          headers: typeof reply.getHeaders === 'function'
            ? reply.getHeaders()
            : {}
        }
      }
    }
  }
})
```

### Per-Plugin Serializers

```javascript
fastify.register(myPlugin, {
  logSerializers: {
    user: (value) => `User(${value.id})`
  }
})
```

Serializers inherit through the plugin context and can override parent serializers.

### Logging Request Bodies

The `req` serializer cannot access `request.body` because body parsing hasn't occurred yet. Log the body in a hook:

```javascript
fastify.addHook('preHandler', async (request) => {
  if (request.body) {
    request.log.info({ body: request.body }, 'parsed body')
  }
})
```

### Serializer Safety

Serializers must never throw errors — an exception in a serializer can crash the Node.js process.

## Log Redaction

Mask sensitive data in log output:

```javascript
const fastify = Fastify({
  logger: {
    level: 'info',
    redact: ['req.headers.authorization'],
    serializers: {
      req(request) {
        return {
          method: request.method,
          url: request.url,
          headers: request.headers,
          remoteAddress: request.ip
        }
      }
    }
  }
})
```

Multiple redaction paths:

```javascript
redact: [
  'req.headers.authorization',
  'req.headers.cookie',
  'req.headers["x-api-key"]'
]
```

With custom replacement:

```javascript
redact: {
  paths: ['req.headers.authorization'],
  censor: '[REDACTED]'
}
```

## Custom Logger Instance

Supply a pre-configured Pino instance:

```javascript
import pino from 'pino'

const logger = pino({
  level: 'info',
  transport: { target: 'pino-pretty' }
})

const fastify = Fastify({ loggerInstance: logger })
```

The custom logger must implement Pino's interface: `info`, `error`, `debug`, `fatal`, `warn`, `trace`, `silent`, `child` methods and a `level` property.

Note: In Fastify v5, use `loggerInstance` instead of `logger` for custom instances.

## Child Logger Factory

Customize how child loggers are created per request:

```javascript
const fastify = Fastify({
  logger: true,
  childLoggerFactory: function (logger, bindings, opts, rawReq) {
    const child = logger.child(bindings, opts)
    child.customProp = rawReq.headers['x-tenant-id']
    return child
  }
})
```

## Structured Logging Pattern

```javascript
// Good: structured data as first argument
request.log.info({ userId: 123, action: 'login' }, 'user logged in')

// Good: error object
request.log.error({ err: error, userId: 123 }, 'login failed')

// Avoid: string interpolation (slower, loses structure)
request.log.info(`User ${userId} logged in`)  // don't do this
```

## Common Pitfalls

1. **String interpolation** — `log.info(\`User ${id}\`)` loses structured data; pass objects as the first argument
2. **pino-pretty in production** — adds overhead; only use in development via `transport`
3. **Body in req serializer** — body isn't available during request serialization; use a preHandler hook
4. **Logger vs loggerInstance** — Fastify v5 requires `loggerInstance` for custom logger instances; `logger` only accepts Pino options
5. **Serializer exceptions** — a throwing serializer crashes the process; always handle edge cases in serializers
6. **Redaction performance** — each redaction path adds minimal overhead; keep the list reasonable but don't worry about a handful of paths
