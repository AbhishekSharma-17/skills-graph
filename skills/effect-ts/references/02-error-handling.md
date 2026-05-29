# Error Handling

> Source: [effect.website/docs](https://effect.website/docs/error-management/) | Package: `effect` v3.21.x

## Table of Contents

- [Philosophy: Typed Errors](#philosophy-typed-errors)
- [Tagged Errors](#tagged-errors)
- [Creating Failing Effects](#creating-failing-effects)
- [Catching Errors](#catching-errors)
- [Defects vs Failures](#defects-vs-failures)
- [Retry Policies](#retry-policies)
- [Error Accumulation](#error-accumulation)
- [Cause — The Full Error Story](#cause--the-full-error-story)
- [Patterns and Best Practices](#patterns-and-best-practices)

## Philosophy: Typed Errors

Effect tracks errors in the type system. If a function returns `Effect<User, NetworkError | ValidationError, Database>`, the compiler knows exactly which errors can occur and won't let you run the effect until every error is handled or propagated.

```typescript
// Compare with traditional TypeScript:
async function fetchUser(id: string): Promise<User> {
  // Can throw anything — caller has no idea what
}

// Effect approach:
const fetchUser = (id: string): Effect.Effect<User, NetworkError | NotFoundError, HttpClient> => ...
// Caller sees exactly: NetworkError and NotFoundError are possible
```

## Tagged Errors

The idiomatic way to define errors in Effect. Use `Data.TaggedError` to create error classes with automatic `_tag` discrimination:

```typescript
import { Data } from "effect"

class NetworkError extends Data.TaggedError("NetworkError")<{
  readonly url: string
  readonly status: number
}> {}

class ValidationError extends Data.TaggedError("ValidationError")<{
  readonly field: string
  readonly message: string
}> {}

class NotFoundError extends Data.TaggedError("NotFoundError")<{
  readonly entity: string
  readonly id: string
}> {}
```

### Why Tagged Errors

- Automatic `_tag` field enables pattern matching with `Effect.catchTag`
- Structural equality (two errors with same data are equal)
- `toString()` includes tag and fields
- Fully serializable
- Works with discriminated union narrowing in TypeScript

## Creating Failing Effects

```typescript
import { Effect } from "effect"

// Fail with a typed error
const fail = Effect.fail(new NetworkError({ url: "/api", status: 500 }))

// Fail conditionally
const validate = (input: string) =>
  input.length > 0
    ? Effect.succeed(input)
    : Effect.fail(new ValidationError({ field: "name", message: "required" }))

// From nullable — fails with NoSuchElementException
const fromNullable = Effect.fromNullable(maybeValue)

// Try/catch with typed error mapping
const parsed = Effect.try({
  try: () => JSON.parse(raw),
  catch: (e) => new ValidationError({ field: "body", message: String(e) })
})
```

## Catching Errors

### catchAll — Catch all errors

```typescript
const program = fetchUser(id).pipe(
  Effect.catchAll((error) =>
    // error: NetworkError | NotFoundError
    Effect.succeed({ name: "Anonymous", fallback: true })
  )
)
// Effect<User, never, HttpClient> — errors eliminated
```

### catchTag — Catch by error tag

```typescript
const program = fetchUser(id).pipe(
  Effect.catchTag("NotFoundError", (error) =>
    Effect.succeed(createDefaultUser(error.id))
  )
)
// Effect<User, NetworkError, HttpClient> — NotFoundError handled, NetworkError remains
```

### catchTags — Catch multiple tags

```typescript
const program = fetchUser(id).pipe(
  Effect.catchTags({
    NotFoundError: (e) => Effect.succeed(createDefaultUser(e.id)),
    ValidationError: (e) => Effect.fail(new BadRequestError({ detail: e.message })),
  })
)
// Only NetworkError remains in the error channel
```

### catchSome — Conditionally catch

```typescript
const program = fetchUser(id).pipe(
  Effect.catchSome((error) => {
    if (error._tag === "NetworkError" && error.status === 404) {
      return Option.some(Effect.succeed(defaultUser))
    }
    return Option.none()
  })
)
```

### either — Convert to Either

```typescript
const program = Effect.gen(function* () {
  const result = yield* Effect.either(riskyOp)
  // result: Either<Success, Error> — no error in the channel

  if (Either.isLeft(result)) {
    return handleError(result.left)
  }
  return result.right
})
```

### orElse — Fallback effect

```typescript
const program = fetchFromPrimary.pipe(
  Effect.orElse(() => fetchFromFallback)
)
```

### orDie — Convert error to defect

```typescript
// Crashes on error (becomes a defect, not a typed error)
const program = riskyOp.pipe(Effect.orDie)
```

## Defects vs Failures

Effect distinguishes between two kinds of errors:

| | Failures | Defects |
|---|---------|---------|
| **What** | Expected, recoverable errors | Unexpected, unrecoverable errors |
| **Type-tracked** | Yes (in `E` parameter) | No |
| **Created by** | `Effect.fail()` | `Effect.die()`, thrown exceptions |
| **Catch with** | `catchAll`, `catchTag`, etc. | `catchAllDefect`, `sandbox` |
| **Examples** | Validation errors, not-found, network | Null pointer, stack overflow, bugs |

### Sandboxing — Accessing the Full Cause

```typescript
// sandbox exposes the full Cause (including defects) as the error
const sandboxed = Effect.sandbox(program)
// Effect<A, Cause<E>, R>

// catchAllCause — access full cause tree
const program = riskyOp.pipe(
  Effect.catchAllCause((cause) => {
    if (Cause.isFailure(cause)) {
      return handleExpected(cause.error)
    }
    return Effect.logError("Unexpected defect", cause)
  })
)
```

## Retry Policies

Use `Schedule` to define retry behavior:

```typescript
import { Effect, Schedule, Duration } from "effect"

// Retry up to 3 times
const retried = Effect.retry(program, Schedule.recurs(3))

// Exponential backoff starting at 1 second
const exponential = Effect.retry(
  program,
  Schedule.exponential(Duration.seconds(1))
)

// Exponential with max delay cap
const capped = Effect.retry(
  program,
  Schedule.exponential(Duration.seconds(1)).pipe(
    Schedule.either(Schedule.spaced(Duration.seconds(30)))
  )
)

// Retry only specific errors
const selective = Effect.retry(program, {
  schedule: Schedule.recurs(3),
  while: (error) => error._tag === "NetworkError"
})

// Retry with jitter
const jittered = Effect.retry(
  program,
  Schedule.exponential(Duration.seconds(1)).pipe(Schedule.jittered)
)

// Combined: 3 retries, exponential backoff, max 30s, only on transient errors
const robust = Effect.retry(program, {
  schedule: Schedule.exponential(Duration.seconds(1)).pipe(
    Schedule.intersect(Schedule.recurs(3)),
    Schedule.jittered
  ),
  while: (error) => error._tag === "NetworkError" && error.status >= 500
})
```

## Error Accumulation

Collect all errors instead of failing fast:

```typescript
import { Effect } from "effect"

// Validate all fields and collect errors
const validateForm = Effect.validateAll(
  [
    validateName(input.name),
    validateEmail(input.email),
    validateAge(input.age)
  ]
)
// Effect<[Name, Email, Age], ValidationError[], never>

// forEach with error accumulation
const results = Effect.forEach(
  items,
  (item) => processItem(item),
  { concurrency: "unbounded", mode: "validate" }
)
// Collects all errors instead of short-circuiting
```

## Cause — The Full Error Story

`Cause<E>` represents the complete error history, including:
- **Fail**: A typed error value
- **Die**: An unexpected defect
- **Interrupt**: Fiber interruption
- **Sequential**: Errors that happened one after another
- **Parallel**: Errors from concurrent operations

```typescript
import { Effect, Cause } from "effect"

const inspectCause = Effect.gen(function* () {
  const exit = yield* Effect.exit(program)

  if (exit._tag === "Failure") {
    const cause = exit.cause
    const failures = Cause.failures(cause)   // Chunk of typed errors
    const defects = Cause.defects(cause)     // Chunk of unexpected errors
    const isInterrupted = Cause.isInterrupted(cause)

    yield* Effect.log(`Failures: ${failures.length}, Defects: ${defects.length}`)
  }
})
```

## Patterns and Best Practices

### Error Hierarchy

Define a base error type for your domain:

```typescript
class AppError extends Data.TaggedError("AppError")<{
  readonly message: string
}> {}

class DbError extends Data.TaggedError("DbError")<{
  readonly query: string
  readonly cause: unknown
}> {}

class AuthError extends Data.TaggedError("AuthError")<{
  readonly reason: "expired" | "invalid" | "missing"
}> {}
```

### Wrapping Third-Party Errors

```typescript
const queryDb = (sql: string) =>
  Effect.tryPromise({
    try: () => pool.query(sql),
    catch: (e) => new DbError({ query: sql, cause: e })
  })
```

### Error Mapping at Boundaries

```typescript
const userService = {
  getUser: (id: string) =>
    queryDb(`SELECT * FROM users WHERE id = $1`, [id]).pipe(
      Effect.mapError((dbErr) =>
        new NotFoundError({ entity: "User", id })
      )
    )
}
```

### Never Swallow Errors

```typescript
// BAD — error information lost
Effect.catchAll(() => Effect.succeed(null))

// GOOD — preserve error context
Effect.catchTag("NotFoundError", (e) =>
  Effect.succeed({ found: false, searched: e.id })
)
```

## Common Pitfalls

- **Don't throw inside Effect.gen**: Use `yield* Effect.fail(...)` instead. Thrown exceptions become defects, not typed errors.
- **Don't catch too broadly**: Prefer `catchTag` over `catchAll` to handle specific errors while letting unexpected ones propagate.
- **Don't ignore the error type**: If a function returns `Effect<A, E, R>`, the `E` is there for a reason — handle it or propagate it intentionally.
- **Don't use `orDie` casually**: Converting failures to defects removes them from the type system. Only use when the error truly can't be recovered from.

## Related Topics

- Creating effects → `01-effect-type.md`
- Dependency injection (errors in services) → `03-context-services.md`
- Retry with concurrency → `06-concurrency.md`
