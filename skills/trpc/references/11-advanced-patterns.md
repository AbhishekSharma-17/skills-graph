# tRPC — Advanced Patterns

> Source: [trpc.io/docs/server/procedures](https://trpc.io/docs/server/procedures) | Version: 11.16.0

## Table of Contents

- [Inference Helpers](#inference-helpers)
- [Router Factory Pattern](#router-factory-pattern)
- [Procedure Builders](#procedure-builders)
- [Multi-Tenant Architecture](#multi-tenant-architecture)
- [RBAC Authorization](#rbac-authorization)
- [Data Transformers](#data-transformers)
- [Response Metadata](#response-metadata)
- [trpc-openapi Integration](#trpc-openapi-integration)
- [Performance Optimization](#performance-optimization)

## Inference Helpers

Extract types from your router without running code:

### Router Input/Output Types

```typescript
import type { inferRouterInputs, inferRouterOutputs } from '@trpc/server';
import type { AppRouter } from '@/server/router';

// Infer all inputs and outputs
type RouterInput = inferRouterInputs<AppRouter>;
type RouterOutput = inferRouterOutputs<AppRouter>;

// Use specific procedure types
type CreateUserInput = RouterInput['user']['create'];
// { name: string; email: string; role?: 'admin' | 'user' }

type UserOutput = RouterOutput['user']['getById'];
// { id: string; name: string; email: string; createdAt: Date }
```

### In React Components

```typescript
import type { inferRouterOutputs } from '@trpc/server';
import type { AppRouter } from '@/server/router';

type Post = inferRouterOutputs<AppRouter>['post']['getById'];

function PostCard({ post }: { post: Post }) {
  return (
    <div>
      <h2>{post.title}</h2>
      <p>{post.content}</p>
      <time>{post.createdAt.toLocaleDateString()}</time>
    </div>
  );
}
```

### Extracting Procedure Types

```typescript
import type { inferProcedureInput, inferProcedureOutput } from '@trpc/server';
import type { AppRouter } from '@/server/router';

// Get the type of a specific procedure
type CreatePostInput = inferProcedureInput<AppRouter['post']['create']>;
type CreatePostOutput = inferProcedureOutput<AppRouter['post']['create']>;
```

## Router Factory Pattern

Create reusable router templates for CRUD operations:

```typescript
import { z, type ZodType } from 'zod';
import { router, protectedProcedure } from './trpc';

function createCRUDRouter<
  TCreate extends ZodType,
  TUpdate extends ZodType,
>(opts: {
  name: string;
  createSchema: TCreate;
  updateSchema: TUpdate;
  getAll: () => Promise<unknown[]>;
  getById: (id: string) => Promise<unknown>;
  create: (data: z.infer<TCreate>) => Promise<unknown>;
  update: (id: string, data: z.infer<TUpdate>) => Promise<unknown>;
  remove: (id: string) => Promise<void>;
}) {
  return router({
    list: protectedProcedure.query(async () => {
      return opts.getAll();
    }),

    getById: protectedProcedure
      .input(z.object({ id: z.string() }))
      .query(async ({ input }) => {
        return opts.getById(input.id);
      }),

    create: protectedProcedure
      .input(opts.createSchema)
      .mutation(async ({ input }) => {
        return opts.create(input);
      }),

    update: protectedProcedure
      .input(z.object({ id: z.string(), data: opts.updateSchema }))
      .mutation(async ({ input }) => {
        return opts.update(input.id, input.data);
      }),

    delete: protectedProcedure
      .input(z.object({ id: z.string() }))
      .mutation(async ({ input }) => {
        await opts.remove(input.id);
        return { success: true };
      }),
  });
}

// Usage
export const tagRouter = createCRUDRouter({
  name: 'tag',
  createSchema: z.object({ name: z.string().min(1) }),
  updateSchema: z.object({ name: z.string().min(1).optional() }),
  getAll: () => db.tag.findMany(),
  getById: (id) => db.tag.findUniqueOrThrow({ where: { id } }),
  create: (data) => db.tag.create({ data }),
  update: (id, data) => db.tag.update({ where: { id }, data }),
  remove: (id) => db.tag.delete({ where: { id } }).then(() => {}),
});
```

## Procedure Builders

Create configurable procedure chains:

```typescript
import { initTRPC, TRPCError } from '@trpc/server';

const t = initTRPC.context<Context>().create();

function createProcedure(opts?: { rateLimit?: number; cache?: number }) {
  let proc = t.procedure;

  if (opts?.rateLimit) {
    proc = proc.use(createRateLimitMiddleware(opts.rateLimit));
  }

  if (opts?.cache) {
    proc = proc.use(createCacheMiddleware(opts.cache));
  }

  return proc;
}

// Usage
const cachedProcedure = createProcedure({ cache: 60 });
const limitedProcedure = createProcedure({ rateLimit: 10 });
const publicProcedure = createProcedure();
```

## Multi-Tenant Architecture

### Tenant-Scoped Procedures

```typescript
const tenantProcedure = protectedProcedure
  .input(z.object({ tenantId: z.string() }))
  .use(async ({ ctx, input, next }) => {
    const membership = await db.tenantMember.findFirst({
      where: {
        userId: ctx.user.id,
        tenantId: input.tenantId,
      },
    });

    if (!membership) {
      throw new TRPCError({
        code: 'FORBIDDEN',
        message: 'Not a member of this tenant',
      });
    }

    return next({
      ctx: {
        tenant: {
          id: input.tenantId,
          role: membership.role,
        },
      },
    });
  });

// Usage — ctx.tenant is guaranteed
const projectRouter = router({
  list: tenantProcedure.query(async ({ ctx }) => {
    return db.project.findMany({
      where: { tenantId: ctx.tenant.id },
    });
  }),
});
```

### Subdomain-Based Tenancy

```typescript
export const createContext = async ({ req }: { req: Request }) => {
  const url = new URL(req.url);
  const subdomain = url.hostname.split('.')[0];
  const tenant = await db.tenant.findUnique({
    where: { subdomain },
  });

  return {
    db: prisma,
    tenant,
    user: await getUser(req),
  };
};
```

## RBAC Authorization

### Permission-Based Middleware

```typescript
type Permission =
  | 'post:read'
  | 'post:write'
  | 'post:delete'
  | 'user:manage'
  | 'admin:all';

const rolePermissions: Record<string, Permission[]> = {
  admin: ['admin:all'],
  editor: ['post:read', 'post:write', 'post:delete'],
  viewer: ['post:read'],
};

function requirePermission(...permissions: Permission[]) {
  return t.middleware(async ({ ctx, next }) => {
    if (!ctx.user) {
      throw new TRPCError({ code: 'UNAUTHORIZED' });
    }

    const userPermissions = rolePermissions[ctx.user.role] ?? [];
    const hasPermission =
      userPermissions.includes('admin:all') ||
      permissions.every(p => userPermissions.includes(p));

    if (!hasPermission) {
      throw new TRPCError({
        code: 'FORBIDDEN',
        message: `Missing permission: ${permissions.join(', ')}`,
      });
    }

    return next({ ctx: { user: ctx.user } });
  });
}

// Usage
const postRouter = router({
  list: publicProcedure.query(/* ... */),
  create: protectedProcedure.use(requirePermission('post:write')).mutation(/* ... */),
  delete: protectedProcedure.use(requirePermission('post:delete')).mutation(/* ... */),
  manageUsers: protectedProcedure.use(requirePermission('user:manage')).mutation(/* ... */),
});
```

## Data Transformers

Transformers serialize/deserialize complex types (Date, Map, Set, BigInt, etc.):

### Using superjson

```typescript
import superjson from 'superjson';

// Server
const t = initTRPC.create({
  transformer: superjson,
});

// Client — must match
const trpc = createTRPCClient<AppRouter>({
  links: [
    httpBatchLink({
      url: '/api/trpc',
      transformer: superjson,
    }),
  ],
});
```

With superjson, `Date` objects round-trip correctly:

```typescript
// Server returns a Date object
const appRouter = router({
  getUser: publicProcedure.query(async () => {
    return {
      name: 'Alice',
      createdAt: new Date(), // Date object, not string
    };
  }),
});

// Client receives a Date object (not a string)
const user = await trpc.getUser.query();
console.log(user.createdAt instanceof Date); // true
```

## Response Metadata

Control HTTP response headers and caching:

```typescript
const server = createHTTPServer({
  router: appRouter,
  createContext,
  responseMeta({ ctx, paths, errors, type }) {
    const allPublic = paths?.every(p => p.startsWith('public.'));
    const allQueries = type === 'query';
    const noErrors = errors.length === 0;

    if (allPublic && allQueries && noErrors) {
      return {
        headers: {
          'Cache-Control': 'public, s-maxage=60, stale-while-revalidate=300',
        },
      };
    }

    return {};
  },
});
```

## trpc-openapi Integration

Expose tRPC procedures as REST endpoints for external consumers:

```typescript
import { generateOpenApiDocument } from 'trpc-openapi';
import { appRouter } from './router';

const openApiDocument = generateOpenApiDocument(appRouter, {
  title: 'My API',
  version: '1.0.0',
  baseUrl: 'https://api.example.com',
});

// Add OpenAPI metadata to procedures
const appRouter = router({
  getUser: publicProcedure
    .meta({
      openapi: {
        method: 'GET',
        path: '/users/{id}',
        tags: ['users'],
        summary: 'Get user by ID',
      },
    })
    .input(z.object({ id: z.string() }))
    .output(userSchema)
    .query(({ input }) => db.user.findUnique({ where: { id: input.id } })),
});
```

## Performance Optimization

### Batching Strategy

```typescript
// httpBatchLink batches calls in the same tick
// These 3 calls become 1 HTTP request:
const [user, posts, comments] = await Promise.all([
  trpc.user.getById.query({ id: '1' }),
  trpc.post.list.query({ limit: 20 }),
  trpc.comment.recent.query({ limit: 10 }),
]);
```

### Selective Streaming

```typescript
// Use httpBatchStreamLink for pages with mixed fast/slow queries
const trpc = createTRPCClient<AppRouter>({
  links: [
    splitLink({
      condition: (op) => op.path.startsWith('analytics.'),
      true: httpBatchStreamLink({ url: '/api/trpc' }), // Slow analytics
      false: httpBatchLink({ url: '/api/trpc' }),       // Fast queries
    }),
  ],
});
```

### Query Deduplication

React Query automatically deduplicates identical queries. Don't manually cache:

```typescript
// These share the same cache entry — only 1 request is made
function ComponentA() {
  const trpc = useTRPC();
  const { data } = useQuery(trpc.user.getById.queryOptions({ id: '1' }));
  return <div>{data?.name}</div>;
}

function ComponentB() {
  const trpc = useTRPC();
  const { data } = useQuery(trpc.user.getById.queryOptions({ id: '1' }));
  return <span>{data?.email}</span>;
}
```

## Common Pitfalls

1. **Don't over-abstract** — the router factory pattern is powerful but can make debugging harder. Use it for genuinely repetitive CRUD, not for every router.

2. **Transformer must match on both sides** — if you enable `superjson` on the server, every client link must also use it. Mismatches cause silent data corruption.

3. **Inference types are read-only** — inferred output types reflect what the server returns, not what you can mutate. Don't use output types as input to mutations.

4. **Permission checks should be in middleware, not handlers** — putting auth checks in procedure handlers means every developer must remember to add them. Middleware enforces it consistently.
