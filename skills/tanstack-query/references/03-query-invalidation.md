# Query Invalidation

> Source: [TanStack Query Docs — Query Invalidation](https://tanstack.com/query/v5/docs/framework/react/guides/query-invalidation)

## Table of Contents

- [Overview](#overview)
- [invalidateQueries](#invalidatequeries)
- [Query Matching](#query-matching)
- [Exact Matching](#exact-matching)
- [Predicate Functions](#predicate-functions)
- [Invalidation from Mutations](#invalidation-from-mutations)
- [refetchQueries](#refetchqueries)
- [resetQueries](#resetqueries)
- [removeQueries](#removequeries)
- [Cache Manipulation Methods](#cache-manipulation-methods)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Query invalidation marks cached data as stale and optionally triggers a refetch. This is the primary mechanism for keeping data fresh after mutations.

```tsx
const queryClient = useQueryClient()

// Mark all queries starting with 'todos' as stale
queryClient.invalidateQueries({ queryKey: ['todos'] })
```

---

## invalidateQueries

```tsx
queryClient.invalidateQueries({
  queryKey?: QueryKey,      // Match by key prefix
  exact?: boolean,          // Exact key match only
  predicate?: (query) => boolean, // Custom matching function
  refetchType?: 'active' | 'inactive' | 'all' | 'none', // Which to refetch
  type?: 'active' | 'inactive' | 'all', // Which to invalidate
})
```

### Default Behavior

1. Marks matching queries as **stale** (ignoring their staleTime)
2. **Refetches** queries that are currently active (rendered in a component)
3. Inactive queries get stale-marked but **don't refetch** until next mount

```tsx
// Invalidate all queries
queryClient.invalidateQueries()

// Invalidate all queries starting with 'todos'
queryClient.invalidateQueries({ queryKey: ['todos'] })

// Invalidate the specific query ['todos', { page: 1 }]
queryClient.invalidateQueries({
  queryKey: ['todos', { page: 1 }],
  exact: true,
})
```

---

## Query Matching

Invalidation uses **prefix matching** by default:

```tsx
queryClient.invalidateQueries({ queryKey: ['todos'] })

// Matches ALL of these:
// ['todos']
// ['todos', 1]
// ['todos', { status: 'active' }]
// ['todos', { status: 'done', page: 1 }]

// Does NOT match:
// ['todo', 1]
// ['posts']
```

### Matching Rules

- `['todos']` matches any key that **starts with** `['todos']`
- `['todos', { status: 'active' }]` matches keys starting with `['todos', { status: 'active' }]`
- Object properties are matched by inclusion (partial match)

---

## Exact Matching

```tsx
// Only invalidate the exact key ['todos']
queryClient.invalidateQueries({
  queryKey: ['todos'],
  exact: true,
})
// Does NOT match ['todos', 1] or ['todos', { status: 'active' }]
```

---

## Predicate Functions

For complex matching logic:

```tsx
// Invalidate all queries where the first key element is 'todos'
// and the second element has status: 'done'
queryClient.invalidateQueries({
  predicate: (query) => {
    const key = query.queryKey
    return key[0] === 'todos' && key[1]?.status === 'done'
  },
})
```

### Combine with queryKey

```tsx
// Predicate runs only on queries matching the key prefix
queryClient.invalidateQueries({
  queryKey: ['todos'],
  predicate: (query) => {
    return query.state.dataUpdatedAt < Date.now() - 60000 // Older than 1 minute
  },
})
```

---

## Invalidation from Mutations

The most common pattern — invalidate after a successful mutation:

```tsx
const queryClient = useQueryClient()

const addTodo = useMutation({
  mutationFn: createTodo,
  onSuccess: () => {
    // Refetch the todos list
    queryClient.invalidateQueries({ queryKey: ['todos'] })
  },
})
```

### Invalidate Multiple Query Groups

```tsx
onSuccess: () => {
  // Invalidate both the list and individual todo queries
  queryClient.invalidateQueries({ queryKey: ['todos'] })
  queryClient.invalidateQueries({ queryKey: ['stats'] })
}
```

### Await Invalidation

```tsx
onSuccess: async () => {
  // Wait for refetch to complete before proceeding
  await queryClient.invalidateQueries({ queryKey: ['todos'] })
  // Now data is fresh
}
```

---

## refetchQueries

Force refetch without marking as stale:

```tsx
// Refetch all active queries
queryClient.refetchQueries({ type: 'active' })

// Refetch specific queries
queryClient.refetchQueries({ queryKey: ['todos'] })

// Refetch with options
queryClient.refetchQueries({
  queryKey: ['todos'],
  exact: true,
  type: 'active', // Only refetch active queries
})
```

### invalidateQueries vs refetchQueries

| | `invalidateQueries` | `refetchQueries` |
|---|---|---|
| Marks stale | Yes | No |
| Refetches active | Yes (default) | Yes |
| Refetches inactive | No (default) | No (default) |
| Next mount behavior | Will refetch | Normal stale check |

---

## resetQueries

Reset queries to their initial state:

```tsx
// Reset all todo queries to initial state
queryClient.resetQueries({ queryKey: ['todos'] })
```

- If query had `initialData`, it resets to that
- If no `initialData`, resets to `pending` status
- Active queries are refetched

---

## removeQueries

Remove queries from cache entirely:

```tsx
// Remove all todo queries from cache
queryClient.removeQueries({ queryKey: ['todos'] })
```

- Removes cache entry completely
- Next render creates fresh query
- Use sparingly — prefer `invalidateQueries`

---

## Cache Manipulation Methods

### setQueryData — Direct Cache Update

```tsx
// Set cache data directly (no network request)
queryClient.setQueryData(['todo', 1], { id: 1, title: 'Updated', completed: true })

// Updater function
queryClient.setQueryData(['todos'], (old: Todo[] | undefined) => {
  if (!old) return old
  return old.map((t) => (t.id === 1 ? { ...t, completed: true } : t))
})
```

### getQueryData — Read Cache

```tsx
const todos = queryClient.getQueryData<Todo[]>(['todos'])
const todo = queryClient.getQueryData<Todo>(['todo', 1])
```

### getQueryState — Read Cache Metadata

```tsx
const state = queryClient.getQueryState(['todos'])
// state.dataUpdatedAt, state.status, state.error, etc.
```

### cancelQueries — Cancel In-Flight Requests

```tsx
await queryClient.cancelQueries({ queryKey: ['todos'] })
```

---

## Common Patterns

### Invalidate Related Queries After CRUD

```tsx
const updateTodo = useMutation({
  mutationFn: (todo: Todo) => api.updateTodo(todo),
  onSuccess: (data) => {
    // Invalidate the list and the individual item
    queryClient.invalidateQueries({ queryKey: ['todos'] })
    queryClient.invalidateQueries({ queryKey: ['todo', data.id] })
  },
})
```

### Selective Refetch Control

```tsx
// Invalidate but don't auto-refetch
queryClient.invalidateQueries({
  queryKey: ['todos'],
  refetchType: 'none', // Mark stale only, don't refetch
})

// Refetch ALL matching queries (including inactive)
queryClient.invalidateQueries({
  queryKey: ['todos'],
  refetchType: 'all',
})
```

### Global Mutation Observer for Auto-Invalidation

```tsx
const queryClient = new QueryClient({
  mutationCache: new MutationCache({
    onSuccess: (_data, _variables, _context, mutation) => {
      // Auto-invalidate based on mutation key
      if (mutation.options.mutationKey) {
        queryClient.invalidateQueries({
          queryKey: mutation.options.mutationKey,
        })
      }
    },
  }),
})
```

---

## Common Pitfalls

1. **Invalidation is async** — `invalidateQueries` returns a promise. Await it if you need fresh data before proceeding.

2. **Inactive queries don't refetch** — Only active (mounted) queries refetch on invalidation. Use `refetchType: 'all'` to include inactive.

3. **Prefix matching invalidates more than expected** — `invalidateQueries({ queryKey: ['todo'] })` invalidates `['todos']` too if you have it. Use `exact: true` for precision.

4. **Don't over-invalidate** — Invalidating everything with `invalidateQueries()` causes unnecessary network requests.

5. **setQueryData doesn't trigger stale marking** — Data set via `setQueryData` is treated as fresh.

---

## Related

- **02-mutations.md** — Triggering invalidation from mutations
- **06-optimistic-updates.md** — Cache updates before server confirmation
- **04-caching.md** — How stale/fresh state works
