# Audit Report — tanstack-query

**Date:** 2026-03-31
**Skill Version:** 1.0.0
**Source Version:** 5.95.0

## Quality Assessment

| Category | Score (1-5) | Notes |
|----------|-------------|-------|
| **Architecture** | 5 | Clean router + 13 leaf files, all under 500 lines, logical topic separation from basics to advanced |
| **Content Quality** | 5 | Comprehensive coverage with runnable TypeScript examples, tables for options/return values, patterns and anti-patterns |
| **Completeness** | 4 | Covers all core React patterns. Missing: Vue/Solid/Svelte/Angular adapters, offline mode, broadcast channel, persistence deep dive |
| **Maintainability** | 5 | VERSION.json tracks all references with source pages, check-updates.py validates integrity, 90-day staleness threshold |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover primary keywords (tanstack query, react query, useQuery, useMutation). Description covers data fetching, caching, SSR, pagination |

## Overall Score: 4.8 / 5

## Coverage Map

| TanStack Query Feature | Reference File | Coverage |
|-----------------------|----------------|----------|
| Overview & setup | 00-overview.md | Full |
| Queries (useQuery) | 01-queries.md | Full |
| Mutations (useMutation) | 02-mutations.md | Full |
| Query invalidation | 03-query-invalidation.md | Full |
| Caching & staleness | 04-caching.md | Full |
| Pagination & infinite queries | 05-pagination-infinite.md | Full |
| Optimistic updates | 06-optimistic-updates.md | Full |
| Prefetching | 07-prefetching.md | Full |
| SSR & hydration | 08-ssr-hydration.md | Full |
| Suspense & error boundaries | 09-suspense.md | Full |
| Dependent & parallel queries | 10-dependent-parallel.md | Full |
| TypeScript & queryOptions | 11-typescript.md | Full |
| DevTools & testing | 12-devtools-testing.md | Full |

## Recommendations for v1.1.0

1. Add reference for Vue Query adapter patterns
2. Add reference for offline mode and network mode deep dive
3. Add reference for query persistence with IndexedDB/localStorage
4. Add reference for TanStack Query + TanStack Router integration
5. Expand SSR reference with Remix and SvelteKit patterns
