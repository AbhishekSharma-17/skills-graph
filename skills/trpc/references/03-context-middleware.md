# tRPC — Context & Middleware

> Source: [trpc.io/docs/server/middlewares](https://trpc.io/docs/server/middlewares) | Version: 11.16.0

## Table of Contents

- [Context](#context)
- [Creating Context](#creating-context)
- [Middleware Basics](#middleware-basics)
- [Context Extension](#context-extension)
- [Authentication Middleware](#authentication-middleware)
- [Middleware Chaining](#middleware-chaining)
- [Reusable Base Procedures](#reusable-base-procedures)
- [Common Middleware Patterns](#common-middleware-patterns)
- [Execution Order](#execution-order)

## Context

Context (`ctx`) is a shared object available to all procedures. It's created fresh for each request and contains request-scoped data like the current user, database connection, or request headers.

```typescript
// The context type flows through the entire procedure chain
const appRouter = router({
  getUser: publicProcedure.query(async ({ ctx }) => {
    // ctx.db, ctx.user, etc. — all typed
    return ctx.db.user.findFirst({ where: { id: ctx.user?.id } });
  }),
});
```

## Creating Context

Context is created via a factory function that receives the incoming request:

### Inner Context (Request-Independent)

```typescript
// context.ts
import { prisma } from './db';

export const createContext = async () => {
  return {
    db: prisma,
  };
};

export type Context = Awaited<ReturnType<typeof createContext>>;
```

### Outer Context (Request-Dependent)

```typescript
import { type CreateNextContextOptions } from '@trpc/server/adapters/next';
import { prisma } from './db';
import { getSession } from './auth';

export const createContext = async (opts: CreateNextContextOptions) => {
  const session = await getSession(opts.req);

  return {
    db: prisma,
    session,
    user: session?.user ?? null,
    req: opts.req,
    res: opts.res,
  };
};

export type Context = Awaited<ReturnType<typeof createContext>>;
```

### Connecting Context to tRPC

```typescript
import { initTRPC } from '@trpc/server';
import { type Context } from './context';

const t = initTRPC.context<Context>().create();

export const router = t.router;
export const publicProcedure = t.procedure;
```

## Middleware Basics

Middleware wraps procedure execution. It receives `opts` with access to `ctx`, `input`, `rawInput`, `path`, `type`, and a `next()` function:

```typescript
const loggerMiddleware = t.middleware(async ({ path, type, next }) => {
  const start = Date.now();
  const result = await next();
  const duration = Date.now() - start;

  if (result.ok) {
    console.log(`[${type}] ${path} — ${duration}ms`);
  } else {
    console.error(`[${type}] ${path} — FAILED — ${duration}ms`);
  }

  return result;
});
```

Key rules:
- Middleware **must** call `next()` and return its result
- `next()` returns `{ ok: true; data: T }` or `{ ok: false; error: TRPCError }`
- Middleware can short-circuit by throwing `TRPCError` before calling `next()`

## Context Extension

Middleware can add or override context properties by passing them to `next()`:

```typescript
const withTimestamp = t.middleware(async ({ next }) => {
  return next({
    ctx: {
      requestedAt: new Date(),
    },
  });
});

// Procedure using this middleware sees ctx.requestedAt
const timedProcedure = publicProcedure.use(withTimestamp);
```

Context extension is type-safe — downstream procedures see the merged context type.

## Authentication Middleware

The most common middleware pattern:

```typescript
import { TRPCError } from '@trpc/server';

const isAuthenticated = t.middleware(async ({ ctx, next }) => {
  if (!ctx.session?.user) {
    throw new TRPCError({
      code: 'UNAUTHORIZED',
      message: 'You must be logged in',
    });
  }

  return next({
    ctx: {
      // Narrows the type: user is guaranteed non-null downstream
      user: ctx.session.user,
    },
  });
});

export const protectedProcedure = publicProcedure.use(isAuthenticated);
```

Usage:

```typescript
const appRouter = router({
  // This requires authentication — ctx.user is non-null
  updateProfile: protectedProcedure
    .input(z.object({ name: z.string() }))
    .mutation(async ({ input, ctx }) => {
      return db.user.update({
        where: { id: ctx.user.id }, // ctx.user is guaranteed here
        data: { name: input.name },
      });
    }),

  // This is public — ctx.user may be null
  getPost: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input, ctx }) => {
      return db.post.findUnique({ where: { id: input.id } });
    }),
});
```

### Role-Based Authorization

```typescript
const hasRole = (requiredRole: 'admin' | 'moderator') =>
  t.middleware(async ({ ctx, next }) => {
    if (!ctx.user) {
      throw new TRPCError({ code: 'UNAUTHORIZED' });
    }
    if (ctx.user.role !== requiredRole && ctx.user.role !== 'admin') {
      throw new TRPCError({
        code: 'FORBIDDEN',
        message: `Requires role: ${requiredRole}`,
      });
    }
    return next({ ctx: { user: ctx.user } });
  });

export const adminProcedure = protectedProcedure.use(hasRole('admin'));
export const moderatorProcedure = protectedProcedure.use(hasRole('moderator'));
```

## Middleware Chaining

Attach multiple middlewares with `.use()`:

```typescript
const loggedAndTimedProcedure = publicProcedure
  .use(loggerMiddleware)
  .use(withTimestamp)
  .use(rateLimitMiddleware);
```

Or compose middleware that calls another:

```typescript
const composedMiddleware = t.middleware(async (opts) => {
  // Do something first
  console.log('Before auth check');

  // Delegate to auth middleware
  return isAuthenticated({ ...opts, next: async (newOpts) => {
    // Do something after auth but before handler
    console.log('Authenticated, proceeding');
    return opts.next(newOpts);
  }});
});
```

## Reusable Base Procedures

Create domain-specific base procedures that bundle common middleware:

```typescript
// trpc.ts — procedure hierarchy

// Level 0: Raw procedure
export const publicProcedure = t.procedure;

// Level 1: Authenticated
export const protectedProcedure = publicProcedure.use(isAuthenticated);

// Level 2: Organization-scoped
export const orgProcedure = protectedProcedure
  .input(z.object({ orgId: z.string() }))
  .use(async ({ ctx, input, next }) => {
    const membership = await db.orgMember.findFirst({
      where: { userId: ctx.user.id, orgId: input.orgId },
    });
    if (!membership) {
      throw new TRPCError({ code: 'FORBIDDEN' });
    }
    return next({
      ctx: { org: membership },
    });
  });

// Level 3: Admin-only within org
export const orgAdminProcedure = orgProcedure.use(async ({ ctx, next }) => {
  if (ctx.org.role !== 'admin') {
    throw new TRPCError({ code: 'FORBIDDEN' });
  }
  return next();
});
```

## Common Middleware Patterns

### Rate Limiting

```typescript
const rateLimiter = new Map<string, { count: number; resetAt: number }>();

const rateLimitMiddleware = t.middleware(async ({ ctx, next }) => {
  const key = ctx.user?.id ?? ctx.req?.headers?.['x-forwarded-for'] ?? 'anon';
  const now = Date.now();
  const entry = rateLimiter.get(key);

  if (entry && entry.resetAt > now && entry.count >= 100) {
    throw new TRPCError({
      code: 'TOO_MANY_REQUESTS',
      message: 'Rate limit exceeded',
    });
  }

  if (!entry || entry.resetAt <= now) {
    rateLimiter.set(key, { count: 1, resetAt: now + 60_000 });
  } else {
    entry.count++;
  }

  return next();
});
```

### Input Sanitization

```typescript
const sanitizeMiddleware = t.middleware(async ({ rawInput, next }) => {
  // Log raw input for debugging (before validation)
  console.log('Raw input:', JSON.stringify(rawInput));
  return next();
});
```

### Timing / Metrics

```typescript
const metricsMiddleware = t.middleware(async ({ path, type, next }) => {
  const start = performance.now();
  const result = await next();
  const duration = performance.now() - start;

  metrics.record({
    procedure: path,
    type,
    duration,
    success: result.ok,
  });

  return result;
});
```

## Execution Order

Middleware executes in the order it's attached:

```
Request
  → Global middlewares (applied to t.procedure)
    → Router-level middlewares
      → Procedure-level middlewares (.use() calls)
        → Input validation
          → Handler (query/mutation/subscription)
        → Output validation
      ← Procedure middleware (after next())
    ← Router middleware (after next())
  ← Global middleware (after next())
Response
```

Each middleware's code before `next()` runs top-down, and code after `next()` runs bottom-up (like Koa middleware).

## Common Pitfalls

1. **Always return `next()`** — forgetting to return the result of `next()` silently drops the response.

2. **Don't mutate `ctx` directly** — always use `next({ ctx: { ...newFields } })` to extend context. Direct mutation loses type safety.

3. **Middleware order matters** — put auth before authorization, logging before everything. The order of `.use()` calls determines execution order.

4. **Context extension merges, doesn't replace** — `next({ ctx: { user } })` adds `user` to the existing context, it doesn't create a new one from scratch.
