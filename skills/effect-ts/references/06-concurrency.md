# Concurrency

> Source: [effect.website/docs](https://effect.website/docs/concurrency/fibers/) | Package: `effect` v3.21.x

## Table of Contents

- [Structured Concurrency](#structured-concurrency)
- [Fibers](#fibers)
- [Forking and Joining](#forking-and-joining)
- [Parallel Combinators](#parallel-combinators)
- [Interruption and Cancellation](#interruption-and-cancellation)
- [Racing](#racing)
- [Timeouts](#timeouts)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Structured Concurrency

Effect implements structured concurrency: every concurrent task has a parent scope, and child fibers are automatically cleaned up when the parent completes or is interrupted. No orphaned tasks, no leaked resources.

```typescript
const program = Effect.gen(function* () {
  // These fibers are children of the current scope
  const fiber1 = yield* Effect.fork(longRunningTask1)
  const fiber2 = yield* Effect.fork(longRunningTask2)

  const result1 = yield* Fiber.join(fiber1)
  const result2 = yield* Fiber.join(fiber2)
  return [result1, result2]
})
// If program is interrupted, fiber1 and fiber2 are also interrupted
```

## Fibers

Fibers are lightweight virtual threads implemented by Effect on top of JavaScript's single-threaded async runtime. They provide:
- Cooperative multitasking (yield points at every `Effect` boundary)
- Independent error channels
- Interruption (cancellation) support
- Resource-safe lifecycle management

```typescript
import { Effect, Fiber } from "effect"

// A fiber wraps a running effect
const fiber: Fiber.RuntimeFiber<string, Error> = ...

// Get the result (blocks the current fiber until done)
const result = yield* Fiber.join(fiber)

// Get the exit status (doesn't re-throw errors)
const exit = yield* Fiber.await(fiber)

// Interrupt a fiber (cancel it)
yield* Fiber.interrupt(fiber)
```

## Forking and Joining

### Effect.fork — Fork into the current scope

```typescript
const program = Effect.gen(function* () {
  // Fork a background task — child of current scope
  const fiber = yield* Effect.fork(backgroundTask)

  // Do other work concurrently
  yield* doSomethingElse()

  // Wait for the background task to complete
  const result = yield* Fiber.join(fiber)
  return result
})
```

### Effect.forkDaemon — Fork outside all scopes

```typescript
// Daemon fibers are NOT interrupted when parent completes
const fiber = yield* Effect.forkDaemon(metricsReporter)
// This fiber lives until the entire program exits
```

### Effect.forkScoped — Fork into a specific scope

```typescript
const program = Effect.scoped(
  Effect.gen(function* () {
    // This fiber is cleaned up when the scope closes
    const fiber = yield* Effect.forkScoped(backgroundWork)
    yield* doWork()
    // fiber is interrupted here when scope ends
  })
)
```

### Effect.forkIn — Fork into an explicit scope

```typescript
const program = Effect.gen(function* () {
  const scope = yield* Scope.make()
  const fiber = yield* Effect.forkIn(backgroundWork, scope)
  // ...
  yield* Scope.close(scope, Exit.void)
  // fiber is interrupted when scope closes
})
```

## Parallel Combinators

### Effect.all — Run effects with configurable concurrency

```typescript
// Sequential (default)
const [a, b, c] = yield* Effect.all([effectA, effectB, effectC])

// Fully parallel
const [a, b, c] = yield* Effect.all(
  [effectA, effectB, effectC],
  { concurrency: "unbounded" }
)

// Bounded parallelism
const results = yield* Effect.all(
  operations,
  { concurrency: 10 }
)

// Parallel with batching
const results = yield* Effect.all(
  operations,
  { concurrency: "unbounded", batching: true }
)
```

### Effect.forEach — Map over items with effects

```typescript
const users = yield* Effect.forEach(
  userIds,
  (id) => fetchUser(id),
  { concurrency: 5 }
)
// Processes up to 5 users concurrently
```

### Effect.allSettled — Collect all results (successes and failures)

```typescript
const results = yield* Effect.allSettled([op1, op2, op3])
// Array<Exit<A, E>> — never fails, collects all outcomes
```

### Struct-based parallel execution

```typescript
const { user, posts, settings } = yield* Effect.all({
  user: fetchUser(userId),
  posts: fetchPosts(userId),
  settings: fetchSettings(userId)
}, { concurrency: "unbounded" })
```

## Interruption and Cancellation

### Interrupting fibers

```typescript
// Interrupt a specific fiber
yield* Fiber.interrupt(fiber)

// Interrupt with a specific cause
yield* Fiber.interruptFork(fiber)

// Self-interruption
yield* Effect.interrupt
```

### Uninterruptible regions

```typescript
// Protect critical sections from interruption
const criticalOperation = Effect.uninterruptible(
  Effect.gen(function* () {
    yield* beginTransaction()
    yield* performUpdates()
    yield* commitTransaction()
    // This entire block cannot be interrupted
  })
)
```

### Interruptibility control

```typescript
// Make an uninterruptible effect interruptible at specific points
const program = Effect.uninterruptible(
  Effect.gen(function* () {
    yield* criticalSetup()
    yield* Effect.interruptible(longRunningButSafe)
    yield* criticalCleanup()
  })
)
```

### onInterrupt — Cleanup on cancellation

```typescript
const program = Effect.gen(function* () {
  yield* startPolling()
}).pipe(
  Effect.onInterrupt(() => Effect.log("Polling cancelled, cleaning up"))
)
```

## Racing

```typescript
// First to succeed wins, loser is interrupted
const fastest = yield* Effect.race(
  fetchFromCDN(url),
  fetchFromOrigin(url)
)

// Race with explicit winner handling
const result = yield* Effect.raceWith(
  fetchFromPrimary,
  fetchFromSecondary,
  {
    onSelfDone: (exit, loserFiber) =>
      Fiber.interrupt(loserFiber).pipe(Effect.as(exit)),
    onOtherDone: (exit, loserFiber) =>
      Fiber.interrupt(loserFiber).pipe(Effect.as(exit))
  }
)

// First success among many
const result = yield* Effect.raceAll([
  fetchFromCDN1(url),
  fetchFromCDN2(url),
  fetchFromOrigin(url)
])
```

## Timeouts

```typescript
import { Effect, Duration } from "effect"

// Timeout — returns Option (None if timed out)
const result = yield* program.pipe(
  Effect.timeout(Duration.seconds(5))
)

// Timeout with fallback
const result = yield* program.pipe(
  Effect.timeoutTo({
    duration: Duration.seconds(5),
    onTimeout: () => Effect.succeed(defaultValue),
    onSuccess: (a) => Effect.succeed(a)
  })
)

// Timeout with failure
const result = yield* program.pipe(
  Effect.timeoutFail({
    duration: Duration.seconds(5),
    onTimeout: () => new TimeoutError()
  })
)

// Disconnect timeout — continue in background even after timeout
const result = yield* program.pipe(
  Effect.disconnect,
  Effect.timeout(Duration.seconds(5))
)
```

## Common Patterns

### Parallel with Fallback

```typescript
const fetchWithFallback = (url: string) =>
  fetchFromCache(url).pipe(
    Effect.orElse(() => fetchFromNetwork(url)),
    Effect.timeout(Duration.seconds(10)),
    Effect.orElseSucceed(() => ({ data: null, cached: false }))
  )
```

### Fan-Out / Fan-In

```typescript
const processChunks = (items: readonly Item[]) =>
  Effect.gen(function* () {
    const chunks = chunk(items, 100)
    const results = yield* Effect.forEach(
      chunks,
      (chunk) => processChunk(chunk),
      { concurrency: 4 }
    )
    return results.flat()
  })
```

### Background Work with Supervision

```typescript
const supervised = Effect.gen(function* () {
  const metricsF = yield* Effect.fork(
    metricsReporter.pipe(
      Effect.retry(Schedule.spaced(Duration.seconds(5))),
      Effect.catchAll(() => Effect.log("Metrics reporter failed permanently"))
    )
  )

  const result = yield* mainWork
  yield* Fiber.interrupt(metricsF)
  return result
})
```

## Common Pitfalls

- **Don't fork without joining or scoping**: Forked fibers that are never joined and not in a scope can leak. Use `Effect.forkScoped` or always join.
- **JavaScript is single-threaded**: Effect fibers provide concurrency (interleaved execution), not parallelism. CPU-bound work won't benefit from fibers.
- **yield* is a yield point**: Every `yield*` inside `Effect.gen` is a point where the runtime can switch to another fiber. Don't hold resources across yield points without proper cleanup.
- **Interruption is cooperative**: Fibers are only interrupted at yield points (`yield*`). A long synchronous computation won't be interrupted until it yields.

## Related Topics

- Concurrency patterns (Semaphore, Queue) → `07-concurrency-patterns.md`
- Streams (async data processing) → `08-streams.md`
- Resource management → `09-resource-management.md`
