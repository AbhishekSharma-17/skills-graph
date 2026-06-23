# Turso & libSQL Overview

> Source: [docs.turso.tech](https://docs.turso.tech) — Turso v0.6.1

## What Is Turso

Turso is an edge-first SQLite-compatible database platform. It consists of two core components:

1. **Turso Database Engine** — A ground-up rewrite of SQLite in Rust with MVCC concurrent writes, native async I/O, built-in vector search, change data capture, and encryption at rest
2. **Turso Cloud** — A managed platform that distributes libSQL databases across 35+ edge regions with embedded replicas, branching, and a REST API for programmatic management

**libSQL** is a production-ready fork of SQLite maintained by Turso. It is fully backwards-compatible with SQLite but adds features like native vector search, WASM-based extensions, and server mode with HTTP/WebSocket access.

## When to Use Turso

| Use Case | Why Turso |
|----------|-----------|
| Per-user databases | Create isolated databases per user or tenant via the Platform API |
| Local-first apps | Embedded replicas give microsecond reads with cloud sync |
| AI/RAG applications | Native vector similarity search without extensions |
| Edge computing | Databases replicated to 35+ regions, close to users |
| Mobile/offline apps | Sync-enabled local databases work without connectivity |
| AI agent state | AgentFS provides sandboxed filesystem on top of Turso |

## When NOT to Use Turso

- Heavy OLAP/analytical workloads (use ClickHouse, DuckDB)
- Complex relational schemas with many JOINs across large tables (use PostgreSQL)
- High-write throughput (>10K writes/sec sustained) without MVCC
- Workloads requiring stored procedures or advanced SQL features beyond SQLite's dialect

## Architecture

```
┌─────────────────────────────────────────────┐
│               Your Application              │
├─────────┬──────────┬──────────┬─────────────┤
│ TS SDK  │ Python   │ Go SDK   │ HTTP/SQL    │
│         │ SDK      │          │ over HTTP   │
├─────────┴──────────┴──────────┴─────────────┤
│           Connection Modes                   │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐  │
│  │  Local   │ │  Remote   │ │   Sync     │  │
│  │ (file:)  │ │ (libsql:) │ │ (push/pull)│  │
│  └──────────┘ └───────────┘ └────────────┘  │
├──────────────────────────────────────────────┤
│         Turso Database Engine (Rust)         │
│  MVCC │ Vector Search │ FTS │ CDC │ Encrypt  │
├──────────────────────────────────────────────┤
│             Turso Cloud (Optional)           │
│  35+ Regions │ Branching │ Platform API      │
└──────────────────────────────────────────────┘
```

## Three Connection Modes

### Local / Embedded
Runs entirely in-process. No server needed. Data stored in a local SQLite file.

```typescript
import { connect } from "@tursodatabase/database";
const db = await connect("app.db");
```

### Remote / Serverless
Connects to Turso Cloud over HTTP. Zero native dependencies. Works in serverless environments.

```typescript
import { connect } from "@tursodatabase/serverless";
const conn = connect({
  url: process.env.TURSO_DATABASE_URL,
  authToken: process.env.TURSO_AUTH_TOKEN,
});
```

### Sync (Local + Cloud)
Local reads and writes with explicit push/pull to cloud. Offline-capable.

```typescript
import { connect } from "@tursodatabase/sync";
const db = await connect({
  path: "./app.db",
  url: process.env.TURSO_DATABASE_URL,
  authToken: process.env.TURSO_AUTH_TOKEN,
});
await db.push(); // Send local changes to cloud
await db.pull(); // Fetch remote changes
```

## Installation

### Turso CLI

```bash
# macOS / Linux
curl -sSfL https://get.tur.so/install.sh | bash

# Windows (PowerShell)
iwr https://get.tur.so/install.ps1 -useb | iex

# Verify
turso --version
```

### Turso Database Engine (Standalone)

```bash
cargo install tursodb

# Run interactive shell
tursodb

# Open/create a database file
tursodb app.db
```

### SDK Packages

```bash
# TypeScript/JavaScript
npm install @tursodatabase/database      # Local/embedded
npm install @tursodatabase/sync          # Sync-enabled
npm install @tursodatabase/serverless    # Remote/serverless
npm install @libsql/client               # ORM compatibility (Drizzle, Prisma)

# Python
pip install pyturso   # Local/embedded + sync
pip install libsql    # Remote access

# Go
go get turso.tech/database/tursogo       # database/sql driver
go get github.com/tursodatabase/libsql-client-go/libsql  # Remote
```

## Key Concepts

### Groups
Databases are organized into **groups**. A group defines a primary region and optional replica regions. All databases in a group share the same replication topology.

### Embedded Replicas
Local SQLite files that sync with a Turso Cloud primary. Reads happen locally in microseconds; writes route to the cloud primary and sync back.

### libSQL Protocol
Turso uses the `libsql://` protocol for remote connections. Databases are addressed as `libsql://[database]-[org].turso.io`.

### Platform API
REST API for programmatic database management — create/delete databases, generate scoped tokens, manage organizations. Enables multi-tenant architectures.

## Turso vs SQLite vs Other Databases

| Feature | SQLite | Turso/libSQL | PostgreSQL |
|---------|--------|-------------|------------|
| Deployment | Embedded | Embedded + Cloud | Server |
| Concurrency | Single writer | MVCC (multiple writers) | MVCC |
| Vector search | Extension (sqlite-vec) | Native | Extension (pgvector) |
| Full-text search | FTS5 | Tantivy-powered | Built-in |
| Replication | None | Embedded replicas + Sync | Streaming replication |
| Multi-tenant | Manual | Platform API (per-user DBs) | Schemas/databases |
| Edge deployment | Manual | 35+ regions | Complex |
| File format | .db | .db (compatible) | Custom |

## Version History

- **v0.6.1** (May 2026) — Current release
- Written in Rust (85.8%), with SDKs for JS, Python, Go, Rust, C, PHP, Ruby, Swift, Kotlin, Dart
- Beta status — production-proven at Turso Cloud, Kin AI, Spice.ai
