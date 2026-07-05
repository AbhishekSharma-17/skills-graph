# Biome — Overview & Getting Started

> Source: [biomejs.dev](https://biomejs.dev/) | Version: 2.5.x

## Table of Contents
- [What Is Biome](#what-is-biome)
- [Key Features](#key-features)
- [Performance](#performance)
- [Supported Languages](#supported-languages)
- [Installation](#installation)
- [Project Initialization](#project-initialization)
- [First Run](#first-run)
- [When to Use Biome](#when-to-use-biome)
- [Architecture](#architecture)
- [Comparison with ESLint + Prettier](#comparison-with-eslint--prettier)
- [Adoption](#adoption)

---

## What Is Biome

Biome is a single, fast toolchain for web projects that replaces ESLint, Prettier, and import sorting tools. Written in Rust, it provides formatting, linting, and code analysis for JavaScript, TypeScript, JSX, TSX, JSON, CSS, GraphQL, and HTML — all from one binary with zero Node.js dependencies at runtime.

Biome was forked from Rome Tools in August 2023 and has since become the leading alternative to the traditional ESLint + Prettier stack.

## Key Features

- **Unified toolchain** — formatting, linting, import sorting, and code assists in one tool
- **Blazing fast** — 35x faster than Prettier, 50x faster than ESLint on typical projects
- **509+ lint rules** — ported from ESLint, typescript-eslint, and other sources
- **97% Prettier compatibility** — near-identical output with intentional improvements
- **Zero configuration** — sensible defaults that work out of the box
- **Type-aware rules** — without requiring the TypeScript compiler (uses its own inference)
- **First-class LSP** — editor integration via Language Server Protocol
- **GritQL plugins** — extensible custom rules via a pattern query language

## Performance

Benchmarks formatting 171,127 lines across 2,104 files:

| Tool | Time | Relative |
|------|------|----------|
| Biome | ~0.3s | 1x |
| Prettier | ~10.5s | ~35x slower |

Benchmarks linting 10,000 files:

| Tool | Time | Relative |
|------|------|----------|
| Biome | ~0.8s | 1x |
| ESLint | ~45s | ~56x slower |

The performance comes from Rust's zero-cost abstractions, parallel file processing, and an optimized parser that avoids the overhead of Node.js.

## Supported Languages

| Language | Parsing | Formatting | Linting |
|----------|---------|------------|---------|
| JavaScript (.js) | Stable | Stable | Stable |
| TypeScript (.ts) | Stable | Stable | Stable |
| JSX (.jsx) | Stable | Stable | Stable |
| TSX (.tsx) | Stable | Stable | Stable |
| JSON (.json) | Stable | Stable | Stable |
| JSONC (.jsonc) | Stable | Stable | Stable |
| CSS (.css) | Stable | Stable | Stable |
| GraphQL (.graphql) | Stable | Stable | Stable |
| HTML (.html) | Experimental | Experimental | Experimental |
| Vue (.vue) | Experimental | Experimental | — |
| Svelte (.svelte) | Experimental | Experimental | — |
| Astro (.astro) | Experimental | Experimental | — |

## Installation

```bash
# npm (always pin exact version — Biome follows semver strictly)
npm i -D --save-exact @biomejs/biome

# pnpm
pnpm add -D --save-exact @biomejs/biome

# yarn
yarn add -D --exact @biomejs/biome

# bun
bun add -D --exact @biomejs/biome

# Homebrew (standalone, no Node.js required)
brew install biome

# Standalone binary (CI or non-Node projects)
curl -L https://github.com/biomejs/biome/releases/latest/download/biome-linux-x64 -o biome
chmod +x biome
```

Pin the exact version to avoid unexpected formatting changes across team members.

## Project Initialization

```bash
# Create a biome.json with recommended defaults
npx @biomejs/biome init
```

This generates a minimal `biome.json`:

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.0/schema.json",
  "vcs": {
    "enabled": false,
    "clientKind": "git",
    "useIgnoreFile": false
  },
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
  }
}
```

## First Run

```bash
# Check everything (format + lint + imports) without modifying files
npx @biomejs/biome check ./src

# Check and auto-fix safe issues
npx @biomejs/biome check --write ./src

# Format only
npx @biomejs/biome format --write ./src

# Lint only
npx @biomejs/biome lint ./src

# CI mode (read-only, exits with error on issues)
npx @biomejs/biome ci ./src
```

## When to Use Biome

**Use Biome when:**
- Starting a new JavaScript/TypeScript project
- Your ESLint + Prettier setup is slow or painful to configure
- You want a single tool for formatting + linting + imports
- You need fast CI checks (sub-second for most projects)
- You value opinionated defaults over infinite configurability

**Consider alternatives when:**
- You rely heavily on ESLint plugins with no Biome equivalent
- Your project uses languages Biome doesn't support (Python, Ruby, etc.)
- You need YAML or TOML configuration formats (Biome uses JSON only)

## Architecture

Biome runs as a single binary with an optional daemon mode for IDE integration:

```
┌──────────────────────────────────────┐
│           Biome Binary (Rust)        │
│                                      │
│  ┌──────────┐  ┌──────────────────┐  │
│  │  Parser   │  │  Formatter       │  │
│  │ (per-lang)│  │  (IR-based)      │  │
│  └──────────┘  └──────────────────┘  │
│  ┌──────────┐  ┌──────────────────┐  │
│  │  Linter   │  │  Assist          │  │
│  │ (509+     │  │  (imports, code  │  │
│  │  rules)   │  │   actions)       │  │
│  └──────────┘  └──────────────────┘  │
│  ┌──────────────────────────────────┐│
│  │  LSP Server (daemon mode)        ││
│  └──────────────────────────────────┘│
└──────────────────────────────────────┘
```

- **Parser** — custom Rust parsers for each language, error-resilient (can format broken code)
- **Formatter** — intermediate representation (IR) based, like Prettier's algorithm
- **Linter** — rule engine with safe/unsafe fix classification
- **Assist** — code actions (import sorting, code transformations)
- **LSP Server** — `biome start` launches a daemon for editor integration

## Comparison with ESLint + Prettier

| Aspect | Biome | ESLint + Prettier |
|--------|-------|-------------------|
| Speed | 35-56x faster | Baseline |
| Config files | 1 (biome.json) | 2-4 (.eslintrc, .prettierrc, etc.) |
| Dependencies | 1 package | 10-30+ packages |
| Install size | ~30 MB | 100-300+ MB |
| Format + lint conflicts | Impossible (unified) | Common pain point |
| Type-aware rules | Built-in inference | Requires tsconfig + typescript-eslint |
| Lint rules | 509+ | 300+ core (thousands with plugins) |
| Plugin ecosystem | GritQL (growing) | Massive (mature) |
| CSS/GraphQL/HTML | Supported | Requires separate tools |

## Adoption

Biome is trusted by major organizations including:
- Astro, AWS, Cloudflare, Discord, Google, Microsoft, Node.js, Vercel

Monthly npm downloads surpassed 15 million in 2025, with adoption accelerating in 2026 as type-aware rules and HTML support mature.
