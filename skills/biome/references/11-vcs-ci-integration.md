# Biome — VCS & CI/CD Integration

> Source: [biomejs.dev/guides/integrate-in-vcs](https://biomejs.dev/guides/integrate-in-vcs/)

## Table of Contents
- [VCS Integration](#vcs-integration)
- [Git Hooks](#git-hooks)
- [Replacing lint-staged](#replacing-lint-staged)
- [CI/CD Integration](#cicd-integration)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Other CI Providers](#other-ci-providers)
- [PR-Scoped Checks](#pr-scoped-checks)
- [Reporters](#reporters)
- [Caching in CI](#caching-in-ci)
- [Common Patterns](#common-patterns)

---

## VCS Integration

Enable VCS integration to respect `.gitignore` and process only changed/staged files:

```json
{
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true,
    "defaultBranch": "main"
  }
}
```

| Field | Purpose |
|-------|---------|
| `enabled` | Activate VCS features |
| `clientKind` | VCS type (only `"git"` supported) |
| `useIgnoreFile` | Respect `.gitignore` patterns |
| `defaultBranch` | Reference for `--changed` flag |

When `useIgnoreFile` is enabled, files matching `.gitignore` and `.git/info/exclude` patterns are skipped by all Biome commands.

## Git Hooks

### Pre-commit Hook (Manual)

```bash
#!/bin/sh
# .git/hooks/pre-commit
npx @biomejs/biome check --write --staged --no-errors-on-unmatched
```

### Using Husky

```bash
# Install husky
npm i -D husky
npx husky init

# Create pre-commit hook
echo 'npx @biomejs/biome check --write --staged --no-errors-on-unmatched' > .husky/pre-commit
```

### Using lefthook

```yaml
# lefthook.yml
pre-commit:
  commands:
    biome:
      glob: "*.{js,ts,jsx,tsx,json,css,graphql}"
      run: npx @biomejs/biome check --write --staged --no-errors-on-unmatched {staged_files}
```

### Using simple-git-hooks

```json
// package.json
{
  "simple-git-hooks": {
    "pre-commit": "npx @biomejs/biome check --write --staged --no-errors-on-unmatched"
  }
}
```

### Key Flags for Pre-commit

| Flag | Purpose |
|------|---------|
| `--staged` | Process only staged files |
| `--write` | Auto-fix and re-stage |
| `--no-errors-on-unmatched` | Don't error if no matching files are staged |

## Replacing lint-staged

Biome's `--staged` flag replaces `lint-staged` for all Biome-supported files:

### Before (with lint-staged)

```json
{
  "lint-staged": {
    "*.{js,ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.json": ["prettier --write"],
    "*.css": ["prettier --write"]
  }
}
```

### After (Biome only)

```bash
# .husky/pre-commit
npx @biomejs/biome check --write --staged --no-errors-on-unmatched
```

No `lint-staged` needed. Biome handles JS, TS, JSX, TSX, JSON, CSS, and GraphQL in one pass.

If you still use other tools (e.g., `stylelint` for SCSS), keep `lint-staged` for those and run Biome separately:

```json
{
  "lint-staged": {
    "*.scss": ["stylelint --fix"]
  }
}
```

```bash
# .husky/pre-commit
npx @biomejs/biome check --write --staged --no-errors-on-unmatched
npx lint-staged
```

## CI/CD Integration

Use `biome ci` for CI pipelines. It's read-only and returns a non-zero exit code on issues.

```bash
npx @biomejs/biome ci ./src
```

### biome ci vs biome check

| Feature | `biome ci` | `biome check` |
|---------|-----------|--------------|
| Writes files | Never | With `--write` |
| `--staged` | Not available | Available |
| Exit code on issues | Non-zero | Non-zero |
| Designed for | CI pipelines | Local development |

## GitHub Actions

### Basic Setup

```yaml
name: Code Quality
on:
  push:
    branches: [main]
  pull_request:

jobs:
  biome:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npx @biomejs/biome ci --reporter=github ./src
```

The `--reporter=github` flag produces GitHub-native annotations that appear inline on PR diffs.

### PR-Only Changed Files

```yaml
jobs:
  biome:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npx @biomejs/biome ci --changed --since=origin/main --reporter=github ./src
```

### Using the Official Biome Action

```yaml
jobs:
  biome:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: biomejs/setup-biome@v2
        with:
          version: latest
      - run: biome ci --reporter=github ./src
```

## GitLab CI

```yaml
biome:
  stage: lint
  image: node:22-alpine
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - node_modules/
  script:
    - npm ci
    - npx @biomejs/biome ci --reporter=gitlab ./src
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## Other CI Providers

### Generic CI

```bash
npm ci
npx @biomejs/biome ci --reporter=summary ./src
```

### Jenkins (JUnit output)

```bash
npx @biomejs/biome ci --reporter=junit ./src > biome-results.xml
```

### Azure Pipelines

```yaml
- script: |
    npm ci
    npx @biomejs/biome ci --reporter=sarif ./src > biome.sarif
  displayName: 'Biome Check'
```

## PR-Scoped Checks

### Check only changed files in PR

```bash
# Files changed since default branch
npx @biomejs/biome ci --changed ./src

# Files changed since specific ref
npx @biomejs/biome ci --changed --since=origin/main ./src
```

Note: `--changed` checks files with any diff (even whitespace changes), not just the modified lines within files.

## Reporters

| Reporter | Output | Best For |
|----------|--------|----------|
| `github` | PR annotations | GitHub Actions |
| `gitlab` | MR code quality report | GitLab CI |
| `junit` | XML test report | Jenkins, Azure |
| `sarif` | Security analysis format | Security tooling |
| `json` | Machine-readable JSON | Custom integrations |
| `summary` | Condensed counts | Quick CI feedback |
| `checkstyle` | Checkstyle XML | Legacy CI systems |
| `concise` | One-line per issue | Compact logs |

## Caching in CI

Biome itself doesn't need caching (it's a single binary). Cache `node_modules` to speed up `npm ci`:

```yaml
# GitHub Actions
- uses: actions/setup-node@v4
  with:
    node-version: 22
    cache: npm
```

For standalone Biome (no npm):

```yaml
- uses: biomejs/setup-biome@v2
  with:
    version: latest
# No cache needed — binary download is fast
```

## Common Patterns

### Complete Pre-commit + CI Setup

```json
// biome.json
{
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true,
    "defaultBranch": "main"
  }
}
```

```json
// package.json
{
  "scripts": {
    "check": "biome check ./src",
    "check:fix": "biome check --write ./src",
    "ci": "biome ci ./src"
  }
}
```

```bash
# .husky/pre-commit
npx @biomejs/biome check --write --staged --no-errors-on-unmatched
```

```yaml
# .github/workflows/ci.yml
- run: npx @biomejs/biome ci --reporter=github ./src
```

### Enforce No Warnings in CI

```bash
npx @biomejs/biome ci --error-on-warnings ./src
```

This fails CI on warnings too, ensuring they get fixed rather than accumulating.
