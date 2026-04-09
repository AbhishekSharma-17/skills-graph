# SSR & Hydration

> Source: [TanStack Query Docs — SSR](https://tanstack.com/query/v5/docs/framework/react/guides/ssr) | [Advanced SSR](https://tanstack.com/query/v5/docs/framework/react/guides/advanced-ssr)

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Next.js App Router (Server Components)](#nextjs-app-router-server-components)
- [Next.js Pages Router](#nextjs-pages-router)
- [Streaming SSR](#streaming-ssr)
- [Dehydration and Hydration API](#dehydration-and-hydration-api)
- [QueryClient for SSR](#queryclient-for-ssr)
- [Prefetching Patterns](#prefetching-patterns)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

TanStack Query works with SSR by **prefetching data on the server**, serializing the cache state (dehydration), and restoring it on the client (hydration). This means:

1. Server fetches data and renders HTML with real content
2. Serialized cache state is sent to the client
3. Client restores the cache from the serialized state
4. Components render immediately with cached data (no loading state)

---

## Core Concepts

### Dehydration

Converting the in-memory QueryClient cache into a serializable object:

```tsx
import { dehydrate } from '@tanstack/react-query'

const dehydratedState = dehydrate(queryClient)
// dehydratedState is a JSON-serializable object
```

### Hydration

Restoring the serialized cache on the client:

```tsx
import { HydrationBoundary } from '@tanstack/react-query'

<HydrationBoundary state={dehydratedState}>
  <App />
</HydrationBoundary>
```

---

## Next.js App Router (Server Components)

### Step 1: Create a QueryClient Factory

```tsx
// app/get-query-client.ts
import { QueryClient, isServer, defaultShouldDehydrateQuery } from '@tanstack/react-query'

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // Prevent immediate refetch on client
      },
      dehydrate: {
        // Include pending queries in dehydration for streaming
        shouldDehydrateQuery: (query) =>
          defaultShouldDehydrateQuery(query) ||
          query.state.status === 'pending',
      },
    },
  })
}

let browserQueryClient: QueryClient | undefined

export function getQueryClient() {
  if (isServer) {
    // Server: always create a new client
    return makeQueryClient()
  }
  // Browser: reuse the same client
  if (!browserQueryClient) browserQueryClient = makeQueryClient()
  return browserQueryClient
}
```

### Step 2: Create Providers

```tsx
// app/providers.tsx
'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { getQueryClient } from './get-query-client'

export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools />
    </QueryClientProvider>
  )
}
```

### Step 3: Prefetch in Server Components

```tsx
// app/todos/page.tsx
import { dehydrate, HydrationBoundary } from '@tanstack/react-query'
import { getQueryClient } from '../get-query-client'
import { TodoList } from './todo-list'

export default async function TodosPage() {
  const queryClient = getQueryClient()

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

### Step 4: Client Component Uses useQuery

```tsx
// app/todos/todo-list.tsx
'use client'

import { useQuery } from '@tanstack/react-query'

export function TodoList() {
  // This finds prefetched data in the hydrated cache — no loading state
  const { data } = useQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  })

  return (
    <ul>
      {data?.map((todo) => <li key={todo.id}>{todo.title}</li>)}
    </ul>
  )
}
```

---

## Next.js Pages Router

### getServerSideProps

```tsx
import { dehydrate, QueryClient } from '@tanstack/react-query'

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
```

### getStaticProps

```tsx
export async function getStaticProps() {
  const queryClient = new QueryClient()

  await queryClient.prefetchQuery({
    queryKey: ['posts'],
    queryFn: fetchPosts,
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
    },
    revalidate: 60, // ISR: revalidate every 60 seconds
  }
}
```

### _app.tsx Setup

```tsx
// pages/_app.tsx
import { useState } from 'react'
import { QueryClient, QueryClientProvider, HydrationBoundary } from '@tanstack/react-query'

export default function MyApp({ Component, pageProps }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
          },
        },
      }),
  )

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

