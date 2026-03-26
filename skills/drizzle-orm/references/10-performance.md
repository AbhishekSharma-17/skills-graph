# Drizzle ORM — Performance

> Source: [orm.drizzle.team/docs/perf-queries](https://orm.drizzle.team/docs/perf-queries) | [read-replicas](https://orm.drizzle.team/docs/read-replicas)

## Table of Contents

- [Overview](#overview)
- [Prepared Statements](#prepared-statements)
- [Placeholders](#placeholders)
- [Read Replicas](#read-replicas)
- [Custom Replica Selection](#custom-replica-selection)
- [Query Optimization Tips](#query-optimization-tips)
- [Logging & Debugging](#logging--debugging)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Drizzle is designed for minimal overhead. The ORM layer is a thin TypeScript abstraction (~31KB, zero dependencies) that adds near-zero runtime cost. Key performance features:

- Prepared statements for query caching
- Read replica routing for scaling reads
- Single SQL query per relational query (no N+1)
- Parameterized queries by default (safe + efficient)

## Prepared Statements

Prepared statements pre-compile SQL once and reuse the binary plan across executions, eliminating repeated parsing overhead.

### PostgreSQL

```typescript
// Prepare with a name
const getUsers = db.select().from(users).prepare('get_all_users');

// Execute multiple times — SQL is parsed only once
const result1 = await getUsers.execute();
const result2 = await getUsers.execute();
```

### MySQL

```typescript
const getUsers = db.select().from(users).prepare();

const result1 = await getUsers.execute();
const result2 = await getUsers.execute();
```

### SQLite

```typescript
const getUsers = db.select().from(users).prepare();

const result1 = getUsers.all();
const result2 = getUsers.all();
```

### Prepared with relational queries

```typescript
const getUserWithPosts = db.query.users.findFirst({
  where: (users, { eq }) => eq(users.id, placeholder('id')),
  with: { posts: true },
}).prepare('get_user_with_posts');

const user = await getUserWithPosts.execute({ id: 1 });
```

## Placeholders

Use `sql.placeholder()` to create parameterized prepared statements with dynamic values:

```typescript
import { sql, placeholder } from 'drizzle-orm';

// Named placeholders
const getUserById = db.select()
  .from(users)
  .where(eq(users.id, sql.placeholder('id')))
  .prepare('get_user_by_id');

await getUserById.execute({ id: 10 });
await getUserById.execute({ id: 25 });

// Multiple placeholders
const getUsersByRoleAndAge = db.select()
  .from(users)
  .where(and(
    eq(users.role, sql.placeholder('role')),
    gte(users.age, sql.placeholder('minAge')),
  ))
  .prepare('get_users_by_role_age');

await getUsersByRoleAndAge.execute({ role: 'admin', minAge: 18 });
```

### Placeholders with insert

```typescript
const insertUser = db.insert(users)
  .values({
    name: sql.placeholder('name'),
    email: sql.placeholder('email'),
  })
  .prepare('insert_user');

await insertUser.execute({ name: 'Alice', email: 'alice@example.com' });
```

## Read Replicas

Route SELECT queries to read replicas while directing writes to the primary:

```typescript
import { drizzle } from 'drizzle-orm/postgres-js';
import { withReplicas } from 'drizzle-orm/pg-core';

const primaryDb = drizzle('postgres://primary-host/db');
const replica1 = drizzle('postgres://replica1-host/db');
const replica2 = drizzle('postgres://replica2-host/db');

const db = withReplicas(primaryDb, [replica1, replica2]);

// Automatically routed to a random replica
await db.select().from(users);

// Automatically routed to primary
await db.insert(users).values({ name: 'Alice' });
await db.update(users).set({ name: 'Bob' }).where(eq(users.id, 1));
await db.delete(users).where(eq(users.id, 1));
```

### Force primary for reads

When you need read-after-write consistency:

```typescript
// Force read from primary
const freshUser = await db.$primary.select().from(users).where(eq(users.id, 1));
```

### Replicas with relational queries

```typescript
// Routes to replica
await db.query.users.findMany();

// Force primary
await db.$primary.query.users.findMany();
```

## Custom Replica Selection

Implement weighted routing or custom logic:

```typescript
const db = withReplicas(primaryDb, [replica1, replica2], (replicas) => {
  // Weighted: 70% to replica1, 30% to replica2
  const weights = [0.7, 0.3];
  let cumulative = 0;
  const rand = Math.random();

  for (const [i, replica] of replicas.entries()) {
    cumulative += weights[i]!;
    if (rand < cumulative) return replica;
  }
  return replicas[0]!;
});
```

### Round-robin selection

```typescript
let counter = 0;
const db = withReplicas(primaryDb, replicas, (replicas) => {
  const replica = replicas[counter % replicas.length]!;
  counter++;
  return replica;
});
```

## Query Optimization Tips

### 1. Select only needed columns

```typescript
// Bad: selects all columns
await db.select().from(users);

// Good: select only what you need
await db.select({ id: users.id, name: users.name }).from(users);
```

### 2. Use indexes effectively

```typescript
// Ensure your WHERE columns are indexed
await db.select().from(users).where(eq(users.email, 'alice@example.com'));
// → Create index: index('email_idx').on(users.email)
```

### 3. Cursor pagination over offset

```typescript
// Bad: offset pagination degrades with large offsets
await db.select().from(users).offset(10000).limit(10);

// Good: cursor-based pagination
await db.select().from(users)
  .where(gt(users.id, lastId))
  .orderBy(asc(users.id))
  .limit(10);
```

### 4. Use relational queries for nested data

```typescript
// Bad: N+1 queries
const users = await db.select().from(usersTable);
for (const user of users) {
  const posts = await db.select().from(postsTable)
    .where(eq(postsTable.authorId, user.id));
}

// Good: single query with relations
const users = await db.query.users.findMany({
  with: { posts: true },
});
```

### 5. Batch inserts

```typescript
// Bad: individual inserts
for (const user of newUsers) {
  await db.insert(users).values(user);
}

// Good: batch insert
await db.insert(users).values(newUsers);
```

## Logging & Debugging

### Enable query logging

```typescript
const db = drizzle(connectionString, {
  logger: true,  // Logs all SQL to console
});
```

### Custom logger

```typescript
import { DefaultLogger, LogWriter } from 'drizzle-orm';

class CustomLogWriter implements LogWriter {
  write(message: string) {
    // Send to your logging service
    myLogger.debug(message);
  }
}

const db = drizzle(connectionString, {
  logger: new DefaultLogger({ writer: new CustomLogWriter() }),
});
```

### Get SQL without executing

```typescript
const query = db.select().from(users).where(eq(users.id, 1));
const { sql: sqlString, params } = query.toSQL();
console.log(sqlString);  // SELECT * FROM users WHERE id = $1
console.log(params);     // [1]
```

## Common Pitfalls

1. **Prepared statement names must be unique** — In PostgreSQL, each prepared statement needs a unique name string. Reusing names causes errors.

2. **Read replicas have replication lag** — Don't read from replicas immediately after writing. Use `db.$primary` when consistency matters.

3. **Over-fetching with `select()`** — Selecting all columns when you need only a few wastes bandwidth and memory.

4. **Not using prepared statements for hot paths** — Queries executed thousands of times per second benefit significantly from preparation.

5. **Logging in production** — Don't enable `logger: true` in production. It logs all SQL including potentially sensitive values. Use a filtered custom logger.

---

**Related:** [Select Queries](./04-select-queries.md) | [Transactions](./08-transactions.md)
