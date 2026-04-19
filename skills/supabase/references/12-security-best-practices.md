# Supabase — Security & Best Practices

> Source: https://supabase.com/docs/guides/security

## Table of Contents

- [Security Checklist](#security-checklist)
- [Key Management](#key-management)
- [RLS Best Practices](#rls-best-practices)
- [Auth Security](#auth-security)
- [Database Security](#database-security)
- [Edge Function Security](#edge-function-security)
- [Storage Security](#storage-security)
- [Production Readiness](#production-readiness)
- [Performance Best Practices](#performance-best-practices)
- [Common Anti-Patterns](#common-anti-patterns)

## Security Checklist

Before going to production, verify:

- [ ] RLS enabled on **every** table in `public` schema
- [ ] RLS policies tested for each role (`anon`, `authenticated`)
- [ ] `service_role` key is **never** exposed to clients
- [ ] Custom SMTP configured (built-in has rate limits)
- [ ] Email confirmation enabled for auth
- [ ] MFA available for sensitive operations
- [ ] Database password is strong and rotated
- [ ] Unused Postgres extensions disabled
- [ ] API rate limiting configured
- [ ] CORS restricted to your domains (not `*` in production)
- [ ] Backups verified and PITR enabled (Team+ plans)

## Key Management

| Key | Exposure | Purpose | Danger If Leaked |
|-----|----------|---------|-----------------|
| `anon` | Public (client) | API access with RLS enforced | Low (RLS protects data) |
| `service_role` | **Server only** | Bypasses RLS, full admin | **Critical** — full DB access |
| DB password | **Server only** | Direct Postgres connection | **Critical** — bypasses everything |
| JWT secret | **Never share** | Token signing/verification | **Critical** — forge any session |

### Rules

1. **Never embed `service_role` in client code** — not in environment variables prefixed with `NEXT_PUBLIC_`, not in mobile apps, not in browser JavaScript.
2. **Rotate the DB password** periodically via Dashboard → Settings → Database.
3. **Use environment variables** — never hardcode keys in source code.
4. **Different keys per environment** — staging and production use separate projects with separate keys.

## RLS Best Practices

### Enable RLS on Every Table

```sql
-- Auto-enable RLS on all future tables
create or replace function public.enable_rls()
returns event_trigger language plpgsql as $$
declare obj record;
begin
  for obj in select * from pg_event_trigger_ddl_commands()
    where command_tag = 'CREATE TABLE'
  loop
    execute format('alter table %s enable row level security', obj.object_identity);
  end loop;
end;
$$;

create event trigger enable_rls_trigger
  on ddl_command_end when tag in ('CREATE TABLE')
  execute function public.enable_rls();
```

### Always Wrap Helper Functions

```sql
-- Performance: call auth.uid() once, not per row
using ((select auth.uid()) = user_id)
```

### Never Trust User Metadata for Authorization

```sql
-- BAD: user can edit their own metadata
using ((auth.jwt()->'user_metadata'->>'role') = 'admin')

-- GOOD: only the server can set app_metadata
using ((auth.jwt()->'app_metadata'->>'role') = 'admin')
```

### Test Policies

```sql
-- Simulate a specific user
set role authenticated;
set request.jwt.claims = '{"sub": "user-uuid-here", "role": "authenticated"}';

select * from todos;  -- Should only return this user's rows

reset role;
```

## Auth Security

### Email Confirmation

Always enable in production. Without it, anyone can sign up with any email:

```toml
# supabase/config.toml
[auth.email]
enable_confirmations = true
double_confirm_changes = true
```

### Password Policy

Configure minimum password requirements via Dashboard → Authentication → Policies.

### Rate Limiting

Supabase applies default rate limits to auth endpoints. For additional protection:

- Implement CAPTCHA on sign-up/sign-in forms
- Use `supabase.auth.signInWithOAuth` scopes to request only needed permissions
- Enable MFA for sensitive operations

### Session Security

```typescript
// Always validate server-side with getUser(), not getSession()
const { data: { user }, error } = await supabase.auth.getUser()

// getSession() reads from local storage — it can be tampered with
// getUser() makes a network request to validate the JWT
```

### Protect Against Account Enumeration

Supabase returns identical responses for existing and non-existing accounts during login. Don't add custom logic that reveals whether an email is registered.

## Database Security

### Schema Isolation

Keep internal tables out of the public API:

```sql
create schema private;

create table private.admin_settings (
  key text primary key,
  value jsonb
);

-- This table is NOT accessible via the REST/GraphQL API
```

### Function Security

```sql
-- Always set search_path for security definer functions
create or replace function private.is_admin()
returns boolean
language plpgsql
security definer
set search_path = ''  -- Prevents search_path injection
as $$
begin
  return exists (
    select 1 from public.user_roles
    where user_id = (select auth.uid())
    and role = 'admin'
  );
end;
$$;
```

### Connection Security

```bash
# Use the pooled connection string for serverless (port 6543)
# Direct connection for migrations/admin (port 5432)

# Always use SSL
psql "postgresql://postgres:password@db.ref.supabase.co:5432/postgres?sslmode=require"
```

## Edge Function Security

### Validate Input

```typescript
Deno.serve(async (req) => {
  // Validate method
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 })
  }

  // Validate content type
  const contentType = req.headers.get('content-type')
  if (!contentType?.includes('application/json')) {
    return new Response('Invalid content type', { status: 400 })
  }

  // Validate and parse body
  let body
  try {
    body = await req.json()
  } catch {
    return new Response('Invalid JSON', { status: 400 })
  }

  // Validate required fields
  if (!body.email || typeof body.email !== 'string') {
    return new Response('Email required', { status: 400 })
  }
})
```

### Webhook Verification

Always verify webhook signatures:

```typescript
import { createHmac, timingSafeEqual } from "node:crypto"

function verifyWebhook(body: string, signature: string, secret: string): boolean {
  const expected = createHmac('sha256', secret).update(body).digest('hex')
  return timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  )
}
```

## Storage Security

### Bucket Policies

```sql
-- Restrict uploads to authenticated users, their own folder
create policy "User uploads" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'uploads'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

-- Restrict file types at the policy level
create policy "Only images" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'avatars'
    and storage.extension(name) in ('jpg', 'jpeg', 'png', 'webp')
  );
```

### File Size Limits

Set per-bucket file size limits to prevent abuse:

```sql
update storage.buckets
set file_size_limit = 5242880  -- 5MB
where id = 'avatars';
```

## Production Readiness

### Connection Pooling

Use the pooled connection string (port 6543) for serverless environments:

```
postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

Direct connections (port 5432) are for migrations and admin tasks only.

### Monitoring

- Enable `pg_stat_statements` for query performance tracking
- Monitor via Dashboard → Reports → Database, API, Auth
- Set up alerts for error rates and slow queries
- Use `supabase inspect db` commands for diagnostics

### Database Indexes

```sql
-- Index columns used in RLS policies
create index idx_todos_user_id on todos(user_id);

-- Index columns used in WHERE clauses and ORDER BY
create index idx_orders_status on orders(status);
create index idx_orders_created on orders(created_at desc);

-- Composite index for common query patterns
create index idx_orders_user_status on orders(user_id, status);

-- Partial index for active records
create index idx_active_orders on orders(user_id)
  where status in ('pending', 'processing');
```

## Performance Best Practices

1. **Use `select` to specify columns** — don't fetch `*` when you need 3 fields
2. **Add indexes on filtered/ordered columns** — especially FK columns and policy columns
3. **Use RPC for complex queries** — database functions are faster than multiple API calls
4. **Enable connection pooling** — mandatory for serverless deployments
5. **Use `count: 'estimated'`** — exact counts lock the table; estimated is fine for pagination
6. **Batch inserts** — send arrays instead of individual rows
7. **Cache with CDN** — use `Cache-Control` headers for public, infrequently-changing data
8. **Use materialized views** — for expensive aggregations that don't need real-time accuracy

## Common Anti-Patterns

1. **"I'll add RLS later"** — The moment data hits your public schema without RLS, it's exposed. Enable RLS first, then create tables.
2. **Using `service_role` everywhere** — If you're using `service_role` in client code "because RLS is annoying," your security model is broken. Fix the policies.
3. **Granting `bypassrls` to roles used by the API** — Only the `service_role` should bypass RLS. Custom roles used by API consumers should always go through RLS.
4. **Storing secrets in the database** — Use edge function secrets (`supabase secrets set`) or vault extensions, not plain-text columns.
5. **Not validating on both client and server** — Client validation is for UX. Server validation (RLS, check constraints, triggers) is for security. You need both.
6. **Ignoring the Security Advisor** — Supabase Dashboard includes a Security Advisor that flags issues. Check it regularly.
