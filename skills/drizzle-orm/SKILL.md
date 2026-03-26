---
name: drizzle-orm
description: "Type-safe TypeScript ORM for PostgreSQL, MySQL, and SQLite with SQL-like and relational query APIs. MANDATORY TRIGGERS: drizzle, drizzle-orm, drizzle orm, drizzle kit, typescript orm, type-safe sql. Also trigger when user wants to define database schemas in TypeScript, write type-safe SQL queries, manage database migrations with drizzle-kit, set up relational queries with nested data, integrate Zod validation with database schemas, or configure read replicas. When in doubt about whether to use this skill for TypeScript database tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["drizzle", "orm", "typescript", "sql", "postgresql", "mysql", "sqlite", "migrations", "schema"]
---

# Drizzle ORM — Skill Router

> Type-safe TypeScript ORM with zero dependencies, SQL-like queries, relational API, and serverless-ready design.

**Source:** [orm.drizzle.team](https://orm.drizzle.team) v0.45.1 | **Package:** `drizzle-orm` | **License:** Apache 2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, project setup, what Drizzle is, quickstart |
| **Schema Declaration** | `references/01-schema-declaration.md` | Defining tables, column types, defaults, enums, PostgreSQL/MySQL/SQLite schemas |
| **Indexes & Constraints** | `references/02-indexes-constraints.md` | Primary keys, foreign keys, unique, check constraints, composite keys, indexes |
| **Relations** | `references/03-relations.md` | One-to-one, one-to-many, many-to-many, self-referencing, relations API |
| **Select Queries** | `references/04-select-queries.md` | SELECT, filtering, ordering, pagination, aggregations, subqueries, CTEs |
| **Mutations** | `references/05-mutations.md` | INSERT, UPDATE, DELETE, returning, upsert, onConflict, batch operations |
| **Joins** | `references/06-joins.md` | Inner, left, right, full, cross, lateral joins, aliases, partial select |
| **Relational Queries** | `references/07-relational-queries.md` | findMany, findFirst, with, nested relations, extras, prepared statements |
| **Transactions** | `references/08-transactions.md` | Transaction API, nested transactions, savepoints, isolation levels, rollback |
| **Migrations** | `references/09-migrations.md` | drizzle-kit generate, push, migrate, pull, config, workflows |
| **Performance** | `references/10-performance.md` | Prepared statements, placeholders, read replicas, query optimization |
| **Validation** | `references/11-validation.md` | Zod integration, insert/select/update schemas, refinements, schema factory |

## Installation

```bash
# Install Drizzle ORM + Kit
npm install drizzle-orm
npm install -D drizzle-kit

# Database drivers (pick one)
npm install postgres        # PostgreSQL (postgres.js)
npm install @neondatabase/serverless  # Neon
npm install mysql2          # MySQL
npm install better-sqlite3  # SQLite
```

## Quick Reference

- **Docs:** https://orm.drizzle.team
- **GitHub:** https://github.com/drizzle-team/drizzle-orm
- **npm:** https://www.npmjs.com/package/drizzle-orm
- **Discord:** https://driz.link/discord
