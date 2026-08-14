# Nuxt — State Management

> Source: [nuxt.com/docs/getting-started/state-management](https://nuxt.com/docs/getting-started/state-management)

## Table of Contents

- [useState Composable](#usestate-composable)
- [Composable-Based State](#composable-based-state)
- [Pinia Integration](#pinia-integration)
- [SSR State Safety](#ssr-state-safety)
- [Shared State Patterns](#shared-state-patterns)
- [Common Pitfalls](#common-pitfalls)

## useState Composable

`useState` is an SSR-friendly replacement for `ref()`. It creates reactive, shared state that persists through server-side rendering and hydration.

```typescript
// Basic usage with a unique key
const counter = useState('counter', () => 0)

// Type-safe usage
const user = useState<User | null>('user', () => null)
```

### Key Characteristics

- **SSR-safe** — values survive server-to-client hydration
- **Shared** — components using the same key reference identical state
- **Serializable** — data must be JSON-compatible (no classes, functions, symbols)
- **Unique keys** — each `useState` call requires a globally unique string key

### Basic Example

```vue
<!-- app/pages/counter.vue -->
<script setup>
const count = useState('count', () => 0)
</script>

<template>
  <div>
    <p>Count: {{ count }}</p>
    <button @click="count++">Increment</button>
  </div>
</template>
```

The state persists across page navigations within the same session.

## Composable-Based State

Wrap `useState` in composable functions for reusable, type-safe state:

```typescript
// app/composables/useCounter.ts
export const useCounter = () => {
  const count = useState('counter', () => 0)

  function increment() {
    count.value++
  }

  function decrement() {
    count.value--
  }

  function reset() {
    count.value = 0
  }

  return { count: readonly(count), increment, decrement, reset }
}
```

```vue
<!-- Any component — auto-imported -->
<script setup>
const { count, increment, decrement } = useCounter()
</script>
```

### Complex State Composables

```typescript
// app/composables/useAuth.ts
export const useAuth = () => {
  const user = useState<User | null>('auth-user', () => null)
  const isAuthenticated = computed(() => !!user.value)

  async function login(credentials: LoginCredentials) {
    const data = await $fetch('/api/auth/login', {
      method: 'POST',
      body: credentials
    })
    user.value = data.user
  }

  async function logout() {
    await $fetch('/api/auth/logout', { method: 'POST' })
    user.value = null
    await navigateTo('/login')
  }

  return { user: readonly(user), isAuthenticated, login, logout }
}
```

### Async State Initialization

Use `callOnce` to initialize state from an API on the server:

```vue
<!-- app/app.vue -->
<script setup>
const config = useState<SiteConfig>('site-config')

await callOnce(async () => {
  config.value = await $fetch('/api/config')
})
</script>
```

`callOnce` ensures the function runs only once during SSR, not again on the client.

## Pinia Integration

Pinia is Vue's official state management library. Install via the Nuxt module:

```bash
npx nuxt module add pinia
```

### Defining a Store

```typescript
// app/stores/cart.ts
import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const total = computed(() =>
    items.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
  )

  function addItem(product: Product) {
    const existing = items.value.find(i => i.id === product.id)
    if (existing) {
      existing.quantity++
    } else {
      items.value.push({ ...product, quantity: 1 })
    }
  }

  function removeItem(id: string) {
    items.value = items.value.filter(i => i.id !== id)
  }

  return { items, total, addItem, removeItem }
})
```

### Using a Store

```vue
<script setup>
const cart = useCartStore()
</script>

<template>
  <div>
    <p>Total: ${{ cart.total }}</p>
    <ul>
      <li v-for="item in cart.items" :key="item.id">
        {{ item.name }} x{{ item.quantity }}
        <button @click="cart.removeItem(item.id)">Remove</button>
      </li>
    </ul>
  </div>
</template>
```

### Pinia with SSR

Pinia automatically handles SSR state serialization. For API calls within stores:

```typescript
export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile | null>(null)

  async function fetchProfile() {
    profile.value = await $fetch('/api/profile')
  }

  return { profile, fetchProfile }
})
```

### useState vs Pinia

| Feature | useState | Pinia |
|---------|----------|-------|
| Setup needed | None (built-in) | Requires `@pinia/nuxt` module |
| Complexity | Simple key-value state | Full store pattern with actions |
| DevTools | Basic | Full Pinia DevTools integration |
| Persistence | Requires manual serialization | Plugins available |
| Best for | Simple shared state | Complex application state |

Use `useState` for simple shared values. Use Pinia when you need organized stores with actions, getters, and DevTools support.

## SSR State Safety

### The Module-Level ref() Problem

Never create reactive state at the module level outside of `<script setup>` or `setup()`:

```typescript
// WRONG — state leaks between server requests
const count = ref(0)

export function useCount() {
  return count // Shared across all users on the server
}
```

```typescript
// CORRECT — useState isolates state per request
export function useCount() {
  return useState('count', () => 0)
}
```

On the server, module-level `ref()` creates a singleton shared across all incoming requests. This causes:
- **Data leakage** — one user sees another user's data
- **Memory leaks** — state accumulates across requests

### Rules for SSR-Safe State

1. Always use `useState()` for shared reactive state
2. Create `ref()` and `reactive()` only inside `<script setup>` or `setup()`
3. Ensure state values are JSON-serializable
4. Use `callOnce` for one-time server-side initialization

## Shared State Patterns

### Feature Flags

```typescript
// app/composables/useFeatureFlags.ts
export const useFeatureFlags = () => {
  const flags = useState<Record<string, boolean>>('feature-flags', () => ({}))

  function isEnabled(flag: string): boolean {
    return flags.value[flag] ?? false
  }

  return { flags: readonly(flags), isEnabled }
}
```

### Toast Notifications

```typescript
// app/composables/useToast.ts
interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
}

export const useToast = () => {
  const toasts = useState<Toast[]>('toasts', () => [])

  function show(message: string, type: Toast['type'] = 'info') {
    const id = crypto.randomUUID()
    toasts.value.push({ id, message, type })
    setTimeout(() => dismiss(id), 5000)
  }

  function dismiss(id: string) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return { toasts: readonly(toasts), show, dismiss }
}
```

### Theme State

```typescript
// app/composables/useTheme.ts
export const useTheme = () => {
  const theme = useState<'light' | 'dark'>('theme', () => 'light')

  function toggle() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return { theme: readonly(theme), toggle }
}
```

## Common Pitfalls

- **Non-serializable state** — `useState` values must be JSON-compatible. Classes, functions, `Map`, `Set`, and `Symbol` values will cause hydration errors.
- **Key collisions** — Two different `useState` calls with the same key will share state, potentially causing bugs. Use descriptive, unique keys.
- **Module-level refs** — `ref()` at the module level causes cross-request state leakage on the server. Always use `useState()` for shared state.
- **Pinia without the module** — Calling `useStore()` without installing `@pinia/nuxt` causes a runtime error. Always add the module first.
- **Overusing useState for local state** — Component-local state that doesn't need to persist across navigation should use `ref()` inside `<script setup>`, not `useState()`.
