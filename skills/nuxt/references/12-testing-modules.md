# Nuxt — Testing & Modules

> Source: [nuxt.com/docs/getting-started/testing](https://nuxt.com/docs/getting-started/testing) | [nuxt.com/modules](https://nuxt.com/modules)

## Table of Contents

- [Testing Overview](#testing-overview)
- [Setup](#setup)
- [Unit Testing](#unit-testing)
- [Component Testing](#component-testing)
- [E2E Testing](#e2e-testing)
- [Testing Utilities](#testing-utilities)
- [Nuxt Modules](#nuxt-modules)
- [Creating Modules](#creating-modules)
- [Nuxt Layers](#nuxt-layers)
- [Popular Modules](#popular-modules)
- [Common Pitfalls](#common-pitfalls)

## Testing Overview

Nuxt provides `@nuxt/test-utils` with first-class support for:
- **Unit tests** — Test composables and utilities in isolation
- **Component tests** — Mount Vue components in a Nuxt environment
- **E2E tests** — Test full application flows with Playwright

## Setup

```bash
npm i --save-dev @nuxt/test-utils vitest @vue/test-utils happy-dom playwright-core
```

### Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import { defineVitestProject } from '@nuxt/test-utils/config'

export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: 'unit',
          include: ['test/unit/**/*.{test,spec}.ts'],
          environment: 'node'
        }
      },
      await defineVitestProject({
        test: {
          name: 'nuxt',
          include: ['test/nuxt/**/*.{test,spec}.ts'],
          environment: 'nuxt'
        }
      })
    ]
  }
})
```

### Recommended Directory Structure

```
test/
├── e2e/
│   └── navigation.test.ts   # Playwright E2E tests
├── nuxt/
│   ├── components.test.ts    # Component tests (Nuxt environment)
│   └── composables.test.ts   # Composable tests (Nuxt environment)
└── unit/
    └── utils.test.ts         # Pure unit tests (Node environment)
```

## Unit Testing

Test pure functions and utilities without the Nuxt runtime:

```typescript
// test/unit/utils.test.ts
import { describe, it, expect } from 'vitest'
import { formatDate, isValidEmail } from '~/shared/utils'

describe('formatDate', () => {
  it('formats ISO dates correctly', () => {
    expect(formatDate('2026-01-15')).toBe('January 15, 2026')
  })
})

describe('isValidEmail', () => {
  it('accepts valid emails', () => {
    expect(isValidEmail('user@example.com')).toBe(true)
  })

  it('rejects invalid emails', () => {
    expect(isValidEmail('not-an-email')).toBe(false)
  })
})
```

## Component Testing

### mountSuspended

Mount Vue components within the full Nuxt environment:

```typescript
// test/nuxt/components.test.ts
import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import { AppHeader } from '#components'

describe('AppHeader', () => {
  it('renders the navigation', async () => {
    const component = await mountSuspended(AppHeader)
    expect(component.find('nav').exists()).toBe(true)
  })

  it('displays the app title', async () => {
    const component = await mountSuspended(AppHeader, {
      props: { title: 'My App' }
    })
    expect(component.text()).toContain('My App')
  })
})
```

### renderSuspended

Render components using Testing Library for DOM interaction testing:

```typescript
import { renderSuspended } from '@nuxt/test-utils/runtime'
import { screen } from '@testing-library/vue'
import { AppFooter } from '#components'

it('renders copyright text', async () => {
  await renderSuspended(AppFooter)
  expect(screen.getByText(/© 2026/)).toBeDefined()
})
```

### Testing Pages

```typescript
import { mountSuspended } from '@nuxt/test-utils/runtime'

it('renders the home page', async () => {
  const page = await mountSuspended(
    () => import('~/pages/index.vue'),
    { route: '/' }
  )
  expect(page.text()).toContain('Welcome')
})
```

## E2E Testing

### With @nuxt/test-utils

```typescript
// test/e2e/navigation.test.ts
import { describe, test, expect } from 'vitest'
import { $fetch, setup } from '@nuxt/test-utils/e2e'

describe('Navigation', async () => {
  await setup({ setupTimeout: 30000 })

  test('home page renders', async () => {
    const html = await $fetch('/')
    expect(html).toContain('Welcome')
  })

  test('API returns data', async () => {
    const data = await $fetch('/api/health')
    expect(data).toHaveProperty('status', 'ok')
  })
})
```

### With Playwright

```typescript
// test/e2e/app.test.ts
import { expect, test } from '@nuxt/test-utils/playwright'

test('navigation works', async ({ page, goto }) => {
  await goto('/', { waitUntil: 'hydration' })
  await expect(page.getByRole('heading')).toHaveText('Welcome')

  await page.getByRole('link', { name: 'About' }).click()
  await expect(page).toHaveURL('/about')
  await expect(page.getByRole('heading')).toHaveText('About Us')
})
```

## Testing Utilities

### mockNuxtImport

Mock auto-imported functions:

```typescript
import { mockNuxtImport } from '@nuxt/test-utils/runtime'

mockNuxtImport('useState', () => {
  return (key: string) => ref('mocked-value')
})

mockNuxtImport('useFetch', () => {
  return () => ({
    data: ref({ items: [] }),
    status: ref('success'),
    error: ref(null)
  })
})
```

### mockComponent

Mock component implementations:

```typescript
import { mockComponent } from '@nuxt/test-utils/runtime'

mockComponent('AppHeader', {
  setup() {
    return () => h('header', 'Mocked Header')
  }
})
```

### registerEndpoint

Create mock API endpoints:

```typescript
import { registerEndpoint } from '@nuxt/test-utils/runtime'

registerEndpoint('/api/users', () => [
  { id: 1, name: 'Alice' },
  { id: 2, name: 'Bob' }
])

registerEndpoint('/api/users', {
  method: 'POST',
  handler: () => ({ id: 3, name: 'Charlie' })
})
```

## Nuxt Modules

Modules extend Nuxt's core functionality. Install via:

```bash
npx nuxt module add <module-name>
```

This adds the module to `nuxt.config.ts` and installs the package.

### Using Modules

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: [
    '@pinia/nuxt',
    '@nuxt/ui',
    '@nuxt/image',
    ['@nuxtjs/i18n', { /* module options */ }]
  ]
})
```

## Creating Modules

### Basic Module

```typescript
// modules/my-module.ts
import { defineNuxtModule, createResolver, addPlugin } from '@nuxt/kit'

export default defineNuxtModule({
  meta: {
    name: 'my-module',
    configKey: 'myModule'
  },
  defaults: {
    enabled: true
  },
  setup(options, nuxt) {
    if (!options.enabled) return

    const { resolve } = createResolver(import.meta.url)

    // Add a plugin
    addPlugin(resolve('./runtime/plugin'))

    // Add composables
    nuxt.hook('imports:dirs', (dirs) => {
      dirs.push(resolve('./runtime/composables'))
    })

    // Add components
    nuxt.hook('components:dirs', (dirs) => {
      dirs.push(resolve('./runtime/components'))
    })
  }
})
```

### @nuxt/kit Utilities

| Utility | Purpose |
|---------|---------|
| `addPlugin` | Register a plugin |
| `addComponent` | Register a component |
| `addImports` | Add auto-imports |
| `addServerHandler` | Add server routes |
| `addTemplate` | Generate files at build time |
| `createResolver` | Resolve paths relative to the module |

## Nuxt Layers

Layers enable sharing configuration, components, and composables across projects:

### Using a Layer

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  extends: [
    './layers/base',                    // Local directory
    'github:user/nuxt-layer',          // Git repository
    '@my-org/shared-layer'             // npm package
  ]
})
```

### Creating a Layer

A layer is a minimal Nuxt project:

```
layers/base/
├── nuxt.config.ts    # Layer configuration
├── components/       # Shared components
├── composables/      # Shared composables
├── layouts/          # Shared layouts
├── plugins/          # Shared plugins
└── utils/            # Shared utilities
```

```typescript
// layers/base/nuxt.config.ts
export default defineNuxtConfig({
  // Layer-specific configuration
  css: ['~/assets/css/base.css']
})
```

### Layer Priority

Later layers override earlier ones. The application's own files always take highest priority.

## Popular Modules

### Official Modules

| Module | Purpose |
|--------|---------|
| `@nuxt/ui` | UI component library (Reka UI + Tailwind) |
| `@nuxt/image` | Image optimization and responsive images |
| `@nuxt/content` | File-based CMS for Markdown/JSON content |
| `@nuxt/fonts` | Font optimization and loading |
| `@nuxt/scripts` | Third-party script management |
| `@nuxt/icon` | Icon system (200K+ icons via Iconify) |
| `@nuxt/devtools` | Development tools and debugging |
| `@nuxt/eslint` | ESLint integration |
| `@nuxt/test-utils` | Testing utilities |

### Community Modules

| Module | Purpose |
|--------|---------|
| `@pinia/nuxt` | Pinia state management |
| `@nuxtjs/i18n` | Internationalization |
| `@nuxtjs/color-mode` | Dark/light mode |
| `@nuxtjs/tailwindcss` | Tailwind CSS integration |
| `@nuxtjs/google-fonts` | Google Fonts loading |
| `@nuxtjs/supabase` | Supabase integration |
| `@sidebase/nuxt-auth` | Authentication |
| `nuxt-security` | Security headers and CSP |
| `@vueuse/nuxt` | VueUse composables |

## Common Pitfalls

- **Mixing test environments** — `@nuxt/test-utils/runtime` and `@nuxt/test-utils/e2e` cannot coexist in the same test file. Separate into different directories.
- **Missing type generation** — Run `nuxt prepare` before tests so TypeScript can resolve auto-imports and aliases.
- **Module ordering** — Some modules depend on others. If you get errors, try reordering modules in `nuxt.config.ts`.
- **Layer file conflicts** — When extending a layer that defines components with the same name as yours, your local version takes priority. This is intentional but can cause confusion.
- **Test state isolation** — Nuxt test environment shares state across tests in the same file. Reset state between tests to prevent cross-contamination.
