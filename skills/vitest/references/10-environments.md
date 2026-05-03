# Test Environments

> Source: [vitest.dev/guide/environment](https://vitest.dev/guide/environment.html) | Version: 4.x

## Table of Contents

- [Built-in Environments](#built-in-environments)
- [Configuring Environments](#configuring-environments)
- [Per-File Environments](#per-file-environments)
- [jsdom](#jsdom)
- [happy-dom](#happy-dom)
- [edge-runtime](#edge-runtime)
- [Custom Environments](#custom-environments)
- [Environment Comparison](#environment-comparison)

---

## Built-in Environments

| Environment | Description | Browser APIs | Speed |
|-------------|-------------|-------------|-------|
| `node` | Default Node.js environment | None | Fastest |
| `jsdom` | Full browser API emulation | Most (window, document, etc.) | Moderate |
| `happy-dom` | Lightweight browser emulation | Subset (faster than jsdom) | Fast |
| `edge-runtime` | Vercel Edge Runtime emulation | Web APIs only | Fast |

## Configuring Environments

### Global Default

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    environment: 'jsdom',
  },
})
```

### Install Dependencies

```bash
# jsdom
npm install -D jsdom

# happy-dom
npm install -D happy-dom

# edge-runtime
npm install -D @edge-runtime/vm
```

## Per-File Environments

Override the environment for individual test files using a comment directive:

```typescript
// @vitest-environment jsdom

import { expect, test } from 'vitest'

test('DOM access', () => {
  const div = document.createElement('div')
  div.textContent = 'Hello'
  expect(div.textContent).toBe('Hello')
})
```

```typescript
// @vitest-environment happy-dom

test('uses happy-dom', () => {
  expect(typeof window).toBe('object')
})
```

```typescript
// @vitest-environment node

test('no browser APIs', () => {
  expect(typeof window).toBe('undefined')
})
```

### Per-File with Options

```typescript
/**
 * @vitest-environment jsdom
 * @vitest-environment-options { "url": "https://example.com" }
 */

test('custom URL', () => {
  expect(window.location.href).toBe('https://example.com/')
})
```

## jsdom

Full browser environment simulation using [jsdom](https://github.com/jsdom/jsdom).

### Setup

```bash
npm install -D jsdom
```

```typescript
export default defineConfig({
  test: {
    environment: 'jsdom',
    environmentOptions: {
      jsdom: {
        url: 'http://localhost:3000',
        resources: 'usable',
        runScripts: 'dangerously',
      },
    },
  },
})
```

### Capabilities

- `window`, `document`, `navigator`, `location`
- DOM manipulation (createElement, querySelector, etc.)
- Event handling (addEventListener, dispatchEvent)
- localStorage, sessionStorage
- fetch (via undici)
- XMLHttpRequest
- Canvas (with `canvas` package)
- CSS parsing

### Common Use Cases

```typescript
// @vitest-environment jsdom

test('DOM manipulation', () => {
  document.body.innerHTML = '<div id="app">Hello</div>'
  const app = document.getElementById('app')
  expect(app?.textContent).toBe('Hello')
})

test('event handling', () => {
  const button = document.createElement('button')
  const handler = vi.fn()
  button.addEventListener('click', handler)
  button.click()
  expect(handler).toHaveBeenCalled()
})

test('localStorage', () => {
  localStorage.setItem('key', 'value')
  expect(localStorage.getItem('key')).toBe('value')
})
```

## happy-dom

Lightweight alternative to jsdom. Faster but with fewer APIs.

### Setup

```bash
npm install -D happy-dom
```

```typescript
export default defineConfig({
  test: {
    environment: 'happy-dom',
  },
})
```

### When to Use happy-dom

- Tests only need basic DOM APIs
- Speed is a priority
- Don't need full CSS/layout support
- Component tests with simple rendering

### When to Use jsdom Instead

- Need full CSS parsing
- Need `canvas` support
- Need complete `XMLHttpRequest` behavior
- Need `MutationObserver` accuracy

## edge-runtime

Emulates Vercel's Edge Runtime for testing edge functions:

```bash
npm install -D @edge-runtime/vm
```

```typescript
export default defineConfig({
  test: {
    environment: 'edge-runtime',
  },
})
```

### Available APIs

- `fetch`, `Request`, `Response`, `Headers`
- `URL`, `URLSearchParams`
- `TextEncoder`, `TextDecoder`
- `crypto` (Web Crypto API)
- `AbortController`, `AbortSignal`
- `setTimeout`, `setInterval` (limited)

### Not Available

- `window`, `document` (no DOM)
- `process` (no Node.js APIs)
- `fs`, `path` (no filesystem)

### Use Case

```typescript
// @vitest-environment edge-runtime

test('edge function handler', async () => {
  const request = new Request('https://example.com/api')
  const response = await handler(request)
  expect(response.status).toBe(200)
})
```

## Custom Environments

Create a custom environment by exporting an `Environment` object:

### Package Convention

Name the package `vitest-environment-{name}`:

```typescript
// vitest-environment-my-custom/index.ts
import type { Environment } from 'vitest/runtime'

export default <Environment>{
  name: 'my-custom',
  viteEnvironment: 'ssr', // 'ssr' | 'client'

  setup(global, options) {
    // Modify global scope
    global.myCustomGlobal = 'hello'

    return {
      teardown() {
        delete global.myCustomGlobal
      },
    }
  },
}
```

### Using Custom Environment

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    environment: 'my-custom',
  },
})
```

Or by file path:

```typescript
environment: './src/test/my-environment.ts',
```

### VM-Based Custom Environment

For full isolation using Node.js `vm` module:

```typescript
export default <Environment>{
  name: 'isolated',
  viteEnvironment: 'ssr',

  async setupVM() {
    const vm = await import('node:vm')
    const context = vm.createContext()

    return {
      getVmContext() { return context },
      teardown() { /* cleanup */ },
    }
  },

  setup() {
    return { teardown() {} }
  },
}
```

### Utility Functions

```typescript
import { builtinEnvironments, populateGlobal } from 'vitest/runtime'

// Access built-in environments
const jsdomEnv = builtinEnvironments.jsdom

// Copy properties to global scope
populateGlobal(global, { fetch, Request, Response })
```

## Environment Comparison

| Feature | node | jsdom | happy-dom | edge-runtime |
|---------|------|-------|-----------|-------------|
| DOM APIs | No | Full | Partial | No |
| `window` | No | Yes | Yes | No |
| `fetch` | Yes | Yes | Yes | Yes |
| `localStorage` | No | Yes | Yes | No |
| CSS parsing | No | Partial | Limited | No |
| Speed | Fastest | Slowest | Fast | Fast |
| Node.js APIs | Full | Full | Full | Limited |
| Web Crypto | No | No | No | Yes |

### Choosing an Environment

1. **Pure logic / utilities** → `node` (default)
2. **React/Vue/Svelte components** → `jsdom` or `happy-dom`
3. **Quick component tests** → `happy-dom`
4. **Full DOM fidelity** → `jsdom`
5. **Edge/serverless functions** → `edge-runtime`
6. **Real browser testing** → Browser Mode (see [07-browser-mode.md](07-browser-mode.md))

---

**Related:** [07-browser-mode.md](07-browser-mode.md) for real browser testing, [00-overview.md](00-overview.md) for configuration
