# ElysiaJS — Overview & Getting Started

> Source: [elysiajs.com](https://elysiajs.com/) · Version 1.4.x · MIT License

## Table of Contents

- [What Is ElysiaJS](#what-is-elysiajs)
- [Key Features](#key-features)
- [Installation](#installation)
- [First Server](#first-server)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [TypeScript Setup](#typescript-setup)
- [Development Workflow](#development-workflow)
- [When to Use ElysiaJS](#when-to-use-elysiajs)
- [Comparison with Alternatives](#comparison-with-alternatives)
- [Common Pitfalls](#common-pitfalls)

---

## What Is ElysiaJS

ElysiaJS is a TypeScript web framework designed primarily for Bun, offering end-to-end type safety and exceptional performance. It uses static code analysis and ahead-of-time compilation to match the performance of Go and Rust frameworks while maintaining an ergonomic TypeScript API.

Core philosophy:
- **Type-safe by default** — types flow from server to client without code generation
- **Performance-first** — 500K+ req/s via Bun's native HTTP and static analysis
- **Ergonomic** — chainable API, minimal boilerplate, convention over configuration
- **WinterTC-compliant** — uses Web Standard Request/Response, portable across runtimes

## Key Features

| Feature | Description |
|---------|-------------|
| **End-to-end type safety** | TypeScript types flow from route schemas to Eden client |
| **Schema validation** | Runtime + compile-time validation via TypeBox or Standard Schema |
| **OpenAPI generation** | Auto-generate docs from type definitions, no annotations |
| **Eden RPC client** | tRPC-like client with <2KB footprint, no codegen |
| **Plugin system** | Composable instances with scoped lifecycle hooks |
| **WebSocket** | First-class WS support with schema validation |
| **Multi-runtime** | Bun (primary), Node.js, Deno, Cloudflare Workers |
| **WinterTC mount** | Compose with Hono, Nitro, Next.js via `.mount()` |

## Installation

### New Project (Recommended)

```bash
# Install Bun (macOS / Linux)
curl -fsSL https://bun.sh/install | bash

# Create ElysiaJS project
bun create elysia app
cd app

# Start dev server with hot reload
bun dev
```

### Add to Existing Project

```bash
bun add elysia

# Common plugins
bun add @elysia/openapi     # OpenAPI / Scalar UI
bun add @elysia/eden         # Type-safe client
bun add @elysia/cors         # CORS middleware
bun add @elysia/jwt          # JWT authentication
bun add @elysia/bearer       # Bearer token extraction
bun add @elysia/static       # Static file serving
```

### Node.js Support

```bash
npm install elysia @elysiajs/node
```

```typescript
import { Elysia } from 'elysia'
import { node } from '@elysiajs/node'

new Elysia({ adapter: node() })
    .get('/', () => 'Hello from Node.js')
    .listen(3000)
```

## First Server

```typescript
import { Elysia } from 'elysia'

const app = new Elysia()
    .get('/', () => 'Hello Elysia')
    .get('/user/:id', ({ params: { id } }) => `User ${id}`)
    .post('/json', ({ body }) => body)
    .listen(3000)

console.log(`Running at ${app.server?.url}`)
```

Every route definition chains on the Elysia instance, returning the same instance for further chaining. Inline literal values (strings, numbers, objects) are optimized via ahead-of-time compilation for maximum performance.

## Project Structure

```
app/
├── src/
│   ├── index.ts            # Entry point, main Elysia instance
│   ├── routes/
│   │   ├── users.ts        # User routes plugin
│   │   └── posts.ts        # Post routes plugin
│   ├── plugins/
│   │   ├── auth.ts         # Auth plugin (derive/resolve)
│   │   └── db.ts           # Database plugin (decorate)
│   └── models/
│       └── schemas.ts      # Shared validation schemas
├── test/
│   └── index.test.ts       # Tests using bun:test
├── package.json
├── tsconfig.json
└── bunfig.toml
```

### Plugin-Based Module Pattern

```typescript
// src/routes/users.ts
import { Elysia, t } from 'elysia'

export const users = new Elysia({ prefix: '/users' })
    .get('/', () => db.users.findMany())
    .get('/:id', ({ params: { id } }) => db.users.findById(id))
    .post('/', ({ body }) => db.users.create(body), {
        body: t.Object({
            name: t.String(),
            email: t.String({ format: 'email' })
        })
    })

// src/index.ts
import { Elysia } from 'elysia'
import { users } from './routes/users'

new Elysia()
    .use(users)
    .listen(3000)
```

## Configuration

### Constructor Options

```typescript
new Elysia({
    prefix: '/api',          // URL prefix for all routes
    name: 'my-plugin',       // Plugin deduplication key
    seed: undefined,         // Additional dedup seed
    tags: ['api'],           // OpenAPI tags for all routes
    aot: true,               // Ahead-of-time compilation (default: true)
    cookie: {                // Global cookie config
        secrets: 'my-secret',
        sign: ['session']
    }
})
```

### Serve Options

```typescript
.listen({
    port: 3000,              // Default: 3000
    hostname: '0.0.0.0',     // Bind address
    tls: {                   // HTTPS
        cert: Bun.file('cert.pem'),
        key: Bun.file('key.pem')
    },
    development: true        // Enable dev features
})
```

## TypeScript Setup

```json
// tsconfig.json
{
    "compilerOptions": {
        "target": "ES2021",
        "module": "ESNext",
        "moduleResolution": "bundler",
        "strict": true,
        "esModuleInterop": true,
        "skipLibCheck": true,
        "types": ["bun-types"]
    }
}
```

## Development Workflow

```bash
# Development with hot reload
bun dev

# Run production
bun run src/index.ts

# Run tests
bun test

# Build for production (optional)
bun build src/index.ts --outdir ./dist --target bun
```

## When to Use ElysiaJS

**Good fit:**
- Bun-native APIs and microservices
- Type-safe REST/RPC APIs where server and client share types
- High-throughput HTTP services (benchmarks, real-time)
- Next.js API route replacement (via WinterTC)
- Projects already using Bun as their runtime

**Consider alternatives when:**
- Multi-runtime is critical from day one (prefer Hono)
- Enterprise ecosystem with mature middleware needed (prefer NestJS/Express)
- Python/Go/Rust is the team language

## Comparison with Alternatives

| Framework | Runtime | Type Safety | RPC Client | Performance |
|-----------|---------|-------------|------------|-------------|
| **ElysiaJS** | Bun (primary) | End-to-end | Eden | ~500K req/s |
| **Hono** | Multi-runtime | Partial | hc client | ~200K req/s |
| **Express** | Node.js | Manual | None | ~30K req/s |
| **Fastify** | Node.js | Via schemas | None | ~70K req/s |
| **NestJS** | Node.js | Decorator | None | ~40K req/s |

## Common Pitfalls

1. **Hook ordering matters** — Lifecycle hooks only apply to routes registered *after* the hook. Place hooks before route definitions.

2. **Plugin scope isolation** — Hooks are `local` by default. Use `as: 'global'` or `as: 'scoped'` to propagate hooks to parent instances.

3. **Inline values are fastest** — Returning a literal string or object enables AOT optimization. Function wrappers are still fast but skip this optimization path.

4. **Eden needs type export** — Export `typeof app` from the server; Eden uses this at compile time only, never imports runtime code.

5. **Bun is required for peak performance** — Node.js adapter works but won't reach Bun-level throughput. Use `@elysiajs/node` for Node compatibility.
