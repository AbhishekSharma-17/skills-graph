# Supabase — Overview & Architecture

> Source: https://supabase.com/docs/guides/getting-started

## What Is Supabase

Supabase is an open-source Firebase alternative that gives every project a full PostgreSQL database plus managed services for authentication, file storage, real-time subscriptions, edge functions, and vector search. Unlike Firebase, Supabase uses standard Postgres — you get full `postgres` access, can use any Postgres tool, and are never locked in.

## When to Use Supabase

- Full-stack web/mobile apps needing auth, database, and file storage in one platform
- Real-time collaborative apps (chat, presence, live dashboards)
- AI applications requiring vector search alongside relational data
- Rapid prototyping where a managed backend accelerates development
- Projects that need Row Level Security for multi-tenant data isolation

## Architecture

Supabase composes several open-source tools behind a unified API:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Database** | PostgreSQL | Primary data store — full Postgres with extensions |
| **Auth** | GoTrue (Go) | JWT-based authentication, OAuth, MFA, SSO |
| **REST API** | PostgREST (Haskell) | Auto-generates RESTful API from database schema |
| **GraphQL** | pg_graphql (SQL) | GraphQL layer via Postgres extension |
| **Realtime** | Realtime Server (Elixir) | WebSocket broadcast, presence, Postgres changes |
| **Storage** | Storage API (Node.js) | S3-compatible object storage with Postgres metadata |
| **Edge Functions** | Deno runtime | Globally distributed serverless TypeScript functions |
| **Studio** | Dashboard (TypeScript) | Open-source admin UI for managing everything |
| **API Gateway** | Kong | Routes requests, handles rate limiting |
| **Connection Pooling** | Supavisor | Multi-tenant Postgres connection pooler |
| **DB Management** | postgres-meta | RESTful API for Postgres admin operations |

Every component can run standalone or together. The platform is designed for portability — you can self-host the entire stack.

## Quickstart

### 1. Create a Project

Sign up at [supabase.com/dashboard](https://supabase.com/dashboard), create a new project, and note your **Project URL** and **anon key** from Settings → API.

### 2. Install the Client Library

```bash
# JavaScript/TypeScript
npm install @supabase/supabase-js

# Python
pip install supabase

# Flutter
flutter pub add supabase_flutter
```

### 3. Initialize the Client

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://<project-ref>.supabase.co',
  '<anon-key>'
)
```

```python
from supabase import create_client

supabase = create_client(
    "https://<project-ref>.supabase.co",
    "<anon-key>"
)
```

### 4. Create a Table (via SQL Editor or Dashboard)

```sql
create table todos (
  id bigint generated always as identity primary key,
  title text not null,
  is_complete boolean default false,
  user_id uuid references auth.users(id),
  created_at timestamptz default now()
);

alter table todos enable row level security;

create policy "Users can read own todos"
  on todos for select
  using ((select auth.uid()) = user_id);
```

### 5. Query from Your App

```typescript
const { data, error } = await supabase
  .from('todos')
  .select('*')
  .eq('is_complete', false)
  .order('created_at', { ascending: false })
```

```python
response = supabase.table("todos") \
    .select("*") \
    .eq("is_complete", False) \
    .order("created_at", desc=True) \
    .execute()
```

## Project Credentials

Every Supabase project provides these keys (Settings → API):

| Key | Purpose | Exposed to Client? |
|-----|---------|-------------------|
| `anon` (publishable) | Public API access, respects RLS | Yes |
| `service_role` | Bypasses RLS, full admin access | **Never** expose to client |
| Project URL | API base URL (`https://<ref>.supabase.co`) | Yes |
| DB connection string | Direct Postgres access | Server-side only |

The `anon` key is safe to embed in client code because RLS policies control what data each user can access. The `service_role` key must only be used server-side.

## Framework Quickstarts

Supabase provides official quickstart guides for:

- **Web:** React, Next.js, Vue, Nuxt, Svelte, SvelteKit, Angular, Solid, Astro, Hono
- **Mobile:** Flutter, React Native (Expo), iOS (Swift), Android (Kotlin)
- **Backend:** Python, RedwoodJS, Refine

Each follows the same pattern: install the client library, initialize with project credentials, create sample data, and query it.

## Client Libraries

| Language | Package | Status |
|----------|---------|--------|
| JavaScript/TypeScript | `@supabase/supabase-js` | Official, most complete |
| Python | `supabase` | Official |
| Flutter/Dart | `supabase_flutter` | Official |
| Swift | `supabase-swift` | Official |
| Kotlin | `supabase-kt` | Official |
| C# | `supabase-csharp` | Community |

## Pricing Model

| Plan | Database | Auth MAU | Storage | Edge Functions |
|------|----------|----------|---------|----------------|
| Free | 500 MB | 50,000 | 1 GB | 500K invocations |
| Pro ($25/mo) | 8 GB | 100,000 | 100 GB | 2M invocations |
| Team ($599/mo) | 8 GB | 100,000 | 100 GB | 2M invocations |
| Enterprise | Custom | Custom | Custom | Custom |

All plans include unlimited API requests and realtime connections.

## Common Pitfalls

1. **Forgetting to enable RLS** — Tables in the `public` schema are exposed via the API. Without RLS, anyone with the `anon` key can read/write all rows.
2. **Using `service_role` key in client code** — This bypasses RLS entirely. Only use it server-side.
3. **Not setting up email confirmation** — On hosted projects, email verification is enabled by default. Test with the built-in Mailpit in local dev.
4. **Ignoring connection pooling** — Use the pooled connection string for serverless environments (Supavisor on port 6543), not the direct connection (port 5432).
5. **Treating Supabase as "just Firebase"** — It's Postgres underneath. Learn SQL, use migrations, leverage extensions. That's its superpower.
