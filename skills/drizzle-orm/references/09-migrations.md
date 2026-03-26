# Drizzle ORM — Migrations

> Source: [orm.drizzle.team/docs/migrations](https://orm.drizzle.team/docs/migrations)

## Table of Contents

- [Overview](#overview)
- [Configuration](#configuration)
- [Migration Commands](#migration-commands)
- [Generate Migrations](#generate-migrations)
- [Apply Migrations](#apply-migrations)
- [Push (No Migration Files)](#push-no-migration-files)
- [Pull (Introspect Database)](#pull-introspect-database)
- [Runtime Migrations](#runtime-migrations)
- [Migration Workflows](#migration-workflows)
- [Custom Migration Scripts](#custom-migration-scripts)
- [Drizzle Studio](#drizzle-studio)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Drizzle Kit is the CLI companion to Drizzle ORM that handles schema migrations. It supports two philosophies:

1. **Codebase-first** — Define schema in TypeScript, generate SQL migrations, apply to database
2. **Database-first** — Pull existing schema from database into TypeScript files

## Configuration

Create `drizzle.config.ts` in your project root:

```typescript
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  // Required
  dialect: 'postgresql',              // 'postgresql' | 'mysql' | 'sqlite' | 'turso'
  schema: './src/db/schema.ts',       // Path to schema file(s)

  // Optional
  out: './drizzle',                   // Migration output directory (default: ./drizzle)
  dbCredentials: {
    url: process.env.DATABASE_URL!,   // Connection string
  },

  // Advanced
  verbose: true,                      // Show SQL in generate output
  strict: true,                       // Prompt for confirmations on destructive changes
  tablesFilter: ['users', 'posts'],   // Only track specific tables
  schemaFilter: ['public'],           // PostgreSQL schema filter
});
```

### Multiple schema files

```typescript
export default defineConfig({
  schema: './src/db/schema/*.ts',     // Glob pattern
  // or
  schema: ['./src/db/users.ts', './src/db/posts.ts'],
});
```

### Turso / LibSQL specific

```typescript
export default defineConfig({
  dialect: 'turso',
  schema: './src/db/schema.ts',
  dbCredentials: {
    url: process.env.TURSO_DATABASE_URL!,
    authToken: process.env.TURSO_AUTH_TOKEN!,
  },
});
```

## Migration Commands

```bash
# Generate SQL migration files from schema changes
npx drizzle-kit generate

# Apply generated SQL migrations to database
npx drizzle-kit migrate

# Push schema directly to database (no migration files)
npx drizzle-kit push

# Pull database schema into TypeScript files
npx drizzle-kit pull

# Check migration consistency
npx drizzle-kit check

# Export schema as SQL (for external tools)
npx drizzle-kit export

# Launch visual database browser
npx drizzle-kit studio
```

## Generate Migrations

Compares your current schema against the previous snapshot and generates SQL migration files:

```bash
npx drizzle-kit generate
```

Output structure:

```
drizzle/
├── 0000_initial.sql          # First migration
├── 0001_add_posts_table.sql  # Subsequent migrations
├── 0002_add_indexes.sql
└── meta/
    ├── 0000_snapshot.json    # Schema snapshot per migration
    ├── 0001_snapshot.json
    ├── 0002_snapshot.json
    └── _journal.json         # Migration order tracking
```

### What generate detects

- New tables
- Dropped tables
- Added/removed/modified columns
- Changed defaults, types, nullability
- Added/removed indexes and constraints
- Enum changes

### Rename detection

When you rename a column or table, Drizzle Kit prompts you to confirm whether it's a rename or a drop+create:

```
Is 'old_name' column in 'users' table renamed to 'new_name'? (y/N)
```

## Apply Migrations

### CLI method

```bash
npx drizzle-kit migrate
```

Applies all pending migrations in order. Tracks applied migrations in a `__drizzle_migrations` table.

### Runtime method

Apply migrations programmatically at app startup:

```typescript
import { drizzle } from 'drizzle-orm/postgres-js';
import { migrate } from 'drizzle-orm/postgres-js/migrator';

const db = drizzle(connectionString);

await migrate(db, { migrationsFolder: './drizzle' });
```

## Push (No Migration Files)

Directly applies schema to database without generating SQL files. Ideal for prototyping:

```bash
npx drizzle-kit push
```

Push vs Generate+Migrate:
- **Push** — Fast iteration, no migration history, great for prototyping
- **Generate+Migrate** — Production-ready, version-controlled, team-friendly

## Pull (Introspect Database)

Generate TypeScript schema from an existing database:

```bash
npx drizzle-kit pull
```

Creates `schema.ts` file with table definitions matching your database structure. Useful for:
- Adopting Drizzle on an existing project
- Syncing after manual database changes
- Generating types from a legacy database

## Runtime Migrations

### PostgreSQL

```typescript
import { drizzle } from 'drizzle-orm/postgres-js';
import { migrate } from 'drizzle-orm/postgres-js/migrator';

const db = drizzle(process.env.DATABASE_URL!);
await migrate(db, { migrationsFolder: './drizzle' });
```

### MySQL

```typescript
import { drizzle } from 'drizzle-orm/mysql2';
import { migrate } from 'drizzle-orm/mysql2/migrator';

const db = drizzle(process.env.DATABASE_URL!);
await migrate(db, { migrationsFolder: './drizzle' });
```

### SQLite

```typescript
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { migrate } from 'drizzle-orm/better-sqlite3/migrator';

const db = drizzle('sqlite.db');
migrate(db, { migrationsFolder: './drizzle' });
```

### Turso

```typescript
import { drizzle } from 'drizzle-orm/libsql';
import { migrate } from 'drizzle-orm/libsql/migrator';

const db = drizzle({ connection: { url, authToken } });
await migrate(db, { migrationsFolder: './drizzle' });
```

## Migration Workflows

### Recommended production workflow

```bash
# 1. Make schema changes in TypeScript
# 2. Generate migration
npx drizzle-kit generate

# 3. Review the generated SQL
cat drizzle/0003_my_change.sql

# 4. Test migration locally
npx drizzle-kit migrate

# 5. Commit schema + migration files
git add src/db/schema.ts drizzle/
git commit -m "feat: add posts table"

# 6. CI/CD applies migration in staging/production
# (use runtime migrate() or drizzle-kit migrate)
```

### Rapid prototyping workflow

```bash
# 1. Edit schema
# 2. Push directly
npx drizzle-kit push
# 3. Repeat until schema is stable
# 4. Switch to generate+migrate for production
```

## Custom Migration Scripts

You can write custom SQL in migration files:

```sql
-- drizzle/0004_custom.sql
-- Custom: Backfill data
UPDATE users SET role = 'user' WHERE role IS NULL;

-- Custom: Create materialized view
CREATE MATERIALIZED VIEW user_stats AS
SELECT role, count(*) as count FROM users GROUP BY role;
```

Add the file to the `meta/_journal.json` to include it in the migration sequence.

## Drizzle Studio

Visual database browser and editor:

```bash
npx drizzle-kit studio
```

Opens a web interface (default: https://local.drizzle.studio) where you can:
- Browse table data
- Edit rows inline
- Run custom SQL queries
- View schema visually

## Common Pitfalls

1. **Always review generated SQL** — `drizzle-kit generate` may produce destructive operations (column drops, type changes). Review before applying.

2. **Don't edit migration files after applying** — Once a migration is applied, treat it as immutable. Create new migrations for changes.

3. **Commit the `meta/` directory** — The snapshots in `drizzle/meta/` are needed for future diff generation. Always commit them.

4. **Push overwrites without history** — `drizzle-kit push` doesn't create migration files. It can cause data loss if it drops columns. Use only for development.

5. **Connection string in config** — Use environment variables (`process.env.DATABASE_URL`) in `drizzle.config.ts`, never hardcode credentials.

6. **Migration order matters** — Migrations are applied in filename order (0000, 0001, ...). Don't manually rename files.

---

**Related:** [Overview & Setup](./00-overview.md) | [Schema Declaration](./01-schema-declaration.md)
