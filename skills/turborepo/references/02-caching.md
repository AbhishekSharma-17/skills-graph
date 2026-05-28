# Turborepo — Caching

> Source: [turborepo.dev/docs/crafting-your-repository/caching](https://turborepo.dev/docs/crafting-your-repository/caching)

## Table of Contents

- [How Caching Works](#how-caching-works)
- [Cache Inputs (Hash Computation)](#cache-inputs-hash-computation)
- [Cache Outputs](#cache-outputs)
- [Cache Hit vs Miss](#cache-hit-vs-miss)
- [Configuring Cache Behavior](#configuring-cache-behavior)
- [Cache Location](#cache-location)
- [Debugging Cache](#debugging-cache)
- [Common Pitfalls](#common-pitfalls)

## How Caching Works

Turborepo uses content-aware hashing to determine whether a task needs to run. For every task, it computes a hash from the task's inputs. If a matching hash is found in the cache, Turborepo replays the cached output (both files and terminal logs) instead of running the task.

```
Source files + env vars + dependency outputs + config
              ↓
     Hash (e.g., abc123def)
              ↓
     Cache lookup
    ┌─────────┴─────────┐
    │                    │
  HIT                  MISS
    │                    │
  Replay               Run task
  cached output        Store output
  (~0ms)               in cache
```

## Cache Inputs (Hash Computation)

The hash for each task is computed from:

1. **Source files** — All files in the package (or those matching the `inputs` glob), excluding `.gitignore`d files
2. **Environment variables** — Variables listed in `env`, `globalEnv`, and framework-specific inferred variables
3. **Dependency outputs** — Hashes of internal dependency packages' outputs
4. **Lock file** — Relevant entries from the package lock file (tracks external dependency versions)
5. **Task configuration** — The task definition in `turbo.json`
6. **Turborepo version** — Different Turborepo versions produce different hashes

### Narrowing Inputs

Reduce unnecessary cache misses by specifying exactly which files matter:

```jsonc
{
  "tasks": {
    "build": {
      "inputs": [
        "src/**",
        "tsconfig.json",
        "!src/**/*.test.ts",    // Test changes don't affect build
        "!src/**/*.spec.ts"
      ]
    },
    "test": {
      "inputs": [
        "src/**",
        "test/**",
        "jest.config.*"
      ]
    }
  }
}
```

### Framework Inference

Turborepo automatically detects and includes framework-specific environment variables:

| Framework | Auto-included variables |
|-----------|------------------------|
| Next.js | `NEXT_PUBLIC_*` |
| Vite | `VITE_*` |
| Create React App | `REACT_APP_*` |
| Nuxt | `NUXT_*`, `NITRO_*` |
| Gatsby | `GATSBY_*` |
| SvelteKit | `PUBLIC_*` |

## Cache Outputs

The `outputs` key tells Turborepo which files to save after a task completes. On a cache hit, these files are restored to their original locations.

```jsonc
{
  "tasks": {
    "build": {
      "outputs": [
        "dist/**",                // Compiled output
        ".next/**",               // Next.js build output
        "!.next/cache/**"         // Exclude Next.js internal cache
      ]
    }
  }
}
```

**Important:** If `outputs` is omitted or empty (`[]`), Turborepo only replays terminal logs on cache hits — no files are restored. This is appropriate for tasks like `lint` or `typecheck` that produce no artifacts.

## Cache Hit vs Miss

### Cache Hit — FULL TURBO

```
$ turbo run build

 @repo/ui:build: cache hit, replaying logs abc123def
 @repo/web:build: cache hit, replaying logs def456ghi

 Tasks:    2 successful, 2 total
 Cached:   2 cached, 2 total
   Time:   87ms >>> FULL TURBO
```

### Cache Miss

```
$ turbo run build

 @repo/ui:build: cache miss, executing abc123def
 @repo/ui:build: > tsc --build
 @repo/web:build: cache hit, replaying logs def456ghi

 Tasks:    2 successful, 2 total
 Cached:   1 cached, 2 total
   Time:   3.2s
```

## Configuring Cache Behavior

### Disable Cache for a Task

```jsonc
{
  "tasks": {
    "dev": {
      "cache": false       // Never cache
    }
  }
}
```

### Force Cache Miss (CLI)

```bash
# Skip reading from cache, but still write to it
turbo run build --force

# Equivalent: ignore existing cache
TURBO_FORCE=true turbo run build
```

### Cache Signing (Integrity)

Enable artifact signature verification (prevents tampering, especially with remote cache):

```jsonc
// .turbo/config.json
{
  "signature": true
}
```

This requires setting `TURBO_REMOTE_CACHE_SIGNATURE_KEY` env var.

## Cache Location

### Local Cache

Stored in `node_modules/.cache/turbo` (default). Can be changed with `--cache-dir`:

```bash
turbo run build --cache-dir=".turbo/cache"
```

### Clearing Cache

```bash
# Clear local Turborepo cache
rm -rf node_modules/.cache/turbo

# Or use turbo daemon to clean
turbo daemon clean
```

### Remote Cache

See [Remote Caching](03-remote-caching.md) for sharing cache across machines.

## Debugging Cache

### Dry Run

See what would run without actually running:

```bash
turbo run build --dry=json
```

Output includes the computed hash, inputs, and whether it's a cache hit.

### Summarize

Get a detailed summary of a run:

```bash
turbo run build --summarize
```

Creates a `.turbo/runs/<run-id>.json` file with full task details, hashes, timing, and cache hit/miss status.

### Verbosity

```bash
# Show hash details
turbo run build --verbosity=2

# Show environment variable contributions to hash
turbo run build --env-mode=strict --verbosity=2
```

### Why Did My Cache Miss?

Common causes of unexpected cache misses:

1. **Untracked environment variable** — An env var changed but isn't in `env`/`globalEnv`. Turborepo's Strict Mode (default in v2) catches this.

2. **Unstable file content** — Build artifacts with timestamps, random IDs, or build metadata create different hashes every run.

3. **Different Turborepo version** — Each version has its own hash computation.

4. **Lock file changes** — Installing or updating any dependency changes the lock file.

5. **OS/platform differences** — Line endings (CRLF vs LF) can cause hash differences between Windows and Unix.

## Common Pitfalls

1. **Empty outputs for build tasks** — If your build produces files in `dist/`, you must list them in `outputs`. Without this, cache hits replay logs but don't restore the built files.

2. **Caching non-deterministic tasks** — Tasks that produce different output on each run (e.g., including timestamps) will never get cache hits.

3. **Over-broad inputs** — Using default inputs (all package files) means ANY file change causes a cache miss. Narrow with specific globs.

4. **Forgetting `.gitignore`** — Turborepo respects `.gitignore` for inputs. If a generated file is in `.gitignore`, it won't be included in the hash.

5. **framework env var inference** — Turborepo auto-includes `NEXT_PUBLIC_*`, `VITE_*`, etc. in hashes. If these change between environments, you'll get cache misses.

## Related

- [Configuration](01-configuration.md) — turbo.json task definitions
- [Remote Caching](03-remote-caching.md) — Share cache across machines
- [Environment Variables](05-environment-variables.md) — How env vars affect caching
