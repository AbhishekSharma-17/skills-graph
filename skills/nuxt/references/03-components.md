# Nuxt — Components

> Source: [nuxt.com/docs/guide/directory-structure/components](https://nuxt.com/docs/guide/directory-structure/components)

## Table of Contents

- [Auto-Import System](#auto-import-system)
- [Naming Conventions](#naming-conventions)
- [Dynamic Components](#dynamic-components)
- [Lazy Loading](#lazy-loading)
- [Client-Only Components](#client-only-components)
- [Server Components](#server-components)
- [Custom Component Directories](#custom-component-directories)
- [Islands Architecture](#islands-architecture)
- [Common Pitfalls](#common-pitfalls)

## Auto-Import System

Nuxt automatically imports components from `app/components/`. No manual `import` statements required:

```vue
<!-- app/components/AppHeader.vue -->
<template>
  <header>
    <nav>My App</nav>
  </header>
</template>
```

```vue
<!-- app/pages/index.vue — no import needed -->
<template>
  <div>
    <AppHeader />
    <p>Content here</p>
  </div>
</template>
```

Components are tree-shaken — unused components are excluded from the production build.

## Naming Conventions

### Path-Based Naming

Component names are derived from their directory path with duplicate segments removed:

```
app/components/
├── AppHeader.vue           → <AppHeader />
├── base/
│   └── Button.vue          → <BaseButton />
├── base/
│   └── card/
│       └── Title.vue       → <BaseCardTitle />
└── form/
    ├── Input.vue           → <FormInput />
    └── form/
        └── Label.vue       → <FormLabel /> (duplicate "form" removed)
```

### Grouping Directories

Use parentheses to exclude a directory from the component name:

```
app/components/
└── base/
    └── (helpers)/
        └── Button.vue      → <BaseButton /> (not BaseHelpersButton)
```

### Disabling Path Prefix

Use filenames only (no directory-based prefixing):

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  components: [{
    path: '~/components',
    pathPrefix: false
  }]
})
```

With this config, `components/ui/Button.vue` registers as `<Button />` instead of `<UiButton />`.

## Dynamic Components

Use Vue's `<component :is="">` with `resolveComponent` or direct imports from `#components`:

```vue
<script setup>
import { SomeComponent } from '#components'

const MyButton = resolveComponent('MyButton')
</script>

<template>
  <component :is="clickable ? MyButton : 'div'" />
  <component :is="SomeComponent" />
</template>
```

For conditionally rendered components, register them dynamically:

```vue
<script setup>
const components = {
  card: resolveComponent('UiCard'),
  list: resolveComponent('UiList'),
  table: resolveComponent('UiTable')
}

const currentView = ref('card')
</script>

<template>
  <component :is="components[currentView]" :data="items" />
</template>
```

## Lazy Loading

Prefix any component with `Lazy` to defer loading until the component is needed:

```vue
<template>
  <div>
    <!-- Loaded immediately -->
    <AppHeader />

    <!-- Loaded only when show becomes true -->
    <LazyHeavyChart v-if="showChart" :data="chartData" />

    <!-- Loaded only when modal opens -->
    <LazyAppModal v-if="isOpen" @close="isOpen = false" />
  </div>
</template>
```

The `Lazy` prefix works with auto-imported components — no additional configuration needed. The component code is split into a separate chunk and loaded on demand.

## Client-Only Components

### `.client` Suffix

Components with `.client.vue` render only in the browser:

```
app/components/
└── Comments.client.vue     → Renders only on client
```

```vue
<template>
  <div>
    <Comments />  <!-- Skipped during SSR, renders after hydration -->
  </div>
</template>
```

### `<ClientOnly>` Wrapper

Wrap any component to prevent SSR:

```vue
<template>
  <ClientOnly>
    <ThirdPartyWidget />
    <template #fallback>
      <p>Loading widget...</p>
    </template>
  </ClientOnly>
</template>
```

The `#fallback` slot renders during SSR and is replaced after hydration.

### `client:only` Attribute (v4.4+)

Use the attribute form for individual component instances:

```vue
<template>
  <MyComponent client:only />
</template>
```

## Server Components

### `.server` Suffix

Components that render only on the server. The HTML is sent to the client but no JavaScript is shipped for the component:

```
app/components/
└── HighlightedMarkdown.server.vue
```

Server components reduce client-side JavaScript but cannot have interactive event handlers. They re-render on the server when props change (via a network request).

### Paired Components

Provide different implementations for server and client:

```
app/components/
├── Comments.server.vue     → Renders during SSR
└── Comments.client.vue     → Takes over after hydration
```

### Server Component with Interactive Slots

Server components can accept client-side interactive content via slots:

```vue
<!-- app/components/ServerWrapper.server.vue -->
<template>
  <div class="server-rendered-frame">
    <slot />  <!-- Client components can go here -->
  </div>
</template>
```

## Custom Component Directories

Register additional directories in `nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  components: [
    { path: '~/components' },
    { path: '~/ui-library/components', prefix: 'Ui' },
    { path: '~/calendar-module/components', pathPrefix: false },
    {
      path: '~/components/global',
      global: true  // Available in all component contexts
    }
  ]
})
```

### Disabling Auto-Import

For manual component management:

```typescript
export default defineNuxtConfig({
  components: {
    dirs: []  // Disable auto-import entirely
  }
})
```

## Islands Architecture

Nuxt supports component islands — isolated interactive components within otherwise static pages. Enable in `nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  experimental: {
    componentIslands: true
  }
})
```

Create island components with the `.server` suffix. They render on the server and hydrate independently on the client.

```vue
<!-- app/components/Counter.server.vue -->
<template>
  <NuxtIsland name="Counter" :props="{ initial: 0 }" />
</template>
```

## Common Pitfalls

- **Name collisions** — Two components resolving to the same name causes unpredictable behavior. Use explicit prefixes or directory paths to disambiguate.
- **Lazy prefix casing** — Use `<LazyMyComponent />`, not `<lazyMyComponent />` or `<lazy-my-component />`.
- **Server component limitations** — `.server` components cannot use `@click`, `v-model`, or other client-side interactivity. Use slots for interactive portions.
- **ClientOnly hydration** — Content inside `<ClientOnly>` is not in the initial HTML. Search engines won't see it. Use `#fallback` for SEO-relevant placeholder content.
- **Third-party components** — Components from npm packages are not auto-imported. Register them in a plugin or import explicitly from `#components`.
