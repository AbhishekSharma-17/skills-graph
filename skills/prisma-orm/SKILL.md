---
name: prisma-orm
description: "Next-generation Node.js and TypeScript ORM with type-safe database access, declarative schema, migrations, and query building. MANDATORY TRIGGERS: prisma, Prisma, PrismaClient, prisma.schema, prisma migrate, prisma generate, @prisma/client, Prisma ORM. Also trigger when user wants to define database models in TypeScript, run type-safe queries, manage database migrations, set up an ORM for PostgreSQL/MySQL/SQLite/MongoDB, handle relations and joins, or optimize database queries in Node.js. When in doubt about whether to use this skill for database ORM tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["prisma", "orm", "database", "typescript", "postgresql", "mysql", "sqlite", "mongodb", "migrations", "type-safe"]
---

# Prisma ORM — Skill Router

> Next-generation ORM for Node.js & TypeScript — type-safe queries, declarative schema, automated migrations.

**Source:** [prisma.io/docs](https://www.prisma.io/docs) | **Package:** `@prisma/client` v7.x | **License:** Apache-2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Installation, Prisma 7 setup, driver adapters, project init |
| **Schema Language** | `references/01-schema-language.md` | Models, fields, scalar types, attributes, enums, type modifiers |
| **Relations** | `references/02-relations.md` | One-to-one, one-to-many, many-to-many, self-relations, referential actions |
| **Client CRUD** | `references/03-client-crud.md` | findMany, findUnique, create, update, upsert, delete, batch operations |
| **Filtering & Sorting** | `references/04-filtering-sorting.md` | where clauses, operators, AND/OR/NOT, relation filters, orderBy, pagination |
| **Select & Include** | `references/05-select-include.md` | Field selection, relation loading, nested queries, _count, omit |
| **Transactions** | `references/06-transactions.md` | Sequential, interactive, nested writes, isolation levels, timeouts |
| **Raw Queries** | `references/07-raw-queries.md` | $queryRaw, $executeRaw, tagged templates, TypedSQL, SQL injection prevention |
| **Migrations** | `references/08-migrations.md` | migrate dev, deploy, reset, seeding, baseline, production workflows |
| **Client Extensions** | `references/09-client-extensions.md` | $extends, model/query/result/client extensions, computed fields |
| **JSON Fields** | `references/10-json-fields.md` | JSON read/write, path filtering, array filters, DbNull vs JsonNull |
| **Error Handling** | `references/11-error-handling.md` | Error types, P2002/P2025 codes, try/catch patterns, validation errors |
| **Performance** | `references/12-performance.md` | N+1 solutions, connection pooling, Accelerate, query optimization |

## Installation

```bash
# Install Prisma CLI and Client (Prisma 7 — PostgreSQL)
npm install prisma --save-dev
npm install @prisma/client @prisma/adapter-pg pg

# Initialize Prisma
npx prisma init

# Generate client after schema changes
npx prisma generate

# Create and apply migration
npx prisma migrate dev --name init

# Deploy migrations in production
npx prisma migrate deploy
```

## Quick Reference

- **Docs:** https://www.prisma.io/docs
- **GitHub:** https://github.com/prisma/prisma
- **npm:** https://www.npmjs.com/package/@prisma/client
- **Changelog:** https://www.prisma.io/changelog
- **Playground:** https://playground.prisma.io
