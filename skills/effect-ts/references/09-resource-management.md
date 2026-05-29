# Resource Management

> Source: [effect.website/docs](https://effect.website/docs/resource-management/scope/) | Package: `effect` v3.21.x

## Table of Contents

- [The Problem](#the-problem)
- [Scope — The Core Abstraction](#scope--the-core-abstraction)
- [Effect.acquireRelease](#effectacquirerelease)
- [Effect.acquireUseRelease](#effectacquireuserelease)
- [Effect.ensuring and Finalizers](#effectensuring-and-finalizers)
- [Composing Resources](#composing-resources)
- [Resources in Layers](#resources-in-layers)
- [Patterns and Best Practices](#patterns-and-best-practices)
- [Common Pitfalls](#common-pitfalls)

## The Problem

Resources like database connections, file handles, and network sockets must be cleaned up, even when errors occur or fibers are interrupted. Traditional try/finally is fragile — it doesn't compose, doesn't handle concurrent cleanup, and breaks with async operations.

```typescript
// Traditional — fragile, doesn't compose
let conn: Connection | null = null
try {
  conn = await pool.getConnection()
  await doWork(conn)
} finally {
  if (conn) conn.release() // hope this doesn't throw
}

// Effect — safe, composable, handles interruption
const program = Effect.acquireUseRelease(
  pool.getConnection(),
  (conn) => doWork(conn),
  (conn) => conn.release()
)
```

## Scope — The Core Abstraction

A `Scope` collects finalizers (cleanup functions) and runs them when it closes. Scopes can be nested — child scopes clean up before parents.

```typescript
import { Effect, Scope } from "effect"

// Effect.scoped creates a scope, runs the effect, then closes the scope
const program = Effect.scoped(
  Effect.gen(function* () {
    const conn = yield* acquireConnection()
    // conn is available here
    const result = yield* useConnection(conn)
    return result
    // conn is released when this scope closes
  })
)
```

## Effect.acquireRelease

Register a resource with the current scope. The release function runs when the scope closes, regardless of success, failure, or interruption:

```typescript
import { Effect } from "effect"

const managedConnection = Effect.acquireRelease(
  // Acquire — create the resource
  Effect.tryPromise(() => pool.getConnection()),
  // Release — cleanup (receives the acquired resource)
  (conn) => Effect.sync(() => conn.release())
)
// Effect<Connection, Error, Scope>
//                              ^^^^^ requires a Scope

// Use it in a scoped context
const program = Effect.scoped(
  Effect.gen(function* () {
    const conn = yield* managedConnection
    return yield* conn.query("SELECT * FROM users")
  })
)
// Effect<QueryResult, Error, never>
// Scope requirement is satisfied by Effect.scoped
```

### Release with Exit

The release function can inspect why the scope is closing:

```typescript
const managedFile = Effect.acquireRelease(
  Effect.sync(() => fs.openSync("data.txt", "r")),
  (fd, exit) =>
    Exit.isSuccess(exit)
      ? Effect.sync(() => { fs.closeSync(fd); console.log("Closed normally") })
      : Effect.sync(() => { fs.closeSync(fd); console.log("Closed due to error") })
)
```

## Effect.acquireUseRelease

For simple acquire-use-release patterns where you don't need composability:

```typescript
const result = yield* Effect.acquireUseRelease(
  // Acquire
  Effect.tryPromise(() => pool.getConnection()),
  // Use
  (conn) => Effect.tryPromise(() => conn.query("SELECT 1")),
  // Release
  (conn) => Effect.sync(() => conn.release())
)
// Effect<QueryResult, Error, never>
// No Scope needed — self-contained
```

### Difference from acquireRelease

| | acquireRelease | acquireUseRelease |
|---|---|---|
| Composability | Yes — multiple resources in same scope | No — self-contained |
| Scope requirement | Yes (needs `Effect.scoped`) | No |
| Use case | Multiple coordinated resources | Single resource lifecycle |

## Effect.ensuring and Finalizers

### Effect.ensuring — Always run

```typescript
const program = doWork().pipe(
  Effect.ensuring(Effect.log("Always runs, success or failure"))
)
```

### Effect.addFinalizer — Register cleanup in current scope

```typescript
const program = Effect.scoped(
  Effect.gen(function* () {
    yield* Effect.addFinalizer((exit) =>
      Effect.log(`Cleaning up. Exit: ${exit._tag}`)
    )
    yield* doWork()
  })
)
```

### Effect.onExit — Run on specific exit

```typescript
const program = doWork().pipe(
  Effect.onExit((exit) =>
    Exit.isFailure(exit)
      ? Effect.log("Operation failed, notifying admin")
      : Effect.void
  )
)
```

## Composing Resources

The power of `acquireRelease` + `Scope` is composability. Multiple resources share a scope and are cleaned up in reverse acquisition order:

```typescript
const managedDb = Effect.acquireRelease(
  Effect.sync(() => createDbPool()),
  (pool) => Effect.promise(() => pool.end())
)

const managedRedis = Effect.acquireRelease(
  Effect.sync(() => createRedisClient()),
  (client) => Effect.sync(() => client.quit())
)

const managedServer = (db: DbPool, redis: RedisClient) =>
  Effect.acquireRelease(
    Effect.sync(() => createHttpServer(db, redis).listen(3000)),
    (server) => Effect.sync(() => server.close())
  )

const program = Effect.scoped(
  Effect.gen(function* () {
    const db = yield* managedDb           // acquired 1st
    const redis = yield* managedRedis     // acquired 2nd
    const server = yield* managedServer(db, redis) // acquired 3rd
    yield* Effect.log("Server running. Press Ctrl+C to stop.")
    yield* Effect.never // keep running
    // Cleanup order: server → redis → db (reverse)
  })
)
```

## Resources in Layers

Layers with scoped resources are the most common pattern in production:

```typescript
class Database extends Effect.Service<Database>()("app/Database", {
  scoped: Effect.gen(function* () {
    const config = yield* AppConfig
    const pool = yield* Effect.acquireRelease(
      Effect.tryPromise(() => pg.Pool(config.dbUrl)),
      (pool) => Effect.promise(() => pool.end())
    )

    yield* Effect.log("Database pool created")
    yield* Effect.addFinalizer(() =>
      Effect.log("Database pool closing")
    )

    return {
      query: (sql: string, params?: unknown[]) =>
        Effect.tryPromise({
          try: () => pool.query(sql, params),
          catch: (e) => new DbError({ query: sql, cause: e })
        })
    }
  }),
  dependencies: [AppConfig.Default]
}) {}
```

When using `ManagedRuntime.make(layers)`, calling `dispose()` closes all scoped layers in reverse order.

## Patterns and Best Practices

### Temporary Files

```typescript
const withTempFile = (prefix: string) =>
  Effect.acquireRelease(
    Effect.sync(() => {
      const path = `${os.tmpdir()}/${prefix}-${Date.now()}`
      fs.writeFileSync(path, "")
      return path
    }),
    (path) => Effect.sync(() => {
      try { fs.unlinkSync(path) } catch {}
    })
  )

const program = Effect.scoped(
  Effect.gen(function* () {
    const tmpPath = yield* withTempFile("upload")
    yield* processUpload(tmpPath)
  })
)
```

### Lock File

```typescript
const withLock = (lockPath: string) =>
  Effect.acquireRelease(
    Effect.sync(() => {
      if (fs.existsSync(lockPath)) throw new Error("Already locked")
      fs.writeFileSync(lockPath, String(process.pid))
    }),
    () => Effect.sync(() => {
      try { fs.unlinkSync(lockPath) } catch {}
    })
  )
```

### Transaction Wrapper

```typescript
const withTransaction = Effect.acquireRelease(
  Effect.gen(function* () {
    const db = yield* Database
    yield* db.query("BEGIN")
    return db
  }),
  (db, exit) =>
    Exit.isSuccess(exit)
      ? db.query("COMMIT")
      : db.query("ROLLBACK")
)

const transferFunds = Effect.scoped(
  Effect.gen(function* () {
    const db = yield* withTransaction
    yield* db.query("UPDATE accounts SET balance = balance - 100 WHERE id = $1", [from])
    yield* db.query("UPDATE accounts SET balance = balance + 100 WHERE id = $1", [to])
  })
)
```

### Graceful Shutdown

```typescript
const gracefulShutdown = Effect.gen(function* () {
  const shutdownSignal = yield* Deferred.make<void>()

  process.on("SIGTERM", () => {
    Effect.runSync(Deferred.succeed(shutdownSignal, undefined))
  })

  yield* Effect.scoped(
    Effect.gen(function* () {
      const server = yield* startServer()
      yield* Effect.addFinalizer(() =>
        Effect.gen(function* () {
          yield* Effect.log("Draining connections...")
          yield* Effect.sleep(Duration.seconds(5))
          yield* Effect.log("Shutdown complete")
        })
      )
      yield* Deferred.await(shutdownSignal)
    })
  )
})
```

## Common Pitfalls

- **Don't forget Effect.scoped**: `acquireRelease` adds a `Scope` requirement. Without `Effect.scoped` (or a scoped Layer), the resource is never released.
- **Release must not fail**: Release functions should be best-effort. Wrap them in `Effect.sync` with try/catch to avoid masking the original error.
- **Order matters**: Resources are released in reverse acquisition order. Acquire dependencies first, dependents second.
- **Effect.scoped is not a scope**: It creates a scope, runs the effect, and immediately closes the scope. For long-lived scopes, use `ManagedRuntime` or `Layer.scoped`.
- **Don't use acquireRelease for layers**: Prefer `Layer.scoped` with `acquireRelease` inside — this wires into the application lifecycle automatically.

## Related Topics

- Layers with resources → `04-layers.md`
- Fibers and scopes → `06-concurrency.md`
- Testing resources → `11-testing.md`
