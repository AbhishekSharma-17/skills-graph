# Fastify — Plugin System

> Source: [fastify.dev/docs/latest/Reference/Plugins](https://fastify.dev/docs/latest/Reference/Plugins/) and [fastify.dev/docs/latest/Reference/Encapsulation](https://fastify.dev/docs/latest/Reference/Encapsulation/)

## Table of Contents

- [Core Concept](#core-concept)
- [Creating Plugins](#creating-plugins)
- [Registering Plugins](#registering-plugins)
- [Encapsulation](#encapsulation)
- [Loading Order](#loading-order)
- [Nested Plugins](#nested-plugins)
- [Autoloading Plugins](#autoloading-plugins)
- [Common Pitfalls](#common-pitfalls)

## Core Concept

Everything in Fastify is a plugin. The `register` API loads plugins, routes, and middleware into the application. By default, each registration creates a new scope — changes to the Fastify instance (via `decorate`) do not affect parent or sibling contexts, only descendants.

This encapsulation model forms a directed acyclic graph (DAG) that prevents cross-plugin contamination.

## Creating Plugins

### Async Plugin (Recommended)

```javascript
// plugins/database.js
export default async function databasePlugin(fastify, opts) {
  const pool = await createPool(opts.connectionString)

  fastify.decorate('db', pool)

  fastify.addHook('onClose', async () => {
    await pool.end()
  })
}
```

### Callback Plugin

```javascript
function legacyPlugin(fastify, opts, done) {
  fastify.decorate('utility', () => 'helper')
  fastify.get('/health', async () => ({ status: 'ok' }))
  done()
}
module.exports = legacyPlugin
```

### Plugin Parameters

Every plugin receives three arguments:

| Parameter | Description |
|-----------|-------------|
| `fastify` | Scoped Fastify instance for this plugin |
| `opts` | Options passed during `register()` |
| `done` | Callback to signal completion (callback style only) |

## Registering Plugins

```javascript
import Fastify from 'fastify'
import dbPlugin from './plugins/database.js'
import userRoutes from './routes/users.js'

const app = Fastify({ logger: true })

// Register plugins
app.register(dbPlugin, { connectionString: 'postgres://...' })
app.register(userRoutes, { prefix: '/api/users' })

await app.listen({ port: 3000 })
```

### Registration Options

| Option | Description |
|--------|-------------|
| `prefix` | Prefix all routes in the plugin |
| `logLevel` | Custom log level for routes in this plugin |
| `logSerializers` | Custom log serializers |
| Any custom key | Passed to the plugin as `opts` |

### Dynamic Options

Options can be a function that receives the parent Fastify instance:

```javascript
app.register(myPlugin, (parent) => ({
  connectionString: parent.config.dbUrl
}))
```

## Encapsulation

### Default Behavior: Scoped

By default, plugins create isolated scopes:

```javascript
const app = Fastify()

app.decorate('shared', 'visible everywhere')

app.register(async function pluginA(instance) {
  instance.decorate('onlyInA', 'isolated')
  // Can access: shared, onlyInA
})

app.register(async function pluginB(instance) {
  // Can access: shared
  // CANNOT access: onlyInA (sibling scope)
})
```

### Visibility Rules

- **Parent → child:** children inherit everything from parent
- **Child → parent:** parent cannot access child decorators/hooks
- **Sibling → sibling:** siblings cannot access each other

### Breaking Encapsulation with fastify-plugin

Use `fastify-plugin` to make a plugin's decorations, hooks, and schemas visible to the parent scope:

```javascript
import fp from 'fastify-plugin'

async function dbPlugin(fastify, opts) {
  const db = await connectToDb(opts.url)
  fastify.decorate('db', db)
}

// Without fp: db is only visible inside this plugin and children
// With fp: db is visible to the parent (and siblings registered after)
export default fp(dbPlugin)
```

### When to Use fastify-plugin

| Scenario | Use fp? |
|----------|---------|
| Shared utility (database, cache, auth) | Yes — needs to be visible everywhere |
| Route plugin (API endpoints) | No — routes should be scoped |
| Plugin that only adds hooks | Depends — use fp if hooks should apply globally |

### Route Prefixing and fastify-plugin

Route prefixing (`{ prefix: '/api' }`) only applies to non-fp-wrapped plugins. Plugins wrapped with `fp` do NOT get prefixed — their routes register at whatever path they define.

## Loading Order

Plugins load sequentially in registration order:

```javascript
app.register(pluginA)  // loads first
app.register(pluginB)  // loads after pluginA completes
app.register(pluginC)  // loads after pluginB completes
```

Plugin initialization begins when you call `listen()`, `inject()`, or `ready()`.

### Ensuring Load Completion

```javascript
await app.register(dbPlugin)
await app.after()  // ensures dbPlugin is fully loaded

// Now safe to use app.db
app.register(async function routes(instance) {
  instance.get('/', async () => {
    return instance.db.query('SELECT 1')
  })
})
```

## Nested Plugins

Plugins can register sub-plugins, creating a hierarchy:

```javascript
async function apiPlugin(fastify) {
  // Shared auth hook for all routes in this plugin
  fastify.addHook('preHandler', async (request, reply) => {
    await verifyApiKey(request)
  })

  // Sub-plugins inherit the auth hook
  fastify.register(userRoutes, { prefix: '/users' })
  fastify.register(postRoutes, { prefix: '/posts' })
  fastify.register(commentRoutes, { prefix: '/comments' })
}

app.register(apiPlugin, { prefix: '/api/v1' })
// Creates: /api/v1/users, /api/v1/posts, /api/v1/comments
// All protected by the auth hook
```

## ESM Plugin Pattern

```javascript
// plugin.mjs
async function myPlugin(fastify, opts) {
  fastify.get('/', async () => ({ hello: 'world' }))
}
export default myPlugin

// app.mjs
import Fastify from 'fastify'
const app = Fastify()
app.register(import('./plugin.mjs'))
await app.listen({ port: 3000 })
```

## Error Handling

Errors during plugin loading are caught by the `after()` or `ready()` handlers:

```javascript
app.register(myPlugin)
app.after((err) => {
  if (err) console.error('Plugin failed:', err)
})

// Or at startup
app.ready((err) => {
  if (err) {
    console.error('App failed to start:', err)
    process.exit(1)
  }
})
```

## Plugin Timeout

Plugins must complete within `pluginTimeout` (default: 10,000ms). If a plugin takes longer, Fastify throws an error:

```javascript
const app = Fastify({
  pluginTimeout: 30000  // 30 seconds
})
```

## Autoloading Plugins

Use `@fastify/autoload` to automatically load plugins from a directory:

```javascript
import autoload from '@fastify/autoload'
import { join } from 'node:path'

app.register(autoload, {
  dir: join(import.meta.dirname, 'plugins')
})

app.register(autoload, {
  dir: join(import.meta.dirname, 'routes'),
  options: { prefix: '/api' }
})
```

Directory structure maps to route prefixes:

```
routes/
├── users/
│   ├── index.js    → /api/users
│   └── hooks.js    → auto-loaded hooks for /api/users
├── posts/
│   └── index.js    → /api/posts
└── root.js         → /api
```

## Real-World Plugin Structure

```javascript
// plugins/auth.js — shared (use fp)
import fp from 'fastify-plugin'

export default fp(async function auth(fastify) {
  fastify.decorate('authenticate', async (request, reply) => {
    const token = request.headers.authorization?.replace('Bearer ', '')
    if (!token) {
      reply.code(401).send({ error: 'Missing token' })
      return reply
    }
    request.user = await verifyJwt(token)
  })
})

// routes/users.js — scoped (no fp)
export default async function userRoutes(fastify) {
  fastify.addHook('preHandler', fastify.authenticate)

  fastify.get('/', async (request) => {
    return fastify.db.query('SELECT * FROM users WHERE org = $1', [request.user.orgId])
  })

  fastify.post('/', {
    schema: {
      body: { $ref: 'CreateUser' }
    }
  }, async (request) => {
    return fastify.db.query('INSERT INTO users ...', [request.body])
  })
}
```

## Common Pitfalls

1. **Accessing decorators before they're loaded** — `register()` is async; decorators from plugins aren't available until after `after()` or `ready()`
2. **Mixing callback and promise** — Fastify v5 requires choosing one pattern per plugin; don't call `done()` in an async plugin
3. **Forgetting fastify-plugin for shared state** — without `fp`, decorators are invisible to parent/sibling scopes
4. **Plugin timeout** — slow database connections or external service calls can exceed the default 10s timeout; increase `pluginTimeout` for slow startups
5. **Route prefix with fp** — plugins wrapped in `fastify-plugin` ignore the `prefix` option; define the full path in your routes instead
