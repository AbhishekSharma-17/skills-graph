# Bun — Test Runner

> Source: [bun.sh/docs/cli/test](https://bun.sh/docs/cli/test)

## Table of Contents

- [Getting Started](#getting-started)
- [Test API](#test-api)
- [Common Matchers](#common-matchers)
- [Async Tests](#async-tests)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Mocking](#mocking)
- [Snapshot Testing](#snapshot-testing)
- [Test Filtering](#test-filtering)
- [Watch Mode](#watch-mode)
- [Code Coverage](#code-coverage)
- [DOM Testing](#dom-testing)
- [Timeouts](#timeouts)
- [GitHub Actions Integration](#github-actions-integration)
- [Migration from Jest and Vitest](#migration-from-jest-and-vitest)
- [Common Pitfalls](#common-pitfalls)

---

## Getting Started

Bun includes a built-in Jest-compatible test runner with no configuration required.

```bash
bun test                        # run all tests
bun test src/utils.test.ts      # specific file
bun test tests/                 # directory
```

Auto-discovered patterns: `*.test.ts`, `*.test.tsx`, `*.test.js`, `*.spec.ts`, `*.spec.tsx`, `__tests__/**/*.ts`.

---

## Test API

```typescript
import { describe, test, it, expect, beforeAll, afterAll } from "bun:test";

describe("Math operations", () => {
  test("addition", () => {
    expect(1 + 2).toBe(3);
  });

  it("subtraction", () => {   // test and it are aliases
    expect(5 - 3).toBe(2);
  });
});

// Nested describe
describe("UserService", () => {
  describe("create", () => {
    test("creates a user with valid data", () => { /* ... */ });
    test("rejects duplicate email", () => { /* ... */ });
  });
});
```

---

## Common Matchers

```typescript
// Equality
expect(value).toBe(expected);           // strict ===
expect(value).toEqual(expected);         // deep equality
expect(value).toStrictEqual(expected);   // deep + type check

// Truthiness
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeNull();
expect(value).toBeUndefined();
expect(value).toBeDefined();
expect(value).toBeNaN();

// Numbers
expect(value).toBeGreaterThan(3);
expect(value).toBeGreaterThanOrEqual(3);
expect(value).toBeLessThan(10);
expect(0.1 + 0.2).toBeCloseTo(0.3, 5);

// Strings
expect(str).toMatch(/regex/);
expect(str).toContain("substring");
expect(str).toStartWith("prefix");
expect(str).toEndWith("suffix");
expect(str).toHaveLength(5);

// Arrays
expect(arr).toContain(item);
expect(arr).toHaveLength(3);
expect(arr).toContainEqual({ id: 1 });  // deep equality check

// Objects
expect(obj).toHaveProperty("key");
expect(obj).toHaveProperty("key", "value");
expect(obj).toHaveProperty("nested.key");
expect(obj).toMatchObject({ name: "Alice" });  // partial match

// Exceptions
expect(() => dangerousCall()).toThrow();
expect(() => dangerousCall()).toThrow("specific message");
expect(() => dangerousCall()).toThrow(CustomError);

// Negation
expect(value).not.toBe(other);
expect(() => safeCall()).not.toThrow();
```

---

## Async Tests

```typescript
test("fetches data", async () => {
  const response = await fetch("https://api.example.com/data");
  const data = await response.json();
  expect(data).toHaveProperty("id");
});

test("promise resolves", async () => {
  await expect(fetchUser(1)).resolves.toEqual({ id: 1, name: "Alice" });
});

test("promise rejects", async () => {
  await expect(fetchUser(-1)).rejects.toThrow("Not found");
});
```

---

## Lifecycle Hooks

```typescript
import { describe, test, beforeAll, beforeEach, afterEach, afterAll } from "bun:test";

describe("Database tests", () => {
  beforeAll(async () => { await connectToDatabase(); });
  afterAll(async () => { await disconnectDatabase(); });
  beforeEach(async () => { await beginTransaction(); });
  afterEach(async () => { await rollbackTransaction(); });

  test("insert user", async () => {
    const user = await db.insert({ name: "Alice" });
    expect(user.id).toBeDefined();
  });
});
```

Nested execution order:
```
Parent beforeAll → Child beforeAll → Parent beforeEach → Child beforeEach
  → TEST → Child afterEach → Parent afterEach → Child afterAll → Parent afterAll
```

---

## Mocking

### mock() — Function Mocks

```typescript
import { test, expect, mock } from "bun:test";

const mockFn = mock(() => "default return");

test("mock function", () => {
  mockFn();
  mockFn("arg1");

  expect(mockFn).toHaveBeenCalled();
  expect(mockFn).toHaveBeenCalledTimes(2);
  expect(mockFn).toHaveBeenCalledWith("arg1");
});
```

### Mock Return Values

```typescript
const mockFn = mock();
mockFn.mockReturnValue("always this");
mockFn.mockReturnValueOnce("first call only");
mockFn.mockResolvedValue({ id: 1 });
mockFn.mockRejectedValue(new Error("fail"));
mockFn.mockImplementation((x: number) => x * 2);
```

### spyOn

```typescript
import { spyOn } from "bun:test";

const user = { getName() { return "Alice"; } };

test("spyOn", () => {
  const spy = spyOn(user, "getName").mockReturnValue("Bob");
  expect(user.getName()).toBe("Bob");
  expect(spy).toHaveBeenCalled();
  spy.mockRestore();
  expect(user.getName()).toBe("Alice");
});
```

### mock.module() — Module Mocking

```typescript
mock.module("./database", () => ({
  query: mock(() => [{ id: 1, name: "Alice" }]),
  connect: mock(() => Promise.resolve()),
}));

import { query } from "./database";

test("mocked module", () => {
  const result = query("SELECT * FROM users");
  expect(result).toEqual([{ id: 1, name: "Alice" }]);
});
```

### Clearing Mocks

```typescript
fn.mockClear();   // clear call history, keep implementation
fn.mockReset();   // clear history + reset implementation
fn.mockRestore(); // restore original (spyOn only)
```

---

## Snapshot Testing

```typescript
test("user object matches snapshot", () => {
  expect(getUser(1)).toMatchSnapshot();
});

test("inline snapshot", () => {
  expect(getGreeting("Alice")).toMatchInlineSnapshot(`"Hello, Alice!"`);
});
```

```bash
bun test --update-snapshots   # update outdated snapshots
```

Snapshots are stored in `__snapshots__/` next to the test file.

---

## Test Filtering

```bash
bun test --grep "user"            # by name
bun test --grep "/create|delete/" # regex
```

```typescript
test.only("only this runs", () => { /* ... */ });
test.skip("not ready yet", () => { /* ... */ });
describe.skip("entire suite skipped", () => { /* ... */ });
test.todo("implement pagination");
test.todo("handle rate limiting");

// Conditional
test.if(process.platform === "linux")("linux-only", () => { /* ... */ });
test.skipIf(process.env.CI)("skip in CI", () => { /* ... */ });
```

---

## Watch Mode

```bash
bun test --watch        # re-run on file changes
bun test --rerun-each   # re-run each test repeatedly
```

---

## Code Coverage

```bash
bun test --coverage
bun test --coverage --coverage-reporter=lcov
bun test --coverage --coverage-dir=./coverage
```

```toml
# bunfig.toml
[test]
coverage = true
coverageReporter = ["text", "lcov"]
coverageDir = "./coverage"
coverageThreshold = { line = 80, function = 80, statement = 80 }
```

---

## DOM Testing

```bash
bun add -d happy-dom
```

```toml
# bunfig.toml
[test]
preload = ["happy-dom"]
```

```typescript
test("DOM manipulation", () => {
  document.body.innerHTML = `<div id="app">Hello</div>`;
  const el = document.getElementById("app");

  expect(el).not.toBeNull();
  expect(el!.textContent).toBe("Hello");

  el!.textContent = "Updated";
  expect(el!.textContent).toBe("Updated");
});
```

---

## Timeouts

```typescript
test("slow operation", async () => {
  const result = await slowApiCall();
  expect(result).toBeDefined();
}, 10_000);  // 10 second timeout as second arg
```

```toml
# bunfig.toml — global timeout
[test]
timeout = 30000
```

Default timeout is 5 seconds per test.

---

## GitHub Actions Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest
      - run: bun install --frozen-lockfile
      - run: bun test
      - run: bun test --coverage --coverage-reporter=lcov
      - uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
```

Bun auto-detects GitHub Actions and adds inline failure annotations on PRs without extra configuration.

---

## Migration from Jest and Vitest

```typescript
// Before (Jest)
const { describe, test, expect } = require('@jest/globals');
// After (Bun)
import { describe, test, expect } from "bun:test";

// Before (Vitest)
import { describe, test, expect, vi } from "vitest";
const spy = vi.fn();
// After (Bun)
import { describe, test, expect, mock } from "bun:test";
const spy = mock();
```

### Key Differences from Jest

| Feature | Jest | Bun |
|---------|------|-----|
| Import | `@jest/globals` | `bun:test` |
| Config | `jest.config.ts` | `bunfig.toml` |
| Module mocking | `jest.mock()` | `mock.module()` |
| Timer mocking | `jest.useFakeTimers()` | `mock.setSystemTime()` |
| Run command | `npx jest` | `bun test` |

Most Jest features work out of the box: `describe`, `test`, `it`, `expect`, lifecycle hooks, matchers, `test.each`, `test.only`, `test.skip`, `mock()`, `spyOn()`, async tests.

---

## Common Pitfalls

**1. Forgetting bun:test import**: Unlike Jest with auto-globals, Bun requires explicit imports. Missing imports produce "describe is not defined" errors.

**2. Module mock hoisting**: `mock.module()` is hoisted to the top of the file. Place it before imports of the mocked module.

**3. Snapshot location**: Snapshots are in `__snapshots__/` next to the test file. Deleting this directory recreates all snapshots on the next run.

**4. Watch mode and mocks**: Module mocks persist between re-runs in watch mode. Restart the runner to clear the module cache.

**5. happy-dom not loaded**: DOM APIs like `document` are undefined unless `happy-dom` is configured in `bunfig.toml` preload.

**6. Timeout too short for integration tests**: The default 5-second timeout is insufficient for database or network tests. Set explicit timeouts or increase the global timeout in `bunfig.toml`.

**7. Coverage with dynamic imports**: Code loaded via dynamic `import()` may not appear in coverage reports. Prefer static imports for accurate coverage.

---

**Related:** [00-overview.md](00-overview.md) for CLI reference, [01-runtime-fundamentals.md](01-runtime-fundamentals.md) for module resolution
