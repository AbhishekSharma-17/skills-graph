---
name: convex
description: "Reactive backend platform with real-time sync, ACID transactions, and TypeScript-first development. MANDATORY TRIGGERS: convex, convex.dev, ConvexProvider, useQuery, useMutation, useAction, convex functions, convex schema, convex database, convex deploy. Also trigger when user wants to build real-time apps with automatic sync, reactive backends, serverless databases with TypeScript, or full-stack apps without infrastructure. When in doubt about whether to use this skill for reactive backend or real-time sync tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["convex", "backend", "real-time", "reactive", "database", "serverless", "typescript", "baas", "full-stack"]
---

# Convex — Skill Router

> The reactive backend platform: real-time database, server functions, file storage, scheduling, and search — all with automatic TypeScript type safety and zero infrastructure.

**Source:** [docs.convex.dev](https://docs.convex.dev) | **npm:** convex v1.34.x | **License:** Source Available (Platform), MIT (Client)

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Quickstart** | `references/00-overview.md` | Getting started, installation, core concepts, project setup |
| **Functions: Queries & Mutations** | `references/01-functions-queries-mutations.md` | Reading/writing data, transactions, real-time subscriptions, caching |
| **Functions: Actions & HTTP** | `references/02-functions-actions-http.md` | External APIs, side effects, HTTP endpoints, webhooks, CORS |
| **Database & Schemas** | `references/03-database-schemas.md` | Schema definition, validators, data types, document IDs, TypeScript types |
| **Indexes & Query Performance** | `references/04-indexes-performance.md` | Index definition, compound indexes, query optimization, pagination |
| **Authentication** | `references/05-authentication.md` | Convex Auth, Clerk, Auth0, WorkOS, custom OIDC, authorization patterns |
| **File Storage** | `references/06-file-storage.md` | Upload, serve, delete files, metadata, HTTP action uploads |
| **Scheduling** | `references/07-scheduling.md` | Scheduled functions, cron jobs, cancellation, status tracking |
| **Search** | `references/08-search.md` | Full-text search, vector search, search indexes, RAG patterns |
| **React & Client Integration** | `references/09-react-client.md` | ConvexProvider, useQuery, useMutation, useAction, Next.js, optimistic updates |
| **AI & Agents** | `references/10-ai-agents.md` | LLM integration, AI agents, RAG, streaming, tool calling with Convex |
| **Best Practices & Patterns** | `references/11-best-practices.md` | Security, performance, code organization, common pitfalls, ESLint rules |
| **Testing & Deployment** | `references/12-testing-deployment.md` | Testing patterns, CI/CD, production deployment, environment variables |

## Installation

```bash
# Create a new Convex project
npm create convex@latest

# Or add to existing project
npm install convex

# Start development server
npx convex dev
```

## Quick Reference

- **Docs:** https://docs.convex.dev
- **GitHub:** https://github.com/get-convex/convex-backend
- **npm:** https://www.npmjs.com/package/convex
- **Stack (Patterns):** https://stack.convex.dev
- **Changelog:** https://ship.convex.dev
- **Discord:** https://convex.dev/community
