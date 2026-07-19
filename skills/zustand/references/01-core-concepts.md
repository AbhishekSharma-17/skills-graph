# Core Concepts

> Source: https://zustand.docs.pmnd.rs

## Table of Contents
- [Creating a Store](#creating-a-store)
- [Reading State with Selectors](#reading-state-with-selectors)
- [Updating State with set](#updating-state-with-set)
- [Accessing Full State with get](#accessing-full-state-with-get)
- [Subscribing Outside React](#subscribing-outside-react)
- [Store API Methods](#store-api-methods)
- [Vanilla Stores](#vanilla-stores)

## Creating a Store

The `create` function is the primary API. It takes a state creator function that receives `set` and `get` parameters:

```typescript
import { create } from 'zustand'

interface TodoState {
  todos: Todo[]
  filter: 'all' | 'active' | 'completed'
  addTodo: (text: string) => void
  toggleTodo: (id: string) => void
  setFilter: (filter: TodoState['filter']) => void
}

const useTodoStore = create<TodoState>()((set, get) => ({
  todos: [],
  filter: 'all',
  addTodo: (text) =>
    set((state) => ({
      todos: [...state.todos, { id: crypto.randomUUID(), text, done: false }],
    })),
  toggleTodo: (id) =>
    set((state) => ({
      todos: state.todos.map((t) =>
        t.id === id ? { ...t, done: !t.done } : t
      ),
    })),
  setFilter: (filter) => set({ filter }),
}))
```

The returned `useTodoStore` is both a React hook and an object with utility methods (`getState`, `setState`, `subscribe`).

## Reading State with Selectors

Pass a selector function to the hook to subscribe to specific state:

```typescript
function TodoCount() {
  // Only re-renders when todos array changes
  const count = useTodoStore((state) => state.todos.length)
  return <span>{count} todos</span>
}

function FilterButton() {
  // Only re-renders when filter changes
  const filter = useTodoStore((state) => state.filter)
  const setFilter = useTodoStore((state) => state.setFilter)
  return <button onClick={() => setFilter('active')}>{filter}</button>
}
```

**Without a selector** (subscribes to entire store — avoid in production):
```typescript
function DebugView() {
  const state = useTodoStore() // Re-renders on ANY state change
  return <pre>{JSON.stringify(state, null, 2)}</pre>
}
```

## Updating State with set

The `set` function merges state by default (like `setState` in class components):

```typescript
// Object form — merges with existing state
set({ filter: 'active' })

// Updater function form — access previous state
set((state) => ({ count: state.count + 1 }))

// Replace entire state (second argument = true)
set({ todos: [], filter: 'all' }, true)
```

**Important:** `set` performs a shallow merge at the top level only. Nested objects must be spread manually:

```typescript
// WRONG — mutates nested state
set((state) => {
  state.user.name = 'Alice' // Never mutate!
  return state
})

// CORRECT — immutable nested update
set((state) => ({
  user: { ...state.user, name: 'Alice' },
}))
```

## Accessing Full State with get

The `get` function returns the current state snapshot. Use it inside actions to read state:

```typescript
const useStore = create<State>()((set, get) => ({
  items: [],
  selectedId: null,

  getSelectedItem: () => {
    const { items, selectedId } = get()
    return items.find((item) => item.id === selectedId)
  },

  removeSelected: () => {
    const { selectedId } = get()
    if (!selectedId) return
    set((state) => ({
      items: state.items.filter((i) => i.id !== selectedId),
      selectedId: null,
    }))
  },
}))
```

## Subscribing Outside React

Access state and subscribe to changes without React hooks:

```typescript
// Read current state (non-reactive snapshot)
const currentTodos = useTodoStore.getState().todos

// Update state from anywhere
useTodoStore.setState({ filter: 'completed' })

// Subscribe to all state changes
const unsub = useTodoStore.subscribe((state, prevState) => {
  console.log('State changed:', state)
})

// Cleanup subscription
unsub()
```

**Use cases for outside-React access:**
- WebSocket message handlers
- Service workers
- Event listeners (keyboard shortcuts, resize observers)
- Third-party library integrations
- Utility/helper functions

```typescript
// WebSocket handler example
const ws = new WebSocket('wss://api.example.com')
ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  useTodoStore.setState((state) => ({
    todos: [...state.todos, data.todo],
  }))
}
```

## Store API Methods

Every store created with `create()` exposes these methods:

```typescript
const useStore = create<MyState>()(/* ... */)

// React hook (primary usage)
const value = useStore((state) => state.value)

// Get current state snapshot
const state = useStore.getState()

// Set state from outside React
useStore.setState({ key: 'value' })
useStore.setState((prev) => ({ count: prev.count + 1 }))

// Subscribe to changes
const unsub = useStore.subscribe((state, prevState) => {
  // Called on every state change
})

// Destroy store (cleanup all listeners)
useStore.destroy()
```

## Vanilla Stores

For framework-agnostic usage, use `createStore` from `zustand/vanilla`:

```typescript
import { createStore } from 'zustand/vanilla'

const store = createStore<CounterState>()((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
}))

// Use with vanilla JavaScript
store.getState().count // 0
store.getState().increment()
store.getState().count // 1

// Subscribe
const unsub = store.subscribe((state) => {
  document.getElementById('count')!.textContent = String(state.count)
})
```

**Using a vanilla store in React:**

```typescript
import { useStore } from 'zustand'
import { createStore } from 'zustand/vanilla'

const counterStore = createStore<CounterState>()(/* ... */)

function Counter() {
  const count = useStore(counterStore, (state) => state.count)
  return <span>{count}</span>
}
```

## Store Initialization Patterns

```typescript
// Lazy initialization — computed on first access
const useStore = create<State>()((set) => ({
  data: computeExpensiveDefault(),
  // ...
}))

// With initial props (factory pattern)
const createStore = (initialData: Data[]) =>
  create<State>()((set) => ({
    data: initialData,
    // ...
  }))
```

## Common Pitfalls

1. **Never mutate state directly** — Always return new objects from `set`
2. **Don't call hooks conditionally** — Standard React rules apply
3. **Avoid selecting the entire store** — Always use selectors for performance
4. **Don't create stores inside components** — Stores should be module-level singletons (unless using context pattern)
5. **set merges shallowly** — Nested objects need manual spreading (or use immer middleware)
