# Testing

> Source: https://docs.deno.com/runtime/fundamentals/testing/

## Table of Contents

- [Writing Tests](#writing-tests)
- [Assertions](#assertions)
- [Test Configuration](#test-configuration)
- [Test Steps](#test-steps)
- [Parameterized Tests](#parameterized-tests)
- [Lifecycle Hooks](#lifecycle-hooks)
- [BDD-Style Testing](#bdd-style-testing)
- [Mocking](#mocking)
- [Snapshot Testing](#snapshot-testing)
- [Running Tests](#running-tests)
- [Coverage](#coverage)
- [Documentation Tests](#documentation-tests)
- [Test Sanitizers](#test-sanitizers)

## Writing Tests

Use `Deno.test()` to define tests. No external test framework needed:

```typescript
import { assertEquals } from "jsr:@std/assert";

// Simple function test
Deno.test("addition works", () => {
  assertEquals(1 + 2, 3);
});

// Async test
Deno.test("fetch returns data", async () => {
  const resp = await fetch("https://api.example.com/health");
  assertEquals(resp.status, 200);
});

// Named config object
Deno.test({
  name: "file operations",
  permissions: { read: true, write: ["./tmp"] },
  fn: async () => {
    await Deno.writeTextFile("./tmp/test.txt", "hello");
    const content = await Deno.readTextFile("./tmp/test.txt");
    assertEquals(content, "hello");
  },
});
```

## Assertions

### Standard Assertions (@std/assert)

```typescript
import {
  assert,
  assertAlmostEquals,
  assertArrayIncludes,
  assertEquals,
  assertExists,
  assertGreater,
  assertInstanceOf,
  assertMatch,
  assertNotEquals,
  assertNotStrictEquals,
  assertObjectMatch,
  assertRejects,
  assertStrictEquals,
  assertStringIncludes,
  assertThrows,
  fail,
  unimplemented,
  unreachable,
} from "jsr:@std/assert";

Deno.test("assertion examples", () => {
  // Equality (deep comparison)
  assertEquals({ a: 1, b: [2, 3] }, { a: 1, b: [2, 3] });

  // Strict equality (reference comparison)
  assertStrictEquals("hello", "hello");

  // Truthiness
  assert(true);
  assertExists("non-null-value");

  // Comparisons
  assertGreater(10, 5);

  // Strings
  assertStringIncludes("hello world", "world");
  assertMatch("user@example.com", /^[\w.]+@[\w.]+$/);

  // Arrays
  assertArrayIncludes([1, 2, 3], [2, 3]);

  // Objects (partial match)
  assertObjectMatch({ name: "Alice", age: 30 }, { name: "Alice" });

  // Floating point
  assertAlmostEquals(0.1 + 0.2, 0.3, 1e-10);
});

// Error assertions
Deno.test("throws on invalid input", () => {
  assertThrows(
    () => { throw new Error("bad input"); },
    Error,
    "bad input",
  );
});

Deno.test("rejects on failure", async () => {
  await assertRejects(
    async () => { throw new Error("async error"); },
    Error,
    "async error",
  );
});
```

### Jest-Style Assertions (@std/expect)

```typescript
import { expect } from "jsr:@std/expect";

Deno.test("jest-style assertions", () => {
  expect(1 + 2).toBe(3);
  expect({ a: 1 }).toEqual({ a: 1 });
  expect("hello").toContain("ell");
  expect([1, 2, 3]).toHaveLength(3);
  expect(null).toBeNull();
  expect(undefined).toBeUndefined();
  expect(42).toBeDefined();
  expect(10).toBeGreaterThan(5);
  expect(() => { throw new Error(); }).toThrow();
});
```

## Test Configuration

```typescript
Deno.test({
  name: "configurable test",

  // Skip this test
  ignore: Deno.build.os === "windows",

  // Focus on this test only (development)
  only: false,

  // Timeout in milliseconds
  timeout: 5000,

  // Retry failing tests
  retry: 3,

  // Repeat test N times (all must pass)
  repeats: 5,

  // Restrict permissions
  permissions: {
    read: ["./fixtures"],
    write: false,
    net: false,
    env: ["TEST_VAR"],
    run: false,
  },

  // Sanitizers
  sanitizeOps: true,     // Detect leaked async ops
  sanitizeResources: true, // Detect leaked resources
  sanitizeExit: true,    // Detect unexpected exits

  fn() {
    // Test body
  },
});

// Shorthand: skip
Deno.test.ignore("skipped test", () => {});

// Shorthand: focused
Deno.test.only("focused test", () => {});
```

## Test Steps

Organize related assertions into sub-steps:

```typescript
Deno.test("database operations", async (t) => {
  const db = await openDatabase();

  await t.step("insert user", async () => {
    const user = await db.insert({ name: "Alice", email: "alice@test.com" });
    assertExists(user.id);
  });

  await t.step("query user", async () => {
    const user = await db.findByEmail("alice@test.com");
    assertEquals(user?.name, "Alice");
  });

  await t.step("update user", async () => {
    await db.update("alice@test.com", { name: "Alice Smith" });
    const user = await db.findByEmail("alice@test.com");
    assertEquals(user?.name, "Alice Smith");
  });

  await t.step("delete user", async () => {
    await db.delete("alice@test.com");
    const user = await db.findByEmail("alice@test.com");
    assertEquals(user, null);
  });

  await db.close();
});
```

Steps can be nested:

```typescript
await t.step("parent", async (t) => {
  await t.step("child 1", () => { /* ... */ });
  await t.step("child 2", () => { /* ... */ });
});
```

## Parameterized Tests

Run the same test logic across multiple inputs (v2.9+):

### Array Form

```typescript
Deno.test.each([
  [1, 1, 2],
  [2, 3, 5],
  [10, -5, 5],
  [0, 0, 0],
])("add(%i, %i) = %i", (a, b, expected) => {
  assertEquals(a + b, expected);
});
```

### Object Form (with interpolation)

```typescript
Deno.test.each([
  { input: "hello", expected: "HELLO" },
  { input: "world", expected: "WORLD" },
  { input: "", expected: "" },
])("toUpperCase($input) = $expected", ({ input, expected }) => {
  assertEquals(input.toUpperCase(), expected);
});
```

## Lifecycle Hooks

```typescript
import {
  afterAll,
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  it,
} from "jsr:@std/testing/bdd";

describe("UserService", () => {
  let db: Database;

  beforeAll(async () => {
    db = await Database.connect(":memory:");
    await db.migrate();
  });

  afterAll(async () => {
    await db.close();
  });

  beforeEach(async () => {
    await db.truncate("users");
  });

  afterEach(() => {
    // Cleanup after each test
  });

  it("creates a user", async () => {
    const user = await db.createUser({ name: "Test" });
    assertExists(user.id);
  });
});
```

## BDD-Style Testing

```typescript
import { describe, it } from "jsr:@std/testing/bdd";
import { expect } from "jsr:@std/expect";

describe("Calculator", () => {
  describe("add", () => {
    it("adds positive numbers", () => {
      expect(add(1, 2)).toBe(3);
    });

    it("handles zero", () => {
      expect(add(0, 5)).toBe(5);
    });

    it("adds negative numbers", () => {
      expect(add(-1, -2)).toBe(-3);
    });
  });

  describe("divide", () => {
    it("divides evenly", () => {
      expect(divide(10, 2)).toBe(5);
    });

    it("throws on division by zero", () => {
      expect(() => divide(1, 0)).toThrow("Division by zero");
    });
  });
});
```

## Mocking

### Using @std/testing/mock

```typescript
import { assertSpyCalls, spy, stub } from "jsr:@std/testing/mock";

Deno.test("spy on function calls", () => {
  const logger = spy(console, "log");

  greet("World");

  assertSpyCalls(logger, 1);
  logger.restore();
});

Deno.test("stub external dependency", () => {
  const fetchStub = stub(globalThis, "fetch", () =>
    Promise.resolve(new Response(JSON.stringify({ status: "ok" })))
  );

  try {
    // Test code that calls fetch
  } finally {
    fetchStub.restore();
  }
});
```

### Using @std/testing/time

```typescript
import { FakeTime } from "jsr:@std/testing/time";

Deno.test("time-dependent code", () => {
  using time = new FakeTime(new Date("2026-01-01"));

  assertEquals(new Date().getFullYear(), 2026);

  time.tick(86400000); // Advance 1 day
  assertEquals(new Date().getDate(), 2);
});
```

## Snapshot Testing

```typescript
import { assertSnapshot } from "jsr:@std/testing/snapshot";

Deno.test("snapshot test", async (t) => {
  const result = generateReport({ users: 100, active: 85 });
  await assertSnapshot(t, result);
});
```

Run with `--update` to create/update snapshots:

```bash
deno test --allow-all -- --update
```

Snapshots are stored in `__snapshots__/` directories alongside test files.

## Running Tests

```bash
# All tests in current directory
deno test

# With permissions
deno test --allow-all

# Specific file
deno test tests/auth_test.ts

# Filter by test name
deno test --filter "user creation"

# Regex filter
deno test --filter "/^database.*insert/"

# Watch mode
deno test --watch

# Parallel execution
deno test --parallel

# Only tests related to changed files (git)
deno test --changed

# Related to a specific file
deno test --related=src/auth.ts

# Fail on first error
deno test --fail-fast

# Reporter formats
deno test --reporter=pretty   # Default
deno test --reporter=dot      # Compact
deno test --reporter=junit    # CI/CD
deno test --reporter=tap      # TAP format

# Test sharding (split across CI runners)
deno test --shard=1/4
deno test --shard=2/4
```

### Test File Discovery

Deno discovers test files matching these patterns:
- `*_test.ts`, `*_test.js`, `*_test.tsx`, `*_test.jsx`
- `*.test.ts`, `*.test.js`, `*.test.tsx`, `*.test.jsx`
- Files in `__tests__/` directories

## Coverage

```bash
# Collect coverage data
deno test --coverage=./coverage

# Print summary
deno coverage ./coverage

# Generate LCOV report
deno coverage ./coverage --lcov > lcov.info

# Generate HTML report
deno coverage ./coverage --html

# Exclude patterns
deno coverage ./coverage --exclude="test|fixtures"
```

## Documentation Tests

Run code examples from JSDoc comments with `deno test --doc mod.ts`. Fenced code blocks in JSDoc `/** */` comments are executed as tests.

## Test Sanitizers

Deno detects leaked resources and incomplete async ops by default:
- **Op sanitizer** (`sanitizeOps: true`) — catches `setTimeout` without cleanup
- **Resource sanitizer** (`sanitizeResources: true`) — catches unclosed files/connections
- **Exit sanitizer** (`sanitizeExit: true`) — catches unexpected `Deno.exit()`

Disable per-test when needed:

```typescript
Deno.test({ name: "background task", sanitizeOps: false, sanitizeResources: false, fn() {} });
```

## Common Pitfalls

1. **Missing permissions for test files** — use `deno test --allow-read` if tests read fixtures
2. **Leaking async ops** — the op sanitizer catches `setTimeout` without cleanup
3. **Leaking resources** — always close files, connections in tests
4. **Test isolation** — tests in the same file share global state; use hooks for cleanup
5. **Snapshot update** — remember to pass `-- --update` (note the double dash separator)
6. **Test.only in CI** — fails if committed; use only during development
