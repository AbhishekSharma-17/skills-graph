# Layers

> Source: [effect.website/docs](https://effect.website/docs/requirements-management/layers/) | Package: `effect` v3.21.x

## Table of Contents

- [What Are Layers](#what-are-layers)
- [Creating Layers](#creating-layers)
- [Composing Layers](#composing-layers)
- [Providing Layers](#providing-layers)
- [Layer Sharing and Memoization](#layer-sharing-and-memoization)
- [Scoped Layers (Resource Management)](#scoped-layers-resource-management)
- [Application Wiring Pattern](#application-wiring-pattern)
- [Common Pitfalls](#common-pitfalls)

## What Are Layers

Layers are the idiomatic way to construct and compose service implementations in Effect. A `Layer<ROut, E, RIn>` describes how to build services of type `ROut`, potentially failing with error `E`, given input services `RIn`.

```typescript
// Layer<Database, DbError, Config>
// "I can build a Database if you give me Config. Construction might fail with DbError."
```

Layers solve the "dependency graph" problem: if ServiceA needs ServiceB which needs ServiceC, layers compose these automatically.

## Creating Layers

### Layer.succeed — Synchronous, no dependencies

```typescript
import { Layer } from "effect"

const LoggerLive = Layer.succeed(Logger, {
  info: (msg: string) => Effect.log(msg),
  error: (msg: string) => Effect.logError(msg)
})
// Layer<Logger, never, never>
```

### Layer.sync — Lazy synchronous

```typescript
const ClockLive = Layer.sync(Clock, () => ({
  now: () => Date.now(),
  timestamp: () => new Date().toISOString()
}))
```

### Layer.effect — Effectful construction

```typescript
const DatabaseLive = Layer.effect(
  Database,
  Effect.gen(function* () {
    const config = yield* AppConfig
    const pool = createPool(config.dbUrl)
    return {
      query: (sql: string, params: unknown[]) =>
        Effect.tryPromise({
          try: () => pool.query(sql, params),
          catch: (e) => new DbError({ query: sql, cause: e })
        })
    }
  })
)
// Layer<Database, never, AppConfig>
```

### Layer.scoped — With resource management

```typescript
const PoolLive = Layer.scoped(
  ConnectionPool,
  Effect.gen(function* () {
    const config = yield* AppConfig
    const pool = yield* Effect.acquireRelease(
      Effect.sync(() => createPool(config.dbUrl, { max: 20 })),
      (pool) => Effect.promise(() => pool.end())
    )
    return { pool }
  })
)
// Layer<ConnectionPool, never, AppConfig>
// Pool is closed when the scope ends
```

### Layer.function — From a function

```typescript
const HasherLive = Layer.function(Hasher, (config: Config) => ({
  hash: (data: string) => Effect.sync(() => crypto.hash(config.algorithm, data))
}))
```

### From Effect.Service

When you define services with `Effect.Service`, the layer is generated automatically:

```typescript
class Database extends Effect.Service<Database>()("app/Database", {
  effect: Effect.gen(function* () {
    // ... build the service
  }),
  dependencies: [ConfigLive]
}) {}

// Use the auto-generated layer:
Database.Default  // Layer<Database, never, never> (dependencies are wired in)
```

## Composing Layers

### Layer.provide — Feed dependencies

```typescript
// DatabaseLive needs AppConfig → wire AppConfig into it
const DatabaseWithConfig = DatabaseLive.pipe(
  Layer.provide(AppConfigLive)
)
// Layer<Database, never, never> — no more requirements
```

### Layer.merge — Combine independent layers

```typescript
const AppLayer = Layer.merge(DatabaseLive, LoggerLive)
// Layer<Database | Logger, never, AppConfig>
```

### Layer.mergeAll — Combine many layers

```typescript
const AppLayer = Layer.mergeAll(
  DatabaseLive,
  LoggerLive,
  CacheLive,
  AuthLive
)
```

### Layer.provideMerge — Provide and expose

```typescript
// Provide Config to Database, expose both Config and Database
const layer = Layer.provideMerge(AppConfigLive, DatabaseLive)
// Layer<AppConfig | Database, never, never>
```

### Complex Dependency Graphs

```typescript
//   AppConfig
//     ├─→ Database ─→ UserRepo
//     └─→ Redis ─────→ Cache
//                       └─→ UserService (needs UserRepo + Cache)

const AppConfigLive = Layer.succeed(AppConfig, { dbUrl: "...", redisUrl: "..." })

const DatabaseLive = Layer.effect(Database,
  Effect.gen(function* () {
    const config = yield* AppConfig
    return createDb(config.dbUrl)
  })
)

const RedisLive = Layer.effect(Redis,
  Effect.gen(function* () {
    const config = yield* AppConfig
    return createRedis(config.redisUrl)
  })
)

const UserRepoLive = Layer.effect(UserRepo,
  Effect.gen(function* () {
    const db = yield* Database
    return { findById: (id) => db.query("...", [id]) }
  })
)

const CacheLive = Layer.effect(Cache,
  Effect.gen(function* () {
    const redis = yield* Redis
    return { get: (k) => redis.get(k), set: (k, v) => redis.set(k, v) }
  })
)

const UserServiceLive = Layer.effect(UserService,
  Effect.gen(function* () {
    const repo = yield* UserRepo
    const cache = yield* Cache
    return {
      getUser: (id: string) =>
        cache.get(id).pipe(
          Effect.flatMap(Option.match({
            onSome: Effect.succeed,
            onNone: () => repo.findById(id).pipe(
              Effect.tap((user) => cache.set(id, JSON.stringify(user)))
            )
          }))
        )
    }
  })
)

// Wire everything together
const AppLayer = UserServiceLive.pipe(
  Layer.provide(UserRepoLive),
  Layer.provide(CacheLive),
  Layer.provide(DatabaseLive),
  Layer.provide(RedisLive),
  Layer.provide(AppConfigLive)
)
// Layer<UserService, never, never> — fully resolved
```

## Providing Layers

### At the entry point

```typescript
import { Effect, ManagedRuntime } from "effect"

// Option 1: Effect.provide
const main = myProgram.pipe(Effect.provide(AppLayer))
Effect.runPromise(main)

// Option 2: ManagedRuntime (recommended for apps)
const runtime = ManagedRuntime.make(AppLayer)
await runtime.runPromise(myProgram)
await runtime.dispose() // clean up scoped resources
```

### In tests

```typescript
const TestLayer = Layer.mergeAll(
  MockDatabaseLive,
  MockCacheLive,
  LoggerLive
)

const program = myEffect.pipe(Effect.provide(TestLayer))
```

## Layer Sharing and Memoization

By default, layers are shared (memoized). If the same layer appears multiple times in the dependency graph, it is only constructed once:

```typescript
//   Database ─→ UserRepo
//   Database ─→ OrderRepo

// Database layer is constructed ONCE, not twice
const AppLayer = Layer.mergeAll(
  UserRepoLive,
  OrderRepoLive
).pipe(Layer.provide(DatabaseLive))
```

### Opting out of sharing

```typescript
// Fresh layer — constructed each time it's used
const FreshDatabase = Layer.fresh(DatabaseLive)
```

## Scoped Layers (Resource Management)

Scoped layers acquire resources on construction and release them when the scope ends:

```typescript
const HttpServerLive = Layer.scoped(
  HttpServer,
  Effect.gen(function* () {
    const config = yield* AppConfig
    const server = yield* Effect.acquireRelease(
      Effect.sync(() => http.createServer().listen(config.port)),
      (server) => Effect.sync(() => server.close())
    )
    yield* Effect.log(`Server listening on port ${config.port}`)
    return { server }
  })
)
```

When using `ManagedRuntime`, calling `dispose()` closes all scoped resources in reverse order.

## Application Wiring Pattern

The recommended structure for a production application:

```typescript
// src/services/Config.ts
class AppConfig extends Effect.Service<AppConfig>()("app/Config", {
  effect: Effect.gen(function* () {
    const port = yield* Config.number("PORT").pipe(Config.withDefault(3000))
    const dbUrl = yield* Config.string("DATABASE_URL")
    return { port, dbUrl }
  })
}) {}

// src/services/Database.ts
class Database extends Effect.Service<Database>()("app/Database", {
  scoped: Effect.gen(function* () {
    const config = yield* AppConfig
    const pool = yield* Effect.acquireRelease(
      Effect.sync(() => createPool(config.dbUrl)),
      (p) => Effect.promise(() => p.end())
    )
    return { query: (sql: string) => Effect.tryPromise(() => pool.query(sql)) }
  }),
  dependencies: [AppConfig.Default]
}) {}

// src/services/UserRepo.ts
class UserRepo extends Effect.Service<UserRepo>()("app/UserRepo", {
  effect: Effect.gen(function* () {
    const db = yield* Database
    return {
      findById: (id: string) => db.query(`SELECT * FROM users WHERE id = '${id}'`)
    }
  }),
  dependencies: [Database.Default]
}) {}

// src/index.ts — the ONLY place with Effect.provide
const main = myProgram.pipe(Effect.provide(UserRepo.Default))
Effect.runPromise(main)
```

## Common Pitfalls

- **Don't provide the same service twice**: The last `provideService` wins silently. Use layer composition to avoid conflicts.
- **Don't create layers inside effects**: Layers should be module-level constants. Creating them dynamically defeats memoization.
- **Don't forget scoped cleanup**: If a layer acquires a resource (connection, file handle), use `Layer.scoped` with `acquireRelease` to ensure cleanup.
- **Layer construction errors**: If a layer's `effect` fails, the error propagates to `Effect.runPromise`. Handle it there or provide a fallback layer.

## Related Topics

- Defining services → `03-context-services.md`
- Resource management → `09-resource-management.md`
- Testing with layers → `11-testing.md`
