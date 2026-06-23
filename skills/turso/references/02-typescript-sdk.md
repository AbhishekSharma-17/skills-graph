# Turso TypeScript / JavaScript SDK

> Source: [docs.turso.tech/sdk/ts](https://docs.turso.tech/sdk/ts/reference)

## Table of Contents
- [Package Selection](#package-selection)
- [Local / Embedded (database)](#local--embedded-database)
- [Remote / Serverless](#remote--serverless)
- [ORM-Compatible (@libsql/client)](#orm-compatible-libsqlclient)
- [Sync-Enabled](#sync-enabled)
- [Query Methods](#query-methods)
- [Parameter Binding](#parameter-binding)
- [Batch Operations](#batch-operations)
- [Interactive Transactions](#interactive-transactions)
- [Embedded Replicas (libsql/client)](#embedded-replicas-libsqlclient)
- [Encryption](#encryption)
- [Runtime Compatibility](#runtime-compatibility)
- [Common Pitfalls](#common-pitfalls)

## Package Selection

| Package | Use Case | Dependencies |
|---------|----------|-------------|
| `@tursodatabase/database` | Local/embedded, MVCC, async I/O | Native (Rust bindings) |
| `@tursodatabase/sync` | Local + cloud push/pull sync | Native (Rust bindings) |
| `@tursodatabase/serverless` | Remote-only, serverless/edge | Zero (fetch-based) |
| `@libsql/client` | ORM integration (Drizzle, Prisma) | libSQL engine |

For new projects, prefer `@tursodatabase/database` (local) or `@tursodatabase/sync` (local + cloud). Use `@libsql/client` when integrating with Drizzle or Prisma.

## Local / Embedded (database)

```bash
npm install @tursodatabase/database
```

```typescript
import { connect } from "@tursodatabase/database";

// File-based database
const db = await connect("app.db");

// In-memory database
const db = await connect(":memory:");

// Prepare and execute
const stmt = db.prepare("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)");
await stmt.run();

// Insert data
const insert = db.prepare("INSERT INTO users (name) VALUES (?)");
await insert.run("Alice");

// Query data
const select = db.prepare("SELECT * FROM users");
const users = await select.all();

// Single row
const user = db.prepare("SELECT * FROM users WHERE id = ?");
const row = await user.get([1]);
```

## Remote / Serverless

```bash
npm install @tursodatabase/serverless
```

```typescript
import { connect } from "@tursodatabase/serverless";

const conn = connect({
  url: process.env.TURSO_DATABASE_URL!,    // libsql://db-org.turso.io
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

// Prepare and execute
const stmt = await conn.prepare("SELECT * FROM users WHERE id = ?");
const row = await stmt.get([1]);
const rows = await stmt.all();
```

### Compat Mode (libsql/client API)

```typescript
import { createClient } from "@tursodatabase/serverless/compat";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

const result = await client.execute("SELECT * FROM users");
```

## ORM-Compatible (@libsql/client)

```bash
npm install @libsql/client
```

### Remote Connection

```typescript
import { createClient } from "@libsql/client";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,    // libsql://db-org.turso.io
  authToken: process.env.TURSO_AUTH_TOKEN!,
});
```

### Local Development

```typescript
// File-based
const client = createClient({ url: "file:local.db" });

// In-memory
const client = createClient({ url: ":memory:" });
```

### Edge Runtime

```typescript
// For Cloudflare Workers, Vercel Edge, etc.
import { createClient } from "@libsql/client/web";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});
```

## Sync-Enabled

```bash
npm install @tursodatabase/sync
```

```typescript
import { connect } from "@tursodatabase/sync";

const db = await connect({
  path: "./app.db",
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

// All reads/writes happen locally
db.prepare("INSERT INTO users (name) VALUES (?)").run("Alice");
const users = db.prepare("SELECT * FROM users").all();

// Explicitly sync with cloud
await db.push();   // Send local changes to cloud
const changed = await db.pull();  // Fetch remote changes

// Compact local WAL
await db.checkpoint();

// Get sync statistics
const stats = await db.stats();
// { cdcOperations, mainWalSize, networkReceivedBytes, networkSentBytes,
//   lastPullUnixTime, lastPushUnixTime, revision }
```

## Query Methods

### Simple Execute (libsql/client)

```typescript
// String shorthand
const result = await client.execute("SELECT * FROM users");

// Object form with parameters
const result = await client.execute({
  sql: "SELECT * FROM users WHERE id = ?",
  args: [1],
});
```

### ResultSet Structure

```typescript
interface ResultSet {
  rows: Array<Row>;          // Retrieved data
  columns: Array<string>;    // Column names
  rowsAffected: number;      // Rows modified by INSERT/UPDATE/DELETE
  lastInsertRowid: bigint | undefined;  // Auto-increment ID
}
```

### Row Access

```typescript
const result = await client.execute("SELECT id, name FROM users");

// Array-style access
result.rows[0][0]; // id
result.rows[0][1]; // name

// Object-style access
result.rows[0].id;
result.rows[0].name;
```

## Parameter Binding

### Positional Parameters

```typescript
const result = await client.execute({
  sql: "SELECT * FROM users WHERE id = ? AND name = ?",
  args: [1, "Alice"],
});
```

### Named Parameters

```typescript
// Colon prefix
const result = await client.execute({
  sql: "INSERT INTO users (name, email) VALUES (:name, :email)",
  args: { name: "Alice", email: "alice@example.com" },
});

// @ prefix also works
const result = await client.execute({
  sql: "SELECT * FROM users WHERE name = @name",
  args: { name: "Alice" },
});

// $ prefix also works
const result = await client.execute({
  sql: "SELECT * FROM users WHERE id = $id",
  args: { id: 1 },
});
```

## Batch Operations

Execute multiple statements atomically:

```typescript
const results = await client.batch(
  [
    { sql: "INSERT INTO users (name) VALUES (?)", args: ["Alice"] },
    { sql: "INSERT INTO users (name) VALUES (?)", args: ["Bob"] },
    { sql: "SELECT COUNT(*) as count FROM users", args: [] },
  ],
  "write"  // Transaction mode: "write" | "read" | "deferred"
);

// results[0].rowsAffected → 1
// results[1].rowsAffected → 1
// results[2].rows[0].count → total users
```

## Interactive Transactions

```typescript
const tx = await client.transaction("write");

try {
  const { rows } = await tx.execute({
    sql: "SELECT balance FROM accounts WHERE id = ?",
    args: [userId],
  });

  const balance = rows[0].balance as number;
  const newBalance = balance - amount;

  if (newBalance < 0) {
    await tx.rollback();
    throw new Error("Insufficient funds");
  }

  await tx.execute({
    sql: "UPDATE accounts SET balance = ? WHERE id = ?",
    args: [newBalance, userId],
  });

  await tx.execute({
    sql: "INSERT INTO transactions (account_id, amount, type) VALUES (?, ?, ?)",
    args: [userId, amount, "debit"],
  });

  await tx.commit();
} catch (e) {
  await tx.rollback();
  throw e;
}
```

### Transaction Modes

| Mode | SQLite Command | Use |
|------|---------------|-----|
| `write` | `BEGIN IMMEDIATE` | Read/write operations |
| `read` | `BEGIN TRANSACTION READONLY` | Read-only queries |
| `deferred` | `BEGIN DEFERRED` | Start read, upgrade to write on demand |

## Embedded Replicas (libsql/client)

```typescript
const client = createClient({
  url: "file:replica.db",                      // Local file
  syncUrl: "libsql://db-org.turso.io",         // Cloud primary
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

// Manual sync
await client.sync();

// Periodic sync (every 60 seconds)
const client = createClient({
  url: "file:replica.db",
  syncUrl: "libsql://db-org.turso.io",
  authToken: process.env.TURSO_AUTH_TOKEN!,
  syncInterval: 60,
});
```

## Encryption

```typescript
const db = await connect("encrypted.db", {
  encryption: {
    cipher: "aegis256",
    hexkey: "b1bbfda4f589dc9daaf004fe21111e00dc00c98237102f5c7002a5669fc76327",
  },
});
```

Supported ciphers: `aegis256`, `aegis256x2`, `aegis128l`, `aegis128x2`, `aegis128x4`, `aes256gcm`, `aes128gcm`.

## Runtime Compatibility

- Node.js 12+
- Deno
- Bun
- Cloudflare Workers (use `@tursodatabase/serverless` or `@libsql/client/web`)
- Vercel Edge Functions
- Netlify Edge Functions

## Common Pitfalls

1. **Wrong package for your environment** — `@tursodatabase/database` requires native bindings; use `@tursodatabase/serverless` for edge/serverless runtimes
2. **Forgetting `await` on queries** — All query methods return promises
3. **Not calling `sync()` or `push()/pull()`** — Embedded replicas and sync-enabled databases don't auto-sync unless `syncInterval` is set
4. **Using `@libsql/client` for local without `file:` prefix** — Local URLs must start with `file:` (e.g., `file:local.db`)
5. **Transaction mode mismatch** — Using `"read"` mode then attempting writes causes errors; use `"write"` for any modifications
6. **Concurrency limit** — Default is 20 concurrent requests per client; configure with `concurrency` option
