# Drizzle ORM — Mutations (INSERT, UPDATE, DELETE)

> Source: [orm.drizzle.team/docs/insert](https://orm.drizzle.team/docs/insert) | [update](https://orm.drizzle.team/docs/update) | [delete](https://orm.drizzle.team/docs/delete)

## Table of Contents

- [INSERT](#insert)
- [Batch Insert](#batch-insert)
- [Returning Clause](#returning-clause)
- [Upsert — ON CONFLICT](#upsert--on-conflict)
- [INSERT SELECT](#insert-select)
- [UPDATE](#update)
- [UPDATE FROM](#update-from)
- [DELETE](#delete)
- [DELETE with CTEs](#delete-with-ctes)
- [Type Inference for Mutations](#type-inference-for-mutations)
- [Common Pitfalls](#common-pitfalls)

---

## INSERT

```typescript
import { db } from './db';
import { users } from './schema';

// Single row
await db.insert(users).values({
  name: 'Alice',
  email: 'alice@example.com',
  age: 30,
});

// Columns with defaults can be omitted
await db.insert(users).values({
  name: 'Bob',
  email: 'bob@example.com',
  // age is nullable, createdAt has defaultNow()
});
```

## Batch Insert

```typescript
await db.insert(users).values([
  { name: 'Alice', email: 'alice@example.com' },
  { name: 'Bob', email: 'bob@example.com' },
  { name: 'Charlie', email: 'charlie@example.com' },
]);
```

## Returning Clause

### PostgreSQL / SQLite

```typescript
// Return all columns
const [inserted] = await db.insert(users)
  .values({ name: 'Alice', email: 'alice@example.com' })
  .returning();

// Return specific columns
const [{ id }] = await db.insert(users)
  .values({ name: 'Alice', email: 'alice@example.com' })
  .returning({ id: users.id });
```

### MySQL

MySQL doesn't support RETURNING. Use `$returningId()` for auto-increment IDs:

```typescript
const [{ id }] = await db.insert(users)
  .values({ name: 'Alice', email: 'alice@example.com' })
  .$returningId();
```

## Upsert — ON CONFLICT

### PostgreSQL / SQLite — onConflictDoNothing

```typescript
// Cancel insert on any unique constraint violation
await db.insert(users)
  .values({ id: 1, name: 'Alice', email: 'alice@example.com' })
  .onConflictDoNothing();

// Cancel on specific target
await db.insert(users)
  .values({ id: 1, name: 'Alice', email: 'alice@example.com' })
  .onConflictDoNothing({ target: users.email });
```

### PostgreSQL / SQLite — onConflictDoUpdate

```typescript
await db.insert(users)
  .values({ id: 1, name: 'Alice', email: 'alice@example.com' })
  .onConflictDoUpdate({
    target: users.email,
    set: { name: 'Alice Updated' },
  });

// Reference excluded values (the row that would have been inserted)
await db.insert(users)
  .values({ id: 1, name: 'Alice', email: 'alice@example.com' })
  .onConflictDoUpdate({
    target: users.email,
    set: { name: sql`excluded.name` },
  });

// Composite target
await db.insert(users)
  .values({ ... })
  .onConflictDoUpdate({
    target: [users.email, users.orgId],
    set: { name: 'Updated' },
  });

// Conditional update (WHERE on the update)
await db.insert(users)
  .values({ ... })
  .onConflictDoUpdate({
    target: users.email,
    set: { name: 'Updated' },
    setWhere: sql`${users.updatedAt} < now() - interval '1 day'`,
  });

// Partial index target
await db.insert(users)
  .values({ ... })
  .onConflictDoUpdate({
    target: users.email,
    targetWhere: sql`${users.isActive} = true`,
    set: { name: 'Updated' },
  });
```

### MySQL — onDuplicateKeyUpdate

```typescript
await db.insert(users)
  .values({ id: 1, name: 'Alice', email: 'alice@example.com' })
  .onDuplicateKeyUpdate({
    set: { name: 'Alice Updated' },
  });
```

## INSERT SELECT

```typescript
// Insert rows from a select query
await db.insert(archivedUsers).select(
  db.select().from(users).where(eq(users.isActive, false))
);

// With specific columns
await db.insert(employees).select(
  db.select({
    name: users.name,
    email: users.email,
  }).from(users).where(eq(users.role, 'employee'))
);
```

## UPDATE

```typescript
import { eq, sql } from 'drizzle-orm';

// Basic update
await db.update(users)
  .set({ name: 'Alice Smith' })
  .where(eq(users.id, 1));

// Multiple columns
await db.update(users)
  .set({
    name: 'Alice Smith',
    age: 31,
    updatedAt: new Date(),
  })
  .where(eq(users.id, 1));

// SQL expressions in set
await db.update(users)
  .set({
    age: sql`${users.age} + 1`,
    updatedAt: sql`now()`,
  })
  .where(eq(users.id, 1));

// Update with returning (PostgreSQL / SQLite)
const [updated] = await db.update(users)
  .set({ name: 'Alice Smith' })
  .where(eq(users.id, 1))
  .returning();

// Limit the number of updated rows
await db.update(users)
  .set({ verified: true })
  .limit(10);
```

### Undefined vs Null in SET

```typescript
await db.update(users).set({
  name: 'Alice',      // Updates name
  bio: null,           // Sets bio to NULL
  age: undefined,      // IGNORED — age is not updated
}).where(eq(users.id, 1));
```

## UPDATE FROM

Join other tables to determine update values:

```typescript
// PostgreSQL
await db.update(users)
  .set({ cityId: cities.id })
  .from(cities)
  .where(
    and(
      eq(cities.name, 'Seattle'),
      eq(users.name, 'John'),
    )
  );
// SQL: UPDATE users SET city_id = cities.id FROM cities WHERE cities.name = 'Seattle' AND users.name = 'John'
```

## DELETE

```typescript
// Delete specific rows
await db.delete(users).where(eq(users.id, 1));

// Delete with multiple conditions
await db.delete(users).where(
  and(
    eq(users.role, 'guest'),
    lt(users.createdAt, cutoffDate),
  )
);

// Delete all rows (careful!)
await db.delete(users);

// Delete with returning (PostgreSQL / SQLite)
const [deleted] = await db.delete(users)
  .where(eq(users.id, 1))
  .returning();

const deletedIds = await db.delete(users)
  .where(eq(users.role, 'banned'))
  .returning({ id: users.id });

// Delete with limit
await db.delete(users)
  .where(eq(users.role, 'guest'))
  .limit(100);
```

## DELETE with CTEs

```typescript
const avgAmount = db.$with('avg_amount').as(
  db.select({ value: sql`avg(${orders.amount})`.as('value') }).from(orders)
);

const deleted = await db.with(avgAmount)
  .delete(orders)
  .where(gt(orders.amount, sql`(select value from ${avgAmount})`))
  .returning({ id: orders.id });
```

## Type Inference for Mutations

```typescript
// Insert type (columns with defaults are optional)
type NewUser = typeof users.$inferInsert;
// { id?: number; name: string; email: string; age?: number | null; createdAt?: Date }

// Use for type-safe function parameters
async function createUser(data: typeof users.$inferInsert) {
  return db.insert(users).values(data).returning();
}

async function updateUser(id: number, data: Partial<typeof users.$inferInsert>) {
  return db.update(users).set(data).where(eq(users.id, id)).returning();
}
```

## Common Pitfalls

1. **`returning()` is not available on MySQL** — Use `$returningId()` for auto-increment IDs or query after insert.

2. **`undefined` values are silently ignored in `set()`** — This is by design but can be surprising. Use `null` to explicitly clear a field.

3. **`onConflictDoUpdate` requires a target** — You must specify which unique constraint/index to match against.

4. **Delete without WHERE deletes everything** — `db.delete(table)` with no `.where()` deletes all rows. Always double-check.

5. **Batch insert type consistency** — All objects in the values array must have the same shape. TypeScript enforces this at compile time.

---

**Related:** [Select Queries](./04-select-queries.md) | [Transactions](./08-transactions.md)
