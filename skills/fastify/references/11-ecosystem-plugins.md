# Fastify — Ecosystem Plugins

> Source: [fastify.dev/ecosystem](https://fastify.dev/ecosystem/)

## Table of Contents

- [Authentication & Security](#authentication--security)
- [API Documentation](#api-documentation)
- [Data Handling](#data-handling)
- [Sessions](#sessions)
- [Real-time](#real-time)
- [Database Plugins](#database-plugins)
- [Server Features](#server-features)
- [Utilities](#utilities)
- [Middleware Compatibility](#middleware-compatibility)
- [Common Pitfalls](#common-pitfalls)

## Overview

Fastify maintains 50+ official plugins under the `@fastify/` scope. These are production-grade, tested against Fastify's CI, and follow the same semver guarantees as the core framework.

## Authentication & Security

### @fastify/jwt

JWT creation and verification using `fast-jwt`:

```bash
npm i @fastify/jwt
```

```javascript
import fastifyJwt from '@fastify/jwt'

app.register(fastifyJwt, { secret: process.env.JWT_SECRET })

// Sign tokens
app.post('/login', async (request) => {
  const user = await authenticate(request.body)
  const token = app.jwt.sign({ id: user.id, role: user.role })
  return { token }
})

// Verify tokens (decorator)
app.decorate('authenticate', async (request, reply) => {
  try {
    await request.jwtVerify()
  } catch (err) {
    reply.send(err)
  }
})

// Protected route
app.get('/profile', { onRequest: [app.authenticate] }, async (request) => {
  return request.user  // decoded JWT payload
})
```

### @fastify/bearer-auth

Simple bearer token authentication:

```javascript
import bearerAuth from '@fastify/bearer-auth'

app.register(bearerAuth, {
  keys: new Set(['super-secret-api-key']),
  errorResponse: (err) => ({ error: 'Unauthorized', code: 401 })
})
```

### @fastify/helmet

Security headers (CSP, HSTS, etc.):

```javascript
import helmet from '@fastify/helmet'

app.register(helmet, {
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"]
    }
  }
})
```

### @fastify/csrf-protection

CSRF token generation and validation:

```javascript
import csrf from '@fastify/csrf-protection'
import cookie from '@fastify/cookie'

app.register(cookie)
app.register(csrf, { cookieOpts: { signed: true } })
```

### @fastify/cors

Cross-Origin Resource Sharing:

```javascript
import cors from '@fastify/cors'

app.register(cors, {
  origin: ['https://app.example.com', 'https://admin.example.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  credentials: true
})
```

### @fastify/rate-limit

Request throttling:

```javascript
import rateLimit from '@fastify/rate-limit'

app.register(rateLimit, {
  max: 100,          // max requests per window
  timeWindow: '1 minute',
  keyGenerator: (request) => request.ip
})

// Per-route override
app.get('/api/search', {
  config: { rateLimit: { max: 10, timeWindow: '1 minute' } }
}, handler)
```

### @fastify/oauth2

OAuth2 provider integration:

```javascript
import oauth2 from '@fastify/oauth2'

app.register(oauth2, {
  name: 'github',
  credentials: {
    client: { id: process.env.GITHUB_ID, secret: process.env.GITHUB_SECRET },
    auth: oauth2.GITHUB_CONFIGURATION
  },
  startRedirectPath: '/login/github',
  callbackUri: 'https://app.example.com/login/github/callback'
})
```

## API Documentation

### @fastify/swagger + @fastify/swagger-ui

Auto-generate OpenAPI documentation from route schemas:

```bash
npm i @fastify/swagger @fastify/swagger-ui
```

```javascript
import swagger from '@fastify/swagger'
import swaggerUi from '@fastify/swagger-ui'

app.register(swagger, {
  openapi: {
    info: {
      title: 'My API',
      version: '1.0.0'
    },
    servers: [{ url: 'https://api.example.com' }]
  }
})

app.register(swaggerUi, {
  routePrefix: '/docs',
  uiConfig: { docExpansion: 'list' }
})
// Visit /docs for Swagger UI
```

Routes with `schema` definitions automatically appear in the documentation.

## Data Handling

### @fastify/cookie

```javascript
import cookie from '@fastify/cookie'

app.register(cookie, {
  secret: 'my-secret',
  parseOptions: { httpOnly: true, secure: true }
})

app.get('/', async (request, reply) => {
  const sessionId = request.cookies.session
  reply.setCookie('visited', 'true', { path: '/', maxAge: 86400 })
  return { sessionId }
})
```

### @fastify/multipart

File uploads:

```javascript
import multipart from '@fastify/multipart'

app.register(multipart, {
  limits: { fileSize: 10 * 1024 * 1024 }  // 10MB
})

app.post('/upload', async (request) => {
  const file = await request.file()
  const buffer = await file.toBuffer()
  await saveFile(file.filename, buffer)
  return { filename: file.filename, size: buffer.length }
})
```

### @fastify/formbody

URL-encoded form data parsing:

```javascript
import formbody from '@fastify/formbody'
app.register(formbody)
// request.body now parses application/x-www-form-urlencoded
```

## Sessions

### @fastify/session

Server-side sessions:

```javascript
import session from '@fastify/session'
import cookie from '@fastify/cookie'

app.register(cookie)
app.register(session, {
  secret: 'a-32-char-secret-at-minimum!!!!!',
  cookie: { secure: false, maxAge: 86400000 }
})

app.get('/', async (request) => {
  request.session.views = (request.session.views || 0) + 1
  return { views: request.session.views }
})
```

### @fastify/secure-session

Stateless encrypted cookie sessions:

```javascript
import secureSession from '@fastify/secure-session'

app.register(secureSession, {
  key: Buffer.from(process.env.SESSION_KEY, 'hex'),
  cookie: { path: '/', httpOnly: true }
})
```

## Real-time

### @fastify/websocket

WebSocket support via the `ws` library:

```javascript
import websocket from '@fastify/websocket'

app.register(websocket)

app.get('/ws', { websocket: true }, (socket, request) => {
  socket.on('message', (msg) => {
    socket.send(`Echo: ${msg}`)
  })

  socket.on('close', () => {
    console.log('Client disconnected')
  })
})
```

## Database Plugins

### @fastify/postgres

```javascript
import pg from '@fastify/postgres'

app.register(pg, {
  connectionString: 'postgres://user:pass@localhost/mydb'
})

app.get('/users', async (request) => {
  const client = await app.pg.connect()
  try {
    const { rows } = await client.query('SELECT * FROM users')
    return rows
  } finally {
    client.release()
  }
})
```

### @fastify/redis

```javascript
import redis from '@fastify/redis'

app.register(redis, { host: '127.0.0.1', port: 6379 })

app.get('/cached', async (request) => {
  const cached = await app.redis.get('key')
  if (cached) return JSON.parse(cached)
  const data = await fetchData()
  await app.redis.set('key', JSON.stringify(data), 'EX', 3600)
  return data
})
```

### @fastify/mongodb

```javascript
import mongo from '@fastify/mongodb'

app.register(mongo, { url: 'mongodb://localhost:27017/mydb' })

app.get('/items', async () => {
  const collection = app.mongo.db.collection('items')
  return collection.find({}).toArray()
})
```

## Server Features

### @fastify/static

Serve static files:

```javascript
import staticPlugin from '@fastify/static'
import { join } from 'node:path'

app.register(staticPlugin, {
  root: join(import.meta.dirname, 'public'),
  prefix: '/public/'
})
```

### @fastify/compress

Response compression:

```javascript
import compress from '@fastify/compress'
app.register(compress, { global: true })
```

### @fastify/http-proxy

Reverse proxy:

```javascript
import proxy from '@fastify/http-proxy'

app.register(proxy, {
  upstream: 'http://backend-service:3001',
  prefix: '/api'
})
```

### @fastify/under-pressure

Health monitoring and circuit breaking:

```javascript
import underPressure from '@fastify/under-pressure'

app.register(underPressure, {
  maxEventLoopDelay: 1000,
  maxHeapUsedBytes: 200 * 1024 * 1024,
  maxRssBytes: 300 * 1024 * 1024,
  retryAfter: 50,
  healthCheck: async () => {
    const dbOk = await checkDatabase()
    return dbOk
  },
  healthCheckInterval: 5000
})
```

## Utilities

### @fastify/autoload

Auto-load plugins from directories:

```javascript
import autoload from '@fastify/autoload'
import { join } from 'node:path'

app.register(autoload, {
  dir: join(import.meta.dirname, 'plugins'),
  encapsulate: false  // share decorators globally
})

app.register(autoload, {
  dir: join(import.meta.dirname, 'routes'),
  options: { prefix: '/api' }
})
```

### @fastify/env

Validated environment configuration:

```javascript
import env from '@fastify/env'

app.register(env, {
  schema: {
    type: 'object',
    required: ['PORT', 'DATABASE_URL'],
    properties: {
      PORT: { type: 'integer', default: 3000 },
      DATABASE_URL: { type: 'string' },
      NODE_ENV: { type: 'string', default: 'development' }
    }
  }
})

// After ready: app.config.PORT, app.config.DATABASE_URL
```

### @fastify/sensible

Common utilities and error constructors:

```javascript
import sensible from '@fastify/sensible'

app.register(sensible)

app.get('/users/:id', async (request, reply) => {
  const user = await getUser(request.params.id)
  if (!user) return reply.notFound('User not found')
  if (!canAccess(user)) return reply.forbidden()
  return user
})
```

### @fastify/awilix

Dependency injection via awilix container with scoped lifetime and auto-disposal.

## Middleware Compatibility

### @fastify/express

Full Express middleware compatibility layer:

```javascript
import expressPlugin from '@fastify/express'
import expressMiddleware from 'some-express-middleware'

await app.register(expressPlugin)
app.use(expressMiddleware())
```

### @fastify/middie

Lightweight Express-style middleware support:

```javascript
import middie from '@fastify/middie'

await app.register(middie)
app.use(someMiddleware)
```

## Common Pitfalls

1. **Plugin version compatibility** — always match `@fastify/` plugin major versions with your Fastify major version (v5 plugins for Fastify v5)
2. **Registration order** — database plugins must register before route plugins that use them
3. **Encapsulation scope** — some plugins (like database connectors) should be wrapped in `fastify-plugin` to be globally accessible
4. **Memory with multipart** — large file uploads can consume memory; use streaming (`request.file()`) instead of buffering
