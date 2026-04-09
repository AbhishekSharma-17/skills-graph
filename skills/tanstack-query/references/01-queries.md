# Queries — useQuery Hook

> Source: [TanStack Query Docs — Queries](https://tanstack.com/query/v5/docs/framework/react/guides/queries)

## Table of Contents

- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [Query Keys](#query-keys)
- [Query Functions](#query-functions)
- [All useQuery Options](#all-usequery-options)
- [Return Values](#return-values)
- [Status and Fetch Status](#status-and-fetch-status)
- [Enabled / Lazy Queries](#enabled--lazy-queries)
- [Retry Configuration](#retry-configuration)
- [Select / Transform Data](#select--transform-data)
- [Placeholder and Initial Data](#placeholder-and-initial-data)
- [Refetch Behavior](#refetch-behavior)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

`useQuery` is the primary hook for fetching and caching data. It takes an options object and returns the query state.

```tsx
const result = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
})
```

---

## Basic Usage

```tsx
import { useQuery } from '@tanstack/react-query'

function TodoList() {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['todos'],
    queryFn: async () => {
      const res = await fetch('/api/todos')
      if (!res.ok) throw new Error('Network response was not ok')
      return res.json()
    },
  })

  if (isPending) return <span>Loading...</span>
  if (isError) return <span>Error: {error.message}</span>

  return (
    <ul>
      {data.map((todo) => (
        <li key={todo.id}>{todo.title}</li>
      ))}
    </ul>
  )
}
```

---

## Query Keys

Query keys uniquely identify a query in the cache. They must be arrays.

### Simple Keys

```tsx
useQuery({ queryKey: ['todos'], ... })
useQuery({ queryKey: ['todo', 5], ... })
```

### Keys with Variables

```tsx
useQuery({ queryKey: ['todo', todoId], ... })
useQuery({ queryKey: ['todos', { status, page }], ... })
useQuery({ queryKey: ['todos', { status: 'done', page: 1 }], ... })
```

### Key Rules

- Keys are **deterministically serialized** — object property order doesn't matter
- `['todos', { page: 1, status: 'active' }]` equals `['todos', { status: 'active', page: 1 }]`
- Array item order **does** matter: `['todo', 5]` ≠ `[5, 'todo']`
- When a key changes, the query automatically refetches (if enabled)

### Key Hierarchies for Invalidation

```tsx
// These are all separate cache entries:
['todos']                          // All todos
['todos', { status: 'active' }]   // Active todos
['todos', { status: 'done' }]     // Done todos
['todos', 1]                      // Todo with id 1

// Invalidating ['todos'] matches ALL of the above
queryClient.invalidateQueries({ queryKey: ['todos'] })
```

---

## Query Functions

Query functions must:
1. Return a **promise** that resolves with data or throws an error
2. **Throw** on error (fetch doesn't throw on HTTP errors!)

```tsx
// WRONG — fetch doesn't throw on 4xx/5xx
queryFn: () => fetch('/api/todos').then(res => res.json())

// CORRECT — check response.ok
queryFn: async () => {
  const res = await fetch('/api/todos')
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
```

### QueryFunctionContext

The query function receives a context object:

```tsx
queryFn: async ({ queryKey, signal, meta }) => {
  const [, todoId] = queryKey
  const res = await fetch(`/api/todos/${todoId}`, { signal })
  if (!res.ok) throw new Error('Failed')
  return res.json()
}
```

- **`queryKey`** — the full query key array
- **`signal`** — `AbortSignal` for automatic request cancellation
- **`meta`** — optional metadata set on the query

### Using the AbortSignal

```tsx
useQuery({
  queryKey: ['todos'],
  queryFn: async ({ signal }) => {
    const res = await fetch('/api/todos', { signal })
    if (!res.ok) throw new Error('Failed')
    return res.json()
  },
})
```

When a query is cancelled (e.g., component unmounts, key changes), the signal aborts the request.

---

## All useQuery Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `queryKey` | `unknown[]` | **required** | Unique identifier for this query |
| `queryFn` | `(ctx) => Promise<T>` | **required** | Function that fetches data |
| `enabled` | `boolean \| (query) => boolean` | `true` | Disable auto-fetching |
| `staleTime` | `number \| 'static'` | `0` | Time (ms) data stays fresh |
| `gcTime` | `number` | `300000` | Time (ms) unused cache persists |
| `retry` | `boolean \| number \| fn` | `3` | Retry count on failure |
| `retryDelay` | `number \| fn` | exponential | Delay between retries |
| `refetchInterval` | `number \| false \| fn` | `false` | Polling interval (ms) |
| `refetchOnMount` | `boolean \| 'always'` | `true` | Refetch on component mount |
| `refetchOnWindowFocus` | `boolean \| 'always'` | `true` | Refetch on window focus |
| `refetchOnReconnect` | `boolean \| 'always'` | `true` | Refetch on network reconnect |
| `select` | `(data: T) => U` | — | Transform/select data |
| `placeholderData` | `T \| (prev, prevQuery) => T` | — | Show while first fetch pending |
| `initialData` | `T \| () => T` | — | Seed cache with initial data |
| `initialDataUpdatedAt` | `number` | — | When initialData was fresh |
| `networkMode` | `'online' \| 'always' \| 'offlineFirst'` | `'online'` | Network behavior |
| `notifyOnChangeProps` | `string[] \| 'all'` | tracked | Props that trigger re-renders |
| `throwOnError` | `boolean \| fn` | `false` | Throw to error boundary |
| `meta` | `Record<string, unknown>` | — | Arbitrary query metadata |

---

## Return Values

```tsx
const {
  // Data
  data,              // TData | undefined — resolved data
  dataUpdatedAt,     // number — timestamp of last successful fetch
  error,             // TError | null — error if query failed
  errorUpdatedAt,    // number — timestamp of last error

  // Status flags
  status,            // 'pending' | 'success' | 'error'
  fetchStatus,       // 'fetching' | 'paused' | 'idle'
  isPending,         // status === 'pending' (no data yet)
  isSuccess,         // status === 'success'
  isError,           // status === 'error'
  isFetching,        // fetchStatus === 'fetching'
  isLoading,         // isPending && isFetching (first load)
  isRefetching,      // !isPending && isFetching (has data, refetching)
  isStale,           // data is older than staleTime
  isPlaceholderData, // currently showing placeholder data

  // Retry info
  failureCount,      // number of failed attempts
  failureReason,     // reason for last failure

  // Actions
  refetch,           // () => Promise — manually trigger refetch
} = useQuery({ ... })
```

### isPending vs isLoading vs isFetching

- **`isPending`** — No cached data, query hasn't resolved yet
- **`isLoading`** — `isPending && isFetching` — first-time load in progress
- **`isFetching`** — Any fetch in progress (initial or background)
- **`isRefetching`** — `!isPending && isFetching` — has data, fetching in background

---

## Status and Fetch Status

Two independent axes:

| | `idle` | `fetching` | `paused` |
|---|---|---|---|
| **`pending`** | Disabled query | First load | Offline, waiting |
| **`success`** | Data fresh/stale | Background refetch | Refetch paused |
| **`error`** | Error, no retry | Retrying | Retry paused |

---

## Enabled / Lazy Queries

Disable automatic fetching with `enabled: false`:

```tsx
const { data, refetch } = useQuery({
  queryKey: ['todo', todoId],
  queryFn: () => fetchTodo(todoId),
  enabled: !!todoId, // Only fetch when todoId is truthy
})
```

When `enabled` is `false`:
- Query does NOT fetch on mount
- Query does NOT refetch in background
- `refetch()` still works manually
- `status` stays `pending` until manually fetched

---

## Retry Configuration

```tsx
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  retry: 3,                    // Retry 3 times (default)
  retryDelay: (attempt) =>     // Exponential backoff with max 30s
    Math.min(1000 * 2 ** attempt, 30000),
})

// Custom retry logic
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  retry: (failureCount, error) => {
    if (error.status === 404) return false // Don't retry 404s
    return failureCount < 3
  },
})
```

---

## Select / Transform Data

Use `select` to transform or pick subsets of data. The selected result is memoized:

```tsx
const { data: todoTitles } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  select: (todos) => todos.map((t) => t.title),
})
// todoTitles: string[]
```

The full response is cached, but the component only re-renders when the selected value changes.

---

## Placeholder and Initial Data

### placeholderData — Temporary Display

```tsx
useQuery({
  queryKey: ['todo', todoId],
  queryFn: () => fetchTodo(todoId),
  placeholderData: { id: todoId, title: 'Loading...', completed: false },
})

// Use previous data as placeholder (great for pagination)
useQuery({
  queryKey: ['todos', page],
  queryFn: () => fetchTodos(page),
  placeholderData: (previousData) => previousData,
})
```

- Placeholder data is NOT put in cache
- `isPlaceholderData` is `true` while showing placeholder

### initialData — Seed the Cache

```tsx
useQuery({
  queryKey: ['todo', todoId],
  queryFn: () => fetchTodo(todoId),
  initialData: () => {
    // Seed from the list cache
    return queryClient.getQueryData(['todos'])
      ?.find((t) => t.id === todoId)
  },
  initialDataUpdatedAt: () => {
    return queryClient.getQueryState(['todos'])?.dataUpdatedAt
  },
})
```

- Initial data IS put in the cache
- Treated as real data for staleTime calculations
- Use `initialDataUpdatedAt` so TQ knows how fresh it is

---

## Refetch Behavior

```tsx
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  refetchOnMount: true,           // Refetch stale data on mount
  refetchOnWindowFocus: true,     // Refetch stale data on focus
  refetchOnReconnect: true,       // Refetch stale data on reconnect
  refetchInterval: 5000,          // Poll every 5 seconds
  refetchIntervalInBackground: false, // Pause polling when tab hidden
})
```

Setting any refetch option to `'always'` refetches even when data is fresh.

---

## Common Patterns

### Fetching with Path Parameters

```tsx
function useTodo(todoId: number) {
  return useQuery({
    queryKey: ['todo', todoId],
    queryFn: async () => {
      const res = await fetch(`/api/todos/${todoId}`)
      if (!res.ok) throw new Error('Failed')
      return res.json() as Promise<Todo>
    },
    enabled: todoId > 0,
  })
}
```

### Fetching with Search/Filter Parameters

```tsx
function useTodos(filters: { status?: string; page: number }) {
  return useQuery({
    queryKey: ['todos', filters],
    queryFn: async () => {
      const params = new URLSearchParams(filters as Record<string, string>)
      const res = await fetch(`/api/todos?${params}`)
      if (!res.ok) throw new Error('Failed')
      return res.json()
    },
  })
}
```

---

## Common Pitfalls

1. **fetch doesn't throw on HTTP errors** — Always check `response.ok` and throw manually.

2. **Don't destructure queryKey in the function signature** — Use the context parameter: `queryFn: ({ queryKey }) => ...`

3. **Returning `undefined` from queryFn is not allowed** — Return `null` instead if there's no data.

4. **Changing queryKey creates a new cache entry** — This is intentional but can cause loading states if you're not using `placeholderData`.

5. **staleTime: 0 (default) refetches on every mount** — Set a reasonable staleTime for data that doesn't change every second.

---

## Related

- **00-overview.md** — Installation and setup
- **02-mutations.md** — Write operations
- **04-caching.md** — Deep dive into cache behavior
- **11-typescript.md** — Type-safe query patterns
