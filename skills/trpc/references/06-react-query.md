# tRPC — React Query Integration

> Source: [trpc.io/docs/client/tanstack-react-query/usage](https://trpc.io/docs/client/tanstack-react-query/usage) | Version: 11.16.0

## Table of Contents

- [Setup](#setup)
- [Query Options Pattern (v11)](#query-options-pattern-v11)
- [useQuery](#usequery)
- [useMutation](#usemutation)
- [useSuspenseQuery](#usesuspensequery)
- [useInfiniteQuery](#useinfinitequery)
- [Prefetching](#prefetching)
- [Cache Invalidation](#cache-invalidation)
- [Optimistic Updates](#optimistic-updates)
- [Query Client Configuration](#query-client-configuration)

## Setup

### Install Packages

```bash
npm install @trpc/server @trpc/client @trpc/tanstack-react-query @tanstack/react-query zod
```

### Create tRPC React Utilities

```typescript
// trpc/client.tsx
'use client';

import { createTRPCContext } from '@trpc/tanstack-react-query';
import type { AppRouter } from '@/server/router';

export const { TRPCProvider, useTRPC } = createTRPCContext<AppRouter>();
```

### Create Query Client

```typescript
// trpc/query-client.ts
import { QueryClient } from '@tanstack/react-query';

let clientQueryClientSingleton: QueryClient | undefined;

export function getQueryClient() {
  if (typeof window === 'undefined') {
    return new QueryClient({
      defaultOptions: {
        queries: { staleTime: 30 * 1000 },
      },
    });
  }
  if (!clientQueryClientSingleton) {
    clientQueryClientSingleton = new QueryClient({
      defaultOptions: {
        queries: { staleTime: 30 * 1000 },
      },
    });
  }
  return clientQueryClientSingleton;
}
```

### Wrap Your App

```typescript
// app/providers.tsx
'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { httpBatchLink } from '@trpc/client';
import { useState } from 'react';
import { TRPCProvider } from '@/trpc/client';
import { getQueryClient } from '@/trpc/query-client';

export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient();
  const [trpcClient] = useState(() =>
    TRPCProvider.createClient({
      links: [
        httpBatchLink({
          url: '/api/trpc',
        }),
      ],
    }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <TRPCProvider client={trpcClient} queryClient={queryClient}>
        {children}
      </TRPCProvider>
    </QueryClientProvider>
  );
}
```

## Query Options Pattern (v11)

tRPC v11 uses the **query options** pattern from TanStack Query v5. Instead of custom hooks, you pass `trpc.<path>.queryOptions()` to standard React Query hooks:

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTRPC } from '@/trpc/client';

function UserProfile({ userId }: { userId: string }) {
  const trpc = useTRPC();

  // v11 pattern: queryOptions + useQuery
  const userQuery = useQuery(
    trpc.user.getById.queryOptions({ id: userId })
  );

  return <div>{userQuery.data?.name}</div>;
}
```

Why this pattern?
- Uses standard React Query hooks (better ecosystem compatibility)
- Works with React Suspense out of the box
- Enables easy prefetching with the same options object
- Full compatibility with TanStack Query v5 features

## useQuery

```typescript
function PostList() {
  const trpc = useTRPC();

  // Basic query
  const postsQuery = useQuery(
    trpc.post.list.queryOptions({ limit: 20 })
  );

  // Query with enabled flag
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const detailQuery = useQuery(
    trpc.post.getById.queryOptions(
      { id: selectedId! },
      { enabled: selectedId !== null },
    )
  );

  // Query with refetch interval
  const statsQuery = useQuery(
    trpc.stats.getCurrent.queryOptions(undefined, {
      refetchInterval: 5000,
    })
  );

  if (postsQuery.isLoading) return <Spinner />;
  if (postsQuery.error) return <Error message={postsQuery.error.message} />;

  return (
    <ul>
      {postsQuery.data.map(post => (
        <li key={post.id} onClick={() => setSelectedId(post.id)}>
          {post.title}
        </li>
      ))}
    </ul>
  );
}
```

## useMutation

```typescript
function CreatePostForm() {
  const trpc = useTRPC();
  const queryClient = useQueryClient();

  const createPost = useMutation(
    trpc.post.create.mutationOptions({
      onSuccess() {
        // Invalidate post list cache after creating
        queryClient.invalidateQueries({
          queryKey: trpc.post.list.queryKey(),
        });
      },
      onError(err) {
        toast.error(err.message);
      },
    })
  );

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    createPost.mutate({
      title: data.get('title') as string,
      content: data.get('content') as string,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="title" required />
      <textarea name="content" required />
      <button type="submit" disabled={createPost.isPending}>
        {createPost.isPending ? 'Creating...' : 'Create Post'}
      </button>
    </form>
  );
}
```

## useSuspenseQuery

For React Suspense (data is guaranteed available — no loading states):

```typescript
function UserProfile({ userId }: { userId: string }) {
  const trpc = useTRPC();

  // Data is guaranteed — no undefined check needed
  const { data: user } = useSuspenseQuery(
    trpc.user.getById.queryOptions({ id: userId })
  );

  return <div>{user.name}</div>;
}

// Parent wraps in Suspense
function UserPage({ userId }: { userId: string }) {
  return (
    <Suspense fallback={<Spinner />}>
      <UserProfile userId={userId} />
    </Suspense>
  );
}
```

## useInfiniteQuery

For paginated / infinite scroll:

```typescript
function InfinitePostList() {
  const trpc = useTRPC();

  const postsQuery = useInfiniteQuery(
    trpc.post.infiniteList.infiniteQueryOptions(
      { limit: 20 },
      {
        getNextPageParam: (lastPage) => lastPage.nextCursor,
      },
    )
  );

  return (
    <div>
      {postsQuery.data?.pages.map((page, i) => (
        <div key={i}>
          {page.items.map(post => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      ))}

      <button
        onClick={() => postsQuery.fetchNextPage()}
        disabled={!postsQuery.hasNextPage || postsQuery.isFetchingNextPage}
      >
        {postsQuery.isFetchingNextPage ? 'Loading...' : 'Load More'}
      </button>
    </div>
  );
}
```

Server procedure for infinite queries:

```typescript
const appRouter = router({
  infiniteList: publicProcedure
    .input(z.object({
      limit: z.number().min(1).max(100).default(20),
      cursor: z.string().nullish(),
    }))
    .query(async ({ input }) => {
      const items = await db.post.findMany({
        take: input.limit + 1,
        cursor: input.cursor ? { id: input.cursor } : undefined,
        orderBy: { createdAt: 'desc' },
      });

      let nextCursor: string | undefined;
      if (items.length > input.limit) {
        nextCursor = items.pop()!.id;
      }

      return { items, nextCursor };
    }),
});
```

## Prefetching

### Server-Side Prefetching (Next.js App Router)

```typescript
// app/posts/page.tsx
import { dehydrate, HydrationBoundary } from '@tanstack/react-query';
import { createTRPCOptionsProxy } from '@trpc/tanstack-react-query';
import { appRouter } from '@/server/router';
import { createContext } from '@/server/context';
import { getQueryClient } from '@/trpc/query-client';
import { PostList } from './post-list';

const trpc = createTRPCOptionsProxy<AppRouter>(appRouter);

export default async function PostsPage() {
  const queryClient = getQueryClient();

  await queryClient.prefetchQuery(
    trpc.post.list.queryOptions({ limit: 20 })
  );

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <PostList />
    </HydrationBoundary>
  );
}
```

### Client-Side Prefetching

```typescript
function PostLink({ postId }: { postId: string }) {
  const trpc = useTRPC();
  const queryClient = useQueryClient();

  const prefetch = () => {
    queryClient.prefetchQuery(
      trpc.post.getById.queryOptions({ id: postId })
    );
  };

  return (
    <Link href={`/posts/${postId}`} onMouseEnter={prefetch}>
      View Post
    </Link>
  );
}
```

## Cache Invalidation

### Using queryKey

```typescript
const trpc = useTRPC();
const queryClient = useQueryClient();

// Invalidate a specific query
queryClient.invalidateQueries({
  queryKey: trpc.post.getById.queryKey({ id: '1' }),
});

// Invalidate all queries under a router path
queryClient.invalidateQueries({
  queryKey: trpc.post.queryKey(), // All post.* queries
});

// Invalidate everything
queryClient.invalidateQueries();
```

### After Mutations

```typescript
const deleteMutation = useMutation(
  trpc.post.delete.mutationOptions({
    onSuccess(_, { id }) {
      // Remove from cache immediately
      queryClient.removeQueries({
        queryKey: trpc.post.getById.queryKey({ id }),
      });
      // Refetch the list
      queryClient.invalidateQueries({
        queryKey: trpc.post.list.queryKey(),
      });
    },
  })
);
```

## Optimistic Updates

```typescript
const updateMutation = useMutation(
  trpc.post.update.mutationOptions({
    async onMutate(newData) {
      const queryKey = trpc.post.getById.queryKey({ id: newData.id });

      await queryClient.cancelQueries({ queryKey });

      const previousPost = queryClient.getQueryData(queryKey);

      queryClient.setQueryData(queryKey, (old: Post | undefined) =>
        old ? { ...old, ...newData } : old,
      );

      return { previousPost, queryKey };
    },
    onError(_err, _newData, context) {
      if (context?.previousPost) {
        queryClient.setQueryData(context.queryKey, context.previousPost);
      }
    },
    onSettled() {
      queryClient.invalidateQueries({
        queryKey: trpc.post.queryKey(),
      });
    },
  })
);
```

## Query Client Configuration

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,        // 30s before refetch
      gcTime: 5 * 60 * 1000,       // 5min garbage collection
      retry: 1,                     // Retry once on failure
      refetchOnWindowFocus: false,  // Disable refetch on tab focus
    },
    mutations: {
      retry: 0,                     // Don't retry mutations
    },
  },
});
```

## Common Pitfalls

1. **Use `queryOptions()` not `.useQuery()`** — v11 deprecates the `trpc.path.useQuery()` pattern. Use `useQuery(trpc.path.queryOptions())` instead.

2. **Query keys are generated automatically** — don't construct query keys manually. Use `trpc.path.queryKey()` for invalidation.

3. **Singleton QueryClient on the client** — in the browser, reuse the same `QueryClient` instance. On the server, create a new one per request.

4. **Don't forget `HydrationBoundary`** — when prefetching on the server, wrap the component tree in `HydrationBoundary` with the dehydrated state.
