# Middleware System

> Source: https://zustand.docs.pmnd.rs

## Table of Contents
- [Overview](#overview)
- [Available Middleware](#available-middleware)
- [Composition Order](#composition-order)
- [Combining Multiple Middleware](#combining-multiple-middleware)
- [DevTools Middleware](#devtools-middleware)
- [SubscribeWithSelector](#subscribewithselector)
- [Combine Middleware](#combine-middleware)
- [Custom Middleware](#custom-middleware)

## Overview

Middleware in Zustand enhances store behavior by wrapping the state creator function. Each middleware adds a specific capability (persistence, debugging, mutation syntax) without changing the store's API.

```typescript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

const useStore = create<State>()(
  devtools(
    persist(
      immer((set) => ({
        // state and actions here
      })),
      { name: 'my-store' }
    )
  )
)
```

## Available Middleware

| Middleware | Import | Purpose |
|---|---|---|
| `persist` | `zustand/middleware` | Save/restore state to storage |
| `devtools` | `zustand/middleware` | Redux DevTools integration |
| `immer` | `zustand/middleware/immer` | Mutable-style state updates |
| `subscribeWithSelector` | `zustand/middleware` | Granular subscriptions with selectors |
| `combine` | `zustand/middleware` | Infer state type from initial state |

## Composition Order

The recommended middleware order (outermost to innermost):

```
persist → devtools → subscribeWithSelector → immer → store
```

This ensures:
1. **Immer** (innermost) — processes mutations first
2. **SubscribeWithSelector** — fires selectors on the processed state
3. **DevTools** — logs the final state transitions
4. **Persist** (outermost) — serializes the stable result

```typescript
const useStore = create<State>()(
  persist(                          // 4. Outermost: persist result
    devtools(                       // 3. Log state changes
      subscribeWithSelector(        // 2. Enable selector subscriptions
        immer((set) => ({           // 1. Innermost: enable mutations
          // store definition
        }))
      )
    ),
    { name: 'store-key' }
  )
)
```

## Combining Multiple Middleware

**Persist + DevTools (most common):**
```typescript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface SettingsState {
  theme: 'light' | 'dark'
  language: string
  setTheme: (theme: 'light' | 'dark') => void
  setLanguage: (lang: string) => void
}

const useSettingsStore = create<SettingsState>()(
  devtools(
    persist(
      (set) => ({
        theme: 'light',
        language: 'en',
        setTheme: (theme) => set({ theme }),
        setLanguage: (language) => set({ language }),
      }),
      { name: 'settings-storage' }
    ),
    { name: 'SettingsStore' }
  )
)
```

**All middleware combined:**
```typescript
import { create } from 'zustand'
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

const useStore = create<AppState>()(
  devtools(
    persist(
      subscribeWithSelector(
        immer((set, get) => ({
          users: [],
          addUser: (user) =>
            set((state) => {
              state.users.push(user) // Immer allows mutation syntax
            }),
        }))
      ),
      { name: 'app-store' }
    ),
    { name: 'AppStore', enabled: process.env.NODE_ENV === 'development' }
  )
)
```

## DevTools Middleware

Connects your store to Redux DevTools browser extension for time-travel debugging:

```typescript
import { devtools } from 'zustand/middleware'

const useStore = create<State>()(
  devtools(
    (set) => ({
      count: 0,
      increment: () =>
        set(
          (state) => ({ count: state.count + 1 }),
          undefined,
          'increment' // Action name shown in DevTools
        ),
    }),
    {
      name: 'CounterStore',       // Store name in DevTools
      enabled: true,               // Enable/disable (default: true in dev)
      anonymousActionType: 'unknown', // Name for unlabeled actions
    }
  )
)
```

**Named actions for DevTools:**
```typescript
set((state) => ({ count: state.count + 1 }), undefined, 'counter/increment')
set({ loading: true }, undefined, 'fetch/start')
set({ data, loading: false }, undefined, 'fetch/success')
```

**DevTools options:**
```typescript
devtools(storeFn, {
  name: 'StoreName',            // Display name in extension
  enabled: true,                // Toggle on/off
  anonymousActionType: 'action', // Default action name
  store: 'storeName',           // For multiple stores
})
```

## SubscribeWithSelector

Enables subscribing to specific state slices outside React components:

```typescript
import { subscribeWithSelector } from 'zustand/middleware'

const useStore = create<State>()(
  subscribeWithSelector((set) => ({
    count: 0,
    name: '',
    increment: () => set((s) => ({ count: s.count + 1 })),
  }))
)

// Subscribe to a specific slice
const unsub = useStore.subscribe(
  (state) => state.count,           // Selector
  (count, previousCount) => {       // Listener (fires only when count changes)
    console.log('Count changed:', previousCount, '->', count)
  },
  {
    equalityFn: Object.is,          // Custom equality (default: Object.is)
    fireImmediately: true,          // Fire listener immediately with current value
  }
)
```

**Use cases:**
```typescript
// Sync to localStorage manually
useStore.subscribe(
  (state) => state.theme,
  (theme) => {
    document.documentElement.setAttribute('data-theme', theme)
  }
)

// Analytics tracking
useStore.subscribe(
  (state) => state.cart.items.length,
  (count, prev) => {
    if (count > prev) analytics.track('item_added')
  }
)

// Cross-store synchronization
useAuthStore.subscribe(
  (state) => state.user,
  (user) => {
    if (!user) useCartStore.getState().clearCart()
  }
)
```

## Combine Middleware

Infers the state type from an initial state object (less common since TypeScript is typical):

```typescript
import { combine } from 'zustand/middleware'

const useStore = create(
  combine(
    { count: 0, name: 'default' }, // Initial state (type inferred)
    (set) => ({
      increment: () => set((s) => ({ count: s.count + 1 })),
      setName: (name: string) => set({ name }),
    })
  )
)
```

## Custom Middleware

Create your own middleware by wrapping the state creator:

```typescript
import { StateCreator, StoreMutatorIdentifier } from 'zustand'

type Logger = <
  T,
  Mps extends [StoreMutatorIdentifier, unknown][] = [],
  Mcs extends [StoreMutatorIdentifier, unknown][] = []
>(
  f: StateCreator<T, Mps, Mcs>,
  name?: string
) => StateCreator<T, Mps, Mcs>

const logger: Logger = (f, name) => (set, get, store) => {
  const loggedSet: typeof set = (...args) => {
    const prev = get()
    set(...(args as Parameters<typeof set>))
    const next = get()
    console.log(`[${name || 'store'}]`, { prev, next })
  }
  return f(loggedSet, get, store)
}

// Usage
const useStore = create<State>()(
  logger(
    (set) => ({
      count: 0,
      increment: () => set((s) => ({ count: s.count + 1 })),
    }),
    'CounterStore'
  )
)
```

## Middleware Pitfalls

1. **Wrong composition order** — Persist should wrap devtools, not the other way around, to avoid persisting debug metadata
2. **Applying middleware inside slices** — Always apply at the combined store level, not per-slice
3. **DevTools in production** — Disable with `enabled: process.env.NODE_ENV === 'development'`
4. **Type complexity** — When TypeScript errors arise from middleware stacking, simplify by reducing middleware or using explicit type annotations
