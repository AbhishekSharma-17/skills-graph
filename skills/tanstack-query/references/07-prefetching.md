# Prefetching

> Source: [TanStack Query Docs — Prefetching](https://tanstack.com/query/v5/docs/framework/react/guides/prefetching)

## Table of Contents

- [Overview](#overview)
- [prefetchQuery](#prefetchquery)
- [Prefetching on Hover](#prefetching-on-hover)
- [Prefetching on Route Change](#prefetching-on-route-change)
- [Prefetching in Event Handlers](#prefetching-in-event-handlers)
- [ensureQueryData](#ensurequerydata)
- [Prefetching Infinite Queries](#prefetching-infinite-queries)
- [Server-Side Prefetching](#server-side-prefetching)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Prefetching populates the cache with data **before** a component needs it, eliminating loading states. Data is prefetched using the same query key and function, so when the component mounts, it finds cached data immediately.

---

## prefetchQuery

```tsx
const queryClient = useQueryClient()

// Prefetch a query — doesn't return data, just populates cache
await queryClient.prefetchQuery({
  queryKey: ['todo', todoId],
  queryFn: () => fetchTodo(todoId),
  staleTime: 60000, // Only prefetch if data is older than 1 min
})
```

`prefetchQuery` silently fetches data and puts it in cache. It:
- Does NOT throw on error
- Does NOT return data
- Respects `staleTime` — won't fetch if fresh data already exists
- Returns a `Promise<void>` that resolves when fetch completes

---

## Prefetching on Hover

Prefetch data when the user hovers over a link or button:

```tsx
function TodoLink({ todoId }: { todoId: number }) {
  const queryClient = useQueryClient()

  const prefetchTodo = () => {
    queryClient.prefetchQuery({
      queryKey: ['todo', todoId],
      queryFn: () => fetchTodo(todoId),
      staleTime: 60000, // Don't re-prefetch if already fresh
    })
  }

  return (
    <Link
      to={`/todos/${todoId}`}
      onMouseEnter={prefetchTodo}
      onFocus={prefetchTodo}
    >
      Todo #{todoId}
    </Link>
  )
}
```

The 200-300ms hover delay before clicking is usually enough to complete the prefetch.

---

## Prefetching on Route Change

### With React Router

```tsx
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'

// Route loader (React Router v6.4+)
export const todoLoader = (queryClient: QueryClient) =>
  async ({ params }: LoaderFunctionArgs) => {
    await queryClient.prefetchQuery({
      queryKey: ['todo', Number(params.todoId)],
      queryFn: () => fetchTodo(Number(params.todoId)),
      staleTime: 60000,
    })
    return null // Data is in cache, component uses useQuery
  }
```

### With TanStack Router

TanStack Router has built-in integration with TanStack Query for route-level prefetching.

---

## Prefetching in Event Handlers

```tsx
function SearchResults({ query }: { query: string }) {
  const queryClient = useQueryClient()

  // Prefetch page 2 when user sees page 1
  useEffect(() => {
    queryClient.prefetchQuery({
      queryKey: ['search', query, 2],
      queryFn: () => searchApi(query, 2),
    })
  }, [query, queryClient])

  const { data } = useQuery({
    queryKey: ['search', query, 1],
    queryFn: () => searchApi(query, 1),
  })

  return <div>{/* render results */}</div>
}
```

---

## ensureQueryData

Like `prefetchQuery` but **returns the data**. Useful when you need the data outside a component:

```tsx
// Returns cached data if fresh, otherwise fetches and returns it
const data = await queryClient.ensureQueryData({
  queryKey: ['todo', todoId],
  queryFn: () => fetchTodo(todoId),
  staleTime: 60000,
})
```

### Differences from prefetchQuery

| | `prefetchQuery` | `ensureQueryData` |
|---|---|---|
| Returns data | No (`Promise<void>`) | Yes (`Promise<TData>`) |
| Throws on error | No (swallows errors) | Yes (throws) |
| Use case | Fire-and-forget prefetch | Need the data value |

---

## Prefetching Infinite Queries

```tsx
await queryClient.prefetchInfiniteQuery({
  queryKey: ['todos'],
  queryFn: ({ pageParam }) => fetchTodosPage(pageParam),
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
  pages: 3, // Prefetch the first 3 pages
})
```

The `pages` option specifies how many pages to prefetch. `getNextPageParam` is called after each page to determine the next.

---

## Server-Side Prefetching

### Next.js App Router (Server Components)

```tsx
// app/todos/page.tsx
import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query'

export default async function TodosPage() {
  const queryClient = new QueryClient()

  await queryClient.prefetchQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <TodoList />
    </HydrationBoundary>
  )
}
```

### Next.js Pages Router (getServerSideProps)

```tsx
export async function getServerSideProps() {
  const queryClient = new QueryClient()

  await queryClient.prefetchQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
    },
  }
}

// In _app.tsx
function MyApp({ Component, pageProps }) {
  const [queryClient] = useState(() => new QueryClient())
  return (
    <QueryClientProvider client={queryClient}>
      <HydrationBoundary state={pageProps.dehydratedState}>
        <Component {...pageProps} />
      </HydrationBoundary>
    </QueryClientProvider>
  )
}
```

---

## Common Patterns

### Prefetch on List Item Hover

```tsx
function TodoList() {
  const queryClient = useQueryClient()
  const { data: todos } = useQuery({ queryKey: ['todos'], queryFn: fetchTodos })

  return (
    <ul>
      {todos?.map((todo) => (
        <li
          key={todo.id}
          onMouseEnter={() => {
            queryClient.prefetchQuery({
              queryKey: ['todo', todo.id],
              queryFn: () => fetchTodo(todo.id),
              staleTime: 30000,
            })
          }}
        >
          <Link to={`/todos/${todo.id}`}>{todo.title}</Link>
        </li>
      ))}
    </ul>
  )
}
```

### Prefetch Related Data After Query Loads

```tsx
function UserProfile({ userId }: { userId: string }) {
  const queryClient = useQueryClient()

  const { data: user } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
  })

  // Prefetch user's posts once we have the user
  useEffect(() => {
    if (user) {
      queryClient.prefetchQuery({
        queryKey: ['posts', userId],
        queryFn: () => fetchUserPosts(userId),
      })
    }
  }, [user, userId, queryClient])

  return <div>{/* render user */}</div>
}
```

---

## Common Pitfalls

1. **prefetchQuery swallows errors** — It won't throw if the fetch fails. Use `ensureQueryData` if you need error handling.

2. **Stale data doesn't trigger prefetch** — `prefetchQuery` respects `staleTime`. If you always want to prefetch, set `staleTime: 0`.

3. **Don't await prefetch in render** — Use `useEffect` or event handlers. Awaiting in render blocks the component.

4. **Server-side: create new QueryClient per request** — Sharing a client between requests leaks data between users.

5. **Prefetch query key/fn must match useQuery** — The query key and function must be identical to what the component uses, or it creates a separate cache entry.

---

## Related

- **08-ssr-hydration.md** — Server-side rendering patterns
- **05-pagination-infinite.md** — Prefetching pagination
- **04-caching.md** — How staleTime affects prefetching
