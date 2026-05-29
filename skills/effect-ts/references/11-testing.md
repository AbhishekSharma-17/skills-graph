# Testing

> Source: [effect.website/docs](https://effect.website/docs) | Package: `@effect/vitest` | `effect` v3.21.x

## Table of Contents

- [Setup](#setup)
- [Basic Testing with it.effect](#basic-testing-with-iteffect)
- [Testing with Layers](#testing-with-layers)
- [TestClock — Time Manipulation](#testclock--time-manipulation)
- [Testing Error Cases](#testing-error-cases)
- [Mocking Services](#mocking-services)
- [Property-Based Testing](#property-based-testing)
- [Testing Streams](#testing-streams)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Setup

Install `@effect/vitest` alongside `vitest`:

```bash
npm install -D vitest @effect/vitest
```

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config"

export default defineConfig({
  test: {
    globals: true
  }
})
```

## Basic Testing with it.effect

The `it.effect` function runs an Effect as a test case, providing a `TestContext` automatically:

```typescript
import { it, describe } from "@effect/vitest"
import { Effect } from "effect"

describe("UserService", () => {
  it.effect("creates a user successfully", () =>
    Effect.gen(function* () {
      const user = yield* createUser({ name: "Alice", email: "alice@test.com" })
      expect(user.name).toBe("Alice")
      expect(user.id).toBeDefined()
    })
  )

  it.effect("fails on duplicate email", () =>
    Effect.gen(function* () {
      yield* createUser({ name: "Alice", email: "alice@test.com" })
      const exit = yield* Effect.exit(
        createUser({ name: "Bob", email: "alice@test.com" })
      )
      expect(exit._tag).toBe("Failure")
    })
  )
})
```

### it.live — Real Clock

By default, `it.effect` provides a `TestClock` that starts at epoch 0. Use `it.live` for the real system clock:

```typescript
it.live("measures actual time", () =>
  Effect.gen(function* () {
    const start = Date.now()
    yield* Effect.sleep(Duration.millis(100))
    const elapsed = Date.now() - start
    expect(elapsed).toBeGreaterThanOrEqual(90)
  })
)
```

### it.scoped — With Resource Cleanup

```typescript
it.scoped("uses a managed resource", () =>
  Effect.gen(function* () {
    const conn = yield* managedConnection
    const result = yield* conn.query("SELECT 1")
    expect(result.rows).toHaveLength(1)
    // conn is released after the test
  })
)
```

## Testing with Layers

Provide services to your tests using `it.layer`:

```typescript
import { it, describe } from "@effect/vitest"
import { Layer, Effect } from "effect"

// Create test implementations
const TestDatabaseLive = Layer.succeed(Database, {
  query: (sql) => Effect.succeed({ rows: [{ id: 1, name: "test" }] })
})

const TestLayer = Layer.mergeAll(
  TestDatabaseLive,
  LoggerLive
)

describe("with test services", () => {
  it.layer(TestLayer)("fetches a user", () =>
    Effect.gen(function* () {
      const db = yield* Database
      const result = yield* db.query("SELECT * FROM users")
      expect(result.rows).toHaveLength(1)
    })
  )
})
```

### Layer per describe block

```typescript
describe("UserRepo", () => {
  const TestLayer = Layer.mergeAll(
    Layer.succeed(Database, mockDb),
    Layer.succeed(Cache, mockCache)
  )

  it.layer(TestLayer)("findById returns user", () =>
    Effect.gen(function* () {
      const repo = yield* UserRepo
      const user = yield* repo.findById("1")
      expect(user.name).toBe("test")
    })
  )

  it.layer(TestLayer)("findById fails for missing user", () =>
    Effect.gen(function* () {
      const repo = yield* UserRepo
      const exit = yield* Effect.exit(repo.findById("999"))
      expect(exit._tag).toBe("Failure")
    })
  )
})
```

## TestClock — Time Manipulation

The `TestClock` lets you control time in tests without waiting:

```typescript
import { it } from "@effect/vitest"
import { Effect, TestClock, Duration, Fiber } from "effect"

it.effect("handles timeout", () =>
  Effect.gen(function* () {
    // Fork a delayed effect
    const fiber = yield* Effect.fork(
      Effect.sleep(Duration.minutes(5)).pipe(
        Effect.as("completed")
      )
    )

    // Fast-forward time
    yield* TestClock.adjust(Duration.minutes(5))

    const result = yield* Fiber.join(fiber)
    expect(result).toBe("completed")
  })
)

it.effect("tests scheduled retries", () =>
  Effect.gen(function* () {
    let attempts = 0

    const program = Effect.gen(function* () {
      attempts++
      if (attempts < 3) {
        return yield* Effect.fail(new Error("not yet"))
      }
      return "success"
    }).pipe(
      Effect.retry(Schedule.spaced(Duration.seconds(10)))
    )

    const fiber = yield* Effect.fork(program)

    // Advance through retries
    yield* TestClock.adjust(Duration.seconds(10))
    yield* TestClock.adjust(Duration.seconds(10))

    const result = yield* Fiber.join(fiber)
    expect(result).toBe("success")
    expect(attempts).toBe(3)
  })
)
```

## Testing Error Cases

### Asserting on Exit

```typescript
it.effect("returns correct error type", () =>
  Effect.gen(function* () {
    const exit = yield* Effect.exit(
      fetchUser("nonexistent-id")
    )

    expect(exit._tag).toBe("Failure")
    if (exit._tag === "Failure") {
      const error = Cause.failureOption(exit.cause)
      expect(Option.isSome(error)).toBe(true)
      if (Option.isSome(error)) {
        expect(error.value._tag).toBe("NotFoundError")
      }
    }
  })
)
```

### Using Effect.either

```typescript
it.effect("validates input correctly", () =>
  Effect.gen(function* () {
    const result = yield* Effect.either(
      validateEmail("not-an-email")
    )

    expect(Either.isLeft(result)).toBe(true)
    if (Either.isLeft(result)) {
      expect(result.left._tag).toBe("ValidationError")
    }
  })
)
```

### it.fails — Expect failure

```typescript
it.effect("rejects invalid input", () =>
  Effect.gen(function* () {
    const result = yield* Effect.flip(validateEmail("bad"))
    expect(result._tag).toBe("ValidationError")
  })
)
```

## Mocking Services

### Simple Mocks

```typescript
const MockDatabase = Layer.succeed(Database, {
  query: (sql: string) => {
    if (sql.includes("users")) {
      return Effect.succeed({ rows: [{ id: "1", name: "Mock User" }] })
    }
    return Effect.succeed({ rows: [] })
  }
})
```

### Stateful Mocks

```typescript
const makeStatefulMock = () => {
  const calls: string[] = []

  const MockDb = Layer.succeed(Database, {
    query: (sql: string) => {
      calls.push(sql)
      return Effect.succeed({ rows: [] })
    }
  })

  return { MockDb, calls }
}

it.effect("executes correct queries", () => {
  const { MockDb, calls } = makeStatefulMock()

  return Effect.gen(function* () {
    yield* getUser("123")
    expect(calls).toContain("SELECT * FROM users WHERE id = $1")
  }).pipe(Effect.provide(MockDb))
})
```

### Ref-Based Mocks

```typescript
const makeRefMock = Effect.gen(function* () {
  const callLog = yield* Ref.make<string[]>([])

  const layer = Layer.succeed(Database, {
    query: (sql: string) =>
      Ref.update(callLog, (log) => [...log, sql]).pipe(
        Effect.as({ rows: [] })
      )
  })

  return { layer, callLog }
})
```

## Property-Based Testing

Effect Schema can generate arbitrary test data:

```typescript
import { Schema, Arbitrary } from "effect"
import * as fc from "fast-check"

const UserSchema = Schema.Struct({
  name: Schema.NonEmptyString,
  age: Schema.Number.pipe(Schema.int(), Schema.between(0, 150)),
  email: Schema.String
})

const userArbitrary = Arbitrary.make(UserSchema)

it("validates any generated user", () => {
  fc.assert(
    fc.property(userArbitrary, (user) => {
      const result = Schema.decodeUnknownEither(UserSchema)(user)
      expect(Either.isRight(result)).toBe(true)
    })
  )
})
```

## Testing Streams

```typescript
it.effect("processes stream correctly", () =>
  Effect.gen(function* () {
    const result = yield* Stream.fromIterable([1, 2, 3, 4, 5]).pipe(
      Stream.filter((n) => n % 2 === 0),
      Stream.map((n) => n * 10),
      Stream.runCollect
    )

    expect(Array.from(result)).toEqual([20, 40])
  })
)

it.effect("handles stream errors", () =>
  Effect.gen(function* () {
    const result = yield* Stream.fromIterable([1, 2, 3]).pipe(
      Stream.mapEffect((n) =>
        n === 2 ? Effect.fail(new Error("bad")) : Effect.succeed(n)
      ),
      Stream.catchAll(() => Stream.succeed(-1)),
      Stream.runCollect
    )

    expect(Array.from(result)).toEqual([1, -1])
  })
)
```

## Common Patterns

### Test Config Provider

```typescript
const TestConfigLayer = Layer.setConfigProvider(
  ConfigProvider.fromMap(new Map([
    ["PORT", "8080"],
    ["DATABASE_URL", "postgres://localhost/test"],
    ["JWT_SECRET", "test-secret"]
  ]))
)

describe("with test config", () => {
  it.layer(TestConfigLayer)("loads config", () =>
    Effect.gen(function* () {
      const port = yield* Config.number("PORT")
      expect(port).toBe(8080)
    })
  )
})
```

### Snapshot Testing

```typescript
it.effect("returns expected structure", () =>
  Effect.gen(function* () {
    const result = yield* buildResponse(testInput)
    expect(result).toMatchSnapshot()
  })
)
```

### Timeout in Tests

```typescript
it.effect("completes within timeout", () =>
  Effect.gen(function* () {
    const result = yield* longOperation.pipe(
      Effect.timeout(Duration.seconds(5)),
      Effect.orDie
    )
    expect(result).toBeDefined()
  })
)
```

## Common Pitfalls

- **TestClock starts at epoch 0**: Don't rely on `Date.now()` in tests with `it.effect`. Use `it.live` or inject a Clock service.
- **Layer construction runs once**: `it.layer(layer)` constructs the layer once for all tests in the block. Don't rely on fresh state per test unless you create a new layer per test.
- **Don't mix Effect and raw async**: Inside `it.effect`, use `yield*` for effects. Don't `await` promises directly — wrap them with `Effect.tryPromise`.
- **Assertion errors are defects**: Using `expect()` inside `Effect.gen` works, but assertion failures become defects, not typed errors. The test still fails correctly.

## Related Topics

- Services and layers → `03-context-services.md` and `04-layers.md`
- Schema for test data → `05-schema.md`
- Config testing → `10-configuration.md`
