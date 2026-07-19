# Immer Middleware

> Source: https://zustand.docs.pmnd.rs

## Table of Contents
- [Why Immer](#why-immer)
- [Setup](#setup)
- [Basic Usage](#basic-usage)
- [Nested Updates](#nested-updates)
- [Array Operations](#array-operations)
- [Combining with Other Middleware](#combining-with-other-middleware)
- [Performance Considerations](#performance-considerations)
- [Patterns and Recipes](#patterns-and-recipes)

## Why Immer

Without immer, updating nested state requires manual spreading at every level:

```typescript
// Without immer — verbose and error-prone
set((state) => ({
  user: {
    ...state.user,
    address: {
      ...state.user.address,
      city: 'New York',
    },
  },
}))

// With immer — direct mutation syntax (produces immutable update)
set((state) => {
  state.user.address.city = 'New York'
})
```

Immer uses structural sharing under the hood — only the changed paths produce new references; unchanged subtrees keep their original references.

## Setup

```bash
npm install immer
```

```typescript
import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'

interface State {
  todos: Todo[]
  addTodo: (text: string) => void
  toggleTodo: (id: string) => void
}

const useTodoStore = create<State>()(
  immer((set) => ({
    todos: [],
    addTodo: (text) =>
      set((state) => {
        state.todos.push({
          id: crypto.randomUUID(),
          text,
          done: false,
        })
      }),
    toggleTodo: (id) =>
      set((state) => {
        const todo = state.todos.find((t) => t.id === id)
        if (todo) todo.done = !todo.done
      }),
  }))
)
```

## Basic Usage

With immer, the `set` function receives a mutable draft. Mutate it directly — no return value needed:

```typescript
// Mutation style (immer) — no return needed
set((state) => {
  state.count += 1
})

// You CAN still return a new object (works like without immer)
set((state) => ({ count: state.count + 1 }))

// Direct assignment
set((state) => {
  state.name = 'Alice'
  state.email = 'alice@example.com'
})
```

**Important:** When using immer, either mutate the draft OR return a new object — never do both.

## Nested Updates

Immer shines with deeply nested state:

```typescript
interface AppState {
  settings: {
    notifications: {
      email: boolean
      push: boolean
      frequency: 'realtime' | 'daily' | 'weekly'
    }
    privacy: {
      profileVisible: boolean
      searchable: boolean
    }
  }
  updateNotificationFrequency: (freq: AppState['settings']['notifications']['frequency']) => void
  toggleEmailNotifications: () => void
}

const useAppStore = create<AppState>()(
  immer((set) => ({
    settings: {
      notifications: {
        email: true,
        push: true,
        frequency: 'realtime',
      },
      privacy: {
        profileVisible: true,
        searchable: true,
      },
    },

    updateNotificationFrequency: (frequency) =>
      set((state) => {
        state.settings.notifications.frequency = frequency
      }),

    toggleEmailNotifications: () =>
      set((state) => {
        state.settings.notifications.email = !state.settings.notifications.email
      }),
  }))
)
```

## Array Operations

Immer makes array mutations natural:

```typescript
interface ListState {
  items: Item[]
  addItem: (item: Item) => void
  removeItem: (id: string) => void
  moveItem: (fromIndex: number, toIndex: number) => void
  updateItem: (id: string, updates: Partial<Item>) => void
  sortItems: (key: keyof Item) => void
}

const useListStore = create<ListState>()(
  immer((set) => ({
    items: [],

    addItem: (item) =>
      set((state) => {
        state.items.push(item)
      }),

    removeItem: (id) =>
      set((state) => {
        const index = state.items.findIndex((i) => i.id === id)
        if (index !== -1) state.items.splice(index, 1)
      }),

    moveItem: (from, to) =>
      set((state) => {
        const [item] = state.items.splice(from, 1)
        state.items.splice(to, 0, item)
      }),

    updateItem: (id, updates) =>
      set((state) => {
        const item = state.items.find((i) => i.id === id)
        if (item) Object.assign(item, updates)
      }),

    sortItems: (key) =>
      set((state) => {
        state.items.sort((a, b) =>
          String(a[key]).localeCompare(String(b[key]))
        )
      }),
  }))
)
```

## Combining with Other Middleware

Immer should be the innermost middleware:

```typescript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

// Correct order: persist > devtools > immer
const useStore = create<State>()(
  persist(
    devtools(
      immer((set) => ({
        // store with mutation syntax
        nested: { deep: { value: 0 } },
        increment: () =>
          set((state) => {
            state.nested.deep.value += 1
          }),
      })),
      { name: 'MyStore' }
    ),
    { name: 'store-key' }
  )
)
```

## Performance Considerations

**When immer helps:**
- Deeply nested state (3+ levels)
- Complex array manipulations (splice, sort, reorder)
- Multiple fields updated in one action
- Large state trees where manual spreading is error-prone

**When immer may not be needed:**
- Flat state with only primitive values
- Simple `{ key: value }` updates
- State with few properties
- Performance-critical hot paths (immer adds ~2-3ms overhead per update)

**Structural sharing:**
```typescript
set((state) => {
  state.user.name = 'Alice'
  // Only user and user.name get new references
  // state.settings, state.todos, etc. keep original references
  // Components selecting settings won't re-render
})
```

## Patterns and Recipes

**Conditional nested updates:**
```typescript
set((state) => {
  const item = state.items.find((i) => i.id === targetId)
  if (!item) return // No-op if not found (no state change produced)
  item.status = 'completed'
  item.completedAt = Date.now()
})
```

**Bulk updates:**
```typescript
set((state) => {
  for (const id of selectedIds) {
    const item = state.items.find((i) => i.id === id)
    if (item) item.selected = true
  }
})
```

**Map/Set-like patterns:**
```typescript
interface CacheState {
  cache: Record<string, CacheEntry>
  setEntry: (key: string, value: unknown) => void
  deleteEntry: (key: string) => void
  clearExpired: () => void
}

const useCacheStore = create<CacheState>()(
  immer((set) => ({
    cache: {},
    setEntry: (key, value) =>
      set((state) => {
        state.cache[key] = { value, timestamp: Date.now() }
      }),
    deleteEntry: (key) =>
      set((state) => {
        delete state.cache[key]
      }),
    clearExpired: () =>
      set((state) => {
        const now = Date.now()
        for (const [key, entry] of Object.entries(state.cache)) {
          if (now - entry.timestamp > 60_000) {
            delete state.cache[key]
          }
        }
      }),
  }))
)
```

**Replace vs mutate:**
```typescript
set((state) => {
  // Mutate: keeps structural sharing
  state.items[0].name = 'Updated'

  // Replace: creates entirely new reference for the array
  state.items = state.items.filter((i) => i.active)
  // Both are valid with immer
})
```

## Common Pitfalls

1. **Returning AND mutating** — Pick one; returning a value from an immer updater replaces the entire draft
2. **Async inside set** — Don't use async/await inside the `set` callback; perform async work outside, then call `set`
3. **Forgetting immer is innermost** — If combined with persist/devtools, immer must be the innermost wrapper
4. **Over-using immer** — For simple `{ key: value }` merges, plain `set` without immer is simpler and faster
