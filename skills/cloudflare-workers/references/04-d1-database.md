# Cloudflare D1 — SQLite Database

> Source: [developers.cloudflare.com/d1](https://developers.cloudflare.com/d1/)

## Table of Contents

- [What Is D1](#what-is-d1)
- [Setup](#setup)
- [D1Database API](#d1database-api)
- [Prepared Statements](#prepared-statements)
- [Batch Operations](#batch-operations)
- [Sessions](#sessions)
- [Migrations](#migrations)
- [Query JSON Data](#query-json-data)
- [Time Travel (PITR)](#time-travel-pitr)
- [Limits and Pricing](#limits-and-pricing)
- [Common Patterns](#common-patterns)

## What Is D1

D1 is Cloudflare's serverless SQLite database. It runs at the edge with automatic replication, point-in-time recovery, and zero configuration.

**Best for:** Relational data, user profiles, content management, multi-tenant apps, any workload that needs SQL.

Key features:
- SQLite SQL syntax (full compatibility)
- Automatic read replication near users
- Built-in point-in-time recovery (30-day window)
- Batch operations as transactions
- JSON query support

## Setup

```bash
# Create a database
wrangler d1 create my-database
# => Created database "my-database" (ID: xxxx-xxxx-xxxx)

# Create migrations directory
mkdir -p migrations
```

```toml
# wrangler.toml
[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "xxxx-xxxx-xxxx"
```

```typescript
interface Env {
  DB: D1Database;
}
```

## D1Database API

### prepare(query) — Prepared Statement

```typescript
const stmt = env.DB.prepare("SELECT * FROM users WHERE id = ?");
```

Returns a `D1PreparedStatement` for parameter binding and execution.

### exec(query) — Raw SQL Execution

```typescript
const result = await env.DB.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
  );
`);
// => { count: number, duration: number }
```

Use `exec()` for DDL and maintenance only — it doesn't support parameter binding.

### batch(statements) — Transaction Batch

```typescript
const results = await env.DB.batch([
  env.DB.prepare("INSERT INTO users (name, email) VALUES (?, ?)").bind("Alice", "alice@example.com"),
  env.DB.prepare("INSERT INTO users (name, email) VALUES (?, ?)").bind("Bob", "bob@example.com"),
  env.DB.prepare("SELECT count(*) as total FROM users"),
]);
// Each result: D1Result
```

Batch operations are **transactional** — if any statement fails, the entire batch is rolled back.

### dump() — Export Database

```typescript
const data = await env.DB.dump();
// => ArrayBuffer (SQLite binary format)
```

## Prepared Statements

### bind(...values) — Parameter Binding

```typescript
const stmt = env.DB.prepare("SELECT * FROM users WHERE name = ? AND age > ?")
  .bind("Alice", 25);
```

Supported types: `string`, `number`, `null`, `ArrayBuffer`. Always use parameter binding — never interpolate values into SQL strings.

### first(column?) — Single Row

```typescript
// Full row
const user = await env.DB.prepare("SELECT * FROM users WHERE id = ?")
  .bind(1)
  .first();
// => { id: 1, name: "Alice", email: "alice@example.com" } | null

// Single column
const name = await env.DB.prepare("SELECT name FROM users WHERE id = ?")
  .bind(1)
  .first("name");
// => "Alice" | null
```

### all() — All Rows

```typescript
const { results, success, meta } = await env.DB.prepare("SELECT * FROM users")
  .all();
// results: Array<Record<string, unknown>>
// meta: { duration: number, rows_read: number, rows_written: number, ... }
```

### run() — Execute (INSERT/UPDATE/DELETE)

```typescript
const result = await env.DB.prepare("INSERT INTO users (name, email) VALUES (?, ?)")
  .bind("Charlie", "charlie@example.com")
  .run();
// => D1Result { success: true, meta: { changes: 1, last_row_id: 3, ... } }
```

### raw(options?) — Raw Arrays

```typescript
const rows = await env.DB.prepare("SELECT id, name FROM users")
  .raw();
// => [[1, "Alice"], [2, "Bob"]]

// With column names as first row
const rowsWithCols = await env.DB.prepare("SELECT id, name FROM users")
  .raw({ columnNames: true });
// => [["id", "name"], [1, "Alice"], [2, "Bob"]]
```

### D1Result Type

```typescript
interface D1Result<T = unknown> {
  results: T[];             // Query result rows
  success: boolean;         // Whether the query succeeded
  meta: {
    duration: number;       // Query duration (ms)
    rows_read: number;      // Rows scanned
    rows_written: number;   // Rows modified
    changes: number;        // Rows changed by INSERT/UPDATE/DELETE
    last_row_id: number;    // Last inserted rowid
    changed_db: boolean;    // Whether the DB was modified
    size_after: number;     // DB size in bytes after query
  };
}
```

## Batch Operations

Batch is the primary way to run transactions in D1:

```typescript
async function transferFunds(env: Env, from: number, to: number, amount: number) {
  const results = await env.DB.batch([
    env.DB.prepare("UPDATE accounts SET balance = balance - ? WHERE id = ?").bind(amount, from),
    env.DB.prepare("UPDATE accounts SET balance = balance + ? WHERE id = ?").bind(amount, to),
    env.DB.prepare("INSERT INTO transfers (from_id, to_id, amount) VALUES (?, ?, ?)").bind(from, to, amount),
  ]);
  // All succeed or all fail (atomic)
}
```

## Sessions

Sessions ensure sequential consistency across multiple queries:

```typescript
const session = env.DB.withSession("first-primary");

// All queries in this session see a consistent state
const user = await session.prepare("SELECT * FROM users WHERE id = ?")
  .bind(1)
  .first();

await session.prepare("UPDATE users SET last_login = datetime('now') WHERE id = ?")
  .bind(1)
  .run();

// Get a bookmark to resume this session later
const { bookmark } = session.getBookmark();
```

Session modes:
- `"first-primary"` — First query routes to primary (strongest consistency)
- `"first-unconstrained"` — First query routes to nearest replica (default)
- A bookmark string — Resume from a previous session's state

## Migrations

```bash
# Create a migration file
wrangler d1 migrations create my-database create_users_table
# => Created migrations/0001_create_users_table.sql

# Apply migrations locally
wrangler d1 migrations apply my-database --local

# Apply to remote database
wrangler d1 migrations apply my-database --remote
```

Migration file:

```sql
-- migrations/0001_create_users_table.sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  role TEXT DEFAULT 'user',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

## Query JSON Data

D1 supports SQLite's JSON functions:

```typescript
// Store JSON
await env.DB.prepare("INSERT INTO settings (user_id, prefs) VALUES (?, ?)")
  .bind(1, JSON.stringify({ theme: "dark", lang: "en" }))
  .run();

// Query JSON fields
const theme = await env.DB.prepare(
  "SELECT json_extract(prefs, '$.theme') as theme FROM settings WHERE user_id = ?"
).bind(1).first("theme");

// Filter by JSON value
const darkUsers = await env.DB.prepare(
  "SELECT user_id FROM settings WHERE json_extract(prefs, '$.theme') = ?"
).bind("dark").all();
```

## Time Travel (PITR)

Restore your database to any point within the last 30 days:

```bash
# List available bookmarks/restore points
wrangler d1 time-travel info my-database

# Restore to a specific timestamp
wrangler d1 time-travel restore my-database --timestamp "2026-04-20T10:00:00Z"

# Restore to a specific bookmark
wrangler d1 time-travel restore my-database --bookmark "bookmark_string"
```

## Limits and Pricing

| Limit | Free | Paid |
|-------|------|------|
| Max DB size | 500 MB | 10 GB |
| Max databases | 50 | 50,000 |
| Rows read/day | 5 million | 25B/mo ($0.001/million) |
| Rows written/day | 100,000 | 50M/mo ($1.00/million) |
| Storage | 5 GB total | 5 GB + $0.75/GB-mo |
| Max query size | 100 KB | 100 KB |
| Max bind parameters | 100 | 100 |
| Max batch statements | 100 | 100 |
| Max columns per table | 100 | 100 |

## Common Patterns

### CRUD API

```typescript
export default {
  async fetch(request: Request, env: Env) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/users") {
      const { results } = await env.DB.prepare("SELECT * FROM users ORDER BY id DESC LIMIT 50").all();
      return Response.json(results);
    }

    if (request.method === "POST" && url.pathname === "/users") {
      const { name, email } = await request.json<{ name: string; email: string }>();
      const result = await env.DB.prepare("INSERT INTO users (name, email) VALUES (?, ?) RETURNING *")
        .bind(name, email)
        .first();
      return Response.json(result, { status: 201 });
    }

    return new Response("Not Found", { status: 404 });
  },
};
```

### Pagination

```typescript
async function getUsers(env: Env, page: number, pageSize: number = 20) {
  const offset = (page - 1) * pageSize;

  const [countResult, dataResult] = await env.DB.batch([
    env.DB.prepare("SELECT count(*) as total FROM users"),
    env.DB.prepare("SELECT * FROM users ORDER BY id DESC LIMIT ? OFFSET ?").bind(pageSize, offset),
  ]);

  const total = (countResult.results[0] as { total: number }).total;
  return { data: dataResult.results, total, page, pageSize, totalPages: Math.ceil(total / pageSize) };
}
```

## Common Pitfalls

- **No `ALTER TABLE ... ADD COLUMN` with constraints** — SQLite limitations apply. Add columns as nullable, then backfill.
- **No `RETURNING *` on `run()`** — Use `first()` or `all()` with `RETURNING` clause instead.
- **Batch is the only transaction** — There's no `BEGIN`/`COMMIT`. Use `batch()` for atomic operations.
- **Write limits** — Free plan: 100K writes/day. Plan for this when building write-heavy apps.
- **Parameter count** — Max 100 bind parameters per query. For large `IN (...)` clauses, use temp tables.
