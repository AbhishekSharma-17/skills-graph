# Fastify Skill — Audit Report

**Audit Date:** 2026-07-30
**Skill Version:** 1.0.0
**Source Version:** Fastify 5.10.x

## Quality Assessment

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| **Architecture** | 5 | Clean router + 13 leaf nodes. One reference per major concept. No file exceeds 500 lines. |
| **Content Quality** | 5 | All content sourced from official Fastify docs. Code examples are runnable. Covers v5 API exclusively with migration notes. |
| **Completeness** | 5 | Covers the full Fastify surface: routing, validation, hooks, plugins, decorators, errors, logging, TypeScript, testing, ecosystem, and deployment. |
| **Maintainability** | 5 | VERSION.json tracks all 13 references with source URLs. check-updates.py validates against npm registry. Staleness threshold: 90 days. |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS include `fastify`, `Fastify`, `@fastify/`, `fastify-plugin`, `fast-json-stringify`. Description covers performance-focused Node.js API use cases. |

## Coverage Map

| Topic | Reference File | Depth |
|-------|---------------|-------|
| Framework overview | 00-overview.md | Installation, architecture, lifecycle, comparison |
| HTTP routing | 01-routing.md | Methods, params, wildcards, constraints, prefixing |
| Request/Reply | 02-request-reply.md | Properties, send, headers, serialization, hijack |
| Validation | 03-validation-serialization.md | JSON Schema, Ajv, fast-json-stringify, shared schemas |
| Lifecycle | 04-lifecycle-hooks.md | 10 request hooks, 6 application hooks, diagnostics |
| Plugins | 05-plugins.md | Encapsulation, DAG, fastify-plugin, autoload |
| Decorators | 06-decorators.md | Instance, request, reply decorators, scope rules |
| Errors | 07-error-handling.md | Error handler, 70+ FST codes, not-found handler |
| Logging | 08-logging.md | Pino, levels, serializers, redaction, request ID |
| TypeScript | 09-typescript.md | Type providers, generics, declaration merging |
| Testing | 10-testing.md | inject(), Vitest, Node test runner, plugin testing |
| Ecosystem | 11-ecosystem-plugins.md | 30+ official plugins with usage examples |
| Production | 12-deployment-production.md | Docker, security, performance, v5 migration |

## Known Gaps

- Advanced HTTP/2 server push patterns not covered (rarely used in practice)
- Custom constraint implementations (async constraints) covered briefly but could be deeper
- Community plugin ecosystem only partially listed (focused on official plugins)
