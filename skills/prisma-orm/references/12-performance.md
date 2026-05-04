# Prisma Performance Optimization

> Source: [prisma.io/docs/orm/prisma-client/queries/query-optimization-performance](https://www.prisma.io/docs/orm/prisma-client/queries/query-optimization-performance) — Prisma ORM v7.x

## Table of Contents

- [N+1 Problem](#n1-problem)
- [Connection Pooling](#connection-pooling)
- [Query Optimization](#query-optimization)
- [Select Only What You Need](#select-only-what-you-need)
- [Batch Operations](#batch-operations)
- [Indexing](#indexing)
- [Logging and Debugging](#logging-and-debugging)
- [Prisma Accelerate](#prisma-accelerate)
- [Serverless Optimization](#serverless-optimization)
- [Common Anti-Patterns](#common-anti-patterns)

---

## N+1 Problem

The N+1 problem occurs when fetching a list of records and then querying for each record's relations individually.

### The Problem

```typescript
// BAD: N+1 queries (1 for users + N for each user's posts)
const users = await prisma.user.findMany();
for (const user of users) {
  const posts = await prisma.post.findMany({
    where: { authorId: user.id },
  });
}
```

### Solution 1: Use include

```typescript
// GOOD: 2 queries (1 for users + 1 for all posts)
const users = await prisma.user.findMany({
  include: { posts: true },
});
```

### Solution 2: Use findUnique + Fluent API (DataLoader)

Prisma automatically batches `findUnique` queries in the same tick:

```typescript
// In a GraphQL resolver — Prisma batches these automatically
const User = {
  posts: (parent: User) =>
    prisma.user.findUnique({ where: { id: parent.id } }).posts(),
};
```

### Solution 3: In-Filter

```typescript
// Fetch all users, then all their posts in one query
const users = await prisma.user.findMany();
const userIds = users.map((u) => u.id);
const posts = await prisma.post.findMany({
  where: { authorId: { in: userIds } },
});
```

### Solution 4: Join Strategy

```typescript
// Single SQL JOIN query
const users = await prisma.user.findMany({
  include: { posts: true },
  relationLoadStrategy: "join",
});
```

## Connection Pooling

### Singleton Pattern

```typescript
// CRITICAL: Only create ONE PrismaClient instance
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ?? new PrismaClient({ adapter });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
```

### Pool Configuration (Prisma 7)

```typescript
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
  max: 20,                      // max pool connections
  idleTimeoutMillis: 30_000,    // close idle connections after 30s
  connectionTimeoutMillis: 5_000, // timeout waiting for connection
});
```

### Default Pool Sizes

| Database | Default Pool | Default Idle Timeout |
|----------|-------------|---------------------|
| PostgreSQL | 10 | 10s |
| MySQL | 10 | 1800s |
| SQL Server | 10 | 30s |

### External Connection Poolers

For serverless or high-concurrency environments, use PgBouncer:

```
# Direct URL for migrations
DIRECT_DATABASE_URL="postgresql://user:pass@host:5432/db"

# PgBouncer URL for queries
DATABASE_URL="postgresql://user:pass@pgbouncer-host:6432/db?pgbouncing=true"
```

## Query Optimization

### Use Appropriate Operations

```typescript
// BAD: Fetches entire record just to check existence
const user = await prisma.user.findUnique({ where: { id: 1 } });
if (user) { /* ... */ }

// GOOD: Minimal query
const exists = await prisma.user.count({ where: { id: 1 } }) > 0;

// BAD: Fetches all fields
const users = await prisma.user.findMany();

// GOOD: Select only needed fields
const users = await prisma.user.findMany({
  select: { id: true, name: true, email: true },
});
```

### Limit Result Sets

```typescript
// Always paginate large result sets
const posts = await prisma.post.findMany({
  take: 20,
  orderBy: { createdAt: "desc" },
});

// Use cursor for deep pagination
const nextPage = await prisma.post.findMany({
  take: 20,
  skip: 1,
  cursor: { id: lastId },
  orderBy: { id: "asc" },
});
```

### Avoid Unnecessary Includes

```typescript
// BAD: Loading full relation trees
const users = await prisma.user.findMany({
  include: {
    posts: { include: { comments: { include: { author: true } } } },
    profile: true,
    settings: true,
  },
});

// GOOD: Load only what the view needs
const users = await prisma.user.findMany({
  select: {
    id: true,
    name: true,
    _count: { select: { posts: true } },
  },
});
```

## Select Only What You Need

### Field Selection

```typescript
// Returns only id, name, email — smaller payload, faster query
const users = await prisma.user.findMany({
  select: { id: true, name: true, email: true },
});
```

### Relation Counts Instead of Full Data

```typescript
// Instead of loading all posts just to count them
const users = await prisma.user.findMany({
  include: {
    _count: { select: { posts: true, comments: true } },
  },
});
```

### Global omit for Sensitive Fields

```typescript
const prisma = new PrismaClient({
  adapter,
  omit: {
    user: { password: true, internalNotes: true },
  },
});
```

## Batch Operations

### Use Bulk Methods

```typescript
// BAD: N individual inserts
for (const item of items) {
  await prisma.product.create({ data: item });
}

// GOOD: Single bulk insert
await prisma.product.createMany({
  data: items,
  skipDuplicates: true,
});

// BAD: N individual updates
for (const id of ids) {
  await prisma.post.update({ where: { id }, data: { published: true } });
}

// GOOD: Single bulk update
await prisma.post.updateMany({
  where: { id: { in: ids } },
  data: { published: true },
});
```

### Transaction for Related Bulk Operations

```typescript
const [deleted, updated] = await prisma.$transaction([
  prisma.comment.deleteMany({ where: { postId: { in: postIds } } }),
  prisma.post.updateMany({
    where: { id: { in: postIds } },
    data: { commentCount: 0 },
  }),
]);
```

## Indexing

### Schema-Level Indexes

```prisma
model Post {
  id        Int      @id @default(autoincrement())
  title     String
  authorId  Int
  published Boolean  @default(false)
  createdAt DateTime @default(now())

  author User @relation(fields: [authorId], references: [id])

  // Index foreign keys
  @@index([authorId])

  // Composite index for common queries
  @@index([published, createdAt])

  // Index for text search
  @@index([title], type: GIN)
}
```

### Index Strategy

| Query Pattern | Index Type |
|--------------|------------|
| Foreign key lookups | `@@index([fkField])` |
| Equality + range | `@@index([equalityField, rangeField])` |
| Multi-column filter | `@@index([col1, col2])` (order matters) |
| Text search | `@@index([field], type: GIN)` |
| Unique lookups | `@unique` (implicit index) |
| Sorting | Index on `orderBy` fields |

### Common Missing Indexes

```prisma
// Always index foreign keys
model Comment {
  postId   Int
  authorId Int
  @@index([postId])
  @@index([authorId])
}

// Index commonly filtered fields
model User {
  role      String
  active    Boolean
  createdAt DateTime
  @@index([role, active])
  @@index([createdAt])
}
```

## Logging and Debugging

### Query Logging

```typescript
const prisma = new PrismaClient({
  adapter,
  log: [
    { emit: "event", level: "query" },
    { emit: "stdout", level: "warn" },
    { emit: "stdout", level: "error" },
  ],
});

prisma.$on("query", (e) => {
  console.log(`Query: ${e.query}`);
  console.log(`Duration: ${e.duration}ms`);
  console.log(`Params: ${e.params}`);
});
```

### Slow Query Detection

```typescript
prisma.$on("query", (e) => {
  if (e.duration > 200) {
    console.warn(`SLOW QUERY (${e.duration}ms): ${e.query}`);
  }
});
```

### Query Attribution with SQLCommenter

```typescript
import { createSqlcommenterQueryInsights } from "@prisma/sqlcommenter-query-insights";

const prisma = new PrismaClient({
  adapter,
  comments: createSqlcommenterQueryInsights(),
});
// Adds SQL comments: /* model=User, action=findMany */
```

## Prisma Accelerate

Global connection pooler + query caching service:

### Setup

```typescript
import { PrismaClient } from "./generated/prisma/index.js";
import { withAccelerate } from "@prisma/extension-accelerate";

const prisma = new PrismaClient({
  accelerateUrl: process.env.DATABASE_URL, // prisma:// URL
}).$extends(withAccelerate());
```

### Caching Queries

```typescript
// Cache for 60 seconds
const posts = await prisma.post.findMany({
  where: { published: true },
  cacheStrategy: { ttl: 60 },
});

// Stale-while-revalidate pattern
const posts = await prisma.post.findMany({
  where: { published: true },
  cacheStrategy: {
    ttl: 60,           // Serve from cache for 60s
    swr: 120,          // Serve stale for 120s while revalidating
    tags: ["posts"],   // Tag for invalidation
  },
});

// Invalidate cache
await prisma.$accelerate.invalidate({ tags: ["posts"] });
```

### When to Use Accelerate

- Serverless deployments (connection pooling)
- Edge/global deployments (reduced latency)
- Read-heavy workloads (query caching)
- Frequently accessed, rarely changing data

## Serverless Optimization

### Cold Start Reduction

```typescript
// Generate without engine for smaller bundles
// npx prisma generate --no-engine

// Use Accelerate for connection pooling
const prisma = new PrismaClient({
  accelerateUrl: process.env.DATABASE_URL,
}).$extends(withAccelerate());
```

### Connection Management

```typescript
// Always disconnect in serverless handlers
export async function handler(event) {
  try {
    const result = await prisma.user.findMany();
    return { statusCode: 200, body: JSON.stringify(result) };
  } finally {
    await prisma.$disconnect();
  }
}
```

## Common Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Multiple PrismaClient instances | Use singleton pattern |
| N+1 in loops | Use `include` or `findMany` with `in` filter |
| `findMany` without `take` | Always paginate |
| `include` entire relation trees | Use `select` for needed fields only |
| Individual creates in loop | Use `createMany` |
| Not indexing foreign keys | Add `@@index` on all FK fields |
| Logging all queries in production | Use event-based logging with thresholds |
| Not disconnecting in serverless | Add `$disconnect()` in finally block |
