# Supabase — CLI & Local Development

> Source: https://supabase.com/docs/guides/local-development/cli/getting-started

## Installing the CLI

```bash
# macOS / Linux (Homebrew)
brew install supabase/tap/supabase

# Windows (Scoop)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# npm (local dev dependency — requires Node.js 20+)
npm install supabase --save-dev

# Linux packages (.deb, .rpm, .apk)
# Download from https://github.com/supabase/cli/releases
```

Update:

```bash
brew upgrade supabase
# or
npm update supabase --save-dev
```

## Project Setup

### Initialize a New Project

```bash
supabase init
```

Creates a `supabase/` directory:

```
supabase/
├── config.toml          # Local dev configuration
├── migrations/          # SQL migration files
├── functions/           # Edge Functions
└── seed.sql             # Seed data (optional)
```

### Start Local Development Stack

```bash
supabase start
```

Downloads Docker images and starts all services:

| Service | URL | Purpose |
|---------|-----|---------|
| Studio | http://localhost:54323 | Dashboard UI |
| API (PostgREST) | http://localhost:54321 | REST/GraphQL API |
| Database | localhost:54322 | Direct Postgres access |
| Mailpit | http://localhost:54324 | Email testing inbox |
| Auth | http://localhost:54321/auth/v1 | GoTrue auth service |
| Storage | http://localhost:54321/storage/v1 | File storage API |
| Realtime | — | WebSocket connections |

### Stop Local Services

```bash
supabase stop              # Stop, keep data
supabase stop --no-backup  # Stop, delete all data
```

### Check Status

```bash
supabase status
```

Outputs all service URLs, anon key, service role key, and database URL.

## Linking to a Remote Project

```bash
# Login to Supabase
supabase login

# Link to your hosted project
supabase link --project-ref <project-ref>

# Find project-ref in Dashboard URL:
# https://supabase.com/dashboard/project/<project-ref>
```

## Database Migrations

### Create a Migration

```bash
# Create an empty migration file
supabase migration new create_todos_table
```

Edit the generated file in `supabase/migrations/`:

```sql
-- supabase/migrations/20260419120000_create_todos_table.sql
create table todos (
  id bigint generated always as identity primary key,
  title text not null,
  is_complete boolean default false,
  user_id uuid references auth.users(id),
  created_at timestamptz default now()
);

alter table todos enable row level security;

create policy "Users can CRUD own todos"
  on todos for all
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
```

### Auto-Generate Migration from Schema Changes

Make changes via Studio UI, then capture them:

```bash
# Diff local schema against migration files
supabase db diff -f add_priority_column

# Creates: supabase/migrations/20260419121000_add_priority_column.sql
```

### Apply Migrations Locally

```bash
supabase db reset  # Recreates database, runs all migrations + seed.sql
```

### Push Migrations to Remote

```bash
supabase db push
```

### Pull Remote Schema

```bash
# First-time: capture existing remote schema as a migration
supabase db pull
```

### List Migration Status

```bash
supabase migration list
```

## Seed Data

Create `supabase/seed.sql` for development data:

```sql
-- supabase/seed.sql
insert into auth.users (id, email)
values ('d0fc3c0e-8c5a-4e8b-b9f0-5e5b5e5e5e5e', 'test@example.com');

insert into todos (title, user_id)
values
  ('Learn Supabase', 'd0fc3c0e-8c5a-4e8b-b9f0-5e5b5e5e5e5e'),
  ('Build an app', 'd0fc3c0e-8c5a-4e8b-b9f0-5e5b5e5e5e5e');
```

Seed runs automatically after `supabase db reset`.

## Type Generation

```bash
# Generate TypeScript types from remote database
supabase gen types typescript --project-id <ref> > src/database.types.ts

# Generate from local database
supabase gen types typescript --local > src/database.types.ts
```

## Edge Functions Commands

```bash
# Create a new function
supabase functions new <function-name>

# Serve locally (hot-reload)
supabase functions serve

# Deploy to production
supabase functions deploy <function-name>
supabase functions deploy  # Deploy all

# Delete a function
supabase functions delete <function-name>
```

## Secrets Management

```bash
# Set secrets for edge functions
supabase secrets set KEY1=value1 KEY2=value2

# List secrets
supabase secrets list

# Remove secrets
supabase secrets unset KEY1 KEY2
```

## Configuration (config.toml)

Key settings in `supabase/config.toml`:

```toml
[project]
id = "<project-ref>"

[api]
port = 54321
schemas = ["public", "graphql_public"]
extra_search_path = ["public", "extensions"]
max_rows = 1000

[db]
port = 54322
major_version = 15

[auth]
site_url = "http://localhost:3000"
additional_redirect_urls = ["https://localhost:3000"]

[auth.email]
enable_signup = true
double_confirm_changes = true
enable_confirmations = false  # Disable for local dev

[storage]
file_size_limit = "50MiB"
```

## Testing Migrations

```bash
# Reset and verify all migrations apply cleanly
supabase db reset

# Run a specific test
supabase test db
```

## Useful Commands Reference

| Command | Purpose |
|---------|---------|
| `supabase init` | Initialize project |
| `supabase start` | Start local stack |
| `supabase stop` | Stop local stack |
| `supabase status` | Show service URLs and keys |
| `supabase login` | Authenticate CLI |
| `supabase link` | Link to remote project |
| `supabase db reset` | Reset local DB, run migrations + seed |
| `supabase db push` | Push migrations to remote |
| `supabase db pull` | Pull remote schema |
| `supabase db diff` | Generate migration from schema changes |
| `supabase migration new` | Create empty migration |
| `supabase migration list` | Show migration status |
| `supabase gen types` | Generate TypeScript types |
| `supabase functions new` | Create edge function |
| `supabase functions serve` | Serve functions locally |
| `supabase functions deploy` | Deploy functions |
| `supabase secrets set` | Set edge function secrets |
| `supabase inspect db` | Database inspection tools |
| `supabase telemetry disable` | Disable CLI telemetry |

## Common Pitfalls

1. **Docker not running** — `supabase start` requires Docker. Ensure Docker Desktop is running before starting.
2. **Port conflicts** — If ports 54321-54324 are in use, services won't start. Stop conflicting processes or change ports in `config.toml`.
3. **Forgetting `db reset` after editing migrations** — Editing existing migration files requires `db reset` to re-apply. New migrations at the end don't need a reset.
4. **Not pulling before pushing** — Always `supabase db pull` on a fresh clone to capture the remote schema before making changes.
5. **Local/remote schema drift** — Keep migrations in version control. Never make manual schema changes to production outside of migrations.
