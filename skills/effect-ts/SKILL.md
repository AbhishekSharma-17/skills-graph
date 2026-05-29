---
name: effect-ts
description: "Effect — production-grade TypeScript framework for type-safe error handling, dependency injection, concurrency, streams, schema validation, and platform abstractions. MANDATORY TRIGGERS: effect-ts, Effect, Effect.gen, Effect.runPromise, @effect/platform, @effect/schema, @effect/vitest, Effect.Service, Layer, Context.Tag. Also trigger when user wants type-safe error handling in TypeScript, typed errors, functional effect system, structured concurrency with fibers, schema decode/encode, dependency injection with layers, or building robust TypeScript backends. When in doubt about whether to use this skill for Effect-related tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["effect-ts", "typescript", "error-handling", "dependency-injection", "concurrency", "schema", "functional-programming", "streams"]
---

# Effect — Skill Router

> Type-safe, composable, production-grade TypeScript framework for building robust applications.

**Source:** [effect.website/docs](https://effect.website/docs) | **Package:** `effect` v3.21.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, what Effect is, when to use it, core types |
| **The Effect Type** | `references/01-effect-type.md` | Creating effects, Effect.gen, running effects, pipe/flow, combinators |
| **Error Handling** | `references/02-error-handling.md` | Typed errors, tagged errors, catching, retrying, defects vs failures |
| **Context & Services** | `references/03-context-services.md` | Dependency injection, Context.Tag, Effect.Service, service patterns |
| **Layers** | `references/04-layers.md` | Layer composition, providing services, Layer.provide, merging layers |
| **Schema** | `references/05-schema.md` | Schema validation, decode/encode, branded types, Schema.Class, transforms |
| **Concurrency** | `references/06-concurrency.md` | Fibers, fork/join, structured concurrency, interruption, racing |
| **Concurrency Patterns** | `references/07-concurrency-patterns.md` | Semaphore, Queue, Deferred, PubSub, rate limiting, backpressure |
| **Streams** | `references/08-streams.md` | Stream creation, transformation, consumption, Sink, Channel |
| **Resource Management** | `references/09-resource-management.md` | Scope, acquireRelease, Scoped effects, finalizers, safe cleanup |
| **Configuration** | `references/10-configuration.md` | Config module, ConfigProvider, environment variables, secrets, nested config |
| **Testing** | `references/11-testing.md` | @effect/vitest, TestClock, TestContext, layer testing, property testing |
| **Platform** | `references/12-platform.md` | HTTP client/server, HttpApi, filesystem, @effect/platform abstractions |

## Installation

```bash
# Install core package
npm install effect

# Common companion packages
npm install @effect/platform @effect/platform-node
npm install @effect/schema    # included in effect since v3
npm install @effect/vitest    # testing integration
```

## Quick Reference

- **Docs:** https://effect.website/docs
- **GitHub:** https://github.com/Effect-TS/effect
- **npm:** https://www.npmjs.com/package/effect
- **API Reference:** https://effect-ts.github.io/effect/
- **Discord:** https://discord.gg/effect-ts
