# Prisma Relations

> Source: [prisma.io/docs/orm/prisma-schema/data-model/relations](https://www.prisma.io/docs/orm/prisma-schema/data-model/relations) — Prisma ORM v7.x

## Table of Contents

- [Relation Concepts](#relation-concepts)
- [One-to-One Relations](#one-to-one-relations)
- [One-to-Many Relations](#one-to-many-relations)
- [Many-to-Many (Implicit)](#many-to-many-implicit)
- [Many-to-Many (Explicit)](#many-to-many-explicit)
- [Self-Relations](#self-relations)
- [Disambiguating Relations](#disambiguating-relations)
- [Referential Actions](#referential-actions)
- [Querying Relations](#querying-relations)
- [Common Pitfalls](#common-pitfalls)

---

## Relation Concepts

A relation is a connection between two models. Every relation consists of:

- **Relation fields** — virtual fields that exist only in the Prisma schema (not in the DB)
- **Scalar relation fields** — actual foreign key columns in the database
- **@relation attribute** — configures the relationship

```prisma
model User {
  id    Int    @id @default(autoincrement())
  posts Post[]           // relation field (virtual — no DB column)
}

model Post {
  id       Int  @id @default(autoincrement())
  author   User @relation(fields: [authorId], references: [id])  // relation field
  authorId Int  // scalar relation field (FK column in DB)
}
```

## One-to-One Relations

One record in model A corresponds to exactly one record in model B.

```prisma
model User {
  id      Int      @id @default(autoincrement())
  email   String   @unique
  profile Profile?
}

model Profile {
  id     Int    @id @default(autoincrement())
  bio    String
  user   User   @relation(fields: [userId], references: [id])
  userId Int    @unique    // @unique makes it 1:1
}
```

Key rules:
- The foreign key field (`userId`) must have `@unique`
- The non-FK side has an optional relation field (`Profile?`)
- `@relation` is on the side that stores the FK

### Querying

```typescript
// Create user with profile
const user = await prisma.user.create({
  data: {
    email: "alice@example.com",
    profile: {
      create: { bio: "Hello world" },
    },
  },
  include: { profile: true },
});

// Access profile from user
const profile = await prisma.user.findUnique({
  where: { id: 1 },
}).profile();
```

## One-to-Many Relations

One record in model A has many related records in model B.

```prisma
model User {
  id    Int    @id @default(autoincrement())
  email String @unique
  posts Post[]
}

model Post {
  id       Int    @id @default(autoincrement())
  title    String
  author   User   @relation(fields: [authorId], references: [id])
  authorId Int
}
```

Key rules:
- The "many" side stores the FK (`authorId` on Post)
- The "one" side has a list relation field (`Post[]`)
- No `@unique` on the FK (that would make it 1:1)

### Querying

```typescript
// Create user with posts
const user = await prisma.user.create({
  data: {
    email: "bob@example.com",
    posts: {
      create: [
        { title: "First Post" },
        { title: "Second Post" },
      ],
    },
  },
});

// Get user's posts
const posts = await prisma.user.findUnique({
  where: { id: 1 },
  include: { posts: true },
});

// Filter users by posts
const usersWithPublished = await prisma.user.findMany({
  where: { posts: { some: { published: true } } },
});
```

## Many-to-Many (Implicit)

Prisma manages the join table automatically.

```prisma
model Post {
  id         Int        @id @default(autoincrement())
  title      String
  categories Category[]
}

model Category {
  id    Int    @id @default(autoincrement())
  name  String @unique
  posts Post[]
}
```

Prisma creates a hidden `_CategoryToPost` join table. Requirements:
- Both models must use `@id` (not `@@id`)
- The join table has no extra columns

### Querying

```typescript
// Create with connection
const post = await prisma.post.create({
  data: {
    title: "GraphQL with Prisma",
    categories: {
      create: [{ name: "GraphQL" }, { name: "Database" }],
    },
  },
});

// Connect existing records
await prisma.post.update({
  where: { id: 1 },
  data: {
    categories: {
      connect: [{ id: 1 }, { id: 2 }],
    },
  },
});

// Disconnect
await prisma.post.update({
  where: { id: 1 },
  data: {
    categories: {
      disconnect: [{ id: 1 }],
    },
  },
});

// Set (replace all)
await prisma.post.update({
  where: { id: 1 },
  data: {
    categories: {
      set: [{ id: 3 }, { id: 4 }],
    },
  },
});
```

## Many-to-Many (Explicit)

Define the join table as a model when you need extra columns or composite IDs.

```prisma
model Post {
  id         Int            @id @default(autoincrement())
  title      String
  categories CategoriesOnPosts[]
}

model Category {
  id    Int                 @id @default(autoincrement())
  name  String              @unique
  posts CategoriesOnPosts[]
}

model CategoriesOnPosts {
  post       Post     @relation(fields: [postId], references: [id])
  postId     Int
  category   Category @relation(fields: [categoryId], references: [id])
  categoryId Int
  assignedAt DateTime @default(now())
  assignedBy String

  @@id([postId, categoryId])
}
```

### Querying Explicit Join Tables

```typescript
// Create with join data
await prisma.categoriesOnPosts.create({
  data: {
    post: { connect: { id: 1 } },
    category: { connect: { id: 1 } },
    assignedBy: "admin",
  },
});

// Query through join table
const posts = await prisma.post.findMany({
  include: {
    categories: {
      include: { category: true },
    },
  },
});
```

## Self-Relations

A model can relate to itself.

### One-to-One Self-Relation

```prisma
model User {
  id          Int   @id @default(autoincrement())
  name        String
  successor   User? @relation("Succession", fields: [successorId], references: [id])
  successorId Int?  @unique
  predecessor User? @relation("Succession")
}
```

### One-to-Many Self-Relation (Tree)

```prisma
model Category {
  id       Int        @id @default(autoincrement())
  name     String
  parent   Category?  @relation("CategoryTree", fields: [parentId], references: [id])
  parentId Int?
  children Category[] @relation("CategoryTree")
}
```

### Many-to-Many Self-Relation (Social Graph)

```prisma
model User {
  id         Int    @id @default(autoincrement())
  name       String
  followedBy User[] @relation("UserFollows")
  following  User[] @relation("UserFollows")
}
```

## Disambiguating Relations

When two models have multiple relations, use named relations:

```prisma
model User {
  id           Int     @id @default(autoincrement())
  writtenPosts Post[]  @relation("WrittenPosts")
  pinnedPost   Post?   @relation("PinnedPost")
}

model Post {
  id         Int   @id @default(autoincrement())
  title      String
  author     User  @relation("WrittenPosts", fields: [authorId], references: [id])
  authorId   Int
  pinnedBy   User? @relation("PinnedPost", fields: [pinnedById], references: [id])
  pinnedById Int?  @unique
}
```

The relation name string must match on both sides.

## Referential Actions

Control what happens when a referenced record is deleted or updated.

```prisma
model Post {
  author   User @relation(fields: [authorId], references: [id], onDelete: Cascade, onUpdate: Cascade)
  authorId Int
}
```

| Action | On Delete | On Update |
|--------|-----------|-----------|
| `Cascade` | Delete related records | Update FK to new value |
| `Restrict` | Prevent deletion if references exist | Prevent update |
| `NoAction` | Similar to Restrict (DB-level) | Similar to Restrict |
| `SetNull` | Set FK to null (field must be optional) | Set FK to null |
| `SetDefault` | Set FK to default value | Set FK to default |

### Common Patterns

```prisma
// Delete user → delete all their posts
model Post {
  author   User @relation(fields: [authorId], references: [id], onDelete: Cascade)
  authorId Int
}

// Delete user → set posts.authorId to null (orphan posts)
model Post {
  author   User? @relation(fields: [authorId], references: [id], onDelete: SetNull)
  authorId Int?
}

// Prevent deleting user if they have posts
model Post {
  author   User @relation(fields: [authorId], references: [id], onDelete: Restrict)
  authorId Int
}
```

## Querying Relations

### Nested Writes

```typescript
// Create parent with children
await prisma.user.create({
  data: {
    email: "alice@example.com",
    posts: {
      create: [{ title: "Post 1" }, { title: "Post 2" }],
    },
  },
});

// Connect existing child
await prisma.user.update({
  where: { id: 1 },
  data: { posts: { connect: { id: 5 } } },
});

// Create or connect
await prisma.user.update({
  where: { id: 1 },
  data: {
    posts: {
      connectOrCreate: {
        where: { id: 10 },
        create: { title: "New Post" },
      },
    },
  },
});
```

### Fluent API

```typescript
// Chain through relations
const posts = await prisma.user
  .findUnique({ where: { id: 1 } })
  .posts();

const author = await prisma.post
  .findUnique({ where: { id: 1 } })
  .author();
```

### Relation Filters

```typescript
// Users who have at least one published post
await prisma.user.findMany({
  where: { posts: { some: { published: true } } },
});

// Users where ALL posts are published
await prisma.user.findMany({
  where: { posts: { every: { published: true } } },
});

// Users with NO posts
await prisma.user.findMany({
  where: { posts: { none: {} } },
});
```

## Common Pitfalls

1. **Missing @relation on both sides** — Every relation needs fields on both models
2. **Forgetting @unique for 1:1** — Without it, the relation is 1:n
3. **Implicit m:n with @@id** — Implicit many-to-many requires `@id`, not compound `@@id`
4. **Ambiguous relations** — Multiple relations between same models need named `@relation("Name")`
5. **Circular cascades** — Be careful with `onDelete: Cascade` on bidirectional relations
