---
name: elysiajs
description: "ElysiaJS — ergonomic Bun-first TypeScript web framework with end-to-end type safety, 500K+ req/s performance, and Eden RPC client. MANDATORY TRIGGERS: elysia, elysiajs, ElysiaJS, Elysia.js, @elysiajs/eden, eden treaty, bun elysia, elysia plugin, elysia ws. Also trigger when user wants to build a Bun web server, create a type-safe API with Bun, set up end-to-end type-safe RPC without code generation, build high-performance TypeScript HTTP servers, or integrate Bun APIs with Next.js. When in doubt about whether to use this skill for Bun backend or type-safe API tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["elysiajs", "elysia", "bun", "typescript", "web-framework", "type-safety", "eden", "rpc", "rest-api", "websocket"]
---

# ElysiaJS — Skill Router

> Ergonomic Bun-first TypeScript framework — end-to-end type safety, 500K+ req/s, Eden RPC client.

**Source:** [elysiajs.com](https://elysiajs.com/) | **Version:** `1.4.x` | **GitHub:** 18.6K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Getting Started** | `references/00-overview.md` | What ElysiaJS is, installation, first server, key features |
| **Routing** | `references/01-routing.md` | HTTP methods, path parameters, wildcards, groups, guards |
| **Handler & Context** | `references/02-handler-context.md` | Context properties, response types, streaming, SSE, files |
| **Validation** | `references/03-validation.md` | Elysia.t schemas, TypeBox, Standard Schema, models, guards |
| **Lifecycle Hooks** | `references/04-lifecycle-hooks.md` | onRequest, parse, transform, beforeHandle, afterHandle, onError |
| **Plugin System** | `references/05-plugin-system.md` | Creating plugins, scoping, deduplication, lazy loading |
| **State & Derive** | `references/06-state-derive.md` | state(), decorate(), derive(), resolve(), store |
| **Eden Client** | `references/07-eden-client.md` | Eden Treaty, Eden Fetch, end-to-end type safety, setup |
| **Error Handling** | `references/08-error-handling.md` | Error codes, custom errors, onError hook, validation errors |
| **WebSocket** | `references/09-websocket.md` | WebSocket routes, events, validation, config, rooms |
| **OpenAPI Documentation** | `references/10-openapi.md` | Swagger/Scalar UI, tags, models, security schemes |
| **Macros & Trace** | `references/11-macros-trace.md` | Macros for cross-cutting concerns, trace for performance |
| **Integration & Deployment** | `references/12-integration-deployment.md` | Next.js, WinterTC, mount(), multi-runtime, testing |

## Installation

```bash
# Create new project
bun create elysia app
cd app
bun dev

# Add to existing Bun project
bun add elysia

# Eden client (frontend)
bun add @elysia/eden

# OpenAPI plugin
bun add @elysia/openapi
```

## Quick Reference

- [ElysiaJS Docs](https://elysiajs.com/)
- [Eden Treaty](https://elysiajs.com/eden/overview)
- [Plugin Ecosystem](https://elysiajs.com/plugins/overview)
- [GitHub](https://github.com/elysiajs/elysia)
