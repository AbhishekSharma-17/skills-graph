# Browser Mode

> Source: [vitest.dev/guide/browser](https://vitest.dev/guide/browser/) | Version: 4.x

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Providers](#providers)
- [Configuration](#configuration)
- [Component Testing](#component-testing)
- [Interactivity APIs](#interactivity-apis)
- [Locators & Assertions](#locators--assertions)
- [Multi-Browser Testing](#multi-browser-testing)
- [Headless Mode](#headless-mode)
- [Limitations](#limitations)

---

## Overview

Browser Mode runs tests in real browsers instead of Node.js, providing access to native browser APIs (`window`, `document`, `navigator`). This enables:

- Component testing with real DOM rendering
- Visual regression testing
- Browser-specific API testing
- Accessibility (ARIA) snapshot testing

## Setup

### Quick Setup

```bash
npx vitest init browser
```

This scaffolds the browser configuration interactively.

### Manual Setup

```bash
# Choose a provider
npm install -D @vitest/browser-playwright    # recommended
# or
npm install -D @vitest/browser-webdriverio
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import { playwright } from '@vitest/browser-playwright'

export default defineConfig({
  test: {
    browser: {
      enabled: true,
      provider: playwright(),
      instances: [
        { browser: 'chromium' },
      ],
    },
  },
})
```

### Framework Plugin (for component testing)

```bash
# React
npm install -D vitest-browser-react

# Vue
npm install -D vitest-browser-vue

# Svelte
npm install -D vitest-browser-svelte

# Angular
npm install -D vitest-browser-angular
```

## Providers

### Playwright (Recommended)

```typescript
import { playwright } from '@vitest/browser-playwright'

export default defineConfig({
  test: {
    browser: {
      provider: playwright(),
      instances: [
        { browser: 'chromium' },
        { browser: 'firefox' },
        { browser: 'webkit' },
      ],
    },
  },
})
```

Supported browsers: Chromium, Firefox, WebKit.

### WebdriverIO

```typescript
import { webdriverio } from '@vitest/browser-webdriverio'

export default defineConfig({
  test: {
    browser: {
      provider: webdriverio(),
      instances: [
        { browser: 'chrome' },
      ],
    },
  },
})
```

Supported browsers: Chrome, Firefox, Edge, Safari.

### Preview (Development Only)

```typescript
import { preview } from '@vitest/browser-preview'

export default defineConfig({
  test: {
    browser: {
      provider: preview(),
    },
  },
})
```

Uses the default system browser. Not suitable for CI.

## Configuration

```typescript
export default defineConfig({
  test: {
    browser: {
      enabled: true,
      provider: playwright(),
      headless: true,             // no visible browser window
      isolate: true,              // isolate each test file
      viewport: { width: 1280, height: 720 },
      instances: [
        { browser: 'chromium' },
      ],
      fileParallelism: true,      // run files in parallel
    },
  },
})
```

### Viewport Configuration

```typescript
instances: [{
  browser: 'chromium',
  viewport: { width: 375, height: 667 }, // iPhone SE
}]
```

## Component Testing

### React

```typescript
import { render } from 'vitest-browser-react'
import { expect, test } from 'vitest'
import { Counter } from './Counter'

test('increments count', async () => {
  const screen = render(<Counter initialCount={0} />)

  await expect(screen.getByText('Count: 0')).toBeVisible()

  await screen.getByRole('button', { name: 'Increment' }).click()

  await expect(screen.getByText('Count: 1')).toBeVisible()
})
```

### Vue

```typescript
import { render } from 'vitest-browser-vue'
import Counter from './Counter.vue'

test('renders counter', async () => {
  const screen = render(Counter, {
    props: { initialCount: 5 },
  })

  await expect(screen.getByText('Count: 5')).toBeVisible()
})
```

### Svelte

```typescript
import { render } from 'vitest-browser-svelte'
import Counter from './Counter.svelte'

test('svelte counter', async () => {
  const screen = render(Counter, { initialCount: 0 })
  await screen.getByRole('button').click()
  await expect(screen.getByText('1')).toBeVisible()
})
```

## Interactivity APIs

### userEvent

```typescript
import { userEvent } from '@vitest/browser/context'

test('form interaction', async () => {
  const screen = render(<LoginForm />)

  await userEvent.fill(screen.getByLabelText('Email'), 'user@test.com')
  await userEvent.fill(screen.getByLabelText('Password'), 'secret')
  await userEvent.click(screen.getByRole('button', { name: 'Login' }))

  await expect(screen.getByText('Welcome')).toBeVisible()
})
```

### Available userEvent Methods

| Method | Description |
|--------|-------------|
| `click(element)` | Click an element |
| `dblClick(element)` | Double-click |
| `tripleClick(element)` | Triple-click (select text) |
| `fill(element, text)` | Type into input (clears first) |
| `type(text)` | Type text at current focus |
| `clear(element)` | Clear input value |
| `tab()` | Press Tab key |
| `keyboard(keys)` | Press keyboard keys |
| `hover(element)` | Hover over element |
| `unhover(element)` | Move away from element |
| `selectOptions(element, values)` | Select dropdown options |
| `upload(element, files)` | Upload files |
| `dragAndDrop(source, target)` | Drag and drop |

## Locators & Assertions

### Page Locators

```typescript
import { page } from '@vitest/browser/context'

const heading = page.getByRole('heading', { name: 'Dashboard' })
const input = page.getByLabelText('Search')
const button = page.getByText('Submit')
const element = page.getByTestId('user-card')
const placeholder = page.getByPlaceholder('Enter name')
const title = page.getByTitle('Close dialog')
const altText = page.getByAltText('Company logo')
```

### DOM Assertions

```typescript
await expect(element).toBeVisible()
await expect(element).toBeInTheDocument()
await expect(element).toHaveTextContent('Hello')
await expect(element).toHaveAttribute('href', '/home')
await expect(element).toHaveClass('active')
await expect(element).toHaveValue('test@email.com')
await expect(element).toBeEnabled()
await expect(element).toBeDisabled()
await expect(element).toBeChecked()
```

## Multi-Browser Testing

Test across multiple browsers simultaneously:

```typescript
export default defineConfig({
  test: {
    browser: {
      provider: playwright(),
      instances: [
        { browser: 'chromium' },
        { browser: 'firefox' },
        { browser: 'webkit' },
      ],
    },
  },
})
```

### Per-Browser Overrides

```typescript
instances: [
  {
    browser: 'chromium',
    viewport: { width: 1920, height: 1080 },
  },
  {
    browser: 'webkit',
    viewport: { width: 375, height: 812 }, // mobile Safari
  },
]
```

## Headless Mode

```typescript
browser: {
  headless: true, // CI-friendly, no visible browser
}
```

```bash
# CLI override
npx vitest --browser.headless
```

In CI environments, headless mode is the default.

### Keep Vitest UI in Headless

```bash
npx vitest --browser.headless --ui
```

## Limitations

### Thread-Blocking Dialogs

`alert()`, `confirm()`, `prompt()` block browser execution. Vitest mocks these by default to prevent hanging.

### Module Spying

Native ESM sealed namespaces prevent `vi.spyOn()` on imports. Use module mocking instead:

```typescript
vi.mock('./module.js', { spy: true })
```

### Variable Mocking

Export wrapper functions rather than mocking exported variables directly:

```typescript
// Instead of trying to mock an exported variable:
// export let count = 0

// Export a function that returns the value:
export function getCount() { return count }
```

### Browser Requirements

- Chrome >= 87
- Firefox >= 78
- Safari >= 15.4
- Edge >= 88

### Mixed Testing Strategy

Use separate projects for Node.js and browser tests:

```typescript
export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: 'unit',
          include: ['**/*.unit.test.ts'],
          environment: 'node',
        },
      },
      {
        test: {
          name: 'component',
          include: ['**/*.browser.test.ts'],
          browser: {
            enabled: true,
            provider: playwright(),
            instances: [{ browser: 'chromium' }],
          },
        },
      },
    ],
  },
})
```

---

**Related:** [10-environments.md](10-environments.md) for test environments, [05-snapshots.md](05-snapshots.md) for ARIA snapshots
