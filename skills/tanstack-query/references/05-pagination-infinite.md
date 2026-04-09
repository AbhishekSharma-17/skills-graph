# Pagination & Infinite Queries

> Source: [TanStack Query Docs — Paginated Queries](https://tanstack.com/query/v5/docs/framework/react/guides/paginated-queries) | [Infinite Queries](https://tanstack.com/query/v5/docs/framework/react/guides/infinite-queries)

## Table of Contents

- [Overview](#overview)
- [Basic Pagination with useQuery](#basic-pagination-with-usequery)
- [Smooth Pagination with placeholderData](#smooth-pagination-with-placeholderdata)
- [useInfiniteQuery — Load More / Infinite Scroll](#useinfinitequery--load-more--infinite-scroll)
- [useInfiniteQuery Options](#useinfinitequery-options)
- [Return Values](#return-values)
- [Bi-Directional Infinite Queries](#bi-directional-infinite-queries)
- [Manual Refetching](#manual-refetching)
- [Prefetching Next Page](#prefetching-next-page)
- [maxPages — Limiting Cached Pages](#maxpages--limiting-cached-pages)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

TanStack Query supports two pagination patterns:

1. **Traditional pagination** — Use `useQuery` with page number in the query key
2. **Infinite scroll / load more** — Use `useInfiniteQuery` for cursor-based or offset-based loading

---

## Basic Pagination with useQuery

Include the page number in the query key. Each page is a separate cache entry:

```tsx
function PaginatedTodos() {
  const [page, setPage] = useState(1)

  const { data, isPending, isError } = useQuery({
    queryKey: ['todos', { page }],
    queryFn: () => fetchTodos(page),
  })

  return (
    <div>
      {isPending ? (
        <p>Loading...</p>
      ) : isError ? (
        <p>Error</p>
      ) : (
        <>
          {data.items.map((todo) => (
            <div key={todo.id}>{todo.title}</div>
          ))}
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
            Previous
          </button>
          <span>Page {page}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={!data.hasMore}>
            Next
          </button>
        </>
      )}
    </div>
  )
}
```

**Problem:** Changing the page shows a loading state because it's a new cache entry.

---

## Smooth Pagination with placeholderData

Use `placeholderData` to show the previous page while the new page loads:

```tsx
import { useQuery, keepPreviousData } from '@tanstack/react-query'

function PaginatedTodos() {
  const [page, setPage] = useState(1)

  const { data, isPending, isFetching, isPlaceholderData } = useQuery({
    queryKey: ['todos', { page }],
    queryFn: () => fetchTodos(page),
    placeholderData: keepPreviousData, // Show previous page data during fetch
  })

  return (
    <div>
      <div style={{ opacity: isPlaceholderData ? 0.5 : 1 }}>
        {data?.items.map((todo) => (
          <div key={todo.id}>{todo.title}</div>
        ))}
      </div>
      <button
        onClick={() => setPage((p) => p + 1)}
        disabled={isPlaceholderData || !data?.hasMore}
      >
        Next {isFetching && '(loading...)'}
      </button>
    </div>
  )
}
```

`keepPreviousData` is a helper that returns the previous query data as placeholder.

---

## useInfiniteQuery — Load More / Infinite Scroll

For "load more" or infinite scroll patterns where pages accumulate:

```tsx
import { useInfiniteQuery } from '@tanstack/react-query'

interface TodoPage {
  items: Todo[]
  nextCursor: number | null
}

function InfiniteTodos() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isPending,
    isError,
  } = useInfiniteQuery({
    queryKey: ['todos'],
    queryFn: async ({ pageParam }): Promise<TodoPage> => {
      const res = await fetch(`/api/todos?cursor=${pageParam}`)
      if (!res.ok) throw new Error('Failed')
      return res.json()
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
  })

  if (isPending) return <p>Loading...</p>
  if (isError) return <p>Error loading todos</p>

  return (
    <div>
      {data.pages.map((page, i) => (
        <div key={i}>
          {page.items.map((todo) => (
            <div key={todo.id}>{todo.title}</div>
          ))}
        </div>
      ))}
      <button
        onClick={() => fetchNextPage()}
        disabled={!hasNextPage || isFetchingNextPage}
      >
        {isFetchingNextPage ? 'Loading more...' : hasNextPage ? 'Load More' : 'No more todos'}
      </button>
    </div>
  )
}
```

---

## useInfiniteQuery Options

All `useQuery` options plus:

| Option | Type | Description |
|--------|------|-------------|
| `initialPageParam` | `TPageParam` | **Required** — The initial page parameter |
| `getNextPageParam` | `(lastPage, allPages, lastPageParam, allPageParams) => TPageParam \| undefined` | **Required** — Returns next page param, or `undefined` to signal no more pages |
| `getPreviousPageParam` | `(firstPage, allPages, firstPageParam, allPageParams) => TPageParam \| undefined` | For bi-directional. Returns previous page param |
| `maxPages` | `number` | Limit number of cached pages (for memory) |

### getNextPageParam

Return `undefined` or `null` to indicate there are no more pages:

```tsx
getNextPageParam: (lastPage, allPages) => {
  // Cursor-based
  return lastPage.nextCursor ?? undefined

  // Offset-based
  // return allPages.length < lastPage.totalPages ? allPages.length + 1 : undefined

  // Item count
  // const totalFetched = allPages.flatMap(p => p.items).length
  // return totalFetched < lastPage.total ? totalFetched : undefined
}
```

---

## Return Values

`useInfiniteQuery` returns all `useQuery` values plus:

```tsx
const {
  data,                 // { pages: TData[], pageParams: TPageParam[] }
  fetchNextPage,        // () => Promise — fetch the next page
  fetchPreviousPage,    // () => Promise — fetch the previous page
  hasNextPage,          // boolean — getNextPageParam returned !== undefined
  hasPreviousPage,      // boolean — getPreviousPageParam returned !== undefined
  isFetchingNextPage,   // boolean — fetching next page
  isFetchingPreviousPage, // boolean — fetching previous page
} = useInfiniteQuery({ ... })
```

### Accessing All Items

```tsx
// data.pages is an array of page results
const allTodos = data.pages.flatMap((page) => page.items)
```

---

## Bi-Directional Infinite Queries

Load pages in both directions (e.g., chat messages):

```tsx
useInfiniteQuery({
  queryKey: ['messages', chatId],
  queryFn: ({ pageParam }) => fetchMessages(chatId, pageParam),
  initialPageParam: 'latest',
  getNextPageParam: (lastPage) => lastPage.olderCursor ?? undefined,
  getPreviousPageParam: (firstPage) => firstPage.newerCursor ?? undefined,
})

// Fetch older messages
fetchNextPage()

// Fetch newer messages
fetchPreviousPage()
```

---

## Manual Refetching

When an infinite query refetches (e.g., after invalidation), **all pages are refetched sequentially** starting from the first:

```tsx
// This refetches ALL cached pages, not just the first
queryClient.invalidateQueries({ queryKey: ['todos'] })
```

This ensures consistency — if data was inserted between pages, all pages are re-fetched with fresh cursors.

---

## Prefetching Next Page

Prefetch the next page while the current one is displayed:

```tsx
const { data, hasNextPage } = useInfiniteQuery({
  queryKey: ['todos'],
  queryFn: fetchTodosPage,
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
})

// Prefetch next page
useEffect(() => {
  if (hasNextPage) {
    queryClient.prefetchInfiniteQuery({
      queryKey: ['todos'],
      queryFn: fetchTodosPage,
      initialPageParam: 0,
      getNextPageParam: (lastPage) => lastPage.nextCursor,
      pages: data.pages.length + 1, // Prefetch one more page
    })
  }
}, [data, hasNextPage])
```

---

## maxPages — Limiting Cached Pages

Prevent memory bloat from caching too many pages:

```tsx
useInfiniteQuery({
  queryKey: ['todos'],
  queryFn: fetchTodosPage,
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
  getPreviousPageParam: (firstPage) => firstPage.previousCursor,
  maxPages: 5, // Only keep 5 pages in cache
})
```

When `maxPages` is set:
- Loading more pages beyond the limit drops the oldest/newest page from cache
- `getPreviousPageParam` is required so dropped pages can be re-fetched
- Refetching only refetches the cached pages (not all ever-fetched pages)

---

## Common Patterns

### Intersection Observer for Infinite Scroll

```tsx
function InfiniteList() {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['items'],
    queryFn: fetchItemsPage,
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  })

  const observerRef = useRef<IntersectionObserver>()
  const loadMoreRef = useCallback((node: HTMLDivElement | null) => {
    if (isFetchingNextPage) return
    if (observerRef.current) observerRef.current.disconnect()
    observerRef.current = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasNextPage) {
        fetchNextPage()
      }
    })
    if (node) observerRef.current.observe(node)
  }, [isFetchingNextPage, hasNextPage, fetchNextPage])

  return (
    <div>
      {data?.pages.map((page, i) => (
        <div key={i}>
          {page.items.map((item) => <Item key={item.id} item={item} />)}
        </div>
      ))}
      <div ref={loadMoreRef}>
        {isFetchingNextPage ? 'Loading...' : hasNextPage ? 'Load more' : 'End'}
      </div>
    </div>
  )
}
```

---

## Common Pitfalls

1. **getNextPageParam must return `undefined` to stop** — Returning `null`, `false`, or `0` may still trigger `hasNextPage: true`.

2. **Refetching refetches ALL pages** — After invalidation, every cached page is sequentially re-fetched. This can be expensive with many pages.

3. **Don't forget `initialPageParam`** — It's required in v5 (was optional in v4).

4. **maxPages requires getPreviousPageParam** — Without it, dropped pages can't be re-fetched.

5. **Infinite query data structure is different** — `data.pages` is an array of pages, not a flat array. Use `flatMap` to flatten.

---

## Related

- **01-queries.md** — useQuery basics
- **07-prefetching.md** — Prefetching patterns
- **04-caching.md** — Cache management
