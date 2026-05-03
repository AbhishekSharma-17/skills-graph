# Type Testing

> Source: [vitest.dev/guide/testing-types](https://vitest.dev/guide/testing-types.html) | Version: 4.x

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [expectTypeOf API](#expecttypeof-api)
- [assertType API](#asserttype-api)
- [Common Patterns](#common-patterns)
- [Error Message Interpretation](#error-message-interpretation)
- [Configuration](#configuration)
- [Best Practices](#best-practices)

---

## Overview

Vitest can test TypeScript types at compile time without executing any code. Type tests verify that your type definitions, generics, and inference work correctly.

Type test files use the `.test-d.ts` extension by default:

```
src/
  utils.ts
  utils.test.ts      # runtime tests
  utils.test-d.ts     # type tests
```

## Setup

### Enable Type Checking

```bash
# Via CLI flag
npx vitest --typecheck

# Type-only run
npx vitest --typecheck.only
```

### Configuration

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    typecheck: {
      enabled: true,
      checker: 'tsc',              // or 'vue-tsc' for Vue
      include: ['**/*.test-d.ts'],
      ignoreSourceErrors: false,    // also report source file errors
      tsconfig: './tsconfig.json',
    },
  },
})
```

### Package Script

```json
{
  "scripts": {
    "test:types": "vitest --typecheck.only",
    "test:all": "vitest --typecheck"
  }
}
```

## expectTypeOf API

### Basic Type Assertions

```typescript
import { expectTypeOf, test } from 'vitest'

test('string type', () => {
  expectTypeOf('hello').toBeString()
  expectTypeOf(42).toBeNumber()
  expectTypeOf(true).toBeBoolean()
  expectTypeOf(null).toBeNull()
  expectTypeOf(undefined).toBeUndefined()
  expectTypeOf({}).toBeObject()
  expectTypeOf(() => {}).toBeFunction()
  expectTypeOf(Symbol()).toBeSymbol()
})
```

### Equality Assertions

```typescript
test('type equality', () => {
  expectTypeOf<string>().toEqualTypeOf<string>()
  expectTypeOf<{ a: string }>().toEqualTypeOf<{ a: string }>()

  // Not equal — different properties
  expectTypeOf<{ a: string }>().not.toEqualTypeOf<{ b: string }>()
})
```

### Matching (Broader)

```typescript
test('type matching', () => {
  // toMatchTypeOf checks assignability (subset)
  expectTypeOf<{ a: string; b: number }>()
    .toMatchTypeOf<{ a: string }>()

  // string extends string | number
  expectTypeOf<string>().toExtend<string | number>()
})
```

### Function Type Assertions

```typescript
import { mount } from './component'

test('function signatures', () => {
  expectTypeOf(mount).toBeFunction()
  expectTypeOf(mount).toBeCallableWith({ name: 'App' })

  // Parameter types
  expectTypeOf(mount).parameter(0).toEqualTypeOf<{ name: string }>()

  // Parameters tuple
  expectTypeOf(mount).parameters.toEqualTypeOf<[{ name: string }]>()

  // Return type
  expectTypeOf(mount).returns.toEqualTypeOf<Component>()
})
```

### Constructor Assertions

```typescript
test('class constructors', () => {
  expectTypeOf(Date).toBeConstructibleWith('2026-01-01')
  expectTypeOf(Date).constructorParameters.toEqualTypeOf<[string | number]>()
  expectTypeOf(Date).instance.toHaveProperty('getTime')
})
```

### Property Assertions

```typescript
test('object properties', () => {
  const user = { name: 'Alice', age: 30 }

  expectTypeOf(user).toHaveProperty('name')
  expectTypeOf(user).toHaveProperty('age')
  expectTypeOf(user).not.toHaveProperty('email')
})
```

### Array & Promise Types

```typescript
test('array items', () => {
  expectTypeOf([1, 2, 3]).items.toBeNumber()
  expectTypeOf(['a', 'b']).items.toBeString()
})

test('promise resolution', () => {
  expectTypeOf(Promise.resolve('hello')).resolves.toBeString()
})
```

### Branded Types

```typescript
test('branded types', () => {
  type UserId = string & { __brand: 'UserId' }
  expectTypeOf<UserId>().branded.toEqualTypeOf<'UserId'>()
})
```

## assertType API

Simpler type assertions using `@ts-expect-error`:

```typescript
import { assertType, test } from 'vitest'

test('assert types', () => {
  const answer = 42

  assertType<number>(answer)

  // @ts-expect-error answer is not a string
  assertType<string>(answer)
})
```

`assertType` is useful when you primarily want to verify that TypeScript catches errors.

## Common Patterns

### Testing Generic Functions

```typescript
test('identity preserves type', () => {
  function identity<T>(x: T): T { return x }

  expectTypeOf(identity('hello')).toBeString()
  expectTypeOf(identity(42)).toBeNumber()
  expectTypeOf(identity({ a: 1 })).toEqualTypeOf<{ a: number }>()
})
```

### Testing Utility Types

```typescript
test('Readonly utility', () => {
  type User = { name: string; age: number }
  type ReadonlyUser = Readonly<User>

  expectTypeOf<ReadonlyUser>().toEqualTypeOf<{
    readonly name: string
    readonly age: number
  }>()
})
```

### Testing Discriminated Unions

```typescript
type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: Error }

test('discriminated union', () => {
  expectTypeOf<Result<string>>().toMatchTypeOf<{ ok: boolean }>()

  const success: Result<string> = { ok: true, data: 'hello' }
  if (success.ok) {
    expectTypeOf(success.data).toBeString()
  }
})
```

### Testing Overloaded Functions

```typescript
test('overloaded function', () => {
  function parse(input: string): object
  function parse(input: string, reviver: Function): object
  function parse(input: string, reviver?: Function) {
    return JSON.parse(input, reviver as any)
  }

  expectTypeOf(parse).toBeCallableWith('{}')
  expectTypeOf(parse).toBeCallableWith('{}', () => {})
})
```

### Testing Inferred Types

```typescript
test('inferred return type', () => {
  const createUser = (name: string, age: number) => ({ name, age, id: crypto.randomUUID() })

  type User = ReturnType<typeof createUser>

  expectTypeOf<User>().toEqualTypeOf<{
    name: string
    age: number
    id: string
  }>()
})
```

## Error Message Interpretation

When type assertions fail, TypeScript displays constraint violations. For example:

```
Type 'string' does not satisfy the constraint '{ Expected: number; Actual: string }'
```

This means: expected `number` but got `string`. Vitest uses `MismatchInfo` types to produce clear error messages.

**Tip:** Use type arguments instead of values for clearer errors:

```typescript
// Clearer error messages
expectTypeOf<string>().toEqualTypeOf<number>()

// Less clear (inferred types)
expectTypeOf('hello').toEqualTypeOf(42)
```

## Configuration

```typescript
export default defineConfig({
  test: {
    typecheck: {
      enabled: true,
      checker: 'tsc',                    // 'tsc' | 'vue-tsc'
      include: ['**/*.test-d.ts'],
      exclude: ['node_modules'],
      allowJs: false,
      ignoreSourceErrors: false,
      tsconfig: './tsconfig.json',
    },
  },
})
```

### Running Alongside Runtime Tests

```bash
# Run both runtime and type tests
npx vitest --typecheck

# Run only type tests
npx vitest --typecheck.only
```

### CLI Flags with Type Tests

These CLI flags work with type testing:
- `--allowOnly` — allow `.only` tests
- `-t` — filter by test name
- `--typecheck.checker` — select checker

## Best Practices

1. **Separate type tests** — use `.test-d.ts` extension for clarity
2. **Test public API types** — focus on what consumers see
3. **Use type arguments** — clearer error messages than inferred types
4. **Leverage typeof** — for complex inferred types from functions
5. **Include in test:include** — ensure `@ts-expect-error` typos are caught
6. **Don't over-test** — skip obvious type checks; focus on tricky generics and inference

---

**Related:** [01-writing-tests.md](01-writing-tests.md) for runtime tests, [00-overview.md](00-overview.md) for setup
