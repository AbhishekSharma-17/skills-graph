# ElysiaJS — Plugin System

> Source: [elysiajs.com/essential/plugin](https://elysiajs.com/essential/plugin) · Version 1.4.x

## Table of Contents

- [Plugin Concept](#plugin-concept)
- [Creating Plugins](#creating-plugins)
- [Plugin Scoping](#plugin-scoping)
- [Deduplication](#deduplication)
- [Lazy Loading](#lazy-loading)
- [Official Plugins](#official-plugins)
- [Plugin Patterns](#plugin-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Plugin Concept

In ElysiaJS, every Elysia instance is a standalone, decoupled unit that can run independently as its own server. Plugins are simply Elysia instances composed into other instances via `.use()`.

```typescript
const plugin = new Elysia()
    .get('/health', () => ({ status: 'ok' }))

const app = new Elysia()
    .use(plugin)
    .listen(3000)
```

This architecture enforces explicit dependency injection — each instance declares its dependencies explicitly rather than relying on implicit global state.

## Creating Plugins

### Instance-Based Plugin

```typescript
// plugins/auth.ts
import { Elysia } from 'elysia'

export const authPlugin = new Elysia({ name: 'auth' })
    .derive(({ headers }) => {
        const token = headers.authorization?.split(' ')[1]
        return { token }
    })
    .macro({
        requireAuth: {
            resolve({ token }) {
                if (!token) return status(401, 'Unauthorized')
                const user = verifyToken(token)
                return { user }
            }
        }
    })

// index.ts
import { authPlugin } from './plugins/auth'

new Elysia()
    .use(authPlugin)
    .get('/me', ({ user }) => user, { requireAuth: true })
    .listen(3000)
```

### Functional Plugin

```typescript
const counterPlugin = (app: Elysia) =>
    app
        .state('counter', 0)
        .get('/counter', ({ store }) => store.counter)
        .post('/counter', ({ store }) => ++store.counter)

new Elysia()
    .use(counterPlugin)
    .listen(3000)
```

### Configurable Plugin

```typescript
const rateLimiter = (options: { max: number; window: number }) => {
    const hits = new Map<string, number[]>()

    return new Elysia({ name: 'rate-limiter' })
        .onBeforeHandle(({ request, server }) => {
            const ip = server?.requestIP(request)?.address ?? 'unknown'
            const now = Date.now()
            const windowHits = (hits.get(ip) ?? [])
                .filter(t => t > now - options.window)

            if (windowHits.length >= options.max) {
                return status(429, 'Too many requests')
            }

            windowHits.push(now)
            hits.set(ip, windowHits)
        })
}

new Elysia()
    .use(rateLimiter({ max: 100, window: 60_000 }))
    .listen(3000)
```

### Prefixed Plugin

```typescript
const userRoutes = new Elysia({ prefix: '/users' })
    .get('/', () => db.users.findMany())          // GET /users
    .get('/:id', ({ params }) => db.users.find(params.id))  // GET /users/:id
    .post('/', ({ body }) => db.users.create(body))         // POST /users

new Elysia()
    .use(userRoutes)
    .listen(3000)
```

## Plugin Scoping

Elysia isolates lifecycle hooks by default. Three scope levels control propagation:

### Local Scope (Default)

Hooks only apply within the current instance and its direct descendants:

```typescript
const plugin = new Elysia()
    .onBeforeHandle(() => console.log('local hook'))
    .get('/plugin', () => 'hi')

new Elysia()
    .use(plugin)
    .get('/app', () => 'app')  // Local hook does NOT run here
```

### Scoped Scope

Hooks propagate to the parent, current instance, and descendants:

```typescript
const plugin = new Elysia()
    .onBeforeHandle({ as: 'scoped' }, () => console.log('scoped hook'))
    .get('/plugin', () => 'hi')

new Elysia()
    .use(plugin)
    .get('/app', () => 'app')  // Scoped hook DOES run here
```

### Global Scope

Hooks propagate to all instances in the tree:

```typescript
const plugin = new Elysia()
    .onBeforeHandle({ as: 'global' }, () => console.log('global hook'))

new Elysia()
    .use(plugin)
    .get('/anywhere', () => 'hi')  // Global hook runs here
```

### Instance-Level Scope Casting

Lift all hooks in a plugin to the parent scope using `.as()`:

```typescript
const middleware = new Elysia()
    .derive(() => ({ timestamp: Date.now() }))
    .onBeforeHandle(({ timestamp }) => {
        console.log(`Request at ${timestamp}`)
    })
    .as('scoped')  // All hooks become scoped

new Elysia()
    .use(middleware)
    .get('/', ({ timestamp }) => `Time: ${timestamp}`)  // Works
```

## Deduplication

By default, plugins execute every time they're applied. Use `name` (and optionally `seed`) for deduplication:

```typescript
const ipPlugin = new Elysia({ name: 'ip' })
    .derive({ as: 'global' }, ({ server, request }) => ({
        ip: server?.requestIP(request)?.address
    }))

// Both routers use ipPlugin, but it executes only once
const router1 = new Elysia().use(ipPlugin).get('/r1', ({ ip }) => ip)
const router2 = new Elysia().use(ipPlugin).get('/r2', ({ ip }) => ip)

new Elysia()
    .use(router1)
    .use(router2)
    .listen(3000)
```

### Seed for Parameterized Deduplication

```typescript
const logger = (level: string) =>
    new Elysia({ name: 'logger', seed: level })
        .onAfterResponse(() => console.log(`[${level}]`))

// These are two different plugin instances (different seeds)
app.use(logger('info'))
   .use(logger('debug'))
```

## Lazy Loading

### Dynamic Import

```typescript
new Elysia()
    .use(import('./plugins/heavy-plugin'))
    .listen(3000)
```

### Async Plugin

```typescript
const staticPlugin = async (app: Elysia) => {
    const files = await loadStaticAssets()
    files.forEach(f => app.get(`/static/${f}`, () => Bun.file(f)))
    return app
}

new Elysia()
    .use(staticPlugin)
    .listen(3000)
```

### Ensuring Module Registration in Tests

```typescript
const app = new Elysia().use(import('./plugins/api'))

// Wait for all deferred modules to register
await app.modules

const response = await app.handle(new Request('http://localhost/api'))
```

## Official Plugins

| Plugin | Package | Purpose |
|--------|---------|---------|
| **CORS** | `@elysia/cors` | Cross-origin resource sharing |
| **JWT** | `@elysia/jwt` | JSON Web Token auth |
| **Bearer** | `@elysia/bearer` | Bearer token extraction |
| **OpenAPI** | `@elysia/openapi` | API documentation |
| **Static** | `@elysia/static` | Serve static files |
| **Stream** | `@elysia/stream` | Streaming responses |
| **Eden** | `@elysia/eden` | Type-safe RPC client |
| **Server Timing** | `@elysia/server-timing` | Performance headers |
| **Tracing** | `@elysia/tracing` | OpenTelemetry integration |

Install: `bun add @elysia/<plugin-name>`

## Plugin Patterns

### Database Plugin

```typescript
const dbPlugin = new Elysia({ name: 'db' })
    .decorate('db', {
        users: new UserRepository(),
        posts: new PostRepository()
    })

app.use(dbPlugin)
   .get('/users', ({ db }) => db.users.findMany())
```

### Auth Middleware Plugin

```typescript
const auth = new Elysia({ name: 'auth' })
    .derive({ as: 'scoped' }, async ({ headers }) => {
        const token = headers.authorization?.replace('Bearer ', '')
        if (!token) return { user: null }
        return { user: await verifyJwt(token) }
    })

const requireAuth = new Elysia({ name: 'require-auth' })
    .use(auth)
    .onBeforeHandle({ as: 'scoped' }, ({ user }) => {
        if (!user) return status(401, 'Unauthorized')
    })
```

### Composing Plugins

```typescript
const app = new Elysia()
    .use(cors())
    .use(openapi())
    .use(dbPlugin)
    .use(authPlugin)
    .use(userRoutes)
    .use(postRoutes)
    .listen(3000)
```

## Common Pitfalls

1. **Forgetting `name` for deduplication** — Without a `name`, plugins re-execute every time they're `.use()`d. Always name plugins that register lifecycle hooks.

2. **Scope confusion** — Default scope is `local`. If a plugin's hooks don't work in the parent, add `as: 'scoped'` or `as: 'global'`.

3. **Type inference across files** — When splitting plugins across files, TypeScript needs the full Elysia type chain. Export the plugin instance directly, don't extract handlers separately.

4. **Plugin order matters** — Plugins are applied in order. A plugin using `derive` must be `.use()`d before routes that access the derived property.

5. **Deferred module testing** — When testing with dynamically imported plugins, `await app.modules` before calling `app.handle()` to ensure all routes are registered.
