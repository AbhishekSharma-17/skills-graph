# uv — Resolution & Caching

> Source: [Resolution](https://docs.astral.sh/uv/concepts/resolution/) | [Caching](https://docs.astral.sh/uv/concepts/cache/)

## Table of Contents

- [Resolution Strategies](#resolution-strategies)
- [Pre-release Handling](#pre-release-handling)
- [Constraints and Overrides](#constraints-and-overrides)
- [Dependency Exclusions](#dependency-exclusions)
- [Multi-Platform Resolution](#multi-platform-resolution)
- [Reproducible Resolutions](#reproducible-resolutions)
- [Caching](#caching)
- [Performance Tips](#performance-tips)

## Resolution Strategies

uv supports three resolution modes that control how versions are selected:

### Highest (Default)

Selects the latest compatible version of every package:

```bash
uv lock                              # Default behavior
uv pip compile requirements.in       # Also default
```

### Lowest

Installs the minimum acceptable version for all dependencies, both direct and transitive. Useful for CI to verify compatibility with declared lower bounds:

```bash
uv lock --resolution lowest
uv pip compile --resolution lowest requirements.in
```

### Lowest-Direct

Minimum versions for direct dependencies, latest for transitive. A middle ground for testing:

```bash
uv lock --resolution lowest-direct
```

### Configuration

```toml
[tool.uv]
resolution = "lowest"  # Apply globally
```

### Best Practice for Libraries

Run tests with multiple resolution strategies in CI:

```yaml
strategy:
  matrix:
    resolution: ["highest", "lowest"]
steps:
  - run: uv sync --resolution ${{ matrix.resolution }}
  - run: uv run pytest
```

## Pre-release Handling

### Modes

| Mode | Behavior |
|------|----------|
| `if-necessary` (default) | Use pre-releases only when no stable version satisfies the requirement |
| `allow` | Consider pre-releases for all packages equally |
| `disallow` | Never use pre-releases |
| `explicit` | Only consider pre-releases when the requirement contains a pre-release identifier |

```bash
# Global flag
uv lock --prerelease allow

# Per-package
uv lock --prerelease-package torch=allow
```

### Configuration

```toml
[tool.uv]
prerelease = "if-necessary"
prerelease-package = { torch = "allow", numpy = "disallow" }
```

## Constraints and Overrides

### Constraints

Narrow acceptable versions without adding packages as dependencies. Only apply if the package is already required:

```toml
[tool.uv]
constraint-dependencies = [
    "numpy<2",
    "scipy>=1.10,<1.14",
]
```

```bash
# CLI equivalent
uv lock --constraint 'numpy<2'
```

### Overrides

Replace declared requirements — use to work around broken upstream version bounds:

```toml
[tool.uv]
override-dependencies = [
    "numpy>=1.26",       # Force newer numpy
    "foo>1",             # Override a broken upper bound
]
```

### Scoped Overrides

Apply overrides only to specific packages:

```toml
[tool.uv]
override-dependencies = [
    { package = { name = "bar", version = "0.0.5" }, dependencies = ["foo>2"] },
]
```

### When to Use Which

| Scenario | Use |
|----------|-----|
| Restrict a transitive dep version | Constraint |
| Fix a broken upstream bound | Override |
| Force a minimum version | Override |
| Add a security floor | Constraint |

## Dependency Exclusions

Remove packages entirely from the resolution graph:

```toml
[tool.uv]
exclude-dependencies = ["unwanted-package"]
```

Scoped exclusions target specific packages:

```toml
[tool.uv]
exclude-dependencies = [
    { package = "bar", dependencies = ["foo"] },
]
```

## Multi-Platform Resolution

uv performs "universal resolution" — the lock file captures versions for all platforms simultaneously, not just the current one.

### Fork Strategy

Controls how uv handles packages with different version requirements across Python versions:

```toml
[tool.uv]
fork-strategy = "requires-python"  # Default: latest per Python version
fork-strategy = "fewest"           # Minimize version count
```

**requires-python (default)**: May include multiple versions of a package, each optimal for its Python range.

Example with numpy and `requires-python >= "3.8"`:
- numpy 1.24.4 for Python 3.8
- numpy 2.0.2 for Python 3.9
- numpy 2.2.0 for Python 3.10+

**fewest**: Prefers a single older version compatible with all supported Python versions.

### Platform Markers

Use environment markers for platform-specific dependencies:

```toml
[project]
dependencies = [
    "pywin32; sys_platform == 'win32'",
    "uvloop; sys_platform != 'win32'",
]
```

## Reproducible Resolutions

### Exclude Newer

Pin resolution to packages published before a specific date:

```toml
[tool.uv]
exclude-newer = "2026-08-17T00:00:00Z"
```

This ensures identical resolution regardless of when `uv lock` is run. Accepts RFC 3339 timestamps or local dates.

### Per-Package Cutoffs

```toml
[tool.uv]
exclude-newer-package = {
    setuptools = "2026-01-01",
    numpy = "2026-06-01",
}
```

### Dependency Cooldowns

Use friendly duration format:

```toml
[tool.uv]
exclude-newer = "1 week"
exclude-newer-package = { setuptools = "30 days" }
```

### Lock File in CI

```bash
# Verify lock file matches pyproject.toml
uv lock --check

# Use locked versions exactly
uv sync --locked
```

## Caching

### How Caching Works

uv caches aggressively to avoid redundant downloads and builds:

| Dependency Type | Cache Strategy |
|----------------|---------------|
| Registry (PyPI) | HTTP caching headers |
| Direct URLs | HTTP headers + URL matching |
| Git | Fully-resolved commit hash |
| Local files | File modification time |
| Flat indexes | Filename (assumed immutable) |

### Cache Location

Priority order:
1. `--cache-dir` flag
2. `UV_CACHE_DIR` environment variable
3. `cache-dir` in config file
4. System default: `$XDG_CACHE_HOME/uv` (Unix), `%LOCALAPPDATA%\uv\cache` (Windows)

### Cache Commands

```bash
# View cache directory
uv cache dir

# Clear all cached data
uv cache clean

# Clear cache for specific package
uv cache clean requests

# Remove unused entries
uv cache prune

# CI-optimized prune (keeps built wheels)
uv cache prune --ci
```

### Refresh Cache

Force revalidation without clearing:

```bash
# Refresh all cached dependencies
uv sync --refresh

# Refresh specific package
uv sync --refresh-package requests

# Reinstall (ignore installed versions)
uv sync --reinstall
```

### Cache Safety

- Thread-safe and append-only
- Supports concurrent reads and writes
- File-based locks protect virtual environment modifications
- Safe for parallel CI jobs sharing a cache

## Performance Tips

### 1. Keep Cache on Same Filesystem

Place the cache on the same filesystem as your Python environments. uv uses hard links by default, which are fast but require same-filesystem:

```bash
# If cache is on different filesystem, switch to copy mode
UV_LINK_MODE=copy uv sync
```

### 2. Compile Bytecode in Production

```bash
uv sync --compile-bytecode
```

Slower install, but faster Python startup. Recommended for Docker images.

### 3. Use --frozen in Development

Skip lock file verification for faster iteration:

```bash
uv run --frozen python main.py
```

### 4. CI Caching Strategy

```yaml
# GitHub Actions
- uses: astral-sh/setup-uv@v9
  with:
    enable-cache: true

# Manual cache with prune
- uses: actions/cache@v4
  with:
    path: /tmp/.uv-cache
    key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
- run: uv cache prune --ci
```

### 5. Parallel Downloads

```bash
# Increase concurrent downloads (default: 50)
UV_CONCURRENT_DOWNLOADS=100 uv sync

# Increase concurrent builds
UV_CONCURRENT_BUILDS=32 uv sync
```

### 6. No-Binary for Specific Packages

Force building from source when pre-built wheels are problematic:

```toml
[tool.uv]
no-binary-package = ["numpy"]
```

### 7. Offline Mode

Work without network access using cached packages:

```bash
UV_OFFLINE=1 uv sync --frozen
```

## Common Pitfalls

1. **Cache on different filesystem** — Hard links fail silently; uv falls back to copy but is slower
2. **--refresh vs --reinstall** — `--refresh` revalidates cache; `--reinstall` ignores installed packages
3. **exclude-newer with no timezone** — Use full RFC 3339 timestamps to avoid ambiguity
4. **Overrides vs constraints** — Overrides can break things by ignoring upstream requirements; use constraints first
5. **CI without --locked** — Without `--locked`, CI silently uses a stale lock file
