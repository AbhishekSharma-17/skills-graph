# tRPC — Testing

> Source: [trpc.io/docs/server/server-side-calls](https://trpc.io/docs/server/server-side-calls) | Version: 11.16.0

## Table of Contents

- [Testing Strategy](#testing-strategy)
- [createCallerFactory](#createcallerfactory)
- [Unit Testing Procedures](#unit-testing-procedures)
- [Testing with Context](#testing-with-context)
- [Testing Middleware](#testing-middleware)
- [Integration Testing](#integration-testing)
- [Frontend Component Testing](#frontend-component-testing)
- [End-to-End Testing](#end-to-end-testing)

## Testing Strategy

| Level | What to Test | Tool |
|-------|-------------|------|
| **Unit** | Individual procedures, business logic | `createCallerFactory` |
| **Integration** | Full router with middleware + context | `createCallerFactory` + real DB |
| **Component** | React components with tRPC | Testing Library + mock tRPC |
| **E2E** | Full client-server flow | Playwright / real server |

`createCallerFactory` is the primary testing tool — it lets you call procedures directly without HTTP.

## createCallerFactory

Creates a function that produces a "caller" — a typed proxy that invokes procedures directly:

```typescript
import { createCallerFactory } from '@trpc/server';
import { appRouter } from './router';

const createCaller = createCallerFactory(appRouter);

// Create a caller with a specific context
const caller = createCaller({
  db: prisma,
  user: null,
});

// Call procedures directly
const users = await caller.user.list();
const post = await caller.post.getById({ id: '1' });
```

## Unit Testing Procedures

### Basic Query Test

```typescript
import { describe, it, expect } from 'vitest';
import { createCallerFactory } from '@trpc/server';
import { appRouter } from '@/server/router';
import { prisma } from '@/server/db';

const createCaller = createCallerFactory(appRouter);

describe('user.getById', () => {
  it('returns user when found', async () => {
    const user = await prisma.user.create({
      data: { name: 'Alice', email: 'alice@test.com' },
    });

    const caller = createCaller({ db: prisma, user: null });
    const result = await caller.user.getById({ id: user.id });

    expect(result).toMatchObject({
      id: user.id,
      name: 'Alice',
      email: 'alice@test.com',
    });
  });

  it('throws NOT_FOUND for missing user', async () => {
    const caller = createCaller({ db: prisma, user: null });

    await expect(
      caller.user.getById({ id: 'nonexistent' }),
    ).rejects.toThrow('NOT_FOUND');
  });
});
```

### Mutation Test

```typescript
describe('post.create', () => {
  it('creates a post for authenticated user', async () => {
    const user = await prisma.user.create({
      data: { name: 'Bob', email: 'bob@test.com' },
    });

    const caller = createCaller({
      db: prisma,
      user: { id: user.id, name: 'Bob' },
    });

    const post = await caller.post.create({
      title: 'Test Post',
      content: 'Hello World',
    });

    expect(post.title).toBe('Test Post');
    expect(post.authorId).toBe(user.id);
  });

  it('rejects unauthenticated users', async () => {
    const caller = createCaller({ db: prisma, user: null });

    await expect(
      caller.post.create({ title: 'Test', content: 'Nope' }),
    ).rejects.toThrow('UNAUTHORIZED');
  });
});
```

### Input Validation Test

```typescript
describe('user.create input validation', () => {
  const caller = createCaller({ db: prisma, user: null });

  it('rejects empty name', async () => {
    await expect(
      caller.user.create({ name: '', email: 'test@test.com' }),
    ).rejects.toThrow();
  });

  it('rejects invalid email', async () => {
    await expect(
      caller.user.create({ name: 'Alice', email: 'not-an-email' }),
    ).rejects.toThrow();
  });

  it('accepts valid input', async () => {
    const result = await caller.user.create({
      name: 'Alice',
      email: 'alice@test.com',
    });
    expect(result.id).toBeDefined();
  });
});
```

## Testing with Context

### Mock Context Factory

```typescript
// test/helpers.ts
import { createCallerFactory } from '@trpc/server';
import { appRouter } from '@/server/router';

const createCaller = createCallerFactory(appRouter);

type TestUser = { id: string; name: string; role: 'admin' | 'user' };

export function createTestCaller(user?: TestUser) {
  return createCaller({
    db: prisma,
    user: user ?? null,
    session: user ? { user, expires: new Date(Date.now() + 86400000) } : null,
  });
}

export const testUsers = {
  admin: { id: 'admin-1', name: 'Admin', role: 'admin' as const },
  regular: { id: 'user-1', name: 'User', role: 'user' as const },
};
```

### Using Test Helpers

```typescript
import { createTestCaller, testUsers } from '@/test/helpers';

describe('admin.settings', () => {
  it('allows admin to update settings', async () => {
    const caller = createTestCaller(testUsers.admin);
    const result = await caller.admin.settings.update({
      key: 'siteName',
      value: 'New Name',
    });
    expect(result.success).toBe(true);
  });

  it('denies regular users', async () => {
    const caller = createTestCaller(testUsers.regular);
    await expect(
      caller.admin.settings.update({ key: 'siteName', value: 'Hack' }),
    ).rejects.toThrow('FORBIDDEN');
  });
});
```

## Testing Middleware

Test middleware indirectly by testing procedures that use it:

```typescript
describe('auth middleware', () => {
  it('passes authenticated context to procedure', async () => {
    const user = testUsers.regular;
    const caller = createTestCaller(user);

    // protectedProcedure uses auth middleware
    const profile = await caller.user.getProfile();
    expect(profile.id).toBe(user.id);
  });

  it('blocks unauthenticated access', async () => {
    const caller = createTestCaller(); // No user

    await expect(caller.user.getProfile()).rejects.toThrow('UNAUTHORIZED');
  });
});

describe('rate limit middleware', () => {
  it('allows requests within limit', async () => {
    const caller = createTestCaller(testUsers.regular);

    // Should succeed 100 times
    for (let i = 0; i < 100; i++) {
      await caller.public.ping();
    }
  });

  it('blocks requests over limit', async () => {
    const caller = createTestCaller(testUsers.regular);

    // Exhaust the limit
    for (let i = 0; i < 100; i++) {
      await caller.public.ping();
    }

    await expect(caller.public.ping()).rejects.toThrow('TOO_MANY_REQUESTS');
  });
});
```

## Integration Testing

### With Real Database

```typescript
import { beforeAll, afterAll, beforeEach } from 'vitest';
import { PrismaClient } from '@prisma/client';

const testPrisma = new PrismaClient({
  datasourceUrl: process.env.TEST_DATABASE_URL,
});

beforeAll(async () => {
  await testPrisma.$connect();
});

afterAll(async () => {
  await testPrisma.$disconnect();
});

beforeEach(async () => {
  // Clean tables between tests
  await testPrisma.post.deleteMany();
  await testPrisma.user.deleteMany();
});

describe('post CRUD flow', () => {
  it('creates, reads, updates, and deletes a post', async () => {
    const user = await testPrisma.user.create({
      data: { name: 'Test', email: 'test@test.com' },
    });

    const caller = createCaller({
      db: testPrisma,
      user: { id: user.id, name: user.name },
    });

    // Create
    const post = await caller.post.create({
      title: 'Test',
      content: 'Content',
    });
    expect(post.id).toBeDefined();

    // Read
    const fetched = await caller.post.getById({ id: post.id });
    expect(fetched.title).toBe('Test');

    // Update
    const updated = await caller.post.update({
      id: post.id,
      title: 'Updated',
    });
    expect(updated.title).toBe('Updated');

    // Delete
    await caller.post.delete({ id: post.id });
    await expect(
      caller.post.getById({ id: post.id }),
    ).rejects.toThrow('NOT_FOUND');
  });
});
```

### Testing with HTTP (Supertest-like)

```typescript
import { createHTTPServer } from '@trpc/server/adapters/standalone';
import { createTRPCClient, httpBatchLink } from '@trpc/client';

describe('HTTP integration', () => {
  let server: ReturnType<typeof createHTTPServer>;
  let client: ReturnType<typeof createTRPCClient<AppRouter>>;

  beforeAll(() => {
    server = createHTTPServer({ router: appRouter, createContext });
    server.listen(0); // Random port
    const port = (server.server.address() as { port: number }).port;

    client = createTRPCClient<AppRouter>({
      links: [httpBatchLink({ url: `http://localhost:${port}` })],
    });
  });

  afterAll(() => {
    server.server.close();
  });

  it('handles batch requests', async () => {
    const [user, posts] = await Promise.all([
      client.user.getById.query({ id: '1' }),
      client.post.list.query({ limit: 10 }),
    ]);

    expect(user).toBeDefined();
    expect(posts).toBeInstanceOf(Array);
  });
});
```

## Frontend Component Testing

### With React Testing Library

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { httpBatchLink } from '@trpc/client';
import { TRPCProvider } from '@/trpc/client';
import { UserProfile } from './user-profile';

function createTestWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  const trpcClient = TRPCProvider.createClient({
    links: [httpBatchLink({ url: 'http://localhost:3000/api/trpc' })],
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <TRPCProvider client={trpcClient} queryClient={queryClient}>
          {children}
        </TRPCProvider>
      </QueryClientProvider>
    );
  };
}

describe('UserProfile', () => {
  it('renders user name', async () => {
    render(<UserProfile userId="1" />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
    });
  });
});
```

## End-to-End Testing

With Playwright:

```typescript
import { test, expect } from '@playwright/test';

test('user can create a post', async ({ page }) => {
  await page.goto('/posts/new');

  await page.fill('[name="title"]', 'E2E Test Post');
  await page.fill('[name="content"]', 'Created via Playwright');
  await page.click('button[type="submit"]');

  await expect(page.getByText('E2E Test Post')).toBeVisible();
});
```

## Common Pitfalls

1. **Use `createCallerFactory` for unit tests** — don't spin up an HTTP server unless you're specifically testing the HTTP layer.

2. **Clean database state between tests** — use `beforeEach` to truncate tables or use transactions that roll back.

3. **Test error cases, not just happy paths** — verify that `UNAUTHORIZED`, `NOT_FOUND`, and `BAD_REQUEST` errors are thrown correctly.

4. **Don't test tRPC internals** — test your business logic through procedures. Don't test that tRPC correctly routes or validates — that's tRPC's job.
