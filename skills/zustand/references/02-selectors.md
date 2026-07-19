# Selectors and Re-rendering

> Source: https://zustand.docs.pmnd.rs

## Table of Contents
- [How Selectors Work](#how-selectors-work)
- [Basic Selectors](#basic-selectors)
- [useShallow Hook](#useshallow-hook)
- [Custom Equality Functions](#custom-equality-functions)
- [Derived State](#derived-state)
- [Selector Patterns](#selector-patterns)
- [Anti-patterns](#anti-patterns)

## How Selectors Work

Zustand uses selectors to determine which components re-render when state changes. The subscription model works as follows:

1. Component calls `useStore(selector)` during render
2. Zustand subscribes the component to the store
3. On state change, Zustand runs the selector against new state
4. Result is compared to previous result using strict equality (`===`)
5. If different, the component re-renders; if same, render is skipped

```typescript
// This component ONLY re-renders when `count` changes
function CountDisplay() {
  const count = useStore((state) => state.count)
  return <span>{count}</span>
}
```

## Basic Selectors

**Selecting a single primitive value:**
```typescript
const count = useStore((state) => state.count)
const name = useStore((state) => state.user.name)
```

**Selecting an action (stable reference):**
```typescript
const increment = useStore((state) => state.increment)
// Actions are stable — same reference across renders
```

**Selecting multiple values separately (recommended):**
```typescript
function UserProfile() {
  const name = useStore((state) => state.user.name)
  const email = useStore((state) => state.user.email)
  // Each selector creates an independent subscription
  return <div>{name} ({email})</div>
}
```

## useShallow Hook

When you need to select multiple values as an object or array, `useShallow` prevents re-renders when contents haven't changed:

```typescript
import { useShallow } from 'zustand/react/shallow'

// Without useShallow — creates new object every render, always re-renders
const { name, email } = useStore((state) => ({
  name: state.user.name,
  email: state.user.email,
})) // BUG: re-renders on ANY state change

// With useShallow — shallow compares object properties
const { name, email } = useStore(
  useShallow((state) => ({
    name: state.user.name,
    email: state.user.email,
  }))
)

// Array selection with useShallow
const [todos, filter] = useStore(
  useShallow((state) => [state.todos, state.filter])
)
```

**When to use useShallow:**
- Selecting multiple values as an object `{ a, b, c }`
- Selecting values as an array `[a, b, c]`
- Selecting a filtered/mapped subset of an array

**When NOT needed:**
- Selecting a single primitive value
- Selecting a single stable reference (action function, object identity)

## Custom Equality Functions

For fine-grained control, use `createWithEqualityFn` from `zustand/traditional`:

```typescript
import { createWithEqualityFn } from 'zustand/traditional'
import { shallow } from 'zustand/shallow'

const useStore = createWithEqualityFn<State>()(
  (set) => ({
    // ... state and actions
  }),
  shallow // Default equality for ALL selectors
)
```

**Per-selector equality (manual approach):**
```typescript
import { useStoreWithEqualityFn } from 'zustand/traditional'

function Component() {
  const data = useStoreWithEqualityFn(
    useStore,
    (state) => state.data,
    (a, b) => a.id === b.id // Custom comparison
  )
}
```

## Derived State

Compute values from state without storing them:

```typescript
// Inline derived state via selector
function ActiveTodoCount() {
  const activeCount = useTodoStore(
    (state) => state.todos.filter((t) => !t.done).length
  )
  return <span>{activeCount} active</span>
}

// Memoized derived selector (reusable)
const selectActiveTodos = (state: TodoState) =>
  state.todos.filter((t) => !t.done)

const selectCompletedCount = (state: TodoState) =>
  state.todos.filter((t) => t.done).length

function TodoList() {
  const activeTodos = useTodoStore(useShallow(selectActiveTodos))
  return <ul>{activeTodos.map(/* ... */)}</ul>
}
```

**Expensive computations (use useMemo in component):**
```typescript
function ExpensiveList() {
  const items = useStore((state) => state.items)
  const sortedItems = useMemo(
    () => items.toSorted((a, b) => a.priority - b.priority),
    [items]
  )
  return <List items={sortedItems} />
}
```

## Selector Patterns

**Parameterized selectors:**
```typescript
// Selector factory
const selectTodoById = (id: string) => (state: TodoState) =>
  state.todos.find((t) => t.id === id)

function TodoItem({ id }: { id: string }) {
  const todo = useTodoStore(selectTodoById(id))
  // Re-renders only when this specific todo changes (by reference)
  return <li>{todo?.text}</li>
}
```

**Composed selectors:**
```typescript
const selectUser = (state: AppState) => state.user
const selectUserName = (state: AppState) => selectUser(state).name
const selectIsAdmin = (state: AppState) => selectUser(state).role === 'admin'

function AdminBadge() {
  const isAdmin = useStore(selectIsAdmin)
  return isAdmin ? <Badge>Admin</Badge> : null
}
```

**Multiple stores, single component:**
```typescript
function Dashboard() {
  const user = useUserStore((s) => s.user)
  const notifications = useNotificationStore((s) => s.unreadCount)
  const theme = useThemeStore((s) => s.mode)
  return <Header user={user} badges={notifications} theme={theme} />
}
```

## Anti-patterns

**Creating new references in selectors:**
```typescript
// BAD — new object on every call, bypasses equality check
const user = useStore((state) => ({
  name: state.name,
  age: state.age,
})) // Re-renders on ANY state change!

// GOOD — use useShallow
const user = useStore(useShallow((state) => ({
  name: state.name,
  age: state.age,
})))
```

**Selecting the entire store:**
```typescript
// BAD — re-renders on every state change
const state = useStore()
const everything = useStore((s) => s)

// GOOD — select only what you need
const count = useStore((s) => s.count)
```

**Inline filter/map without useShallow:**
```typescript
// BAD — filter creates new array reference every time
const active = useStore((s) => s.todos.filter((t) => !t.done))

// GOOD — wrap with useShallow
const active = useStore(useShallow((s) => s.todos.filter((t) => !t.done)))
```

**Selector depending on props without memoization:**
```typescript
// CAUTION — new function identity every render
function Item({ id }: { id: string }) {
  // This is fine — Zustand handles it correctly
  // The selector identity doesn't matter; only its return value does
  const item = useStore((s) => s.items.find((i) => i.id === id))
  return <div>{item?.name}</div>
}
```

## Equality Check Summary

| Selection Type | Default Behavior | Fix |
|---|---|---|
| Primitive (number, string, boolean) | `===` works correctly | None needed |
| Stable reference (action function) | Same reference | None needed |
| New object `{ a, b }` | Always different | `useShallow` |
| New array `[a, b]` | Always different | `useShallow` |
| Filtered array | Always different | `useShallow` |
| Single object from store | Reference equality | Works if store reference is stable |
