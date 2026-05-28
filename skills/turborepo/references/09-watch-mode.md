# Turborepo — Watch Mode

> Source: [turborepo.dev/docs/reference/watch](https://turborepo.dev/docs/reference/watch)

## Overview

`turbo watch` continuously monitors your workspace for file changes and re-runs tasks when their inputs change. Unlike `turbo run dev` (which runs persistent dev servers), `turbo watch` re-executes non-persistent tasks like `build`, `test`, or `typecheck` whenever source files change.

## Basic Usage

```bash
# Watch and re-run build on file changes
turbo watch build

# Watch multiple tasks
turbo watch build typecheck

# Watch with filtering
turbo watch build --filter=@repo/ui
```

## How It Works

1. Turborepo starts a file system watcher on all workspace packages
2. When a file changes, it determines which packages are affected
3. It re-runs the specified tasks only for affected packages
4. Dependencies are respected: if `@repo/ui` changes, `@repo/web` (which depends on it) also rebuilds

```
File change in packages/ui/src/Button.tsx
    ↓
Detects @repo/ui is affected
    ↓
Re-runs build for @repo/ui
    ↓
Detects @repo/web depends on @repo/ui
    ↓
Re-runs build for @repo/web
```

## Watch vs Dev

| Feature | `turbo watch <task>` | `turbo run dev` |
|---------|---------------------|-----------------|
| **Purpose** | Re-run tasks on change | Start long-running processes |
| **Task type** | Non-persistent (build, test) | Persistent (dev servers) |
| **Caching** | Uses Turborepo cache | `cache: false` recommended |
| **Use case** | Continuous type-checking, test re-runs | Development servers with HMR |

### Common Combination

Run dev servers alongside continuous type-checking:

```bash
# Terminal 1: Dev servers
turbo run dev

# Terminal 2: Continuous type-checking
turbo watch typecheck
```

## Task-Level Filtering

By default, `turbo watch` operates at the **package level**: if any file in a package changes, all specified tasks in that package re-run. This can be too broad.

Enable task-level filtering to only re-run when files matching a task's `inputs` glob change:

```jsonc
// turbo.json
{
  "tasks": {
    "build": {
      "inputs": ["src/**", "tsconfig.json"],
      "outputs": ["dist/**"]
    },
    "test": {
      "inputs": ["src/**", "test/**", "jest.config.*"]
    }
  }
}
```

With task-level inputs defined, changing a test file only re-runs `test`, not `build`.

## Combining with --filter

```bash
# Watch only the web app and its dependencies
turbo watch build --filter=@repo/web...

# Watch all packages in apps/
turbo watch build --filter="./apps/*"
```

## Debouncing

`turbo watch` automatically debounces rapid file changes (e.g., when saving multiple files in quick succession or when a build tool writes many files). You don't need to configure this.

## Limitations

- **Persistent tasks** — `turbo watch` is for non-persistent tasks. Use `turbo run dev` for dev servers
- **stdin** — Interactive tasks (requiring stdin input) don't work with watch mode
- **Performance** — Watching very large monorepos (hundreds of packages) may use significant memory for file watchers

## Common Patterns

### Continuous Type-Checking in Development

```bash
turbo watch typecheck --filter=@repo/web...
```

### Rebuild Shared Packages on Change

```bash
# Useful when apps use JIT packages but some packages need compilation
turbo watch build --filter="./packages/*"
```

### Test on Save

```bash
# Re-run tests when source or test files change
turbo watch test --filter=@repo/utils
```

## Common Pitfalls

1. **Using watch for dev servers** — `turbo watch dev` is redundant. Dev servers already watch files internally. Use `turbo run dev` instead.

2. **Missing inputs configuration** — Without specific `inputs` in turbo.json, any file change triggers all tasks. Define narrow input globs.

3. **Watch + persistent = conflict** — Don't set `"persistent": true` on tasks you want to use with `turbo watch`.

## Related

- [Running Tasks](06-running-tasks.md) — `turbo run` command
- [Configuration](01-configuration.md) — Defining task inputs
- [CLI Reference](12-cli-reference.md) — Watch command flags
