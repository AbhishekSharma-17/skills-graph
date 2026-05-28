# Turborepo — CI/CD Integration

> Source: [turborepo.dev/docs/crafting-your-repository/constructing-ci](https://turborepo.dev/docs/crafting-your-repository/constructing-ci)

## Table of Contents

- [General CI Strategy](#general-ci-strategy)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Remote Caching in CI](#remote-caching-in-ci)
- [Using --affected in CI](#using---affected-in-ci)
- [Optimizing CI Pipelines](#optimizing-ci-pipelines)
- [Common Pitfalls](#common-pitfalls)

## General CI Strategy

Turborepo accelerates CI pipelines through two mechanisms:

1. **Remote Caching** — Reuse build artifacts from previous CI runs
2. **--affected** — Only run tasks for packages that changed

A well-configured Turborepo CI pipeline typically:
- Installs dependencies (cached by package manager)
- Runs `turbo run build lint test` (cached by Turborepo)
- Deploys only affected applications

## GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 2    # Needed for --affected to work

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Setup pnpm
        uses: pnpm/action-setup@v4

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Build
        run: pnpm turbo run build

      - name: Lint
        run: pnpm turbo run lint

      - name: Test
        run: pnpm turbo run test
```

### With Vercel Remote Cache

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
      TURBO_TEAM: ${{ vars.TURBO_TEAM }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - uses: actions/setup-node@v4
        with:
          node-version: 22

      - uses: pnpm/action-setup@v4

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Build, Lint, Test
        run: pnpm turbo run build lint test
```

### With --affected on PRs

```yaml
jobs:
  ci:
    runs-on: ubuntu-latest
    env:
      TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
      TURBO_TEAM: ${{ vars.TURBO_TEAM }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0    # Full history for accurate --affected

      - uses: actions/setup-node@v4
        with:
          node-version: 22

      - uses: pnpm/action-setup@v4

      - run: pnpm install --frozen-lockfile

      - name: Build (affected only)
        run: pnpm turbo run build --affected

      - name: Lint (affected only)
        run: pnpm turbo run lint --affected

      - name: Test (affected only)
        run: pnpm turbo run test --affected
```

### Matrix Strategy for Parallel Jobs

```yaml
jobs:
  ci:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        task: [build, lint, test]
    env:
      TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
      TURBO_TEAM: ${{ vars.TURBO_TEAM }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - uses: pnpm/action-setup@v4
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo run ${{ matrix.task }} --affected
```

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test

variables:
  TURBO_TOKEN: $TURBO_TOKEN
  TURBO_TEAM: "my-team"

.turbo-cache:
  before_script:
    - corepack enable
    - pnpm install --frozen-lockfile

build:
  stage: build
  extends: .turbo-cache
  script:
    - pnpm turbo run build --affected

test:
  stage: test
  extends: .turbo-cache
  script:
    - pnpm turbo run lint test --affected
```

## Remote Caching in CI

### Setting Up Secrets

1. Generate a Vercel token at https://vercel.com/account/tokens
2. Add `TURBO_TOKEN` as a repository secret in your CI provider
3. Set `TURBO_TEAM` to your Vercel team slug

### Self-Hosted Cache in CI

```yaml
env:
  TURBO_API: "https://cache.internal.example.com"
  TURBO_TEAM: "my-team"
  TURBO_TOKEN: ${{ secrets.TURBO_CACHE_TOKEN }}
```

### Read-Only Cache in PR Builds

Prevent PR builds from polluting the main cache:

```yaml
- name: Build (read-only cache for PRs)
  run: pnpm turbo run build --remote-cache-read-only
  if: github.event_name == 'pull_request'
```

## Using --affected in CI

### Requirements

- `fetch-depth: 0` (or at least 2) in checkout to have git history
- CI environment provides the base ref (GitHub Actions sets `GITHUB_BASE_REF` automatically)

### How It Works in CI

1. On a PR: compares against the PR's target branch
2. On push to main: compares against the previous commit
3. Turborepo reads `GITHUB_BASE_REF` (or equivalent) to determine the comparison point

### Combining --affected with Remote Cache

They work together. `--affected` determines WHICH packages to run. Remote cache determines WHETHER to actually execute or replay from cache. Together, they minimize CI time.

## Optimizing CI Pipelines

### 1. Cache Dependencies

Use your package manager's cache alongside Turborepo's:

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: 22
    cache: 'pnpm'   # Caches pnpm store
```

### 2. Combine Tasks in a Single Run

```bash
# One turbo invocation is faster than three
pnpm turbo run build lint test
```

### 3. Use --continue for Full Failure Visibility

```bash
# See all failures, not just the first
pnpm turbo run build lint test --continue
```

### 4. Minimize fetch-depth When Not Using --affected

```yaml
# Without --affected, shallow clone is fine
- uses: actions/checkout@v4
  with:
    fetch-depth: 1
```

### 5. Pin Turborepo Version

```bash
# In CI, pin to prevent breaking changes
npx turbo@2.9.15 run build
```

Or better, use the version from `devDependencies` via your package manager:

```bash
pnpm turbo run build   # Uses locally installed turbo
```

## Common Pitfalls

1. **Missing fetch-depth for --affected** — `actions/checkout@v4` defaults to `fetch-depth: 1` (shallow clone). `--affected` needs history to compute diffs. Use `fetch-depth: 0` or at least `2`.

2. **TURBO_TOKEN not set** — Remote caching silently falls back to local-only. Check CI logs for "Remote caching disabled" warnings.

3. **Inconsistent Node/pnpm versions** — Different CI runner versions produce different hashes. Pin versions in your workflow.

4. **Running turbo globally** — Using `npx turbo` may use a different version than your project's `devDependencies`. Always use `pnpm turbo` (or equivalent) to use the local version.

5. **Caching node_modules in CI** — Don't cache `node_modules` directly. Cache the package manager store instead. Turborepo's cache is separate from dependency installation.

## Related

- [Remote Caching](03-remote-caching.md) — Remote cache setup
- [Running Tasks](06-running-tasks.md) — CLI usage and filtering
- [Docker Deployment](08-docker.md) — Docker builds in CI
