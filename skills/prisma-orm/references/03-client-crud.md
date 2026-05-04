# Prisma Client CRUD Operations

> Source: [prisma.io/docs/orm/prisma-client/queries/crud](https://www.prisma.io/docs/orm/prisma-client/queries/crud) — Prisma ORM v7.x

## Table of Contents

- [Read Operations](#read-operations)
- [Create Operations](#create-operations)
- [Update Operations](#update-operations)
- [Delete Operations](#delete-operations)
- [Upsert](#upsert)
- [Batch Operations](#batch-operations)
- [Aggregate Operations](#aggregate-operations)
- [Group By](#group-by)
- [Count](#count)
- [Common Patterns](#common-patterns)

---

## Read Operations

### findUnique — Single Record by Unique Field

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
});

const user = await prisma.user.findUnique({
  where: { email: "alice@example.com" },
});

// Compound unique
const postTag = await prisma.postTag.findUnique({
  where: { postId_tagId: { postId: 1, tagId: 2 } },
});
```

Returns `null` if not found.

### findUniqueOrThrow — Throws if Not Found

```typescript
const user = await prisma.user.findUniqueOrThrow({
  where: { id: 1 },
});
// Throws PrismaClientKnownRequestError (P2025) if not found
```

### findFirst — First Matching Record

```typescript
const post = await prisma.post.findFirst({
  where: { published: true },
  orderBy: { createdAt: "desc" },
});
```

Returns `null` if nothing matches.

### findFirstOrThrow — Throws if No Match

```typescript
const post = await prisma.post.findFirstOrThrow({
  where: { published: true },
});
```

### findMany — Multiple Records

```typescript
// All records
const allUsers = await prisma.user.findMany();

// With filters, sorting, pagination
const users = await prisma.user.findMany({
  where: { role: "ADMIN" },
  orderBy: { createdAt: "desc" },
  take: 10,
  skip: 0,
  select: { id: true, email: true, name: true },
});
```

Returns an empty array `[]` if nothing matches.

## Create Operations

### create — Single Record

```typescript
const user = await prisma.user.create({
  data: {
    email: "alice@example.com",
    name: "Alice",
    role: "USER",
  },
});

// Create with relations (nested write)
const user = await prisma.user.create({
  data: {
    email: "bob@example.com",
    name: "Bob",
    posts: {
      create: [
        { title: "First Post", published: true },
        { title: "Draft Post" },
      ],
    },
    profile: {
      create: { bio: "I love coding" },
    },
  },
  include: { posts: true, profile: true },
});
```

### createMany — Bulk Insert

```typescript
const result = await prisma.user.createMany({
  data: [
    { email: "a@example.com", name: "Alice" },
    { email: "b@example.com", name: "Bob" },
    { email: "c@example.com", name: "Charlie" },
  ],
  skipDuplicates: true,   // skip rows with duplicate unique fields
});
console.log(result.count); // number of created records
```

`createMany` does NOT support nested writes (relations).

### createManyAndReturn — Bulk Insert with Results

```typescript
// PostgreSQL, CockroachDB, SQLite only
const users = await prisma.user.createManyAndReturn({
  data: [
    { email: "a@example.com", name: "Alice" },
    { email: "b@example.com", name: "Bob" },
  ],
  select: { id: true, email: true },
});
```

## Update Operations

### update — Single Record

```typescript
const user = await prisma.user.update({
  where: { email: "alice@example.com" },
  data: { name: "Alice Updated" },
});
```

#### Numeric Operations

```typescript
await prisma.post.update({
  where: { id: 1 },
  data: {
    views: { increment: 1 },       // views + 1
    likes: { decrement: 1 },       // likes - 1
    score: { multiply: 2 },        // score * 2
    rank: { divide: 2 },           // rank / 2
  },
});
```

#### Updating Relations

```typescript
// Connect an existing related record
await prisma.post.update({
  where: { id: 1 },
  data: {
    author: { connect: { id: 5 } },
  },
});

// Disconnect a relation (1:1 or 1:n optional)
await prisma.post.update({
  where: { id: 1 },
  data: {
    author: { disconnect: true },
  },
});

// Update nested records
await prisma.user.update({
  where: { id: 1 },
  data: {
    posts: {
      update: {
        where: { id: 10 },
        data: { title: "Updated Title" },
      },
    },
  },
});

// Create, update, and delete in one operation
await prisma.user.update({
  where: { id: 1 },
  data: {
    posts: {
      create: { title: "New Post" },
      update: { where: { id: 10 }, data: { title: "Changed" } },
      delete: { id: 20 },
    },
  },
});
```

### updateMany — Bulk Update

```typescript
const result = await prisma.post.updateMany({
  where: { published: false, authorId: 1 },
  data: { published: true },
});
console.log(result.count); // number of updated records
```

`updateMany` does NOT support `select` or `include`.

### updateManyAndReturn — Bulk Update with Results

```typescript
const posts = await prisma.post.updateManyAndReturn({
  where: { published: false },
  data: { published: true },
  select: { id: true, title: true },
});
```

## Delete Operations

### delete — Single Record

```typescript
const user = await prisma.user.delete({
  where: { email: "alice@example.com" },
});
```

Throws `P2025` if the record doesn't exist.

### deleteMany — Bulk Delete

```typescript
// Delete matching records
const result = await prisma.post.deleteMany({
  where: { published: false },
});
console.log(result.count);

// Delete ALL records
await prisma.post.deleteMany();
```

## Upsert

Create if not found, update if exists:

```typescript
const user = await prisma.user.upsert({
  where: { email: "alice@example.com" },
  update: { name: "Alice Updated" },
  create: {
    email: "alice@example.com",
    name: "Alice",
    role: "USER",
  },
});
```

The `where` clause must use a unique field.

## Batch Operations

### $transaction — Sequential Batch

```typescript
const [users, posts] = await prisma.$transaction([
  prisma.user.findMany(),
  prisma.post.findMany({ where: { published: true } }),
]);
```

## Aggregate Operations

### aggregate — Mathematical Computations

```typescript
const result = await prisma.post.aggregate({
  _avg: { views: true, likes: true },
  _sum: { views: true },
  _min: { views: true },
  _max: { views: true },
  _count: true,
  where: { published: true },
});

console.log(result._avg.views);   // average views
console.log(result._sum.views);   // total views
console.log(result._count);       // total records
```

## Group By

```typescript
const result = await prisma.user.groupBy({
  by: ["role"],
  _count: { _all: true },
  _avg: { age: true },
  orderBy: { _count: { _all: "desc" } },
  having: { age: { _avg: { gt: 25 } } },
});

// Result: [{ role: "ADMIN", _count: { _all: 5 }, _avg: { age: 35 } }, ...]
```

## Count

```typescript
// Count all users
const count = await prisma.user.count();

// Count with filter
const activeCount = await prisma.user.count({
  where: { active: true },
});

// Count relations
const usersWithPostCount = await prisma.user.findMany({
  include: { _count: { select: { posts: true } } },
});
// Result: [{ id: 1, name: "Alice", _count: { posts: 5 } }, ...]
```

## Common Patterns

### Find or Create

```typescript
const user = await prisma.user.upsert({
  where: { email: "alice@example.com" },
  update: {},   // no-op if exists
  create: { email: "alice@example.com", name: "Alice" },
});
```

### Soft Delete

```typescript
// "Delete" by setting timestamp
await prisma.post.update({
  where: { id: 1 },
  data: { deletedAt: new Date() },
});

// Query only non-deleted records
const activePosts = await prisma.post.findMany({
  where: { deletedAt: null },
});
```

### Check Existence

```typescript
const exists = await prisma.user.count({
  where: { email: "alice@example.com" },
}) > 0;

// Or use findFirst for minimal overhead
const exists = (await prisma.user.findFirst({
  where: { email: "alice@example.com" },
  select: { id: true },
})) !== null;
```

### Paginated List with Total

```typescript
const [posts, total] = await prisma.$transaction([
  prisma.post.findMany({
    where: { published: true },
    orderBy: { createdAt: "desc" },
    take: 10,
    skip: page * 10,
  }),
  prisma.post.count({ where: { published: true } }),
]);
```
