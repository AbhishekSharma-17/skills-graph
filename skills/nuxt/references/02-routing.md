# Nuxt — Routing

> Source: [nuxt.com/docs/getting-started/routing](https://nuxt.com/docs/getting-started/routing)

## Table of Contents

- [File-Based Routing](#file-based-routing)
- [Dynamic Routes](#dynamic-routes)
- [Nested Routes](#nested-routes)
- [Catch-All Routes](#catch-all-routes)
- [Navigation](#navigation)
- [Route Parameters](#route-parameters)
- [Route Middleware](#route-middleware)
- [Route Validation](#route-validation)
- [Route Groups](#route-groups)
- [Page Metadata](#page-metadata)
- [Common Pitfalls](#common-pitfalls)

## File-Based Routing

Every `.vue` file in `app/pages/` creates a corresponding route. No manual route configuration needed.

```
app/pages/
├── index.vue               → /
├── about.vue               → /about
├── contact.vue             → /contact
└── blog/
    ├── index.vue           → /blog
    └── [slug].vue          → /blog/:slug
```

The `pages/` directory is **optional**. Without it, Nuxt excludes `vue-router` entirely, which is useful for single-page apps or landing pages rendered from `app.vue` alone.

Enable the pages directory by creating it and adding at least one `.vue` file, then use `<NuxtPage />` in `app.vue`:

```vue
<!-- app/app.vue -->
<template>
  <div>
    <NuxtPage />
  </div>
</template>
```

## Dynamic Routes

Use bracket notation for dynamic segments:

```
app/pages/
├── users/
│   ├── [id].vue            → /users/:id
│   └── [id]/
│       └── posts.vue       → /users/:id/posts
├── products/
│   └── [category]-[id].vue → /products/:category-:id
```

```vue
<!-- app/pages/users/[id].vue -->
<script setup>
const route = useRoute()
console.log(route.params.id) // "42" for /users/42
</script>
```

### Optional Parameters

Use double brackets for optional segments:

```
app/pages/
└── [[slug]].vue            → / or /:slug
```

## Nested Routes

Directory structure maps to nested route components. The parent needs `<NuxtPage />` to render children:

```
app/pages/
├── parent.vue              → /parent (renders NuxtPage for children)
└── parent/
    ├── index.vue           → /parent (default child)
    ├── child-a.vue         → /parent/child-a
    └── child-b.vue         → /parent/child-b
```

```vue
<!-- app/pages/parent.vue -->
<template>
  <div>
    <h1>Parent Layout</h1>
    <NuxtPage />  <!-- Renders child routes here -->
  </div>
</template>
```

## Catch-All Routes

Use `[...slug]` to match any remaining path segments:

```
app/pages/
└── [...slug].vue           → Matches any unmatched route
```

```vue
<!-- app/pages/[...slug].vue -->
<script setup>
const route = useRoute()
// /foo/bar → route.params.slug = ['foo', 'bar']
</script>

<template>
  <div>
    <p>Path: {{ route.params.slug?.join('/') }}</p>
  </div>
</template>
```

## Navigation

### NuxtLink Component

Client-side navigation without full page reloads. Prefetches linked pages when they enter the viewport:

```vue
<template>
  <nav>
    <NuxtLink to="/">Home</NuxtLink>
    <NuxtLink to="/about">About</NuxtLink>
    <NuxtLink :to="{ name: 'blog-slug', params: { slug: 'hello' } }">
      Blog Post
    </NuxtLink>
    <NuxtLink to="https://example.com" external>
      External Link
    </NuxtLink>
  </nav>
</template>
```

`NuxtLink` renders an `<a>` tag and adds the `router-link-active` and `router-link-exact-active` CSS classes for active routes.

### Programmatic Navigation

```typescript
// Navigate to a route
await navigateTo('/about')

// Navigate with options
await navigateTo('/login', { replace: true }) // replace history entry

// Navigate with route object
await navigateTo({ path: '/users', query: { page: 2 } })

// External navigation
await navigateTo('https://example.com', { external: true })

// Redirect from server middleware or API routes
return navigateTo('/login', { redirectCode: 302 })
```

### useRouter

Access the Vue Router instance directly:

```typescript
const router = useRouter()

router.push('/about')
router.replace('/login')
router.back()
router.forward()
router.go(-2)
```

## Route Parameters

Access route information with `useRoute()`:

```typescript
const route = useRoute()

route.params       // Dynamic segments { id: '42' }
route.query        // Query string { page: '2', sort: 'name' }
route.path         // Current path /users/42
route.fullPath     // Path with query /users/42?page=2
route.name         // Route name 'users-id'
route.hash         // Hash fragment '#section'
route.meta         // Merged route meta from definePageMeta
route.matched      // Array of matched route records
```

## Route Middleware

Middleware runs before navigating to a route. Three types:

### Named Middleware

```typescript
// app/middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const user = useAuthUser()
  if (!user.value) {
    return navigateTo('/login')
  }
})
```

Apply to specific pages:

```vue
<script setup>
definePageMeta({
  middleware: 'auth'
  // or multiple: middleware: ['auth', 'admin']
})
</script>
```

### Global Middleware

Runs on every route change. Use the `.global` suffix:

```typescript
// app/middleware/01.tracking.global.ts
export default defineNuxtRouteMiddleware((to, from) => {
  console.log(`Navigating to ${to.path}`)
})
```

### Inline Middleware

Defined directly in the page:

```vue
<script setup>
definePageMeta({
  middleware: [
    function (to, from) {
      if (to.params.id === '1') {
        return abortNavigation()
      }
    }
  ]
})
</script>
```

### Middleware Execution Order

1. Global middleware (alphabetically by filename)
2. Page-defined middleware (array order)

Prefix global middleware with numbers for explicit ordering: `01.setup.global.ts`, `02.analytics.global.ts`.

### Navigation Control

```typescript
export default defineNuxtRouteMiddleware((to, from) => {
  // Redirect
  return navigateTo('/login')

  // Redirect with status code (server-side)
  return navigateTo('/login', { redirectCode: 301 })

  // Block navigation
  return abortNavigation()

  // Block with error
  return abortNavigation('Access denied')

  // Allow navigation (return nothing or true)
})
```

## Route Validation

Validate route parameters using `definePageMeta`:

```vue
<script setup>
definePageMeta({
  validate: async (route) => {
    // Return true/false or an error object
    return /^\d+$/.test(route.params.id as string)
  }
})
</script>
```

Returning `false` triggers a 404 error. Return a custom error object for different status codes:

```typescript
definePageMeta({
  validate: (route) => {
    if (!/^\d+$/.test(route.params.id as string)) {
      return createError({
        statusCode: 404,
        statusMessage: 'Page Not Found'
      })
    }
    return true
  }
})
```

## Route Groups

Group routes without affecting the URL path using parenthesized directories:

```
app/pages/
├── (marketing)/
│   ├── pricing.vue         → /pricing
│   └── features.vue        → /features
└── (app)/
    ├── dashboard.vue       → /dashboard
    └── settings.vue        → /settings
```

Route groups are useful for organizing pages that share middleware or layouts without nesting the URL.

## Page Metadata

Define metadata per page with `definePageMeta`:

```vue
<script setup>
definePageMeta({
  title: 'Dashboard',
  layout: 'admin',
  middleware: ['auth'],
  keepalive: true,
  pageTransition: { name: 'fade' },
  layoutTransition: { name: 'slide' }
})
</script>
```

Access page meta in layouts and middleware via `route.meta`.

## Common Pitfalls

- **Using `useRoute()` in middleware** — The route object is not yet resolved during middleware execution. Use the `to` and `from` parameters instead.
- **Forgetting `<NuxtPage />`** — Pages won't render without this component in `app.vue` or a parent layout/page.
- **Non-Vue files in `pages/`** — Every `.vue` file becomes a route. Use route groups `(folder)` or `.nuxtignore` to exclude files.
- **Dynamic imports** — Nuxt automatically code-splits each page. Don't manually lazy-import page components.
