# Effect-TS Skill — Audit Report

**Audit Date:** 2026-05-30
**Skill Version:** 1.0.0
**Source Tracked:** `effect` v3.21.x

## Architecture Scorecard

| Category | Score | Notes |
|----------|:-----:|-------|
| SKILL.md size | 5/5 | 54 lines — well under 100-line limit |
| Progressive disclosure | 5/5 | 3-level loading: metadata → router → specific reference |
| Reference splitting | 5/5 | All files 200-500 lines, no file exceeds limit |
| YAML frontmatter | 5/5 | Proper name, description, metadata, tags |
| TOC on large files | 5/5 | All files >300 lines include table of contents |
| Description triggering | 5/5 | MANDATORY TRIGGERS with 10+ keywords, broad coverage |
| Tooling & maintenance | 5/5 | VERSION.json, CHANGELOG.md, check-updates.py |
| Code examples | 4/5 | Comprehensive examples covering core patterns |
| Cross-references | 5/5 | Every reference links to related topics |
| Content accuracy | 4/5 | Based on official docs and community best practices |

**Overall: 48/50 (96%)**

## Coverage Assessment

| Domain | Coverage | Key Topics |
|--------|----------|------------|
| Core Effect type | Complete | Effect<A,E,R>, gen, pipe, running, combinators |
| Error handling | Complete | Tagged errors, catchTag, retry, defects, Cause |
| Dependency injection | Complete | Services, Context, Tag, accessor patterns |
| Layers | Complete | Composition, scoped, memoization, wiring |
| Schema | Complete | Decode/encode, branded, Class, transforms |
| Concurrency | Complete | Fibers, fork/join, parallel, interruption |
| Concurrency patterns | Complete | Ref, Deferred, Queue, Semaphore, PubSub |
| Streams | Complete | Creation, transforms, Sink, Channel |
| Resource management | Complete | Scope, acquireRelease, finalizers |
| Configuration | Complete | Config, providers, nested, secrets |
| Testing | Complete | @effect/vitest, TestClock, mocking |
| Platform | Complete | HTTP client/server, HttpApi, filesystem |

## Improvement Opportunities

1. **Add @effect/sql reference** — Database access with Effect SQL could be a separate reference file
2. **Add @effect/cli reference** — CLI application building patterns
3. **Add migration guide** — From fp-ts, Zod, or plain TypeScript to Effect
4. **Expand real-world examples** — Full application architectures beyond individual patterns

## Platform Compatibility

| Platform | Status |
|----------|--------|
| Claude Code | Full |
| Gemini CLI | Full |
| Cursor | Full |
| Windsurf | Full |
| Codex | Full |
| Trae | Full |
| Antigravity | Full |
