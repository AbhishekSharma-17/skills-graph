# Suspense & Error Boundaries

> Source: [TanStack Query Docs — Suspense](https://tanstack.com/query/v5/docs/framework/react/guides/suspense)

## Table of Contents

- [Overview](#overview)
- [useSuspenseQuery](#usesuspensequery)
- [useSuspenseInfiniteQuery](#usesuspenseinfinitequery)
- [useSuspenseQueries](#usequeries-with-suspense)
- [Error Boundaries](#error-boundaries)
- [Combining Suspense and Error Boundaries](#combining-suspense-and-error-boundaries)
- [Nested Suspense Boundaries](#nested-suspense-boundaries)
- [Streaming with Suspense](#streaming-with-suspense)
- [throwOnError with useQuery](#throwonerror-with-usequery)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

TanStack Query v5 provides first-class Suspense support through dedicated hooks. These hooks throw promises (for Suspense boundaries) and errors (for Error Boundaries), providing a cleaner component structure.

**Key difference from regular hooks:**
- `useSuspenseQuery` — data is **always defined** (TypeScript knows this)
- `useQuery` — data is `TData | undefined`

---

## useSuspenseQuery

```tsx
import { useSuspenseQuery } from '@tanstack/react-query'
import { Suspense } from 'react'

function TodoList() {
  // data is always defined — no need to check for undefined
  const { data } = useSuspenseQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  })

  return (
    <ul>
      {data.map((todo) => (
        <li key={todo.id}>{todo.title}</li>
      ))}
    </ul>
  )
}

// Wrap with Suspense boundary
function App() {
  return (
    <Suspense fallback={<div>Loading todos...</div>}>
      <TodoList />
    </Suspense>
  )
}
```

### Key Differences from useQuery

| Feature | `useQuery` | `useSuspenseQuery` |
|---------|-----------|-------------------|
| `data` type | `TData \| undefined` | `TData` (always defined) |
| `isPending` | Can be `true` | Always `false` |
| `isLoading` | Can be `true` | Always `false` |
| `status` | `'pending' \| 'success' \| 'error'` | Always `'success'` |
| Loading state | Handled in component | Handled by Suspense boundary |
| Error state | Handled in component | Handled by Error Boundary |
| `enabled` option | Supported | **Not supported** |
| `placeholderData` | Supported | **Not supported** |

### Options NOT Available

`useSuspenseQuery` does not accept:
- `enabled` — Suspense queries always fetch
- `placeholderData` — No placeholder concept with Suspense
- `throwOnError` — Errors always throw to Error Boundary

---

## useSuspenseInfiniteQuery

```tsx
import { useSuspenseInfiniteQuery } from '@tanstack/react-query'

function InfiniteTodos() {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useSuspenseInfiniteQuery({
      queryKey: ['todos'],
      queryFn: ({ pageParam }) => fetchTodosPage(pageParam),
      initialPageParam: 0,
      getNextPageParam: (lastPage) => lastPage.nextCursor,
    })

  return (
    <div>
      {data.pages.flatMap((page) =>
        page.items.map((todo) => <div key={todo.id}>{todo.title}</div>),
      )}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  )
}
```

---

## useQueries with Suspense

Use `useSuspenseQueries` for multiple parallel suspense queries:

```tsx
import { useSuspenseQueries } from '@tanstack/react-query'

function Dashboard() {
  const [userQuery, todosQuery, statsQuery] = useSuspenseQueries({
    queries: [
      { queryKey: ['user'], queryFn: fetchUser },
      { queryKey: ['todos'], queryFn: fetchTodos },
      { queryKey: ['stats'], queryFn: fetchStats },
    ],
  })

  // All data is defined — all queries resolved before this renders
  return (
    <div>
      <h1>{userQuery.data.name}</h1>
      <TodoList todos={todosQuery.data} />
      <Stats stats={statsQuery.data} />
    </div>
  )
}

// Single Suspense boundary waits for ALL queries
function App() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <Dashboard />
    </Suspense>
  )
}
```

---

## Error Boundaries

Suspense queries throw errors to the nearest Error Boundary:

```tsx
import { ErrorBoundary } from 'react-error-boundary'

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  )
}

function App() {
  const queryClient = useQueryClient()

  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={() => {
        // Reset all queries when error boundary resets
        queryClient.resetQueries()
      }}
    >
      <Suspense fallback={<Loading />}>
        <TodoList />
      </Suspense>
    </ErrorBoundary>
  )
}
```

### QueryErrorResetBoundary

TanStack Query provides a built-in reset mechanism:

```tsx
import { QueryErrorResetBoundary } from '@tanstack/react-query'
import { ErrorBoundary } from 'react-error-boundary'

function App() {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          FallbackComponent={({ error, resetErrorBoundary }) => (
            <div>
              <p>Error: {error.message}</p>
              <button onClick={resetErrorBoundary}>Retry</button>
            </div>
          )}
        >
          <Suspense fallback={<Loading />}>
            <TodoList />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  )
}
```

`QueryErrorResetBoundary` resets the query error state so that retrying the query works correctly.

---

## Combining Suspense and Error Boundaries

The recommended pattern is Error Boundary wrapping Suspense:

```tsx
<ErrorBoundary FallbackComponent={ErrorFallback}>
  <Suspense fallback={<Skeleton />}>
    <DataComponent />
  </Suspense>
</ErrorBoundary>
```

Render flow:
1. Component suspends → Suspense shows fallback
2. Data loads → Component renders
3. If error → Error Boundary catches and shows error fallback

---

## Nested Suspense Boundaries

Control loading granularity with nested boundaries:

```tsx
function Dashboard() {
  return (
    <div>
      {/* Critical content — loads first */}
      <Suspense fallback={<HeaderSkeleton />}>
        <Header />
      </Suspense>

      {/* Secondary content — can load independently */}
      <Suspense fallback={<TodosSkeleton />}>
        <TodoList />
      </Suspense>

      {/* Tertiary content */}
      <Suspense fallback={<StatsSkeleton />}>
        <Stats />
      </Suspense>
    </div>
  )
}
```

Each Suspense boundary independently resolves. If `Header` fetches faster, it renders before `TodoList` and `Stats`.

---

## Streaming with Suspense

With SSR streaming (React 18+), Suspense boundaries enable progressive rendering:

```tsx
// Server Component
export default async function Page() {
  return (
    <div>
      {/* Renders immediately */}
      <h1>Dashboard</h1>

      {/* Streams when data resolves */}
      <Suspense fallback={<Skeleton />}>
        <TodoList />  {/* Uses useSuspenseQuery internally */}
      </Suspense>
    </div>
  )
}
```

The server sends the `<h1>` and skeleton immediately, then streams the resolved `<TodoList>` when data is ready.

---

## throwOnError with useQuery

If you don't want to use `useSuspenseQuery` but still want errors in Error Boundaries:

```tsx
const { data, isPending } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  throwOnError: true, // Throws to Error Boundary
})

// Or conditionally
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  throwOnError: (error) => error.status >= 500, // Only throw server errors
})
```

---

## Common Patterns

### Suspense with Route Transitions

```tsx
function App() {
  return (
    <Suspense fallback={<GlobalSkeleton />}>
      <Routes>
        <Route
          path="/todos"
          element={
            <Suspense fallback={<TodosSkeleton />}>
              <TodosPage />
            </Suspense>
          }
        />
        <Route
          path="/todos/:id"
          element={
            <Suspense fallback={<TodoDetailSkeleton />}>
              <TodoDetailPage />
            </Suspense>
          }
        />
      </Routes>
    </Suspense>
  )
}
```

### Conditional Rendering Without `enabled`

Since `useSuspenseQuery` doesn't support `enabled`, gate rendering at the parent:

```tsx
function TodoDetail({ todoId }: { todoId: number | null }) {
  if (!todoId) return <p>Select a todo</p>

  return (
    <Suspense fallback={<Skeleton />}>
      <TodoDetailContent todoId={todoId} />
    </Suspense>
  )
}

function TodoDetailContent({ todoId }: { todoId: number }) {
  const { data } = useSuspenseQuery({
    queryKey: ['todo', todoId],
    queryFn: () => fetchTodo(todoId),
  })
  return <div>{data.title}</div>
}
```

---

## Common Pitfalls

1. **Multiple `useSuspenseQuery` in one component suspends on ALL** — All queries must resolve before the component renders. Split into separate Suspense boundaries for independent loading.

2. **`enabled` is not supported** — Use conditional rendering to control when Suspense queries run.

3. **Missing Error Boundary** — Without one, errors crash the app. Always pair Suspense with Error Boundaries.

4. **staleTime: 0 with SSR** — Causes a client refetch that triggers Suspense again. Set staleTime > 0 for SSR.

5. **Infinite re-suspending** — If queryFn always throws, the component re-suspends endlessly. Use retry limits.

---

## Related

- **08-ssr-hydration.md** — SSR with Suspense streaming
- **01-queries.md** — Regular useQuery (non-Suspense)
- **10-dependent-parallel.md** — Parallel queries with Suspense
