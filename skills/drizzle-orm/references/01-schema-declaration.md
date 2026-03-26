# Drizzle ORM — Schema Declaration

> Source: [orm.drizzle.team/docs/sql-schema-declaration](https://orm.drizzle.team/docs/sql-schema-declaration)

## Table of Contents

- [Overview](#overview)
- [PostgreSQL Tables](#postgresql-tables)
- [MySQL Tables](#mysql-tables)
- [SQLite Tables](#sqlite-tables)
- [Column Types — PostgreSQL](#column-types--postgresql)
- [Column Types — MySQL](#mysql-column-types)
- [Column Types — SQLite](#sqlite-column-types)
- [Column Modifiers](#column-modifiers)
- [Enums](#enums)
- [Default Values](#default-values)
- [Identity Columns](#identity-columns)
- [Generated Columns](#generated-columns)
- [Custom Types](#custom-types)
- [Type Inference](#type-inference)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Drizzle schemas are declared in TypeScript using dialect-specific table builders. Each table export becomes a queryable entity. Schemas serve as the single source of truth for types, migrations, and queries.

## PostgreSQL Tables

```typescript
import { pgTable, serial, text, integer, boolean, timestamp, uuid } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  age: integer('age'),
  isActive: boolean('is_active').default(true),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});
```

## MySQL Tables

```typescript
import { mysqlTable, serial, varchar, int, boolean, timestamp } from 'drizzle-orm/mysql-core';

export const users = mysqlTable('users', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 255 }).notNull(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  age: int('age'),
  isActive: boolean('is_active').default(true),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});
```

## SQLite Tables

```typescript
import { sqliteTable, integer, text } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  age: integer('age'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
});
```

## Column Types — PostgreSQL

### Numeric Types

```typescript
import {
  integer, smallint, bigint, serial, smallserial, bigserial,
  numeric, real, doublePrecision,
} from 'drizzle-orm/pg-core';

// Integers
id: integer('id'),                    // 4-byte signed
small: smallint('small'),             // 2-byte signed
big: bigint('big', { mode: 'number' }), // 8-byte, mode: 'number' | 'bigint'

// Auto-incrementing
id: serial('id'),                     // auto-increment 4-byte
bigId: bigserial('big_id', { mode: 'number' }), // auto-increment 8-byte

// Decimal
price: numeric('price', { precision: 10, scale: 2 }), // exact decimal
score: real('score'),                 // single precision float
value: doublePrecision('value'),      // double precision float
```

### Text Types

```typescript
import { text, varchar, char } from 'drizzle-orm/pg-core';

name: text('name'),                   // unlimited text
email: varchar('email', { length: 255 }), // variable length, optional limit
code: char('code', { length: 2 }),    // fixed length

// Enum-constrained text (TypeScript inference only, not DB enum)
role: text('role', { enum: ['admin', 'user', 'guest'] }),
```

### Date & Time

```typescript
import { timestamp, date, time, interval } from 'drizzle-orm/pg-core';

createdAt: timestamp('created_at'),                          // Date object
createdStr: timestamp('created_at', { mode: 'string' }),     // ISO string
withTz: timestamp('with_tz', { withTimezone: true }),        // timestamptz
precise: timestamp('precise', { precision: 3 }),             // milliseconds
birthday: date('birthday'),                                   // date only
startTime: time('start_time'),                                // time only
duration: interval('duration'),                                // interval
```

### JSON Types

```typescript
import { json, jsonb } from 'drizzle-orm/pg-core';

data: json('data'),                   // stored as text
config: jsonb('config'),              // stored as binary (indexable)

// Type-safe JSON with generics
metadata: jsonb('metadata').$type<{ theme: string; lang: string }>(),
```

### Other Types

```typescript
import { boolean, uuid, pgEnum } from 'drizzle-orm/pg-core';

isActive: boolean('is_active'),
id: uuid('id').defaultRandom(),       // auto-generate UUIDv4
```

## MySQL Column Types

```typescript
import {
  int, tinyint, smallint, mediumint, bigint,
  float, double, decimal,
  varchar, text, char,
  boolean, date, datetime, timestamp, time, year,
  json, binary, varbinary,
  mysqlEnum,
} from 'drizzle-orm/mysql-core';

// MySQL-specific enum
role: mysqlEnum('role', ['admin', 'user', 'guest']),

// Datetime with fractional seconds
createdAt: datetime('created_at', { fsp: 3 }),
```

## SQLite Column Types

```typescript
import { integer, text, real, blob } from 'drizzle-orm/sqlite-core';

// SQLite has 4 fundamental types; Drizzle maps modes:
id: integer('id'),                              // number
createdAt: integer('created_at', { mode: 'timestamp' }),  // Date via unix timestamp
isActive: integer('is_active', { mode: 'boolean' }),      // boolean (0/1)
amount: real('amount'),                          // floating point
data: blob('data', { mode: 'json' }),           // JSON stored as blob
raw: blob('data', { mode: 'buffer' }),          // raw Buffer
```

## Column Modifiers

```typescript
// Applicable to all dialects
column.notNull()              // NOT NULL constraint
column.default(value)         // Static default value
column.primaryKey()           // PRIMARY KEY
column.unique()               // UNIQUE constraint
column.$type<CustomType>()    // Override TypeScript type

// PostgreSQL specific
column.defaultRandom()        // gen_random_uuid()
column.generatedAlwaysAs(sql) // Generated column (ALWAYS)
```

## Enums

### PostgreSQL Native Enums

```typescript
import { pgEnum } from 'drizzle-orm/pg-core';

export const roleEnum = pgEnum('role', ['admin', 'user', 'guest']);

export const users = pgTable('users', {
  role: roleEnum('role').default('user').notNull(),
});
```

### MySQL Native Enums

```typescript
import { mysqlEnum } from 'drizzle-orm/mysql-core';

export const users = mysqlTable('users', {
  role: mysqlEnum('role', ['admin', 'user', 'guest']).notNull(),
});
```

## Default Values

```typescript
// Static defaults
age: integer('age').default(0),
role: text('role').default('user'),

// SQL expression defaults
createdAt: timestamp('created_at').defaultNow(),
id: uuid('id').defaultRandom(),

// Runtime defaults (executed in JS, not SQL)
id: text('id').$defaultFn(() => crypto.randomUUID()),

// On-update functions (for updated_at patterns)
updatedAt: timestamp('updated_at').$onUpdateFn(() => new Date()),
```

## Identity Columns

Preferred over `serial` for PostgreSQL:

```typescript
import { integer } from 'drizzle-orm/pg-core';

// GENERATED ALWAYS AS IDENTITY
id: integer('id').generatedAlwaysAsIdentity().primaryKey(),

// GENERATED BY DEFAULT AS IDENTITY (allows manual insert)
id: integer('id').generatedByDefaultAsIdentity().primaryKey(),

// With custom sequence options
id: integer('id').generatedAlwaysAsIdentity({
  startWith: 1000,
  increment: 1,
  minValue: 1000,
  maxValue: 999999,
  cache: 10,
}),
```

## Generated Columns

```typescript
import { sql } from 'drizzle-orm';

export const products = pgTable('products', {
  price: numeric('price').notNull(),
  quantity: integer('quantity').notNull(),
  total: numeric('total').generatedAlwaysAs(
    sql`${products.price} * ${products.quantity}`
  ),
});
```

## Custom Types

```typescript
import { customType } from 'drizzle-orm/pg-core';

const citext = customType<{ data: string }>({
  dataType() {
    return 'citext';
  },
});

export const users = pgTable('users', {
  email: citext('email').notNull(),
});
```

## Type Inference

```typescript
import { InferSelectModel, InferInsertModel } from 'drizzle-orm';

// Infer types from table definitions
type User = InferSelectModel<typeof users>;       // { id: number; name: string; ... }
type NewUser = InferInsertModel<typeof users>;     // { id?: number; name: string; ... }

// Or using $inferSelect / $inferInsert
type User = typeof users.$inferSelect;
type NewUser = typeof users.$inferInsert;
```

## Common Pitfalls

1. **Column name must match DB column** — The string argument (`'id'`, `'created_at'`) is the actual DB column name. The JS property name can differ.

2. **MySQL varchar requires length** — Unlike PostgreSQL `text`, MySQL `varchar` needs a `{ length }` option.

3. **SQLite has no native boolean** — Use `integer('col', { mode: 'boolean' })` which maps 0/1.

4. **JSON types have no runtime validation** — `$type<T>()` only provides compile-time safety. Use Drizzle's Zod integration for runtime validation.

5. **Enum changes require migrations** — Adding values to `pgEnum` needs a new migration. Reordering or removing values is destructive.

---

**Related:** [Indexes & Constraints](./02-indexes-constraints.md) | [Relations](./03-relations.md)
