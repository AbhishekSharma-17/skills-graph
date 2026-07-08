# ElysiaJS — Integration & Deployment

> Source: [elysiajs.com](https://elysiajs.com/) · Version 1.4.x

## Table of Contents

- [WinterTC & Multi-Runtime](#wintertc--multi-runtime)
- [Next.js Integration](#nextjs-integration)
- [Mount (Framework Composition)](#mount-framework-composition)
- [Node.js Adapter](#nodejs-adapter)
- [Docker Deployment](#docker-deployment)
- [Unit Testing](#unit-testing)
- [CORS Configuration](#cors-configuration)
- [JWT Authentication](#jwt-authentication)
- [Static Files](#static-files)
- [Production Checklist](#production-checklist)
- [Common Pitfalls](#common-pitfalls)

---

## WinterTC & Multi-Runtime

ElysiaJS implements the WinterTC standard (Web-interoperable Runtimes Community Group), using Web Standard `Request` and `Response` APIs. This makes it portable across runtimes:

| Runtime | Support Level |
|---------|--------------|
| **Bun** | Primary, full optimization |
| **Node.js** | Via `@elysiajs/node` adapter |
| **Deno** | Community support |
| **Cloudflare Workers** | Via fetch handler |
| **Vercel Edge** | Via fetch handler |
| **Netlify Edge** | Via fetch handler |

### Cloudflare Workers

```typescript
import { Elysia } from 'elysia'

const app = new Elysia()
    .get('/', () => 'Hello from the Edge')

export default {
    fetch: app.fetch
}
```

### Vercel Edge

```typescript
// api/index.ts
import { Elysia } from 'elysia'

const app = new Elysia({ prefix: '/api' })
    .get('/', () => 'Hello Vercel')

export const GET = app.fetch
export const POST = app.fetch
```

## Next.js Integration

Run Elysia as Next.js API routes using App Router catch-all routes:

### Setup

```typescript
// app/api/[[...slugs]]/route.ts
import { Elysia, t } from 'elysia'

const app = new Elysia({ prefix: '/api' })
    .get('/', () => 'Hello from Elysia in Next.js')
    .post('/echo', ({ body }) => body, {
        body: t.Object({
            message: t.String()
        })
    })
    .get('/users/:id', ({ params }) => ({
        id: params.id,
        name: 'User ' + params.id
    }))

export const GET = app.fetch
export const POST = app.fetch
export const PUT = app.fetch
export const DELETE = app.fetch
export const PATCH = app.fetch
```

### Key Points

- Use `prefix: '/api'` matching the file directory
- Export `app.fetch` for each HTTP method you need
- For pnpm, install peer deps: `@sinclair/typebox`, `openapi-types`
- Eden works with Next.js for isomorphic type-safe calls

### Subdirectory Prefix

```typescript
// app/user/[[...slugs]]/route.ts
const app = new Elysia({ prefix: '/user' })
    .get('/profile', getProfile)
    .put('/settings', updateSettings)
```

## Mount (Framework Composition)

`.mount()` integrates any WinterTC-compliant framework via its `fetch` function:

```typescript
import { Elysia } from 'elysia'
import { Hono } from 'hono'

const hono = new Hono()
    .get('/', (c) => c.text('Hello from Hono'))

const app = new Elysia()
    .get('/', () => 'Hello from Elysia')
    .mount('/hono', hono.fetch)     // /hono/* handled by Hono
    .listen(3000)
```

### Compatible Frameworks

- Hono
- Nitro / H3
- Next.js (API routes)
- Nuxt (server routes)
- SvelteKit (endpoints)
- Any framework exposing a `fetch(Request): Response` function

### Nested Mounting

```typescript
const micro1 = new Elysia().get('/', () => 'Service 1')
const micro2 = new Elysia().get('/', () => 'Service 2')

const gateway = new Elysia()
    .mount('/service1', micro1.fetch)
    .mount('/service2', micro2.fetch)
    .listen(3000)
```

## Node.js Adapter

Run Elysia on Node.js when Bun isn't available:

```bash
npm install elysia @elysiajs/node
```

```typescript
import { Elysia } from 'elysia'
import { node } from '@elysiajs/node'

const app = new Elysia({ adapter: node() })
    .get('/', () => 'Hello from Node.js')
    .listen(3000)
```

Performance will be lower than Bun but the API is identical.

## Docker Deployment

### Dockerfile (Bun)

```dockerfile
FROM oven/bun:1 AS base
WORKDIR /app

# Install dependencies
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile --production

# Copy source
COPY src/ src/
COPY tsconfig.json ./

# Run
EXPOSE 3000
ENV NODE_ENV=production
CMD ["bun", "run", "src/index.ts"]
```

### Multi-Stage Build

```dockerfile
FROM oven/bun:1 AS build
WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun build src/index.ts --outdir ./dist --target bun

FROM oven/bun:1-slim AS production
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
EXPOSE 3000
ENV NODE_ENV=production
CMD ["bun", "run", "dist/index.js"]
```

### Docker Compose

```yaml
version: '3.8'
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
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## Unit Testing

### Using Elysia.handle()

```typescript
import { describe, expect, it } from 'bun:test'
import { Elysia } from 'elysia'

describe('API', () => {
    const app = new Elysia()
        .get('/', () => 'Hello')
        .post('/echo', ({ body }) => body)

    it('handles GET /', async () => {
        const res = await app.handle(
            new Request('http://localhost/')
        )
        expect(await res.text()).toBe('Hello')
        expect(res.status).toBe(200)
    })

    it('handles POST /echo', async () => {
        const res = await app.handle(
            new Request('http://localhost/echo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'hi' })
            })
        )
        const data = await res.json()
        expect(data.message).toBe('hi')
    })
})
```

### Using Eden Treaty for Type-Safe Tests

```typescript
import { treaty } from '@elysia/eden'

const app = new Elysia()
    .get('/users/:id', ({ params }) => ({
        id: Number(params.id),
        name: 'Test User'
    }))

const api = treaty(app)  // No URL — direct instance

it('gets a user', async () => {
    const { data, error } = await api.users({ id: 1 }).get()
    expect(error).toBeNull()
    expect(data?.name).toBe('Test User')
})
```

### Testing with Deferred Modules

```typescript
const app = new Elysia()
    .use(import('./plugins/auth'))
    .use(import('./routes/users'))

await app.modules  // Wait for dynamic imports

const res = await app.handle(new Request('http://localhost/users'))
```

## CORS Configuration

```bash
bun add @elysia/cors
```

```typescript
import { cors } from '@elysia/cors'

app.use(cors({
    origin: ['https://example.com', 'https://app.example.com'],
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true,
    maxAge: 86400
}))
```

## JWT Authentication

```bash
bun add @elysia/jwt
```

```typescript
import { jwt } from '@elysia/jwt'

const app = new Elysia()
    .use(jwt({
        name: 'jwt',
        secret: process.env.JWT_SECRET!
    }))
    .post('/login', async ({ jwt, body }) => {
        const user = await authenticate(body)
        const token = await jwt.sign({ sub: user.id, role: user.role })
        return { token }
    })
    .derive(async ({ jwt, headers }) => {
        const token = headers.authorization?.split(' ')[1]
        if (!token) return { auth: null }
        const payload = await jwt.verify(token)
        return { auth: payload }
    })
    .get('/me', ({ auth }) => {
        if (!auth) return status(401)
        return auth
    })
```

## Static Files

```bash
bun add @elysia/static
```

```typescript
import { staticPlugin } from '@elysia/static'

app.use(staticPlugin({
    assets: 'public',           // Directory to serve
    prefix: '/static',          // URL prefix
    alwaysStatic: false,        // Cache in memory
    ignorePatterns: ['.git']    // Ignore patterns
}))
```

## Production Checklist

1. **Set `NODE_ENV=production`** — Disables verbose validation errors
2. **Use `bun run` not `bun dev`** — Dev mode adds overhead
3. **Enable CORS** — Configure allowed origins explicitly
4. **Add health check** — `GET /health` endpoint for load balancers
5. **Structured logging** — Use `onAfterResponse` for request logging
6. **Graceful shutdown** — Handle SIGTERM for container orchestration
7. **Rate limiting** — Implement via `onBeforeHandle` or macro
8. **Security headers** — Set via `onAfterHandle` or dedicated plugin

### Graceful Shutdown

```typescript
const app = new Elysia()
    .get('/', () => 'Hello')
    .listen(3000)

process.on('SIGTERM', () => {
    console.log('Shutting down...')
    app.stop()
    process.exit(0)
})
```

## Common Pitfalls

1. **Next.js prefix must match directory** — If your catch-all is at `app/api/[...]`, the Elysia prefix must be `/api`.

2. **Mount loses Elysia features** — Mounted frameworks don't benefit from Elysia's type system, validation, or lifecycle. They run independently.

3. **Handle() needs full URLs** — `app.handle(new Request('/path'))` fails. Use `http://localhost/path`.

4. **Node.js performance** — The Node adapter works but benchmarks at 10-20% of Bun performance. Use Bun for production when possible.

5. **Deferred modules in tests** — Always `await app.modules` when using dynamic `import()` in plugins before running test assertions.
