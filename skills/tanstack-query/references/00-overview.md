# TanStack Query — Overview & Setup

> Source: [tanstack.com/query](https://tanstack.com/query/latest) | Version: 5.95

## Table of Contents

- [What Is TanStack Query](#what-is-tanstack-query)
- [Core Concepts](#core-concepts)
- [Installation](#installation)
- [QueryClient Setup](#queryclient-setup)
- [Provider Configuration](#provider-configuration)
- [Default Options](#default-options)
- [Quick Start Example](#quick-start-example)
- [Key Mental Models](#key-mental-models)
- [Feature Overview](#feature-overview)
- [Common Pitfalls](#common-pitfalls)

---

## What Is TanStack Query

TanStack Query (formerly React Query) is a data-fetching and server-state management library. It replaces manual `useEffect` + `useState` patterns for loading remote data with a declarative, cache-first approach.

**Core problems it solves:**
- Caching and deduplication of network requests
- Background refetching and stale data management
- Automatic retries on failure
- Pagination, infinite scroll, and prefetching
- Optimistic updates with rollback
- Server-side rendering and hydration
- Garbage collection of unused cache entries

**Framework support:** React, Vue, Solid, Svelte, Angular (this skill focuses on React)

**Zero dependencies** — despite its feature density, it has no external runtime dependencies.

---

## Core Concepts

### Server State vs Client State

TanStack Query manages **server state** — data that:
- Is persisted remotely (databases, APIs)
- Requires async APIs to fetch/update
- Is shared and can be changed by others without your knowledge
- Can become stale in your application

This is fundamentally different from **client state** (UI state, form inputs, toggles) which tools like `useState`, Zustand, or Jotai handle.

### The Query Lifecycle

```
Fresh ──(staleTime expires)──> Stale ──(trigger)──> Fetching ──> Fresh
                                                         │
                                                    (on error)
                                                         │
                                                       Error ──(retry)──> Fetching
```

### Cache Entries

Every query is identified by a **query key** (an array). The cache stores entries keyed by the serialized query key. Each entry tracks:
- `data` — the resolved value
- `dataUpdatedAt` — when data was last fetched
- `status` — `pending` | `success` | `error`
- `fetchStatus` — `idle` | `fetching` | `paused`
- Observer count (how many components subscribe)

---

## Installation

```bash
# React
npm install @tanstack/react-query

# Optional: DevTools
npm install @tanstack/react-query-devtools

# Optional: ESLint plugin
npm install -D @tanstack/eslint-plugin-query
```

### Peer Dependencies

- React 18.0+ (React 19 supported)
- TypeScript 5.0+ (optional but recommended)

---

## QueryClient Setup

The `QueryClient` is the central coordinator. It holds the query cache, mutation cache, and default options.

```tsx
import { QueryClient } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,     // 1 minute before data is stale
      gcTime: 1000 * 60 * 5,    // 5 minutes before unused cache is garbage collected
      retry: 3,                  // Retry failed queries 3 times
      refetchOnWindowFocus: true, // Refetch when window regains focus
    },
    mutations: {
      retry: 0,                  // Don't retry mutations by default
    },
  },
})
```

### Key Default Options

| Option | Default | Description |
|--------|---------|-------------|
| `staleTime` | `0` | Time (ms) before data is considered stale |
| `gcTime` | `300000` (5 min) | Time (ms) unused cache lives in memory |
| `retry` | `3` (client), `0` (server) | Number of retry attempts |
| `refetchOnMount` | `true` | Refetch stale queries on component mount |
| `refetchOnWindowFocus` | `true` | Refetch stale queries when window gains focus |
| `refetchOnReconnect` | `true` | Refetch stale queries on network reconnect |

---

## Provider Configuration

Wrap your application with `QueryClientProvider` to make the client available to all hooks:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

### Important: Client Creation in React

Never create the `QueryClient` inside a component's render path without memoization:

```tsx
// WRONG — creates new client every render
function App() {
  const queryClient = new QueryClient()
  return <QueryClientProvider client={queryClient}>...</QueryClientProvider>
}

// CORRECT — stable reference
function App() {
  const [queryClient] = useState(() => new QueryClient())
  return <QueryClientProvider client={queryClient}>...</QueryClientProvider>
}
```

---

## Default Options

Override defaults globally or per-query:

```tsx
// Global defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
})

// Per-query override
const { data } = useQuery({
  queryKey: ['users'],
  queryFn: fetchUsers,
  staleTime: Infinity, // This specific query never goes stale
})
```

### Setting Defaults for Specific Query Keys

```tsx
queryClient.setQueryDefaults(['todos'], {
  staleTime: 1000 * 60 * 10, // 10 minutes for all 'todos' queries
})
```

---

## Quick Start Example

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

interface Todo {
  id: number
  title: string
  completed: boolean
}

function Todos() {
  const queryClient = useQueryClient()

  // Fetch todos
  const { data: todos, isPending, error } = useQuery({
    queryKey: ['todos'],
    queryFn: async (): Promise<Todo[]> => {
      const res = await fetch('/api/todos')
      if (!res.ok) throw new Error('Failed to fetch')
      return res.json()
    },
  })

  // Add a new todo
  const addTodo = useMutation({
    mutationFn: async (title: string) => {
      const res = await fetch('/api/todos', {
        method: 'POST',
        body: JSON.stringify({ title }),
        headers: { 'Content-Type': 'application/json' },
      })
      return res.json()
    },
    onSuccess: () => {
      // Invalidate and refetch the todos list
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })

  if (isPending) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <div>
      <button onClick={() => addTodo.mutate('New Todo')}>Add Todo</button>
      <ul>
        {todos.map((todo) => (
          <li key={todo.id}>{todo.title}</li>
        ))}
      </ul>
    </div>
  )
}
```

---

## Key Mental Models

### 1. Declarative, Not Imperative

You don't call `fetch` in `useEffect`. You declare what data you need and how fresh it should be. TanStack Query handles when and how to fetch.

### 2. Cache First

Every query result is cached. Subsequent renders with the same query key return cached data instantly while potentially refetching in the background.

### 3. Smart Defaults

Out of the box, queries are:
- Retried 3 times on failure (with exponential backoff)
- Refetched when the window regains focus
- Refetched when the network reconnects
- Considered stale immediately (`staleTime: 0`)

### 4. Status vs Fetch Status

Two orthogonal states:
- **`status`**: `pending` → `success` | `error` (has data or not?)
- **`fetchStatus`**: `fetching` | `paused` | `idle` (is it currently fetching?)

A query can be `success` + `fetching` (has cached data, refetching in background).

---

## Feature Overview

| Feature | Hook / API | Use Case |
|---------|-----------|----------|
| Basic fetching | `useQuery` | GET requests, read operations |
| Create/update/delete | `useMutation` | POST/PUT/DELETE operations |
| Multiple queries | `useQueries` | Dynamic number of parallel queries |
| Infinite lists | `useInfiniteQuery` | Load more, infinite scroll |
| Suspense | `useSuspenseQuery` | React Suspense integration |
| Prefetching | `queryClient.prefetchQuery` | Preload data on hover/route |
| Manual cache | `queryClient.setQueryData` | Direct cache manipulation |
| Invalidation | `queryClient.invalidateQueries` | Force refetch |

---

## Common Pitfalls

1. **staleTime: 0 (default) causes aggressive refetching** — Set a reasonable `staleTime` for data that doesn't change frequently.

2. **Query keys must be serializable** — Use arrays of primitives and plain objects. Functions, class instances, and `undefined` values cause issues.

3. **Don't put `queryClient` in render path** — Always use `useState` or module scope for client creation.

4. **QueryFn must throw on error** — `fetch` doesn't throw on 4xx/5xx. You must check `response.ok` and throw manually.

5. **Don't use `useEffect` to refetch** — Use `enabled`, `refetchInterval`, or query invalidation instead.

---

## Related

- **01-queries.md** — Deep dive into `useQuery` and all its options
- **02-mutations.md** — Creating, updating, deleting data
- **04-caching.md** — Cache lifecycle, staleTime, gcTime
- **12-devtools-testing.md** — DevTools setup and testing patterns
