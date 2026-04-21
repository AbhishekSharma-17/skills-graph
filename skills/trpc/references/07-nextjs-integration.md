# tRPC — Next.js Integration

> Source: [trpc.io/docs/client/nextjs](https://trpc.io/docs/client/nextjs) | Version: 11.16.0

## Table of Contents

- [App Router Setup](#app-router-setup)
- [API Route Handler](#api-route-handler)
- [Server-Side tRPC](#server-side-trpc)
- [Client-Side tRPC](#client-side-trpc)
- [React Server Components](#react-server-components)
- [Server Actions with tRPC](#server-actions-with-trpc)
- [Pages Router Setup](#pages-router-setup)
- [Deployment Considerations](#deployment-considerations)

## App Router Setup

### Step 1: Initialize tRPC Server

```typescript
// server/trpc.ts
import { initTRPC, TRPCError } from '@trpc/server';
import superjson from 'superjson';

export const createTRPCContext = async (opts: { headers: Headers }) => {
  const session = await getServerSession();
  return {
    db: prisma,
    session,
    user: session?.user ?? null,
  };
};

const t = initTRPC.context<typeof createTRPCContext>().create({
  transformer: superjson,
});

export const router = t.router;
export const publicProcedure = t.procedure;
export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.user) throw new TRPCError({ code: 'UNAUTHORIZED' });
  return next({ ctx: { user: ctx.user } });
});
```

### Step 2: Define Your Router

```typescript
// server/routers/_app.ts
import { router } from '../trpc';
import { userRouter } from './user';
import { postRouter } from './post';

export const appRouter = router({
  user: userRouter,
  post: postRouter,
});

export type AppRouter = typeof appRouter;
```

### Step 3: Create the API Handler

```typescript
// app/api/trpc/[trpc]/route.ts
import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { appRouter } from '@/server/routers/_app';
import { createTRPCContext } from '@/server/trpc';

const handler = (req: Request) =>
  fetchRequestHandler({
    endpoint: '/api/trpc',
    req,
    router: appRouter,
    createContext: () => createTRPCContext({ headers: req.headers }),
  });

export { handler as GET, handler as POST };
```

### Step 4: Client Setup

```typescript
// trpc/client.tsx
'use client';

import { createTRPCContext } from '@trpc/tanstack-react-query';
import superjson from 'superjson';
import type { AppRouter } from '@/server/routers/_app';

export const { TRPCProvider, useTRPC } = createTRPCContext<AppRouter>();
```

```typescript
// trpc/query-client.ts
import { QueryClient } from '@tanstack/react-query';

let browserClient: QueryClient | undefined;

export function getQueryClient() {
  if (typeof window === 'undefined') {
    return new QueryClient({
      defaultOptions: { queries: { staleTime: 30_000 } },
    });
  }
  if (!browserClient) {
    browserClient = new QueryClient({
      defaultOptions: { queries: { staleTime: 30_000 } },
    });
  }
  return browserClient;
}
```

### Step 5: Provider in Layout

```typescript
// app/layout.tsx
import { Providers } from './providers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

```typescript
// app/providers.tsx
'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { httpBatchLink } from '@trpc/client';
import { useState } from 'react';
import superjson from 'superjson';
import { TRPCProvider } from '@/trpc/client';
import { getQueryClient } from '@/trpc/query-client';

export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient();
  const [trpcClient] = useState(() =>
    TRPCProvider.createClient({
      links: [
        httpBatchLink({
          url: '/api/trpc',
          transformer: superjson,
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

## API Route Handler

The fetch adapter works with Next.js App Router's route handlers:

```typescript
// app/api/trpc/[trpc]/route.ts
import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { appRouter } from '@/server/routers/_app';
import { createTRPCContext } from '@/server/trpc';

const handler = (req: Request) =>
  fetchRequestHandler({
    endpoint: '/api/trpc',
    req,
    router: appRouter,
    createContext: () => createTRPCContext({ headers: req.headers }),
    onError({ error, path }) {
      console.error(`tRPC error on '${path}':`, error);
    },
  });

export { handler as GET, handler as POST };
```

## Server-Side tRPC

### Direct Server Calls (No HTTP)

Call procedures directly on the server without HTTP overhead:

```typescript
// trpc/server.ts
import 'server-only';
import { createCallerFactory } from '@trpc/server';
import { appRouter } from '@/server/routers/_app';
import { createTRPCContext } from '@/server/trpc';

const createCaller = createCallerFactory(appRouter);

export async function getServerTRPC() {
  const ctx = await createTRPCContext({ headers: new Headers() });
  return createCaller(ctx);
}
```

Usage in Server Components:

```typescript
// app/users/page.tsx (Server Component)
import { getServerTRPC } from '@/trpc/server';

export default async function UsersPage() {
  const trpc = await getServerTRPC();
  const users = await trpc.user.list();

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

## Client-Side tRPC

Use the `useTRPC()` hook in Client Components:

```typescript
// components/user-list.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { useTRPC } from '@/trpc/client';

export function UserList() {
  const trpc = useTRPC();
  const usersQuery = useQuery(trpc.user.list.queryOptions());

  if (usersQuery.isLoading) return <div>Loading...</div>;
  if (usersQuery.error) return <div>Error: {usersQuery.error.message}</div>;

  return (
    <ul>
      {usersQuery.data?.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

## React Server Components

### Prefetch + Hydrate Pattern

The recommended pattern for RSC: prefetch on the server, hydrate on the client:

```typescript
// app/posts/page.tsx (Server Component)
import { dehydrate, HydrationBoundary } from '@tanstack/react-query';
import { createTRPCOptionsProxy } from '@trpc/tanstack-react-query';
import { appRouter } from '@/server/routers/_app';
import { createTRPCContext } from '@/server/trpc';
import { getQueryClient } from '@/trpc/query-client';
import { PostList } from './post-list';
import type { AppRouter } from '@/server/routers/_app';

export default async function PostsPage() {
  const queryClient = getQueryClient();
  const ctx = await createTRPCContext({ headers: new Headers() });

  const serverTRPC = createTRPCOptionsProxy<AppRouter>({
    ctx,
    router: appRouter,
  });

  await queryClient.prefetchQuery(
    serverTRPC.post.list.queryOptions({ limit: 20 })
  );

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <PostList />
    </HydrationBoundary>
  );
}
```

```typescript
// app/posts/post-list.tsx (Client Component)
'use client';

import { useQuery } from '@tanstack/react-query';
import { useTRPC } from '@/trpc/client';

export function PostList() {
  const trpc = useTRPC();
  // This picks up the prefetched data — no loading state on first render
  const postsQuery = useQuery(trpc.post.list.queryOptions({ limit: 20 }));

  return (
    <ul>
      {postsQuery.data?.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}
```

## Server Actions with tRPC

You can call tRPC procedures from Next.js Server Actions:

```typescript
// app/actions.ts
'use server';

import { getServerTRPC } from '@/trpc/server';
import { revalidatePath } from 'next/cache';

export async function createPost(formData: FormData) {
  const trpc = await getServerTRPC();

  await trpc.post.create({
    title: formData.get('title') as string,
    content: formData.get('content') as string,
  });

  revalidatePath('/posts');
}
```

## Pages Router Setup

For the older Next.js Pages Router:

```typescript
// pages/api/trpc/[trpc].ts
import { createNextApiHandler } from '@trpc/server/adapters/next';
import { appRouter } from '@/server/routers/_app';
import { createTRPCContext } from '@/server/trpc';

export default createNextApiHandler({
  router: appRouter,
  createContext: createTRPCContext,
});
```

```typescript
// utils/trpc.ts
import { httpBatchLink } from '@trpc/client';
import { createTRPCNext } from '@trpc/next';
import type { AppRouter } from '@/server/routers/_app';

export const trpc = createTRPCNext<AppRouter>({
  config() {
    return {
      links: [
        httpBatchLink({
          url: '/api/trpc',
        }),
      ],
    };
  },
  ssr: false, // Set to true for SSR
});
```

## Deployment Considerations

### Vercel

- Use the fetch adapter (App Router) — it works in Edge and Serverless runtimes
- Set `runtime: 'edge'` in the route handler for Edge Runtime
- httpBatchStreamLink works on Vercel

### Edge Runtime

```typescript
// app/api/trpc/[trpc]/route.ts
export const runtime = 'edge';
// ... same handler as above
```

### Environment Variables

```typescript
httpBatchLink({
  url: `${getBaseUrl()}/api/trpc`,
});

function getBaseUrl() {
  if (typeof window !== 'undefined') return '';
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  return `http://localhost:${process.env.PORT ?? 3000}`;
}
```

## Common Pitfalls

1. **Don't import server code in Client Components** — only import `type AppRouter`, never the actual router. Use `import type` to prevent server code from leaking into the client bundle.

2. **Use `superjson` transformer consistently** — if you enable superjson on the server, enable it on every client link too. Mismatched transformers cause deserialization errors.

3. **Create a new QueryClient per server request** — in the browser, use a singleton. On the server (RSC), create a fresh instance to prevent data leaking between requests.

4. **The `[trpc]` route segment is a catch-all** — it captures the procedure path. The `endpoint` option must match the file path (`/api/trpc`).
