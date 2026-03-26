# Drizzle ORM — Relational Queries API

> Source: [orm.drizzle.team/docs/rqb](https://orm.drizzle.team/docs/rqb)

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [findMany](#findmany)
- [findFirst](#findfirst)
- [Nested Relations with `with`](#nested-relations-with-with)
- [Column Selection](#column-selection)
- [Filtering](#filtering)
- [Ordering](#ordering)
- [Pagination](#pagination)
- [Extras — Computed Fields](#extras--computed-fields)
- [Prepared Statements](#prepared-statements)
- [PlanetScale Mode](#planetscale-mode)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

The Relational Queries API provides a typed, object-based way to fetch nested data. Unlike the SQL-like API which requires manual joins, relational queries use declared relations to automatically generate efficient SQL (one query per request, not N+1).

Two main methods: `findMany()` and `findFirst()`.

## Setup

Relations must be declared and the schema must be passed to the `drizzle()` constructor:

```typescript
import { drizzle } from 'drizzle-orm/postgres-js';
import * as schema from './schema';

const db = drizzle(connectionString, { schema });

// Now db.query.* is available
await db.query.users.findMany();
```

The `schema` object must include both tables AND relations exports.

## findMany

Retrieves multiple records:

```typescript
// All users
const users = await db.query.users.findMany();

// With options
const users = await db.query.users.findMany({
  columns: { id: true, name: true },
  with: { posts: true },
  where: (users, { eq }) => eq(users.role, 'admin'),
  orderBy: (users, { desc }) => [desc(users.createdAt)],
  limit: 10,
  offset: 0,
});
```

## findFirst

Returns a single record (adds `LIMIT 1`):

```typescript
const user = await db.query.users.findFirst({
  where: (users, { eq }) => eq(users.id, 1),
  with: { posts: true },
});
// Type: User & { posts: Post[] } | undefined
```

## Nested Relations with `with`

### Basic nesting

```typescript
const usersWithPosts = await db.query.users.findMany({
  with: {
    posts: true,  // Include all post columns
  },
});
```

### Deep nesting

```typescript
const usersWithPostsAndComments = await db.query.users.findMany({
  with: {
    posts: {
      with: {
        comments: true,
      },
    },
  },
});
```

### Filtered nested data

```typescript
const users = await db.query.users.findMany({
  with: {
    posts: {
      where: (posts, { eq }) => eq(posts.status, 'published'),
      orderBy: (posts, { desc }) => [desc(posts.createdAt)],
      limit: 5,
      columns: { id: true, title: true },
    },
  },
});
```

### Many-to-many through junction

```typescript
const usersWithGroups = await db.query.users.findMany({
  with: {
    usersToGroups: {
      with: {
        group: true,
      },
    },
  },
});
// Access: user.usersToGroups[0].group.name
```

## Column Selection

### Include specific columns

```typescript
const users = await db.query.users.findMany({
  columns: {
    id: true,
    name: true,
    // email excluded
  },
});
```

### Exclude specific columns

```typescript
const users = await db.query.users.findMany({
  columns: {
    password: false,  // Exclude password
  },
});
```

### Column selection on nested relations

```typescript
const users = await db.query.users.findMany({
  columns: { id: true, name: true },
  with: {
    posts: {
      columns: { id: true, title: true },
    },
  },
});
```

## Filtering

### Callback syntax (recommended)

```typescript
const admins = await db.query.users.findMany({
  where: (users, { eq, and, gt }) => and(
    eq(users.role, 'admin'),
    gt(users.age, 18),
  ),
});
```

### Operator import syntax

```typescript
import { eq } from 'drizzle-orm';

const admins = await db.query.users.findMany({
  where: eq(users.role, 'admin'),
});
```

All standard operators work: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `ilike`, `inArray`, `isNull`, `and`, `or`, `not`, `between`, `exists`.

## Ordering

```typescript
// Single column
const users = await db.query.users.findMany({
  orderBy: (users, { asc }) => [asc(users.name)],
});

// Multiple columns
const users = await db.query.users.findMany({
  orderBy: (users, { asc, desc }) => [
    desc(users.role),
    asc(users.name),
  ],
});

// Direct import style
import { desc } from 'drizzle-orm';
const users = await db.query.users.findMany({
  orderBy: [desc(users.createdAt)],
});
```

## Pagination

```typescript
const page3 = await db.query.users.findMany({
  limit: 10,
  offset: 20,
  orderBy: (users, { asc }) => [asc(users.id)],
});
```

Note: `offset` is only supported at the top level, not on nested relations.

## Extras — Computed Fields

Add computed SQL expressions to query results:

```typescript
import { sql } from 'drizzle-orm';

const users = await db.query.users.findMany({
  extras: {
    fullName: sql<string>`concat(${users.firstName}, ' ', ${users.lastName})`.as('full_name'),
    postCount: sql<number>`(
      SELECT count(*) FROM posts WHERE posts.author_id = ${users.id}
    )`.as('post_count'),
  },
});
// Type: { id, firstName, lastName, fullName: string, postCount: number }[]
```

### Extras on nested relations

```typescript
const users = await db.query.users.findMany({
  with: {
    posts: {
      extras: {
        commentCount: sql<number>`(
          SELECT count(*) FROM comments WHERE comments.post_id = ${posts.id}
        )`.as('comment_count'),
      },
    },
  },
});
```

## Prepared Statements

Cache and reuse query plans for better performance:

```typescript
import { placeholder } from 'drizzle-orm';

const getUserById = db.query.users.findFirst({
  where: (users, { eq }) => eq(users.id, placeholder('id')),
  with: { posts: true },
}).prepare('get_user_by_id');

// Execute multiple times with different params
const user1 = await getUserById.execute({ id: 1 });
const user2 = await getUserById.execute({ id: 2 });
```

## PlanetScale Mode

PlanetScale doesn't support lateral joins. Set the mode:

```typescript
import { drizzle } from 'drizzle-orm/planetscale-serverless';

const db = drizzle(connection, {
  schema,
  mode: 'planetscale',
});
```

For regular MySQL connections, use `mode: 'default'` (or omit it).

## Common Pitfalls

1. **Schema must include relations** — `db.query.*` requires both table AND relations exports in the schema object passed to `drizzle()`.

2. **`offset` only works at the top level** — You can't paginate nested relations with offset. Use `limit` on nested queries instead.

3. **Extras need `.as()` alias** — Every SQL expression in `extras` must have an `.as('name')` alias.

4. **Callback vs direct syntax** — The callback style `(table, operators) => ...` is preferred because it provides operator autocompletion and avoids import issues.

5. **Single SQL query guarantee** — Drizzle generates one SQL query per relational query call, not N+1. This is a key performance advantage over naive implementations.

6. **`findFirst` returns `undefined`** — Unlike `findMany` which returns `[]`, `findFirst` returns `undefined` when no match is found. Always handle this case.

---

**Related:** [Relations](./03-relations.md) | [Select Queries](./04-select-queries.md)
