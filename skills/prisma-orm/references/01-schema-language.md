# Prisma Schema Language

> Source: [prisma.io/docs/orm/prisma-schema](https://www.prisma.io/docs/orm/prisma-schema) — Prisma ORM v7.x

## Table of Contents

- [Schema Structure](#schema-structure)
- [Data Sources](#data-sources)
- [Generators](#generators)
- [Models](#models)
- [Scalar Types](#scalar-types)
- [Type Modifiers](#type-modifiers)
- [Field Attributes](#field-attributes)
- [Block Attributes](#block-attributes)
- [Enums](#enums)
- [Native Type Attributes](#native-type-attributes)
- [Composite Types (MongoDB)](#composite-types-mongodb)
- [Multi-File Schemas](#multi-file-schemas)
- [Common Patterns](#common-patterns)

---

## Schema Structure

Every Prisma schema has three sections: data source, generator(s), and data model.

```prisma
// 1. Data source — database connection
datasource db {
  provider = "postgresql"
}

// 2. Generator — what to generate
generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"
}

// 3. Data model — your tables/collections
model User {
  id    Int    @id @default(autoincrement())
  email String @unique
  name  String?
}
```

## Data Sources

Configures which database to connect to. Only one data source per schema.

```prisma
datasource db {
  provider = "postgresql"    // postgresql | mysql | sqlite | sqlserver | mongodb | cockroachdb
}
```

The connection URL is provided at runtime via the driver adapter in Prisma 7, or via `prisma.config.ts`.

## Generators

Controls what code gets generated. Multiple generators allowed.

```prisma
generator client {
  provider        = "prisma-client"
  output          = "../src/generated/prisma"
  previewFeatures = ["fullTextSearch"]
}
```

| Field | Purpose |
|-------|---------|
| `provider` | `"prisma-client"` for the standard client |
| `output` | Where to write generated files |
| `previewFeatures` | Opt-in to experimental features |
| `binaryTargets` | Target OS for engine binaries (pre-v7) |

## Models

Models map to database tables (SQL) or collections (MongoDB).

```prisma
model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int

  @@index([authorId])
  @@map("posts")
}
```

### Naming Conventions

- Model names: PascalCase, singular (e.g., `User`, `Post`, `Comment`)
- Field names: camelCase (e.g., `firstName`, `createdAt`)
- Use `@map` and `@@map` to map to snake_case database columns/tables

## Scalar Types

| Prisma Type | PostgreSQL | MySQL | SQLite | MongoDB |
|-------------|-----------|-------|--------|---------|
| `String` | `text` | `varchar(191)` | `TEXT` | `String` |
| `Boolean` | `boolean` | `tinyint(1)` | `INTEGER` | `Bool` |
| `Int` | `integer` | `int` | `INTEGER` | `Int` |
| `BigInt` | `bigint` | `bigint` | `INTEGER` | `Long` |
| `Float` | `double precision` | `double` | `REAL` | `Double` |
| `Decimal` | `decimal(65,30)` | `decimal(65,30)` | `REAL` | `Decimal128` |
| `DateTime` | `timestamp(3)` | `datetime(3)` | `NUMERIC` | `Timestamp` |
| `Json` | `jsonb` | `json` | — | `Object` |
| `Bytes` | `bytea` | `longblob` | `BLOB` | `BinData` |

## Type Modifiers

```prisma
model User {
  name     String    // required field
  bio      String?   // optional (nullable)
  tags     String[]  // list/array (not supported on SQLite)
}
```

| Modifier | Syntax | Meaning |
|----------|--------|---------|
| Optional | `Type?` | Field can be `null` |
| List | `Type[]` | Array of values |
| Required | `Type` | Must have a value (default) |

## Field Attributes

### @id — Primary Key

```prisma
model User {
  id   Int    @id @default(autoincrement())   // auto-incrementing integer
}

model Post {
  id   String @id @default(uuid())            // UUID primary key
}

model Event {
  id   String @id @default(cuid())            // CUID primary key
}
```

### @unique — Unique Constraint

```prisma
model User {
  email String @unique
  phone String @unique
}
```

### @default — Default Values

```prisma
model Post {
  id        Int      @id @default(autoincrement())
  uuid      String   @default(uuid())
  cuid      String   @default(cuid())
  active    Boolean  @default(true)
  role      Role     @default(USER)
  createdAt DateTime @default(now())
  data      Json     @default("[]")
}
```

Available functions: `autoincrement()`, `uuid()`, `cuid()`, `now()`, `dbgenerated("expression")`

### @updatedAt — Auto-Timestamp

```prisma
model Post {
  updatedAt DateTime @updatedAt   // automatically set on every update
}
```

### @map — Column Name Mapping

```prisma
model User {
  firstName String @map("first_name")   // column is "first_name" in DB
  lastName  String @map("last_name")
}
```

### @relation — Relationship Configuration

```prisma
model Post {
  author   User @relation(fields: [authorId], references: [id], onDelete: Cascade)
  authorId Int
}
```

### @ignore — Exclude from Client

```prisma
model User {
  id       Int    @id
  internal String @ignore   // field exists in DB but not in Prisma Client
}
```

## Block Attributes

Applied at the model level with `@@` prefix.

### @@id — Compound Primary Key

```prisma
model PostTag {
  postId Int
  tagId  Int

  @@id([postId, tagId])
}
```

### @@unique — Compound Unique Constraint

```prisma
model User {
  firstName String
  lastName  String
  email     String

  @@unique([firstName, lastName])
}
```

### @@index — Database Index

```prisma
model Post {
  id       Int    @id
  title    String
  authorId Int

  @@index([authorId])
  @@index([title, authorId])
}
```

#### Index Types (PostgreSQL)

```prisma
model Post {
  title   String
  content String

  @@index([title], type: Hash)
  @@index([title, content], type: GIN)     // for full-text search
  @@index([title], type: BTree)            // default
}
```

### @@map — Table Name Mapping

```prisma
model User {
  id Int @id

  @@map("users")   // table is "users" in DB, model is "User" in code
}
```

### @@ignore — Exclude Model from Client

```prisma
@@ignore
model LegacyTable {
  id Int @id
}
```

## Enums

```prisma
enum Role {
  USER
  ADMIN
  MODERATOR
}

model User {
  id   Int  @id @default(autoincrement())
  role Role @default(USER)
}
```

Usage in queries:

```typescript
import { Role } from "./generated/prisma/index.js";

await prisma.user.create({
  data: { email: "admin@example.com", role: Role.ADMIN },
});

await prisma.user.findMany({
  where: { role: Role.ADMIN },
});
```

## Native Type Attributes

Override the default database type mapping with `@db.*`:

```prisma
model Product {
  name        String  @db.VarChar(255)
  description String  @db.Text
  price       Decimal @db.Decimal(10, 2)
  sku         String  @db.Char(12)
  metadata    Json    @db.Json           // json instead of jsonb
}
```

### PostgreSQL Native Types

```prisma
model Example {
  varchar  String   @db.VarChar(100)
  text     String   @db.Text
  char     String   @db.Char(10)
  smallint Int      @db.SmallInt
  integer  Int      @db.Integer
  bigint   BigInt   @db.BigInt
  decimal  Decimal  @db.Decimal(10, 2)
  real     Float    @db.Real
  double   Float    @db.DoublePrecision
  ts       DateTime @db.Timestamp(3)
  tsz      DateTime @db.Timestamptz(3)
  date     DateTime @db.Date
  time     DateTime @db.Time
  bool     Boolean  @db.Boolean
  json     Json     @db.Json
  jsonb    Json     @db.JsonB
  bytes    Bytes    @db.ByteA
  uuid     String   @db.Uuid
  inet     String   @db.Inet
  citext   String   @db.Citext
}
```

## Composite Types (MongoDB)

Composite types define embedded documents in MongoDB:

```prisma
model Product {
  id      String  @id @default(auto()) @map("_id") @db.ObjectId
  name    String
  photos  Photo[]
  address Address
}

type Photo {
  url     String
  caption String?
  width   Int
  height  Int
}

type Address {
  street String
  city   String
  state  String
  zip    String
}
```

## Multi-File Schemas

Prisma supports splitting your schema across multiple `.prisma` files in the `prisma/schema/` directory:

```
prisma/
  schema/
    base.prisma       # datasource + generator
    user.prisma       # User model
    post.prisma       # Post model
    enums.prisma      # All enums
```

## Common Patterns

### Soft Deletes

```prisma
model Post {
  id        Int       @id @default(autoincrement())
  title     String
  deletedAt DateTime?

  @@index([deletedAt])
}
```

### Polymorphic Relations (Discriminator)

```prisma
model Notification {
  id   Int    @id @default(autoincrement())
  type String
  // Store the ID of the related entity
  entityId Int
  // Use type to determine which table to join
}
```

### Audit Timestamps

```prisma
// Common pattern: add to every model
model User {
  id        Int      @id @default(autoincrement())
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

### Database Views

```prisma
model UserWithPostCount {
  id        Int    @id
  name      String
  postCount Int

  @@map("user_post_counts")   // maps to a database view
  @@ignore                     // exclude from migrations
}
```
