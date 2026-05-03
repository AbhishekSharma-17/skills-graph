---
name: vitest
description: "Next-generation testing framework powered by Vite — test API, matchers, mocking, snapshots, coverage, browser mode, type testing, CLI, and advanced patterns. MANDATORY TRIGGERS: vitest, Vitest, vitest.config, vi.mock, vi.fn, vi.spyOn, expect matchers, test coverage vitest, vitest browser mode. Also trigger when user wants to write unit tests with Vite, configure test coverage, mock modules in ESM, run browser-based component tests, benchmark code, test TypeScript types, or migrate from Jest. When in doubt about whether to use this skill for JavaScript/TypeScript testing tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["vitest", "testing", "vite", "unit-tests", "mocking", "coverage", "snapshots", "browser-testing", "typescript", "esm"]
---

# Vitest — Skill Router

> Next generation testing framework powered by Vite.

**Source:** [vitest.dev](https://vitest.dev) | **Package:** `vitest` v4.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, configuration, why Vitest |
| **Writing Tests** | `references/01-writing-tests.md` | test, describe, it, hooks, lifecycle, context, fixtures |
| **Assertions & Matchers** | `references/02-assertions.md` | expect, toBe, toEqual, asymmetric matchers, custom matchers |
| **Mocking** | `references/03-mocking.md` | vi.fn, vi.spyOn, vi.mock, module mocking, partial mocking |
| **Timers & Dates** | `references/04-timers-dates.md` | Fake timers, vi.useFakeTimers, vi.setSystemTime, date mocking |
| **Snapshots** | `references/05-snapshots.md` | toMatchSnapshot, inline, file snapshots, serializers |
| **Coverage** | `references/06-coverage.md` | v8, istanbul, thresholds, reporters, per-file config |
| **Browser Mode** | `references/07-browser-mode.md` | Component testing, Playwright provider, DOM assertions |
| **CLI & Reporters** | `references/08-cli-reporters.md` | vitest run, watch, bench, reporters, sharding, filtering |
| **Type Testing** | `references/09-type-testing.md` | expectTypeOf, assertType, typecheck config |
| **Environments** | `references/10-environments.md` | jsdom, happy-dom, edge-runtime, custom environments |
| **Advanced Patterns** | `references/11-advanced-patterns.md` | Projects, parallelism, in-source testing, debugging, migration |

## Installation

```bash
# Install
npm install -D vitest

# Run tests
npx vitest

# Run once (CI)
npx vitest run

# With coverage
npx vitest run --coverage
```

## Quick Reference

- **Docs:** https://vitest.dev
- **GitHub:** https://github.com/vitest-dev/vitest
- **npm:** https://www.npmjs.com/package/vitest
- **Config:** https://vitest.dev/config/
- **API:** https://vitest.dev/api/
