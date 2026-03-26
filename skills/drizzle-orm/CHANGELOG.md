# Changelog — drizzle-orm skill

## [1.0.0] — 2026-03-26

**Source version tracked:** drizzle-orm 0.45.1

### Added

- **00-overview.md** — What Drizzle is, installation, database drivers, connection setup, project structure, quickstart
- **01-schema-declaration.md** — Table definitions for PostgreSQL/MySQL/SQLite, column types, enums, defaults, identity columns, generated columns, custom types, type inference
- **02-indexes-constraints.md** — Primary keys, composite keys, foreign keys, unique constraints, check constraints, indexes, PostgreSQL/MySQL index features
- **03-relations.md** — One-to-one, one-to-many, many-to-many, self-referencing, named relations, disambiguation, relations vs foreign keys
- **04-select-queries.md** — SELECT, partial select, filtering, operators, ordering, pagination, distinct, aggregations, group by, subqueries, CTEs, dynamic queries
- **05-mutations.md** — INSERT, batch insert, returning, upsert (onConflict), INSERT SELECT, UPDATE, UPDATE FROM, DELETE, type inference
- **06-joins.md** — Inner, left, right, full, cross, lateral joins, aliases, self-joins, partial select with joins
- **07-relational-queries.md** — findMany, findFirst, nested relations with `with`, column selection, filtering, ordering, pagination, extras, prepared statements
- **08-transactions.md** — Transaction API, returning values, rollback, nested transactions/savepoints, isolation levels, common patterns
- **09-migrations.md** — drizzle-kit config, generate, migrate, push, pull, runtime migrations, workflows, Drizzle Studio
- **10-performance.md** — Prepared statements, placeholders, read replicas, custom replica selection, optimization tips, logging
- **11-validation.md** — Zod integration, select/insert/update schemas, refinements, schema factory, Valibot/TypeBox, practical patterns

### Stats

- Routing entries: 12
- Reference files: 12
- Total lines: ~3,800
