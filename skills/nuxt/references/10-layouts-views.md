# Nuxt — Layouts & Views

> Source: [nuxt.com/docs/guide/directory-structure/layouts](https://nuxt.com/docs/guide/directory-structure/layouts)

## Table of Contents

- [Application Structure](#application-structure)
- [app.vue](#appvue)
- [Layouts](#layouts)
- [NuxtPage Component](#nuxtpage-component)
- [Error Handling](#error-handling)
- [Transitions](#transitions)
- [Common Pitfalls](#common-pitfalls)

## Application Structure

Nuxt's view hierarchy flows from outer to inner:

```
app.vue
  └── NuxtLayout (default.vue)
        └── NuxtPage (pages/index.vue)
```

Each layer is optional:
- Without `app.vue` → Nuxt uses a built-in default
- Without `layouts/` → pages render without a layout wrapper
- Without `pages/` → content renders directly from `app.vue`

## app.vue

The root component of every Nuxt application:

```vue
<!-- app/app.vue -->
<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>
```

### Minimal app.vue (No Pages)

```vue
<!-- app/app.vue -->
<template>
  <div>
    <h1>My Single-Page App</h1>
    <p>No pages directory needed</p>
  </div>
</template>
```

### app.vue with Global Setup

```vue
<!-- app/app.vue -->
<script setup>
// Global head tags
useHead({
  titleTemplate: '%s | My App',
  htmlAttrs: { lang: 'en' }
})

// Global state initialization
const config = useState<SiteConfig>('config')
await callOnce(async () => {
  config.value = await $fetch('/api/config')
})
</script>

<template>
  <div>
    <AppHeader />
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <AppFooter />
  </div>
</template>
```

## Layouts

Layouts wrap page content with shared UI elements. Place in `app/layouts/`.

### Default Layout

Used automatically when no layout is specified:

```vue
<!-- app/layouts/default.vue -->
<template>
  <div class="layout-default">
    <header>
      <nav>
        <NuxtLink to="/">Home</NuxtLink>
        <NuxtLink to="/about">About</NuxtLink>
      </nav>
    </header>

    <main>
      <slot />  <!-- Page content renders here -->
    </main>

    <footer>
      <p>&copy; 2026 My App</p>
    </footer>
  </div>
</template>
```

### Named Layouts

Create layouts for different sections of your app:

```vue
<!-- app/layouts/admin.vue -->
<template>
  <div class="layout-admin">
    <aside>
      <AdminSidebar />
    </aside>
    <main>
      <slot />
    </main>
  </div>
</template>
```

```vue
<!-- app/layouts/auth.vue -->
<template>
  <div class="layout-auth">
    <div class="auth-card">
      <slot />
    </div>
  </div>
</template>
```

### Using Named Layouts

Set a page's layout with `definePageMeta`:

```vue
<!-- app/pages/admin/dashboard.vue -->
<script setup>
definePageMeta({
  layout: 'admin'
})
</script>

<template>
  <div>
    <h1>Admin Dashboard</h1>
  </div>
</template>
```

### Disabling Layouts

```vue
<script setup>
definePageMeta({
  layout: false
})
</script>
```

### Layout Props (v4.4+)

Pass data to layouts through `definePageMeta`:

```vue
<!-- app/pages/settings.vue -->
<script setup>
definePageMeta({
  layout: {
    name: 'panel',
    props: {
      sidebar: true,
      title: 'Settings'
    }
  }
})
</script>
```

```vue
<!-- app/layouts/panel.vue -->
<script setup>
defineProps<{
  sidebar?: boolean
  title?: string
}>()
</script>

<template>
  <div class="panel-layout">
    <aside v-if="sidebar">
      <PanelSidebar />
    </aside>
    <main>
      <h1 v-if="title">{{ title }}</h1>
      <slot />
    </main>
  </div>
</template>
```

### Dynamic Layout Changes

Switch layouts at runtime:

```vue
<script setup>
function switchToAdmin() {
  setPageLayout('admin')
}
</script>
```

### Route Rules for Layouts

Set layouts via `nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  routeRules: {
    '/admin/**': { appLayout: 'admin' },
    '/auth/**': { appLayout: 'auth' }
  }
})
```

## NuxtPage Component

Renders the matched page component. Required in `app.vue` or a layout:

```vue
<template>
  <NuxtPage />
</template>
```

### With Page Transitions

```vue
<template>
  <NuxtPage :transition="{
    name: 'page',
    mode: 'out-in'
  }" />
</template>

<style>
.page-enter-active,
.page-leave-active {
  transition: all 0.3s;
}
.page-enter-from,
.page-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
```

### With Keep-Alive

```vue
<template>
  <NuxtPage keepalive />
</template>
```

Or per-page:

```vue
<script setup>
definePageMeta({
  keepalive: true
})
</script>
```

### Passing Props to Pages

```vue
<template>
  <NuxtPage :foobar="123" />
</template>
```

```vue
<!-- In the page component -->
<script setup>
const props = defineProps<{ foobar: number }>()
</script>
```

## Error Handling

### error.vue

Global error page for unhandled errors:

```vue
<!-- app/error.vue -->
<script setup>
const props = defineProps<{
  error: {
    statusCode: number
    statusMessage: string
    message: string
    data?: any
  }
}>()

const handleError = () => clearError({ redirect: '/' })
</script>

<template>
  <div class="error-page">
    <h1>{{ error.statusCode }}</h1>
    <p>{{ error.statusMessage }}</p>
    <button @click="handleError">Go Home</button>
  </div>
</template>
```

### Throwing Errors in Pages

```vue
<script setup>
const route = useRoute()
const { data: post } = await useFetch(`/api/posts/${route.params.slug}`)

if (!post.value) {
  throw createError({
    statusCode: 404,
    statusMessage: 'Post Not Found'
  })
}
</script>
```

### NuxtErrorBoundary

Catch errors within specific parts of the page:

```vue
<template>
  <div>
    <AppHeader />

    <NuxtErrorBoundary @error="logError">
      <NuxtPage />
      <template #error="{ error, clearError }">
        <div class="error-container">
          <p>Something went wrong: {{ error.message }}</p>
          <button @click="clearError">Try Again</button>
        </div>
      </template>
    </NuxtErrorBoundary>

    <AppFooter />
  </div>
</template>

<script setup>
function logError(error: Error) {
  console.error('Caught error:', error)
}
</script>
```

### showError Utility

Trigger the full-screen error page programmatically:

```typescript
showError({
  statusCode: 500,
  statusMessage: 'Something went wrong'
})
```

### clearError Utility

Dismiss the error and optionally redirect:

```typescript
clearError()                    // Just clear the error
clearError({ redirect: '/' })  // Clear and redirect
```

## Transitions

### Page Transitions

Enable globally:

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  app: {
    pageTransition: { name: 'page', mode: 'out-in' }
  }
})
```

```css
/* app/assets/css/transitions.css */
.page-enter-active,
.page-leave-active {
  transition: all 0.3s ease;
}
.page-enter-from,
.page-leave-to {
  opacity: 0;
  filter: blur(1rem);
}
```

### Per-Page Transitions

```vue
<script setup>
definePageMeta({
  pageTransition: {
    name: 'slide',
    mode: 'out-in'
  }
})
</script>
```

### Layout Transitions

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  app: {
    layoutTransition: { name: 'layout', mode: 'out-in' }
  }
})
```

### Disabling Transitions

```vue
<script setup>
definePageMeta({
  pageTransition: false,
  layoutTransition: false
})
</script>
```

### JavaScript Hooks

```vue
<script setup>
definePageMeta({
  pageTransition: {
    name: 'custom',
    mode: 'out-in',
    onBeforeEnter: (el) => {
      console.log('Before enter:', el)
    },
    onEnter: (el, done) => {
      // Use GSAP, anime.js, etc.
      done()
    },
    onLeave: (el, done) => {
      done()
    }
  }
})
</script>
```

## Common Pitfalls

- **Single root element in layouts** — Layouts must have a single root element for transitions to work. Wrap content in a `<div>` if needed.
- **Missing `<slot />`** — Layouts without a `<slot />` won't render page content. Always include a slot.
- **NuxtLayout placement** — `<NuxtLayout>` must wrap `<NuxtPage>`. Placing `<NuxtPage>` outside `<NuxtLayout>` bypasses layout rendering.
- **Layout name casing** — Layout names are normalized to kebab-case. `adminPanel.vue` → `layout: 'admin-panel'`.
- **error.vue is not a page** — `error.vue` sits at the app root (`app/error.vue`), not in `app/pages/`. It doesn't use layouts by default.
