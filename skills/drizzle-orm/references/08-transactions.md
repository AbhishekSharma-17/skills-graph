# Drizzle ORM — Transactions

> Source: [orm.drizzle.team/docs/transactions](https://orm.drizzle.team/docs/transactions)

## Table of Contents

- [Overview](#overview)
- [Basic Transactions](#basic-transactions)
- [Returning Values](#returning-values)
- [Rollback](#rollback)
- [Nested Transactions / Savepoints](#nested-transactions--savepoints)
- [Isolation Levels](#isolation-levels)
- [Transactions with Relational Queries](#transactions-with-relational-queries)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Drizzle transactions ensure a group of database operations either all succeed (commit) or all fail (rollback) as a single atomic unit. The API is consistent across all supported databases.

## Basic Transactions

```typescript
await db.transaction(async (tx) => {
  await tx.insert(accounts).values({ id: 1, balance: 100 });
  await tx.insert(accounts).values({ id: 2, balance: 200 });
});
```

The callback receives a transaction object (`tx`) that has the same API as `db` — use `tx` instead of `db` for all operations inside the transaction.

## Returning Values

Transactions can return computed values:

```typescript
const result = await db.transaction(async (tx) => {
  const [sender] = await tx.select()
    .from(accounts)
    .where(eq(accounts.id, senderId));

  const [receiver] = await tx.select()
    .from(accounts)
    .where(eq(accounts.id, receiverId));

  const newSenderBalance = sender.balance - amount;
  const newReceiverBalance = receiver.balance + amount;

  await tx.update(accounts)
    .set({ balance: newSenderBalance })
    .where(eq(accounts.id, senderId));

  await tx.update(accounts)
    .set({ balance: newReceiverBalance })
    .where(eq(accounts.id, receiverId));

  return { newSenderBalance, newReceiverBalance };
});

console.log(result.newSenderBalance);
```

## Rollback

Manually abort a transaction when business logic fails:

```typescript
await db.transaction(async (tx) => {
  const [account] = await tx.select()
    .from(accounts)
    .where(eq(accounts.id, 1));

  if (account.balance < amount) {
    tx.rollback();
    // Everything above is undone, execution stops here
    // tx.rollback() throws an error, so code below never runs
  }

  await tx.update(accounts)
    .set({ balance: account.balance - amount })
    .where(eq(accounts.id, 1));
});
```

Note: `tx.rollback()` throws a `DrizzleError` which is caught by the transaction wrapper. The transaction resolves as rejected.

## Nested Transactions / Savepoints

Nested `tx.transaction()` calls create database savepoints:

```typescript
await db.transaction(async (tx) => {
  await tx.insert(users).values({ name: 'Alice' });

  // Creates a savepoint
  await tx.transaction(async (tx2) => {
    await tx2.insert(posts).values({ title: 'Hello', authorId: 1 });
    // If this throws, only the savepoint is rolled back
    // The outer transaction and Alice insert remain intact
  });

  await tx.insert(users).values({ name: 'Bob' });
});
```

Savepoint rollback:

```typescript
await db.transaction(async (tx) => {
  await tx.insert(users).values({ name: 'Alice' });

  try {
    await tx.transaction(async (tx2) => {
      await tx2.insert(posts).values({ title: 'Bad post' });
      throw new Error('Oops');
      // Savepoint rolls back — 'Bad post' is undone
    });
  } catch (e) {
    // Alice insert is still valid
  }

  await tx.insert(users).values({ name: 'Bob' });
  // Final result: Alice and Bob inserted, no posts
});
```

## Isolation Levels

### PostgreSQL

```typescript
await db.transaction(async (tx) => {
  // ...
}, {
  isolationLevel: 'read committed',   // default
  // Options: 'read uncommitted' | 'read committed' | 'repeatable read' | 'serializable'
  accessMode: 'read write',           // default
  // Options: 'read write' | 'read only'
});
```

### MySQL

```typescript
await db.transaction(async (tx) => {
  // ...
}, {
  isolationLevel: 'read committed',
  // Options: 'read uncommitted' | 'read committed' | 'repeatable read' | 'serializable'
  // MySQL also supports: 'consistent snapshot' with 'with consistent snapshot'
  accessMode: 'read write',
});
```

### SQLite

```typescript
await db.transaction(async (tx) => {
  // ...
}, {
  behavior: 'deferred',  // default
  // Options: 'deferred' | 'immediate' | 'exclusive'
});
```

## Transactions with Relational Queries

The relational query API works inside transactions:

```typescript
await db.transaction(async (tx) => {
  const user = await tx.query.users.findFirst({
    where: eq(users.id, 1),
    with: { posts: true },
  });

  if (user) {
    await tx.update(users)
      .set({ lastLogin: new Date() })
      .where(eq(users.id, user.id));
  }
});
```

## Common Patterns

### Transfer funds

```typescript
async function transfer(fromId: number, toId: number, amount: number) {
  return db.transaction(async (tx) => {
    const [from] = await tx
      .select()
      .from(accounts)
      .where(eq(accounts.id, fromId))
      .for('update');  // PostgreSQL: SELECT FOR UPDATE (row lock)

    if (from.balance < amount) {
      tx.rollback();
    }

    await tx.update(accounts)
      .set({ balance: sql`${accounts.balance} - ${amount}` })
      .where(eq(accounts.id, fromId));

    await tx.update(accounts)
      .set({ balance: sql`${accounts.balance} + ${amount}` })
      .where(eq(accounts.id, toId));

    return { success: true };
  });
}
```

### Idempotent insert

```typescript
async function ensureUser(email: string, name: string) {
  return db.transaction(async (tx) => {
    const existing = await tx.query.users.findFirst({
      where: eq(users.email, email),
    });

    if (existing) return existing;

    const [created] = await tx.insert(users)
      .values({ email, name })
      .returning();

    return created;
  });
}
```

### Batch with rollback on any failure

```typescript
async function createOrder(items: OrderItem[]) {
  return db.transaction(async (tx) => {
    const [order] = await tx.insert(orders)
      .values({ status: 'pending' })
      .returning();

    for (const item of items) {
      const [product] = await tx.select()
        .from(products)
        .where(eq(products.id, item.productId));

      if (product.stock < item.quantity) {
        tx.rollback();  // Rolls back order + all previous items
      }

      await tx.update(products)
        .set({ stock: sql`${products.stock} - ${item.quantity}` })
        .where(eq(products.id, item.productId));

      await tx.insert(orderItems)
        .values({ orderId: order.id, ...item });
    }

    return order;
  });
}
```

## Common Pitfalls

1. **Always use `tx` inside transaction** — Using `db` instead of `tx` inside a transaction callback runs queries outside the transaction boundary.

2. **`tx.rollback()` throws** — It throws an error to stop execution. Don't put code after `tx.rollback()` expecting it to run.

3. **Connection pool exhaustion** — Long-running transactions hold connections. Keep transactions short and focused.

4. **Isolation level defaults** — PostgreSQL and MySQL default to 'read committed'. Use 'serializable' only when you need strict consistency, as it can cause retries.

5. **SQLite locking** — SQLite uses file-level locking. Use `behavior: 'immediate'` for write transactions to avoid SQLITE_BUSY errors.

---

**Related:** [Mutations](./05-mutations.md) | [Performance](./10-performance.md)
