# Turborepo — CLI Reference

> Source: [turborepo.dev/docs/reference](https://turborepo.dev/docs/reference)

## Table of Contents

- [turbo run](#turbo-run)
- [turbo watch](#turbo-watch)
- [turbo prune](#turbo-prune)
- [turbo gen](#turbo-gen)
- [turbo ls](#turbo-ls)
- [turbo query](#turbo-query)
- [turbo login / link / unlink](#turbo-login--link--unlink)
- [turbo daemon](#turbo-daemon)
- [turbo boundaries](#turbo-boundaries)
- [Global Flags](#global-flags)
- [Environment Variables](#environment-variables)

## turbo run

Execute tasks across workspace packages.

```bash
turbo run <task1> [task2] [...] [flags]
```

### Frequently Used Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--filter` | Select packages | `--filter=@repo/web` |
| `--affected` | Only changed packages | `--affected` |
| `--force` | Ignore cache | `--force` |
| `--concurrency` | Parallel limit | `--concurrency=4` |
| `--continue` | Don't stop on error | `--continue` |
| `--dry` | Preview without executing | `--dry=json` |
| `--summarize` | Generate run summary | `--summarize` |
| `--output-logs` | Control output | `--output-logs=errors-only` |
| `--env-mode` | Environment handling | `--env-mode=strict` |
| `--ui` | Terminal UI mode | `--ui=tui` |
| `--remote-only` | Only use remote cache | `--remote-only` |
| `--remote-cache-read-only` | Don't write to remote | `--remote-cache-read-only` |
| `--cache-dir` | Local cache location | `--cache-dir=.turbo/cache` |
| `--` | Pass args to scripts | `-- --watch` |

### Filter Syntax

```bash
# By package name
--filter=@repo/web
--filter=@repo/web --filter=@repo/api

# By directory
--filter="./apps/*"
--filter="./packages/ui"

# With dependencies
--filter=@repo/web...       # Package + its dependencies
--filter=...@repo/web       # Only its dependencies

# By git changes
--filter="[main]"           # Changed since main
--filter="...[main]"        # Changed + their dependents

# Exclude
--filter="!@repo/docs"

# Glob
--filter="@repo/*"
```

### Examples

```bash
turbo run build lint test
turbo run build --filter=@repo/web --force
turbo run test --affected --continue
turbo run build --dry=json
turbo run build --summarize
turbo run test -- --coverage
```

## turbo watch

Continuously re-run tasks on file changes.

```bash
turbo watch <task1> [task2] [...] [flags]
```

Supports the same flags as `turbo run` plus file watching behavior. See [Watch Mode](09-watch-mode.md) for details.

```bash
turbo watch build
turbo watch build typecheck --filter=@repo/web...
```

## turbo prune

Generate a minimal monorepo subset for a target package.

```bash
turbo prune <package-name> [flags]
```

| Flag | Description |
|------|-------------|
| `--docker` | Split output for Docker layer caching |
| `--out-dir` | Output directory (default: `out/`) |

```bash
turbo prune @repo/web
turbo prune @repo/web --docker
turbo prune @repo/api --out-dir=pruned
```

See [Docker Deployment](08-docker.md) for Dockerfile patterns.

## turbo gen

Generate code and workspaces.

```bash
turbo gen [generator-name] [flags]
```

### Subcommands

```bash
# Create a new workspace (interactive)
turbo gen workspace

# Create workspace from copy
turbo gen workspace --copy

# Run custom generators
turbo gen
turbo gen component
```

| Flag | Description |
|------|-------------|
| `--name` | Workspace name |
| `--destination` | Target directory |
| `--copy` | Copy from existing workspace |
| `--config` | Custom generator config path |

See [Code Generation](10-generators.md) for custom generator setup.

## turbo ls

List workspace packages and their information.

```bash
turbo ls [flags]
```

```bash
# List all packages
turbo ls

# List affected packages
turbo ls --affected

# List with filter
turbo ls --filter="./apps/*"

# JSON output
turbo ls --output=json
```

## turbo query

Query workspace dependency graph using GraphQL.

```bash
turbo query [query-string] [flags]
```

### Interactive Mode

```bash
# Open GraphiQL IDE in browser
turbo query
```

### Direct Queries

```bash
# Get all packages
turbo query "query { packages { items { name path } } }"

# Get affected packages with test task
turbo query "query { affectedPackages(base: \"main\") { items { name } } }"

# From a file
turbo query --file=query.graphql
```

### Useful Queries

```graphql
# All packages and their dependencies
query {
  packages {
    items {
      name
      directDependencies {
        items { name }
      }
    }
  }
}

# Affected packages
query {
  affectedPackages(base: "main") {
    items {
      name
      path
    }
  }
}
```

## turbo login / link / unlink

Manage Vercel Remote Cache connection.

```bash
# Authenticate with Vercel
turbo login

# Link repo to Vercel team for remote caching
turbo link

# Disconnect from remote cache
turbo unlink

# Logout
turbo logout
```

## turbo daemon

Manage the background Turborepo daemon process.

```bash
# Show daemon status
turbo daemon status

# Stop the daemon
turbo daemon stop

# Clean daemon cache
turbo daemon clean
```

The daemon runs in the background for faster subsequent runs. It's started automatically and rarely needs manual management.

## turbo boundaries

Check package boundary rules.

```bash
turbo boundaries
```

Reports violations of import rules, undeclared dependencies, and tag-based rules. See [Boundaries](11-boundaries.md).

## Global Flags

These flags work with all commands:

| Flag | Description |
|------|-------------|
| `--version` | Print version |
| `--help` | Show help |
| `--verbosity` | Log level (0-2) |
| `--cwd` | Set working directory |
| `--no-daemon` | Disable background daemon |
| `--color` | Force color output |
| `--no-color` | Disable color output |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TURBO_TOKEN` | Authentication token for remote cache |
| `TURBO_TEAM` | Team identifier for remote cache |
| `TURBO_API` | Remote cache API URL |
| `TURBO_FORCE` | Skip cache reads (`true`/`false`) |
| `TURBO_REMOTE_ONLY` | Only use remote cache |
| `TURBO_LOG_VERBOSITY` | Log level |
| `TURBO_REMOTE_CACHE_SIGNATURE_KEY` | Key for signing cached artifacts |
| `TURBO_CACHE_DIR` | Local cache directory |
| `TURBO_TELEMETRY_DISABLED` | Disable telemetry |

## Common Pitfalls

1. **`turbo run` vs `turbo`** — `turbo build` is shorthand for `turbo run build`. Both work, but `turbo run` is more explicit and supports all flags.

2. **Global vs local turbo** — Always prefer the locally installed version (`pnpm turbo`, `npx turbo`) over a globally installed one to ensure version consistency.

3. **Quoting filter expressions** — Shell glob characters need quoting: `--filter="@repo/*"` not `--filter=@repo/*`.

4. **--dry doesn't check cache** — Dry runs show the task graph but don't verify remote cache availability.

## Related

- [Running Tasks](06-running-tasks.md) — Detailed task execution guide
- [Docker Deployment](08-docker.md) — turbo prune usage
- [Code Generation](10-generators.md) — turbo gen usage
