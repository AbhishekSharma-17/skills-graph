# Writing Tests

> Source: [vitest.dev/api](https://vitest.dev/api/) | Version: 4.x

## Table of Contents

- [Test Functions](#test-functions)
- [Describe Blocks](#describe-blocks)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Test Context](#test-context)
- [Fixtures with test.extend](#fixtures-with-testextend)
- [Parameterized Tests](#parameterized-tests)
- [Concurrent Tests](#concurrent-tests)
- [Test Modifiers](#test-modifiers)
- [Test Options](#test-options)
- [Benchmarking](#benchmarking)

---

## Test Functions

### Basic Test

```typescript
import { test, expect } from 'vitest'

test('should add numbers', () => {
  expect(1 + 1).toBe(2)
})
```

`it` is an alias for `test`:

```typescript
import { it, expect } from 'vitest'

it('should add numbers', () => {
  expect(1 + 1).toBe(2)
})
```

### Async Tests

```typescript
test('fetches user data', async () => {
  const user = await fetchUser(1)
  expect(user.name).toBe('Alice')
})
```

## Describe Blocks

Group related tests into suites:

```typescript
import { describe, it, expect } from 'vitest'

describe('Calculator', () => {
  describe('add', () => {
    it('adds positive numbers', () => {
      expect(add(1, 2)).toBe(3)
    })

    it('adds negative numbers', () => {
      expect(add(-1, -2)).toBe(-3)
    })
  })

  describe('multiply', () => {
    it('multiplies by zero', () => {
      expect(multiply(5, 0)).toBe(0)
    })
  })
})
```

### Nested Describe

Suites can be nested arbitrarily deep. Each level can have its own hooks.

## Lifecycle Hooks

```typescript
import { beforeAll, afterAll, beforeEach, afterEach } from 'vitest'

beforeAll(async () => {
  // Runs once before all tests in this file/suite
  await setupDatabase()
})

afterAll(async () => {
  // Runs once after all tests
  await teardownDatabase()
})

beforeEach(() => {
  // Runs before each test
  resetState()
})

afterEach(() => {
  // Runs after each test
  cleanupMocks()
})
```

### aroundEach and aroundAll (v4.1.0+)

Wrap test execution with setup/teardown in a single function:

```typescript
import { test } from 'vitest'

const myTest = test.extend({})

myTest.aroundEach(async (run) => {
  const conn = await openConnection()
  await run()
  await conn.close()
})
```

### Hook Execution Order

For nested suites:
1. Parent `beforeAll`
2. Child `beforeAll`
3. Parent `beforeEach`
4. Child `beforeEach`
5. **Test runs**
6. Child `afterEach`
7. Parent `afterEach`
8. Child `afterAll`
9. Parent `afterAll`

## Test Context

Each test receives a `TestContext` object:

```typescript
test('with context', (ctx) => {
  // ctx.task — current test task metadata
  // ctx.expect — scoped expect (required for concurrent snapshot tests)
  ctx.expect(1).toBe(1)
})
```

### Using Context for Concurrent Snapshots

Concurrent tests must use the scoped `expect` from context:

```typescript
test.concurrent('snapshot A', ({ expect }) => {
  expect({ name: 'Alice' }).toMatchSnapshot()
})

test.concurrent('snapshot B', ({ expect }) => {
  expect({ name: 'Bob' }).toMatchSnapshot()
})
```

## Fixtures with test.extend

Create reusable test fixtures (similar to Playwright's fixture model):

```typescript
import { test as base } from 'vitest'

interface MyFixtures {
  db: Database
  user: User
}

const test = base.extend<MyFixtures>({
  db: async ({}, use) => {
    const db = await createTestDb()
    await use(db)
    await db.close()
  },
  user: async ({ db }, use) => {
    const user = await db.createUser({ name: 'Test' })
    await use(user)
    await db.deleteUser(user.id)
  },
})

test('user has name', ({ user }) => {
  expect(user.name).toBe('Test')
})
```

### Fixture Override (v4.1.0+)

Override fixture values for specific suites:

```typescript
const adminTest = test.override({
  user: async ({ db }, use) => {
    const admin = await db.createUser({ name: 'Admin', role: 'admin' })
    await use(admin)
  },
})

adminTest('admin can delete', ({ user }) => {
  expect(user.role).toBe('admin')
})
```

### Scoped Hooks on Extended Tests

```typescript
test.beforeEach(({ db }) => {
  // has access to fixtures from test.extend
  db.beginTransaction()
})

test.afterEach(({ db }) => {
  db.rollbackTransaction()
})
```

## Parameterized Tests

### test.each

```typescript
test.each([
  [1, 1, 2],
  [1, 2, 3],
  [2, 2, 4],
])('add(%d, %d) = %d', (a, b, expected) => {
  expect(add(a, b)).toBe(expected)
})
```

### Template Literal Syntax

```typescript
test.each`
  a    | b    | expected
  ${1} | ${1} | ${2}
  ${1} | ${2} | ${3}
  ${2} | ${2} | ${4}
`('add($a, $b) = $expected', ({ a, b, expected }) => {
  expect(add(a, b)).toBe(expected)
})
```

### test.for (Alternative)

Provides access to `TestContext`:

```typescript
test.for([
  { input: 'hello', expected: 'HELLO' },
  { input: 'world', expected: 'WORLD' },
])('uppercase($input)', ({ input, expected }, { expect }) => {
  expect(input.toUpperCase()).toBe(expected)
})
```

### Format Specifiers

| Specifier | Description |
|-----------|-------------|
| `%s` | String |
| `%d` | Number |
| `%i` | Integer |
| `%f` | Float |
| `%j` | JSON |
| `%o` | Object |
| `%#` | 0-based index |
| `%$` | 1-based index |

## Concurrent Tests

Run tests in parallel within a suite:

```typescript
describe('database queries', () => {
  test.concurrent('query users', async () => {
    const users = await db.query('SELECT * FROM users')
    expect(users.length).toBeGreaterThan(0)
  })

  test.concurrent('query posts', async () => {
    const posts = await db.query('SELECT * FROM posts')
    expect(posts.length).toBeGreaterThan(0)
  })
})
```

Mark an entire suite as concurrent:

```typescript
describe.concurrent('parallel suite', () => {
  test('test A', async () => { /* ... */ })
  test('test B', async () => { /* ... */ })
})
```

### Sequential Override

Force sequential execution within a concurrent context:

```typescript
describe.concurrent('mostly parallel', () => {
  test('parallel test', async () => { /* ... */ })

  test.sequential('must run alone', async () => {
    // This test runs sequentially
  })
})
```

## Test Modifiers

```typescript
test.skip('skipped test', () => { /* ... */ })

test.skipIf(process.env.CI)('skip in CI', () => { /* ... */ })

test.runIf(process.env.CI)('only in CI', () => { /* ... */ })

test.only('focus on this test', () => { /* ... */ })

test.todo('implement later')

test.fails('known broken', () => {
  expect(brokenFunction()).toBe('correct')
})
```

### Dynamic Skip via Context

```typescript
test('conditionally skip', (ctx) => {
  if (someCondition) {
    ctx.skip()
  }
  // test body
})
```

## Test Options

```typescript
test('with options', {
  timeout: 10_000,
  retry: { count: 3, delay: 1000 },
  tags: ['slow', 'integration'],
  concurrent: true,
}, async () => {
  // test body
})
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `timeout` | `number` | 5000 | Milliseconds before timeout |
| `retry` | `number \| object` | 0 | Retry count with optional delay/condition |
| `repeats` | `number` | 0 | Run test N additional times |
| `tags` | `string[]` | `[]` | Custom tags for filtering |
| `meta` | `TaskMeta` | `{}` | Custom metadata for reporters |
| `concurrent` | `boolean` | `false` | Run in parallel |
| `sequential` | `boolean` | `false` | Force sequential |
| `skip` | `boolean` | `false` | Skip this test |
| `only` | `boolean` | `false` | Run exclusively |
| `fails` | `boolean` | `false` | Expect failure |

## Benchmarking

```typescript
import { bench, describe } from 'vitest'

describe('sorting algorithms', () => {
  bench('Array.sort', () => {
    const arr = [3, 1, 4, 1, 5, 9]
    arr.sort((a, b) => a - b)
  })

  bench('custom quicksort', () => {
    const arr = [3, 1, 4, 1, 5, 9]
    quickSort(arr)
  })
})
```

Run benchmarks:

```bash
npx vitest bench
```

### Bench Options

```typescript
bench('with options', () => { /* ... */ }, {
  time: 1000,       // ms to run benchmark
  iterations: 100,  // minimum iterations
  warmupTime: 500,  // warmup duration
  warmupIterations: 10,
  setup: (task) => { /* runs before each benchmark */ },
  teardown: (task) => { /* runs after each benchmark */ },
})
```

---

**Related:** [02-assertions.md](02-assertions.md) for matchers, [03-mocking.md](03-mocking.md) for mocking
