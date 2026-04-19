# Supabase — REST & GraphQL APIs

> Source: https://supabase.com/docs/guides/api

## Overview

Every Supabase project auto-generates APIs from your database schema. You get three API layers without writing any backend code:

| API | Technology | Best For |
|-----|-----------|----------|
| **REST** | PostgREST v14 | CRUD operations, filters, relationships |
| **GraphQL** | pg_graphql | Complex nested queries, typed schemas |
| **Realtime** | Elixir WebSocket | Live subscriptions (see `06-realtime.md`) |

## REST API (PostgREST)

PostgREST turns your Postgres database into a RESTful API. Every table, view, and function in exposed schemas becomes an endpoint.

### API URL Structure

```
https://<project-ref>.supabase.co/rest/v1/<table-name>
```

### Authentication

All requests require the `apikey` header (your anon or service_role key). Authenticated requests also include an `Authorization: Bearer <jwt>` header:

```bash
curl 'https://<ref>.supabase.co/rest/v1/todos' \
  -H "apikey: <anon-key>" \
  -H "Authorization: Bearer <user-jwt>"
```

The client library handles this automatically.

### CRUD Operations

```bash
# SELECT (GET)
GET /rest/v1/todos?select=id,title&is_complete=eq.false&order=created_at.desc

# INSERT (POST)
POST /rest/v1/todos
Content-Type: application/json
{"title": "New todo", "user_id": "..."}

# UPDATE (PATCH)
PATCH /rest/v1/todos?id=eq.1
Content-Type: application/json
{"is_complete": true}

# DELETE (DELETE)
DELETE /rest/v1/todos?id=eq.1

# UPSERT (POST with Prefer header)
POST /rest/v1/todos
Prefer: resolution=merge-duplicates
Content-Type: application/json
{"id": 1, "title": "Updated todo"}
```

### Filtering Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `eq` | Equal | `?status=eq.active` |
| `neq` | Not equal | `?status=neq.archived` |
| `gt` | Greater than | `?price=gt.100` |
| `gte` | Greater than or equal | `?price=gte.100` |
| `lt` | Less than | `?price=lt.50` |
| `lte` | Less than or equal | `?price=lte.50` |
| `like` | LIKE (case-sensitive) | `?name=like.*shoes*` |
| `ilike` | ILIKE (case-insensitive) | `?name=ilike.*shoes*` |
| `is` | IS (null, true, false) | `?deleted_at=is.null` |
| `in` | IN | `?id=in.(1,2,3)` |
| `cs` | Contains | `?tags=cs.{sale}` |
| `cd` | Contained by | `?tags=cd.{sale,new}` |
| `ov` | Overlaps | `?tags=ov.{sale,new}` |
| `not` | Negate | `?not.status=eq.archived` |
| `or` | OR logic | `?or=(status.eq.active,price.gt.100)` |
| `and` | AND logic | `?and=(status.eq.active,price.gt.100)` |

### Ordering & Pagination

```bash
# Order by column
?order=created_at.desc

# Multiple ordering
?order=category.asc,price.desc

# Pagination with Range header
Range: 0-9           # First 10 items
Range: 10-19          # Next 10 items

# Or with limit/offset
?limit=10&offset=20

# Get total count
Prefer: count=exact   # Response header: Content-Range: 0-9/42
```

### Querying Relationships

PostgREST auto-detects foreign keys:

```bash
# Embed related table (one-to-many)
GET /rest/v1/orders?select=id,total,order_items(product_id,quantity)

# Nested relationships
GET /rest/v1/orders?select=id,users(name),order_items(products(name,price))

# Many-to-many (through junction table)
GET /rest/v1/products?select=id,name,tags(name)
```

### Calling Functions (RPC)

```bash
POST /rest/v1/rpc/get_user_stats
Content-Type: application/json
{"target_user_id": "550e8400-..."}
```

### Response Headers

| Header | Purpose |
|--------|---------|
| `Content-Range` | Pagination info (with `Prefer: count=exact`) |
| `Prefer: return=representation` | Return the modified row(s) |
| `Prefer: return=minimal` | Return only status code |
| `Prefer: resolution=merge-duplicates` | Upsert behavior |

### Performance Tips

- PostgREST v14 provides ~20% more RPS for GET requests
- Use `select=col1,col2` instead of `select=*` to reduce payload
- Add database indexes on filtered/ordered columns
- Use `head=true` for count-only queries (no data transfer)

## GraphQL API (pg_graphql)

pg_graphql is a Postgres extension that provides a GraphQL interface reflecting your database schema. It's automatically available on all Supabase projects.

### Endpoint

```
https://<project-ref>.supabase.co/graphql/v1
```

### Querying

```graphql
query {
  todosCollection(
    filter: { is_complete: { eq: false } }
    orderBy: [{ created_at: DescNullsLast }]
    first: 10
  ) {
    edges {
      node {
        id
        title
        is_complete
        created_at
        users {
          name
          email
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### Mutations

```graphql
mutation {
  insertIntoTodosCollection(
    objects: [{ title: "New todo", user_id: "..." }]
  ) {
    records {
      id
      title
    }
  }
}

mutation {
  updateTodosCollection(
    filter: { id: { eq: 1 } }
    set: { is_complete: true }
  ) {
    records {
      id
      is_complete
    }
  }
}

mutation {
  deleteFromTodosCollection(
    filter: { id: { eq: 1 } }
  ) {
    records {
      id
    }
  }
}
```

### Using from JavaScript

```typescript
const { data, error } = await supabase
  .from('graphql')
  .select()  // Not how you'd use it — use a proper GraphQL client:

// With fetch:
const response = await fetch(`${supabaseUrl}/graphql/v1`, {
  method: 'POST',
  headers: {
    'apikey': anonKey,
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: `query { todosCollection { edges { node { id title } } } }`,
  }),
})
```

### GraphQL Naming Conventions

pg_graphql converts Postgres names to GraphQL conventions:

| Postgres | GraphQL |
|----------|---------|
| `todos` (table) | `todosCollection` (query) |
| `todo_items` | `todoItemsCollection` |
| `insert` | `insertIntoTodosCollection` |
| `update` | `updateTodosCollection` |
| `delete` | `deleteFromTodosCollection` |

### Enabling pg_graphql

```sql
create extension if not exists pg_graphql;
```

Pre-enabled on all Supabase projects.

## API Access Control

Both APIs respect Row Level Security. The flow:

1. Client sends request with `apikey` header (maps to `anon` or `authenticated` Postgres role)
2. If JWT is present, `auth.uid()` and `auth.jwt()` are set from the token
3. PostgREST/pg_graphql executes the query as that role
4. RLS policies filter results

### Exposing Additional Schemas

By default, only `public` is exposed. Add more in `config.toml`:

```toml
[api]
schemas = ["public", "custom_schema"]
```

Or via Dashboard: Settings → API → Exposed schemas.

## Common Pitfalls

1. **Relying on the API without RLS** — The auto-generated API exposes your entire schema. RLS is mandatory.
2. **Not using `select` to limit columns** — Fetching `*` transfers unnecessary data and may expose sensitive columns.
3. **Ignoring `Prefer` headers** — Without `return=representation`, INSERT/UPDATE/DELETE don't return the affected rows.
4. **Using GraphQL for simple CRUD** — The REST API is simpler and faster for basic operations. Use GraphQL when you need deeply nested queries.
5. **Not indexing filtered columns** — PostgREST passes filters to Postgres. Without indexes, filtered queries are slow.
