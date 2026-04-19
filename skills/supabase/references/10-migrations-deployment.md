# Supabase — Migrations & Deployment

> Source: https://supabase.com/docs/guides/deployment/managing-environments

## Migration Workflow

Supabase uses SQL migration files versioned in your git repository. The recommended workflow:

```
Local Dev → Feature Branch → PR → Staging → Production
```

### Creating Migrations

**Option 1: Manual SQL** (recommended for precision)

```bash
supabase migration new add_profiles_table
```

Write SQL directly:

```sql
-- supabase/migrations/20260419_add_profiles_table.sql
create table profiles (
  id uuid references auth.users(id) primary key,
  display_name text,
  avatar_url text,
  bio text,
  updated_at timestamptz default now()
);

alter table profiles enable row level security;

create policy "Public profiles"
  on profiles for select
  using (true);

create policy "Users update own profile"
  on profiles for update
  to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

-- Trigger to auto-create profile on user signup
create or replace function handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, new.raw_user_meta_data->>'display_name');
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();
```

**Option 2: Auto-diff** (fast iteration)

Make changes via Studio UI, then capture:

```bash
supabase db diff -f add_profiles_table
```

The auto-generated SQL is more verbose but comprehensive. Review before committing.

### Applying Migrations

```bash
# Locally: reset and re-apply all migrations
supabase db reset

# Remote: push pending migrations
supabase db push
```

### Migration Best Practices

1. **One concern per migration** — Don't mix table creation with data backfill.
2. **Idempotent when possible** — Use `if not exists`, `create or replace`.
3. **Never edit applied migrations** — Create a new migration to fix issues.
4. **Test with `db reset`** — Ensure all migrations apply cleanly from scratch.
5. **Include RLS policies** — Add policies in the same migration as the table.

## Environment Setup

### Recommended Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Local Dev  │ ──→ │   Staging   │ ──→ │  Production  │
│  (CLI/Docker)│     │  (Supabase) │     │  (Supabase)  │
└─────────────┘     └─────────────┘     └─────────────┘
       ↑                    ↑                    ↑
   supabase start     develop branch       main branch
```

### Setting Up Staging & Production

1. Create two Supabase projects (staging + production)
2. Link your local environment to staging for development
3. Use GitHub Actions (or similar CI) to deploy migrations

### GitHub Actions CI/CD

**Required GitHub Secrets:**

| Secret | Purpose |
|--------|---------|
| `SUPABASE_ACCESS_TOKEN` | CLI authentication |
| `STAGING_DB_PASSWORD` | Staging database password |
| `STAGING_PROJECT_ID` | Staging project reference |
| `PRODUCTION_DB_PASSWORD` | Production database password |
| `PRODUCTION_PROJECT_ID` | Production project reference |

**CI Workflow (test on PR):**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [develop, main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1
        with:
          version: latest

      - name: Start local Supabase
        run: supabase start

      - name: Verify migrations
        run: supabase db reset

      - name: Run tests
        run: npm test

      - name: Check types
        run: |
          supabase gen types typescript --local > src/database.types.ts
          npx tsc --noEmit
```

**Deploy to Staging (on push to develop):**

```yaml
# .github/workflows/staging.yml
name: Deploy to Staging

on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
      SUPABASE_DB_PASSWORD: ${{ secrets.STAGING_DB_PASSWORD }}
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1

      - name: Link to staging
        run: supabase link --project-ref ${{ secrets.STAGING_PROJECT_ID }}

      - name: Push migrations
        run: supabase db push

      - name: Deploy functions
        run: supabase functions deploy
```

**Deploy to Production (on push to main):**

```yaml
# .github/workflows/production.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
      SUPABASE_DB_PASSWORD: ${{ secrets.PRODUCTION_DB_PASSWORD }}
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1

      - name: Link to production
        run: supabase link --project-ref ${{ secrets.PRODUCTION_PROJECT_ID }}

      - name: Push migrations
        run: supabase db push

      - name: Deploy functions
        run: supabase functions deploy
```

## Branching (Preview Environments)

Supabase Branching creates ephemeral database instances for each PR:

```bash
# Enable branching for a project
supabase branches create preview/feature-xyz

# Branching is also available via Dashboard and GitHub integration
```

Each branch gets its own database, applies your migrations, and runs seed data — ideal for testing schema changes in isolation.

## Database Backups

Supabase automatically manages backups:

| Plan | Frequency | Retention |
|------|-----------|-----------|
| Free | Daily | 7 days |
| Pro | Daily | 14 days |
| Team | Daily + PITR | 14 days |
| Enterprise | Custom + PITR | Custom |

**Point-in-Time Recovery (PITR):** Restore to any second within the retention window. Available on Team and Enterprise plans.

Backups include schema and data but **not Storage API objects** (only metadata references).

## Deploying Edge Functions

```bash
# Deploy all functions
supabase functions deploy

# Deploy specific function
supabase functions deploy my-function

# Set secrets before deploying
supabase secrets set STRIPE_KEY=sk_live_xxx
```

## Rollback Strategy

There's no automatic rollback. Plan for it:

1. **Write reversible migrations** — Include a comment block with the rollback SQL:

```sql
-- Migration: add status column
alter table orders add column status text default 'pending';

-- ROLLBACK:
-- alter table orders drop column status;
```

2. **Test in staging first** — Always deploy to staging before production.
3. **Keep backups** — Download a backup before risky migrations.
4. **Use feature flags** — Decouple schema changes from application deployments.

## Common Pitfalls

1. **Making schema changes directly in production** — Always use migrations. Manual changes cause drift between environments.
2. **Not testing `db reset` before pushing** — If migrations don't apply cleanly from scratch, they'll fail in CI.
3. **Large data migrations in schema migrations** — Separate schema changes from data backfills. Schema migrations should be fast.
4. **Forgetting to deploy edge functions** — `db push` only handles migrations. Edge functions need separate `functions deploy`.
5. **Not setting secrets per environment** — Staging and production need different secrets. Don't share API keys between environments.
