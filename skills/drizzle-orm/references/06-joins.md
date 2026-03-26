# Drizzle ORM — Joins

> Source: [orm.drizzle.team/docs/joins](https://orm.drizzle.team/docs/joins)

## Table of Contents

- [Overview](#overview)
- [Inner Join](#inner-join)
- [Left Join](#left-join)
- [Right Join](#right-join)
- [Full Join](#full-join)
- [Cross Join](#cross-join)
- [Lateral Joins](#lateral-joins)
- [Multiple Joins](#multiple-joins)
- [Self Joins with Aliases](#self-joins-with-aliases)
- [Partial Select with Joins](#partial-select-with-joins)
- [Join Conditions](#join-conditions)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Drizzle provides type-safe join methods on the SQL-like query builder. The return type automatically reflects nullability based on the join type:
- **Inner join** — All columns are non-nullable
- **Left join** — Right table columns become nullable
- **Right join** — Left table columns become nullable
- **Full join** — All columns become nullable

## Inner Join

Returns only rows that have matching values in both tables.

```typescript
const result = await db.select()
  .from(users)
  .innerJoin(posts, eq(users.id, posts.authorId));

// Type: { users: User; posts: Post }[]
// Both sides guaranteed non-null
```

## Left Join

Returns all rows from the left table, with matching right table rows or nulls.

```typescript
const result = await db.select()
  .from(users)
  .leftJoin(posts, eq(users.id, posts.authorId));

// Type: { users: User; posts: Post | null }[]
// posts columns are nullable
```

## Right Join

Returns all rows from the right table, with matching left table rows or nulls.

```typescript
const result = await db.select()
  .from(users)
  .rightJoin(posts, eq(users.id, posts.authorId));

// Type: { users: User | null; posts: Post }[]
// users columns are nullable
```

## Full Join

Returns all rows from both tables, with nulls where there's no match.

```typescript
const result = await db.select()
  .from(users)
  .fullJoin(posts, eq(users.id, posts.authorId));

// Type: { users: User | null; posts: Post | null }[]
// Both sides nullable
```

## Cross Join

Cartesian product — every row from left paired with every row from right.

```typescript
const result = await db.select()
  .from(colors)
  .crossJoin(sizes);

// Type: { colors: Color; sizes: Size }[]
// No join condition needed
```

## Lateral Joins

Lateral joins allow the subquery to reference columns from the outer query (correlated subqueries in FROM).

```typescript
// Left join lateral
const latestPost = db.select({
  id: posts.id,
  title: posts.title,
}).from(posts)
  .where(eq(posts.authorId, users.id))
  .orderBy(desc(posts.createdAt))
  .limit(1)
  .as('latest_post');

const result = await db.select()
  .from(users)
  .leftJoinLateral(latestPost, sql`true`);

// Inner join lateral
const result2 = await db.select()
  .from(users)
  .innerJoinLateral(latestPost, sql`true`);

// Cross join lateral
const result3 = await db.select()
  .from(users)
  .crossJoinLateral(latestPost);
```

## Multiple Joins

Chain multiple joins:

```typescript
const result = await db.select({
  userName: users.name,
  postTitle: posts.title,
  commentBody: comments.body,
}).from(users)
  .innerJoin(posts, eq(users.id, posts.authorId))
  .leftJoin(comments, eq(posts.id, comments.postId));
```

## Self Joins with Aliases

Use `alias()` for joining a table to itself:

```typescript
import { alias } from 'drizzle-orm';

const managers = alias(users, 'managers');

const result = await db.select({
  employeeName: users.name,
  managerName: managers.name,
}).from(users)
  .leftJoin(managers, eq(users.managerId, managers.id));
```

### Hierarchical queries:

```typescript
const parent = alias(categories, 'parent');

const result = await db.select({
  categoryName: categories.name,
  parentName: parent.name,
}).from(categories)
  .leftJoin(parent, eq(categories.parentId, parent.id));
```

## Partial Select with Joins

Flatten results instead of nested objects:

```typescript
// Default: nested objects
const nested = await db.select().from(users)
  .leftJoin(posts, eq(users.id, posts.authorId));
// { users: { id, name }, posts: { id, title } | null }

// Flattened: explicit column selection
const flat = await db.select({
  userId: users.id,
  userName: users.name,
  postId: posts.id,
  postTitle: posts.title,
}).from(users)
  .leftJoin(posts, eq(users.id, posts.authorId));
// { userId: number; userName: string; postId: number | null; postTitle: string | null }
```

## Join Conditions

### Complex conditions

```typescript
await db.select().from(users)
  .leftJoin(posts, and(
    eq(users.id, posts.authorId),
    eq(posts.status, 'published'),
  ));
```

### Using SQL expressions

```typescript
await db.select().from(users)
  .leftJoin(posts, sql`${users.id} = ${posts.authorId} AND ${posts.created_at} > now() - interval '7 days'`);
```

### Joining on multiple columns

```typescript
await db.select().from(orders)
  .innerJoin(products, and(
    eq(orders.productId, products.id),
    eq(orders.storeId, products.storeId),
  ));
```

## Common Pitfalls

1. **Null types with left/right/full joins** — Drizzle correctly makes columns nullable based on join type. Check for nulls when accessing right-table columns in a left join.

2. **Cross joins produce large result sets** — A cross join of N x M rows produces N*M results. Use only when you intentionally need a Cartesian product.

3. **Lateral joins require PostgreSQL** — Lateral joins are PostgreSQL-only. MySQL and SQLite don't support them.

4. **Alias names must be unique** — Each alias needs a unique string identifier. Using the same alias name twice causes a runtime error.

5. **Join vs relation query API** — Joins are for the SQL-like API. For nested data fetching, consider the relational query API (`db.query.*`) which is often simpler for common patterns.

---

**Related:** [Select Queries](./04-select-queries.md) | [Relational Queries](./07-relational-queries.md)
