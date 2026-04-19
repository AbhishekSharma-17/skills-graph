---
name: supabase
description: "Supabase — the open-source Firebase alternative built on Postgres with Auth, Storage, Realtime, Edge Functions, and AI Vectors. MANDATORY TRIGGERS: supabase, supabase-js, @supabase/supabase-js, createClient supabase, supabase.auth, supabase.from, supabase.storage, supabase.channel, supabase.functions, supabase edge functions, supabase realtime, supabase auth, supabase storage, supabase rls, row level security, supabase cli, supabase init, supabase start, supabase migration, supabase vectors, pgvector supabase, supabase project. Also trigger when the user asks about building an app with Postgres backend-as-a-service, Firebase alternative, serverless Postgres, real-time database subscriptions, or managed auth with RLS. When in doubt about whether to use this skill for Supabase tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["supabase", "postgres", "baas", "auth", "realtime", "edge-functions"]
---

# Supabase

> **Skill Version:** 1.0.0 | **Tracks:** supabase-js v2.49, Supabase Platform (March 2026) | **Source:** https://supabase.com/docs

Supabase is the open-source Firebase alternative built on PostgreSQL. Every project gets a full Postgres database, authentication, file storage, real-time subscriptions, edge functions, and vector search — all accessible via auto-generated REST and GraphQL APIs or client libraries for JavaScript, Python, Flutter, Swift, and Kotlin.

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Architecture** | `references/00-overview.md` | "what is supabase", "install supabase", "getting started", "supabase architecture" |
| **Database & Tables** | `references/01-database.md` | "create table", "data types", "foreign keys", "views", "functions", "schemas" |
| **Authentication** | `references/02-authentication.md` | "sign up", "sign in", "OAuth", "social login", "MFA", "SSO", "sessions", "JWT" |
| **Row Level Security** | `references/03-row-level-security.md` | "RLS", "row level security", "policies", "auth.uid()", "security policies" |
| **Client SDK** | `references/04-client-sdk.md` | "supabase-js", "createClient", "select", "insert", "update", "delete", "filters" |
| **Storage** | `references/05-storage.md` | "file upload", "storage bucket", "presigned URL", "image transform", "CDN" |
| **Realtime** | `references/06-realtime.md` | "realtime", "broadcast", "presence", "postgres changes", "channels", "subscribe" |
| **Edge Functions** | `references/07-edge-functions.md` | "edge functions", "Deno", "supabase functions", "invoke", "deploy function" |
| **AI & Vectors** | `references/08-ai-vectors.md` | "pgvector", "embeddings", "vector search", "similarity", "RAG", "ai supabase" |
| **CLI & Local Development** | `references/09-cli-local-dev.md` | "supabase cli", "supabase init", "supabase start", "local dev", "supabase link" |
| **Migrations & Deployment** | `references/10-migrations-deployment.md` | "migration", "db diff", "staging", "production", "CI/CD", "environments" |
| **REST & GraphQL APIs** | `references/11-rest-graphql-api.md` | "PostgREST", "REST API", "GraphQL", "pg_graphql", "auto-generated API" |
| **Security & Best Practices** | `references/12-security-best-practices.md` | "security checklist", "common pitfalls", "performance", "production readiness" |

## Installation

```bash
# JavaScript/TypeScript
npm install @supabase/supabase-js

# Python
pip install supabase

# Supabase CLI (macOS/Linux)
brew install supabase/tap/supabase

# Copy skill to Claude Code
cp -r . ~/.claude/skills/supabase/
```

## Quick Reference

- **Docs:** https://supabase.com/docs
- **GitHub:** https://github.com/supabase/supabase
- **Dashboard:** https://supabase.com/dashboard
- **Client Libraries:** https://supabase.com/docs/reference
- **Status:** https://status.supabase.com
