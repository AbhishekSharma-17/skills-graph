# TypeScript Patterns

> Source: https://zustand.docs.pmnd.rs/learn/guides/advanced-typescript

## Table of Contents
- [Basic Store Typing](#basic-store-typing)
- [The Double Parentheses Pattern](#the-double-parentheses-pattern)
- [StateCreator Type](#statecreator-type)
- [Middleware Type Annotations](#middleware-type-annotations)
- [Extracting Types](#extracting-types)
- [Generic Stores](#generic-stores)
- [Strict Typing Patterns](#strict-typing-patterns)

## Basic Store Typing

Always define an interface for your store state:

```typescript
import { create } from 'zustand'

interface CounterState {
  count: number
  increment: () => void
  decrement: () => void
  incrementBy: (amount: number) => void
  reset: () => void
}

const useCounterStore = create<CounterState>()((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
  incrementBy: (amount) => set((state) => ({ count: state.count + amount })),
  reset: () => set({ count: 0 }),
}))
```

## The Double Parentheses Pattern

Zustand v5 requires `create<State>()((set) => ...)` — note the extra `()`. This enables proper TypeScript inference, especially with middleware:

```typescript
// CORRECT — double parentheses
const useStore = create<MyState>()((set) => ({ ... }))

// WRONG — single call (type inference breaks with middleware)
const useStore = create<MyState>((set) => ({ ... }))
```

**Why?** The first call `create<MyState>()` returns a curried function that carries the type parameter. The second call `(set => ...)` provides the implementation. This separation allows TypeScript to infer middleware types correctly.

## StateCreator Type

`StateCreator` is the type for slice factory functions:

```typescript
import { StateCreator } from 'zustand'

// StateCreator<FullState, MiddlewareMutators, MiddlewareMutators, SliceState>
type StateCreator<
  T,                                          // Full state type
  Mis extends [StoreMutatorIdentifier, unknown][] = [], // Middleware in
  Mos extends [StoreMutatorIdentifier, unknown][] = [], // Middleware out
  U = T                                       // Slice return type
>
```

**Common usage patterns:**

```typescript
// Simple slice (no middleware awareness)
const createAuthSlice: StateCreator<AppState, [], [], AuthSlice> =
  (set) => ({ ... })

// Slice aware of immer middleware
const createAuthSlice: StateCreator<
  AppState,
  [['zustand/immer', never]],
  [],
  AuthSlice
> = (set) => ({ ... })

// Slice aware of persist + devtools
const createAuthSlice: StateCreator<
  AppState,
  [['zustand/persist', unknown], ['zustand/devtools', never]],
  [],
  AuthSlice
> = (set) => ({ ... })
```

## Middleware Type Annotations

Each middleware has a specific mutator identifier for TypeScript:

```typescript
// Middleware identifiers
type PersistMutator = ['zustand/persist', unknown]
type DevtoolsMutator = ['zustand/devtools', never]
type ImmerMutator = ['zustand/immer', never]
type SubscribeWithSelectorMutator = ['zustand/subscribeWithSelector', never]
```

**Fully typed store with multiple middleware:**
```typescript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

interface BearState {
  bears: number
  addBear: () => void
}

const useBearStore = create<BearState>()(
  devtools(
    persist(
      immer((set) => ({
        bears: 0,
        addBear: () => set((state) => { state.bears += 1 }),
      })),
      { name: 'bear-storage' }
    ),
    { name: 'BearStore' }
  )
)
```

## Extracting Types

Extract state type from an existing store:

```typescript
// Extract full state type from store
type StoreState = ReturnType<typeof useStore.getState>

// Extract using ExtractState utility (zustand v5)
import { ExtractState } from 'zustand'

type State = ExtractState<typeof useStore>

// For selectors
const selectCount = (state: StoreState) => state.count
const selectUser = (state: StoreState) => state.user
```

**Extracting action types:**
```typescript
interface AppState {
  // State
  count: number
  user: User | null

  // Actions
  increment: () => void
  login: (email: string) => Promise<void>
}

// Separate state from actions for partialize/persist
type AppStateData = Pick<AppState, 'count' | 'user'>
type AppActions = Omit<AppState, keyof AppStateData>
```

## Generic Stores

Create reusable store factories with generics:

```typescript
// Generic CRUD store factory
interface CrudState<T extends { id: string }> {
  items: T[]
  selectedId: string | null
  isLoading: boolean
  add: (item: T) => void
  remove: (id: string) => void
  update: (id: string, changes: Partial<T>) => void
  select: (id: string | null) => void
}

function createCrudStore<T extends { id: string }>() {
  return create<CrudState<T>>()((set) => ({
    items: [],
    selectedId: null,
    isLoading: false,

    add: (item) =>
      set((state) => ({ items: [...state.items, item] })),

    remove: (id) =>
      set((state) => ({
        items: state.items.filter((i) => i.id !== id),
        selectedId: state.selectedId === id ? null : state.selectedId,
      })),

    update: (id, changes) =>
      set((state) => ({
        items: state.items.map((i) =>
          i.id === id ? { ...i, ...changes } : i
        ),
      })),

    select: (id) => set({ selectedId: id }),
  }))
}

// Usage
interface Todo { id: string; text: string; done: boolean }
interface Project { id: string; name: string; status: string }

const useTodoStore = createCrudStore<Todo>()
const useProjectStore = createCrudStore<Project>()
```

## Strict Typing Patterns

**Discriminated unions for state machines:**
```typescript
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string }

interface FetchState<T> {
  state: AsyncState<T>
  fetch: () => Promise<void>
  reset: () => void
}

const useDataStore = create<FetchState<User[]>>()((set) => ({
  state: { status: 'idle' },

  fetch: async () => {
    set({ state: { status: 'loading' } })
    try {
      const data = await api.getUsers()
      set({ state: { status: 'success', data } })
    } catch (err) {
      set({ state: { status: 'error', error: (err as Error).message } })
    }
  },

  reset: () => set({ state: { status: 'idle' } }),
}))

// Type-safe consumption
function UserList() {
  const state = useDataStore((s) => s.state)
  switch (state.status) {
    case 'idle': return <p>Ready</p>
    case 'loading': return <Spinner />
    case 'error': return <Error message={state.error} />
    case 'success': return <List items={state.data} />
  }
}
```

**Readonly state enforcement:**
```typescript
interface ReadonlyState {
  readonly items: readonly Item[]
  readonly config: Readonly<Config>
  addItem: (item: Item) => void
}
```

**Selector type safety:**
```typescript
// Type-safe selector creator
function createSelector<T>(selector: (state: AppState) => T) {
  return selector
}

const selectActiveUsers = createSelector(
  (state) => state.users.filter((u) => u.active)
)

// Usage with useShallow
const activeUsers = useStore(useShallow(selectActiveUsers))
```

## Common TypeScript Pitfalls

1. **Missing double parentheses** — `create<State>()((set) => ...)` not `create<State>((set) => ...)`
2. **Middleware order affects types** — Mismatched `Mis`/`Mos` in StateCreator causes cryptic errors
3. **Implicit any in set callbacks** — Always type the state parameter or provide the store interface
4. **Generic stores losing inference** — Use explicit return types on factory functions
5. **v5 setState type strictness** — `set({}, true)` requires a complete state object when replace=true
