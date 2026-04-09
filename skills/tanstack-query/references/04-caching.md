# Caching & Staleness

> Source: [TanStack Query Docs — Caching](https://tanstack.com/query/v5/docs/framework/react/guides/caching)

## Table of Contents

- [Overview](#overview)
- [Cache Lifecycle](#cache-lifecycle)
- [staleTime — Data Freshness](#staletime--data-freshness)
- [gcTime — Garbage Collection](#gctime--garbage-collection)
- [Fresh vs Stale](#fresh-vs-stale)
- [Background Refetching](#background-refetching)
- [Cache Entry States](#cache-entry-states)
- [Structural Sharing](#structural-sharing)
- [QueryCache and MutationCache](#querycache-and-mutationcache)
- [Cache Persistence](#cache-persistence)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

TanStack Query's cache is an in-memory store keyed by query keys. Every query result is cached, and the cache lifecycle is controlled by two main timers: `staleTime` (how long data is fresh) and `gcTime` (how long unused data stays in memory).

---

## Cache Lifecycle

```
Component mounts → Cache MISS → Fetch → Cache data (status: fresh)
                                              │
                   ┌──── staleTime expires ────┘
                   ▼
              Data is STALE
                   │
     ┌─────────────┼───────────────┐
     ▼             ▼               ▼
  Mount      Window focus      Reconnect    → Background refetch → Fresh again

Component unmounts → Cache entry becomes INACTIVE
                              │
               ┌── gcTime expires ──┐
               ▼                    ▼
         Entry REMOVED      (If gcTime: Infinity)
         from memory         Entry persists
```

---

## staleTime — Data Freshness

Controls how long fetched data is considered "fresh." While fresh, no automatic refetching occurs.

```tsx
// Data is fresh for 5 minutes
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  staleTime: 1000 * 60 * 5, // 5 minutes
})

// Data never goes stale (manual invalidation only)
useQuery({
  queryKey: ['config'],
  queryFn: fetchConfig,
  staleTime: Infinity,
})

// Data is stale immediately (default)
useQuery({
  queryKey: ['messages'],
  queryFn: fetchMessages,
  staleTime: 0, // Default — always stale
})
```

### staleTime: 'static'

New in v5 — data never becomes stale unless manually invalidated:

```tsx
useQuery({
  queryKey: ['constants'],
  queryFn: fetchConstants,
  staleTime: 'static', // Never stale, never auto-refetches
})
```

### Dynamic staleTime

```tsx
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  staleTime: (query) => {
    // Longer stale time for queries with more data
    return query.state.data?.length > 100 ? 60000 : 5000
  },
})
```

### Global staleTime

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // All queries fresh for 1 minute by default
    },
  },
})
```

---

## gcTime — Garbage Collection

Controls how long **inactive** cache entries persist in memory. An entry is inactive when no component subscribes to it.

```tsx
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  gcTime: 1000 * 60 * 10, // Keep in cache 10 minutes after last subscriber unmounts
})

// Never garbage collect
useQuery({
  queryKey: ['user'],
  queryFn: fetchUser,
  gcTime: Infinity,
})
```

### Default Values

| Context | staleTime | gcTime |
|---------|-----------|--------|
| Client-side | `0` | `300000` (5 min) |
| SSR | `0` | `Infinity` |

### When gcTime Triggers

1. Component using the query **unmounts** → entry becomes inactive
2. Timer starts counting down from `gcTime`
3. If a new component mounts and uses the same key before expiry → timer resets
4. If timer expires → entry is removed from cache

---

## Fresh vs Stale

| State | Behavior |
|-------|----------|
| **Fresh** | No automatic refetching on mount, focus, or reconnect |
| **Stale** | Automatic refetch on mount, window focus, reconnect (if those options are enabled) |

### What Triggers Stale → Refetch?

Stale data is refetched when:
- A new component **mounts** that uses the query (`refetchOnMount: true`)
- The window **regains focus** (`refetchOnWindowFocus: true`)
- The network **reconnects** (`refetchOnReconnect: true`)
- A **refetchInterval** fires
- `invalidateQueries()` is called

### What Does NOT Trigger Refetch?

- staleTime expiring on its own (it only marks data as stale)
- Other components re-rendering
- Parent component re-rendering

---

## Background Refetching

When stale data is refetched, the old data continues to be shown while the new data loads:

```tsx
const { data, isFetching, isRefetching } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  staleTime: 60000,
})

// data is shown immediately from cache
// isFetching = true during background refetch
// isRefetching = true (isFetching && !isPending)
```

This provides a seamless UX — users see cached data instantly while fresh data loads in the background.

---

## Cache Entry States

Each cache entry has a **status** and **fetchStatus**:

```
status: 'pending'  → No data yet
status: 'success'  → Has data
status: 'error'    → Failed

fetchStatus: 'idle'     → Not fetching
fetchStatus: 'fetching' → Currently fetching
fetchStatus: 'paused'   → Waiting for network
```

### Observer Count

The cache tracks how many components observe each entry:
- **Active query**: observer count > 0 (at least one mounted component)
- **Inactive query**: observer count = 0 (no mounted components)

Inactive queries are candidates for garbage collection after `gcTime`.

---

## Structural Sharing

TanStack Query uses structural sharing to minimize re-renders. When new data arrives, it compares the old and new data structurally:

```tsx
// If the new data is deeply equal to old data, the old reference is kept
// This means React.memo, useMemo, and other reference-based optimizations work

const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  structuralSharing: true, // Default
})
```

Disable for non-JSON data:

```tsx
useQuery({
  queryKey: ['binary-data'],
  queryFn: fetchBinaryData,
  structuralSharing: false, // Disable for non-serializable data
})
```

---

## QueryCache and MutationCache

### QueryCache — Global Event Handlers

```tsx
const queryCache = new QueryCache({
  onError: (error, query) => {
    // Global error handler for all queries
    if (error.status === 401) {
      redirectToLogin()
    }
  },
  onSuccess: (data, query) => {
    // Global success handler
  },
  onSettled: (data, error, query) => {
    // Global settled handler
  },
})

const queryClient = new QueryClient({ queryCache })
```

### MutationCache

```tsx
const mutationCache = new MutationCache({
  onError: (error, variables, context, mutation) => {
    // Global error handler for all mutations
    toast.error(`Mutation failed: ${error.message}`)
  },
  onSuccess: (data, variables, context, mutation) => {
    // Global success handler
  },
})

const queryClient = new QueryClient({ mutationCache })
```

---

## Cache Persistence

Persist cache to storage for offline support:

```bash
npm install @tanstack/query-sync-storage-persister
npm install @tanstack/react-query-persist-client
```

```tsx
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client'
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister'

const persister = createSyncStoragePersister({
  storage: window.localStorage,
})

function App() {
  return (
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{ persister, maxAge: 1000 * 60 * 60 * 24 }} // 24 hours
    >
      <YourApp />
    </PersistQueryClientProvider>
  )
}
```

---

## Common Patterns

### Tiered Stale Times

```tsx
// Static config — never refetch
useQuery({ queryKey: ['config'], queryFn: fetchConfig, staleTime: Infinity })

// User profile — fresh for 5 min
useQuery({ queryKey: ['user'], queryFn: fetchUser, staleTime: 300000 })

// Chat messages — always stale (real-time)
useQuery({ queryKey: ['messages'], queryFn: fetchMessages, staleTime: 0 })
```

### Prevent Flash of Loading State

```tsx
// Keep old data while refetching new page
useQuery({
  queryKey: ['todos', page],
  queryFn: () => fetchTodos(page),
  placeholderData: (prev) => prev, // Show previous page data during fetch
})
```

---

## Common Pitfalls

1. **staleTime: 0 causes too many requests** — Every mount, focus, and reconnect triggers a fetch. Set a reasonable staleTime.

2. **gcTime shorter than staleTime makes no sense** — Data can't be fresh if it's been garbage collected.

3. **Infinite gcTime causes memory leaks** — Use Infinity only for data you truly need forever (like the current user).

4. **Structural sharing fails with non-JSON data** — Disable it for Dates, Maps, Sets, or binary data.

5. **staleTime is per-observer, not per-cache-entry** — Different components can have different staleTime for the same query key.

---

## Related

- **01-queries.md** — useQuery options reference
- **03-query-invalidation.md** — Manually marking data as stale
- **07-prefetching.md** — Pre-populating the cache
