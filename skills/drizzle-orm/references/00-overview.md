# Drizzle ORM — Overview & Setup

> Source: [orm.drizzle.team](https://orm.drizzle.team) | Version: 0.45.1 | License: Apache 2.0

## Table of Contents

- [What Is Drizzle ORM](#what-is-drizzle-orm)
- [Key Features](#key-features)
- [Installation](#installation)
- [Database Drivers](#database-drivers)
- [Connection Setup](#connection-setup)
- [Drizzle Kit Setup](#drizzle-kit-setup)
- [Project Structure](#project-structure)
- [Quick Start Example](#quick-start-example)
- [Common Pitfalls](#common-pitfalls)

---

## What Is Drizzle ORM

Drizzle ORM is a headless, TypeScript-first SQL ORM with zero dependencies (~31KB). It provides two query APIs:

1. **SQL-like API** — Mirrors SQL syntax in TypeScript (`select`, `insert`, `update`, `delete`)
2. **Relational Queries API** — Object-based nested data fetching (similar to Prisma's `include`)

Philosophy: Drizzle embraces SQL rather than abstracting it away. You write TypeScript that maps directly to the SQL you'd write by hand, with full type inference from schema to query results.

## Key Features

- **Zero dependencies** — Lightweight, serverless-ready
- **Full TypeScript inference** — Schema → queries → results, all type-safe
- **Multi-dialect** — PostgreSQL, MySQL, SQLite, SingleStore, MSSQL
- **Multi-runtime** — Node.js, Bun, Deno, Cloudflare Workers, Vercel Edge
- **Drizzle Kit** — CLI for migrations, schema generation, and DB studio
- **Dual query API** — SQL-like and relational, choose per query
- **Serverless-optimized** — Built for Neon, PlanetScale, Turso, D1, Vercel Postgres

## Installation

```bash
# Core ORM package
npm install drizzle-orm

# Dev tooling (migrations, studio)
npm install -D drizzle-kit
```

Package manager alternatives:

```bash
pnpm add drizzle-orm && pnpm add -D drizzle-kit
yarn add drizzle-orm && yarn add -D drizzle-kit
bun add drizzle-orm && bun add -D drizzle-kit
```

## Database Drivers

Install the driver matching your database:

### PostgreSQL

```bash
# postgres.js (recommended)
npm install postgres

# node-postgres (pg)
npm install pg
npm install -D @types/pg

# Neon Serverless
npm install @neondatabase/serverless

# Vercel Postgres
npm install @vercel/postgres

# Supabase
npm install postgres  # uses postgres.js under the hood

# PGlite (in-browser/embedded)
npm install @electric-sql/pglite
```

### MySQL

```bash
# mysql2 (recommended)
npm install mysql2

# PlanetScale Serverless
npm install @planetscale/database
```

### SQLite

```bash
# better-sqlite3 (Node.js)
npm install better-sqlite3
npm install -D @types/better-sqlite3

# Turso / LibSQL
npm install @libsql/client

# Bun SQLite (built-in, no install needed)

# Cloudflare D1 (uses Workers runtime, no install needed)
```

## Connection Setup

### PostgreSQL with postgres.js

```typescript
import { drizzle } from 'drizzle-orm/postgres-js';

const db = drizzle('postgresql://user:password@host:5432/dbname');
```

### PostgreSQL with node-postgres

```typescript
import { drizzle } from 'drizzle-orm/node-postgres';

const db = drizzle('postgresql://user:password@host:5432/dbname');
```

### Neon Serverless

```typescript
import { drizzle } from 'drizzle-orm/neon-http';

const db = drizzle(process.env.DATABASE_URL!);
```

### MySQL with mysql2

```typescript
import { drizzle } from 'drizzle-orm/mysql2';

const db = drizzle('mysql://user:password@host:3306/dbname');
```

### SQLite with better-sqlite3

```typescript
import { drizzle } from 'drizzle-orm/better-sqlite3';

const db = drizzle('sqlite.db');
```

### Turso / LibSQL

```typescript
import { drizzle } from 'drizzle-orm/libsql';

const db = drizzle({
  connection: {
    url: process.env.TURSO_DATABASE_URL!,
    authToken: process.env.TURSO_AUTH_TOKEN!,
  },
});
```

### Passing Schema for Relational Queries

```typescript
import * as schema from './schema';
import { drizzle } from 'drizzle-orm/postgres-js';

const db = drizzle('postgresql://...', { schema });

// Now db.query.* is available
await db.query.users.findMany();
```

## Drizzle Kit Setup

Create `drizzle.config.ts` in your project root:

```typescript
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  dialect: 'postgresql',  // 'postgresql' | 'mysql' | 'sqlite' | 'turso'
  schema: './src/db/schema.ts',
  out: './drizzle',  // migration output directory
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

Common commands:

```bash
# Generate migration from schema changes
npx drizzle-kit generate

# Push schema directly to database (prototyping)
npx drizzle-kit push

# Apply generated migrations
npx drizzle-kit migrate

# Pull existing DB schema into TypeScript
npx drizzle-kit pull

# Launch Drizzle Studio (GUI)
npx drizzle-kit studio
```

## Project Structure

Recommended layout for a Drizzle project:

```
src/
├── db/
│   ├── schema.ts        # All table definitions
│   ├── relations.ts     # Relations declarations
│   ├── index.ts         # Database connection + export db instance
│   └── migrate.ts       # Runtime migration script (optional)
├── ...
drizzle/
├── 0000_initial.sql     # Generated migration files
├── 0001_add_posts.sql
└── meta/                # Migration metadata (auto-generated)
drizzle.config.ts        # Drizzle Kit configuration
```

For larger projects, split schema across files:

```typescript
// src/db/schema/users.ts
export const users = pgTable('users', { ... });

// src/db/schema/posts.ts
export const posts = pgTable('posts', { ... });

// src/db/schema/index.ts
export * from './users';
export * from './posts';
```

## Quick Start Example

```typescript
// 1. Define schema (src/db/schema.ts)
import { pgTable, serial, text, integer, timestamp } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  age: integer('age'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// 2. Connect (src/db/index.ts)
import { drizzle } from 'drizzle-orm/postgres-js';
import * as schema from './schema';

export const db = drizzle(process.env.DATABASE_URL!, { schema });

// 3. Query
import { eq } from 'drizzle-orm';
import { db } from './db';
import { users } from './db/schema';

// Insert
await db.insert(users).values({
  name: 'Alice',
  email: 'alice@example.com',
  age: 30,
});

// Select
const allUsers = await db.select().from(users);

// Filter
const alice = await db.select().from(users).where(eq(users.email, 'alice@example.com'));

// Update
await db.update(users).set({ age: 31 }).where(eq(users.name, 'Alice'));

// Delete
await db.delete(users).where(eq(users.name, 'Alice'));
```

## Common Pitfalls

1. **Forgetting to pass schema to `drizzle()`** — Without `{ schema }`, the relational query API (`db.query.*`) is not available. Always pass schema if using relational queries.

2. **Using `serial` for new projects** — Prefer `integer().generatedAlwaysAsIdentity()` over `serial()` for PostgreSQL identity columns. Serial is legacy.

3. **Not installing drizzle-kit as devDependency** — Drizzle Kit is only needed at dev/build time, not in production.

4. **Mixing up `push` and `migrate`** — Use `push` for rapid prototyping (no migration files). Use `generate` + `migrate` for production workflows with migration history.

5. **String vs Date mode for timestamps** — By default, timestamps return `Date` objects. Use `mode: 'string'` if you want ISO strings instead.

6. **BigInt type mismatch** — `bigint` columns default to JavaScript `bigint`. Use `mode: 'number'` if your values fit in a regular number.

---

**Related:** [Schema Declaration](./01-schema-declaration.md) | [Migrations](./09-migrations.md)
