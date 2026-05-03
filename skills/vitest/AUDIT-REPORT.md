# Audit Report — vitest

**Date:** 2026-05-03
**Skill Version:** 1.0.0
**Source Version:** vitest 4.x (v4.1.5)

## Quality Scores

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| **Architecture** | 5 | Clean router pattern, 12 focused leaf nodes, no file exceeds 500 lines |
| **Content Quality** | 5 | Comprehensive API coverage, runnable code examples, practical patterns |
| **Completeness** | 5 | Covers all major Vitest features: test API, assertions, mocking, snapshots, coverage, browser mode, type testing, environments, CLI, and advanced patterns |
| **Maintainability** | 5 | VERSION.json tracks all references with source pages, check-updates.py validates integrity |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover vitest, vi.mock, vi.fn, vi.spyOn, expect matchers, coverage, browser mode; broad use cases described |

## Coverage Assessment

### Core Features Covered

- [x] Test API (test, describe, it, hooks, context, fixtures)
- [x] Assertions (50+ matchers, asymmetric, soft, polling, custom)
- [x] Mocking (functions, modules, classes, partial, auto-mocking)
- [x] Timer and date mocking
- [x] Snapshot testing (file, inline, custom file, ARIA, serializers)
- [x] Code coverage (v8, istanbul, thresholds, reporters)
- [x] Browser mode (Playwright, WebdriverIO, component testing)
- [x] CLI commands and reporters
- [x] Type testing (expectTypeOf, assertType)
- [x] Test environments (node, jsdom, happy-dom, edge-runtime, custom)
- [x] Advanced patterns (projects, parallelism, in-source, debugging)

### Not Covered (Intentional)

- Vitest internal plugin API (too niche)
- Every individual config option (config reference is available online)
- Third-party Vitest plugins ecosystem
- Vitest Node API for programmatic execution

## Recommendations

- Monitor Vitest 5.x for breaking changes
- Update browser mode section when new providers are added
- Track new matchers added in minor versions
