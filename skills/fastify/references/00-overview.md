# Fastify — Overview & Getting Started

> Source: [fastify.dev/docs/latest/Guides/Getting-Started](https://fastify.dev/docs/latest/Guides/Getting-Started/)

## What Is Fastify?

Fastify is a high-performance, low-overhead web framework for Node.js. It focuses on developer experience with a powerful plugin system, schema-based request/response validation, and built-in logging via Pino. In benchmarks on Node.js v22 LTS, Fastify v5 handles approximately 78,500 requests per second compared to 32,400 for Express 5 — roughly 2.4x faster for JSON serialization workloads.

### Key Design Principles

- **Schema-first validation** — declare request and response schemas up front using JSON Schema. Fastify compiles highly optimized validation (Ajv) and serialization (fast-json-stringify) functions ahead of time
- **Encapsulated plugins** — every plugin runs in its own scope, forming a directed acyclic graph (DAG). Changes in a child plugin never leak to parent or sibling scopes unless explicitly exposed
- **Performance** — zero-cost abstractions, ahead-of-time compilation, radix-tree router (find-my-way)
- **Async-first** — native async/await support throughout the lifecycle
- **Extensible** — 50+ official plugins for auth, CORS, WebSocket, Swagger, databases, and more

### When to Choose Fastify

| Use Case | Why Fastify |
|----------|-------------|
| High-throughput APIs | 2-3x Express performance for JSON workloads |
| Microservices | Encapsulated plugins prevent cross-service contamination |
| Schema-validated endpoints | Built-in JSON Schema validation without extra libraries |
| TypeScript APIs | First-class type providers (TypeBox, json-schema-to-ts) |
| Production logging | Pino gives structured JSON logs out of the box |

### When Express or Another Framework May Fit Better

- You need the vast Express middleware ecosystem with minimal rewriting
- Your team is deeply invested in a decorator/DI pattern (consider NestJS)
- You run on Bun and want native Bun APIs (consider Elysia or Hono)

## Installation

```bash
# npm
npm i fastify

# yarn
yarn add fastify

# pnpm
pnpm add fastify
```

**Requirements:** Node.js v20 or later (Fastify v5 dropped support for earlier versions).

### Project Setup with TypeScript

```bash
mkdir my-api && cd my-api
npm init -y
npm i fastify
npm i -D typescript @types/node
npx tsc --init
```

Set `"target": "ES2022"` and `"module": "NodeNext"` in `tsconfig.json`.

### CLI Scaffolding

```bash
npm i -g fastify-cli
fastify generate my-project --lang=ts
cd my-project
npm i
npm run dev
```

## Your First Server

### ESM (recommended)

```javascript
import Fastify from 'fastify'

const fastify = Fastify({ logger: true })

fastify.get('/', async (request, reply) => {
  return { hello: 'world' }
})

try {
  await fastify.listen({ port: 3000 })
} catch (err) {
  fastify.log.error(err)
  process.exit(1)
}
```

### CommonJS

```javascript
const fastify = require('fastify')({ logger: true })

fastify.get('/', function (request, reply) {
  reply.send({ hello: 'world' })
})

fastify.listen({ port: 3000 }, function (err, address) {
  if (err) {
    fastify.log.error(err)
    process.exit(1)
  }
})
```

### Key Notes

- **ESM projects** — include `"type": "module"` in `package.json`
- **Default bind** — `listen()` binds to `127.0.0.1` (localhost only)
- **All interfaces** — use `host: '0.0.0.0'` for IPv4 or `host: '::'` for IPv6
- **Docker** — always use `0.0.0.0` so the container port is reachable

## Application Structure

Fastify recommends separating application setup from server startup:

```javascript
// app.js — build the application
import Fastify from 'fastify'
import routes from './routes.js'

export function buildApp(opts = {}) {
  const app = Fastify(opts)
  app.register(routes)
  return app
}
```

```javascript
// server.js — start listening
import { buildApp } from './app.js'

const app = buildApp({ logger: true })
await app.listen({ port: 3000 })
```

This pattern enables testing via `inject()` without starting a server.

## Plugin Loading Order

Fastify loads plugins sequentially via `register()`. The recommended structure:

```
└── ecosystem plugins (@fastify/cors, @fastify/helmet)
└── custom shared plugins (database connectors, utilities)
└── decorators
└── hooks
└── route plugins (your API routes)
```

Plugin initialization begins when you call `fastify.listen()`, `fastify.inject()`, or `fastify.ready()`.

## Request Lifecycle

```
Incoming Request
  │
  └─▶ Routing
       │
       ├─▶ onRequest hooks
       │
       ├─▶ preParsing hooks
       │
       ├─▶ Body Parsing
       │
       ├─▶ preValidation hooks
       │
       ├─▶ Schema Validation
       │
       ├─▶ preHandler hooks
       │
       ├─▶ Route Handler
       │
       ├─▶ preSerialization hooks
       │
       ├─▶ onSend hooks
       │
       ├─▶ Response Sent
       │
       └─▶ onResponse hooks
```

## Core API at a Glance

| API | Purpose |
|-----|---------|
| `fastify.register(plugin, opts)` | Load a plugin |
| `fastify.get/post/put/delete/patch(url, opts, handler)` | Define routes |
| `fastify.addHook(name, fn)` | Attach lifecycle hooks |
| `fastify.decorate(name, value)` | Extend the Fastify instance |
| `fastify.decorateRequest(name, value)` | Extend Request objects |
| `fastify.decorateReply(name, value)` | Extend Reply objects |
| `fastify.setErrorHandler(fn)` | Custom error handling |
| `fastify.addSchema(schema)` | Register shared JSON Schemas |
| `fastify.inject(opts)` | HTTP injection for testing |
| `fastify.listen({ port })` | Start accepting connections |
| `fastify.close()` | Graceful shutdown |

## Comparison with Express

| Feature | Express 5 | Fastify 5 |
|---------|-----------|-----------|
| Throughput (JSON) | ~32K req/s | ~78K req/s |
| Validation | Manual (joi, zod) | Built-in JSON Schema |
| Serialization | JSON.stringify | fast-json-stringify (2-3x faster) |
| Logging | Manual (morgan) | Built-in Pino (structured JSON) |
| Plugin scoping | Global middleware | Encapsulated DAG |
| TypeScript | Community types | Official type providers |
| Async errors | Manual try/catch | Automatic async error catching |

## Common Pitfalls

1. **Forgetting `return reply`** — in async handlers that call `reply.send()`, you must `return reply` to avoid double-send
2. **Arrow functions in hooks** — arrow functions break `this` binding to the Fastify instance; use regular functions when you need `this`
3. **Listening on localhost in Docker** — the default bind address is `127.0.0.1`, which is unreachable from outside the container
4. **Plugin loading order** — plugins load sequentially; a plugin cannot access decorators from plugins registered after it
5. **Reference type decorators** — decorating Request/Reply with objects or arrays shares state across requests; use hooks for per-request initialization
