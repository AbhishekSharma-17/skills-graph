---
name: biome
description: "Biome — ultra-fast Rust-powered linter, formatter, and code analyzer for JavaScript, TypeScript, JSX, CSS, JSON, GraphQL, and HTML. MANDATORY TRIGGERS: biome, Biome, biomejs, biome.json, biome.jsonc, @biomejs/biome, biome check, biome lint, biome format, biome ci, biome migrate. Also trigger when user wants to replace ESLint or Prettier, set up a unified linter and formatter, configure code quality tooling for JS/TS projects, migrate from ESLint or Prettier, set up type-aware linting, organize imports, or configure CI code checks. When in doubt about whether to use this skill for linting, formatting, or code quality tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["biome", "linter", "formatter", "eslint", "prettier", "rust", "typescript", "javascript", "code-quality", "static-analysis"]
---

# Biome — Skill Router

> Ultra-fast Rust-powered toolchain for web projects — formatting, linting, and code analysis in a fraction of a second.

**Source:** [biomejs.dev](https://biomejs.dev/) | **Version:** `2.5.x` | **GitHub:** 16K+ stars | **npm:** 15M+ monthly downloads

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Getting Started** | `references/00-overview.md` | What Biome is, installation, first run, project setup |
| **Configuration** | `references/01-configuration.md` | biome.json structure, extends, overrides, file patterns |
| **Formatter** | `references/02-formatter.md` | Formatting options, language-specific settings, Prettier differences |
| **Linter Basics** | `references/03-linter-basics.md` | Rule groups, severity levels, enabling/disabling rules, presets |
| **Lint Rule Categories** | `references/04-lint-rule-categories.md` | a11y, complexity, correctness, performance, security, style, suspicious |
| **Type-Aware Rules** | `references/05-type-aware-rules.md` | Project domain, scanner, noFloatingPromises, inference engine |
| **Domains** | `references/06-domains.md` | React, Solid, Next.js, test — auto-detection, domain-specific rules |
| **Assist & Import Sorting** | `references/07-assist-imports.md` | organizeImports, import groups, sorting order, suppression |
| **CLI Reference** | `references/08-cli-reference.md` | check, lint, format, ci, init, migrate, search, rage commands |
| **Editor Integration** | `references/09-editor-integration.md` | VS Code, IntelliJ, Zed, Neovim, format-on-save, code actions |
| **Migration Guide** | `references/10-migration-guide.md` | Migrating from ESLint and Prettier, command mapping, config conversion |
| **VCS & CI/CD Integration** | `references/11-vcs-ci-integration.md` | Git hooks, --staged, --changed, CI reporters, lint-staged replacement |
| **GritQL Plugins** | `references/12-gritql-plugins.md` | Custom rules via GritQL, plugin configuration, pattern syntax |

## Installation

```bash
# npm (recommended — pin exact version)
npm i -D --save-exact @biomejs/biome

# pnpm / yarn / bun
pnpm add -D --save-exact @biomejs/biome
yarn add -D --exact @biomejs/biome
bun add -D --exact @biomejs/biome

# Initialize config
npx @biomejs/biome init

# Format + lint + organize imports in one pass
npx @biomejs/biome check --write ./src
```

## Quick Reference

- [Biome Docs](https://biomejs.dev/)
- [Lint Rules List](https://biomejs.dev/linter/rules/)
- [Configuration Reference](https://biomejs.dev/reference/configuration/)
- [CLI Reference](https://biomejs.dev/reference/cli/)
- [GitHub](https://github.com/biomejs/biome)
