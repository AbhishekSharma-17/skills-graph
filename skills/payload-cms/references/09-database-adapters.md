# Database Adapters

> Source: https://payloadcms.com/docs/database/overview

## Overview

Payload uses a database adapter pattern to support multiple databases. The adapter abstracts all database operations, so your collections, fields, hooks, and access control work identically regardless of which database you choose.

Supported adapters:
- **MongoDB** — `@payloadcms/db-mongodb` (uses Mongoose)
- **PostgreSQL** — `@payloadcms/db-postgres` (uses Drizzle ORM + node-postgres)
- **SQLite** — `@payloadcms/db-sqlite` (uses Drizzle ORM + better-sqlite3)

## MongoDB Adapter

Best for: rapid prototyping, flexible schemas, existing MongoDB infrastructure.

```bash
npm install @payloadcms/db-mongodb
```

```typescript
import { buildConfig } from 'payload'
import { mongooseAdapter } from '@payloadcms/db-mongodb'

export default buildConfig({
  db: mongooseAdapter({
    url: process.env.DATABASE_URI!,
    // Optional configuration
    connectOptions: {
      dbName: 'my-app',
    },
    migrationDir: './migrations',
    transactionOptions: false,  // Disable transactions (for shared clusters)
  }),
  // ...
})
```

### MongoDB Considerations

- No migrations needed for schema changes (schemaless)
- Automatic indexing based on field config
- Supports transactions (requires replica set)
- Rich text and JSON fields stored natively as BSON
- Best query performance for deeply nested/polymorphic data (blocks, arrays)

## PostgreSQL Adapter

Best for: production applications, ACID compliance, complex queries, existing Postgres infrastructure.

```bash
npm install @payloadcms/db-postgres
```

```typescript
import { buildConfig } from 'payload'
import { postgresAdapter } from '@payloadcms/db-postgres'

export default buildConfig({
  db: postgresAdapter({
    pool: {
      connectionString: process.env.DATABASE_URI!,
      max: 10,
    },
    migrationDir: './migrations',
    push: false,              // Disable automatic schema push (use migrations)
    schemaName: 'public',
    idType: 'uuid',           // 'serial' | 'uuid' (default: serial)
  }),
  // ...
})
```

### Postgres Migrations

Schema changes require migrations with Postgres and SQLite:

```bash
# Generate migration from config changes
npx payload migrate:create

# Run pending migrations
npx payload migrate

# Check migration status
npx payload migrate:status

# Reset database (destructive)
npx payload migrate:reset

# Fresh migration (reset + migrate)
npx payload migrate:fresh
```

### Postgres Considerations

- Requires migrations for schema changes
- Full ACID transactions
- JSON fields stored as `jsonb` columns
- Relationship fields use foreign keys
- Better for complex relational queries
- Drizzle ORM provides type-safe query building

## SQLite Adapter

Best for: development, testing, small self-hosted apps, embedded use cases.

```bash
npm install @payloadcms/db-sqlite
```

```typescript
import { buildConfig } from 'payload'
import { sqliteAdapter } from '@payloadcms/db-sqlite'

export default buildConfig({
  db: sqliteAdapter({
    client: {
      url: process.env.DATABASE_URI!,  // file:./data.db or :memory:
    },
    migrationDir: './migrations',
    push: false,
  }),
  // ...
})
```

## Choosing a Database

| Factor | MongoDB | PostgreSQL | SQLite |
|--------|---------|------------|--------|
| Schema changes | No migrations needed | Requires migrations | Requires migrations |
| Transactions | Yes (replica set) | Yes (built-in) | Yes (limited) |
| Hosting | Atlas, self-hosted | Neon, Supabase, RDS | File-based |
| Scaling | Horizontal (sharding) | Vertical + read replicas | Single file |
| JSON queries | Native | jsonb operators | Limited |
| Best for | Flexible content, prototyping | Production apps | Dev/testing, small apps |

## Custom Database Access

Access the underlying database client for custom queries:

```typescript
// MongoDB — access Mongoose
const mongoose = payload.db.connection

// PostgreSQL — access Drizzle
const drizzle = payload.db.drizzle
const result = await drizzle.execute(sql`SELECT * FROM posts WHERE ...`)
```

## Indexing

Payload automatically creates indexes based on field configuration:

```typescript
{
  name: 'slug',
  type: 'text',
  unique: true,     // Creates unique index
  index: true,      // Creates standard index
}
```

For compound indexes or specialized indexes, use database-specific configuration or custom migrations.

## Connection Pooling

### MongoDB

```typescript
db: mongooseAdapter({
  url: process.env.DATABASE_URI,
  connectOptions: {
    maxPoolSize: 10,
    minPoolSize: 2,
  },
})
```

### PostgreSQL

```typescript
db: postgresAdapter({
  pool: {
    connectionString: process.env.DATABASE_URI,
    max: 20,         // Max connections in pool
    min: 2,          // Min connections
    idleTimeoutMillis: 30000,
  },
})
```

## Common Pitfalls

1. **MongoDB without replica set** — Transactions require a replica set. Use `transactionOptions: false` for standalone instances.
2. **Forgetting migrations with Postgres/SQLite** — Schema changes aren't applied automatically. Always run `npx payload migrate` after config changes.
3. **`push: true` in production** — Auto-pushing schema changes can cause data loss. Use migrations in production.
4. **Connection string format** — MongoDB uses `mongodb://` or `mongodb+srv://`, Postgres uses `postgresql://`, SQLite uses `file:` paths.
5. **SQLite concurrency** — SQLite has limited write concurrency. Not suitable for high-traffic production apps.
6. **Missing database indexes** — Add `index: true` to fields used in `where` clauses for better query performance.
