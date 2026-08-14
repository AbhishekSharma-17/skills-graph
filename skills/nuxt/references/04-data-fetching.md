# Nuxt — Data Fetching

> Source: [nuxt.com/docs/getting-started/data-fetching](https://nuxt.com/docs/getting-started/data-fetching)

## Table of Contents

- [Core Composables](#core-composables)
- [useFetch](#usefetch)
- [useAsyncData](#useasyncdata)
- [$fetch](#fetch)
- [Return Values](#return-values)
- [Options](#options)
- [Caching and Keys](#caching-and-keys)
- [Refreshing Data](#refreshing-data)
- [Parallel Requests](#parallel-requests)
- [Error Handling](#error-handling)
- [Common Pitfalls](#common-pitfalls)

## Core Composables

Nuxt provides three data fetching mechanisms:

| Method | SSR-Safe | Deduplication | Use Case |
|--------|----------|---------------|----------|
| `useFetch` | Yes | Yes | Default choice for API calls |
| `useAsyncData` | Yes | Yes | Complex logic, non-URL data sources |
| `$fetch` | No* | No | Client-side events, form submissions |

*`$fetch` works on the server but doesn't deduplicate or prevent double-fetching during SSR/hydration.

## useFetch

The primary data fetching composable. Wraps `$fetch` with SSR safety:

```vue
<script setup>
const { data: posts, status, error } = await useFetch('/api/posts')
</script>

<template>
  <div v-if="status === 'pending'">Loading...</div>
  <div v-else-if="error">Error: {{ error.message }}</div>
  <ul v-else>
    <li v-for="post in posts" :key="post.id">{{ post.title }}</li>
  </ul>
</template>
```

### With Options

```typescript
const { data: user } = await useFetch('/api/users/1', {
  method: 'GET',
  headers: { 'Accept': 'application/json' },
  query: { include: 'posts' },
  pick: ['name', 'email'],
  transform: (response) => response.data,
  default: () => ({ name: '', email: '' })
})
```

### POST Requests

```typescript
const { data } = await useFetch('/api/users', {
  method: 'POST',
  body: { name: 'John', email: 'john@example.com' }
})
```

## useAsyncData

For non-URL data sources or complex fetching logic:

```typescript
const { data: users } = await useAsyncData('users', () => {
  return $fetch('/api/users', {
    headers: useRequestHeaders(['cookie'])
  })
})
```

### With External APIs

```typescript
const { data: weather } = await useAsyncData('weather', async () => {
  const [current, forecast] = await Promise.all([
    $fetch('https://api.weather.com/current'),
    $fetch('https://api.weather.com/forecast')
  ])
  return { current, forecast }
})
```

### Key Differences from useFetch

`useFetch(url, opts)` is shorthand for `useAsyncData(url, () => $fetch(url, opts))`. Use `useAsyncData` when:
- Fetching from non-HTTP sources (databases, CMS SDKs)
- Combining multiple API calls into one data object
- Adding custom pre/post-processing logic

## $fetch

Direct HTTP requests using [ofetch](https://github.com/unjs/ofetch). Not SSR-safe for initial data loading:

```vue
<script setup>
// Use for client-side interactions, NOT initial page data
async function submitForm(formData: FormData) {
  const result = await $fetch('/api/submit', {
    method: 'POST',
    body: formData
  })
}

async function deleteItem(id: string) {
  await $fetch(`/api/items/${id}`, { method: 'DELETE' })
  await refreshNuxtData('items') // Refresh cached data
}
</script>
```

`$fetch` is auto-imported globally. On the server, it calls API routes directly (no HTTP roundtrip).

## Return Values

All composables (`useFetch`, `useAsyncData`) return:

```typescript
const {
  data,       // Ref<T | null> — the fetched data
  status,     // Ref<'idle' | 'pending' | 'success' | 'error'>
  error,      // Ref<Error | null> — error object if failed
  refresh,    // () => Promise<void> — re-execute the fetch
  execute,    // () => Promise<void> — alias for refresh
  clear       // () => void — set data to undefined, clear error
} = await useFetch('/api/data')
```

## Options

### Lazy Loading

Don't block navigation while fetching:

```typescript
const { data, status } = useFetch('/api/posts', { lazy: true })
// Page renders immediately, data arrives asynchronously
```

Equivalent shorthand:

```typescript
const { data, status } = useLazyFetch('/api/posts')
const { data, status } = useLazyAsyncData('key', fetchFn)
```

### Server-Only / Client-Only

```typescript
// Fetch only on the server (skip during client hydration)
const { data } = await useFetch('/api/secret', { server: true }) // default

// Fetch only on the client (skip during SSR)
const { data } = await useFetch('/api/comments', { server: false })
```

### Watch — Reactive Refetching

```typescript
const page = ref(1)
const category = ref('all')

const { data } = await useFetch('/api/posts', {
  query: { page, category },
  watch: [page, category] // Refetch when these change
})
```

### Pick and Transform

Reduce payload size by selecting specific fields:

```typescript
// Pick specific fields
const { data } = await useFetch('/api/mountains/everest', {
  pick: ['title', 'description']
})

// Transform the response
const { data } = await useFetch('/api/posts', {
  transform: (posts) => posts.map(p => ({
    id: p.id,
    title: p.title,
    summary: p.content.slice(0, 100)
  }))
})
```

### Immediate — Deferred Execution

```typescript
const { data, status, execute } = await useFetch('/api/comments', {
  immediate: false // Don't fetch until execute() is called
})

// Trigger manually
async function loadComments() {
  await execute()
}
```

### Default Values

```typescript
const { data } = await useFetch('/api/users', {
  default: () => [] // data.value starts as [] instead of null
})
```

### Custom Cache Behavior

```typescript
const { data } = await useFetch('/api/config', {
  getCachedData: (key, nuxtApp) => {
    return nuxtApp.payload.data[key] || nuxtApp.static.data[key]
  }
})
```

## Caching and Keys

### Automatic Key Generation

`useFetch` generates cache keys from:
- Request URL
- Fetch options (method, query, body)
- Source file location

`useAsyncData` uses the first string argument as the key:

```typescript
// Explicit key
const { data } = await useAsyncData('user-profile', () => fetchProfile())

// Auto-generated key (from function arguments)
const { data } = await useAsyncData(() => fetchProfile())
```

### Shared Data Rules

When multiple components use the same key, these options must match:
- Handler function, `deep`, `transform`, `pick`, `getCachedData`, `default`

These can safely differ between consumers:
- `server`, `lazy`, `immediate`, `dedupe`, `watch`

### Deduplication

```typescript
const { data } = await useFetch('/api/posts', {
  dedupe: 'cancel'  // Cancel previous in-flight request (default)
  // dedupe: 'defer' // Wait for existing request to complete
})
```

## Refreshing Data

### Refresh Specific Data

```typescript
const { data, refresh } = await useFetch('/api/posts')

async function onNewPost() {
  await $fetch('/api/posts', { method: 'POST', body: newPost })
  await refresh() // Refetch posts
}
```

### Refresh All Data

```typescript
// Refresh all useAsyncData/useFetch in the current page
await refreshNuxtData()

// Refresh specific keys
await refreshNuxtData('posts')
await refreshNuxtData(['posts', 'comments'])
```

### Clear Cached Data

```typescript
// Clear all cached data
clearNuxtData()

// Clear specific key
clearNuxtData('posts')

// Clear with predicate
clearNuxtData(key => key.startsWith('user-'))
```

## Parallel Requests

Avoid request waterfalls by fetching data in parallel:

```typescript
// Sequential (slow) — each waits for the previous
const { data: user } = await useFetch('/api/user')
const { data: posts } = await useFetch(`/api/users/${user.value.id}/posts`)

// Parallel (fast) — independent requests
const [{ data: users }, { data: categories }] = await Promise.all([
  useFetch('/api/users'),
  useFetch('/api/categories')
])
```

For `useAsyncData` with multiple `$fetch` calls:

```typescript
const { data } = await useAsyncData('dashboard', async () => {
  const [users, stats, activity] = await Promise.all([
    $fetch('/api/users'),
    $fetch('/api/stats'),
    $fetch('/api/activity')
  ])
  return { users, stats, activity }
})
```

## Error Handling

```vue
<script setup>
const { data, error } = await useFetch('/api/posts')

// Handle errors programmatically
watch(error, (err) => {
  if (err) {
    console.error('Fetch failed:', err.message)
  }
})
</script>

<template>
  <div v-if="error">
    <p>Failed to load: {{ error.statusCode }}</p>
    <button @click="refresh()">Retry</button>
  </div>
  <div v-else>
    {{ data }}
  </div>
</template>
```

### Error Types

```typescript
const { error } = await useFetch('/api/data')
// error.value is a NuxtError with:
// - statusCode: number
// - statusMessage: string
// - message: string
// - data: any
```

## Common Pitfalls

- **Using `$fetch` for page data** — Causes double-fetching during SSR. The server fetches, sends HTML, then the client fetches again. Use `useFetch` or `useAsyncData` instead.
- **Calling composables outside `<script setup>`** — `useFetch` and `useAsyncData` must be called in `<script setup>`, `setup()`, or a Nuxt plugin. They cannot be called in event handlers or lifecycle hooks.
- **Not awaiting in `<script setup>`** — Without `await`, the component renders before data is ready. Use `await` to block rendering or `lazy: true` to render immediately with a loading state.
- **Mutating `data.value` directly** — Use `refresh()` to update data. Direct mutation can cause hydration mismatches.
- **Missing `server: false` for auth-dependent data** — If an endpoint requires client-side auth tokens not available during SSR, set `server: false`.
