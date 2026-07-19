# Migration and Recipes

> Source: https://zustand.docs.pmnd.rs/reference/migrations/migrating-to-v5

## Table of Contents
- [Migrating from v4 to v5](#migrating-from-v4-to-v5)
- [Migrating from Redux](#migrating-from-redux)
- [Migrating from React Context](#migrating-from-react-context)
- [Common Recipes](#common-recipes)
- [Undo/Redo Pattern](#undoredo-pattern)
- [Computed Properties](#computed-properties)

## Migrating from v4 to v5

### Breaking Changes

1. **React 18+ required** — Zustand v5 uses native `useSyncExternalStore` (dropped `use-sync-external-store` shim)
2. **TypeScript 4.5+ required**
3. **ES2017+ target** — ES5 no longer supported
4. **Custom equality removed from `create`** — Use `createWithEqualityFn` instead
5. **`setState` replace mode** — Must provide complete state when `replace=true`
6. **Persist initial state** — No longer stored during creation

### Migration Steps

```typescript
// v4 — custom equality on create
import { create } from 'zustand'
import { shallow } from 'zustand/shallow'
const useStore = create(storeFn, shallow) // ❌ No longer supported

// v5 — use createWithEqualityFn or useShallow
import { createWithEqualityFn } from 'zustand/traditional'
import { shallow } from 'zustand/shallow'
const useStore = createWithEqualityFn(storeFn, shallow) // ✅

// OR use useShallow per-selector (preferred)
import { useShallow } from 'zustand/react/shallow'
const data = useStore(useShallow((s) => ({ a: s.a, b: s.b }))) // ✅
```

**setState replace mode:**
```typescript
// v4 — partial state with replace was allowed (but incorrect)
store.setState({}, true) // ❌ Invalid in v5

// v5 — replace requires complete state
store.setState({ count: 0, name: '', items: [] }, true) // ✅
```

**Recommended migration path:**
1. Update to latest v4 first (shows deprecation warnings)
2. Replace deprecated `createContext` usage
3. Switch custom equality to `useShallow` or `createWithEqualityFn`
4. Update to v5
5. Fix any remaining TypeScript errors

## Migrating from Redux

### Conceptual Mapping

| Redux | Zustand |
|-------|---------|
| `createSlice` | Slice pattern or inline store |
| `useSelector` | `useStore(selector)` |
| `useDispatch` + `dispatch(action())` | `useStore(s => s.action)` direct call |
| `Provider` + `configureStore` | Module-level `create()` (no provider) |
| `createAsyncThunk` | Async function in store |
| `extraReducers` | Cross-slice access via `get()` |
| `RTK Query` | TanStack Query (separate concern) |

### Before (Redux Toolkit):
```typescript
// counterSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit'

const counterSlice = createSlice({
  name: 'counter',
  initialState: { value: 0 },
  reducers: {
    increment: (state) => { state.value += 1 },
    decrement: (state) => { state.value -= 1 },
    incrementByAmount: (state, action: PayloadAction<number>) => {
      state.value += action.payload
    },
  },
})

// Component
function Counter() {
  const count = useSelector((state: RootState) => state.counter.value)
  const dispatch = useDispatch()
  return (
    <button onClick={() => dispatch(counterSlice.actions.increment())}>
      {count}
    </button>
  )
}
```

### After (Zustand):
```typescript
// counterStore.ts
import { create } from 'zustand'

interface CounterState {
  value: number
  increment: () => void
  decrement: () => void
  incrementByAmount: (amount: number) => void
}

const useCounterStore = create<CounterState>()((set) => ({
  value: 0,
  increment: () => set((s) => ({ value: s.value + 1 })),
  decrement: () => set((s) => ({ value: s.value - 1 })),
  incrementByAmount: (amount) => set((s) => ({ value: s.value + amount })),
}))

// Component — no Provider, no dispatch
function Counter() {
  const count = useCounterStore((s) => s.value)
  const increment = useCounterStore((s) => s.increment)
  return <button onClick={increment}>{count}</button>
}
```

### Async Redux Thunk → Zustand:
```typescript
// Redux
const fetchUser = createAsyncThunk('user/fetch', async (userId: string) => {
  return await api.getUser(userId)
})

// Zustand
const useUserStore = create<UserState>()((set) => ({
  user: null,
  isLoading: false,
  fetchUser: async (userId: string) => {
    set({ isLoading: true })
    const user = await api.getUser(userId)
    set({ user, isLoading: false })
  },
}))
```

## Migrating from React Context

### Before (Context + useReducer):
```typescript
const AppContext = createContext<AppState | null>(null)

function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

function Counter() {
  const { state, dispatch } = useContext(AppContext)!
  return (
    <button onClick={() => dispatch({ type: 'INCREMENT' })}>
      {state.count}
    </button>
  )
}
```

### After (Zustand):
```typescript
const useStore = create<AppState>()((set) => ({
  count: 0,
  increment: () => set((s) => ({ count: s.count + 1 })),
}))

// No Provider needed! Remove the wrapper entirely.
function Counter() {
  const count = useStore((s) => s.count)
  const increment = useStore((s) => s.increment)
  return <button onClick={increment}>{count}</button>
}
```

**Benefits of migration:**
- Remove Provider nesting (no "provider hell")
- Automatic selective re-rendering (Context re-renders all consumers)
- Access state outside React components
- Built-in persistence, devtools, middleware

## Common Recipes

**Reset all state:**
```typescript
const initialState = {
  count: 0,
  items: [],
  filter: 'all' as const,
}

interface StoreState extends typeof initialState {
  increment: () => void
  reset: () => void
}

const useStore = create<StoreState>()((set) => ({
  ...initialState,
  increment: () => set((s) => ({ count: s.count + 1 })),
  reset: () => set(initialState),
}))
```

**Map-like state (Record<id, entity>):**
```typescript
interface EntityState<T extends { id: string }> {
  entities: Record<string, T>
  ids: string[]
  upsert: (entity: T) => void
  remove: (id: string) => void
  getById: (id: string) => T | undefined
}

const useEntityStore = create<EntityState<User>>()((set, get) => ({
  entities: {},
  ids: [],
  upsert: (entity) =>
    set((state) => ({
      entities: { ...state.entities, [entity.id]: entity },
      ids: state.ids.includes(entity.id)
        ? state.ids
        : [...state.ids, entity.id],
    })),
  remove: (id) =>
    set((state) => {
      const { [id]: _, ...rest } = state.entities
      return { entities: rest, ids: state.ids.filter((i) => i !== id) }
    }),
  getById: (id) => get().entities[id],
}))
```

## Undo/Redo Pattern

```typescript
interface HistoryState<T> {
  past: T[]
  present: T
  future: T[]
  set: (newPresent: T) => void
  undo: () => void
  redo: () => void
  canUndo: boolean
  canRedo: boolean
}

function createHistoryStore<T>(initialPresent: T) {
  return create<HistoryState<T>>()((set, get) => ({
    past: [],
    present: initialPresent,
    future: [],
    canUndo: false,
    canRedo: false,

    set: (newPresent) =>
      set((state) => ({
        past: [...state.past, state.present],
        present: newPresent,
        future: [],
        canUndo: true,
        canRedo: false,
      })),

    undo: () => {
      const { past, present, future } = get()
      if (past.length === 0) return
      const previous = past[past.length - 1]
      set({
        past: past.slice(0, -1),
        present: previous,
        future: [present, ...future],
        canUndo: past.length > 1,
        canRedo: true,
      })
    },

    redo: () => {
      const { past, present, future } = get()
      if (future.length === 0) return
      const next = future[0]
      set({
        past: [...past, present],
        present: next,
        future: future.slice(1),
        canUndo: true,
        canRedo: future.length > 1,
      })
    },
  }))
}

// Usage
const useDrawingHistory = createHistoryStore<DrawingState>(emptyCanvas)
```

## Computed Properties

Zustand doesn't have built-in computed/derived state. Here are the patterns:

**Selector-based (no caching, recalculates on each render):**
```typescript
// Simple derived value — fine for cheap computations
const totalPrice = useCartStore(
  (s) => s.items.reduce((sum, i) => sum + i.price * i.qty, 0)
)
```

**useMemo in component (cached per component):**
```typescript
function CartSummary() {
  const items = useCartStore((s) => s.items)
  const { total, itemCount } = useMemo(() => ({
    total: items.reduce((sum, i) => sum + i.price * i.qty, 0),
    itemCount: items.reduce((sum, i) => sum + i.qty, 0),
  }), [items])

  return <span>{itemCount} items — ${total.toFixed(2)}</span>
}
```

**Store-level derived (computed on state change):**
```typescript
import { subscribeWithSelector } from 'zustand/middleware'

const useCartStore = create<CartState>()(
  subscribeWithSelector((set) => ({
    items: [],
    total: 0, // Derived, kept in sync

    addItem: (item) =>
      set((state) => {
        const items = [...state.items, item]
        return {
          items,
          total: items.reduce((s, i) => s + i.price * i.qty, 0),
        }
      }),
  }))
)
```
