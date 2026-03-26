# Drizzle ORM — Indexes & Constraints

> Source: [orm.drizzle.team/docs/indexes-constraints](https://orm.drizzle.team/docs/indexes-constraints)

## Table of Contents

- [Overview](#overview)
- [Primary Keys](#primary-keys)
- [Composite Primary Keys](#composite-primary-keys)
- [Foreign Keys](#foreign-keys)
- [Unique Constraints](#unique-constraints)
- [Check Constraints](#check-constraints)
- [Indexes](#indexes)
- [PostgreSQL Index Features](#postgresql-index-features)
- [MySQL Index Features](#mysql-index-features)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Drizzle supports declaring constraints and indexes inline (on columns) or as table-level declarations in the third argument of the table builder function.

## Primary Keys

### Single Column

```typescript
// Inline
id: serial('id').primaryKey(),

// Or with identity (preferred for PostgreSQL)
id: integer('id').generatedAlwaysAsIdentity().primaryKey(),
```

### Composite Primary Keys

```typescript
import { pgTable, integer, primaryKey } from 'drizzle-orm/pg-core';

export const bookAuthors = pgTable('book_authors', {
  bookId: integer('book_id').notNull(),
  authorId: integer('author_id').notNull(),
}, (t) => [
  primaryKey({ columns: [t.bookId, t.authorId] }),
]);
```

With a custom constraint name:

```typescript
primaryKey({ name: 'book_author_pk', columns: [t.bookId, t.authorId] }),
```

## Foreign Keys

### Inline Foreign Keys

```typescript
import { pgTable, integer, serial, text } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
});

export const posts = pgTable('posts', {
  id: serial('id').primaryKey(),
  authorId: integer('author_id').references(() => users.id),
  title: text('title').notNull(),
});
```

### With Actions (CASCADE, SET NULL, etc.)

```typescript
authorId: integer('author_id').references(() => users.id, {
  onDelete: 'cascade',      // 'cascade' | 'restrict' | 'no action' | 'set null' | 'set default'
  onUpdate: 'no action',
}),
```

### Table-Level Foreign Keys

```typescript
import { pgTable, foreignKey, integer, serial } from 'drizzle-orm/pg-core';

export const posts = pgTable('posts', {
  id: serial('id').primaryKey(),
  authorId: integer('author_id').notNull(),
}, (t) => [
  foreignKey({
    name: 'posts_author_fk',
    columns: [t.authorId],
    foreignColumns: [users.id],
  }).onDelete('cascade'),
]);
```

### Composite Foreign Keys

```typescript
foreignKey({
  columns: [t.col1, t.col2],
  foreignColumns: [otherTable.id1, otherTable.id2],
}),
```

### Self-Referencing Foreign Keys

```typescript
export const categories = pgTable('categories', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
  parentId: integer('parent_id'),
}, (t) => [
  foreignKey({
    columns: [t.parentId],
    foreignColumns: [t.id],
  }),
]);
```

## Unique Constraints

### Single Column

```typescript
email: text('email').unique(),

// Named constraint
email: text('email').unique('users_email_unique'),
```

### Composite Unique

```typescript
import { pgTable, unique, text, integer } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  name: text('name').notNull(),
  orgId: integer('org_id').notNull(),
}, (t) => [
  unique('name_org_unique').on(t.name, t.orgId),
]);
```

### Partial Unique (PostgreSQL)

```typescript
unique('active_email_unique')
  .on(t.email)
  .where(sql`${t.isActive} = true`),
```

### Null Not Distinct (PostgreSQL)

```typescript
unique().on(t.email).nullsNotDistinct(),
```

## Check Constraints

```typescript
import { pgTable, integer, check } from 'drizzle-orm/pg-core';
import { sql } from 'drizzle-orm';

export const users = pgTable('users', {
  age: integer('age').notNull(),
  salary: integer('salary'),
}, (t) => [
  check('age_check', sql`${t.age} >= 18`),
  check('salary_positive', sql`${t.salary} > 0`),
]);
```

## Indexes

### Basic Indexes

```typescript
import { pgTable, index, uniqueIndex, text, integer } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  name: text('name').notNull(),
  email: text('email').notNull(),
  age: integer('age'),
}, (t) => [
  index('name_idx').on(t.name),
  uniqueIndex('email_idx').on(t.email),
]);
```

### Composite Indexes

```typescript
index('name_age_idx').on(t.name, t.age),
```

### Expression Indexes

```typescript
index('lower_email_idx').on(sql`lower(${t.email})`),
```

## PostgreSQL Index Features

```typescript
import { index } from 'drizzle-orm/pg-core';

// Specify algorithm
index('name_idx').using('btree', t.name),       // btree (default)
index('geo_idx').using('gist', t.location),      // GiST
index('search_idx').using('gin', t.searchVector), // GIN
index('hash_idx').using('hash', t.code),          // Hash

// Sort order
index('name_idx').on(t.name.asc()),
index('created_idx').on(t.createdAt.desc().nullsLast()),

// Partial index (WHERE clause)
index('active_users_idx')
  .on(t.name)
  .where(sql`${t.isActive} = true`),

// Concurrent creation
index('name_idx').on(t.name).concurrently(),
```

## MySQL Index Features

```typescript
import { index } from 'drizzle-orm/mysql-core';

// Specify algorithm
index('name_idx').on(t.name).using('btree'),

// Index hints in queries
await db.select().from(users, {
  useIndex: nameIdx,
});

await db.select().from(users, {
  forceIndex: emailIdx,
});

await db.select().from(users, {
  ignoreIndex: oldIdx,
});
```

## Common Pitfalls

1. **Table-level constraints use array syntax** — The third argument to `pgTable` must return an array `(t) => [...]`, not an object.

2. **Foreign key circular references** — Use lazy references `() => table.column` to avoid circular import issues.

3. **Index naming conflicts** — Always provide explicit names for indexes to avoid auto-generated name collisions during migrations.

4. **Check constraints with raw SQL** — Always use the `sql` template tag and reference columns via the table parameter to ensure proper escaping.

5. **Unique constraint vs unique index** — They are semantically equivalent in most databases, but `unique()` creates a constraint and `uniqueIndex()` creates an index. Use `unique()` for data integrity rules.

---

**Related:** [Schema Declaration](./01-schema-declaration.md) | [Foreign Keys & Relations](./03-relations.md)
