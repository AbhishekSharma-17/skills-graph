# Prisma Filtering & Sorting

> Source: [prisma.io/docs/orm/prisma-client/queries](https://www.prisma.io/docs/orm/prisma-client/queries) — Prisma ORM v7.x

## Table of Contents

- [Comparison Operators](#comparison-operators)
- [String Filters](#string-filters)
- [Logical Operators](#logical-operators)
- [Relation Filters](#relation-filters)
- [List Filters](#list-filters)
- [Sorting](#sorting)
- [Offset Pagination](#offset-pagination)
- [Cursor-Based Pagination](#cursor-based-pagination)
- [Distinct](#distinct)
- [Common Patterns](#common-patterns)

---

## Comparison Operators

All comparison operators work inside the `where` clause:

```typescript
// Equals (implicit)
await prisma.user.findMany({
  where: { email: "alice@example.com" },
});

// Equals (explicit)
await prisma.user.findMany({
  where: { email: { equals: "alice@example.com" } },
});

// Not equal
await prisma.user.findMany({
  where: { email: { not: "alice@example.com" } },
});

// In list
await prisma.user.findMany({
  where: { role: { in: ["ADMIN", "MODERATOR"] } },
});

// Not in list
await prisma.user.findMany({
  where: { role: { notIn: ["BANNED"] } },
});

// Numeric comparisons
await prisma.post.findMany({
  where: {
    views: { gt: 100 },       // greater than
    likes: { gte: 10 },       // greater than or equal
    score: { lt: 50 },        // less than
    rank: { lte: 5 },         // less than or equal
  },
});

// DateTime comparisons
await prisma.post.findMany({
  where: {
    createdAt: { gte: new Date("2025-01-01") },
    updatedAt: { lt: new Date() },
  },
});

// Null checks
await prisma.user.findMany({
  where: { deletedAt: null },           // IS NULL
});
await prisma.user.findMany({
  where: { deletedAt: { not: null } },  // IS NOT NULL
});
```

## String Filters

```typescript
// Contains (LIKE '%text%')
await prisma.user.findMany({
  where: { name: { contains: "ali" } },
});

// Case-insensitive (PostgreSQL, MongoDB)
await prisma.user.findMany({
  where: { name: { contains: "ali", mode: "insensitive" } },
});

// Starts with
await prisma.user.findMany({
  where: { email: { startsWith: "admin" } },
});

// Ends with
await prisma.user.findMany({
  where: { email: { endsWith: "@prisma.io" } },
});

// Combine string filters
await prisma.user.findMany({
  where: {
    email: {
      contains: "prisma",
      endsWith: ".io",
      mode: "insensitive",
    },
  },
});
```

## Logical Operators

### AND

```typescript
// Implicit AND (multiple fields)
await prisma.user.findMany({
  where: {
    role: "ADMIN",
    active: true,
  },
});

// Explicit AND (same field or complex)
await prisma.post.findMany({
  where: {
    AND: [
      { views: { gt: 100 } },
      { views: { lt: 1000 } },
      { published: true },
    ],
  },
});
```

### OR

```typescript
await prisma.user.findMany({
  where: {
    OR: [
      { email: { contains: "prisma" } },
      { name: { contains: "Prisma" } },
    ],
  },
});
```

### NOT

```typescript
await prisma.user.findMany({
  where: {
    NOT: {
      role: "BANNED",
    },
  },
});

// NOT with array
await prisma.user.findMany({
  where: {
    NOT: [
      { role: "BANNED" },
      { active: false },
    ],
  },
});
```

### Combining Operators

```typescript
await prisma.post.findMany({
  where: {
    AND: [
      { published: true },
      {
        OR: [
          { title: { contains: "prisma" } },
          { content: { contains: "prisma" } },
        ],
      },
      { NOT: { authorId: null } },
    ],
  },
});
```

## Relation Filters

Filter parent records based on properties of their children.

### some — At Least One Match

```typescript
// Users who have at least one published post
await prisma.user.findMany({
  where: {
    posts: { some: { published: true } },
  },
});
```

### every — All Must Match

```typescript
// Users where ALL posts are published
await prisma.user.findMany({
  where: {
    posts: { every: { published: true } },
  },
});
```

### none — No Matches

```typescript
// Users with no posts
await prisma.user.findMany({
  where: {
    posts: { none: {} },
  },
});

// Users with no unpublished posts
await prisma.user.findMany({
  where: {
    posts: { none: { published: false } },
  },
});
```

### is / isNot — Single Relation Filter

```typescript
// Posts by a specific author
await prisma.post.findMany({
  where: {
    author: { is: { email: "alice@example.com" } },
  },
});

// Posts NOT by a specific author
await prisma.post.findMany({
  where: {
    author: { isNot: { role: "BANNED" } },
  },
});

// Posts with no author (null check on relation)
await prisma.post.findMany({
  where: { author: null },
});
```

## List Filters

Filter on scalar list fields (arrays):

```typescript
// Has exact value in array
await prisma.post.findMany({
  where: { tags: { has: "typescript" } },
});

// Has every value
await prisma.post.findMany({
  where: { tags: { hasEvery: ["typescript", "prisma"] } },
});

// Has at least one value
await prisma.post.findMany({
  where: { tags: { hasSome: ["typescript", "prisma"] } },
});

// Is empty
await prisma.post.findMany({
  where: { tags: { isEmpty: true } },
});

// Equals exact array
await prisma.post.findMany({
  where: { tags: { equals: ["typescript", "prisma"] } },
});
```

## Sorting

### Basic Ordering

```typescript
// Single field
await prisma.user.findMany({
  orderBy: { createdAt: "desc" },
});

// Multiple fields
await prisma.user.findMany({
  orderBy: [
    { role: "asc" },
    { name: "asc" },
  ],
});
```

### Null Positioning

```typescript
await prisma.user.findMany({
  orderBy: {
    updatedAt: { sort: "desc", nulls: "last" },
  },
});

// Options: "first" | "last"
```

### Ordering by Relation

```typescript
// Order users by their post count
await prisma.user.findMany({
  orderBy: {
    posts: { _count: "desc" },
  },
});

// Order posts by author name
await prisma.post.findMany({
  orderBy: {
    author: { name: "asc" },
  },
});
```

### Ordering by Relevance (Full-Text Search)

```typescript
await prisma.post.findMany({
  orderBy: {
    _relevance: {
      fields: ["title", "content"],
      search: "prisma database",
      sort: "desc",
    },
  },
});
```

## Offset Pagination

```typescript
// Page-based pagination
const page = 2;
const pageSize = 10;

const posts = await prisma.post.findMany({
  skip: (page - 1) * pageSize,
  take: pageSize,
  orderBy: { createdAt: "desc" },
});
```

Pros: Simple, easy random page access.
Cons: Performance degrades on large offsets; inconsistent with concurrent writes.

## Cursor-Based Pagination

```typescript
// First page
const firstPage = await prisma.post.findMany({
  take: 10,
  orderBy: { id: "asc" },
});

// Next page (using last item's ID as cursor)
const lastItem = firstPage[firstPage.length - 1];
const nextPage = await prisma.post.findMany({
  take: 10,
  skip: 1,         // skip the cursor record itself
  cursor: { id: lastItem.id },
  orderBy: { id: "asc" },
});

// Previous page (negative take)
const prevPage = await prisma.post.findMany({
  take: -10,
  skip: 1,
  cursor: { id: firstItem.id },
  orderBy: { id: "asc" },
});
```

Pros: Consistent performance regardless of dataset size; stable pagination.
Cons: No random page access; cursor field must be unique and sequential.

## Distinct

```typescript
// Unique roles
const roles = await prisma.user.findMany({
  distinct: ["role"],
  select: { role: true },
});

// Distinct combination
const results = await prisma.post.findMany({
  distinct: ["authorId", "published"],
});
```

## Common Patterns

### Search with Combined Filters

```typescript
async function searchPosts(query: string, filters: PostFilters) {
  return prisma.post.findMany({
    where: {
      AND: [
        { published: true },
        query
          ? {
              OR: [
                { title: { contains: query, mode: "insensitive" } },
                { content: { contains: query, mode: "insensitive" } },
              ],
            }
          : {},
        filters.authorId ? { authorId: filters.authorId } : {},
        filters.tags?.length ? { tags: { hasSome: filters.tags } } : {},
      ],
    },
    orderBy: { createdAt: "desc" },
    take: filters.limit ?? 20,
    skip: filters.offset ?? 0,
    include: { author: { select: { name: true } } },
  });
}
```

### Dynamic Where Clauses

```typescript
import { Prisma } from "./generated/prisma/index.js";

function buildWhere(filters: Filters): Prisma.PostWhereInput {
  const where: Prisma.PostWhereInput = {};

  if (filters.published !== undefined) where.published = filters.published;
  if (filters.authorId) where.authorId = filters.authorId;
  if (filters.search) {
    where.OR = [
      { title: { contains: filters.search, mode: "insensitive" } },
      { content: { contains: filters.search, mode: "insensitive" } },
    ];
  }

  return where;
}

const posts = await prisma.post.findMany({
  where: buildWhere(filters),
});
```
