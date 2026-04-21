# tRPC — Routers & Procedures

> Source: [trpc.io/docs/server/routers](https://trpc.io/docs/server/routers) | Version: 11.16.0

## Table of Contents

- [Procedures Overview](#procedures-overview)
- [Queries](#queries)
- [Mutations](#mutations)
- [Subscriptions](#subscriptions)
- [Defining Routers](#defining-routers)
- [Merging Routers](#merging-routers)
- [Nested Routers](#nested-routers)
- [Procedure Chaining](#procedure-chaining)
- [Procedure Metadata](#procedure-metadata)

## Procedures Overview

A procedure is a function exposed by the server. There are three types:

| Type | HTTP Method | Purpose | Example |
|------|-------------|---------|---------|
| `query` | GET | Read data | Fetch a user, list posts |
| `mutation` | POST | Write data | Create user, update post, delete |
| `subscription` | SSE/WS | Real-time stream | Live notifications, chat |

Procedures are created from a base procedure (typically from `t.procedure` or a custom procedure with middleware):

```typescript
import { initTRPC } from '@trpc/server';

const t = initTRPC.create();

export const publicProcedure = t.procedure;
export const router = t.router;
```

## Queries

Queries are for reading data. They map to HTTP GET requests and are cached by React Query.

```typescript
const appRouter = router({
  // Simple query — no input
  getAll: publicProcedure.query(async () => {
    return db.user.findMany();
  }),

  // Query with input
  getById: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      const user = await db.user.findUnique({ where: { id: input.id } });
      if (!user) throw new TRPCError({ code: 'NOT_FOUND' });
      return user;
    }),

  // Query with optional input
  search: publicProcedure
    .input(z.object({
      query: z.string().optional(),
      limit: z.number().min(1).max(100).default(20),
      cursor: z.string().nullish(),
    }))
    .query(async ({ input }) => {
      const items = await db.post.findMany({
        take: input.limit + 1,
        where: input.query
          ? { title: { contains: input.query } }
          : undefined,
        cursor: input.cursor ? { id: input.cursor } : undefined,
      });

      let nextCursor: string | undefined;
      if (items.length > input.limit) {
        const next = items.pop();
        nextCursor = next?.id;
      }

      return { items, nextCursor };
    }),
});
```

## Mutations

Mutations are for creating, updating, or deleting data. They map to HTTP POST requests.

```typescript
const appRouter = router({
  create: publicProcedure
    .input(z.object({
      title: z.string().min(1).max(200),
      content: z.string().min(1),
      published: z.boolean().default(false),
    }))
    .mutation(async ({ input, ctx }) => {
      return db.post.create({
        data: {
          ...input,
          authorId: ctx.userId,
        },
      });
    }),

  update: publicProcedure
    .input(z.object({
      id: z.string(),
      title: z.string().min(1).max(200).optional(),
      content: z.string().optional(),
      published: z.boolean().optional(),
    }))
    .mutation(async ({ input }) => {
      const { id, ...data } = input;
      return db.post.update({ where: { id }, data });
    }),

  delete: publicProcedure
    .input(z.object({ id: z.string() }))
    .mutation(async ({ input }) => {
      await db.post.delete({ where: { id: input.id } });
      return { success: true };
    }),
});
```

## Subscriptions

Subscriptions provide real-time data via SSE (recommended in v11) or WebSockets. See `08-subscriptions-streaming.md` for full details.

```typescript
import { observable } from '@trpc/server/observable';

const appRouter = router({
  onNewMessage: publicProcedure
    .input(z.object({ channelId: z.string() }))
    .subscription(async function* ({ input }) {
      // Generator-based subscription (v11)
      for await (const message of messageStream(input.channelId)) {
        yield message;
      }
    }),
});
```

## Defining Routers

Routers group related procedures. Each router is a plain object of procedure definitions:

```typescript
// routers/user.ts
import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '../trpc';

export const userRouter = router({
  getProfile: publicProcedure
    .input(z.object({ userId: z.string() }))
    .query(async ({ input }) => {
      return db.user.findUnique({ where: { id: input.userId } });
    }),

  updateProfile: protectedProcedure
    .input(z.object({
      name: z.string().optional(),
      bio: z.string().max(500).optional(),
    }))
    .mutation(async ({ input, ctx }) => {
      return db.user.update({
        where: { id: ctx.userId },
        data: input,
      });
    }),

  deleteAccount: protectedProcedure
    .mutation(async ({ ctx }) => {
      await db.user.delete({ where: { id: ctx.userId } });
      return { success: true };
    }),
});
```

## Merging Routers

The root router merges sub-routers to form the complete API:

```typescript
// routers/_app.ts
import { router } from '../trpc';
import { userRouter } from './user';
import { postRouter } from './post';
import { commentRouter } from './comment';

export const appRouter = router({
  user: userRouter,
  post: postRouter,
  comment: commentRouter,
});

export type AppRouter = typeof appRouter;
```

Client usage becomes namespaced:

```typescript
// These are all typed
const user = await trpc.user.getProfile.query({ userId: '1' });
const post = await trpc.post.create.mutate({ title: 'Hello', content: '...' });
const comments = await trpc.comment.listByPost.query({ postId: '1' });
```

## Nested Routers

Routers can be nested to any depth:

```typescript
const appRouter = router({
  admin: router({
    user: router({
      ban: adminProcedure
        .input(z.object({ userId: z.string() }))
        .mutation(async ({ input }) => {
          // ...
        }),
      list: adminProcedure.query(async () => {
        // ...
      }),
    }),
    settings: router({
      get: adminProcedure.query(async () => {
        // ...
      }),
      update: adminProcedure
        .input(z.object({ key: z.string(), value: z.string() }))
        .mutation(async ({ input }) => {
          // ...
        }),
    }),
  }),
});

// Client: trpc.admin.user.ban.mutate({ userId: '1' })
// Client: trpc.admin.settings.get.query()
```

## Procedure Chaining

Procedures support method chaining for building up behavior:

```typescript
const createPost = publicProcedure
  .input(z.object({ title: z.string() }))   // 1. Validate input
  .use(loggerMiddleware)                      // 2. Add middleware
  .use(rateLimitMiddleware)                   // 3. More middleware
  .output(z.object({                          // 4. Validate output
    id: z.string(),
    title: z.string(),
  }))
  .mutation(async ({ input, ctx }) => {       // 5. Handler
    return db.post.create({ data: input });
  });
```

The chain order matters for middleware — they execute in the order they are added.

## Procedure Metadata

v11 supports attaching metadata to procedures for cross-cutting concerns like OpenAPI generation or authorization:

```typescript
import { initTRPC } from '@trpc/server';

interface Meta {
  authRequired: boolean;
  openapi?: { method: 'GET' | 'POST'; path: string };
}

const t = initTRPC.meta<Meta>().create();

const publicProcedure = t.procedure;

const appRouter = router({
  getUser: publicProcedure
    .meta({
      authRequired: false,
      openapi: { method: 'GET', path: '/users/{id}' },
    })
    .input(z.object({ id: z.string() }))
    .query(({ input }) => {
      return db.user.findUnique({ where: { id: input.id } });
    }),
});
```

Access metadata in middleware:

```typescript
const authMiddleware = t.middleware(async ({ meta, ctx, next }) => {
  if (meta?.authRequired && !ctx.user) {
    throw new TRPCError({ code: 'UNAUTHORIZED' });
  }
  return next();
});
```

## Common Pitfalls

1. **Don't mix up query and mutation** — queries use GET (cacheable), mutations use POST (side effects). Using a query for writes breaks React Query caching assumptions.

2. **Always export `AppRouter` as a type** — use `export type AppRouter = typeof appRouter` to ensure no server code leaks into the client bundle.

3. **Avoid circular router imports** — keep sub-routers in separate files and merge them in one root file.

4. **Input validation is optional but recommended** — without it, `input` is typed as `void` and the procedure takes no arguments.
