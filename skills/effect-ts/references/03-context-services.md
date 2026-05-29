# Context & Services

> Source: [effect.website/docs](https://effect.website/docs/requirements-management/services/) | Package: `effect` v3.21.x

## Table of Contents

- [What Are Services](#what-are-services)
- [Defining Services with Effect.Service](#defining-services-with-effectservice)
- [Using Services in Effects](#using-services-in-effects)
- [Context.Tag — Manual Service Tags](#contexttag--manual-service-tags)
- [Providing Services](#providing-services)
- [Service Patterns](#service-patterns)
- [Common Pitfalls](#common-pitfalls)

## What Are Services

Services are the dependency injection mechanism in Effect. Instead of importing concrete implementations directly, your effects declare what services they need through the `R` (Requirements) type parameter.

```typescript
// Without services — tightly coupled
const getUser = (id: string) => {
  const db = new PostgresClient(process.env.DB_URL!) // hardcoded
  return db.query("SELECT * FROM users WHERE id = $1", [id])
}

// With services — the Effect tracks the dependency in its type
const getUser = (id: string): Effect.Effect<User, DbError, Database> => ...
//                                                          ^^^^^^^^
//                                                 compiler tracks this
```

## Defining Services with Effect.Service

The recommended way to define services since Effect v3:

```typescript
import { Effect, Context } from "effect"

// Define a service with its interface
class Database extends Effect.Service<Database>()("app/Database", {
  effect: Effect.gen(function* () {
    const pool = yield* Effect.tryPromise(() => createPool(config))
    return {
      query: (sql: string, params: unknown[]) =>
        Effect.tryPromise({
          try: () => pool.query(sql, params),
          catch: (e) => new DbError({ query: sql, cause: e })
        }),
      transaction: <A, E, R>(effect: Effect.Effect<A, E, R>) =>
        Effect.scoped(
          Effect.acquireRelease(
            Effect.tryPromise(() => pool.getConnection()),
            (conn) => Effect.sync(() => conn.release())
          ).pipe(Effect.flatMap(() => effect))
        )
    }
  }),
  dependencies: [ConfigLive]
}) {}

// The class IS both the tag and the layer
// Database (tag) — used in Effect.gen with yield*
// Database.Default (layer) — provided to Effect.provide
```

### Simpler Services

```typescript
class Logger extends Effect.Service<Logger>()("app/Logger", {
  succeed: {
    info: (msg: string) => Effect.log(msg),
    error: (msg: string, cause?: unknown) => Effect.logError(msg, cause),
    debug: (msg: string) => Effect.logDebug(msg)
  }
}) {}

class Clock extends Effect.Service<Clock>()("app/Clock", {
  sync: {
    now: () => Date.now(),
    timestamp: () => new Date().toISOString()
  }
}) {}
```

## Using Services in Effects

```typescript
const getUser = (id: string) =>
  Effect.gen(function* () {
    const db = yield* Database
    const logger = yield* Logger

    yield* logger.info(`Fetching user ${id}`)
    const result = yield* db.query("SELECT * FROM users WHERE id = $1", [id])

    if (result.rows.length === 0) {
      return yield* Effect.fail(new NotFoundError({ entity: "User", id }))
    }

    return result.rows[0] as User
  })
// Effect<User, NotFoundError | DbError, Database | Logger>
//                                        ^^^^^^^^^^^^^^^^
//                                  requirements tracked automatically
```

## Context.Tag — Manual Service Tags

For more control or simpler cases:

```typescript
import { Context, Effect } from "effect"

// Define an interface
interface HttpClient {
  readonly get: (url: string) => Effect.Effect<Response, HttpError>
  readonly post: (url: string, body: unknown) => Effect.Effect<Response, HttpError>
}

// Create a tag
const HttpClient = Context.GenericTag<HttpClient>("app/HttpClient")

// Use the tag in effects
const fetchData = Effect.gen(function* () {
  const http = yield* HttpClient
  return yield* http.get("https://api.example.com/data")
})
// Effect<Response, HttpError, HttpClient>

// Provide an implementation inline
const program = fetchData.pipe(
  Effect.provideService(HttpClient, {
    get: (url) => Effect.tryPromise({
      try: () => fetch(url),
      catch: (e) => new HttpError({ url, cause: e })
    }),
    post: (url, body) => Effect.tryPromise({
      try: () => fetch(url, { method: "POST", body: JSON.stringify(body) }),
      catch: (e) => new HttpError({ url, cause: e })
    })
  })
)
```

## Providing Services

### Effect.provideService — Single service

```typescript
const program = myEffect.pipe(
  Effect.provideService(Logger, consoleLogger)
)
```

### Effect.provide — Layer-based (recommended)

```typescript
const program = myEffect.pipe(
  Effect.provide(Layer.mergeAll(
    Database.Default,
    Logger.Default,
    ConfigLive
  ))
)
```

### Effect.provideServiceEffect — Effectful creation

```typescript
const program = myEffect.pipe(
  Effect.provideServiceEffect(
    Database,
    Effect.gen(function* () {
      const config = yield* Config
      return createDatabaseClient(config.dbUrl)
    })
  )
)
```

## Service Patterns

### Service with Configuration

```typescript
class ApiClient extends Effect.Service<ApiClient>()("app/ApiClient", {
  effect: Effect.gen(function* () {
    const config = yield* AppConfig
    const baseUrl = config.apiBaseUrl
    const apiKey = config.apiKey

    return {
      get: (path: string) =>
        Effect.tryPromise({
          try: () => fetch(`${baseUrl}${path}`, {
            headers: { Authorization: `Bearer ${apiKey}` }
          }),
          catch: (e) => new ApiError({ path, cause: e })
        })
    }
  }),
  dependencies: [AppConfig.Default]
}) {}
```

### Service with Resource Management

```typescript
class ConnectionPool extends Effect.Service<ConnectionPool>()("app/ConnectionPool", {
  scoped: Effect.gen(function* () {
    const config = yield* AppConfig
    const pool = yield* Effect.acquireRelease(
      Effect.sync(() => createPool(config.dbUrl, { max: 20 })),
      (pool) => Effect.promise(() => pool.end())
    )
    return {
      getConnection: () => Effect.tryPromise(() => pool.connect()),
      query: (sql: string) => Effect.tryPromise({
        try: () => pool.query(sql),
        catch: (e) => new DbError({ query: sql, cause: e })
      })
    }
  }),
  dependencies: [AppConfig.Default]
}) {}
```

### Service with Multiple Implementations

```typescript
// Interface
class Cache extends Context.Tag("app/Cache")<Cache, {
  readonly get: (key: string) => Effect.Effect<Option.Option<string>>
  readonly set: (key: string, value: string, ttl?: number) => Effect.Effect<void>
  readonly del: (key: string) => Effect.Effect<void>
}>() {}

// In-memory implementation
const MemoryCacheLive = Layer.sync(Cache, () => {
  const store = new Map<string, string>()
  return {
    get: (key) => Effect.succeed(Option.fromNullable(store.get(key))),
    set: (key, value) => Effect.sync(() => { store.set(key, value) }),
    del: (key) => Effect.sync(() => { store.delete(key) })
  }
})

// Redis implementation
const RedisCacheLive = Layer.effect(Cache,
  Effect.gen(function* () {
    const redis = yield* RedisClient
    return {
      get: (key) => Effect.tryPromise(() => redis.get(key)).pipe(Effect.map(Option.fromNullable)),
      set: (key, value, ttl) => Effect.tryPromise(() => redis.set(key, value, { EX: ttl })),
      del: (key) => Effect.tryPromise(() => redis.del(key))
    }
  })
)

// Usage — same code, different implementations
const app = myProgram.pipe(
  Effect.provide(process.env.USE_REDIS ? RedisCacheLive : MemoryCacheLive)
)
```

### Accessor Pattern

Create convenience functions that automatically access the service:

```typescript
class UserRepo extends Effect.Service<UserRepo>()("app/UserRepo", {
  effect: Effect.gen(function* () {
    const db = yield* Database
    return {
      findById: (id: string) =>
        db.query("SELECT * FROM users WHERE id = $1", [id]).pipe(
          Effect.map(r => r.rows[0] as User | undefined),
          Effect.flatMap(Effect.fromNullable),
          Effect.mapError(() => new NotFoundError({ entity: "User", id }))
        ),
      create: (data: CreateUser) =>
        db.query("INSERT INTO users ... RETURNING *", [data.name, data.email]).pipe(
          Effect.map(r => r.rows[0] as User)
        )
    }
  }),
  dependencies: [Database.Default]
}) {}

// Direct accessor functions
const findUserById = (id: string) =>
  Effect.gen(function* () {
    const repo = yield* UserRepo
    return yield* repo.findById(id)
  })
```

## Common Pitfalls

- **Don't provide services multiple times**: If a service depends on another, use layers to wire them together. Multiple `provideService` calls for the same tag silently overwrite.
- **Don't access services outside Effect.gen**: Services are only available inside the effect context. You can't `yield* Database` in regular TypeScript code.
- **Use unique string identifiers**: The string passed to `Effect.Service()("app/Database")` must be globally unique. Use a namespace prefix like `"app/"`.
- **One provide at the edge**: Compose all layers and provide once at the application entry point. Scattering `Effect.provide` throughout the codebase defeats the purpose of DI.

## Related Topics

- Layer composition → `04-layers.md`
- Resource management in services → `09-resource-management.md`
- Configuration → `10-configuration.md`
- Testing services → `11-testing.md`
