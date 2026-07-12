---
name: deno
description: "Secure TypeScript/JavaScript runtime with built-in toolchain, npm compatibility, and Web API standards. MANDATORY TRIGGERS: deno, Deno, deno.json, deno.lock, Deno.serve, Deno Deploy, JSR, jsr:, Fresh framework. Also trigger when the user works with secure-by-default JS runtimes, needs built-in linting/formatting/testing without external tools, uses URL imports or import maps, or deploys to Deno Deploy. When in doubt about whether to use this skill for Deno runtime tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["deno", "typescript", "javascript", "runtime", "serverless", "jsr"]
---

# Deno

> v2.9.0 | Source: https://docs.deno.com | Runtime: https://deno.com

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Starting with Deno, comparing runtimes, installation |
| [01-modules-dependencies.md](references/01-modules-dependencies.md) | Importing packages, npm/jsr specifiers, import maps, dependency management |
| [02-permissions-security.md](references/02-permissions-security.md) | Configuring permissions, --allow-* flags, deny flags, runtime permission API |
| [03-typescript-support.md](references/03-typescript-support.md) | TypeScript config, deno check, JSX, compiler options, declaration files |
| [04-cli-toolchain.md](references/04-cli-toolchain.md) | CLI commands: run, task, compile, lint, fmt, bench, doc, install, publish |
| [05-http-server.md](references/05-http-server.md) | Deno.serve, routing, WebSocket, streaming, TLS, static files |
| [06-testing.md](references/06-testing.md) | Deno.test, assertions, steps, BDD, coverage, parameterized tests, snapshots |
| [07-configuration.md](references/07-configuration.md) | deno.json, tasks, workspaces, lock files, compiler options |
| [08-node-compatibility.md](references/08-node-compatibility.md) | Node.js compat, npm packages, CommonJS, node_modules, package.json |
| [09-standard-library.md](references/09-standard-library.md) | @std packages, key modules, testing utilities, file system helpers |
| [10-runtime-apis.md](references/10-runtime-apis.md) | Deno namespace: file I/O, subprocess, FFI, permissions API, WebAssembly |
| [11-deploy-production.md](references/11-deploy-production.md) | Deno Deploy, Docker, CI/CD, deno compile, edge functions |
| [12-web-development.md](references/12-web-development.md) | Fresh, Hono, frameworks, web APIs, static serving, JSX/React |

## Installation

```bash
# macOS / Linux
curl -fsSL https://deno.land/install.sh | sh

# Homebrew
brew install deno

# Windows (PowerShell)
irm https://deno.land/install.ps1 | iex

# Verify
deno --version
```

## Quick Reference

- Docs: https://docs.deno.com
- Standard Library: https://jsr.io/@std
- Deploy: https://deno.com/deploy
- Fresh Framework: https://fresh.deno.dev
