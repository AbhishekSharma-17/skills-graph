# Changelog

All notable changes to the `supabase` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-04-19

### Added

Initial release tracking Supabase Platform (March 2026), supabase-js v2.49.x, CLI v2.92.x.

Reference files:

- `00-overview.md` — What Supabase is, architecture (PostgREST, GoTrue, Realtime, etc.), quickstart, credentials, framework guides, pricing.
- `01-database.md` — Tables, data types, primary keys, foreign keys, relationships, views, materialized views, database functions, schemas, extensions, bulk loading.
- `02-authentication.md` — Email/password, magic link, OTP, social login (OAuth with 20+ providers), phone auth, SSO, session management, MFA, user management, auth hooks.
- `03-row-level-security.md` — Enabling RLS, policy types (SELECT/INSERT/UPDATE/DELETE), helper functions (`auth.uid()`, `auth.jwt()`), common patterns (public read, org-based, RBAC, restrictive), performance optimization (6 strategies with benchmarks).
- `04-client-sdk.md` — supabase-js installation, TypeScript types, SELECT with relationships, INSERT/UPDATE/UPSERT/DELETE, 15+ filter operators, modifiers, pagination, RPC, SSR setup with `@supabase/ssr`.
- `05-storage.md` — Buckets, upload (standard/resumable/signed), download, public/signed URLs, file management, image transformations, RLS policies on `storage.objects`, S3-compatible access.
- `06-realtime.md` — Channels, Broadcast (WebSocket/HTTP/database), Presence (track/sync/untrack), Postgres Changes (subscribe/filter by event/column), private channels, connection management.
- `07-edge-functions.md` — Deno runtime, creating/deploying functions, CORS, secrets, database access, webhook handlers, Stripe integration, shared code, scheduling with pg_cron.
- `08-ai-vectors.md` — pgvector, storing vectors, generating embeddings (Edge Function + Python), similarity search, distance operators, HNSW/IVFFlat indexes, hybrid search (semantic + keyword), RAG pattern, metadata filtering.
- `09-cli-local-dev.md` — CLI installation, project setup, local stack (Studio/API/DB/Mailpit), linking to remote, migrations, seed data, type generation, edge function commands, config.toml.
- `10-migrations-deployment.md` — Migration workflow, manual vs auto-diff, environment setup (local/staging/production), GitHub Actions CI/CD (3 workflow files), branching, backups, PITR, rollback strategy.
- `11-rest-graphql-api.md` — PostgREST REST API (CRUD, 16+ filter operators, ordering, pagination, relationships, RPC), pg_graphql (queries, mutations, naming conventions), API access control.
- `12-security-best-practices.md` — Security checklist, key management, RLS best practices, auth security, database security, edge function security, storage security, production readiness, performance tips, common anti-patterns.

Tracking infrastructure:

- `SKILL.md` — Router with 13 routing entries, MANDATORY TRIGGERS, install instructions.
- `VERSION.json` — Pinned to supabase-js 2.49.x / Platform March 2026 with per-file source page mapping.
- `scripts/check-updates.py` — Integrity + staleness + upstream-version checker.
- `AUDIT-REPORT.md` — Quality self-assessment.

### Stats

- **13** routing entries in `SKILL.md`.
- **13** leaf reference files.
- **~4,800** total reference lines.
- **Source version tracked:** supabase-js 2.49.x / Platform March 2026.
- **Docs snapshot date:** 2026-04-19.
