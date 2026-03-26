# Drizzle ORM — Relations

> Source: [orm.drizzle.team/docs/relations](https://orm.drizzle.team/docs/relations)

## Table of Contents

- [Overview](#overview)
- [Declaring Relations](#declaring-relations)
- [One-to-One](#one-to-one)
- [One-to-Many](#one-to-many)
- [Many-to-Many](#many-to-many)
- [Self-Referencing Relations](#self-referencing-relations)
- [Named Relations](#named-relations)
- [Disambiguation](#disambiguation)
- [How Relations Differ from Foreign Keys](#how-relations-differ-from-foreign-keys)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Drizzle relations are a declarative way to describe how tables connect. They power the **Relational Queries API** (`db.query.*`), enabling nested data fetching in a single SQL query.

Relations are separate from foreign keys. Foreign keys enforce referential integrity at the database level. Relations define how Drizzle builds joins for the relational query API. You can use both together or independently.

## Declaring Relations

```typescript
import { relations } from 'drizzle-orm';
import { pgTable, serial, text, integer } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
});

export const posts = pgTable('posts', {
  id: serial('id').primaryKey(),
  content: text('content').notNull(),
  authorId: integer('author_id').notNull(),
});

// Declare relations AFTER tables
export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
}));
```

## One-to-One

```typescript
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
});

export const profiles = pgTable('profiles', {
  id: serial('id').primaryKey(),
  bio: text('bio'),
  userId: integer('user_id').notNull().unique(),
});

export const usersRelations = relations(users, ({ one }) => ({
  profile: one(profiles),
}));

export const profilesRelations = relations(profiles, ({ one }) => ({
  user: one(users, {
    fields: [profiles.userId],
    references: [users.id],
  }),
}));
```

The side that holds the foreign key (`profiles.userId`) must specify `fields` and `references`. The other side just references the table.

## One-to-Many

```typescript
export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
}));
```

Usage with relational queries:

```typescript
const usersWithPosts = await db.query.users.findMany({
  with: {
    posts: true,
  },
});
// Result: { id: 1, name: 'Alice', posts: [{ id: 1, content: '...', authorId: 1 }] }
```

## Many-to-Many

Requires a junction (join/pivot) table:

```typescript
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
});

export const groups = pgTable('groups', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
});

export const usersToGroups = pgTable('users_to_groups', {
  userId: integer('user_id').notNull().references(() => users.id),
  groupId: integer('group_id').notNull().references(() => groups.id),
}, (t) => [
  primaryKey({ columns: [t.userId, t.groupId] }),
]);

// Relations
export const usersRelations = relations(users, ({ many }) => ({
  usersToGroups: many(usersToGroups),
}));

export const groupsRelations = relations(groups, ({ many }) => ({
  usersToGroups: many(usersToGroups),
}));

export const usersToGroupsRelations = relations(usersToGroups, ({ one }) => ({
  user: one(users, {
    fields: [usersToGroups.userId],
    references: [users.id],
  }),
  group: one(groups, {
    fields: [usersToGroups.groupId],
    references: [groups.id],
  }),
}));
```

Querying many-to-many:

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
```

## Self-Referencing Relations

```typescript
export const categories = pgTable('categories', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
  parentId: integer('parent_id'),
});

export const categoriesRelations = relations(categories, ({ one, many }) => ({
  parent: one(categories, {
    fields: [categories.parentId],
    references: [categories.id],
    relationName: 'parent-child',
  }),
  children: many(categories, {
    relationName: 'parent-child',
  }),
}));
```

## Named Relations

When a table has multiple relations to the same table, use `relationName` to disambiguate:

```typescript
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
});

export const posts = pgTable('posts', {
  id: serial('id').primaryKey(),
  authorId: integer('author_id').notNull(),
  reviewerId: integer('reviewer_id'),
});

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
    relationName: 'author',
  }),
  reviewer: one(users, {
    fields: [posts.reviewerId],
    references: [users.id],
    relationName: 'reviewer',
  }),
}));

export const usersRelations = relations(users, ({ many }) => ({
  authoredPosts: many(posts, { relationName: 'author' }),
  reviewedPosts: many(posts, { relationName: 'reviewer' }),
}));
```

## Disambiguation

Both sides of a named relation must use the same `relationName` string. Drizzle uses this to match pairs.

```typescript
// CORRECT: Both sides use 'author'
one(users, { ..., relationName: 'author' })
many(posts, { relationName: 'author' })

// WRONG: Names don't match
one(users, { ..., relationName: 'postAuthor' })
many(posts, { relationName: 'author' })  // Error: unmatched relation
```

## How Relations Differ from Foreign Keys

| Aspect | Foreign Keys | Relations |
|--------|-------------|-----------|
| Purpose | DB-level referential integrity | Query API routing |
| Enforced by | Database engine | Drizzle ORM (JS/TS) |
| Required for SQL-like queries | No | No |
| Required for `db.query.*` | No | Yes |
| Affects migrations | Yes | No |
| Can exist independently | Yes | Yes |

Best practice: Use both. Foreign keys for data integrity, relations for the query API.

```typescript
// Foreign key (DB constraint) + relation (query API)
authorId: integer('author_id').notNull().references(() => users.id),

// Then also declare the relation
export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, {
    fields: [posts.authorId],
    references: [users.id],
  }),
}));
```

## Common Pitfalls

1. **Missing `fields` and `references` on the FK side** — The `one()` side that holds the foreign key column must specify `fields` and `references`. The other side does not.

2. **Not passing schema to `drizzle()`** — Relations only work with the relational query API, which requires `{ schema }` in the connection setup.

3. **Forgetting `relationName` with multiple relations** — If a table has two or more relations to the same target table, both sides must have matching `relationName` values.

4. **Relations are not foreign keys** — Declaring a relation does NOT create a foreign key constraint in the database. Add `.references()` separately if you want DB-level enforcement.

5. **Junction tables need relations on all three tables** — For many-to-many, you need relations on the source, target, AND junction tables.

---

**Related:** [Relational Queries](./07-relational-queries.md) | [Joins](./06-joins.md)
