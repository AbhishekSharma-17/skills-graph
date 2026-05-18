# Bun -- Overview & Getting Started

> Source: [bun.sh/docs](https://bun.sh/docs) | All-in-one JavaScript runtime

## Table of Contents

- [What is Bun?](#what-is-bun)
- [Installation](#installation)
- [CLI Commands Reference](#cli-commands-reference)
- [Node.js Compatibility](#nodejs-compatibility)
- [Performance Characteristics](#performance-characteristics)
- [Version History Highlights](#version-history-highlights)
- [When to Use Bun vs Node.js vs Deno](#when-to-use-bun-vs-nodejs-vs-deno)
- [Configuration with bunfig.toml](#configuration-with-bunfigtoml)
- [Common Pitfalls](#common-pitfalls)

---

## What is Bun?

Bun is an all-in-one JavaScript runtime, bundler, transpiler, package manager, and test runner built from scratch using the Zig programming language. It uses Apple's JavaScriptCore engine (the same engine powering Safari) instead of V8, which gives it distinct performance characteristics including significantly faster startup times.

Bun replaces multiple tools in a typical JavaScript project:

| Traditional Toolchain | Bun Equivalent |
|----------------------|----------------|
| Node.js (runtime) | `bun run` |
| npm / yarn / pnpm (package manager) | `bun install` |
| esbuild / webpack (bundler) | `bun build` |
| ts-node / tsx (TypeScript runner) | Native TypeScript support |
| jest / vitest (test runner) | `bun test` |
| npx (package executor) | `bunx` |
| dotenv (env loading) | Built-in `.env` loading |

Bun aims for full compatibility with the Node.js ecosystem while delivering substantial performance improvements across every operation.

## Installation

### macOS and Linux (recommended)

```bash
# Install via curl (official installer)
curl -fsSL https://bun.sh/install | bash

# Install a specific version
curl -fsSL https://bun.sh/install | bash -s "bun-v1.3.0"
```

### Homebrew (macOS)

```bash
brew install oven-sh/bun/bun
```

### npm (any platform with Node.js)

```bash
npm install -g bun
```

### Docker

```dockerfile
# Official Docker image
FROM oven/bun:1.3

WORKDIR /app
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile
COPY . .

EXPOSE 3000
CMD ["bun", "run", "start"]
```

### Windows

```powershell
# Via scoop
scoop install bun

# Via PowerShell installer
irm bun.sh/install.ps1 | iex
```

### Verify installation

```bash
bun --version
# 1.3.x
```

### Upgrade Bun

```bash
bun upgrade

# Upgrade to a specific version
bun upgrade --stable
bun upgrade --canary
```

## CLI Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `bun run <file>` | Execute a JS/TS/JSX file | `bun run index.ts` |
| `bun run <script>` | Run a package.json script | `bun run dev` |
| `bun install` | Install all dependencies | `bun install` |
| `bun add <pkg>` | Add a dependency | `bun add hono` |
| `bun add -d <pkg>` | Add a dev dependency | `bun add -d vitest` |
| `bun remove <pkg>` | Remove a dependency | `bun remove express` |
| `bun test` | Run test files | `bun test` |
| `bun build <entry>` | Bundle for production | `bun build ./src/index.ts --outdir ./dist` |
| `bunx <pkg>` | Execute a package binary | `bunx prisma migrate dev` |
| `bun init` | Initialize a new project | `bun init` |
| `bun create <template>` | Scaffold from a template | `bun create hono my-app` |
| `bun upgrade` | Upgrade Bun itself | `bun upgrade` |
| `bun pm ls` | List installed packages | `bun pm ls` |
| `bun pm cache` | Manage package cache | `bun pm cache rm` |

### Running files directly

```bash
# Bun natively executes TypeScript, JSX, and TSX
bun run server.ts
bun run app.tsx
bun run script.jsx

# The 'run' keyword is optional for files
bun server.ts
```

### Package management

```bash
# Install with frozen lockfile (CI)
bun install --frozen-lockfile

# Install production dependencies only
bun install --production

# Generate a yarn-compatible lockfile
bun install --yarn

# Global install
bun add -g typescript
```

## Node.js Compatibility

Bun targets 95%+ compatibility with Node.js APIs. Most npm packages work without modification.

### Supported Node.js APIs

| Module | Status | Notes |
|--------|--------|-------|
| `node:fs` | Full | Sync and async |
| `node:path` | Full | All methods |
| `node:http` / `node:https` | Full | Server and client |
| `node:crypto` | Full | Including subtle crypto |
| `node:stream` | Full | Readable, Writable, Transform |
| `node:buffer` | Full | Buffer class globally available |
| `node:events` | Full | EventEmitter |
| `node:child_process` | Full | spawn, exec, fork |
| `node:worker_threads` | Full | Worker threads |
| `node:net` | Full | TCP sockets |
| `node:os` | Full | System information |
| `node:url` | Full | URL parsing |
| `node:util` | Full | Utilities |
| `node:assert` | Full | Assertions |
| `node:dns` | Partial | Most methods supported |
| `node:cluster` | Partial | Basic clustering |

### Global compatibility

```javascript
// These Node.js globals work in Bun
console.log(process.env.NODE_ENV);  // process object
console.log(Buffer.from("hello"));  // Buffer class
console.log(__dirname);             // Current directory
console.log(__filename);            // Current file path
console.log(require("fs"));        // CommonJS require
```

## Performance Characteristics

Bun achieves significant performance improvements over Node.js in several areas:

| Operation | Bun | Node.js | Speedup |
|-----------|-----|---------|---------|
| Startup time | ~6ms | ~25ms | ~4x faster |
| Package install (clean) | ~0.5s | ~12s | ~25x faster |
| TypeScript transpilation | Built-in | Requires ts-node/tsx | No build step |
| HTTP server (req/sec) | ~105,000 | ~48,000 | ~2x faster |
| SQLite queries/sec | ~120,000 | ~40,000 (better-sqlite3) | ~3x faster |
| File I/O (read) | Native optimized | Native | ~1.5x faster |
| `bun test` vs `jest` | ~8x faster | Baseline | 8x faster |

Key reasons for the performance advantage:

1. **JavaScriptCore engine** -- Faster startup and lower memory usage than V8 for many workloads
2. **Zig implementation** -- Systems-level language with manual memory management and zero overhead
3. **Integrated toolchain** -- No inter-process communication overhead between tools
4. **Native built-ins** -- SQLite, hashing, and file I/O implemented in native code
5. **Optimized package manager** -- Hardlink-based node_modules, parallel resolution

## Version History Highlights

| Version | Date | Key Features |
|---------|------|--------------|
| **1.0** | March 2025 | Stable release, Node.js compat milestone, production-ready APIs |
| **1.1** | July 2025 | Improved Windows support, `Bun.serve()` static routes, `bun build` CSS support |
| **1.2** | November 2025 | `Bun.SQL` for PostgreSQL, improved `node:cluster`, cross-compilation |
| **1.3** | February 2026 | `Bun.Redis`, `Bun.MySQL`, frontend dev server, improved HMR |

### Notable additions across versions

- **Bun.SQL** (1.2) -- Built-in PostgreSQL client with tagged template literals
- **Bun.Redis** (1.3) -- Native Redis client, no external packages needed
- **Bun.MySQL** (1.3) -- Native MySQL client
- **Frontend dev server** (1.3) -- Built-in development server with HMR for React and frameworks
- **Static routes** (1.1) -- Pre-allocated responses in `Bun.serve()` for maximum throughput
- **CSS bundling** (1.1) -- CSS processing in `bun build` pipeline

## When to Use Bun vs Node.js vs Deno

| Factor | Bun | Node.js | Deno |
|--------|-----|---------|------|
| **Best for** | Performance-critical, rapid dev | Maximum ecosystem, enterprise | Security-first, web standards |
| **Startup speed** | Fastest | Moderate | Fast |
| **TypeScript** | Built-in | Via flag/tooling | Built-in |
| **Package manager** | Built-in (npm compat) | npm/yarn/pnpm | npm compat + URL imports |
| **Test runner** | Built-in | Via packages | Built-in |
| **npm compatibility** | 95%+ | 100% | 90%+ |
| **Production maturity** | Growing | Battle-tested | Growing |
| **Edge/serverless** | Good | Good | Good |
| **Windows support** | Good (1.1+) | Excellent | Good |

### Decision guide

Choose **Bun** when:
- Startup performance is critical (serverless, CLI tools, scripts)
- You want a single tool replacing Node + npm + bundler + test runner
- You need native SQLite, PostgreSQL, or Redis without external packages
- You are building a new project without legacy Node.js constraints

Choose **Node.js** when:
- Maximum npm ecosystem compatibility is required
- You depend on native addons (N-API) that have not been tested with Bun
- Enterprise environment requires battle-tested, long-term-support runtime
- Existing large codebase is built on Node.js

Choose **Deno** when:
- Security sandboxing is a hard requirement (permissions model)
- You prefer web-standard APIs exclusively (fetch, Web Streams, etc.)
- You want built-in code formatting and linting in the runtime

## Configuration with bunfig.toml

Bun reads configuration from `bunfig.toml` at the project root or `~/.bunfig.toml` globally.

```toml
# bunfig.toml

# Package management
[install]
# Use a private registry
registry = "https://npm.pkg.github.com"

# Scoped registry
[install.scopes]
"@mycompany" = "https://npm.mycompany.com"

# Cache configuration
[install.cache]
dir = "~/.bun/install/cache"
disable = false

# Test runner configuration
[test]
# Coverage reporting
coverage = true
coverageDir = "./coverage"
coverageReporter = ["text", "lcov"]

# Test timeout in milliseconds
timeout = 5000

# Preload scripts before tests
preload = ["./tests/setup.ts"]

# Bundler configuration
[build]
# Default target
target = "bun"

# Sourcemap generation
sourcemap = "external"

# Minification
minify = true

# Runtime configuration
smol = false  # Use less memory at the cost of speed
logLevel = "info"
```

### Environment-specific configuration

```toml
# Development overrides
[run.env]
NODE_ENV = "development"

# Preload scripts for all bun run commands
preload = ["./src/instrument.ts"]
```

## Common Pitfalls

### 1. Assuming full Node.js native addon compatibility

Not all native addons (N-API / node-gyp) work with Bun. Test any package that relies on compiled C/C++ extensions before committing to Bun in production.

```bash
# Check if a package works
bun add bcrypt
bun -e "const bcrypt = require('bcrypt'); console.log(bcrypt.hashSync('test', 10))"
```

### 2. Mixing lockfile formats

Bun uses `bun.lockb` (binary lockfile). Do not commit both `bun.lockb` and `package-lock.json` to the same project. Pick one runtime and stick with it.

```bash
# Remove conflicting lockfiles
rm package-lock.json yarn.lock pnpm-lock.yaml
bun install  # Generates bun.lockb
```

### 3. Relying on Node.js-specific flags

Some Node.js CLI flags do not exist in Bun. For example, `--max-old-space-size` is a V8 flag that has no effect on JavaScriptCore.

```bash
# Node.js (V8-specific)
node --max-old-space-size=4096 server.js

# Bun (use Bun-specific memory controls)
bun run server.ts
# Memory is managed differently by JavaScriptCore
```

### 4. Assuming bun.lockb is human-readable

The `bun.lockb` file is a binary format for speed. To inspect it:

```bash
# Print lockfile as YAML for inspection
bun bun.lockb
```

### 5. Forgetting bun install uses hardlinks

Bun's package manager uses hardlinks to a global cache. This saves disk space but means modifying files inside `node_modules` directly will affect all projects sharing that cached version.

### 6. Not handling the bun-specific test runner API

`bun test` uses a jest-compatible API but has Bun-specific extensions. Test files written for `bun test` may not run under jest or vitest without modification.

```typescript
// Bun-specific test features
import { expect, test, mock } from "bun:test";

test("bun-specific mock", () => {
  const fn = mock(() => 42);
  expect(fn()).toBe(42);
  expect(fn).toHaveBeenCalled();
});
```

### 7. Port conflicts with the built-in dev server

Bun's frontend dev server (1.3+) defaults to common ports. Always specify the port explicitly to avoid conflicts with other services.

```typescript
Bun.serve({
  port: parseInt(process.env.PORT || "3000"),
  fetch(req) {
    return new Response("ok");
  },
});
```
