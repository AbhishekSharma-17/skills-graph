# Mocking

> Source: [vitest.dev/api/mock](https://vitest.dev/api/mock.html) | [vitest.dev/guide/mocking](https://vitest.dev/guide/mocking.html) | Version: 4.x

## Table of Contents

- [Mock Functions](#mock-functions)
- [Spying on Methods](#spying-on-methods)
- [Module Mocking](#module-mocking)
- [Partial Module Mocking](#partial-module-mocking)
- [Hoisting and vi.hoisted](#hoisting-and-vihoisted)
- [Auto-Mocking](#auto-mocking)
- [Class Mocking](#class-mocking)
- [Mock Implementations](#mock-implementations)
- [Mock Return Values](#mock-return-values)
- [Mock State & Properties](#mock-state--properties)
- [Clearing and Resetting](#clearing-and-resetting)
- [Global and Environment Mocking](#global-and-environment-mocking)
- [Common Patterns](#common-patterns)

---

## Mock Functions

### vi.fn()

Create a standalone mock function:

```typescript
import { vi, expect, test } from 'vitest'

const getPrice = vi.fn((product: string) => {
  switch (product) {
    case 'apple': return 1.50
    case 'banana': return 0.75
    default: return 0
  }
})

test('mock function tracks calls', () => {
  getPrice('apple')
  getPrice('banana')

  expect(getPrice).toHaveBeenCalledTimes(2)
  expect(getPrice).toHaveBeenCalledWith('apple')
  expect(getPrice).toHaveReturnedWith(1.50)
})
```

### Empty Mock

```typescript
const callback = vi.fn() // returns undefined by default
callback(1, 2, 3)
expect(callback).toHaveBeenCalledWith(1, 2, 3)
```

## Spying on Methods

### vi.spyOn()

Track calls to existing object methods without replacing them:

```typescript
const cart = {
  getTotal() { return 100 },
}

const spy = vi.spyOn(cart, 'getTotal')
cart.getTotal()

expect(spy).toHaveBeenCalled()
expect(spy).toHaveReturnedWith(100)

spy.mockRestore() // restore original
```

### Spy on Getters/Setters

```typescript
const user = {
  _name: 'Alice',
  get name() { return this._name },
  set name(v) { this._name = v },
}

const getSpy = vi.spyOn(user, 'name', 'get')
const setSpy = vi.spyOn(user, 'name', 'set')

user.name           // triggers getter spy
user.name = 'Bob'   // triggers setter spy

expect(getSpy).toHaveBeenCalled()
expect(setSpy).toHaveBeenCalledWith('Bob')
```

## Module Mocking

### vi.mock()

Replace an entire module. **Hoisted to the top of the file** automatically:

```typescript
import { vi, test, expect } from 'vitest'
import { readFile } from './file-utils'

vi.mock('./file-utils', () => ({
  readFile: vi.fn(() => 'mocked content'),
}))

test('uses mocked module', () => {
  expect(readFile('test.txt')).toBe('mocked content')
})
```

### Dynamic Import Syntax

Use `import()` for type safety:

```typescript
vi.mock(import('./file-utils'), () => ({
  readFile: vi.fn(() => 'mocked content'),
}))
```

### vi.doMock() — Non-Hoisted

For mocks that need access to outer variables:

```typescript
let mockValue = 'initial'

vi.doMock('./config', () => ({
  getValue: () => mockValue,
}))

test('can change mock between tests', async () => {
  mockValue = 'updated'
  const { getValue } = await import('./config')
  expect(getValue()).toBe('updated')
})
```

### Unmocking

```typescript
vi.unmock('./file-utils')   // hoisted
vi.doUnmock('./file-utils') // non-hoisted
```

## Partial Module Mocking

Keep original implementations while mocking specific exports:

```typescript
vi.mock(import('./math-utils'), async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    complexCalculation: vi.fn(() => 42), // only mock this one
  }
})
```

### vi.importActual()

Import original module inside a mock factory:

```typescript
vi.mock('./utils', async () => {
  const actual = await vi.importActual('./utils')
  return {
    ...actual,
    fetchData: vi.fn(),
  }
})
```

## Hoisting and vi.hoisted

`vi.mock()` calls are hoisted to the top of the file, so they cannot reference variables defined later. Use `vi.hoisted()` to define values that are available during hoisting:

```typescript
const { mockFetch } = vi.hoisted(() => ({
  mockFetch: vi.fn(),
}))

vi.mock('./api', () => ({
  fetch: mockFetch,
}))

test('uses hoisted mock', () => {
  mockFetch.mockReturnValue({ data: 'test' })
  // ...
})
```

## Auto-Mocking

Without a factory, `vi.mock()` auto-mocks all exports:

```typescript
vi.mock('./user-service')
// All exports become vi.fn() returning undefined
// Original types are preserved for TypeScript
```

### vi.importMock()

Import a module with all exports auto-mocked:

```typescript
const mockedModule = await vi.importMock('./utils')
```

## Class Mocking

```typescript
vi.mock(import('./logger'), () => {
  const Logger = vi.fn(class MockLogger {
    log = vi.fn()
    error = vi.fn()
    warn = vi.fn()
  })
  return { Logger }
})

test('mocked class', () => {
  const logger = new Logger()
  logger.log('test')
  expect(logger.log).toHaveBeenCalledWith('test')
})
```

## Mock Implementations

```typescript
const fn = vi.fn()

fn.mockImplementation((x: number) => x * 2)
expect(fn(5)).toBe(10)

fn.mockImplementationOnce((x: number) => x * 3)
expect(fn(5)).toBe(15) // first call: x3
expect(fn(5)).toBe(10) // falls back to default: x2
```

### Temporary Implementation

```typescript
fn.withImplementation(
  (x: number) => x * 100,
  () => {
    expect(fn(2)).toBe(200) // temporary
  },
)
expect(fn(2)).toBe(4) // restored
```

### Async withImplementation

```typescript
await fn.withImplementation(
  async () => 'temp',
  async () => {
    expect(await fn()).toBe('temp')
  },
)
```

## Mock Return Values

```typescript
const fn = vi.fn()

fn.mockReturnValue(42)
expect(fn()).toBe(42)

fn.mockReturnValueOnce(1)
  .mockReturnValueOnce(2)
  .mockReturnValueOnce(3)
expect(fn()).toBe(1)
expect(fn()).toBe(2)
expect(fn()).toBe(3)
expect(fn()).toBe(42) // falls back to mockReturnValue

fn.mockReturnThis() // returns `this`
```

### Async Return Values

```typescript
fn.mockResolvedValue({ data: 'ok' })
await expect(fn()).resolves.toEqual({ data: 'ok' })

fn.mockResolvedValueOnce('first')
fn.mockRejectedValue(new Error('fail'))
fn.mockRejectedValueOnce(new Error('once'))
```

### Error Throwing (v4.1.0+)

```typescript
fn.mockThrow(new Error('always throws'))
fn.mockThrowOnce(new Error('throws once'))
```

## Mock State & Properties

```typescript
const fn = vi.fn()
fn('a', 'b')
fn('c')

fn.mock.calls        // [['a', 'b'], ['c']]
fn.mock.lastCall     // ['c']
fn.mock.results      // [{ type: 'return', value: undefined }, ...]
fn.mock.settledResults // for async: [{ type: 'fulfilled', value: ... }]
fn.mock.instances    // array of `this` for `new fn()`
fn.mock.contexts     // array of `this` for regular calls
fn.mock.invocationCallOrder // [1, 2] — global call order
```

### Mock Name

```typescript
fn.mockName('myMock')
fn.getMockName()         // 'myMock'
fn.getMockImplementation() // returns current impl or undefined
```

## Clearing and Resetting

| Method | Clears History | Resets Impl | Restores Original |
|--------|---------------|-------------|-------------------|
| `mockClear()` | Yes | No | No |
| `mockReset()` | Yes | Yes | No |
| `mockRestore()` | Yes | Yes | Yes (for spyOn) |

```typescript
// Per mock
fn.mockClear()
fn.mockReset()
fn.mockRestore()

// All mocks at once
vi.clearAllMocks()
vi.resetAllMocks()
vi.restoreAllMocks()
```

### Auto-Reset in Config

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    clearMocks: true,    // clearAllMocks before each test
    mockReset: true,     // resetAllMocks before each test
    restoreMocks: true,  // restoreAllMocks before each test
  },
})
```

## Global and Environment Mocking

### Stub Globals

```typescript
vi.stubGlobal('__VERSION__', '2.0.0')
expect(globalThis.__VERSION__).toBe('2.0.0')

vi.unstubAllGlobals() // restore all
```

### Stub Environment Variables

```typescript
vi.stubEnv('API_KEY', 'test-key-123')
expect(import.meta.env.API_KEY).toBe('test-key-123')
expect(process.env.API_KEY).toBe('test-key-123')

vi.unstubAllEnvs() // restore all
```

### Auto-Restore Config

```typescript
export default defineConfig({
  test: {
    unstubGlobals: true,
    unstubEnvs: true,
  },
})
```

## Common Patterns

### Mock Fetch

```typescript
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

mockFetch.mockResolvedValue({
  ok: true,
  json: () => Promise.resolve({ data: 'test' }),
})

test('fetches data', async () => {
  const response = await fetch('/api/data')
  const data = await response.json()
  expect(data).toEqual({ data: 'test' })
})
```

### Mock File System

Use `memfs` or similar for filesystem mocking:

```typescript
vi.mock('node:fs', async () => {
  const memfs = await vi.importActual('memfs')
  return memfs.fs
})

vi.mock('node:fs/promises', async () => {
  const memfs = await vi.importActual('memfs')
  return memfs.fs.promises
})
```

### Type-Safe Mocks

```typescript
import type { UserService } from './user-service'

const mockService = vi.mocked<UserService>({
  getUser: vi.fn(),
  createUser: vi.fn(),
} as UserService)
```

---

**Related:** [04-timers-dates.md](04-timers-dates.md) for timer mocking, [02-assertions.md](02-assertions.md) for mock matchers
