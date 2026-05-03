# Advanced Patterns

> Source: [vitest.dev/guide](https://vitest.dev/guide/) | Version: 4.x

## Table of Contents

- [Test Projects](#test-projects)
- [Parallelism & Performance](#parallelism--performance)
- [In-Source Testing](#in-source-testing)
- [Debugging Tests](#debugging-tests)
- [waitFor and waitUntil](#waitfor-and-waituntil)
- [Setup Files](#setup-files)
- [Global Setup](#global-setup)
- [Test Tags](#test-tags)
- [Sequence Control](#sequence-control)
- [OpenTelemetry Integration](#opentelemetry-integration)
- [Common Recipes](#common-recipes)

---

## Test Projects

Run multiple test configurations in a single Vitest instance:

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: 'unit',
          include: ['src/**/*.unit.test.ts'],
          environment: 'node',
        },
      },
      {
        test: {
          name: 'integration',
          include: ['src/**/*.int.test.ts'],
          environment: 'node',
          testTimeout: 30_000,
        },
      },
      {
        test: {
          name: 'components',
          include: ['src/**/*.component.test.tsx'],
          environment: 'jsdom',
          setupFiles: ['./src/test/dom-setup.ts'],
        },
      },
    ],
  },
})
```

### Run Specific Project

```bash
npx vitest --project unit
npx vitest --project unit --project integration
```

### Using Workspace Files

```typescript
// vitest.workspace.ts
import { defineWorkspace } from 'vitest/config'

export default defineWorkspace([
  'packages/*/vitest.config.ts',
  {
    test: {
      name: 'shared',
      include: ['shared/**/*.test.ts'],
    },
  },
])
```

## Parallelism & Performance

### File Parallelism

By default, test files run in parallel. Disable for resource-heavy tests:

```typescript
export default defineConfig({
  test: {
    fileParallelism: false, // run files sequentially
  },
})
```

### Worker Pool

```typescript
export default defineConfig({
  test: {
    pool: 'threads',    // 'threads' | 'forks' | 'vmThreads'
    maxWorkers: 4,      // limit worker count
  },
})
```

| Pool | Isolation | Speed | Memory |
|------|-----------|-------|--------|
| `threads` | Worker threads | Fast | Shared |
| `forks` | Child processes | Moderate | Separate |
| `vmThreads` | VM contexts | Moderate | Shared |

### Concurrent Tests

```typescript
describe.concurrent('parallel tests', () => {
  test('A', async () => { /* ... */ })
  test('B', async () => { /* ... */ })
  test('C', async () => { /* ... */ })
})
```

### Bail on Failure

Stop after N failures:

```bash
npx vitest --bail 1   # stop after first failure
npx vitest --bail 5   # stop after 5 failures
```

## In-Source Testing

Write tests alongside your source code:

```typescript
// src/math.ts
export function add(a: number, b: number): number {
  return a + b
}

if (import.meta.vitest) {
  const { test, expect } = import.meta.vitest

  test('add', () => {
    expect(add(1, 2)).toBe(3)
    expect(add(-1, 1)).toBe(0)
  })
}
```

### Enable In-Source Testing

```typescript
// vitest.config.ts
export default defineConfig({
  define: {
    'import.meta.vitest': 'undefined', // tree-shake in production
  },
  test: {
    includeSource: ['src/**/*.ts'],
  },
})
```

### TypeScript Declaration

```typescript
// src/env.d.ts
/// <reference types="vitest/importMeta" />
```

### Benefits

- Tests live next to code — easy to find and maintain
- Tree-shaken out of production builds
- Fast feedback during development

## Debugging Tests

### Node.js Inspector

```bash
npx vitest --inspect              # attach debugger
npx vitest --inspectBrk           # break before first test
```

Then attach from VS Code or Chrome DevTools.

### VS Code Launch Config

```json
{
  "type": "node",
  "request": "launch",
  "name": "Debug Vitest",
  "program": "${workspaceFolder}/node_modules/vitest/vitest.mjs",
  "args": ["--run", "--reporter", "verbose"],
  "console": "integratedTerminal"
}
```

### Debug Single Test

```bash
npx vitest --inspect-brk --run -t "specific test name"
```

### Vitest UI

Visual test runner with built-in debugging:

```bash
npm install -D @vitest/ui
npx vitest --ui
```

Opens a browser dashboard showing test results, source code, and module graph.

## waitFor and waitUntil

### vi.waitFor

Retry a callback until it succeeds:

```typescript
import { vi, test, expect } from 'vitest'

test('eventually succeeds', async () => {
  let count = 0
  const increment = () => { count++ }
  setInterval(increment, 100)

  await vi.waitFor(() => {
    expect(count).toBeGreaterThan(5)
  }, {
    timeout: 2000,  // max wait time
    interval: 50,   // retry interval
  })
})
```

### vi.waitUntil

Like `waitFor` but stops immediately on error (doesn't retry on throws):

```typescript
test('wait for condition', async () => {
  const result = await vi.waitUntil(
    () => checkServiceReady(),
    { timeout: 5000, interval: 200 },
  )
  expect(result).toBeTruthy()
})
```

### Difference

| Method | On Error | On Falsy Return |
|--------|----------|-----------------|
| `waitFor` | Retries | Retries |
| `waitUntil` | Throws immediately | Retries |

## Setup Files

Run before each test file:

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

```typescript
// src/test/setup.ts
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})

// Extend expect
expect.extend({
  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling
    return { pass, message: () => `expected ${received} within [${floor}, ${ceiling}]` }
  },
})
```

## Global Setup

Run once before all test files (and once after):

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    globalSetup: ['./src/test/global-setup.ts'],
  },
})
```

```typescript
// src/test/global-setup.ts
import type { GlobalSetupContext } from 'vitest/node'

export default async function setup({ provide }: GlobalSetupContext) {
  const server = await startTestServer()
  provide('serverPort', server.port)

  return async function teardown() {
    await server.close()
  }
}
```

### Inject Provided Values

```typescript
// In test files
import { inject, test } from 'vitest'

test('uses server', () => {
  const port = inject('serverPort')
  // use port
})
```

## Test Tags

Organize tests with tags for selective running:

```typescript
test('quick check', { tags: ['fast'] }, () => { /* ... */ })
test('database test', { tags: ['slow', 'db'] }, () => { /* ... */ })
describe('API', { tags: ['integration'] }, () => { /* ... */ })
```

```bash
npx vitest --tagsFilter fast
npx vitest --tagsFilter "fast | integration"
npx vitest --tagsFilter "!slow"
npx vitest --tagsFilter "integration & !db"
```

## Sequence Control

### Randomize Order

```typescript
export default defineConfig({
  test: {
    sequence: {
      shuffle: {
        files: true,   // randomize file order
        tests: true,   // randomize test order within files
      },
      seed: 12345,     // reproducible order
    },
  },
})
```

### Concurrent by Default

```typescript
export default defineConfig({
  test: {
    sequence: {
      concurrent: true, // all tests concurrent unless marked sequential
    },
  },
})
```

## OpenTelemetry Integration

Export test execution spans to observability tools:

```typescript
export default defineConfig({
  test: {
    opentelemetry: {
      enabled: true,
    },
  },
})
```

## Common Recipes

### Testing with Environment Variables

```typescript
test('uses env vars', () => {
  vi.stubEnv('API_URL', 'https://test.api.com')
  expect(getApiUrl()).toBe('https://test.api.com')
})
```

### Testing Event Emitters

```typescript
test('emits event', async () => {
  const emitter = new EventEmitter()
  const handler = vi.fn()
  emitter.on('data', handler)

  emitter.emit('data', { value: 42 })

  expect(handler).toHaveBeenCalledWith({ value: 42 })
})
```

### Testing Streams

```typescript
test('readable stream', async () => {
  const stream = createReadStream()
  const chunks: string[] = []

  for await (const chunk of stream) {
    chunks.push(chunk.toString())
  }

  expect(chunks.join('')).toContain('expected content')
})
```

### Retry Flaky Tests

```typescript
test('flaky test', { retry: 3 }, async () => {
  const result = await unstableOperation()
  expect(result).toBeDefined()
})
```

### Retry with Delay and Condition

```typescript
test('retry with backoff', {
  retry: {
    count: 3,
    delay: 1000,
    condition: (error) => error.message.includes('timeout'),
  },
}, async () => {
  await fetchWithTimeout()
})
```

---

**Related:** [00-overview.md](00-overview.md) for configuration, [08-cli-reporters.md](08-cli-reporters.md) for CLI options
