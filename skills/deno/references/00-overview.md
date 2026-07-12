# Deno Overview

> Source: https://docs.deno.com | Version: 2.9.0

## What is Deno?

Deno is a modern JavaScript and TypeScript runtime built on V8, Rust, and Tokio. Created by Ryan Dahl (also the original creator of Node.js), Deno addresses design decisions in Node that became pain points over time — particularly around security, module resolution, and toolchain fragmentation.

Key design principles:
- **Secure by default** — no file, network, or environment access unless explicitly granted
- **TypeScript first** — runs `.ts` files natively with no build step
- **Web-standard APIs** — uses `fetch`, `Request`, `Response`, `URL`, Web Streams, etc.
- **Built-in toolchain** — linter, formatter, test runner, bundler, documentation generator
- **Single executable** — everything ships in one `deno` binary

## When to Use Deno

| Use Case | Why Deno |
|----------|----------|
| New TypeScript projects | Zero-config TS, no `tsconfig.json` required |
| Secure server applications | Permission model prevents supply-chain attacks |
| Edge/serverless functions | Fast cold starts, small binary via `deno compile` |
| CLI tools | `deno compile` produces single executables |
| Monorepos | Built-in workspace support with `deno.json` |
| Scripting and automation | No `package.json`, no `node_modules`, just run |

## When to Prefer Node.js

- Deep dependency on Node-specific native addons with no WASM alternative
- Large existing codebase with complex webpack/babel pipelines
- Libraries that require npm's exact `node_modules` layout (rare but exists)

## Installation

```bash
# macOS / Linux (recommended)
curl -fsSL https://deno.land/install.sh | sh

# Homebrew
brew install deno

# Windows (PowerShell)
irm https://deno.land/install.ps1 | iex

# Docker
docker run -it denoland/deno:2.9.0

# Upgrade to latest
deno upgrade
```

After installation, verify:

```bash
deno --version
# deno 2.9.0
# v8 13.x.x
# typescript 5.x.x
```

## Quick Start

```bash
# Initialize a project
deno init my-project
cd my-project

# Run a script
deno run main.ts

# Run with permissions
deno run --allow-net --allow-read server.ts

# Run a remote script
deno run https://examples.deno.land/hello-world.ts
```

The generated project structure:

```
my-project/
├── deno.json      # Configuration + import map + tasks
├── main.ts        # Entry point
└── main_test.ts   # Test file
```

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│                  Deno CLI                     │
│  (lint, fmt, test, bench, compile, deploy)   │
├─────────────────────────────────────────────┤
│              TypeScript Compiler              │
│  (type-strip for execution, full check opt) │
├─────────────────────────────────────────────┤
│              Module Resolution               │
│  (URL imports, npm:, jsr:, import maps)      │
├─────────────────────────────────────────────┤
│              Permission System               │
│  (--allow-read, --allow-net, --deny-*)       │
├─────────────────────────────────────────────┤
│                V8 Engine                      │
├─────────────────────────────────────────────┤
│          Rust Runtime (Tokio)                │
│  (async I/O, HTTP, file system, subprocess)  │
└─────────────────────────────────────────────┘
```

## Comparison with Other Runtimes

| Feature | Deno | Node.js | Bun |
|---------|------|---------|-----|
| TypeScript | Native (no config) | Requires tsc/tsx | Native (type-strip) |
| Security | Permission-based sandbox | No sandbox | No sandbox |
| Package manager | Built-in (deno add) | npm/yarn/pnpm | bun install |
| Test runner | Built-in (deno test) | External (jest/vitest) | Built-in |
| Linter | Built-in (deno lint) | External (eslint/biome) | N/A |
| Formatter | Built-in (deno fmt) | External (prettier/biome) | N/A |
| npm compat | Full (npm: specifier) | Native | Full |
| Module system | ES modules (+ CJS compat) | CJS + ESM | CJS + ESM |
| Standard library | @std on JSR (43 packages) | Minimal built-ins | Minimal |
| Cold start | ~15ms | ~30-50ms | ~5ms |

## Ecosystem

- **JSR** (jsr.io) — The JavaScript/TypeScript registry designed for Deno (also works in Node)
- **npm** — Full npm compatibility via `npm:` specifiers
- **Deno Deploy** — Serverless platform for Deno applications
- **Fresh** — Full-stack web framework with islands architecture
- **@std** — Official standard library with 43+ packages

## Common Patterns

### Hello World Server

```typescript
Deno.serve({ port: 8000 }, (_req) => {
  return new Response("Hello, World!");
});
```

### Read a File

```typescript
const content = await Deno.readTextFile("./data.json");
const data = JSON.parse(content);
```

### Run a Subprocess

```typescript
const command = new Deno.Command("git", {
  args: ["status"],
  stdout: "piped",
});
const { stdout } = await command.output();
console.log(new TextDecoder().decode(stdout));
```

### Fetch from Network

```typescript
const response = await fetch("https://api.example.com/data");
const json = await response.json();
```

## IDE Setup

### VS Code
Install the official "Deno" extension (`denoland.vscode-deno`), then enable it per workspace:

```json
// .vscode/settings.json
{
  "deno.enable": true,
  "deno.lint": true,
  "deno.unstable": []
}
```

### JetBrains (WebStorm/IntelliJ)
Install the Deno plugin from the marketplace. Enable Deno support in `Settings > Languages & Frameworks > Deno`.

## Key Concepts Summary

1. **No `node_modules` by default** — dependencies cached globally, or opt into local `node_modules`
2. **Explicit file extensions** — `import { foo } from "./bar.ts"` (not `"./bar"`)
3. **URL-based imports** — can import directly from URLs or registries
4. **Permission flags** — must grant access: `--allow-read`, `--allow-net`, etc.
5. **Web platform alignment** — uses standard browser APIs wherever possible
6. **Single config file** — `deno.json` replaces tsconfig + eslintrc + prettierrc + package.json
