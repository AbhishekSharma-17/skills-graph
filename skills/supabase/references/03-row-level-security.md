# Supabase — Row Level Security (RLS)

> Source: https://supabase.com/docs/guides/database/postgres/row-level-security

## Table of Contents

- [Why RLS Matters](#why-rls-matters)
- [Enabling RLS](#enabling-rls)
- [Policy Types](#policy-types)
- [Helper Functions](#helper-functions)
- [Common Policy Patterns](#common-policy-patterns)
- [Performance Optimization](#performance-optimization)
- [Advanced Patterns](#advanced-patterns)
- [Common Pitfalls](#common-pitfalls)

## Why RLS Matters

Row Level Security adds invisible WHERE clauses to every query, filtering data based on who's asking. In Supabase, RLS is the primary authorization layer — it sits between the API and your data, ensuring users only see and modify rows they're allowed to.

**RLS must always be enabled** on tables in exposed schemas (especially `public`). Without it, anyone with the `anon` key can read and write every row.

## Enabling RLS

Tables created via the Dashboard Table Editor have RLS enabled automatically. For SQL-created tables:

```sql
alter table todos enable row level security;
```

Once enabled, **no data is accessible** via the API until you create policies. The `service_role` key always bypasses RLS.

### Auto-Enable for All Future Tables

```sql
create or replace function public.enable_rls_on_new_tables()
returns event_trigger
language plpgsql
as $$
declare
  obj record;
begin
  for obj in select * from pg_event_trigger_ddl_commands()
    where command_tag = 'CREATE TABLE'
  loop
    execute format('alter table %s enable row level security', obj.object_identity);
  end loop;
end;
$$;

create event trigger enable_rls_trigger
  on ddl_command_end
  when tag in ('CREATE TABLE')
  execute function public.enable_rls_on_new_tables();
```

## Policy Types

### SELECT — Control Who Can Read

```sql
create policy "Anyone can view public profiles"
  on profiles for select
  to anon, authenticated
  using (is_public = true);

create policy "Users can view own profile"
  on profiles for select
  to authenticated
  using ((select auth.uid()) = user_id);
```

### INSERT — Validate New Rows

```sql
create policy "Users can create own todos"
  on todos for insert
  to authenticated
  with check ((select auth.uid()) = user_id);
```

### UPDATE — Control Reads and Writes

UPDATE policies use **both** `using` (which rows can be seen for update) and `with check` (what the row must look like after update):

```sql
create policy "Users can update own todos"
  on todos for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
```

A SELECT policy is also required for UPDATE to work.

### DELETE — Control Row Removal

```sql
create policy "Users can delete own todos"
  on todos for delete
  to authenticated
  using ((select auth.uid()) = user_id);
```

### ALL — Shorthand for All Operations

```sql
create policy "Full access to own rows"
  on todos for all
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
```

## Helper Functions

### `auth.uid()`

Returns the current user's UUID from the JWT. This is the most commonly used function in RLS policies:

```sql
using ((select auth.uid()) = user_id)
```

### `auth.jwt()`

Access full JWT claims — useful for role-based access, team membership, or metadata checks:

```sql
-- Check app_metadata (server-controlled, safe for auth)
create policy "Admins can manage all"
  on products for all
  to authenticated
  using (
    (select auth.jwt()->'app_metadata'->>'role') = 'admin'
  );

-- Check team membership
create policy "Team members can view"
  on team_data for select
  to authenticated
  using (
    team_id in (
      select jsonb_array_elements_text(
        (select auth.jwt()->'app_metadata'->'teams')
      )::bigint
    )
  );
```

**Important:** Use `raw_app_meta_data` (set server-side) for authorization, never `raw_user_meta_data` (user-editable).

### `auth.role()`

Returns the current Postgres role (`anon` or `authenticated`):

```sql
create policy "Authenticated users only"
  on private_data for select
  using (auth.role() = 'authenticated');
```

## Common Policy Patterns

### Public Read, Authenticated Write

```sql
create policy "Public read" on posts
  for select using (true);

create policy "Auth write" on posts
  for insert to authenticated
  with check ((select auth.uid()) = author_id);
```

### Organization/Team-Based Access

```sql
create policy "Org members can view"
  on documents for select
  to authenticated
  using (
    org_id in (
      select org_id from org_members
      where user_id = (select auth.uid())
    )
  );
```

### Role-Based Access Control (RBAC)

```sql
create policy "Editors can update"
  on articles for update
  to authenticated
  using (
    exists (
      select 1 from user_roles
      where user_id = (select auth.uid())
      and role in ('editor', 'admin')
    )
  );
```

### Restrictive Policies (AND Logic)

By default, multiple policies on the same table combine with OR. Use `as restrictive` for AND:

```sql
create policy "Must be authenticated"
  on sensitive_data
  as restrictive
  for select
  to authenticated
  using (true);

create policy "Must have MFA"
  on sensitive_data
  as restrictive
  for select
  to authenticated
  using ((select auth.jwt()->>'aal') = 'aal2');
```

## Performance Optimization

RLS adds overhead to every query. These patterns dramatically improve performance:

### 1. Wrap Functions in SELECT

Force function evaluation once per statement instead of once per row:

```sql
-- SLOW: auth.uid() called for every row
using (auth.uid() = user_id)

-- FAST: auth.uid() called once, result reused
using ((select auth.uid()) = user_id)
```

Benchmarks show **94-99% performance improvement**.

### 2. Add Indexes on Policy Columns

```sql
create index idx_todos_user_id on todos using btree (user_id);
create index idx_org_members_user_id on org_members using btree (user_id);
```

This alone can improve query time by **99.94%** on large tables.

### 3. Add Explicit Filters in Client Queries

Duplicate the RLS condition in your application query so Postgres can use indexes:

```typescript
const { data } = await supabase
  .from('todos')
  .select('*')
  .eq('user_id', userId)  // Helps the query planner
```

### 4. Avoid Joins in Policies — Use Subqueries

```sql
-- SLOW: joins source table
using (
  (select auth.uid()) in (
    select user_id from team_members
    where team_members.team_id = team_data.team_id
  )
)

-- FAST: independent subquery
using (
  team_id in (
    select team_id from team_members
    where user_id = (select auth.uid())
  )
)
```

### 5. Use Security Definer Functions for Complex Checks

```sql
create function private.user_has_role(required_role text)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
begin
  return exists (
    select 1 from public.user_roles
    where user_id = (select auth.uid())
    and role = required_role
  );
end;
$$;

create policy "Admin access"
  on resources for all
  to authenticated
  using ((select private.user_has_role('admin')));
```

### 6. Always Specify the Target Role

```sql
-- Without role: policy evaluates for ALL roles (wasteful)
create policy "Read" on data for select using (...);

-- With role: only evaluates for matching role
create policy "Read" on data for select to authenticated using (...);
```

## Advanced Patterns

### Bypassing RLS for Service Operations

```sql
-- Grant bypass to a specific role (use sparingly)
alter role service_backend with bypassrls;
```

### Views and RLS

Views bypass RLS by default. Force RLS enforcement:

```sql
create view my_todos with (security_invoker = true) as
  select * from todos;
```

### Handling NULL auth.uid()

When no user is authenticated, `auth.uid()` returns NULL. Comparisons with NULL always fail, which is correct for most policies. But be explicit when needed:

```sql
using (
  auth.uid() is not null
  and (select auth.uid()) = user_id
)
```

## Common Pitfalls

1. **Forgetting RLS on new tables** — Every table in `public` needs RLS enabled. Set up the auto-enable trigger.
2. **Using `user_metadata` for authorization** — Users can edit their own `raw_user_meta_data`. Use `raw_app_meta_data` instead.
3. **Not wrapping `auth.uid()` in SELECT** — Causes per-row function evaluation. Always use `(select auth.uid())`.
4. **Missing indexes on policy columns** — RLS adds WHERE clauses. Without indexes, you get full table scans.
5. **Permissive when you need restrictive** — Multiple permissive policies OR together. Use `as restrictive` when policies must ALL pass.
6. **Not testing policies** — Test with the Supabase SQL Editor using `set role authenticated; set request.jwt.claims = '...'` to simulate different users.
