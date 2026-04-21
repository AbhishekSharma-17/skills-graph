# tRPC — Input & Output Validation

> Source: [trpc.io/docs/server/validators](https://trpc.io/docs/server/validators) | Version: 11.16.0

## Table of Contents

- [Input Validation](#input-validation)
- [Supported Validators](#supported-validators)
- [Zod Integration](#zod-integration)
- [Output Validation](#output-validation)
- [Chaining Input](#chaining-input)
- [Complex Schema Patterns](#complex-schema-patterns)
- [Runtime vs Compile-Time](#runtime-vs-compile-time)

## Input Validation

Every procedure can define an `.input()` validator. The validator both:
1. **Validates** incoming data at runtime (returns 400 on bad input)
2. **Infers** the TypeScript type for the `input` parameter in the handler

```typescript
import { z } from 'zod';
import { publicProcedure, router } from './trpc';

const appRouter = router({
  createUser: publicProcedure
    .input(z.object({
      name: z.string().min(1).max(100),
      email: z.string().email(),
      role: z.enum(['admin', 'user']).default('user'),
    }))
    .mutation(async ({ input }) => {
      // input is typed as: { name: string; email: string; role: 'admin' | 'user' }
      return db.user.create({ data: input });
    }),
});
```

Without `.input()`, the procedure accepts no arguments and `input` is `void`.

## Supported Validators

tRPC works with any validation library that implements a compatible interface. The validator must either:
- Be a function `(input: unknown) => T`
- Have a `.parse(input: unknown): T` method (Zod, Valibot, ArkType)
- Have a `~standard` interface (Standard Schema)

| Library | Method | Example |
|---------|--------|---------|
| **Zod** | `.parse()` | `z.object({ name: z.string() })` |
| **Valibot** | Standard Schema | `v.object({ name: v.string() })` |
| **ArkType** | `.parse()` | `type({ name: 'string' })` |
| **Yup** | `.validateSync()` | Requires wrapper |
| **Custom** | Function | `(input: unknown) => schema.parse(input)` |

### Using a Custom Validation Function

```typescript
const appRouter = router({
  getUser: publicProcedure
    .input((val: unknown) => {
      if (typeof val === 'string') return val;
      throw new Error('Invalid input: expected string');
    })
    .query(({ input }) => {
      // input is typed as `string`
      return db.user.findUnique({ where: { id: input } });
    }),
});
```

## Zod Integration

Zod is the recommended validator. Common patterns:

### Basic Types

```typescript
// String with constraints
.input(z.object({
  name: z.string().min(1).max(255),
  email: z.string().email(),
  url: z.string().url().optional(),
  slug: z.string().regex(/^[a-z0-9-]+$/),
}))

// Numbers
.input(z.object({
  page: z.number().int().min(1).default(1),
  limit: z.number().int().min(1).max(100).default(20),
  price: z.number().positive(),
}))

// Enums and unions
.input(z.object({
  status: z.enum(['draft', 'published', 'archived']),
  sortBy: z.union([z.literal('date'), z.literal('title'), z.literal('views')]),
}))
```

### Arrays and Nested Objects

```typescript
.input(z.object({
  tags: z.array(z.string()).min(1).max(10),
  metadata: z.record(z.string(), z.unknown()),
  address: z.object({
    street: z.string(),
    city: z.string(),
    country: z.string().length(2),
    zip: z.string().optional(),
  }),
}))
```

### Discriminated Unions

```typescript
const notificationInput = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('email'),
    to: z.string().email(),
    subject: z.string(),
  }),
  z.object({
    type: z.literal('sms'),
    phone: z.string(),
    message: z.string().max(160),
  }),
  z.object({
    type: z.literal('push'),
    deviceToken: z.string(),
    title: z.string(),
  }),
]);

const appRouter = router({
  sendNotification: publicProcedure
    .input(notificationInput)
    .mutation(async ({ input }) => {
      switch (input.type) {
        case 'email':
          return sendEmail(input.to, input.subject);
        case 'sms':
          return sendSMS(input.phone, input.message);
        case 'push':
          return sendPush(input.deviceToken, input.title);
      }
    }),
});
```

### Preprocessing and Transforms

```typescript
.input(z.object({
  // Coerce string to number (from query params)
  page: z.coerce.number().int().min(1).default(1),

  // Transform input
  email: z.string().email().transform(s => s.toLowerCase()),

  // Date from string
  startDate: z.coerce.date(),

  // Trim whitespace
  name: z.string().trim().min(1),
}))
```

## Output Validation

Output validation is optional — tRPC already infers return types from your handler. Use output validators when:
- Returning data from untrusted sources (external APIs, raw DB queries)
- Stripping sensitive fields before sending to client
- Enforcing a stable API contract

```typescript
const appRouter = router({
  getUser: publicProcedure
    .input(z.object({ id: z.string() }))
    .output(z.object({
      id: z.string(),
      name: z.string(),
      email: z.string(),
      // Note: password hash is NOT in the output schema
    }))
    .query(async ({ input }) => {
      const user = await db.user.findUnique({ where: { id: input.id } });
      // If user has extra fields (like passwordHash), they're stripped
      return user;
    }),
});
```

### Output Validation on Subscriptions (v11)

```typescript
const appRouter = router({
  onMessage: publicProcedure
    .output(z.object({
      id: z.string(),
      text: z.string(),
      createdAt: z.date(),
    }))
    .subscription(async function* () {
      // Output schema validates each yielded value
      for await (const msg of messageStream()) {
        yield msg;
      }
    }),
});
```

## Chaining Input

You can call `.input()` multiple times to merge schemas. Each call's schema is merged with the previous one:

```typescript
const baseProcedure = publicProcedure
  .input(z.object({ orgId: z.string() }));

const appRouter = router({
  getOrgUser: baseProcedure
    .input(z.object({ userId: z.string() }))
    .query(({ input }) => {
      // input: { orgId: string; userId: string }
      return db.user.findFirst({
        where: { id: input.userId, orgId: input.orgId },
      });
    }),
});
```

This is powerful for base procedures that add common parameters (like `orgId` or `tenantId`) through middleware.

## Complex Schema Patterns

### Pagination Schema (Reusable)

```typescript
const paginationInput = z.object({
  limit: z.number().min(1).max(100).default(20),
  cursor: z.string().nullish(),
});

const paginatedOutput = <T extends z.ZodType>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    nextCursor: z.string().nullish(),
  });

const appRouter = router({
  listPosts: publicProcedure
    .input(paginationInput.extend({
      authorId: z.string().optional(),
    }))
    .query(async ({ input }) => {
      const items = await db.post.findMany({
        take: input.limit + 1,
        cursor: input.cursor ? { id: input.cursor } : undefined,
        where: input.authorId ? { authorId: input.authorId } : undefined,
      });

      let nextCursor: string | undefined;
      if (items.length > input.limit) {
        nextCursor = items.pop()!.id;
      }

      return { items, nextCursor };
    }),
});
```

### File Upload (v11 FormData Support)

```typescript
const appRouter = router({
  uploadAvatar: publicProcedure
    .input(z.instanceof(FormData))
    .mutation(async ({ input }) => {
      const file = input.get('file') as File;
      const buffer = await file.arrayBuffer();
      // Process file...
      return { url: '/avatars/uploaded.png' };
    }),
});
```

## Runtime vs Compile-Time

| Aspect | Without Validator | With Validator |
|--------|-------------------|----------------|
| Input type | `void` (no args) | Inferred from schema |
| Runtime check | None — raw input passed through | Validated before handler runs |
| Error on bad input | Handler may crash or behave unexpectedly | Clean 400 error with details |
| Client DX | No autocompletion for input | Full autocompletion |

Always use input validation for procedures that accept user data. Skip it only for zero-argument queries.

## Common Pitfalls

1. **Don't use `.passthrough()` on output schemas** — it defeats the purpose of output validation (stripping extra fields). Use `.strict()` if you want to reject unknown fields.

2. **Avoid heavy transforms in input schemas** — transforms make the input type differ from what the client sends, which can be confusing. Keep transforms simple (trim, lowercase).

3. **Don't validate output in development only** — if you validate output, do it in all environments. Inconsistent validation causes prod-only bugs.

4. **Use `.nullish()` for optional cursor fields** — `null` from JSON and `undefined` from missing params both need to work.
