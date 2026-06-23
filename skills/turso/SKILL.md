---
name: turso
description: "Edge-first SQLite database platform built on libSQL. MANDATORY TRIGGERS: Turso, turso, libSQL, libsql, tursodatabase, edge SQLite, embedded replicas, turso sync. Also trigger when the user wants an edge database, per-user SQLite databases, local-first database with cloud sync, vector search in SQLite, or multi-tenant SQLite. When in doubt about whether to use this skill for edge database tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["database", "sqlite", "edge", "libsql", "embedded-replicas", "vector-search", "local-first"]
---

# Turso — Edge-First SQLite Database

> Source: [docs.turso.tech](https://docs.turso.tech) — Turso Database v0.6.1 / libSQL

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Need to understand what Turso/libSQL is, architecture, or installation |
| [01-getting-started.md](references/01-getting-started.md) | Setting up CLI, creating databases, basic SQL operations |
| [02-typescript-sdk.md](references/02-typescript-sdk.md) | Using Turso from TypeScript/JavaScript (all packages) |
| [03-python-sdk.md](references/03-python-sdk.md) | Using Turso from Python (pyturso and libsql packages) |
| [04-go-sdk.md](references/04-go-sdk.md) | Using Turso from Go (tursogo and libsql-client-go) |
| [05-sync-replicas.md](references/05-sync-replicas.md) | Embedded replicas, Turso Sync, push/pull, offline-first |
| [06-vector-search.md](references/06-vector-search.md) | Vector similarity search, embeddings, DiskANN indexes, RAG |
| [07-full-text-search.md](references/07-full-text-search.md) | Tantivy-powered FTS, tokenizers, BM25 ranking, highlighting |
| [08-orm-integrations.md](references/08-orm-integrations.md) | Drizzle ORM, Prisma, SQLAlchemy integration with Turso |
| [09-platform-api.md](references/09-platform-api.md) | REST API for databases, groups, tokens, multi-tenancy |
| [10-auth-security.md](references/10-auth-security.md) | Tokens, JWKS, fine-grained permissions, encryption |
| [11-advanced-features.md](references/11-advanced-features.md) | CDC, concurrent writes (MVCC), branching, point-in-time recovery |
| [12-production.md](references/12-production.md) | Deployment, AgentFS, performance, limitations, best practices |

## Installation

```bash
# CLI (macOS/Linux)
curl -sSfL https://get.tur.so/install.sh | bash

# Turso DB engine
cargo install tursodb

# TypeScript
npm install @tursodatabase/database      # Local/embedded
npm install @tursodatabase/serverless    # Remote/serverless
npm install @libsql/client               # ORM compatibility

# Python
pip install pyturso   # Local/embedded
pip install libsql    # Remote access

# Go
go get turso.tech/database/tursogo
```

## Quick Reference

- [Turso Docs](https://docs.turso.tech)
- [GitHub — tursodatabase/turso](https://github.com/tursodatabase/turso)
- [libSQL GitHub](https://github.com/tursodatabase/libsql)
- [Turso Cloud Dashboard](https://turso.tech/app)
