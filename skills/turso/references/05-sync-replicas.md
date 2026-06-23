# Turso Sync & Embedded Replicas

> Source: [docs.turso.tech/sync](https://docs.turso.tech/sync/usage) | [docs.turso.tech/features/embedded-replicas](https://docs.turso.tech/features/embedded-replicas/introduction)

## Table of Contents
- [Two Sync Approaches](#two-sync-approaches)
- [Turso Sync (Recommended)](#turso-sync-recommended)
- [Embedded Replicas (Legacy)](#embedded-replicas-legacy)
- [Push and Pull Operations](#push-and-pull-operations)
- [Conflict Resolution](#conflict-resolution)
- [Offline-First Architecture](#offline-first-architecture)
- [Checkpoint and WAL Management](#checkpoint-and-wal-management)
- [Partial Sync](#partial-sync)
- [Monitoring Sync State](#monitoring-sync-state)
- [Deployment Patterns](#deployment-patterns)
- [Common Pitfalls](#common-pitfalls)

## Two Sync Approaches

| Feature | Turso Sync (New) | Embedded Replicas (Legacy) |
|---------|-----------------|---------------------------|
| Engine | Turso Database (Rust) | libSQL |
| Sync model | Statement-level push/pull | Page-level replication |
| Write location | Local-first, then push | Remote primary, then sync back |
| Offline writes | Yes (push when online) | Only with `offline: true` |
| Bandwidth | Lower (logical statements) | Higher (4KB page frames) |
| Recommended | Yes, for new projects | Use for existing @libsql/client apps |

## Turso Sync (Recommended)

### Setup

```typescript
import { connect } from "@tursodatabase/sync";

const db = await connect({
  path: "./app.db",                           // Local database file
  url: process.env.TURSO_DATABASE_URL!,       // Cloud primary
  authToken: process.env.TURSO_AUTH_TOKEN!,
});
```

```python
import turso.sync
import os

db = turso.sync.connect(
    "app.db",
    remote_url=os.environ["TURSO_DATABASE_URL"],
    auth_token=os.environ["TURSO_AUTH_TOKEN"],
)
```

```go
syncDb, err := turso.NewTursoSyncDb(ctx, turso.TursoSyncDbConfig{
    Path:      "app.db",
    RemoteUrl: os.Getenv("TURSO_DATABASE_URL"),
    AuthToken: os.Getenv("TURSO_AUTH_TOKEN"),
})
db := syncDb.DB()
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `path` | string | required | Local database file path |
| `url` | string | required | Remote Turso Cloud URL |
| `authToken` | string | required | Authentication token |
| `longPollTimeoutMs` | number | — | Server wait time for pull requests |
| `bootstrapIfEmpty` | boolean | true | Initialize local DB from remote on first connect |

## Embedded Replicas (Legacy)

Uses `@libsql/client` with `syncUrl` parameter:

```typescript
import { createClient } from "@libsql/client";

const client = createClient({
  url: "file:replica.db",                        // Local replica file
  syncUrl: "libsql://db-org.turso.io",           // Cloud primary
  authToken: process.env.TURSO_AUTH_TOKEN!,
  syncInterval: 60,                               // Auto-sync every 60s (optional)
});

// Reads from local replica (microsecond latency)
const users = await client.execute("SELECT * FROM users");

// Writes go to remote primary, then sync back
await client.execute({ sql: "INSERT INTO users (name) VALUES (?)", args: ["Alice"] });

// Manual sync
await client.sync();
```

### Read-Your-Writes Semantics

After a write returns successfully, the replica that initiated the write sees the new data immediately. Other replicas receive updates on their next sync cycle.

## Push and Pull Operations

### Push — Send Local Changes to Cloud

```typescript
await db.push();
```

```python
db.push()
```

```go
syncDb.Push(ctx)
```

Push sends local changes to Turso Cloud using logical statements. The strategy is **last push wins** — if two clients push conflicting changes, the last push takes precedence.

### Pull — Fetch Remote Changes

```typescript
const changed = await db.pull();
// Returns boolean: true if local database was modified
```

```python
db.pull()
```

```go
syncDb.Pull(ctx)
```

Pull fetches and applies remote changes to the local database. Changes may register after pushing due to server-side conflict processing.

### Sync Pattern for Web Servers

```typescript
import { connect } from "@tursodatabase/sync";
import express from "express";

const db = await connect({
  path: "./app.db",
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

// Pull on startup
await db.pull();

// Periodic sync
setInterval(async () => {
  await db.push();
  await db.pull();
}, 30_000); // Every 30 seconds

const app = express();

app.post("/users", async (req, res) => {
  db.prepare("INSERT INTO users (name) VALUES (?)").run(req.body.name);
  await db.push(); // Sync immediately after writes
  res.json({ ok: true });
});
```

## Conflict Resolution

Turso Sync uses **last-push-wins** conflict resolution:

1. Client A pushes `UPDATE users SET name = 'Alice' WHERE id = 1`
2. Client B pushes `UPDATE users SET name = 'Bob' WHERE id = 1`
3. The last push received by the server wins — no merge, no CRDT
4. Both clients see "Bob" after their next pull

For applications requiring custom conflict resolution, design schemas to avoid conflicts:

```sql
-- Append-only design (no conflicts possible)
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    payload TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Per-user isolation (each client owns its data)
CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY,
    settings TEXT NOT NULL
);
```

## Offline-First Architecture

### Bootstrap Control

```typescript
const db = await connect({
  path: "./app.db",
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
  bootstrapIfEmpty: false,  // Don't fetch from remote on first connect
});
```

With `bootstrapIfEmpty: false`, the app starts with an empty local database and can operate fully offline. Changes are pushed when connectivity becomes available.

### Offline Write Pattern

```typescript
// Works without internet
db.prepare("INSERT INTO queue (data) VALUES (?)").run(JSON.stringify(event));

// When online, sync
async function syncWhenOnline() {
  try {
    await db.push();
    await db.pull();
  } catch {
    // Retry later
  }
}
```

## Checkpoint and WAL Management

The local write-ahead log (WAL) grows as changes accumulate. Checkpoint compacts it:

```typescript
await db.checkpoint();
```

```go
syncDb.Checkpoint(ctx)
```

Run checkpoint periodically to bound disk usage, especially on resource-constrained devices.

## Partial Sync

Sync only specific tables or rows to reduce bandwidth:

```typescript
// Partial sync is configured at the database level
// Filter what gets synced to specific namespaces or tables
```

Useful for mobile apps that only need a subset of the server database.

## Monitoring Sync State

```typescript
const stats = await db.stats();
// {
//   cdcOperations: number,       // Total CDC operations tracked
//   mainWalSize: number,         // WAL file size in bytes
//   networkReceivedBytes: number, // Total bytes received from cloud
//   networkSentBytes: number,     // Total bytes sent to cloud
//   lastPullUnixTime: number,    // Unix timestamp of last pull
//   lastPushUnixTime: number,    // Unix timestamp of last push
//   revision: number             // Current sync revision
// }
```

## Deployment Patterns

### VPS / VM (Recommended)

Persistent filesystem enables sync databases. Deploy on Fly.io, Railway, Render, or any VPS.

```
┌─────────────┐       push/pull       ┌──────────────┐
│ Your App    │  ─────────────────►   │ Turso Cloud  │
│ + local.db  │  ◄─────────────────   │ (Primary)    │
└─────────────┘                       └──────────────┘
```

### Serverless (Remote Only)

No persistent filesystem — use `@tursodatabase/serverless` or `@libsql/client` with remote URL only. No sync.

### Multi-Region

```
┌───────────┐         ┌───────────┐
│ US App    │         │ EU App    │
│ + us.db   │         │ + eu.db   │
└─────┬─────┘         └─────┬─────┘
      │                     │
      └────────┬────────────┘
               │
        ┌──────▼──────┐
        │ Turso Cloud │
        │ (Primary    │
        │  us-east)   │
        └─────────────┘
```

## Common Pitfalls

1. **Serverless environments** — Embedded replicas and Turso Sync require persistent filesystems. Lambda, Cloudflare Workers, and similar environments cannot use sync mode
2. **Not calling push after writes** — Local changes are not visible to other clients until pushed
3. **Assuming real-time sync** — Sync is explicit (push/pull) or periodic (syncInterval). It is not real-time streaming
4. **Large WAL without checkpoint** — WAL grows unbounded without periodic `checkpoint()` calls
5. **Conflicting writes** — Last push wins with no merge. Design schemas to minimize conflicts
6. **Bootstrap on slow connections** — First connect with `bootstrapIfEmpty: true` downloads the entire database; set to `false` for offline-first
