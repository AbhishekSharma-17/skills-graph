# Fastify — Deployment & Production

> Source: [fastify.dev/docs/latest/Reference/Server](https://fastify.dev/docs/latest/Reference/Server/) and [fastify.dev/docs/latest/Guides/Migration-Guide-V5](https://fastify.dev/docs/latest/Guides/Migration-Guide-V5/)

## Table of Contents

- [Server Factory Options](#server-factory-options)
- [Graceful Shutdown](#graceful-shutdown)
- [Docker Deployment](#docker-deployment)
- [Performance Tuning](#performance-tuning)
- [Security Hardening](#security-hardening)
- [Health Check Endpoint](#health-check-endpoint)
- [Fastify v5 Migration Checklist](#fastify-v5-migration-checklist)
- [Production Checklist](#production-checklist)
- [Common Pitfalls](#common-pitfalls)

## Server Factory Options

### Core Configuration

```javascript
import Fastify from 'fastify'

const app = Fastify({
  // Logging
  logger: {
    level: process.env.LOG_LEVEL || 'info'
    // No transport in production — raw JSON to stdout
  },

  // Request limits
  bodyLimit: 1048576,           // 1MB max body (default)
  maxParamLength: 100,          // URL param length limit (ReDoS protection)

  // Timeouts
  connectionTimeout: 0,         // socket timeout (0 = disabled)
  keepAliveTimeout: 72000,      // 72s keep-alive (default)
  requestTimeout: 30000,        // 30s to receive full request
  pluginTimeout: 10000,         // 10s for plugin loading

  // Router
  caseSensitive: true,          // /Foo !== /foo (default)
  ignoreTrailingSlash: false,   // /foo !== /foo/ (default)
  ignoreDuplicateSlashes: false,

  // Security
  trustProxy: false,            // set to true behind a reverse proxy
  onProtoPoisoning: 'error',    // reject __proto__ in JSON
  onConstructorPoisoning: 'error',

  // Request ID
  requestIdHeader: 'x-request-id',
  genReqId: (req) => crypto.randomUUID()
})
```

### Trust Proxy

When running behind nginx, Cloudflare, or a load balancer:

```javascript
const app = Fastify({
  trustProxy: true
  // Or be specific:
  // trustProxy: '127.0.0.1'
  // trustProxy: ['127.0.0.0/8', '10.0.0.0/8']
  // trustProxy: 2  // trust N hops
})
```

This enables `request.ip` to read from `X-Forwarded-For` and `request.protocol` from `X-Forwarded-Proto`.

### HTTPS

```javascript
import { readFileSync } from 'node:fs'

const app = Fastify({
  https: {
    key: readFileSync('./certs/key.pem'),
    cert: readFileSync('./certs/cert.pem')
  }
})
```

### HTTP/2

```javascript
const app = Fastify({
  http2: true,
  https: {
    key: readFileSync('./certs/key.pem'),
    cert: readFileSync('./certs/cert.pem'),
    allowHTTP1: true  // fallback to HTTP/1.1
  }
})
```

## Graceful Shutdown

```javascript
const app = buildApp({ logger: true })

// Handle shutdown signals
const signals = ['SIGINT', 'SIGTERM']
for (const signal of signals) {
  process.on(signal, async () => {
    app.log.info(`Received ${signal}, shutting down...`)
    await app.close()
    process.exit(0)
  })
}

// close() drains connections, runs onClose hooks, then resolves
await app.listen({ port: 3000, host: '0.0.0.0' })
```

### Shutdown Hook Order

1. `preClose` hooks — before HTTP server stops
2. HTTP server stops accepting new connections
3. In-flight requests complete
4. Connections drain
5. `onClose` hooks — cleanup resources (DB, cache, etc.)
6. Child-plugin `onClose` hooks run before parent hooks

## Docker Deployment

### Dockerfile

```dockerfile
FROM node:22-slim AS base

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy application
COPY . .

# Non-root user
USER node

EXPOSE 3000

CMD ["node", "server.js"]
```

### Docker Key Points

- **Bind to `0.0.0.0`** — Fastify defaults to `127.0.0.1`, which is unreachable from outside the container:

```javascript
await app.listen({ port: 3000, host: '0.0.0.0' })
```

- **Use `node` directly** — avoid `npm start` in Docker; it adds an unnecessary process layer
- **Set `NODE_ENV=production`** — via environment variable, not in Dockerfile
- **Health check** — add a health endpoint and Docker HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:3000/health || exit 1
```

### docker-compose.yml

```yaml
services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
    depends_on:
      - db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

## Performance Tuning

### Response Schemas

Always define response schemas — they enable fast-json-stringify, which is 2-3x faster than `JSON.stringify`:

```javascript
app.get('/users', {
  schema: {
    response: {
      200: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            name: { type: 'string' }
          }
        }
      }
    }
  }
}, handler)
```

### Load Shedding with @fastify/under-pressure

Protect against overload:

```javascript
import underPressure from '@fastify/under-pressure'

app.register(underPressure, {
  maxEventLoopDelay: 1000,
  maxHeapUsedBytes: 200 * 1024 * 1024,
  maxRssBytes: 500 * 1024 * 1024,
  retryAfter: 50,
  pressureHandler: (request, reply, type, value) => {
    reply.code(503).send({
      error: 'Service Unavailable',
      message: `Server under pressure: ${type}`
    })
  }
})
```

### Connection Keep-Alive

```javascript
const app = Fastify({
  keepAliveTimeout: 72000,    // 72s (default, good for most cases)
  // For high-throughput APIs behind a load balancer:
  // keepAliveTimeout: 5000   // shorter to free connections faster
})
```

### Handler Timeout

Prevent slow handlers from holding connections:

```javascript
app.get('/slow', {
  handlerTimeout: 5000  // 5 second limit
}, async (request) => {
  return await potentiallySlowOperation()
})
```

## Security Hardening

### Essential Security Headers

```javascript
import helmet from '@fastify/helmet'
app.register(helmet)
```

### Rate Limiting

```javascript
import rateLimit from '@fastify/rate-limit'

app.register(rateLimit, {
  max: 100,
  timeWindow: '1 minute'
})
```

### CORS

```javascript
import cors from '@fastify/cors'

app.register(cors, {
  origin: process.env.ALLOWED_ORIGINS?.split(',') || false,
  credentials: true
})
```

### Body Size Limits

```javascript
const app = Fastify({
  bodyLimit: 1048576  // 1MB default
})

// Per-route override for file uploads
app.post('/upload', {
  bodyLimit: 50 * 1024 * 1024  // 50MB for this route
}, handler)
```

### Prototype Poisoning Protection

Fastify protects against `__proto__` and `constructor` injection by default:

```javascript
const app = Fastify({
  onProtoPoisoning: 'error',       // reject (default)
  onConstructorPoisoning: 'error'  // reject (default)
})
```

## Health Check Endpoint

```javascript
app.get('/health', { logLevel: 'warn' }, async () => {
  return {
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  }
})

app.get('/ready', { logLevel: 'warn' }, async () => {
  const dbOk = await checkDatabase()
  const cacheOk = await checkCache()

  if (!dbOk || !cacheOk) {
    const err = new Error('Not ready')
    err.statusCode = 503
    throw err
  }

  return { status: 'ready', db: dbOk, cache: cacheOk }
})
```

## Environment Configuration

Use `@fastify/env` for validated configuration:

```javascript
import env from '@fastify/env'

app.register(env, {
  schema: {
    type: 'object',
    required: ['DATABASE_URL'],
    properties: {
      PORT: { type: 'integer', default: 3000 },
      HOST: { type: 'string', default: '0.0.0.0' },
      DATABASE_URL: { type: 'string' },
      JWT_SECRET: { type: 'string' },
      NODE_ENV: { type: 'string', default: 'development' },
      LOG_LEVEL: { type: 'string', default: 'info' }
    }
  }
})
```

## Fastify v5 Migration Checklist

Key breaking changes from v4:

| Change | v4 | v5 |
|--------|----|----|
| Node.js | v14+ | v20+ |
| JSON Schema | Shorthand allowed | Full schema with `type` required |
| Custom logger | `logger: instance` | `loggerInstance: instance` |
| `listen()` | Variadic args | Object syntax only |
| `redirect()` | `redirect(code, url)` | `redirect(url, code?)` |
| Request properties | `request.routerPath` | `request.routeOptions.url` |
| `request.connection` | Available | Removed (use `request.socket`) |
| `reply.getResponseTime()` | Available | Removed (use `reply.elapsedTime`) |
| Plugins | Can mix callback+promise | Must choose one pattern |
| DELETE body | Empty body accepted | Empty body with JSON content-type rejected |
| Semicolons in query | Enabled | Disabled by default |

## Production Checklist

- [ ] Response schemas on all routes (performance + security)
- [ ] Structured JSON logging (no pino-pretty in production)
- [ ] Graceful shutdown handling (SIGINT, SIGTERM)
- [ ] Health check and readiness endpoints
- [ ] Rate limiting on public-facing routes
- [ ] Security headers via @fastify/helmet
- [ ] CORS configured for allowed origins only
- [ ] Body size limits set appropriately
- [ ] Trust proxy configured correctly behind reverse proxy
- [ ] Error handler that hides internal details in production
- [ ] Request timeout set to prevent hung connections
- [ ] Load shedding via @fastify/under-pressure
- [ ] Bind to `0.0.0.0` in containerized environments

## Common Pitfalls

1. **Localhost bind in containers** — Fastify binds to `127.0.0.1` by default; always use `host: '0.0.0.0'` in Docker
2. **pino-pretty in production** — adds CPU overhead; use raw JSON output and pipe to jq or a log aggregator
3. **Missing trustProxy** — behind a load balancer, `request.ip` returns the proxy's IP without `trustProxy: true`
4. **No response schemas** — missing schemas mean every response uses slow `JSON.stringify` and may leak internal fields
5. **Node.js version** — Fastify v5 requires Node.js v20+; check your Docker base image
