# Turso Production Deployment & Best Practices

> Source: [docs.turso.tech](https://docs.turso.tech/cloud/limitations) | [docs.turso.tech/agentfs](https://docs.turso.tech/agentfs/introduction)

## Table of Contents
- [Deployment Architectures](#deployment-architectures)
- [Framework Integration Guides](#framework-integration-guides)
- [AgentFS — AI Agent Filesystem](#agentfs--ai-agent-filesystem)
- [Performance Best Practices](#performance-best-practices)
- [Turso Cloud Limitations](#turso-cloud-limitations)
- [Migration from SQLite](#migration-from-sqlite)
- [Monitoring and Observability](#monitoring-and-observability)
- [Common Pitfalls](#common-pitfalls)

## Deployment Architectures

### Serverless (Vercel, Cloudflare Workers, AWS Lambda)

No persistent filesystem — use remote connection only:

```typescript
// Vercel Edge Function
import { createClient } from "@libsql/client/web";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

export const runtime = "edge";

export async function GET() {
  const { rows } = await client.execute("SELECT * FROM posts LIMIT 10");
  return Response.json(rows);
}
```

### VPS / VM with Sync (Fly.io, Railway, Render)

Persistent filesystem enables embedded replicas or Turso Sync:

```typescript
// server.ts — Sync-enabled for microsecond reads
import { connect } from "@tursodatabase/sync";

const db = await connect({
  path: "/data/app.db",
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

// Pull on startup
await db.pull();

// Periodic sync
setInterval(async () => {
  try {
    await db.push();
    await db.pull();
  } catch (e) {
    console.error("Sync failed:", e);
  }
}, 30_000);
```

### Self-Hosted (libSQL Server)

Run libSQL server for full control without Turso Cloud:

```bash
# Install and run libSQL server
cargo install libsql-server

# Start server
libsql-server --db-path ./data/app.db --http-listen-addr 0.0.0.0:8080
```

## Framework Integration Guides

### Next.js

```typescript
// lib/turso.ts
import { createClient } from "@libsql/client/web";

export const turso = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

// app/api/users/route.ts
import { turso } from "@/lib/turso";
import { NextResponse } from "next/server";

export async function GET() {
  const { rows } = await turso.execute("SELECT * FROM users");
  return NextResponse.json(rows);
}
```

### Hono

```typescript
import { Hono } from "hono";
import { createClient } from "@libsql/client";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

const app = new Hono();

app.get("/users", async (c) => {
  const { rows } = await client.execute("SELECT * FROM users");
  return c.json(rows);
});

export default app;
```

### FastAPI (Python)

```python
from fastapi import FastAPI, Depends
import turso

app = FastAPI()

def get_db():
    db = turso.connect("app.db")
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
async def list_users(db=Depends(get_db)):
    rows = db.execute("SELECT * FROM users").fetchall()
    columns = ["id", "name", "email"]
    return [dict(zip(columns, row)) for row in rows]
```

## AgentFS — AI Agent Filesystem

AgentFS is a filesystem abstraction for AI agents built on Turso's SQLite infrastructure.

### Installation

```bash
# macOS / Linux
curl -sSfL https://get.agentfs.dev/install.sh | bash

# Verify
agentfs --version
```

### Core Features

- **Copy-on-Write Isolation** — Agents modify files without affecting originals
- **Single File Storage** — All data in one portable SQLite database
- **Built-in Auditing** — Every file operation is recorded and queryable
- **Cloud Sync** — Optional synchronization to Turso Cloud

### Usage

```bash
# Start a sandboxed session in current directory
agentfs run bash

# Run an AI coding agent in a sandbox
agentfs run -- claude --dangerously-skip-permissions

# Named sessions (for sharing state between agents)
agentfs run --session my-feature bash
```

### MCP Server Mode

```bash
# Start AgentFS as an MCP server for AI assistants
agentfs mcp
```

### Auditing

```bash
# Inspect what an agent did
agentfs audit

# Query specific file operations
agentfs audit --table files --query "SELECT * FROM files WHERE path LIKE '%.py'"
```

### SDK Usage

```typescript
import { AgentFS } from "@agentfs/sdk";

const fs = new AgentFS({ session: "my-agent" });

// File operations (copy-on-write isolated)
await fs.writeFile("config.json", JSON.stringify({ key: "value" }));
const content = await fs.readFile("config.json");

// Audit trail
const changes = await fs.audit();
```

## Performance Best Practices

### Connection Management

```typescript
// GOOD: Reuse client instance
const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
  concurrency: 20,  // Max concurrent requests (default: 20)
});

// BAD: Creating client per request
app.get("/users", async (req, res) => {
  const client = createClient({...}); // Don't do this
});
```

### Batch Operations

```typescript
// GOOD: Batch multiple operations
await client.batch([
  { sql: "INSERT INTO users (name) VALUES (?)", args: ["Alice"] },
  { sql: "INSERT INTO users (name) VALUES (?)", args: ["Bob"] },
], "write");

// BAD: Individual calls
await client.execute({ sql: "INSERT...", args: ["Alice"] });
await client.execute({ sql: "INSERT...", args: ["Bob"] });
```

### Indexing

```sql
-- Index frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_posts_user_published ON posts(user_id, published);

-- Partial indexes for filtered queries
CREATE INDEX idx_active_users ON users(email) WHERE active = 1;

-- Analyze for query planner
ANALYZE;
```

### Query Optimization

```sql
-- Use EXPLAIN to check query plans
EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = 'alice@example.com';

-- Prefer EXISTS over COUNT for existence checks
SELECT EXISTS(SELECT 1 FROM users WHERE email = ?);

-- Limit result sets
SELECT * FROM posts ORDER BY created_at DESC LIMIT 20 OFFSET 0;
```

## Turso Cloud Limitations

| Limitation | Details |
|-----------|---------|
| Max database size | Varies by plan (Starter: 500MB, Pro: 10GB) |
| Max databases | Varies by plan (Starter: 500, Pro: 10,000) |
| Row size | 2MB max per row |
| SQL statement size | 1MB max |
| Concurrent connections | Plan-dependent |
| Regions | 35+ available locations |
| Extensions | Must be enabled at group creation |
| WAL mode | Default; cannot switch to rollback journal |

### SQLite Compatibility Notes

- Most SQLite features work identically
- `VACUUM` works but may be slow on large databases
- `ATTACH DATABASE` is supported but deprecated in favor of multi-DB schemas
- User-defined functions are not supported in Turso Cloud (use locally)
- `LOAD_EXTENSION` is not available in Turso Cloud

## Migration from SQLite

### Import Existing Database

```bash
# Upload a local SQLite file to Turso Cloud
turso db create my-app --from-file ./existing.db

# Or import into an existing database
turso db import my-app ./data.db
```

### Code Changes Required

```typescript
// Before (better-sqlite3)
import Database from "better-sqlite3";
const db = new Database("app.db");
const users = db.prepare("SELECT * FROM users").all();

// After (Turso — local)
import { connect } from "@tursodatabase/database";
const db = await connect("app.db");
const stmt = db.prepare("SELECT * FROM users");
const users = await stmt.all();

// After (Turso — remote)
import { createClient } from "@libsql/client";
const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});
const { rows: users } = await client.execute("SELECT * FROM users");
```

### Key Differences from SQLite

- All SDK methods are async (return promises)
- Remote connections require auth tokens
- `PRAGMA` support varies — some pragmas are not available in Turso Cloud
- File locking behavior differs with MVCC enabled

## Monitoring and Observability

### Database Stats

```bash
turso db inspect my-app
```

### Sentry Integration

```typescript
import * as Sentry from "@sentry/node";
import { createClient } from "@libsql/client";

// The @libsql/client supports Sentry integration
// for tracing slow queries and capturing SQL errors
```

### Sync Statistics

```typescript
const stats = await db.stats();
console.log({
  walSize: stats.mainWalSize,
  bytesSent: stats.networkSentBytes,
  bytesReceived: stats.networkReceivedBytes,
  lastPush: new Date(stats.lastPushUnixTime * 1000),
  lastPull: new Date(stats.lastPullUnixTime * 1000),
});
```

## Common Pitfalls

1. **Serverless + sync** — Sync-enabled databases require persistent storage. Don't use with Lambda or Workers
2. **Large row sizes** — Turso has a 2MB row limit. Store large blobs in object storage (S3, R2) and reference them
3. **Missing indexes** — Query plans scan tables without indexes. Use `EXPLAIN QUERY PLAN` to verify
4. **Not batching writes** — Individual INSERT calls over the network are slow. Use `batch()` for multiple operations
5. **Stale replicas** — Embedded replicas and sync databases can serve stale reads between sync cycles. Design for eventual consistency
6. **Agent sandbox scope** — AgentFS sandboxes are per-session. Different sessions see different filesystem states
7. **Connection leaks** — Always close database connections in request handlers and teardown hooks
8. **VACUUM timing** — Running VACUUM on large databases blocks all writes. Schedule during low-traffic periods