## Streaming SSR

With React 18+ streaming, you can start rendering before all data is ready:

### Using ReactQueryStreamedHydration

```bash
npm install @tanstack/react-query-next-experimental
```

```tsx
// app/providers.tsx
'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryStreamedHydration } from '@tanstack/react-query-next-experimental'
import { getQueryClient } from './get-query-client'

export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <ReactQueryStreamedHydration>
        {children}
      </ReactQueryStreamedHydration>
    </QueryClientProvider>
  )
}
```

With streamed hydration, `useSuspenseQuery` calls in client components automatically have their data streamed from the server — no manual `prefetchQuery` + `dehydrate` needed.

### Dehydrating Pending Queries

As of v5.40.0, pending queries can be dehydrated without awaiting:

```tsx
// Kick off prefetch but don't await
queryClient.prefetchQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
})

// Dehydrate immediately — pending queries stream when they resolve
return (
  <HydrationBoundary state={dehydrate(queryClient)}>
    <TodoList />
  </HydrationBoundary>
)
```

---

## Dehydration and Hydration API

### dehydrate(queryClient, options?)

```tsx
const dehydratedState = dehydrate(queryClient, {
  shouldDehydrateQuery: (query) => {
    // Only dehydrate successful queries (default)
    return query.state.status === 'success'
  },
  shouldDehydrateMutation: (mutation) => {
    return false // Don't dehydrate mutations (default)
  },
})
```

### HydrationBoundary

```tsx
<HydrationBoundary state={dehydratedState}>
  {children}
</HydrationBoundary>
```

Multiple `HydrationBoundary` components can be nested — each adds its queries to the cache.

---

## QueryClient for SSR

Critical rules for SSR:

```tsx
// Server: ALWAYS create a new QueryClient per request
// Sharing a client between requests leaks data between users!
if (isServer) {
  return new QueryClient()
}

// Browser: Reuse the same client
// Creating a new one on every render loses cache!
if (!browserClient) browserClient = new QueryClient()
return browserClient
```

### Recommended staleTime for SSR

```tsx
defaultOptions: {
  queries: {
    staleTime: 60 * 1000, // 1 minute
  },
}
```

Without this, `staleTime: 0` (default) causes an immediate refetch on the client after hydration, defeating the purpose of SSR prefetching.

---

## Prefetching Patterns

### Multiple Queries in Parallel

```tsx
export default async function DashboardPage() {
  const queryClient = getQueryClient()

  // Prefetch in parallel
  await Promise.all([
    queryClient.prefetchQuery({ queryKey: ['user'], queryFn: fetchUser }),
    queryClient.prefetchQuery({ queryKey: ['todos'], queryFn: fetchTodos }),
    queryClient.prefetchQuery({ queryKey: ['stats'], queryFn: fetchStats }),
  ])

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <Dashboard />
    </HydrationBoundary>
  )
}
```

---

## Common Patterns

### Error Handling in SSR

```tsx
export default async function TodosPage() {
  const queryClient = getQueryClient()

  // prefetchQuery never throws — errors are captured in cache
  await queryClient.prefetchQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  })

  // The client component's useQuery will see the error state
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <TodoList />
    </HydrationBoundary>
  )
}
```

---

## Common Pitfalls

1. **Sharing QueryClient between requests** — Server must create a new client per request to prevent data leaks.

2. **staleTime: 0 on SSR** — Causes immediate client refetch after hydration. Set at least 60s.

3. **Forgetting HydrationBoundary** — Without it, prefetched data isn't hydrated into the client cache.

4. **Mismatched query keys** — Server prefetch key must exactly match client useQuery key.

5. **Not using `isServer` check** — Use the `isServer` export from TanStack Query for the client/server check.

---

## Related

- **07-prefetching.md** — General prefetching patterns
- **09-suspense.md** — Suspense with SSR streaming
- **00-overview.md** — Basic setup
