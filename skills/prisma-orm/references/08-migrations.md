# Prisma Migrations

> Source: [prisma.io/docs/orm/prisma-migrate](https://www.prisma.io/docs/orm/prisma-migrate) — Prisma ORM v7.x

## Table of Contents

- [Migration Workflow](#migration-workflow)
- [CLI Commands](#cli-commands)
- [Development Migrations](#development-migrations)
- [Production Migrations](#production-migrations)
- [Customizing Migrations](#customizing-migrations)
- [Database Seeding](#database-seeding)
- [Baselining Existing Databases](#baselining-existing-databases)
- [Introspection](#introspection)
- [Prisma Config (v7)](#prisma-config-v7)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## Migration Workflow

```
Schema change → prisma migrate dev → SQL generated → Applied to dev DB
                                                          ↓
                              Commit migration files → prisma migrate deploy → Production DB
```

Migrations live in `prisma/migrations/` as timestamped directories containing `migration.sql` files.

```
prisma/
  migrations/
    20250101120000_init/
      migration.sql
    20250115090000_add_posts/
      migration.sql
    migration_lock.toml
  schema.prisma
```

## CLI Commands

| Command | Environment | Purpose |
|---------|-------------|---------|
| `prisma migrate dev` | Development | Create and apply migration |
| `prisma migrate deploy` | Production/CI | Apply pending migrations |
| `prisma migrate reset` | Development | Reset DB, apply all migrations, seed |
| `prisma migrate diff` | Any | Compare two schema states |
| `prisma migrate resolve` | Production | Mark migration as applied/rolled-back |
| `prisma db push` | Prototyping | Push schema changes without migration files |
| `prisma db pull` | Any | Introspect DB into schema |
| `prisma db seed` | Any | Run seed script |

## Development Migrations

### Creating a Migration

```bash
# Create migration from schema changes
npx prisma migrate dev --name add_user_profile

# Create migration without applying
npx prisma migrate dev --create-only --name add_indexes
```

This:
1. Diffs your schema against the migration history
2. Generates a SQL migration file
3. Applies the migration to your dev database
4. Regenerates Prisma Client

### Example Migration SQL

For this schema change:
```prisma
model User {
  id      Int      @id @default(autoincrement())
  email   String   @unique
  name    String?
  profile Profile?    // NEW
}

model Profile {        // NEW
  id     Int    @id @default(autoincrement())
  bio    String
  user   User   @relation(fields: [userId], references: [id])
  userId Int    @unique
}
```

Generated migration:
```sql
-- CreateTable
CREATE TABLE "Profile" (
    "id" SERIAL NOT NULL,
    "bio" TEXT NOT NULL,
    "userId" INTEGER NOT NULL,

    CONSTRAINT "Profile_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Profile_userId_key" ON "Profile"("userId");

-- AddForeignKey
ALTER TABLE "Profile" ADD CONSTRAINT "Profile_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "User"("id")
    ON DELETE RESTRICT ON UPDATE CASCADE;
```

### Reset Database

```bash
# Drop database, reapply all migrations, run seed
npx prisma migrate reset

# Skip seed
npx prisma migrate reset --skip-seed

# Force (skip confirmation)
npx prisma migrate reset --force
```

### db push (Prototyping)

```bash
# Push schema directly — no migration files
npx prisma db push

# Force reset if needed
npx prisma db push --force-reset
```

Use `db push` for:
- Early prototyping before you need migration history
- Rapid iteration on schema design
- Local development without migration overhead

Switch to `migrate dev` when:
- You need reproducible migrations
- Working with a team
- Preparing for production

## Production Migrations

### Deploying Migrations

```bash
# Apply all pending migrations (no new migrations created)
npx prisma migrate deploy
```

This command:
- Does NOT generate new migrations
- Does NOT trigger schema push
- Applies pending migrations in order
- Is safe for CI/CD pipelines

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Apply migrations
  run: npx prisma migrate deploy
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}

- name: Generate client
  run: npx prisma generate
```

### Migration Status

```bash
# Check which migrations have been applied
npx prisma migrate status
```

## Customizing Migrations

### Edit Before Applying

```bash
# Create migration without applying
npx prisma migrate dev --create-only --name rename_column

# Edit the generated SQL
# prisma/migrations/20250115_rename_column/migration.sql

# Then apply
npx prisma migrate dev
```

### Data Migrations

Add data transformations in the migration SQL:

```sql
-- prisma/migrations/20250115_split_name/migration.sql

-- Add new columns
ALTER TABLE "User" ADD COLUMN "firstName" TEXT;
ALTER TABLE "User" ADD COLUMN "lastName" TEXT;

-- Migrate data
UPDATE "User" SET
  "firstName" = split_part(name, ' ', 1),
  "lastName" = split_part(name, ' ', 2);

-- Make required
ALTER TABLE "User" ALTER COLUMN "firstName" SET NOT NULL;

-- Drop old column
ALTER TABLE "User" DROP COLUMN "name";
```

### Handling Breaking Changes

Adding a required field to a table with existing data:

```bash
# 1. Create migration with --create-only
npx prisma migrate dev --create-only --name add_required_role

# 2. Edit the SQL to add a default
```

```sql
-- Add column with default
ALTER TABLE "User" ADD COLUMN "role" TEXT NOT NULL DEFAULT 'USER';
```

## Database Seeding

### Configuration (Prisma 7)

```typescript
// prisma/config.ts
import "dotenv/config";
import { defineConfig, env } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
    seed: "tsx prisma/seed.ts",
  },
  datasource: {
    url: env("DATABASE_URL"),
  },
});
```

### Seed File

```typescript
// prisma/seed.ts
import "dotenv/config";
import { Pool } from "pg";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../src/generated/prisma/index.js";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const adapter = new PrismaPg(pool);
const prisma = new PrismaClient({ adapter });

async function main() {
  // Upsert to make seeds idempotent
  const admin = await prisma.user.upsert({
    where: { email: "admin@example.com" },
    update: {},
    create: {
      email: "admin@example.com",
      name: "Admin",
      role: "ADMIN",
      posts: {
        create: [
          { title: "Welcome", published: true },
          { title: "Getting Started", published: true },
        ],
      },
    },
  });

  console.log({ admin });
}

main()
  .then(async () => {
    await prisma.$disconnect();
    await pool.end();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    await pool.end();
    process.exit(1);
  });
```

### Running Seeds

```bash
# Run seed script
npx prisma db seed

# With custom arguments
npx prisma db seed -- --environment development
```

## Baselining Existing Databases

For adopting Prisma Migrate on an existing database:

```bash
# 1. Introspect your database
npx prisma db pull

# 2. Generate baseline migration (SQL only, don't apply)
npx prisma migrate diff \
  --from-empty \
  --to-schema prisma/schema.prisma \
  --script > prisma/migrations/0_init/migration.sql

# 3. Create the migration directory
mkdir -p prisma/migrations/0_init

# 4. Mark as already applied
npx prisma migrate resolve --applied 0_init

# 5. Future changes use normal workflow
npx prisma migrate dev --name next_change
```

## Introspection

Pull an existing database schema into Prisma:

```bash
# Generate/update schema from database
npx prisma db pull

# Force overwrite existing schema
npx prisma db pull --force
```

This updates your `schema.prisma` with models matching your database tables.

## Prisma Config (v7)

```typescript
// prisma/config.ts
import { defineConfig, env } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
    seed: "tsx prisma/seed.ts",
  },
  datasource: {
    url: env("DATABASE_URL"),
    directUrl: env("DIRECT_DATABASE_URL"),
  },
});
```

The `directUrl` is used for migrations when the primary URL goes through a connection pooler (like PgBouncer or Prisma Accelerate).

## Common Patterns

### Safe Column Rename

```bash
# 1. Add new column
npx prisma migrate dev --create-only --name add_display_name
# Edit: ALTER TABLE "User" ADD COLUMN "displayName" TEXT;
# Edit: UPDATE "User" SET "displayName" = "name";

# 2. Apply and update schema to use new column
npx prisma migrate dev

# 3. Drop old column in next migration
npx prisma migrate dev --name drop_old_name
```

### Adding Non-Null Column to Existing Table

```prisma
// Step 1: Add as optional
model User {
  role String?
}

// Step 2: Backfill in migration SQL
// UPDATE "User" SET role = 'USER' WHERE role IS NULL;

// Step 3: Make required
model User {
  role String @default("USER")
}
```

## Common Pitfalls

1. **Editing applied migrations** — Never edit a migration that's already been applied; create a new one
2. **Missing migration files** — Always commit `prisma/migrations/` to version control
3. **Schema drift** — Run `prisma migrate dev` regularly to keep schema and DB in sync
4. **Data loss warnings** — `migrate dev` warns about destructive operations; review before confirming
5. **Shadow database access** — `migrate dev` may need permission to create/drop a shadow database
6. **Seeding not automatic in v7** — Seeds only run via `npx prisma db seed`, not during `migrate dev`
