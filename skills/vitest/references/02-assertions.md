# Assertions & Matchers

> Source: [vitest.dev/api/expect](https://vitest.dev/api/expect.html) | Version: 4.x

## Table of Contents

- [Basic Usage](#basic-usage)
- [Equality Matchers](#equality-matchers)
- [Truthiness Matchers](#truthiness-matchers)
- [Numeric Matchers](#numeric-matchers)
- [String & Pattern Matchers](#string--pattern-matchers)
- [Collection Matchers](#collection-matchers)
- [Object Matchers](#object-matchers)
- [Type Matchers](#type-matchers)
- [Error Matchers](#error-matchers)
- [Mock/Spy Matchers](#mockspy-matchers)
- [Promise Matchers](#promise-matchers)
- [Asymmetric Matchers](#asymmetric-matchers)
- [Soft Assertions](#soft-assertions)
- [Polling Assertions](#polling-assertions)
- [Assertion Counting](#assertion-counting)
- [Custom Matchers](#custom-matchers)

---

## Basic Usage

```typescript
import { expect, test } from 'vitest'

test('basic assertion', () => {
  expect(value).toBe(expected)
})
```

Use `.not` to negate any matcher:

```typescript
expect(value).not.toBe(other)
```

## Equality Matchers

### toBe

Strict equality using `Object.is()`. Use for primitives and reference checks:

```typescript
expect(1 + 1).toBe(2)
expect('hello').toBe('hello')

const obj = { a: 1 }
expect(obj).toBe(obj) // same reference
```

### toEqual

Deep equality. Ignores `undefined` properties and array holes:

```typescript
expect({ a: 1, b: { c: 2 } }).toEqual({ a: 1, b: { c: 2 } })
expect([1, , 3]).toEqual([1, undefined, 3]) // sparse arrays match
```

### toStrictEqual

Stricter deep equality. Checks property types, `undefined` properties, and array sparseness:

```typescript
expect({ a: 1 }).not.toStrictEqual({ a: 1, b: undefined })
expect([1, , 3]).not.toStrictEqual([1, undefined, 3])
```

### toBeCloseTo

Compare floating-point numbers with precision:

```typescript
expect(0.1 + 0.2).toBeCloseTo(0.3, 5) // 5 decimal places
expect(0.1 + 0.2).not.toBe(0.3) // would fail with toBe
```

## Truthiness Matchers

```typescript
expect(true).toBeTruthy()
expect(0).toBeFalsy()
expect(null).toBeNull()
expect(undefined).toBeUndefined()
expect(1).toBeDefined()
expect(null).toBeNullable()     // null or undefined
expect(NaN).toBeNaN()
```

## Numeric Matchers

```typescript
expect(10).toBeGreaterThan(5)
expect(10).toBeGreaterThanOrEqual(10)
expect(5).toBeLessThan(10)
expect(5).toBeLessThanOrEqual(5)
```

## String & Pattern Matchers

### toMatch

Match strings or regex:

```typescript
expect('hello world').toMatch('hello')
expect('hello world').toMatch(/^hello/)
```

## Collection Matchers

### toContain

Check array items, string substrings, or DOM containment:

```typescript
expect([1, 2, 3]).toContain(2)
expect('hello world').toContain('world')
expect(new Set([1, 2])).toContain(1)
```

### toContainEqual

Deep equality for array items:

```typescript
expect([{ a: 1 }, { b: 2 }]).toContainEqual({ a: 1 })
```

### toHaveLength

```typescript
expect([1, 2, 3]).toHaveLength(3)
expect('hello').toHaveLength(5)
```

## Object Matchers

### toHaveProperty

Check property existence with optional value:

```typescript
const user = { name: 'Alice', address: { city: 'NYC' } }

expect(user).toHaveProperty('name')
expect(user).toHaveProperty('name', 'Alice')
expect(user).toHaveProperty('address.city', 'NYC')
expect(user).toHaveProperty(['address', 'city'], 'NYC')
```

### toMatchObject

Partial object matching:

```typescript
expect({ a: 1, b: 2, c: 3 }).toMatchObject({ a: 1, b: 2 })

expect([{ a: 1 }, { b: 2 }]).toMatchObject([{ a: 1 }])
```

### toBeOneOf

Match any value in a set:

```typescript
expect(result.status).toBeOneOf(['active', 'pending'])
```

## Type Matchers

```typescript
expect(42).toBeTypeOf('number')
expect('hello').toBeTypeOf('string')
expect(true).toBeTypeOf('boolean')
expect({}).toBeTypeOf('object')
expect(() => {}).toBeTypeOf('function')
expect(undefined).toBeTypeOf('undefined')
expect(Symbol()).toBeTypeOf('symbol')
expect(1n).toBeTypeOf('bigint')

expect(new Date()).toBeInstanceOf(Date)
expect(new Error()).toBeInstanceOf(Error)
```

## Error Matchers

### toThrow

Assert function throws:

```typescript
expect(() => { throw new Error('fail') }).toThrow()
expect(() => { throw new Error('fail') }).toThrow('fail')
expect(() => { throw new Error('fail') }).toThrow(/fail/)
expect(() => { throw new Error('fail') }).toThrow(Error)
```

## Mock/Spy Matchers

### Call Assertions

```typescript
const fn = vi.fn()
fn('hello', 'world')
fn('foo')

expect(fn).toHaveBeenCalled()
expect(fn).toHaveBeenCalledTimes(2)
expect(fn).toHaveBeenCalledWith('hello', 'world')
expect(fn).toHaveBeenLastCalledWith('foo')
expect(fn).toHaveBeenNthCalledWith(1, 'hello', 'world')
expect(fn).toHaveBeenCalledExactlyOnceWith('hello', 'world') // fails: called 2x
```

### Call Order Assertions

```typescript
const fn1 = vi.fn()
const fn2 = vi.fn()
fn1()
fn2()

expect(fn1).toHaveBeenCalledBefore(fn2)
expect(fn2).toHaveBeenCalledAfter(fn1)
```

### Return Value Assertions

```typescript
const fn = vi.fn(() => 42)
fn()

expect(fn).toHaveReturned()
expect(fn).toHaveReturnedTimes(1)
expect(fn).toHaveReturnedWith(42)
expect(fn).toHaveLastReturnedWith(42)
expect(fn).toHaveNthReturnedWith(1, 42)
```

### Async Return Assertions

```typescript
const fn = vi.fn(async () => 'data')
await fn()

expect(fn).toHaveResolved()
expect(fn).toHaveResolvedTimes(1)
expect(fn).toHaveResolvedWith('data')
```

## Promise Matchers

### resolves / rejects

Unwrap promises for assertion:

```typescript
await expect(Promise.resolve(42)).resolves.toBe(42)
await expect(Promise.reject(new Error('fail'))).rejects.toThrow('fail')
```

## Asymmetric Matchers

Use as expected values for partial matching:

```typescript
expect(fn).toHaveBeenCalledWith(
  expect.stringContaining('hello'),
  expect.any(Number),
)

expect({ name: 'Alice', id: 123 }).toEqual({
  name: expect.stringMatching(/^Ali/),
  id: expect.any(Number),
})
```

### Available Asymmetric Matchers

| Matcher | Description |
|---------|-------------|
| `expect.anything()` | Matches anything except `null`/`undefined` |
| `expect.any(Constructor)` | Matches any instance of constructor |
| `expect.stringContaining(str)` | String includes substring |
| `expect.stringMatching(regex)` | String matches regex |
| `expect.arrayContaining(arr)` | Array includes all items |
| `expect.objectContaining(obj)` | Object has matching subset |
| `expect.closeTo(num, digits?)` | Float comparison in objects |
| `expect.toBeOneOf(values)` | Asymmetric variant of toBeOneOf |
| `expect.schemaMatching(schema)` | Standard Schema v1 validation |

## Soft Assertions

Continue test execution after failure, collecting all errors:

```typescript
test('soft assertions', () => {
  expect.soft(1).toBe(2) // records failure, continues
  expect.soft(2).toBe(3) // records failure, continues
  // test reports both failures
})
```

## Polling Assertions

Retry assertions until they pass (useful for async state):

```typescript
test('eventually resolves', async () => {
  await expect.poll(() => fetchStatus(), {
    interval: 100,  // ms between retries
    timeout: 5000,  // max wait time
  }).toBe('ready')
})
```

## Assertion Counting

Ensure the expected number of assertions ran:

```typescript
test('assertion count', () => {
  expect.assertions(2) // exactly 2 assertions must run
  expect(1).toBe(1)
  expect(2).toBe(2)
})

test('at least one', () => {
  expect.hasAssertions() // at least 1 assertion must run
  expect(true).toBeTruthy()
})
```

### expect.unreachable

Mark code paths that should never execute:

```typescript
test('switch coverage', () => {
  switch (status) {
    case 'ok': break
    case 'error': break
    default: expect.unreachable('unexpected status')
  }
})
```

## Custom Matchers

### Define Custom Matchers

```typescript
expect.extend({
  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling
    return {
      pass,
      message: () =>
        `expected ${received} to be within range ${floor} - ${ceiling}`,
    }
  },
})

test('custom matcher', () => {
  expect(100).toBeWithinRange(90, 110)
})
```

### TypeScript Declaration

```typescript
import type { Assertion, AsymmetricMatchersContaining } from 'vitest'

declare module 'vitest' {
  interface CustomMatchers<R = unknown> {
    toBeWithinRange(floor: number, ceiling: number): R
  }
}
```

### Custom Snapshot Serializers

```typescript
expect.addSnapshotSerializer({
  test(val) {
    return val && typeof val.toJSON === 'function'
  },
  serialize(val, config, indentation, depth, refs, printer) {
    return printer(val.toJSON(), config, indentation, depth, refs)
  },
})
```

### Custom Equality Testers

```typescript
expect.addEqualityTesters([
  function areDatesEqual(a, b) {
    if (a instanceof Date && b instanceof Date) {
      return a.getTime() === b.getTime()
    }
    return undefined // fall through to default
  },
])
```

---

**Related:** [01-writing-tests.md](01-writing-tests.md) for test API, [03-mocking.md](03-mocking.md) for mock matchers
