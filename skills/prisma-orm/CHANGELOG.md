# Changelog

## [1.0.0] — 2026-05-04

**Source version tracked:** Prisma ORM 7.x (v7.7.0)

### Added

- **00-overview.md** — What is Prisma, core components, installation, Prisma 7 driver adapters, singleton pattern
- **01-schema-language.md** — Prisma Schema Language: models, scalar types, attributes, enums, native types, multi-file schemas
- **02-relations.md** — One-to-one, one-to-many, many-to-many (implicit/explicit), self-relations, referential actions
- **03-client-crud.md** — Full CRUD API: findMany, findUnique, create, createMany, update, upsert, delete, aggregate, groupBy
- **04-filtering-sorting.md** — Comparison operators, string filters, logical operators, relation filters, sorting, pagination
- **05-select-include.md** — Field selection, relation loading, nested queries, _count, omit, fluent API, relation load strategy
- **06-transactions.md** — Sequential, interactive, nested writes, isolation levels, timeout configuration
- **07-raw-queries.md** — $queryRaw, $executeRaw, Prisma.sql, TypedSQL, MongoDB raw commands, SQL injection prevention
- **08-migrations.md** — migrate dev/deploy/reset, customizing migrations, seeding, baselining, introspection
- **09-client-extensions.md** — Model, result, query, client extensions; computed fields; middleware replacement
- **10-json-fields.md** — JSON read/write, path-based filtering, array filters, DbNull vs JsonNull, type safety
- **11-error-handling.md** — Error types, P2002/P2025 codes, try/catch patterns, reusable error handlers
- **12-performance.md** — N+1 solutions, connection pooling, query optimization, indexing, Prisma Accelerate, serverless

### Stats

- **Routing entries:** 13
- **Reference files:** 13
- **Total lines:** ~4,800
