---
name: trpc
description: "End-to-end typesafe APIs for TypeScript with automatic type inference, no code generation. MANDATORY TRIGGERS: trpc, tRPC, typesafe api, typesafe rpc, end-to-end type safety, @trpc/server, @trpc/client, @trpc/react-query, @trpc/tanstack-react-query, t3 stack trpc. Also trigger when user wants to build type-safe APIs without code generation, create full-stack TypeScript apps with shared types, integrate React Query with type-safe backends, or add real-time subscriptions via SSE. When in doubt about whether to use this skill for TypeScript API or RPC tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["trpc", "typescript", "typesafe-api", "react-query", "nextjs", "rpc", "sse", "streaming", "zod", "tanstack"]
---

# tRPC — Skill Router

> Move fast and break nothing. End-to-end typesafe APIs made easy — no schemas, no code generation.

**Source:** [trpc.io](https://trpc.io) v11.16.0 | **Package:** `@trpc/server` | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, what tRPC is, quickstart, packages |
| **Routers & Procedures** | `references/01-routers-procedures.md` | Defining queries, mutations, subscriptions, merging routers |
| **Input & Output Validation** | `references/02-input-output-validation.md` | Zod schemas, input validation, output validators, custom validators |
| **Context & Middleware** | `references/03-context-middleware.md` | Request context, auth middleware, logging, chaining, context extension |
| **Error Handling** | `references/04-error-handling.md` | TRPCError, error codes, error formatting, error shapes |
| **Client & Links** | `references/05-client-links.md` | Vanilla client, httpBatchLink, splitLink, loggerLink, custom links |
| **React Query Integration** | `references/06-react-query.md` | @trpc/tanstack-react-query, useQuery, useMutation, prefetching |
| **Next.js Integration** | `references/07-nextjs-integration.md` | App Router setup, Pages Router, RSC, server-side calls, API routes |
| **Subscriptions & Streaming** | `references/08-subscriptions-streaming.md` | SSE, httpSubscriptionLink, httpBatchStreamLink, generators |
| **Server Adapters** | `references/09-server-adapters.md` | Express, Fastify, standalone, fetch/edge, AWS Lambda, Cloudflare |
| **Testing** | `references/10-testing.md` | createCallerFactory, integration tests, frontend testing, mocking |
| **Advanced Patterns** | `references/11-advanced-patterns.md` | Inference helpers, merging routers, factory patterns, authorization |

## Installation

```bash
# Core packages
npm install @trpc/server @trpc/client zod

# React Query integration
npm install @trpc/tanstack-react-query @tanstack/react-query

# Next.js integration
npm install @trpc/next
```

## Quick Reference

- **Docs:** https://trpc.io/docs
- **GitHub:** https://github.com/trpc/trpc
- **npm:** https://www.npmjs.com/package/@trpc/server
- **Discord:** https://trpc.io/discord
