# Mutations — useMutation Hook

> Source: [TanStack Query Docs — Mutations](https://tanstack.com/query/v5/docs/framework/react/guides/mutations)

## Table of Contents

- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [useMutation Options](#usemutation-options)
- [Return Values](#return-values)
- [Side Effect Callbacks](#side-effect-callbacks)
- [mutate vs mutateAsync](#mutate-vs-mutateasync)
- [Invalidating Queries After Mutation](#invalidating-queries-after-mutation)
- [Updating Cache from Response](#updating-cache-from-response)
- [Mutation State and isPending](#mutation-state-and-ispending)
- [Retry Configuration](#retry-configuration)
- [Mutation Scope and Concurrency](#mutation-scope-and-concurrency)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Mutations are used for **creating, updating, and deleting** data — any operation that modifies server state. Unlike queries (which are declarative), mutations are **imperative** — you trigger them explicitly.

---

## Basic Usage

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query'

function AddTodo() {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: async (newTodo: { title: string }) => {
      const res = await fetch('/api/todos', {
        method: 'POST',
        body: JSON.stringify(newTodo),
        headers: { 'Content-Type': 'application/json' },
      })
      if (!res.ok) throw new Error('Failed to create todo')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })

  return (
    <button
      onClick={() => mutation.mutate({ title: 'New Todo' })}
      disabled={mutation.isPending}
    >
      {mutation.isPending ? 'Adding...' : 'Add Todo'}
    </button>
  )
}
```

---

## useMutation Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `mutationFn` | `(vars) => Promise<T>` | **required** | Function that performs the mutation |
| `mutationKey` | `unknown[]` | — | Optional key for deduplication / defaults |
| `onMutate` | `(vars, ctx) => Promise<C> \| C` | — | Called before mutationFn executes |
| `onSuccess` | `(data, vars, mutateResult, ctx) => void` | — | Called on success |
| `onError` | `(error, vars, mutateResult, ctx) => void` | — | Called on error |
| `onSettled` | `(data, error, vars, mutateResult, ctx) => void` | — | Called on success OR error |
| `retry` | `boolean \| number \| fn` | `0` | Retry count |
| `retryDelay` | `number \| fn` | exponential | Delay between retries |
| `gcTime` | `number` | `300000` | Cache time for mutation result |
| `networkMode` | `'online' \| 'always' \| 'offlineFirst'` | `'online'` | Network behavior |
| `throwOnError` | `boolean \| fn` | `false` | Throw to error boundary |
| `meta` | `Record<string, unknown>` | — | Metadata for the mutation |
| `scope` | `{ id: string }` | — | Concurrency scope |

---

## Return Values

```tsx
const {
  // Actions
  mutate,          // (vars, options?) => void — fire and forget
  mutateAsync,     // (vars, options?) => Promise<T> — returns promise
  reset,           // () => void — reset mutation state

  // Data
  data,            // T | undefined — last successful response
  error,           // TError | null — last error
  variables,       // TVars | undefined — variables passed to mutate

  // Status
  status,          // 'idle' | 'pending' | 'success' | 'error'
  isPending,       // currently executing
  isSuccess,       // last mutation succeeded
  isError,         // last mutation failed
  isIdle,          // no mutation yet
  failureCount,    // number of failures
  failureReason,   // last failure reason
  submittedAt,     // timestamp of last mutate call
} = useMutation({ ... })
```

---

## Side Effect Callbacks

Callbacks fire in this order: `onMutate` → `mutationFn` → `onSuccess`/`onError` → `onSettled`

```tsx
useMutation({
  mutationFn: updateTodo,
  onMutate: (variables) => {
    // Fires BEFORE mutationFn
    // Return value available as context in other callbacks
    console.log('Starting mutation with:', variables)
    return { startedAt: Date.now() }
  },
  onSuccess: (data, variables, mutateResult, context) => {
    // Fires on success
    console.log('Created:', data)
  },
  onError: (error, variables, mutateResult, context) => {
    // Fires on error
    console.error('Failed:', error.message)
  },
  onSettled: (data, error, variables, mutateResult, context) => {
    // Fires on success OR error (finally)
    console.log('Mutation completed')
  },
})
```

### Per-Call Callbacks

You can also pass callbacks when calling `mutate()`:

```tsx
mutation.mutate(newTodo, {
  onSuccess: (data) => {
    // Component-specific success handler
    navigate(`/todos/${data.id}`)
  },
  onError: (error) => {
    toast.error(error.message)
  },
})
```

**Execution order:** Hook-level callbacks fire first, then per-call callbacks.

---

## mutate vs mutateAsync

### mutate — Fire and Forget

```tsx
mutation.mutate(data)
// Returns void — use callbacks for side effects
```

### mutateAsync — Promise-Based

```tsx
try {
  const result = await mutation.mutateAsync(data)
  console.log('Success:', result)
} catch (error) {
  console.error('Failed:', error)
}
```

**Prefer `mutate`** in most cases — it's simpler and callbacks handle side effects. Use `mutateAsync` when you need the result in an async flow.

---

## Invalidating Queries After Mutation

The most common pattern — refetch affected queries after a mutation:

```tsx
const queryClient = useQueryClient()

const mutation = useMutation({
  mutationFn: createTodo,
  onSuccess: () => {
    // Invalidate all queries starting with 'todos'
    queryClient.invalidateQueries({ queryKey: ['todos'] })
  },
})
```

### Awaiting Invalidation

```tsx
onSuccess: async (data, variables, mutateResult, context) => {
  // Wait for queries to refetch before proceeding
  await context.client.invalidateQueries({ queryKey: ['todos'] })
},
```

---

## Updating Cache from Response

Instead of refetching, update the cache directly with the mutation response:

```tsx
const queryClient = useQueryClient()

const mutation = useMutation({
  mutationFn: updateTodo,
  onSuccess: (updatedTodo) => {
    // Update the individual todo in cache
    queryClient.setQueryData(['todo', updatedTodo.id], updatedTodo)

    // Update the todo in the list cache
    queryClient.setQueryData(['todos'], (old: Todo[] | undefined) =>
      old?.map((t) => (t.id === updatedTodo.id ? updatedTodo : t))
    )
  },
})
```

This avoids an extra network request but requires the server to return the full updated object.

---

## Mutation State and isPending

```tsx
function SubmitButton() {
  const mutation = useMutation({ mutationFn: submitForm })

  return (
    <button
      onClick={() => mutation.mutate(formData)}
      disabled={mutation.isPending}
    >
      {mutation.isPending ? 'Submitting...' : 'Submit'}
    </button>
  )
}
```

### Reset Mutation State

```tsx
// Reset to idle state (clear error, data, etc.)
mutation.reset()
```

---

## Retry Configuration

Mutations default to **0 retries** (unlike queries which default to 3):

```tsx
useMutation({
  mutationFn: createTodo,
  retry: 3,
  retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30000),
})
```

---

## Mutation Scope and Concurrency

By default, all mutations run concurrently. Use `scope` to serialize mutations:

```tsx
useMutation({
  mutationFn: updateTodo,
  scope: { id: 'todo-updates' }, // Mutations with same scope run sequentially
})
```

---

## Common Patterns

### Form Submission

```tsx
function ContactForm() {
  const [form, setForm] = useState({ name: '', email: '' })

  const mutation = useMutation({
    mutationFn: async (data: typeof form) => {
      const res = await fetch('/api/contact', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json' },
      })
      if (!res.ok) throw new Error('Submission failed')
      return res.json()
    },
  })

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(form) }}>
      <input value={form.name} onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))} />
      <input value={form.email} onChange={(e) => setForm(f => ({ ...f, email: e.target.value }))} />
      <button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? 'Sending...' : 'Send'}
      </button>
      {mutation.isError && <p>Error: {mutation.error.message}</p>}
      {mutation.isSuccess && <p>Sent successfully!</p>}
    </form>
  )
}
```

### Delete with Confirmation

```tsx
const deleteMutation = useMutation({
  mutationFn: async (todoId: number) => {
    const res = await fetch(`/api/todos/${todoId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Delete failed')
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] })
  },
})

// Usage
<button onClick={() => {
  if (confirm('Delete this todo?')) {
    deleteMutation.mutate(todo.id)
  }
}}>Delete</button>
```

---

## Common Pitfalls

1. **Don't destructure `mutation.mutate` outside the component** — It depends on component lifecycle.

2. **Mutations don't cache by default** — Unlike queries, mutation results aren't automatically cached for reuse.

3. **Use `onSettled` for cleanup, not `onSuccess`** — `onSettled` fires on both success and error.

4. **Per-call callbacks don't fire if component unmounts** — Hook-level callbacks always fire.

5. **Don't use `useMutation` for GET requests** — That's what `useQuery` is for.

---

## Related

- **03-query-invalidation.md** — Invalidation patterns
- **06-optimistic-updates.md** — Optimistic UI updates
- **01-queries.md** — useQuery for read operations
