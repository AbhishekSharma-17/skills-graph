# Vitest — Overview & Setup

> Source: [vitest.dev/guide](https://vitest.dev/guide/) | Version: 4.x

## Table of Contents

- [What is Vitest](#what-is-vitest)
- [Why Vitest](#why-vitest)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Setup](#project-setup)
- [Configuration](#configuration)
- [Workspaces & Projects](#workspaces--projects)
- [IDE Integration](#ide-integration)
- [Migration from Jest](#migration-from-jest)

---

## What is Vitest

Vitest is a next-generation testing framework powered by Vite. It reuses Vite's configuration, transformers, resolvers, and plugins to provide a blazing-fast test runner with native ESM support, TypeScript/JSX out of the box, and a Jest-compatible API.

Key capabilities:
- Unit, integration, and component testing
- Browser mode for real-browser testing
- Benchmarking via Tinybench
- Type-level testing with `expectTypeOf`
- Coverage via v8 or Istanbul
- Snapshot testing (file, inline, ARIA)
- Watch mode with Vite-powered HMR

## Why Vitest

| Feature | Vitest | Jest |
|---------|--------|------|
| ESM support | Native, first-class | Experimental, requires config |
| TypeScript | Out of the box | Requires ts-jest or babel |
| Config reuse | Shares vite.config | Separate jest.config |
| Speed | Vite's transform pipeline | Slower cold starts |
| Browser testing | Built-in browser mode | Requires separate tools |
| Benchmarking | Built-in `bench` API | Not available |
| Type testing | Built-in `expectTypeOf` | Not available |

## Requirements

- **Node.js** >= v20.0.0
- **Vite** >= v6.0.0
- TypeScript >= 5.0 (optional, for type testing)

## Installation

```bash
# npm
npm install -D vitest

# yarn
yarn add -D vitest

# pnpm
pnpm add -D vitest

# bun
bun add -D vitest
```

Add the test script to `package.json`:

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage"
  }
}
```

## Project Setup

### Basic Example

```typescript
// src/math.ts
export function sum(a: number, b: number): number {
  return a + b
}
```

```typescript
// src/math.test.ts
import { expect, test } from 'vitest'
import { sum } from './math'

test('adds 1 + 2 to equal 3', () => {
  expect(sum(1, 2)).toBe(3)
})
```

```bash
npx vitest
```

### File Naming Conventions

Vitest looks for files matching these patterns by default:
- `**/*.test.{ts,tsx,js,jsx}`
- `**/*.spec.{ts,tsx,js,jsx}`
- `**/__tests__/**/*.{ts,tsx,js,jsx}`

## Configuration

Vitest reads from `vite.config.ts` by default. Add test-specific config in the `test` property:

```typescript
// vite.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

### Dedicated Config File

For projects where `vite.config.ts` should stay clean:

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    // test-specific options
  },
})
```

Vitest resolves config in this order:
1. `vitest.config.ts`
2. `vite.config.ts`
3. Inline CLI options

### Global API Injection

Enable Jest-like globals (no imports needed):

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    globals: true,
  },
})
```

```typescript
// tsconfig.json — add types for globals
{
  "compilerOptions": {
    "types": ["vitest/globals"]
  }
}
```

Now tests can use `describe`, `it`, `expect` without importing.

## Workspaces & Projects

Define multiple test projects with different configurations:

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: 'unit',
          include: ['src/**/*.test.ts'],
          environment: 'node',
        },
      },
      {
        test: {
          name: 'browser',
          include: ['src/**/*.browser.test.ts'],
          browser: {
            enabled: true,
            provider: 'playwright',
            instances: [{ browser: 'chromium' }],
          },
        },
      },
    ],
  },
})
```

Run a specific project:

```bash
npx vitest --project unit
```

## IDE Integration

### VS Code

Install the official [Vitest VS Code extension](https://marketplace.visualstudio.com/items?itemName=vitest.explorer) for:
- Test discovery and execution from the editor
- Inline test results and error highlighting
- Debug configuration
- Watch mode integration

### JetBrains

WebStorm and IntelliJ IDEA have built-in Vitest support since 2023.3.

## Migration from Jest

### Key Differences

| Jest | Vitest |
|------|--------|
| `jest.fn()` | `vi.fn()` |
| `jest.mock()` | `vi.mock()` |
| `jest.spyOn()` | `vi.spyOn()` |
| `jest.useFakeTimers()` | `vi.useFakeTimers()` |
| `jest.requireActual()` | `vi.importActual()` |
| `jest.requireMock()` | `vi.importMock()` |
| `@jest/globals` | `vitest` |

### Automating Migration

```bash
# Use codemod for automated migration
npx @vitest/codemod migrate-from-jest
```

### Common Pitfalls

- `vi.mock()` is hoisted but uses ESM semantics — factory cannot reference outer scope variables unless wrapped in `vi.hoisted()`
- Vitest uses real ESM by default; no `__esModule` property on mocked modules
- Snapshot format differs slightly (e.g., `printBasicPrototype` defaults to `false`)
- `done` callback is not supported — use async/await or return a promise

---

**Related:** [01-writing-tests.md](01-writing-tests.md) for test API, [03-mocking.md](03-mocking.md) for mocking patterns
