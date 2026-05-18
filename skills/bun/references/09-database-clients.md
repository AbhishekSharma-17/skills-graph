# Bun — Database Clients

> Source: [bun.sh/docs/api/sql](https://bun.sh/docs/api/sql) | [bun.sh/docs/api/sqlite](https://bun.sh/docs/api/sqlite) | [bun.sh/docs/api/redis](https://bun.sh/docs/api/redis)

## Table of Contents

- [Overview](#overview)
- [Bun.SQL — Postgres and MySQL](#bunsql----postgres-and-mysql)
- [Tagged Template Queries](#tagged-template-queries)
- [Parameterized Queries](#parameterized-queries)
- [Transactions](#transactions)
- [Prepared Statements](#prepared-statements)
- [Connection Pooling](#connection-pooling)
- [SQLite — bun:sqlite](#sqlite----bunsqlite)
- [SQLite WAL Mode and Performance](#sqlite-wal-mode-and-performance)
- [Bun.redis — Redis Client](#bunredis----redis-client)
- [Redis Pub/Sub](#redis-pubsub)
- [Redis Performance](#redis-performance)
- [Error Handling and Reconnection](#error-handling-and-reconnection)
- [Migration Patterns](#migration-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Bun ships with zero-dependency, high-performance database clients built into the runtime — no need to install `pg`, `mysql2`, `better-sqlite3`, or `ioredis`.

| Client | Database | Import |
|--------|----------|--------|
| `Bun.SQL` | PostgreSQL, MySQL | `import { SQL } from "bun"` |
| `Database` | SQLite | `import { Database } from "bun:sqlite"` |
| `Bun.redis` | Redis | `import { RedisClient } from "bun"` |

## Bun.SQL — Postgres and MySQL

```typescript
import { SQL } from "bun";

const sql = new SQL("postgres://user:password@localhost:5432/mydb");
const mysql = new SQL("mysql://user:password@localhost:3306/mydb");

const db = new SQL({
  url: "postgres://localhost:5432/mydb",
  username: "app_user",
  password: process.env.DB_PASSWORD,
  database: "mydb",
  max: 20,
  idleTimeout: 30,
  tls: true,
});

process.on("beforeExit", () => sql.close());
```

## Tagged Template Queries

Values interpolated into tagged template literals are **automatically parameterized** — never concatenated into SQL:

```typescript
const sql = new SQL("postgres://localhost/mydb");

const users = await sql`SELECT * FROM users`;
const [user] = await sql`SELECT * FROM users WHERE id = ${id}`;

const [created] = await sql`
  INSERT INTO users (name, email) VALUES (${name}, ${email}) RETURNING *
`;

const [updated] = await sql`
  UPDATE users SET email = ${newEmail} WHERE id = ${created.id} RETURNING *
`;

await sql`DELETE FROM users WHERE id = ${deletedId}`;

// Dynamic column selection
const columns = sql(["id", "name", "email"]);
const rows = await sql`SELECT ${columns} FROM users LIMIT 10`;
```

## Parameterized Queries

```typescript
// SQL injection is impossible — values are always parameterized
const userInput = "'; DROP TABLE users; --";
const results = await sql`SELECT * FROM users WHERE name = ${userInput}`;
// Executes: SELECT * FROM users WHERE name = $1

// Multiple parameters
const filtered = await sql`
  SELECT * FROM users WHERE age BETWEEN ${minAge} AND ${maxAge} AND country = ${country}
`;

// IN clause with arrays
const batch = await sql`SELECT * FROM users WHERE id IN (${ids})`;

// JSON values
await sql`UPDATE users SET metadata = ${JSON.stringify(metadata)} WHERE id = ${1}`;
```

## Transactions

```typescript
const [order] = await sql.begin(async (tx) => {
  const [order] = await tx`
    INSERT INTO orders (user_id, total) VALUES (${userId}, ${total}) RETURNING *
  `;
  for (const item of items) {
    await tx`INSERT INTO order_items (order_id, product_id, quantity)
             VALUES (${order.id}, ${item.productId}, ${item.quantity})`;
    await tx`UPDATE products SET stock = stock - ${item.quantity} WHERE id = ${item.productId}`;
  }
  return [order];
});
// Auto-commits on success, auto-rolls-back on throw

// Savepoints for nested transactions
await sql.begin(async (tx) => {
  await tx`INSERT INTO logs (message) VALUES ('started')`;
  try {
    await tx.savepoint(async (sp) => {
      await sp`INSERT INTO risky_table (data) VALUES ('test')`;
      throw new Error("Oops");
    });
  } catch {
    await tx`INSERT INTO logs (message) VALUES ('risky op failed')`;
  }
  await tx`INSERT INTO logs (message) VALUES ('completed')`;
});
```

## Prepared Statements

```typescript
const findUser = sql`SELECT * FROM users WHERE id = $1`.prepare();

const user1 = await findUser.execute([1]);
const user2 = await findUser.execute([2]);
// Bun.SQL also implicitly caches queries based on template string
```

## Connection Pooling

```typescript
const sql = new SQL({
  url: "postgres://localhost/mydb",
  max: 20,               // max pool connections (default: 10)
  idleTimeout: 30,
  connectionTimeout: 10,
});

// Concurrent queries use different pool connections automatically
const [users, products, orders] = await Promise.all([
  sql`SELECT * FROM users LIMIT 100`,
  sql`SELECT * FROM products WHERE active = true`,
  sql`SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '1 day'`,
]);

console.log(sql.pool); // { size, available, pending }
```

## SQLite — bun:sqlite

Built-in synchronous SQLite driver running in-process:

```typescript
import { Database } from "bun:sqlite";

const db = new Database("myapp.sqlite");
const memdb = new Database(":memory:");
const readonly = new Database("data.sqlite", { readonly: true });

db.run(`CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
)`);

const insert = db.prepare("INSERT INTO users (name, email) VALUES ($name, $email)");
insert.run({ $name: "Alice", $email: "alice@example.com" });

const select = db.prepare("SELECT * FROM users WHERE name = ?");
const user = select.get("Alice");   // single row or null
const allUsers = db.prepare("SELECT * FROM users").all();

// Memory-efficient iteration for large result sets
for (const row of db.prepare("SELECT * FROM users").iterate()) {
  console.log(row.name);
}

// Transactions
const insertMany = db.transaction((users: { name: string; email: string }[]) => {
  const stmt = db.prepare("INSERT INTO users (name, email) VALUES ($name, $email)");
  for (const u of users) { stmt.run({ $name: u.name, $email: u.email }); }
  return users.length;
});

const count = insertMany([
  { name: "Bob", email: "bob@example.com" },
  { name: "Charlie", email: "charlie@example.com" },
]);

db.close();
```

## SQLite WAL Mode and Performance

```typescript
const db = new Database("app.sqlite");

db.run("PRAGMA journal_mode = WAL");      // recommended for production
db.run("PRAGMA synchronous = NORMAL");    // faster writes, safe with WAL
db.run("PRAGMA cache_size = -64000");     // 64MB cache
db.run("PRAGMA foreign_keys = ON");
db.run("PRAGMA busy_timeout = 5000");     // wait 5s on lock contention

// Bulk insert — transactions are critical for performance
const insertStmt = db.prepare("INSERT INTO events (type, data) VALUES (?, ?)");
const bulkInsert = db.transaction((events: [string, string][]) => {
  for (const [type, data] of events) { insertStmt.run(type, data); }
});

const events: [string, string][] = Array.from(
  { length: 100_000 }, (_, i) => ["click", JSON.stringify({ index: i })]
);
bulkInsert(events); // completes in milliseconds
```

## Bun.redis — Redis Client

```typescript
import { RedisClient } from "bun";

const redis = new RedisClient("redis://localhost:6379");

await redis.set("name", "Alice");
const name = await redis.get("name");                    // "Alice"
await redis.set("session:abc", "user_123", "EX", 3600); // with expiry
const missing = await redis.get("nonexistent");          // null

await redis.hset("user:1", "name", "Alice", "email", "alice@example.com");
const user = await redis.hgetall("user:1");

await redis.lpush("queue", "task1", "task2", "task3");
const task = await redis.rpop("queue");

await redis.sadd("tags", "javascript", "bun", "runtime");
const tags = await redis.smembers("tags");

await redis.zadd("leaderboard", 100, "alice", 200, "bob");
const top = await redis.zrevrange("leaderboard", 0, 2, "WITHSCORES");

await redis.expire("session:abc", 1800);
await redis.del("name", "user:1");
redis.close();
```

## Redis Pub/Sub

```typescript
const subscriber = new RedisClient("redis://localhost:6379");
const publisher = new RedisClient("redis://localhost:6379");

subscriber.subscribe("notifications", "alerts");
subscriber.on("message", (channel: string, message: string) => {
  console.log(`[${channel}] ${message}`);
});

subscriber.psubscribe("user:*:events");
subscriber.on("pmessage", (pattern: string, channel: string, message: string) => {
  console.log(`[${pattern}] ${channel}: ${message}`);
});

await publisher.publish("notifications", JSON.stringify({ type: "new_message", from: "alice" }));
```

## Redis Performance

Bun's Redis client is built in native Zig code — ~8x faster than ioredis.

```typescript
// Pipelining — multiple commands in a single round-trip
const pipeline = redis.pipeline();
pipeline.set("key1", "value1");
pipeline.set("key2", "value2");
pipeline.get("key1");
pipeline.get("key2");
const results = await pipeline.exec(); // ["OK", "OK", "value1", "value2"]

// Bulk cache pattern
async function cacheUsers(users: { id: number; name: string }[]) {
  const pipeline = redis.pipeline();
  for (const user of users) {
    pipeline.set(`user:${user.id}`, JSON.stringify(user), "EX", 3600);
  }
  await pipeline.exec();
}
```

## Error Handling and Reconnection

```typescript
// PostgreSQL — handle query errors
try {
  await sql`INSERT INTO users (email) VALUES (${duplicateEmail})`;
} catch (err) {
  if (err.code === "23505") {  // unique violation
    console.log("Email already exists");
  } else { throw err; }
}

// SQLite — constraint violations
try {
  db.run("INSERT INTO users (email) VALUES (?)", ["duplicate@example.com"]);
} catch (err) {
  if (err.message.includes("UNIQUE constraint failed")) {
    console.log("Duplicate entry");
  } else { throw err; }
}

// Redis — connection error handling
redis.on("error", (err) => console.error("Redis error:", err.message));
redis.on("reconnecting", () => console.log("Reconnecting to Redis..."));
```

## Migration Patterns

```typescript
import { SQL } from "bun";

const sql = new SQL("postgres://localhost/mydb");

interface Migration { version: number; name: string; up: string; down: string; }

const migrations: Migration[] = [
  {
    version: 1, name: "create_users",
    up: `CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW())`,
    down: `DROP TABLE users`,
  },
  {
    version: 2, name: "add_user_role",
    up: `ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'`,
    down: `ALTER TABLE users DROP COLUMN role`,
  },
];

async function migrate(sql: InstanceType<typeof SQL>) {
  await sql`CREATE TABLE IF NOT EXISTS _migrations (
    version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TIMESTAMPTZ DEFAULT NOW()
  )`;

  const applied = await sql`SELECT version FROM _migrations ORDER BY version`;
  const appliedVersions = new Set(applied.map((r: { version: number }) => r.version));

  for (const migration of migrations) {
    if (appliedVersions.has(migration.version)) continue;
    await sql.begin(async (tx) => {
      await tx.unsafe(migration.up);
      await tx`INSERT INTO _migrations (version, name) VALUES (${migration.version}, ${migration.name})`;
    });
    console.log(`Applied migration: ${migration.name}`);
  }
}

await migrate(sql);
```

## Common Pitfalls

1. **Using string concatenation for SQL** — Always use tagged template literals; concatenation bypasses parameterization and enables SQL injection
2. **Forgetting to close connections** — Call `sql.close()`, `db.close()`, or `redis.close()` on shutdown; leaked connections exhaust pool limits or file descriptors
3. **Running SQLite in default journal mode** — Always enable WAL mode (`PRAGMA journal_mode = WAL`); the default rollback journal is slower under concurrent access
4. **Using the subscriber connection for commands** — A Redis connection in subscribe mode cannot run regular GET/SET commands; use a separate connection for pub/sub
5. **Not wrapping bulk inserts in a transaction** — SQLite and PostgreSQL commit after each statement by default; wrapping N inserts in one transaction is orders of magnitude faster
6. **Ignoring connection pool limits** — If `max` is too low for query concurrency, requests queue up; monitor pool usage under load
7. **Storing large blobs in SQLite** — For files larger than a few hundred KB, store them on disk and keep the path in the database
8. **Assuming Bun.SQL API is identical to `postgres` (npm)** — While inspired by the `postgres` package, Bun.SQL has differences in configuration and some advanced features
