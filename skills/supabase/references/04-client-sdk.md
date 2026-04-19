# Supabase — Client SDK (supabase-js)

> Source: https://supabase.com/docs/reference/javascript

## Table of Contents

- [Installation & Setup](#installation--setup)
- [TypeScript Support](#typescript-support)
- [Querying Data (SELECT)](#querying-data-select)
- [Inserting Data](#inserting-data)
- [Updating Data](#updating-data)
- [Upserting Data](#upserting-data)
- [Deleting Data](#deleting-data)
- [Filters](#filters)
- [Modifiers](#modifiers)
- [Calling Functions (RPC)](#calling-functions-rpc)
- [Server-Side Rendering](#server-side-rendering)
- [Common Pitfalls](#common-pitfalls)

## Installation & Setup

```bash
npm install @supabase/supabase-js
```

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

### Client Options

```typescript
const supabase = createClient(url, anonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    storage: window.localStorage,     // Custom storage adapter
    storageKey: 'supabase-auth-token',
    flowType: 'pkce',                 // 'implicit' or 'pkce'
  },
  db: {
    schema: 'public',                 // Default schema
  },
  global: {
    headers: { 'x-custom-header': 'value' },
    fetch: customFetch,               // Custom fetch implementation
  },
  realtime: {
    params: { eventsPerSecond: 10 },
  },
})
```

## TypeScript Support

Generate types from your database schema:

```bash
# Install CLI
npm install supabase --save-dev

# Generate types
npx supabase gen types typescript --project-id <project-ref> > src/database.types.ts
```

Use generated types with the client:

```typescript
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

const supabase = createClient<Database>(url, anonKey)

// Now fully typed: autocomplete on table names, column names, and return types
const { data } = await supabase.from('todos').select('id, title')
// data is typed as { id: number; title: string }[] | null
```

## Querying Data (SELECT)

### Basic Select

```typescript
// All columns
const { data, error } = await supabase.from('todos').select('*')

// Specific columns
const { data, error } = await supabase.from('todos').select('id, title, is_complete')

// Rename columns in response
const { data, error } = await supabase.from('todos').select('id, taskName:title')
```

### Querying Relationships (Joins)

```typescript
// One-to-many: get todos with their user
const { data } = await supabase
  .from('todos')
  .select('*, users(name, email)')

// Many-to-many through junction table
const { data } = await supabase
  .from('products')
  .select('*, tags(name)')

// Nested relationships
const { data } = await supabase
  .from('orders')
  .select(`
    id,
    created_at,
    users(name),
    order_items(
      quantity,
      products(name, price)
    )
  `)
```

### Counting Rows

```typescript
// Exact count (slower, accurate)
const { count } = await supabase
  .from('todos')
  .select('*', { count: 'exact', head: true })

// Estimated count (faster, approximate)
const { count } = await supabase
  .from('todos')
  .select('*', { count: 'estimated', head: true })
```

## Inserting Data

```typescript
// Single row
const { data, error } = await supabase
  .from('todos')
  .insert({ title: 'Buy groceries', user_id: userId })
  .select()  // Return the inserted row

// Multiple rows
const { data, error } = await supabase
  .from('todos')
  .insert([
    { title: 'Buy groceries', user_id: userId },
    { title: 'Walk the dog', user_id: userId },
  ])
  .select()
```

## Updating Data

```typescript
const { data, error } = await supabase
  .from('todos')
  .update({ is_complete: true })
  .eq('id', todoId)
  .select()
```

**Warning:** Calling `.update()` without a filter updates ALL rows. Always add filters.

## Upserting Data

Insert or update based on primary key or unique constraint:

```typescript
const { data, error } = await supabase
  .from('users')
  .upsert(
    { id: userId, name: 'Updated Name', email: 'new@email.com' },
    { onConflict: 'id' }
  )
  .select()

// Bulk upsert
const { data, error } = await supabase
  .from('products')
  .upsert(productsArray, {
    onConflict: 'sku',
    ignoreDuplicates: false,  // true = skip conflicts instead of updating
  })
```

## Deleting Data

```typescript
const { error } = await supabase
  .from('todos')
  .delete()
  .eq('id', todoId)

// Delete multiple
const { error } = await supabase
  .from('todos')
  .delete()
  .in('id', [1, 2, 3])
```

**Warning:** Calling `.delete()` without a filter deletes ALL rows.

## Filters

```typescript
const query = supabase.from('products').select('*')

// Equality
query.eq('status', 'active')           // status = 'active'
query.neq('status', 'archived')        // status != 'archived'

// Comparison
query.gt('price', 100)                 // price > 100
query.gte('price', 100)                // price >= 100
query.lt('price', 50)                  // price < 50
query.lte('price', 50)                 // price <= 50

// Pattern matching
query.like('name', '%shoe%')           // LIKE (case-sensitive)
query.ilike('name', '%shoe%')          // ILIKE (case-insensitive)

// Array / Set
query.in('status', ['active', 'pending'])  // status IN ('active', 'pending')
query.contains('tags', ['sale'])           // tags @> ['sale']
query.containedBy('tags', ['sale', 'new']) // tags <@ ['sale', 'new']
query.overlaps('tags', ['sale', 'new'])    // tags && ['sale', 'new']

// NULL checks
query.is('deleted_at', null)           // deleted_at IS NULL
query.not('status', 'eq', 'archived') // NOT (status = 'archived')

// Full-text search
query.textSearch('description', 'shoes & running', {
  type: 'websearch',
  config: 'english',
})

// Range
query.rangeGt('age_range', '[20,30]')  // Range operators

// OR conditions
query.or('status.eq.active,price.gt.100')

// AND across different columns (default behavior — just chain filters)
query.eq('status', 'active').gt('price', 100)
```

### Complex OR/AND

```typescript
// (status = 'active' AND price > 100) OR (status = 'featured')
const { data } = await supabase
  .from('products')
  .select('*')
  .or('and(status.eq.active,price.gt.100),status.eq.featured')
```

## Modifiers

```typescript
const { data } = await supabase
  .from('products')
  .select('*')
  .order('created_at', { ascending: false })   // ORDER BY
  .limit(10)                                    // LIMIT
  .range(0, 9)                                  // OFFSET + LIMIT (pagination)
  .single()                                     // Expect exactly 1 row (error if 0 or 2+)
  .maybeSingle()                                // Expect 0 or 1 row

// Order by multiple columns
  .order('category', { ascending: true })
  .order('price', { ascending: false })

// CSV output
  .csv()

// Abort signal
  .abortSignal(controller.signal)
```

### Pagination Pattern

```typescript
const PAGE_SIZE = 20

async function fetchPage(page: number) {
  const from = page * PAGE_SIZE
  const to = from + PAGE_SIZE - 1

  const { data, error, count } = await supabase
    .from('products')
    .select('*', { count: 'exact' })
    .range(from, to)
    .order('created_at', { ascending: false })

  return { data, totalPages: Math.ceil((count ?? 0) / PAGE_SIZE) }
}
```

## Calling Functions (RPC)

```typescript
// Call a database function
const { data, error } = await supabase.rpc('get_user_stats', {
  target_user_id: userId,
})

// RPC with filters (if function returns a table)
const { data, error } = await supabase
  .rpc('search_products', { search_term: 'shoes' })
  .gt('price', 50)
  .order('relevance', { ascending: false })
  .limit(10)
```

## Server-Side Rendering

For SSR frameworks, use `@supabase/ssr` instead of `@supabase/supabase-js`:

```bash
npm install @supabase/supabase-js @supabase/ssr
```

```typescript
// Next.js Server Component
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createSupabaseServer() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options)
          })
        },
      },
    }
  )
}
```

## Common Pitfalls

1. **Forgetting `.select()` after mutations** — `insert`, `update`, `upsert` don't return data by default. Chain `.select()` to get the result.
2. **Missing filters on `update`/`delete`** — Without filters, these affect ALL rows. Always add `.eq()` or similar.
3. **Not handling errors** — Every query returns `{ data, error }`. Always check `error` before using `data`.
4. **Using the client in server components without `@supabase/ssr`** — The standard client stores sessions in `localStorage`, which doesn't exist server-side.
5. **Not regenerating types** — After schema changes, re-run `supabase gen types` to keep TypeScript in sync.
6. **Chaining `.single()` on queries that might return 0 rows** — Use `.maybeSingle()` instead to avoid errors when no row matches.
