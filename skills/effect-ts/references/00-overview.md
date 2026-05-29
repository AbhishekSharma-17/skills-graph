# Effect — Overview & Setup

> Source: [effect.website/docs](https://effect.website/docs) | Package: `effect` v3.21.x

## What Is Effect

Effect is a production-grade TypeScript framework that provides a fully-fledged functional effect system with a rich standard library. It extends TypeScript's type system so that every error path, every dependency, and every async step is tracked and composed at the type level.

Used in production by Vercel, Prisma, and numerous fintech companies. The `effect` npm package has 12M+ weekly downloads and 10K+ GitHub stars.

## When to Use Effect

**Use Effect when:**
- You need type-safe error handling beyond try/catch
- Your application has complex dependency graphs (services, databases, caches)
- You need structured concurrency (parallel work, cancellation, timeouts)
- Data validation and transformation are core to your domain (APIs, ETL)
- You want a single framework covering errors, DI, concurrency, streams, and HTTP

**Don't use Effect when:**
- You have a simple script with minimal error paths
- Your team is unfamiliar with functional programming patterns and cannot invest in learning
- You only need schema validation (use Zod or Valibot instead)
- Performance overhead of the effect system is unacceptable for hot paths

## Core Types

### Effect<A, E, R>

The central abstraction. Describes a computation that:
- **Succeeds** with a value of type `A`
- **Fails** with a typed error `E`
- **Requires** services declared in `R` from the environment

```typescript
import { Effect } from "effect"

// Effect<string, Error, never> — succeeds with string, may fail with Error, no requirements
const program: Effect.Effect<string, Error, never> = Effect.tryPromise({
  try: () => fetch("/api/data").then(r => r.json()),
  catch: (e) => new Error(`Fetch failed: ${e}`)
})
```

### Key Type Aliases

```typescript
// No error, no requirements — always succeeds
type Effect<A> = Effect.Effect<A, never, never>

// Has error but no requirements
type Effect<A, E> = Effect.Effect<A, E, never>
```

## Installation

### New Project

```bash
# Create a new Effect project with recommended setup
npx create-effect-app@latest my-app
cd my-app
npm install
```

### Existing Project

```bash
# Core package (includes Schema since v3)
npm install effect

# Platform abstractions (HTTP, filesystem, etc.)
npm install @effect/platform @effect/platform-node

# Testing integration
npm install -D @effect/vitest

# Optional packages
npm install @effect/cli        # CLI applications
npm install @effect/sql        # SQL database access
npm install @effect/opentelemetry  # Observability
```

### TypeScript Configuration

Effect requires TypeScript 5.4+ with strict mode:

```json
{
  "compilerOptions": {
    "strict": true,
    "exactOptionalPropertyTypes": true,
    "moduleResolution": "bundler",
    "target": "ES2022",
    "module": "ES2022"
  }
}
```

## Project Structure

A typical Effect project follows this layout:

```
src/
├── index.ts           # Entry point — Effect.runPromise(program)
├── services/          # Service definitions (Tag + interface + Layer)
│   ├── Database.ts
│   ├── Logger.ts
│   └── Config.ts
├── domain/            # Domain models and schemas
│   ├── User.ts
│   └── Order.ts
├── routes/            # HTTP route handlers (if using @effect/platform)
│   ├── users.ts
│   └── orders.ts
└── lib/               # Shared utilities
    └── errors.ts      # Tagged error classes
```

## Hello World

```typescript
import { Effect, Console } from "effect"

const program = Effect.gen(function* () {
  yield* Console.log("Hello from Effect!")
  const result = yield* Effect.succeed(42)
  yield* Console.log(`The answer is ${result}`)
  return result
})

Effect.runPromise(program).then(console.log)
// Hello from Effect!
// The answer is 42
// 42
```

## Ecosystem Packages

| Package | Purpose |
|---------|---------|
| `effect` | Core: Effect, Schema, Stream, Layer, Config, and more |
| `@effect/platform` | Platform-independent HTTP, filesystem, workers |
| `@effect/platform-node` | Node.js runtime bindings |
| `@effect/platform-bun` | Bun runtime bindings |
| `@effect/platform-browser` | Browser runtime bindings |
| `@effect/sql` | SQL database access (Postgres, MySQL, SQLite) |
| `@effect/cli` | Type-safe CLI applications |
| `@effect/vitest` | Vitest testing integration |
| `@effect/opentelemetry` | OpenTelemetry tracing and metrics |
| `@effect/cluster` | Distributed systems primitives |
| `@effect/ai` | AI/LLM integration utilities |

## Key Concepts at a Glance

| Concept | Module | Purpose |
|---------|--------|---------|
| Effect | `Effect` | Core computation type, composition, execution |
| Schema | `Schema` | Validation, decoding, encoding, branded types |
| Layer | `Layer` | Service composition and dependency injection |
| Stream | `Stream` | Async event-driven data processing |
| Fiber | `Fiber` | Lightweight virtual threads for concurrency |
| Scope | `Scope` | Resource lifecycle management |
| Config | `Config` | Type-safe configuration loading |
| Context | `Context` | Service container and dependency resolution |
| Ref | `Ref` | Mutable references with safe concurrent access |
| Schedule | `Schedule` | Retry and repeat policies |

## Common Pitfalls

- **Effects are lazy**: `Effect.succeed(42)` doesn't run anything — it describes a computation. You must run it with `Effect.runPromise`, `Effect.runSync`, or similar.
- **Don't mix async/await with Effect.gen**: Inside `Effect.gen`, use `yield*` for effects, not `await` for promises. Wrap promises with `Effect.tryPromise`.
- **Type parameters matter**: `Effect<string, NetworkError, Database>` tells you exactly what this effect does, how it can fail, and what it needs. Read the types.
- **One `provide` at the edge**: Compose all layers and provide them once at your application entry point, not scattered throughout the codebase.
- **Schema is in core**: Since Effect v3, Schema is part of the `effect` package. You don't need `@effect/schema` separately (it re-exports from core).

## Related Topics

- Effect type deep dive → `01-effect-type.md`
- Error handling patterns → `02-error-handling.md`
- Dependency injection → `03-context-services.md` and `04-layers.md`
