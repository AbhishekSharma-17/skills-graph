# Turborepo — Running Tasks

> Source: [turborepo.dev/docs/crafting-your-repository/running-tasks](https://turborepo.dev/docs/crafting-your-repository/running-tasks)

## Table of Contents

- [Basic Usage](#basic-usage)
- [Task Dependencies](#task-dependencies)
- [Filtering Packages](#filtering-packages)
- [The --affected Flag](#the---affected-flag)
- [Concurrency](#concurrency)
- [Dry Runs](#dry-runs)
- [Output Control](#output-control)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Basic Usage

### Run a Single Task

```bash
# Run "build" in all packages that have a build script
turbo run build

# Shorthand (omit "run")
turbo build
```

### Run Multiple Tasks

```bash
# Run build, then lint and test (respecting dependsOn)
turbo run build lint test
```

Tasks are executed in dependency order based on `dependsOn` in `turbo.json`, with maximum parallelism for independent tasks.

### Pass Arguments to Underlying Scripts

Use `--` to pass arguments through to the underlying npm scripts:

```bash
# Pass --watch to the underlying test script
turbo run test -- --watch

# Pass --fix to the lint script
turbo run lint -- --fix
```

## Task Dependencies

Task ordering is controlled by `dependsOn` in `turbo.json`. Turborepo builds a directed acyclic graph (DAG) and executes tasks in topological order.

```jsonc
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"]       // Build dependencies first (topological)
    },
    "test": {
      "dependsOn": ["build"]        // Build this package before testing it
    },
    "lint": {}                       // No dependencies — runs in parallel
    "deploy": {
      "dependsOn": ["build", "test", "lint"]  // All must pass
    }
  }
}
```

Execution order for `turbo run deploy`:

```
lint ──────────┐
               ├──→ deploy
^build → build ┤
               │
test ──────────┘
```

## Filtering Packages

The `--filter` flag selects which packages to include:

### By Package Name

```bash
# Only run build for the web app
turbo run build --filter=@repo/web

# Multiple packages
turbo run build --filter=@repo/web --filter=@repo/api

# Glob pattern
turbo run build --filter="@repo/*"
```

### By Directory

```bash
# All packages in apps/
turbo run build --filter="./apps/*"

# Specific directory
turbo run build --filter="./packages/ui"
```

### By Dependency Relationship

```bash
# Package and all its dependencies (topological)
turbo run build --filter=@repo/web...

# Only the dependencies (not the package itself)
turbo run build --filter=...@repo/web

# Dependents of a package (packages that depend ON it)
turbo run build --filter=...^@repo/ui
```

### By Git Changes

```bash
# Packages changed since main
turbo run build --filter="[main]"

# Packages changed in the last commit
turbo run build --filter="[HEAD^1]"

# Combine: changed packages and their dependents
turbo run build --filter="...[main]"
```

### Combining Filters

Filters can be combined — results are the union:

```bash
# Changed packages OR the web app
turbo run build --filter="[main]" --filter=@repo/web
```

### Excluding Packages

```bash
# All packages except docs
turbo run build --filter="!@repo/docs"
```

## The --affected Flag

The `--affected` flag automatically detects which packages have changed compared to a base branch and runs tasks only for those packages (and their dependents).

```bash
# Run tests only for affected packages
turbo run test --affected

# Combine with explicit filters (intersection)
turbo run test --affected --filter="./apps/*"
```

### How --affected Works

1. Determines the base branch (defaults to `main` or `master`)
2. Computes the diff between HEAD and the base
3. Maps changed files to workspace packages
4. Includes packages that depend on changed packages
5. Runs tasks only in affected packages

### Customizing the Base Branch

```bash
# Compare against a specific branch
turbo run build --affected --base=develop

# Compare against a specific commit
turbo run build --affected --base=abc123
```

### CI Auto-Detection

In CI environments, Turborepo automatically detects the base ref:
- **GitHub Actions:** reads `GITHUB_BASE_REF`
- **GitLab CI:** reads `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`
- **Other CI:** falls back to `main`

## Concurrency

### Default Behavior

Turborepo runs tasks with maximum parallelism by default, limited by the number of CPU cores.

### Setting Concurrency

```bash
# Limit to 4 concurrent tasks
turbo run build --concurrency=4

# Use 50% of available cores
turbo run build --concurrency=50%

# Serial execution (one at a time)
turbo run build --concurrency=1
```

### Persistent Tasks and Concurrency

Persistent tasks (like `dev`) occupy a concurrency slot. If you run `turbo run dev` with 3 dev servers and `--concurrency=3`, all slots are taken and no other tasks can run.

## Dry Runs

Preview what Turborepo would do without executing:

```bash
# Text output
turbo run build --dry

# JSON output (for scripting)
turbo run build --dry=json
```

Dry runs show:
- Which tasks would execute
- In what order
- Cache hit/miss prediction
- Computed hashes

## Output Control

### Log Verbosity

```bash
# Minimal output
turbo run build --output-logs=errors-only

# Hash-only (show task names and hashes)
turbo run build --output-logs=hash-only

# Only show output for cache misses
turbo run build --output-logs=new-only

# Full output (default)
turbo run build --output-logs=full

# No output
turbo run build --output-logs=none
```

### UI Mode

```bash
# Streaming output (default)
turbo run build --ui=stream

# Terminal UI (interactive)
turbo run build --ui=tui
```

### Continue on Error

```bash
# Don't stop if one package's task fails
turbo run build --continue
```

### Log Files

Each task's output is saved to `.turbo/turbo-<task>.log` within the package directory, regardless of the output-logs setting.

## Common Patterns

### Development Workflow

```bash
# Start all dev servers in parallel
turbo run dev

# Start only the web app and its dependencies
turbo run dev --filter=@repo/web...
```

### Pre-Commit Check

```bash
# Run lint and typecheck for changed packages only
turbo run lint typecheck --affected
```

### Deployment Pipeline

```bash
# Build, test, and deploy one specific app
turbo run build test deploy --filter=@repo/api
```

## Common Pitfalls

1. **Using --filter without understanding scope** — `--filter=@repo/web` only runs the task in `@repo/web`. It does NOT build dependencies unless `dependsOn` includes `^build`.

2. **Running persistent tasks with non-persistent tasks** — `turbo run dev test` won't work well because `dev` never exits. Use separate commands or `turbo watch`.

3. **Forgetting --continue in CI** — By default, Turborepo stops on the first failure. Use `--continue` to see all failures at once.

4. **--affected without CI context** — On a developer's local machine without a clean git state, `--affected` may include more packages than expected. It works best in CI.

## Related

- [Configuration](01-configuration.md) — Task definitions in turbo.json
- [CI/CD Integration](07-ci-cd.md) — Running tasks in CI pipelines
- [Watch Mode](09-watch-mode.md) — Continuous task execution
