# Drizzle ORM — Select Queries

> Source: [orm.drizzle.team/docs/select](https://orm.drizzle.team/docs/select)

## Table of Contents

- [Basic Select](#basic-select)
- [Partial Select](#partial-select)
- [Filtering with WHERE](#filtering-with-where)
- [Filter Operators](#filter-operators)
- [Combining Conditions](#combining-conditions)
- [Ordering](#ordering)
- [Pagination](#pagination)
- [Distinct](#distinct)
- [Aggregations](#aggregations)
- [Group By & Having](#group-by--having)
- [Subqueries](#subqueries)
- [Common Table Expressions (CTEs)](#common-table-expressions-ctes)
- [Dynamic Queries](#dynamic-queries)
- [Common Pitfalls](#common-pitfalls)

---

## Basic Select

```typescript
import { db } from './db';
import { users } from './schema';

// Select all columns, all rows
const allUsers = await db.select().from(users);
// Type: { id: number; name: string; email: string; age: number | null }[]
```

## Partial Select

```typescript
const result = await db.select({
  id: users.id,
  name: users.name,
}).from(users);
// Type: { id: number; name: string }[]
```

With computed fields:

```typescript
import { sql } from 'drizzle-orm';

const result = await db.select({
  id: users.id,
  lowerName: sql<string>`lower(${users.name})`,
  nameLength: sql<number>`length(${users.name})`,
}).from(users);
```

## Filtering with WHERE

```typescript
import { eq, ne, gt, gte, lt, lte } from 'drizzle-orm';

// Equality
await db.select().from(users).where(eq(users.id, 42));

// Not equal
await db.select().from(users).where(ne(users.role, 'admin'));

// Comparison
await db.select().from(users).where(gt(users.age, 18));
await db.select().from(users).where(gte(users.age, 18));
await db.select().from(users).where(lt(users.age, 65));
await db.select().from(users).where(lte(users.age, 65));
```

## Filter Operators

```typescript
import {
  eq, ne, gt, gte, lt, lte,
  isNull, isNotNull,
  inArray, notInArray,
  between, notBetween,
  like, ilike, notLike, notIlike,
  exists, notExists,
  arrayContains, arrayContained, arrayOverlaps,
} from 'drizzle-orm';

// NULL checks
await db.select().from(users).where(isNull(users.deletedAt));
await db.select().from(users).where(isNotNull(users.email));

// IN / NOT IN
await db.select().from(users).where(inArray(users.id, [1, 2, 3]));
await db.select().from(users).where(notInArray(users.role, ['banned', 'suspended']));

// BETWEEN
await db.select().from(users).where(between(users.age, 18, 65));

// LIKE / ILIKE (case-insensitive, PostgreSQL)
await db.select().from(users).where(like(users.name, '%Alice%'));
await db.select().from(users).where(ilike(users.email, '%@gmail.com'));

// EXISTS (subquery)
await db.select().from(users).where(
  exists(db.select().from(posts).where(eq(posts.authorId, users.id)))
);

// PostgreSQL array operators
await db.select().from(posts).where(arrayContains(posts.tags, ['typescript']));
await db.select().from(posts).where(arrayOverlaps(posts.tags, ['js', 'ts']));
```

## Combining Conditions

```typescript
import { and, or, not } from 'drizzle-orm';

// AND
await db.select().from(users).where(
  and(
    eq(users.role, 'admin'),
    gt(users.age, 18),
  )
);

// OR
await db.select().from(users).where(
  or(
    eq(users.role, 'admin'),
    eq(users.role, 'moderator'),
  )
);

// NOT
await db.select().from(users).where(
  not(eq(users.role, 'banned'))
);

// Nested
await db.select().from(users).where(
  and(
    gt(users.age, 18),
    or(
      eq(users.role, 'admin'),
      eq(users.role, 'moderator'),
    ),
  )
);
```

## Ordering

```typescript
import { asc, desc } from 'drizzle-orm';

// Single column
await db.select().from(users).orderBy(asc(users.name));
await db.select().from(users).orderBy(desc(users.createdAt));

// Multiple columns
await db.select().from(users).orderBy(
  desc(users.role),
  asc(users.name),
);

// SQL expression
await db.select().from(users).orderBy(sql`${users.name} COLLATE "en_US"`);
```

## Pagination

```typescript
// Offset pagination
await db.select().from(users)
  .orderBy(asc(users.id))
  .limit(10)
  .offset(20);  // Page 3 (0-indexed)

// Cursor-based pagination (better performance)
await db.select().from(users)
  .where(gt(users.id, lastSeenId))
  .orderBy(asc(users.id))
  .limit(10);
```

## Distinct

```typescript
// DISTINCT
await db.selectDistinct().from(users);

// DISTINCT ON (PostgreSQL)
await db.selectDistinctOn([users.role]).from(users)
  .orderBy(users.role, desc(users.createdAt));
```

## Aggregations

```typescript
import { count, countDistinct, avg, sum, max, min } from 'drizzle-orm';

// Count all rows
const [{ total }] = await db.select({
  total: count(),
}).from(users);

// Count distinct
const [{ uniqueRoles }] = await db.select({
  uniqueRoles: countDistinct(users.role),
}).from(users);

// Average
const [{ avgAge }] = await db.select({
  avgAge: avg(users.age),
}).from(users);

// Sum, Max, Min
const [{ totalRevenue }] = await db.select({
  totalRevenue: sum(orders.amount),
}).from(orders);

const [{ highestPrice }] = await db.select({
  highestPrice: max(products.price),
}).from(products);
```

## Group By & Having

```typescript
// Group by with aggregation
const roleStats = await db.select({
  role: users.role,
  count: count(),
  avgAge: avg(users.age),
}).from(users)
  .groupBy(users.role);

// HAVING clause
const popularRoles = await db.select({
  role: users.role,
  count: count(),
}).from(users)
  .groupBy(users.role)
  .having(({ count }) => gt(count, 5));
```

## Subqueries

```typescript
// Subquery in FROM
const sq = db.select({
  authorId: posts.authorId,
  postCount: count().as('post_count'),
}).from(posts)
  .groupBy(posts.authorId)
  .as('sq');

const result = await db.select({
  name: users.name,
  postCount: sq.postCount,
}).from(users)
  .leftJoin(sq, eq(users.id, sq.authorId));

// Subquery in WHERE
const activeAuthors = await db.select().from(users).where(
  inArray(
    users.id,
    db.select({ id: posts.authorId }).from(posts),
  )
);
```

## Common Table Expressions (CTEs)

```typescript
const activePosts = db.$with('active_posts').as(
  db.select().from(posts).where(eq(posts.status, 'published'))
);

const result = await db.with(activePosts)
  .select({
    authorId: activePosts.authorId,
    postCount: count(),
  })
  .from(activePosts)
  .groupBy(activePosts.authorId);
```

## Dynamic Queries

Build queries conditionally:

```typescript
function getUsers(filters: { role?: string; minAge?: number; search?: string }) {
  const query = db.select().from(users).$dynamic();

  const conditions: SQL[] = [];

  if (filters.role) {
    conditions.push(eq(users.role, filters.role));
  }
  if (filters.minAge) {
    conditions.push(gte(users.age, filters.minAge));
  }
  if (filters.search) {
    conditions.push(ilike(users.name, `%${filters.search}%`));
  }

  if (conditions.length > 0) {
    query.where(and(...conditions));
  }

  return query;
}
```

## Common Pitfalls

1. **All filter values are parameterized** — Drizzle auto-parameterizes values in operators, preventing SQL injection. Never use string concatenation.

2. **`sql<T>` needs explicit type** — When using raw `sql` template, provide the TypeScript return type as a generic: `sql<number>`.

3. **Aggregation returns strings** — Functions like `avg()` and `sum()` may return strings. Cast explicitly: `sql<number>\`cast(count(*) as int)\``.

4. **`$dynamic()` for conditional queries** — Always call `.$dynamic()` before conditionally chaining methods, otherwise TypeScript types won't narrow correctly.

5. **Offset pagination scales poorly** — For large datasets, prefer cursor-based pagination with `where(gt(id, lastId))` over `offset()`.

---

**Related:** [Joins](./06-joins.md) | [Relational Queries](./07-relational-queries.md)
