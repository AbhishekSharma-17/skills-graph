---
name: tanstack-query
description: "Powerful asynchronous state management and data fetching for React, Vue, Solid, Svelte, and Angular. MANDATORY TRIGGERS: tanstack query, react query, TanStack Query, useQuery, useMutation, useInfiniteQuery, server state. Also trigger when user wants to fetch and cache API data in React, implement optimistic updates, handle pagination or infinite scroll, prefetch data, manage server state with automatic background refetching, or set up SSR data hydration. When in doubt about whether to use this skill for data fetching or server state management tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["tanstack-query", "react-query", "data-fetching", "caching", "server-state", "mutations", "optimistic-updates", "infinite-scroll", "ssr", "suspense"]
---

# TanStack Query — Skill Router

> Powerful asynchronous state management, server-state utilities, and data fetching for the web.

**Source:** [tanstack.com/query](https://tanstack.com/query/latest) v5.95 | **Package:** `@tanstack/react-query` (npm) | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, what TanStack Query is, QueryClient setup |
| **Queries (useQuery)** | `references/01-queries.md` | Fetching data, useQuery hook, query keys, query functions, all options |
| **Mutations** | `references/02-mutations.md` | Creating/updating/deleting data, useMutation, side effects, mutateAsync |
| **Query Invalidation** | `references/03-query-invalidation.md` | Invalidating cache, refetching, matching queries, predicates |
| **Caching & Staleness** | `references/04-caching.md` | staleTime, gcTime, cache lifecycle, background refetching, fresh vs stale |
| **Pagination & Infinite Queries** | `references/05-pagination-infinite.md` | Paginated data, useInfiniteQuery, cursor-based, load more, infinite scroll |
| **Optimistic Updates** | `references/06-optimistic-updates.md` | Immediate UI feedback, cache rollback, onMutate patterns |
| **Prefetching** | `references/07-prefetching.md` | Prefetching data, router integration, deferred queries, warm cache |
| **SSR & Hydration** | `references/08-ssr-hydration.md` | Server-side rendering, dehydrate/hydrate, Next.js, streaming, RSC |
| **Suspense & Error Boundaries** | `references/09-suspense.md` | useSuspenseQuery, error boundaries, streaming SSR, Suspense integration |
| **Dependent & Parallel Queries** | `references/10-dependent-parallel.md` | Dependent queries, useQueries, parallel fetching, dynamic query counts |
| **TypeScript & queryOptions** | `references/11-typescript.md` | Type inference, queryOptions helper, type-safe patterns, generics |
| **DevTools & Testing** | `references/12-devtools-testing.md` | React Query DevTools, testing with QueryClientProvider, mocking |

## Installation

```bash
npm install @tanstack/react-query
pnpm add @tanstack/react-query
yarn add @tanstack/react-query
bun add @tanstack/react-query
```

## Quick Reference

- **Docs:** https://tanstack.com/query/latest
- **GitHub:** https://github.com/TanStack/query
- **npm:** https://www.npmjs.com/package/@tanstack/react-query
