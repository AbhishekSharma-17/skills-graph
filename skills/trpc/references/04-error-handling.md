# tRPC — Error Handling

> Source: [trpc.io/docs/server/error-handling](https://trpc.io/docs/server/error-handling) | Version: 11.16.0

## Table of Contents

- [TRPCError](#trpcerror)
- [Error Codes](#error-codes)
- [Throwing Errors](#throwing-errors)
- [Error Formatting](#error-formatting)
- [Client-Side Error Handling](#client-side-error-handling)
- [Error Shapes](#error-shapes)
- [Error Handling in Middleware](#error-handling-in-middleware)

## TRPCError

`TRPCError` is the standard error class for tRPC. Always throw `TRPCError` (not generic `Error`) inside procedures and middleware:

```typescript
import { TRPCError } from '@trpc/server';

throw new TRPCError({
  code: 'NOT_FOUND',
  message: 'User not found',
  cause: originalError, // optional: wrap the original error
});
```

If a non-TRPCError is thrown inside a procedure, tRPC wraps it as an `INTERNAL_SERVER_ERROR` automatically.

## Error Codes

tRPC maps its error codes to HTTP status codes:

| tRPC Code | HTTP Status | When to Use |
|-----------|-------------|-------------|
| `BAD_REQUEST` | 400 | Malformed request (validation failures are automatic) |
| `UNAUTHORIZED` | 401 | Not logged in / invalid credentials |
| `FORBIDDEN` | 403 | Logged in but lacking permission |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `METHOD_NOT_SUPPORTED` | 405 | Wrong HTTP method |
| `TIMEOUT` | 408 | Operation timed out |
| `CONFLICT` | 409 | Resource conflict (duplicate, version mismatch) |
| `PRECONDITION_FAILED` | 412 | Business rule violation |
| `PAYLOAD_TOO_LARGE` | 413 | Request body too large |
| `UNPROCESSABLE_CONTENT` | 422 | Semantically invalid |
| `TOO_MANY_REQUESTS` | 429 | Rate limited |
| `CLIENT_CLOSED_REQUEST` | 499 | Client disconnected |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |
| `NOT_IMPLEMENTED` | 501 | Feature not implemented |
| `BAD_GATEWAY` | 502 | Upstream service error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily down |
| `GATEWAY_TIMEOUT` | 504 | Upstream timeout |

## Throwing Errors

### In Procedures

```typescript
const appRouter = router({
  getUser: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      const user = await db.user.findUnique({ where: { id: input.id } });

      if (!user) {
        throw new TRPCError({
          code: 'NOT_FOUND',
          message: `User with id '${input.id}' not found`,
        });
      }

      return user;
    }),

  createTeam: protectedProcedure
    .input(z.object({ name: z.string() }))
    .mutation(async ({ input, ctx }) => {
      const existing = await db.team.findFirst({
        where: { name: input.name, ownerId: ctx.user.id },
      });

      if (existing) {
        throw new TRPCError({
          code: 'CONFLICT',
          message: 'Team with this name already exists',
        });
      }

      return db.team.create({
        data: { name: input.name, ownerId: ctx.user.id },
      });
    }),
});
```

### Wrapping External Errors

```typescript
const appRouter = router({
  fetchExternalData: publicProcedure.query(async () => {
    try {
      const res = await fetch('https://api.external.com/data');
      if (!res.ok) {
        throw new TRPCError({
          code: 'BAD_GATEWAY',
          message: 'External API returned an error',
        });
      }
      return res.json();
    } catch (err) {
      if (err instanceof TRPCError) throw err;
      throw new TRPCError({
        code: 'INTERNAL_SERVER_ERROR',
        message: 'Failed to fetch external data',
        cause: err,
      });
    }
  }),
});
```

## Error Formatting

Customize the error shape sent to clients using `errorFormatter`:

```typescript
import { initTRPC } from '@trpc/server';
import { ZodError } from 'zod';

const t = initTRPC.context<Context>().create({
  errorFormatter({ shape, error }) {
    return {
      ...shape,
      data: {
        ...shape.data,
        // Add Zod validation details
        zodError:
          error.cause instanceof ZodError
            ? error.cause.flatten()
            : null,
      },
    };
  },
});
```

The default error shape:

```typescript
{
  message: string;
  code: number;        // HTTP-like numeric code
  data: {
    code: string;      // tRPC error code (e.g., 'NOT_FOUND')
    httpStatus: number; // HTTP status code
    path?: string;     // Procedure path
    stack?: string;    // Stack trace (development only)
  };
}
```

## Client-Side Error Handling

### Vanilla Client

```typescript
import { TRPCClientError } from '@trpc/client';

try {
  const user = await trpc.user.getById.query({ id: '123' });
} catch (err) {
  if (err instanceof TRPCClientError) {
    console.log(err.message);        // Error message
    console.log(err.data?.code);     // 'NOT_FOUND', 'UNAUTHORIZED', etc.
    console.log(err.data?.zodError); // Zod validation errors (if formatted)
  }
}
```

### React Query Integration

```typescript
function UserProfile({ userId }: { userId: string }) {
  const userQuery = useQuery(
    trpc.user.getById.queryOptions({ id: userId })
  );

  if (userQuery.error) {
    const err = userQuery.error;
    if (err.data?.code === 'NOT_FOUND') {
      return <NotFoundPage />;
    }
    if (err.data?.code === 'UNAUTHORIZED') {
      return <LoginRedirect />;
    }
    return <ErrorPage message={err.message} />;
  }

  if (userQuery.isLoading) return <Spinner />;

  return <div>{userQuery.data.name}</div>;
}
```

### Form Validation Errors

```typescript
function CreateUserForm() {
  const createUser = useMutation(
    trpc.user.create.mutationOptions()
  );

  const handleSubmit = (data: FormData) => {
    createUser.mutate(data, {
      onError(err) {
        if (err.data?.zodError) {
          const fieldErrors = err.data.zodError.fieldErrors;
          // fieldErrors: { name?: string[], email?: string[] }
          setErrors(fieldErrors);
        }
      },
    });
  };
}
```

## Error Shapes

### Extending Error Shape with Custom Data

```typescript
const t = initTRPC.context<Context>().create({
  errorFormatter({ shape, error }) {
    return {
      ...shape,
      data: {
        ...shape.data,
        zodError:
          error.cause instanceof ZodError
            ? error.cause.flatten()
            : null,
        // Add request ID for support tickets
        requestId: crypto.randomUUID(),
      },
    };
  },
});
```

### Hiding Stack Traces in Production

```typescript
const t = initTRPC.create({
  errorFormatter({ shape }) {
    return {
      ...shape,
      data: {
        ...shape.data,
        stack: process.env.NODE_ENV === 'development' ? shape.data.stack : undefined,
      },
    };
  },
});
```

## Error Handling in Middleware

Middleware can catch and transform errors:

```typescript
const errorLoggingMiddleware = t.middleware(async ({ path, next }) => {
  const result = await next();

  if (!result.ok) {
    // Log the error but don't modify it
    console.error(`Procedure ${path} failed:`, result.error);
  }

  return result;
});
```

Middleware can also wrap errors:

```typescript
const sentryMiddleware = t.middleware(async ({ path, type, next }) => {
  try {
    return await next();
  } catch (error) {
    Sentry.captureException(error, {
      tags: { procedure: path, type },
    });
    throw error; // Re-throw so tRPC handles it
  }
});
```

## Common Pitfalls

1. **Don't throw generic `Error`** — always use `TRPCError`. Generic errors become `INTERNAL_SERVER_ERROR` with the original message hidden in production.

2. **Don't expose sensitive information** in error messages — error messages are sent to the client. Put sensitive details in `cause` instead.

3. **Input validation errors are automatic** — Zod validation failures automatically become `BAD_REQUEST` errors. Don't manually catch and re-throw them.

4. **Use `cause` for error chaining** — when wrapping external errors, pass the original as `cause` to preserve the stack trace for debugging.
