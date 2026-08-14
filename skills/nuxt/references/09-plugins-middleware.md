# Nuxt — Plugins & Middleware

> Source: [nuxt.com/docs/guide/directory-structure/plugins](https://nuxt.com/docs/guide/directory-structure/plugins)

## Table of Contents

- [Plugin System](#plugin-system)
- [Creating Plugins](#creating-plugins)
- [Plugin Order and Loading](#plugin-order-and-loading)
- [Provide and Inject](#provide-and-inject)
- [Vue Directives](#vue-directives)
- [Route Middleware Deep Dive](#route-middleware-deep-dive)
- [Server Middleware vs Route Middleware](#server-middleware-vs-route-middleware)
- [Common Pitfalls](#common-pitfalls)

## Plugin System

Plugins run during Vue application initialization. They are used for:
- Registering Vue plugins (Pinia, i18n, third-party libraries)
- Providing global helpers
- Registering custom directives
- Setting up error handlers
- Running initialization logic

Plugins are auto-loaded from `app/plugins/`.

## Creating Plugins

### Basic Plugin

```typescript
// app/plugins/analytics.ts
export default defineNuxtPlugin((nuxtApp) => {
  console.log('Analytics plugin initialized')
})
```

### Object Syntax

```typescript
// app/plugins/01.auth.ts
export default defineNuxtPlugin({
  name: 'auth-plugin',
  enforce: 'pre',  // Run before other plugins
  async setup(nuxtApp) {
    const { data } = await useFetch('/api/auth/session')
    if (data.value) {
      useState('user', () => data.value)
    }
  }
})
```

### Registering Vue Plugins

```typescript
// app/plugins/vue-toastification.ts
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(Toast, {
    position: 'top-right',
    timeout: 3000
  })
})
```

### Client-Only and Server-Only Plugins

Use file suffixes to restrict execution environment:

```
app/plugins/
├── analytics.client.ts    → Runs only in browser
├── logger.server.ts       → Runs only on server
└── shared.ts              → Runs in both
```

## Plugin Order and Loading

### Ordering

Plugins load alphabetically by default. Prefix with numbers for explicit ordering:

```
app/plugins/
├── 01.auth.ts             → First
├── 02.analytics.ts        → Second
├── 03.error-handler.ts    → Third
└── vue-plugins.ts         → After numbered plugins
```

Filenames are sorted as strings, so `10.plugin.ts` comes before `2.plugin.ts`. Zero-pad single digits.

### Parallel Execution

Mark plugins as parallel to avoid blocking:

```typescript
export default defineNuxtPlugin({
  name: 'heavy-plugin',
  parallel: true,  // Don't block other plugins
  async setup(nuxtApp) {
    await heavyInitialization()
  }
})
```

### Dependencies

Declare plugin dependencies:

```typescript
export default defineNuxtPlugin({
  name: 'analytics',
  dependsOn: ['auth-plugin'],  // Wait for auth to complete
  setup(nuxtApp) {
    const user = useState('user')
    trackUser(user.value)
  }
})
```

### Enforce Ordering

```typescript
export default defineNuxtPlugin({
  name: 'critical-plugin',
  enforce: 'pre',   // Run before default plugins
  // enforce: 'post' // Run after default plugins
  setup(nuxtApp) {}
})
```

## Provide and Inject

Make helpers available throughout the application:

```typescript
// app/plugins/api.ts
export default defineNuxtPlugin(() => {
  const api = {
    users: {
      list: () => $fetch('/api/users'),
      get: (id: string) => $fetch(`/api/users/${id}`),
      create: (data: any) => $fetch('/api/users', { method: 'POST', body: data })
    }
  }

  return {
    provide: {
      api
    }
  }
})
```

### Usage in Components

```vue
<script setup>
const { $api } = useNuxtApp()

const { data: users } = await useAsyncData('users', () => $api.users.list())
</script>

<template>
  <ul>
    <li v-for="user in users" :key="user.id">{{ user.name }}</li>
  </ul>
</template>
```

### TypeScript Support

```typescript
// app/plugins/api.ts
export default defineNuxtPlugin(() => {
  return {
    provide: {
      api: createApiClient()
    }
  }
})

// Type declaration
declare module '#app' {
  interface NuxtApp {
    $api: ReturnType<typeof createApiClient>
  }
}

declare module 'vue' {
  interface ComponentCustomProperties {
    $api: ReturnType<typeof createApiClient>
  }
}
```

### Composables vs Provide/Inject

The Nuxt docs recommend composables over `provide`:

```typescript
// Preferred — composable in app/composables/
export const useApi = () => {
  return {
    users: {
      list: () => $fetch('/api/users')
    }
  }
}

// Less preferred — plugin provide
export default defineNuxtPlugin(() => ({
  provide: { api: createApi() }
}))
```

Composables are tree-shaken, typed automatically, and don't pollute the global namespace.

## Vue Directives

Register custom directives in plugins:

```typescript
// app/plugins/directives.ts
export default defineNuxtPlugin((nuxtApp) => {
  // v-focus — auto-focus an element on mount
  nuxtApp.vueApp.directive('focus', {
    mounted(el) {
      el.focus()
    }
  })

  // v-click-outside — detect clicks outside an element
  nuxtApp.vueApp.directive('click-outside', {
    mounted(el, binding) {
      el._clickOutside = (event: MouseEvent) => {
        if (!el.contains(event.target as Node)) {
          binding.value(event)
        }
      }
      document.addEventListener('click', el._clickOutside)
    },
    unmounted(el) {
      document.removeEventListener('click', el._clickOutside)
    }
  })
})
```

Usage:

```vue
<template>
  <input v-focus />
  <div v-click-outside="closeDropdown">
    Dropdown content
  </div>
</template>
```

### SSR-Safe Directives

Directives run on both server and client. Guard browser-only APIs:

```typescript
nuxtApp.vueApp.directive('tooltip', {
  mounted(el, binding) {
    // mounted only runs on client, safe to use DOM APIs
    el.title = binding.value
  },
  getSSRProps(binding) {
    // Return attributes for server-rendered HTML
    return { title: binding.value }
  }
})
```

## Route Middleware Deep Dive

### Authentication Middleware

```typescript
// app/middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const user = useAuthUser()

  if (!user.value && to.path !== '/login') {
    return navigateTo('/login')
  }
})
```

### Role-Based Access

```typescript
// app/middleware/admin.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const user = useAuthUser()

  if (!user.value || user.value.role !== 'admin') {
    return abortNavigation(
      createError({ statusCode: 403, statusMessage: 'Forbidden' })
    )
  }
})
```

### Dynamic Middleware Registration

Register middleware at runtime from within a plugin:

```typescript
// app/plugins/middleware.ts
export default defineNuxtPlugin(() => {
  addRouteMiddleware('custom', (to, from) => {
    console.log('Custom middleware:', to.path)
  })

  addRouteMiddleware('global-guard', (to, from) => {
    // This runs on every navigation
  }, { global: true })
})
```

### Middleware Return Values

```typescript
export default defineNuxtRouteMiddleware((to, from) => {
  // Allow navigation — return nothing or undefined
  return

  // Redirect
  return navigateTo('/other-page')

  // Redirect with status code (server-side only)
  return navigateTo('/login', { redirectCode: 302 })

  // Block navigation silently
  return abortNavigation()

  // Block with error
  return abortNavigation(
    createError({ statusCode: 403, statusMessage: 'Access denied' })
  )
})
```

## Server Middleware vs Route Middleware

| Feature | Route Middleware | Server Middleware |
|---------|-----------------|-------------------|
| Location | `app/middleware/` | `server/middleware/` |
| Runs on | Client + server navigation | Every HTTP request |
| Access to | Vue Router (`to`, `from`) | H3 Event (headers, cookies) |
| Purpose | Auth guards, redirects | Logging, CORS, API auth |
| Can return response | No (redirects only) | No (should not return) |

## Common Pitfalls

- **Plugin composable timing** — Composables that depend on later-loaded plugins or Vue lifecycle hooks may fail. Plugins execute before component initialization.
- **Only top-level files** — Only files directly in `app/plugins/` are auto-loaded. Subdirectory files require explicit registration in `nuxt.config.ts`.
- **Directive SSR errors** — Browser APIs (`document`, `window`) are unavailable during SSR. Use `mounted` hook for client-side DOM operations and `getSSRProps` for server rendering.
- **Middleware `useRoute()`** — Don't use `useRoute()` inside middleware. The composable returns the route before resolution. Use the `to` and `from` parameters instead.
- **Global middleware naming** — The `.global` suffix must be part of the filename: `auth.global.ts`, not `global.auth.ts`.
