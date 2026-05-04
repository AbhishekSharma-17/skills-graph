# Prisma Select & Include

> Source: [prisma.io/docs/orm/prisma-client/queries/select-fields](https://www.prisma.io/docs/orm/prisma-client/queries/select-fields) — Prisma ORM v7.x

## Table of Contents

- [Select vs Include](#select-vs-include)
- [Select — Pick Specific Fields](#select--pick-specific-fields)
- [Include — Load Relations](#include--load-relations)
- [Nested Select and Include](#nested-select-and-include)
- [Relation Count with _count](#relation-count-with-_count)
- [Omit — Exclude Fields](#omit--exclude-fields)
- [Fluent API](#fluent-api)
- [Relation Load Strategy](#relation-load-strategy)
- [Common Patterns](#common-patterns)

---

## Select vs Include

| Feature | `select` | `include` |
|---------|----------|-----------|
| Returns | Only specified fields | All scalar fields + specified relations |
| Relations | Must be explicitly selected | Added on top of scalars |
| Mutual exclusion | Cannot use with `include` | Cannot use with `select` |
| Default behavior | All scalar fields if neither used | All scalar fields if neither used |

**Rule**: You cannot use `select` and `include` at the same level in the same query.

## Select — Pick Specific Fields

Return only the fields you need:

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  select: {
    id: true,
    email: true,
    name: true,
  },
});
// Type: { id: number; email: string; name: string | null }
// Other fields like role, createdAt are NOT returned
```

### Select with Relations

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  select: {
    name: true,
    posts: {
      select: {
        title: true,
        published: true,
      },
    },
  },
});
// Type: { name: string | null; posts: { title: string; published: boolean }[] }
```

### Select on Nested Relations

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  select: {
    name: true,
    posts: {
      select: {
        title: true,
        categories: {
          select: { name: true },
        },
      },
    },
  },
});
```

## Include — Load Relations

Fetch all scalar fields PLUS specified relations:

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: { posts: true },
});
// Returns: all User fields + posts array with all Post fields
```

### Include with Filters

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: {
    posts: {
      where: { published: true },
      orderBy: { createdAt: "desc" },
      take: 5,
    },
  },
});
```

### Multiple Relations

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: {
    posts: true,
    profile: true,
    comments: true,
  },
});
```

## Nested Select and Include

You can use `select` inside `include` (at different nesting levels):

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: {
    posts: {
      select: {
        id: true,
        title: true,
        // only these fields from Post
      },
    },
  },
});
```

### Deep Nesting

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: {
    posts: {
      include: {
        comments: {
          include: {
            author: {
              select: { name: true, email: true },
            },
          },
        },
      },
    },
  },
});
```

## Relation Count with _count

Get the count of related records without fetching them:

```typescript
// Count all relations
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: {
    _count: {
      select: { posts: true, comments: true },
    },
  },
});
// Result: { id: 1, name: "Alice", ..., _count: { posts: 5, comments: 12 } }
```

### Filtered Count

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: {
    _count: {
      select: {
        posts: { where: { published: true } },
      },
    },
  },
});
```

### Count with Select

```typescript
const users = await prisma.user.findMany({
  select: {
    id: true,
    name: true,
    _count: {
      select: { posts: true },
    },
  },
  orderBy: {
    posts: { _count: "desc" },
  },
});
```

## Omit — Exclude Fields

Exclude specific fields (inverse of `select`):

```typescript
const user = await prisma.user.findUnique({
  where: { id: 1 },
  omit: {
    password: true,     // exclude password
    internalNotes: true, // exclude internal notes
  },
});
// Returns all fields EXCEPT password and internalNotes
```

### Global Omit

Configure fields to always exclude:

```typescript
const prisma = new PrismaClient({
  adapter,
  omit: {
    user: { password: true },  // always exclude password from User queries
  },
});

// Override in specific queries
const userWithPassword = await prisma.user.findUnique({
  where: { id: 1 },
  omit: { password: false },  // explicitly include
});
```

**Note**: `omit` cannot be used with `select` at the same level.

## Fluent API

Chain through relations without `include`:

```typescript
// Get a user's posts directly
const posts = await prisma.user
  .findUnique({ where: { id: 1 } })
  .posts();

// Get a post's author
const author = await prisma.post
  .findUnique({ where: { id: 1 } })
  .author();

// Chain with filters
const publishedPosts = await prisma.user
  .findUnique({ where: { id: 1 } })
  .posts({ where: { published: true } });

// Deep chaining
const comments = await prisma.user
  .findUnique({ where: { id: 1 } })
  .posts()
  .then((posts) => posts[0])
  // Note: further chaining doesn't work this way;
  // use include for deep nesting instead
```

## Relation Load Strategy

Control how relations are loaded from the database:

```typescript
// Default: separate queries
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: { posts: true },
  relationLoadStrategy: "query",  // default: separate SELECT queries
});

// Join: single SQL JOIN query
const user = await prisma.user.findUnique({
  where: { id: 1 },
  include: { posts: true },
  relationLoadStrategy: "join",   // single JOIN query
});
```

**join** constraints:
- Only equality filters on relations
- No boolean operators on relation filters
- Better for simple relation loading with fewer records

**query** (default) advantages:
- More flexible filtering
- Better for large result sets
- Works with all filter types

## Common Patterns

### API Response Shaping

```typescript
const publicUser = await prisma.user.findUnique({
  where: { id: userId },
  select: {
    id: true,
    name: true,
    email: true,
    profile: {
      select: { bio: true, avatar: true },
    },
    _count: {
      select: { posts: true, followers: true },
    },
  },
});
```

### Type-Safe Return Types

```typescript
import { Prisma } from "./generated/prisma/index.js";

// Define a reusable select
const userWithPosts = Prisma.validator<Prisma.UserSelect>()({
  id: true,
  name: true,
  email: true,
  posts: {
    select: { id: true, title: true },
  },
});

// Use in queries
const user = await prisma.user.findUnique({
  where: { id: 1 },
  select: userWithPosts,
});

// Derive the type
type UserWithPosts = Prisma.UserGetPayload<{
  select: typeof userWithPosts;
}>;
```

### Conditional Includes

```typescript
async function getUser(id: number, includePosts: boolean) {
  return prisma.user.findUnique({
    where: { id },
    include: {
      profile: true,
      ...(includePosts && { posts: true }),
    },
  });
}
```

### Avoiding Over-Fetching

```typescript
// BAD — fetches all fields including large content
const posts = await prisma.post.findMany({
  include: { author: true },
});

// GOOD — only fetch what the UI needs
const posts = await prisma.post.findMany({
  select: {
    id: true,
    title: true,
    createdAt: true,
    author: {
      select: { name: true },
    },
  },
});
```
