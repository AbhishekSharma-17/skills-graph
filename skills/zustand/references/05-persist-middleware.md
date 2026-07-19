# Persist Middleware

> Source: https://zustand.docs.pmnd.rs

## Table of Contents
- [Basic Usage](#basic-usage)
- [Storage Options](#storage-options)
- [Partialize](#partialize)
- [State Migrations](#state-migrations)
- [Hydration Control](#hydration-control)
- [Custom Storage Engines](#custom-storage-engines)
- [SSR Considerations](#ssr-considerations)
- [Advanced Patterns](#advanced-patterns)

## Basic Usage

The persist middleware automatically saves and restores state to a storage backend:

```typescript
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface UserPreferences {
  theme: 'light' | 'dark'
  fontSize: number
  sidebarOpen: boolean
  setTheme: (theme: 'light' | 'dark') => void
  setFontSize: (size: number) => void
  toggleSidebar: () => void
}

const usePreferencesStore = create<UserPreferences>()(
  persist(
    (set) => ({
      theme: 'light',
      fontSize: 14,
      sidebarOpen: true,
      setTheme: (theme) => set({ theme }),
      setFontSize: (fontSize) => set({ fontSize }),
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
    }),
    {
      name: 'user-preferences', // Key in storage
    }
  )
)
```

## Storage Options

**localStorage (default):**
```typescript
persist(storeFn, {
  name: 'my-store',
  // localStorage is the default, no need to specify
})
```

**sessionStorage:**
```typescript
persist(storeFn, {
  name: 'session-store',
  storage: createJSONStorage(() => sessionStorage),
})
```

**AsyncStorage (React Native):**
```typescript
import AsyncStorage from '@react-native-async-storage/async-storage'

persist(storeFn, {
  name: 'mobile-store',
  storage: createJSONStorage(() => AsyncStorage),
})
```

**IndexedDB (via idb-keyval):**
```typescript
import { get, set, del } from 'idb-keyval'

const indexedDBStorage = {
  getItem: async (name: string) => {
    return (await get(name)) ?? null
  },
  setItem: async (name: string, value: string) => {
    await set(name, value)
  },
  removeItem: async (name: string) => {
    await del(name)
  },
}

persist(storeFn, {
  name: 'idb-store',
  storage: createJSONStorage(() => indexedDBStorage),
})
```

## Partialize

Only persist specific parts of your state (exclude functions and transient data):

```typescript
interface AppState {
  user: User | null
  token: string | null
  isLoading: boolean    // Don't persist
  error: string | null  // Don't persist
  login: () => void     // Don't persist (functions)
  logout: () => void
}

persist(storeFn, {
  name: 'auth-store',
  partialize: (state) => ({
    user: state.user,
    token: state.token,
    // Omit isLoading, error, and action functions
  }),
})
```

**Type-safe partialize with Pick:**
```typescript
partialize: (state) =>
  Object.fromEntries(
    Object.entries(state).filter(
      ([key]) => !['isLoading', 'error'].includes(key)
    )
  ) as Pick<AppState, 'user' | 'token'>,
```

## State Migrations

Handle schema changes when persisted state structure evolves:

```typescript
persist(storeFn, {
  name: 'app-store',
  version: 2, // Current version

  migrate: (persistedState, version) => {
    const state = persistedState as any

    if (version === 0) {
      // v0 → v1: rename `darkMode` to `theme`
      state.theme = state.darkMode ? 'dark' : 'light'
      delete state.darkMode
    }

    if (version < 2) {
      // v1 → v2: add fontSize with default
      state.fontSize = state.fontSize ?? 14
    }

    return state as AppState
  },
})
```

**Migration best practices:**
- Always increment `version` when state shape changes
- Migrations should be cumulative (handle v0→v2 by running v0→v1 then v1→v2)
- Never delete old migration code — users may have very old persisted state
- Test migrations with representative old state shapes

## Hydration Control

Control when and how persisted state is loaded:

```typescript
persist(storeFn, {
  name: 'store',
  skipHydration: true, // Don't hydrate automatically
})

// Manually trigger hydration later
useStore.persist.rehydrate()
```

**Hydration event listeners:**
```typescript
const useStore = create<State>()(
  persist(storeFn, { name: 'store' })
)

// Check hydration status
const isHydrated = useStore.persist.hasHydrated()

// Listen for hydration completion
useStore.persist.onHydrate((state) => {
  console.log('Hydration started')
})

useStore.persist.onFinishHydration((state) => {
  console.log('Hydration finished', state)
})
```

**Waiting for hydration in components:**
```typescript
function App() {
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    const unsub = useStore.persist.onFinishHydration(() => {
      setHydrated(true)
    })
    // Check if already hydrated
    if (useStore.persist.hasHydrated()) {
      setHydrated(true)
    }
    return unsub
  }, [])

  if (!hydrated) return <LoadingSpinner />
  return <MainApp />
}
```

## Custom Storage Engines

Implement the `StateStorage` interface for custom backends:

```typescript
import { StateStorage } from 'zustand/middleware'

// Encrypted localStorage
const encryptedStorage: StateStorage = {
  getItem: (name) => {
    const raw = localStorage.getItem(name)
    if (!raw) return null
    return decrypt(raw)
  },
  setItem: (name, value) => {
    localStorage.setItem(name, encrypt(value))
  },
  removeItem: (name) => {
    localStorage.removeItem(name)
  },
}

persist(storeFn, {
  name: 'secure-store',
  storage: createJSONStorage(() => encryptedStorage),
})
```

**URL hash storage (shareable state):**
```typescript
const hashStorage: StateStorage = {
  getItem: (key) => {
    const params = new URLSearchParams(window.location.hash.slice(1))
    return params.get(key)
  },
  setItem: (key, value) => {
    const params = new URLSearchParams(window.location.hash.slice(1))
    params.set(key, value)
    window.location.hash = params.toString()
  },
  removeItem: (key) => {
    const params = new URLSearchParams(window.location.hash.slice(1))
    params.delete(key)
    window.location.hash = params.toString()
  },
}
```

## SSR Considerations

Avoid hydration mismatches in SSR (Next.js, Remix):

```typescript
// Pattern: skip hydration + manual rehydrate on mount
const useStore = create<State>()(
  persist(storeFn, {
    name: 'store',
    skipHydration: true,
  })
)

// In your root layout or _app.tsx
function App({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    useStore.persist.rehydrate()
  }, [])
  return <>{children}</>
}
```

**Alternative: client-only rendering for persisted state:**
```typescript
function ThemeToggle() {
  const [mounted, setMounted] = useState(false)
  const theme = useStore((s) => s.theme)

  useEffect(() => setMounted(true), [])

  if (!mounted) return <div className="w-8 h-8" /> // Placeholder
  return <button>{theme === 'dark' ? 'Light' : 'Dark'}</button>
}
```

## Advanced Patterns

**Multi-tab synchronization:**
```typescript
// Storage events fire across tabs automatically with localStorage
// For custom sync, use BroadcastChannel:
const channel = new BroadcastChannel('zustand-sync')

persist(storeFn, {
  name: 'store',
  storage: {
    getItem: (name) => localStorage.getItem(name),
    setItem: (name, value) => {
      localStorage.setItem(name, value)
      channel.postMessage({ name, value })
    },
    removeItem: (name) => localStorage.removeItem(name),
  },
})

// Listen for changes from other tabs
channel.onmessage = () => {
  useStore.persist.rehydrate()
}
```

**Clear persisted state:**
```typescript
// Remove from storage and reset to defaults
useStore.persist.clearStorage()

// Or manually
localStorage.removeItem('store-key')
useStore.setState(initialState, true)
```

**Persist options reference:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | `string` | required | Storage key |
| `storage` | `StateStorage` | `localStorage` | Storage backend |
| `partialize` | `(state) => partial` | identity | Filter persisted fields |
| `version` | `number` | `0` | Schema version |
| `migrate` | `(state, version) => state` | — | Migration function |
| `merge` | `(persisted, current) => state` | shallow merge | Custom merge strategy |
| `skipHydration` | `boolean` | `false` | Disable auto-hydration |
| `onRehydrateStorage` | `(state) => void` | — | Callback after rehydrate |
