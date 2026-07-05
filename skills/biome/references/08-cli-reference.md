# Biome — CLI Reference

> Source: [biomejs.dev/reference/cli](https://biomejs.dev/reference/cli/)

## Table of Contents
- [Core Commands](#core-commands)
- [biome check](#biome-check)
- [biome lint](#biome-lint)
- [biome format](#biome-format)
- [biome ci](#biome-ci)
- [biome init](#biome-init)
- [biome migrate](#biome-migrate)
- [biome search](#biome-search)
- [Utility Commands](#utility-commands)
- [Global Options](#global-options)
- [Exit Codes](#exit-codes)
- [Reporters](#reporters)
- [Package Manager Scripts](#package-manager-scripts)

---

## Core Commands

| Command | Purpose | Writes Files |
|---------|---------|:------------:|
| `biome check` | Run formatter + linter + imports | With `--write` |
| `biome lint` | Run linter only | With `--write` |
| `biome format` | Run formatter only | With `--write` |
| `biome ci` | Read-only check for CI pipelines | Never |
| `biome init` | Create default biome.json | Yes |
| `biome migrate` | Migrate config from ESLint/Prettier | With `--write` |
| `biome search` | Search code with GritQL patterns | Never |

## biome check

The primary command. Runs formatting, linting, and import sorting in one pass.

```bash
# Dry run — report all issues
npx @biomejs/biome check ./src

# Apply safe fixes
npx @biomejs/biome check --write ./src

# Apply safe + unsafe fixes
npx @biomejs/biome check --write --unsafe ./src

# Check only staged files
npx @biomejs/biome check --write --staged

# Check files changed since default branch
npx @biomejs/biome check --write --changed

# Check files changed since specific ref
npx @biomejs/biome check --write --since=develop

# Watch mode
npx @biomejs/biome check --write --watch ./src

# Only run specific rules
npx @biomejs/biome check --only=correctness/noUnusedVariables ./src

# Skip specific rules
npx @biomejs/biome check --skip=style ./src
```

### Key Flags

| Flag | Description |
|------|-------------|
| `--write` | Apply fixes to files on disk |
| `--unsafe` | Include unsafe fixes (may change behavior) |
| `--staged` | Only process git-staged files |
| `--changed` | Only process files changed since default branch |
| `--since=REF` | Compare against specific git ref |
| `--watch` | Re-run on file changes |
| `--only=RULE` | Run only specified rules, groups, or domains |
| `--skip=RULE` | Skip specified rules, groups, or domains |

## biome lint

Run the linter only (no formatting, no import sorting).

```bash
# Report lint issues
npx @biomejs/biome lint ./src

# Auto-fix safe issues
npx @biomejs/biome lint --write ./src

# Auto-fix including unsafe
npx @biomejs/biome lint --write --unsafe ./src

# Suppress all current violations (migration helper)
npx @biomejs/biome lint --suppress --reason "migrating to biome" ./src

# Only lint specific domains
npx @biomejs/biome lint --only=react --only=test ./src

# Lint staged files
npx @biomejs/biome lint --staged ./src
```

### Suppress Flag

The `--suppress` flag adds `// biome-ignore` comments to all current violations. Invaluable during migration:

```bash
# Suppress all current issues with a reason
npx @biomejs/biome lint --suppress --reason "TODO: fix during biome migration" ./src
```

This lets you adopt Biome immediately without fixing every existing issue.

## biome format

Run the formatter only.

```bash
# Check formatting (dry run)
npx @biomejs/biome format ./src

# Apply formatting
npx @biomejs/biome format --write ./src

# Format staged files
npx @biomejs/biome format --write --staged

# Format with specific options (CLI overrides config)
npx @biomejs/biome format --write \
  --indent-style=space \
  --indent-width=4 \
  --line-width=120 \
  ./src

# Language-specific formatter toggles
npx @biomejs/biome format --write \
  --javascript-formatter-enabled=true \
  --json-formatter-enabled=false \
  ./src
```

## biome ci

Read-only check designed for CI pipelines. Never modifies files. Returns non-zero exit code if any issues are found.

```bash
# Standard CI check
npx @biomejs/biome ci ./src

# CI with specific reporter
npx @biomejs/biome ci --reporter=github ./src

# CI for only changed files (useful in PR checks)
npx @biomejs/biome ci --changed ./src

# CI with max diagnostics
npx @biomejs/biome ci --max-diagnostics=50 ./src
```

`biome ci` does not support `--staged` (staging is for pre-commit, not CI).

## biome init

Bootstrap a new Biome project:

```bash
# Create biome.json with defaults
npx @biomejs/biome init

# Generated file
{
  "$schema": "https://biomejs.dev/schemas/2.5.0/schema.json",
  "vcs": { "enabled": false, "clientKind": "git", "useIgnoreFile": false },
  "organizeImports": { "enabled": true },
  "linter": { "enabled": true, "rules": { "recommended": true } }
}
```

## biome migrate

Convert ESLint and Prettier configurations to Biome:

```bash
# Migrate ESLint config
npx @biomejs/biome migrate eslint --write

# Migrate Prettier config
npx @biomejs/biome migrate prettier --write

# Include "inspired" rules (not direct ports)
npx @biomejs/biome migrate eslint --write --include-inspired

# Migrate config format on major version upgrade
npx @biomejs/biome migrate --write
```

## biome search

Search code using GritQL patterns (experimental):

```bash
# Find all console.log calls
npx @biomejs/biome search "console.log($msg)" ./src

# Find unused async functions
npx @biomejs/biome search "async function $name() { $body }" ./src
```

## Utility Commands

```bash
# Show version
npx @biomejs/biome version

# Upgrade to latest version
npx @biomejs/biome upgrade

# Start daemon server (for IDE integration)
npx @biomejs/biome start

# Stop daemon server
npx @biomejs/biome stop

# Debug information (for bug reports)
npx @biomejs/biome rage

# Show documentation for a rule or topic
npx @biomejs/biome explain correctness/noUnusedVariables

# Clean daemon logs
npx @biomejs/biome clean

# LSP proxy (for editors)
npx @biomejs/biome lsp-proxy
```

## Global Options

These apply to all commands:

| Flag | Description |
|------|-------------|
| `--colors=off\|force` | Control terminal colors |
| `--use-server` | Connect to daemon instead of single-shot |
| `--verbose` | Show detailed file processing info |
| `--config-path=PATH` | Specify config file location |
| `--max-diagnostics=N` | Limit output (default: 20, `none` for unlimited) |
| `--skip-parse-errors` | Continue despite syntax errors |
| `--error-on-warnings` | Treat warnings as errors |
| `--reporter=FORMAT` | Output format |
| `--diagnostic-level=LEVEL` | Minimum severity to show |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success, no issues |
| `1` | Lint/format errors found |
| `2` | CLI usage error |

## Reporters

| Reporter | Use Case |
|----------|----------|
| `default` | Human-readable terminal output |
| `json` | Machine-readable JSON |
| `json-pretty` | Pretty-printed JSON |
| `github` | GitHub Actions annotations |
| `gitlab` | GitLab CI annotations |
| `junit` | JUnit XML format |
| `summary` | Condensed summary |
| `checkstyle` | Checkstyle XML |
| `sarif` | SARIF for security tools |
| `rdjson` | ReviewDog JSON |
| `concise` | Minimal one-line-per-issue output |

## Package Manager Scripts

### package.json scripts

```json
{
  "scripts": {
    "check": "biome check ./src",
    "check:fix": "biome check --write ./src",
    "lint": "biome lint ./src",
    "lint:fix": "biome lint --write ./src",
    "format": "biome format --write ./src",
    "ci": "biome ci ./src"
  }
}
```

### Pre-commit hook (without lint-staged)

```json
{
  "scripts": {
    "pre-commit": "biome check --write --staged --no-errors-on-unmatched"
  }
}
```

Biome's `--staged` flag replaces lint-staged entirely for Biome-supported files.
