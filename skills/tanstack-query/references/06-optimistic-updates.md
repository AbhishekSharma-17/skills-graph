# Optimistic Updates

> Source: [TanStack Query Docs — Optimistic Updates](https://tanstack.com/query/v5/docs/framework/react/guides/optimistic-updates)

## Table of Contents

- [Overview](#overview)
- [Cache-Based Optimistic Updates](#cache-based-optimistic-updates)
- [Step-by-Step Breakdown](#step-by-step-breakdown)
- [Updating a Single Item](#updating-a-single-item)
- [Adding to a List](#adding-to-a-list)
- [Removing from a List](#removing-from-a-list)
- [UI-Based Optimistic Updates](#ui-based-optimistic-updates)
- [Choosing Between Approaches](#choosing-between-approaches)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Optimistic updates update the UI **immediately** before the server confirms the change. If the mutation fails, the UI **rolls back** to the previous state.

Two approaches:
1. **Cache-based** — Modify the query cache in `onMutate`, rollback in `onError`
2. **UI-based** — Use mutation state (`variables`, `isPending`) to show optimistic data

---

## Cache-Based Optimistic Updates

The full pattern involves three callbacks on `useMutation`:

```tsx
const queryClient = useQueryClient()

const updateTodo = useMutation({
  mutationFn: (updatedTodo: Todo) => api.updateTodo(updatedTodo),

  onMutate: async (newTodo, context) => {
    // 1. Cancel outgoing refetches to prevent overwriting optimistic update
    await context.client.cancelQueries({ queryKey: ['todos', newTodo.id] })

    // 2. Snapshot the previous value for rollback
    const previousTodo = context.client.getQueryData(['todos', newTodo.id])

    // 3. Optimistically update the cache
    context.client.setQueryData(['todos', newTodo.id], newTodo)

    // 4. Return snapshot for rollback
    return { previousTodo }
  },

  onError: (err, newTodo, onMutateResult, context) => {
    // Rollback to previous value on error
    context.client.setQueryData(
      ['todos', newTodo.id],
      onMutateResult.previousTodo,
    )
  },

  onSettled: (data, error, variables, onMutateResult, context) => {
    // Always refetch to ensure cache matches server
    context.client.invalidateQueries({ queryKey: ['todos', variables.id] })
  },
})
```

---

## Step-by-Step Breakdown

### Step 1: Cancel Outgoing Queries

```tsx
await context.client.cancelQueries({ queryKey: ['todos', newTodo.id] })
```

Prevents in-flight refetches from overwriting the optimistic update with stale server data.

### Step 2: Snapshot Previous State

```tsx
const previousTodo = context.client.getQueryData(['todos', newTodo.id])
```

Save the current cache value so you can restore it if the mutation fails.

### Step 3: Update Cache Optimistically

```tsx
context.client.setQueryData(['todos', newTodo.id], newTodo)
```

Immediately update the cache with the expected new value. Components see this instantly.

### Step 4: Return Rollback Data

```tsx
return { previousTodo }
```

The return value of `onMutate` is passed as `onMutateResult` to `onError` and `onSettled`.

### Step 5: Rollback on Error

```tsx
onError: (err, newTodo, onMutateResult, context) => {
  context.client.setQueryData(
    ['todos', newTodo.id],
    onMutateResult.previousTodo,
  )
}
```

### Step 6: Settle (Always)

```tsx
onSettled: (data, error, variables, onMutateResult, context) => {
  context.client.invalidateQueries({ queryKey: ['todos', variables.id] })
}
```

Invalidate to sync cache with server truth, regardless of success or failure.

---

## Updating a Single Item

```tsx
useMutation({
  mutationFn: (todo: Todo) => api.updateTodo(todo),
  onMutate: async (newTodo, context) => {
    await context.client.cancelQueries({ queryKey: ['todos', newTodo.id] })

    const previousTodo = context.client.getQueryData<Todo>(['todos', newTodo.id])
    context.client.setQueryData(['todos', newTodo.id], newTodo)

    return { previousTodo }
  },
  onError: (err, newTodo, result, context) => {
    context.client.setQueryData(['todos', newTodo.id], result.previousTodo)
  },
  onSettled: (data, error, variables, result, context) => {
    context.client.invalidateQueries({ queryKey: ['todos', variables.id] })
  },
})
```

---

## Adding to a List

```tsx
useMutation({
  mutationFn: (newTodo: CreateTodoInput) => api.createTodo(newTodo),
  onMutate: async (newTodo, context) => {
    await context.client.cancelQueries({ queryKey: ['todos'] })

    const previousTodos = context.client.getQueryData<Todo[]>(['todos'])

    // Add optimistic item with a temporary ID
    context.client.setQueryData<Todo[]>(['todos'], (old) => [
      ...(old ?? []),
      { ...newTodo, id: `temp-${Date.now()}`, createdAt: new Date().toISOString() },
    ])

    return { previousTodos }
  },
  onError: (err, newTodo, result, context) => {
    context.client.setQueryData(['todos'], result.previousTodos)
  },
  onSettled: (data, error, variables, result, context) => {
    context.client.invalidateQueries({ queryKey: ['todos'] })
  },
})
```

---

## Removing from a List

```tsx
useMutation({
  mutationFn: (todoId: number) => api.deleteTodo(todoId),
  onMutate: async (todoId, context) => {
    await context.client.cancelQueries({ queryKey: ['todos'] })

    const previousTodos = context.client.getQueryData<Todo[]>(['todos'])

    // Optimistically remove the item
    context.client.setQueryData<Todo[]>(['todos'], (old) =>
      old?.filter((t) => t.id !== todoId),
    )

    return { previousTodos }
  },
  onError: (err, todoId, result, context) => {
    context.client.setQueryData(['todos'], result.previousTodos)
  },
  onSettled: (data, error, variables, result, context) => {
    context.client.invalidateQueries({ queryKey: ['todos'] })
  },
})
```

---

## UI-Based Optimistic Updates

Instead of modifying the cache, use the mutation's own state to render optimistic UI:

```tsx
function TodoList() {
  const { data: todos } = useQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  })

  const addTodo = useMutation({
    mutationFn: createTodo,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })

  return (
    <ul>
      {todos?.map((todo) => (
        <li key={todo.id}>{todo.title}</li>
      ))}
      {/* Show optimistic item while mutation is pending */}
      {addTodo.isPending && (
        <li style={{ opacity: 0.5 }}>{addTodo.variables.title}</li>
      )}
    </ul>
  )
}
```

### Using useMutationState for Cross-Component Optimistic UI

```tsx
import { useMutationState } from '@tanstack/react-query'

function TodoList() {
  // Get all pending "addTodo" mutations from any component
  const pendingTodos = useMutationState({
    filters: { mutationKey: ['addTodo'], status: 'pending' },
    select: (mutation) => mutation.state.variables as CreateTodoInput,
  })

  return (
    <ul>
      {todos?.map((todo) => <li key={todo.id}>{todo.title}</li>)}
      {pendingTodos.map((todo, i) => (
        <li key={`pending-${i}`} style={{ opacity: 0.5 }}>{todo.title}</li>
      ))}
    </ul>
  )
}
```

---

## Choosing Between Approaches

| | Cache-Based | UI-Based |
|---|---|---|
| **Complexity** | Higher (cancel, snapshot, rollback) | Lower (just use mutation state) |
| **Cross-component** | Works everywhere (cache is global) | Need `useMutationState` |
| **Rollback** | Automatic via `onError` | Automatic (mutation fails → no pending state) |
| **Multiple mutations** | Need careful cache management | Simpler with `useMutationState` |
| **Best for** | Complex updates, multiple cache entries | Simple add/remove operations |

---

## Common Patterns

### Toggle Completion

```tsx
const toggleTodo = useMutation({
  mutationFn: (todo: Todo) =>
    api.updateTodo({ ...todo, completed: !todo.completed }),
  onMutate: async (todo, context) => {
    await context.client.cancelQueries({ queryKey: ['todos'] })
    const previousTodos = context.client.getQueryData<Todo[]>(['todos'])

    context.client.setQueryData<Todo[]>(['todos'], (old) =>
      old?.map((t) =>
        t.id === todo.id ? { ...t, completed: !t.completed } : t,
      ),
    )

    return { previousTodos }
  },
  onError: (err, todo, result, context) => {
    context.client.setQueryData(['todos'], result.previousTodos)
  },
  onSettled: (data, error, vars, result, context) => {
    context.client.invalidateQueries({ queryKey: ['todos'] })
  },
})
```

### Updating Multiple Cache Entries

```tsx
onMutate: async (updatedTodo, context) => {
  await context.client.cancelQueries({ queryKey: ['todos'] })
  await context.client.cancelQueries({ queryKey: ['todo', updatedTodo.id] })

  const previousTodos = context.client.getQueryData<Todo[]>(['todos'])
  const previousTodo = context.client.getQueryData<Todo>(['todo', updatedTodo.id])

  // Update both the list and individual caches
  context.client.setQueryData<Todo[]>(['todos'], (old) =>
    old?.map((t) => (t.id === updatedTodo.id ? updatedTodo : t)),
  )
  context.client.setQueryData(['todo', updatedTodo.id], updatedTodo)

  return { previousTodos, previousTodo }
},
onError: (err, updatedTodo, result, context) => {
  context.client.setQueryData(['todos'], result.previousTodos)
  context.client.setQueryData(['todo', updatedTodo.id], result.previousTodo)
},
```

---

## Common Pitfalls

1. **Forgetting `cancelQueries`** — Without it, an in-flight refetch can overwrite your optimistic update.

2. **Not invalidating in `onSettled`** — Always invalidate to ensure cache matches server, even on success.

3. **Temporary IDs in optimistic items** — Use a prefix like `temp-` for optimistic items to distinguish them.

4. **Race conditions with concurrent mutations** — Multiple optimistic updates to the same cache can conflict. Consider using `scope` for sequential execution.

5. **Not handling `undefined` in `setQueryData`** — The updater function receives `undefined` if the cache entry doesn't exist.

---

## Related

- **02-mutations.md** — useMutation basics
- **03-query-invalidation.md** — Invalidation patterns
- **04-caching.md** — How the cache works
