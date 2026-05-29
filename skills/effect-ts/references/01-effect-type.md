# The Effect Type

> Source: [effect.website/docs](https://effect.website/docs/getting-started/the-effect-type/) | Package: `effect` v3.21.x

## Table of Contents

- [The Effect<A, E, R> Type](#the-effecta-e-r-type)
- [Creating Effects](#creating-effects)
- [Effect.gen — Generator Syntax](#effectgen--generator-syntax)
- [Pipe and Flow](#pipe-and-flow)
- [Running Effects](#running-effects)
- [Combining Effects](#combining-effects)
- [Mapping and Transformation](#mapping-and-transformation)
- [Tapping (Side Effects)](#tapping-side-effects)
- [Common Patterns](#common-patterns)

## The Effect<A, E, R> Type

Every Effect value has three type parameters:

```typescript
Effect<Success, Error, Requirements>
//      A        E      R
```

- **A** (Success): The type of the value produced on success
- **E** (Error): The type of the expected error (use `never` for infallible effects)
- **R** (Requirements): The services needed from the environment (use `never` for self-contained effects)

The type parameters flow through composition — when you combine two effects, their errors union and their requirements union automatically.

## Creating Effects

### From Values

```typescript
import { Effect } from "effect"

// Succeed with a value — Effect<number, never, never>
const success = Effect.succeed(42)

// Fail with an error — Effect<never, Error, never>
const failure = Effect.fail(new Error("something broke"))

// Suspend a lazy computation — Effect<number, never, never>
const suspended = Effect.sync(() => Math.random())

// Die with a defect (untyped, unrecoverable)
const defect = Effect.die(new Error("unexpected"))
```

### From Promises

```typescript
// Wrap a promise — requires a catch handler for type safety
const fromPromise = Effect.tryPromise({
  try: () => fetch("https://api.example.com/data"),
  catch: (error) => new NetworkError({ cause: error })
})
// Effect<Response, NetworkError, never>

// Simple promise wrapping (error typed as UnknownException)
const simple = Effect.tryPromise(() => fetch("/api"))
// Effect<Response, UnknownException, never>
```

### From Callbacks

```typescript
import { Effect } from "effect"

const readFile = Effect.async<string, NodeJS.ErrnoException>((resume) => {
  fs.readFile("data.txt", "utf-8", (err, data) => {
    if (err) resume(Effect.fail(err))
    else resume(Effect.succeed(data))
  })
})
```

### Conditional Effects

```typescript
const checked = Effect.if(condition, {
  onTrue: () => Effect.succeed("yes"),
  onFalse: () => Effect.fail(new InvalidInput())
})

// From nullable
const fromNullable = Effect.fromNullable(maybeValue)
// Effect<NonNullable<T>, Cause.NoSuchElementException, never>
```

## Effect.gen — Generator Syntax

The recommended way to write sequential Effect code. Uses generators to provide an async/await-like syntax:

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const user = yield* fetchUser(userId)
  const posts = yield* fetchPosts(user.id)
  const enriched = yield* enrichPosts(posts)
  return { user, posts: enriched }
})
```

### Rules for Effect.gen

- Use `yield*` (not `yield`) to unwrap effects
- The generator function receives no arguments
- Return value becomes the success type
- Errors from yielded effects automatically propagate
- Requirements from yielded effects automatically accumulate

### Error Handling in Generators

```typescript
const program = Effect.gen(function* () {
  const result = yield* Effect.either(riskyOperation)
  // result is Either<Success, Error> — no exception thrown

  if (result._tag === "Left") {
    yield* Console.log(`Recovered from: ${result.left}`)
    return "default"
  }
  return result.right
})
```

## Pipe and Flow

Effect provides two composition styles:

### pipe — Point-free chaining

```typescript
import { pipe } from "effect"

const result = pipe(
  Effect.succeed(5),
  Effect.map(n => n * 2),
  Effect.flatMap(n => Effect.succeed(n + 1)),
  Effect.tap(n => Console.log(`Result: ${n}`))
)
```

### Instance .pipe method

```typescript
const result = Effect.succeed(5).pipe(
  Effect.map(n => n * 2),
  Effect.flatMap(n => Effect.succeed(n + 1))
)
```

### Flow — Function composition

```typescript
import { flow } from "effect"

const transform = flow(
  (s: string) => s.trim(),
  (s) => s.toLowerCase(),
  (s) => s.split(" ")
)
transform("  Hello World  ") // ["hello", "world"]
```

## Running Effects

Effects are lazy descriptions — you must explicitly run them:

```typescript
import { Effect } from "effect"

// Run and return a Promise (most common)
const result = await Effect.runPromise(program)

// Run synchronously (only for sync effects)
const sync = Effect.runSync(syncProgram)

// Run and get an Exit (success or failure, never throws)
const exit = await Effect.runPromiseExit(program)

// Run with a custom runtime
const runtime = ManagedRuntime.make(myLayers)
const result = await runtime.runPromise(program)
```

### ManagedRuntime for Applications

```typescript
import { ManagedRuntime, Layer } from "effect"

const AppLayer = Layer.mergeAll(DatabaseLive, LoggerLive, ConfigLive)
const runtime = ManagedRuntime.make(AppLayer)

// Use throughout your application
const result = await runtime.runPromise(myEffect)

// Clean up on shutdown
await runtime.dispose()
```

## Combining Effects

### Sequential

```typescript
// flatMap — chain dependent effects
const program = Effect.flatMap(fetchUser(id), (user) => fetchPosts(user.id))

// andThen — chain ignoring the previous result
const program = Effect.andThen(initDb, startServer)

// tap — run a side effect, keep the original value
const program = Effect.tap(fetchUser(id), (user) => logAccess(user))
```

### Parallel

```typescript
// Run all in parallel, fail on first error
const [user, posts, comments] = yield* Effect.all(
  [fetchUser(id), fetchPosts(id), fetchComments(id)],
  { concurrency: "unbounded" }
)

// Run all, collect both successes and failures
const results = yield* Effect.allSettled([op1, op2, op3])

// Race — first to complete wins
const fastest = yield* Effect.race(fetchFromCDN, fetchFromOrigin)

// Run effects with bounded parallelism
const results = yield* Effect.all(operations, { concurrency: 10 })
```

### Iteration

```typescript
// Map over an array with effects
const users = yield* Effect.forEach(
  userIds,
  (id) => fetchUser(id),
  { concurrency: 5 }
)

// Reduce with effects
const total = yield* Effect.reduce(
  items,
  0,
  (acc, item) => Effect.succeed(acc + item.price)
)
```

## Mapping and Transformation

```typescript
// Map the success value
Effect.map(effect, (a) => a.toUpperCase())

// Map the error
Effect.mapError(effect, (e) => new WrappedError(e))

// Map both
Effect.mapBoth(effect, {
  onFailure: (e) => new WrappedError(e),
  onSuccess: (a) => a.toUpperCase()
})

// FlatMap — chain into another effect
Effect.flatMap(effect, (a) => anotherEffect(a))

// Provide a fallback value on error
Effect.orElseSucceed(effect, () => "default")

// Provide a fallback effect on error
Effect.orElse(primary, () => fallbackEffect)
```

## Tapping (Side Effects)

Tap functions run a side effect without changing the return value:

```typescript
// Tap on success
Effect.tap(fetchUser(id), (user) => Console.log(`Fetched: ${user.name}`))

// Tap on error
Effect.tapError(program, (err) => logError(err))

// Tap on both
Effect.tapBoth(program, {
  onFailure: (err) => logError(err),
  onSuccess: (val) => logSuccess(val)
})

// Tap with an effectful operation
Effect.tap(fetchUser(id), (user) => saveToCache(user))
```

## Common Patterns

### Option Handling

```typescript
import { Effect, Option } from "effect"

const program = Effect.gen(function* () {
  const maybeUser = yield* findUser(email) // Effect<Option<User>, DbError, Database>

  if (Option.isNone(maybeUser)) {
    return yield* Effect.fail(new UserNotFound({ email }))
  }

  return maybeUser.value
})
```

### Timeout

```typescript
import { Effect, Duration } from "effect"

const withTimeout = program.pipe(
  Effect.timeout(Duration.seconds(5)),
  // Effect<Option<A>, E, R> — None if timed out
)

// Or fail on timeout
const failOnTimeout = program.pipe(
  Effect.timeoutFail({
    duration: Duration.seconds(5),
    onTimeout: () => new TimeoutError()
  })
)
```

### Delay and Scheduling

```typescript
// Delay before running
const delayed = Effect.delay(program, Duration.seconds(1))

// Repeat on a schedule
const repeated = Effect.repeat(program, Schedule.spaced(Duration.seconds(10)))

// Retry on a schedule
const retried = Effect.retry(program, Schedule.exponential(Duration.seconds(1)))
```

### Annotations and Logging

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  yield* Effect.log("Starting operation")
  yield* Effect.logDebug("Debug details")
  yield* Effect.logWarning("Something unusual")
  yield* Effect.logError("Something failed")

  yield* Effect.annotateCurrentSpan("userId", userId)
  yield* Effect.withSpan("fetchUser")(fetchUser(userId))
})
```

## Common Pitfalls

- **Forgetting yield***: Writing `const x = fetchUser(id)` inside `Effect.gen` assigns the Effect description, not the result. Always `yield*`.
- **Using async/await inside Effect.gen**: Don't. Wrap promises with `Effect.tryPromise` and use `yield*`.
- **Ignoring the R parameter**: If your effect requires services, you must provide them before running. The compiler enforces this.
- **Effect.runSync on async effects**: This throws. Use `Effect.runPromise` for any effect that involves async operations.

## Related Topics

- Error handling patterns → `02-error-handling.md`
- Dependency injection → `03-context-services.md`
- Parallel execution → `06-concurrency.md`
