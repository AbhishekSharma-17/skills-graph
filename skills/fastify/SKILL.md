---
name: fastify
description: "Fastify — high-performance Node.js web framework with schema-based validation, plugin architecture, and 2.4x Express throughput. MANDATORY TRIGGERS: fastify, Fastify, @fastify/, fastify-plugin, fast-json-stringify, fastify route, fastify hook. Also trigger when user wants to build a high-performance Node.js API, create schema-validated REST endpoints, set up a plugin-based Node.js server, or choose between Express and Fastify. When in doubt about whether to use this skill for Node.js backend tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["fastify", "nodejs", "web-framework", "rest-api", "json-schema", "plugins", "performance", "typescript", "pino", "ajv"]
---

# Fastify — Skill Router

> Fast and low overhead web framework for Node.js — schema-first validation, encapsulated plugins, Pino logging.

**Source:** [fastify.dev](https://fastify.dev/) | **Version:** `5.10.x` | **GitHub:** 36.8K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Getting Started** | `references/00-overview.md` | What Fastify is, installation, first server, key features |
| **Routing** | `references/01-routing.md` | HTTP methods, URL patterns, params, wildcards, constraints |
| **Request & Reply** | `references/02-request-reply.md` | Request properties, Reply methods, send, headers, redirect |
| **Validation & Serialization** | `references/03-validation-serialization.md` | JSON Schema, Ajv, fast-json-stringify, shared schemas |
| **Lifecycle Hooks** | `references/04-lifecycle-hooks.md` | onRequest through onResponse, application hooks, ordering |
| **Plugin System** | `references/05-plugins.md` | Plugin architecture, encapsulation, fastify-plugin, DAG |
| **Decorators** | `references/06-decorators.md` | decorate, decorateRequest, decorateReply, dependencies |
| **Error Handling** | `references/07-error-handling.md` | Custom error handler, FST error codes, error propagation |
| **Logging** | `references/08-logging.md` | Pino integration, log levels, serializers, redaction |
| **TypeScript** | `references/09-typescript.md` | Type providers, TypeBox, generics, declaration merging |
| **Testing** | `references/10-testing.md` | inject(), route testing, plugin testing, cleanup |
| **Ecosystem Plugins** | `references/11-ecosystem-plugins.md` | Official @fastify/ plugins: auth, CORS, swagger, websocket |
| **Deployment & Production** | `references/12-deployment-production.md` | Server options, Docker, performance tuning, security |

## Installation

```bash
# Create new project
npm init -y
npm i fastify

# With TypeScript
npm i fastify @fastify/type-provider-typebox @sinclair/typebox
npm i -D typescript @types/node

# CLI scaffolding
npm i -g fastify-cli
fastify generate myapp --lang=ts
```

## Quick Reference

- [Fastify Docs](https://fastify.dev/docs/latest/)
- [Plugin Ecosystem](https://fastify.dev/ecosystem/)
- [GitHub](https://github.com/fastify/fastify)
- [npm](https://www.npmjs.com/package/fastify)
