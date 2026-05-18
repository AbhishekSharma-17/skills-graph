---
name: bun
description: "Bun all-in-one JavaScript runtime, bundler, test runner, and package manager built with Zig for extreme performance. MANDATORY TRIGGERS: Bun, bun runtime, bun install, bun test, bun build, Bun.serve, Bun.file, Bun.write, Bun.spawn, Bun.SQL, Bun.redis, bun:ffi, bun:test, bunx, bun.lock. Also trigger when building HTTP servers with Bun, migrating from Node.js to Bun, configuring the Bun bundler, writing tests with bun:test, using Bun's package manager, running shell commands with Bun.$, using built-in database clients, or developing fullstack apps with Bun's frontend dev server. When in doubt about whether to use this skill for Bun or JavaScript runtime tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["javascript", "runtime", "bundler", "test-runner", "package-manager", "typescript", "bun"]
---

# Bun

> All-in-one JavaScript runtime — v1.3.x | [Docs](https://bun.com/docs) | [GitHub](https://github.com/oven-sh/bun) | [Blog](https://bun.com/blog)

## Reference Files

| File | Read When |
|:-----|:----------|
| `references/00-overview.md` | Starting with Bun, installation, CLI commands, Node.js compatibility, quick start |
| `references/01-runtime-fundamentals.md` | Module resolution, TypeScript/JSX support, environment variables, globals, watch mode |
| `references/02-http-server.md` | Building HTTP servers with Bun.serve(), routing, request/response, TLS, static files |
| `references/03-websockets.md` | Server-side WebSockets, pub/sub topics, compression, scalable real-time messaging |
| `references/04-package-manager.md` | bun install, bun add/remove, workspaces, lockfile, registries, overrides |
| `references/05-bundler.md` | Bun.build(), entrypoints, targets, code splitting, plugins, minification, loaders |
| `references/06-test-runner.md` | bun:test API, describe/test/expect, mocks, snapshots, lifecycle hooks, watch mode |
| `references/07-file-io.md` | Bun.file(), Bun.write(), streaming, BunFile, Glob, FileSink |
| `references/08-shell-api.md` | Bun.$ shell, template literals, piping, environment variables, escaping |
| `references/09-database-clients.md` | Bun.SQL (Postgres/MySQL/SQLite), Bun.redis, tagged templates, connection pooling |
| `references/10-child-processes.md` | Bun.spawn(), Bun.spawnSync(), IPC, worker threads, structured cloning |
| `references/11-ffi.md` | bun:ffi, dlopen, C ABI interop, type mapping, callbacks, performance |
| `references/12-frontend-dev.md` | HTML imports, fullstack dev server, HMR, React Fast Refresh, zero-config frontend |

## Quick Start

```bash
# Install Bun
curl -fsSL https://bun.sh/install | bash

# Create a project
bun init

# Run a file
bun run index.ts

# Install dependencies (25x faster than npm)
bun install

# Run tests
bun test

# Bundle for production
bun build ./src/index.ts --outdir ./dist
```

## Quick Reference

- [API Reference](https://bun.com/reference) — Complete API documentation
- [Guides](https://bun.com/guides) — How-to guides for common tasks
- [Blog](https://bun.com/blog) — Release notes and announcements
