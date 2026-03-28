---
name: hono
description: "Ultrafast web framework built on Web Standards for Cloudflare Workers, Deno, Bun, Node.js, and edge runtimes. MANDATORY TRIGGERS: hono, hono.js, honojs, hono framework, edge web framework, cloudflare workers framework. Also trigger when user wants to build APIs for edge runtimes, create type-safe REST APIs with RPC client, use JSX for server-side rendering without React, deploy web apps to Cloudflare Workers or Deno Deploy, or build multi-runtime web applications. When in doubt about whether to use this skill for edge or lightweight web framework tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["hono", "web-framework", "edge", "cloudflare-workers", "typescript", "rest-api", "jsx", "middleware", "bun", "deno"]
---

# Hono — Skill Router

> Small, simple, and ultrafast web framework built on Web Standards — runs on any JavaScript runtime.

**Source:** [hono.dev](https://hono.dev) v4.12.0 | **Package:** `hono` | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, project scaffolding, what Hono is, quickstart |
| **Routing** | `references/01-routing.md` | Route definitions, path params, wildcards, groups, app.route(), chaining |
| **Context API** | `references/02-context-api.md` | c.json, c.text, c.html, c.header, c.set/get, c.req, c.env, c.redirect |
| **Middleware** | `references/03-middleware.md` | Built-in middleware, CORS, logger, etag, compress, custom middleware |
| **Authentication** | `references/04-authentication.md` | JWT, Bearer, Basic auth middleware, API key patterns |
| **Validation** | `references/05-validation.md` | Zod validator, request validation, form/JSON/query/header/param validation |
| **RPC & Type Safety** | `references/06-rpc-type-safety.md` | hc client, AppType export, end-to-end type safety, chained routes |
| **JSX & Rendering** | `references/07-jsx-rendering.md` | Server-side JSX, streaming, Suspense, jsxRenderer, client components |
| **Error Handling** | `references/08-error-handling.md` | HTTPException, app.onError, app.notFound, custom error responses |
| **Testing** | `references/09-testing.md` | app.request, testClient, Vitest setup, mocking env bindings |
| **Runtime Adapters** | `references/10-runtime-adapters.md` | Node.js, Cloudflare Workers, Bun, Deno, Vercel, AWS Lambda, static files |
| **Best Practices** | `references/11-best-practices.md` | Project structure, factory pattern, performance, security, deployment |

## Installation

```bash
# Create a new project
npm create hono@latest my-app

# Or install manually
npm install hono

# Zod validator (optional)
npm install @hono/zod-validator zod
```

## Quick Reference

- **Docs:** https://hono.dev
- **GitHub:** https://github.com/honojs/hono
- **npm:** https://www.npmjs.com/package/hono
- **Discord:** https://discord.gg/hono
