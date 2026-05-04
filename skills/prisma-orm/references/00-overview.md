# Prisma ORM — Overview & Setup

> Source: [prisma.io/docs](https://www.prisma.io/docs) — Prisma ORM v7.x

## Table of Contents

- [What Is Prisma](#what-is-prisma)
- [Core Components](#core-components)
- [Supported Databases](#supported-databases)
- [Installation (Prisma 7)](#installation-prisma-7)
- [Project Initialization](#project-initialization)
- [Driver Adapters (Prisma 7)](#driver-adapters-prisma-7)
- [Schema Basics](#schema-basics)
- [Generating the Client](#generating-the-client)
- [Instantiating PrismaClient](#instantiating-prismaclient)
- [First Query](#first-query)
- [Prisma vs Alternatives](#prisma-vs-alternatives)
- [Common Pitfalls](#common-pitfalls)

---

## What Is Prisma

Prisma ORM is a next-generation Node.js and TypeScript ORM that replaces traditional ORMs and raw SQL with a type-safe, declarative approach to database access. It provides:

- **Type-safe queries** validated at compile time with full autocompletion
- **Declarative schema** as a single source of truth for your data model
- **Automated migrations** that evolve your database safely
- **Plain JavaScript objects** returned from queries — no model instances

## Core Components

| Component | Purpose |
|-----------|---------|
| **Prisma Schema** | Declarative data model definition (`.prisma` files) |
| **Prisma Client** | Auto-generated, type-safe query builder |
| **Prisma Migrate** | Database migration system based on schema diffs |
| **Prisma Studio** | Visual GUI for browsing and editing data |
| **Prisma CLI** | Command-line tools for generate, migrate, db push, introspect |

## Supported Databases

| Database | Provider | Status |
|----------|----------|--------|
| PostgreSQL | `postgresql` | Full support |
| MySQL | `mysql` | Full support |
| MariaDB | `mysql` | Full support |
| SQLite | `sqlite` | Full support |
| SQL Server | `sqlserver` | Full support |
| MongoDB | `mongodb` | Full support |
| CockroachDB | `cockroachdb` | Full support |
| PlanetScale | `mysql` | Via driver adapter |

## Installation (Prisma 7)

Prisma 7 requires driver adapters. Install based on your database:

```bash
# PostgreSQL
npm install prisma --save-dev
npm install @prisma/client @prisma/adapter-pg pg

# MySQL
npm install prisma --save-dev
npm install @prisma/client @prisma/adapter-mysql2 mysql2

# SQLite
npm install prisma --save-dev
npm install @prisma/client @prisma/adapter-better-sqlite3 better-sqlite3

# MongoDB
npm install prisma --save-dev
npm install @prisma/client @prisma/adapter-mongodb mongodb
```

**ESM requirement**: Your `package.json` must include `"type": "module"` for Prisma 7.

## Project Initialization

```bash
# Initialize with PostgreSQL (default)
npx prisma init

# Initialize with specific database
npx prisma init --datasource-provider mysql
npx prisma init --datasource-provider sqlite
npx prisma init --datasource-provider mongodb

# Bootstrap (Prisma 7) — interactive full setup
npx prisma bootstrap
```

This creates:
- `prisma/schema.prisma` — your data model
- `prisma/config.ts` — Prisma configuration (v7)
- `.env` — environment variables with `DATABASE_URL`

## Driver Adapters (Prisma 7)

Prisma 7 uses native Node.js database drivers instead of the Rust query engine:

```typescript
// prisma/schema.prisma
datasource db {
  provider = "postgresql"
}

generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"
}
```

```typescript
// src/db.ts — PostgreSQL adapter
import { PrismaClient } from "./generated/prisma/index.js";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
});

export const prisma = new PrismaClient({ adapter });
```

### Adapter Configuration Options

```typescript
// PostgreSQL with pool tuning
const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
  connectionTimeoutMillis: 5_000,
  idleTimeoutMillis: 300_000,
  max: 20,
});

// MySQL
import { PrismaMysql2 } from "@prisma/adapter-mysql2";
const adapter = new PrismaMysql2({
  connectionString: process.env.DATABASE_URL,
});

// SQLite
import { PrismaBetterSQLite3 } from "@prisma/adapter-better-sqlite3";
const adapter = new PrismaBetterSQLite3({ url: "file:./dev.db" });
```

## Schema Basics

A minimal Prisma schema with models:

```prisma
datasource db {
  provider = "postgresql"
}

generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"
}

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  author    User     @relation(fields: [authorId], references: [id])
  authorId  Int
  createdAt DateTime @default(now())
}
```

## Generating the Client

```bash
# Generate after any schema change
npx prisma generate

# Generate without engine (for serverless/edge)
npx prisma generate --no-engine
```

The generated client must be imported from the configured output path.

## Instantiating PrismaClient

```typescript
// Singleton pattern (recommended)
import { PrismaClient } from "./generated/prisma/index.js";
import { PrismaPg } from "@prisma/adapter-pg";

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
});

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ?? new PrismaClient({ adapter });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
```

### Logging Configuration

```typescript
const prisma = new PrismaClient({
  adapter,
  log: ["query", "info", "warn", "error"],
});

// Event-based logging
const prisma = new PrismaClient({
  adapter,
  log: [{ emit: "event", level: "query" }],
});

prisma.$on("query", (e) => {
  console.log(`Query: ${e.query} — Duration: ${e.duration}ms`);
});
```

## First Query

```typescript
import { prisma } from "./db.js";

async function main() {
  // Create a user
  const user = await prisma.user.create({
    data: {
      email: "alice@prisma.io",
      name: "Alice",
      posts: {
        create: { title: "Hello World", published: true },
      },
    },
    include: { posts: true },
  });

  console.log(user);

  // Query all users
  const allUsers = await prisma.user.findMany({
    include: { posts: true },
  });

  console.log(allUsers);
}

main()
  .then(() => prisma.$disconnect())
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
```

## Prisma vs Alternatives

| Feature | Prisma | Drizzle | TypeORM | Knex |
|---------|--------|---------|---------|------|
| Type safety | Full (generated) | Full (schema) | Partial | Manual |
| Schema definition | Prisma Schema Language | TypeScript | Decorators/Entities | None (query builder) |
| Migrations | Built-in | Built-in | Built-in | Built-in |
| Query style | Method chaining | SQL-like | Active Record/Data Mapper | SQL-like |
| Learning curve | Low | Medium | Medium | Low |
| Raw SQL escape | Easy | Native | Moderate | Native |
| Edge/serverless | Via Accelerate | Native | Limited | Limited |

**Choose Prisma when**: You want maximum type safety, prefer declarative schema, need integrated migrations, and value developer experience over raw SQL control.

**Consider alternatives when**: You need SQL-first queries (Drizzle), decorator-based entities (TypeORM), or a lightweight query builder (Knex).

## Common Pitfalls

1. **Multiple PrismaClient instances** — Always use a singleton pattern; multiple instances exhaust connection pools
2. **Forgetting `prisma generate`** — After schema changes, always regenerate the client before using new models
3. **Missing `"type": "module"`** — Prisma 7 requires ESM; add to `package.json`
4. **Connection string in source** — Always use environment variables via `env("DATABASE_URL")`
5. **Not disconnecting** — Call `prisma.$disconnect()` in scripts and serverless handlers
6. **Schema drift** — Always use `prisma migrate dev` in development; never edit migration SQL unless customizing
