# Prisma Transactions

> Source: [prisma.io/docs/orm/prisma-client/queries/transactions](https://www.prisma.io/docs/orm/prisma-client/queries/transactions) — Prisma ORM v7.x

## Table of Contents

- [Transaction Types Overview](#transaction-types-overview)
- [Nested Writes (Implicit Transactions)](#nested-writes-implicit-transactions)
- [Sequential Transactions](#sequential-transactions)
- [Interactive Transactions](#interactive-transactions)
- [Isolation Levels](#isolation-levels)
- [Timeout Configuration](#timeout-configuration)
- [Batch Operations](#batch-operations)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Transaction Types Overview

| Type | Use Case | Syntax |
|------|----------|--------|
| **Nested writes** | Create/update related records atomically | Single `create`/`update` call with nested `data` |
| **Sequential** | Multiple independent queries that must all succeed | `$transaction([query1, query2])` |
| **Interactive** | Queries with conditional logic between them | `$transaction(async (tx) => { ... })` |
| **Batch** | Bulk create/update/delete of same model | `createMany`, `updateMany`, `deleteMany` |

## Nested Writes (Implicit Transactions)

Single operations that touch multiple models are automatically wrapped in a transaction:

```typescript
// This entire operation is atomic
const user = await prisma.user.create({
  data: {
    email: "alice@example.com",
    name: "Alice",
    profile: {
      create: { bio: "Hello world" },
    },
    posts: {
      create: [
        { title: "Post 1" },
        { title: "Post 2" },
      ],
    },
  },
  include: { profile: true, posts: true },
});
// If any part fails, nothing is created
```

Nested writes support: `create`, `createMany`, `connect`, `connectOrCreate`, `disconnect`, `set`, `update`, `upsert`, `delete`, `updateMany`, `deleteMany`.

## Sequential Transactions

Pass an array of Prisma queries — they execute sequentially and atomically:

```typescript
const [posts, totalPosts] = await prisma.$transaction([
  prisma.post.findMany({ where: { published: true }, take: 10 }),
  prisma.post.count({ where: { published: true } }),
]);
```

### Multiple Writes

```typescript
const [deletedComments, deletedPosts, deletedUser] =
  await prisma.$transaction([
    prisma.comment.deleteMany({ where: { authorId: userId } }),
    prisma.post.deleteMany({ where: { authorId: userId } }),
    prisma.user.delete({ where: { id: userId } }),
  ]);
```

**Key characteristics**:
- Queries execute in order (sequential, not parallel)
- If any query fails, all changes are rolled back
- Results are returned as a tuple matching the input array

## Interactive Transactions

Use when you need conditional logic, error handling, or read-modify-write patterns:

```typescript
const result = await prisma.$transaction(async (tx) => {
  // 1. Check balance
  const sender = await tx.account.update({
    data: { balance: { decrement: 100 } },
    where: { email: "alice@example.com" },
  });

  // 2. Validate
  if (sender.balance < 0) {
    throw new Error("Insufficient funds");
    // Entire transaction is rolled back
  }

  // 3. Credit recipient
  const recipient = await tx.account.update({
    data: { balance: { increment: 100 } },
    where: { email: "bob@example.com" },
  });

  return { sender, recipient };
});
```

### Important Rules

1. **Use `tx` not `prisma`** — Always use the transaction client (`tx`), not the regular `prisma` client
2. **Throw to rollback** — Any thrown error rolls back the entire transaction
3. **Return value** — The callback's return value becomes `$transaction`'s return value
4. **No `await` outside** — Don't pass promises created outside the callback

```typescript
// WRONG — uses prisma instead of tx
await prisma.$transaction(async (tx) => {
  await prisma.user.create({ data: { email: "test@test.com" } }); // NOT transactional!
});

// CORRECT — uses tx
await prisma.$transaction(async (tx) => {
  await tx.user.create({ data: { email: "test@test.com" } }); // transactional
});
```

## Isolation Levels

Control the transaction isolation level:

```typescript
import { Prisma } from "./generated/prisma/index.js";

// Sequential transactions
const [users, posts] = await prisma.$transaction(
  [prisma.user.findMany(), prisma.post.findMany()],
  {
    isolationLevel: Prisma.TransactionIsolationLevel.Serializable,
  }
);

// Interactive transactions
await prisma.$transaction(
  async (tx) => {
    // ...
  },
  {
    isolationLevel: Prisma.TransactionIsolationLevel.RepeatableRead,
  }
);
```

Available isolation levels:

| Level | Description |
|-------|-------------|
| `ReadUncommitted` | Lowest isolation; dirty reads possible |
| `ReadCommitted` | Default for PostgreSQL; no dirty reads |
| `RepeatableRead` | Default for MySQL; consistent reads within transaction |
| `Serializable` | Highest isolation; transactions appear sequential |
| `Snapshot` | SQL Server only; row versioning |

## Timeout Configuration

Interactive transactions have configurable timeouts:

```typescript
await prisma.$transaction(
  async (tx) => {
    // Long-running operations
    await tx.post.updateMany({ data: { published: true }, where: {} });
    await tx.user.updateMany({ data: { active: true }, where: {} });
  },
  {
    maxWait: 5000,   // Max time to wait for transaction slot (ms)
    timeout: 30000,  // Max execution time for transaction (ms)
  }
);
```

| Option | Default | Description |
|--------|---------|-------------|
| `maxWait` | 2000ms | Time to wait to acquire transaction from pool |
| `timeout` | 5000ms | Maximum duration of the transaction |

## Batch Operations

These automatically run as transactions:

```typescript
// createMany — atomic
const result = await prisma.user.createMany({
  data: users,
  skipDuplicates: true,
});

// updateMany — atomic
await prisma.post.updateMany({
  where: { authorId: deletedUserId },
  data: { authorId: null },
});

// deleteMany — atomic
await prisma.comment.deleteMany({
  where: { postId: { in: postIds } },
});
```

## Common Patterns

### Transfer Between Accounts

```typescript
async function transfer(fromId: number, toId: number, amount: number) {
  return prisma.$transaction(async (tx) => {
    const sender = await tx.account.update({
      where: { id: fromId },
      data: { balance: { decrement: amount } },
    });

    if (sender.balance < 0) {
      throw new Error(`Insufficient balance: ${sender.balance}`);
    }

    const recipient = await tx.account.update({
      where: { id: toId },
      data: { balance: { increment: amount } },
    });

    return { sender, recipient };
  });
}
```

### Cascade Delete with Validation

```typescript
async function deleteUserAndContent(userId: number) {
  return prisma.$transaction(async (tx) => {
    const user = await tx.user.findUniqueOrThrow({
      where: { id: userId },
      include: { _count: { select: { posts: true, comments: true } } },
    });

    await tx.comment.deleteMany({ where: { authorId: userId } });
    await tx.post.deleteMany({ where: { authorId: userId } });
    await tx.profile.deleteMany({ where: { userId } });
    await tx.user.delete({ where: { id: userId } });

    return { deletedUser: user.email, postsDeleted: user._count.posts };
  });
}
```

### Idempotent Operations

```typescript
async function ensureTeamMembership(userId: number, teamId: number) {
  return prisma.$transaction(async (tx) => {
    const existing = await tx.teamMember.findUnique({
      where: { userId_teamId: { userId, teamId } },
    });

    if (existing) return existing;

    return tx.teamMember.create({
      data: { userId, teamId, role: "MEMBER" },
    });
  });
}
```

### Paginated List with Consistent Count

```typescript
async function getPaginatedPosts(page: number, size: number) {
  const [posts, total] = await prisma.$transaction([
    prisma.post.findMany({
      where: { published: true },
      skip: (page - 1) * size,
      take: size,
      orderBy: { createdAt: "desc" },
    }),
    prisma.post.count({ where: { published: true } }),
  ]);

  return { posts, total, pages: Math.ceil(total / size) };
}
```

## Common Pitfalls

1. **Using `prisma` inside `$transaction`** — Always use the `tx` client parameter; queries on `prisma` bypass the transaction
2. **Long-running transactions** — Keep transactions short; long locks can cause timeouts and deadlocks
3. **Ignoring timeouts** — Default 5s timeout may be too short for data migrations; increase `timeout`
4. **Nesting transactions** — Prisma doesn't support nested `$transaction` calls
5. **Async work outside DB** — Don't do HTTP calls or file I/O inside transactions; they hold locks
