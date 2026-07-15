# htmx Skill — Audit Report

**Audit Date:** 2026-07-16
**Skill Version:** 1.0.0
**Source Version:** htmx 2.0.10

## Quality Scores

| Dimension | Score (1-5) | Notes |
|-----------|:-----------:|-------|
| **Architecture** | 5 | Clean router → leaf structure, 13 focused reference files, all under 500 lines |
| **Content Quality** | 5 | Practical code examples in HTML/Python/JS, covers real-world patterns across backends |
| **Completeness** | 5 | All core features covered: attributes, triggers, swapping, OOB, history, SSE/WS, security |
| **Maintainability** | 5 | VERSION.json tracks source, check-updates.py validates integrity, clear staleness thresholds |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover hx-* attributes, hypermedia, HATEOAS, and backend integration use cases |

## Coverage Analysis

### Covered Topics
- All hx-* attributes with usage examples
- Trigger syntax including modifiers, filters, and polling
- All swap strategies with modifiers (scroll, transition, settle)
- Out-of-band swap patterns
- Boosting and browser history integration
- Form handling, file uploads, and validation
- Complete events system and JavaScript API
- CSS transitions and View Transitions API
- All 7 core extensions (SSE, WS, idiomorph, preload, response-targets, head-support, htmx-1-compat)
- Configuration options and security hardening
- Server integration for Django, FastAPI, Flask, Express, Go
- Template fragment pattern
- Testing htmx endpoints

### Not Covered (Out of Scope for v1)
- Every community extension in detail
- htmx 4.0 alpha features (Fetch API replacement)
- Hyperscript integration (separate tool)
- Specific CSS framework integrations (Bootstrap, Tailwind with htmx)
- htmx 1.x migration guide (covered by htmx-1-compat extension reference)

## Recommendations for Future Updates
1. Add reference for htmx 4.0 when released (Fetch API, breaking changes)
2. Cover new extensions as they mature
3. Add Hyperscript integration reference if demand warrants
4. Consider a patterns/recipes reference for common UI interactions
