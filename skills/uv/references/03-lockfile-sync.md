# uv — Locking & Syncing

> Source: [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/lock/) | [Exporting](https://docs.astral.sh/uv/concepts/projects/export/)

## Table of Contents

- [Lock File Basics](#lock-file-basics)
- [uv lock](#uv-lock)
- [uv sync](#uv-sync)
- [Upgrade Strategies](#upgrade-strategies)
- [Resolution Modes](#resolution-modes)
- [Exporting](#exporting)
- [CI/CD Best Practices](#cicd-best-practices)

## Lock File Basics

`uv.lock` is a cross-platform lock file that captures the exact resolved versions of all dependencies. It is:

- **Human-readable** — TOML format, can be inspected and diffed
- **Universal** — Resolves for all platforms simultaneously, not just the current one
- **Deterministic** — Same inputs always produce the same output
- **Auto-managed** — Created and updated by `uv lock`, never edit manually

### When Is the Lock File Updated?

The lock file is refreshed automatically when:
- Running `uv lock` explicitly
- Running `uv sync` (if the lock file is stale)
- Running `uv run` (if the lock file is stale)
- Running `uv add` or `uv remove`

## uv lock

Creates or updates the lock file based on `pyproject.toml`:

```bash
# Create/update lock file
uv lock

# Check if lock file is up-to-date (exit 1 if not)
uv lock --check

# Upgrade all packages to latest compatible versions
uv lock --upgrade

# Upgrade specific packages
uv lock --upgrade-package requests
uv lock --upgrade-package requests --upgrade-package httpx

# Dry run — show what would change
uv lock --dry-run

# Skip dependency source overrides
uv lock --no-sources
```

### Key Flags

| Flag | Purpose |
|------|---------|
| `--check` | Verify lock file is up-to-date without modifying |
| `--upgrade` | Upgrade all packages to latest versions |
| `--upgrade-package <pkg>` | Upgrade specific package |
| `--dry-run` | Show changes without applying |
| `--no-sources` | Ignore `[tool.uv.sources]` |
| `--python <ver>` | Use specific Python version for resolution |

## uv sync

Installs dependencies from the lock file into the virtual environment:

```bash
# Sync all dependencies (including dev)
uv sync

# Sync without dev dependencies (production)
uv sync --no-dev

# Sync with specific extras
uv sync --extra network --extra plot

# Sync all extras
uv sync --all-extras

# Sync with specific groups
uv sync --group test
uv sync --all-groups

# Fail if lock file is out of date (for CI)
uv sync --locked

# Skip lock file check (fastest, trusts existing lock)
uv sync --frozen

# Include only specific groups, no project deps
uv sync --only-group test

# Compile bytecode for faster startup
uv sync --compile-bytecode

# Don't install the project itself
uv sync --no-install-project

# Don't install workspace members
uv sync --no-install-workspace

# Target a specific workspace package
uv sync --package my-library
```

### Key Flags

| Flag | Purpose |
|------|---------|
| `--locked` | Fail if lock file is stale (CI) |
| `--frozen` | Skip lock file verification (fastest) |
| `--no-dev` | Exclude dev dependencies |
| `--all-extras` | Include all optional dependency groups |
| `--all-groups` | Include all dependency groups |
| `--group <name>` | Include a specific group |
| `--no-install-project` | Skip installing the project itself |
| `--compile-bytecode` | Pre-compile .pyc files |

## Upgrade Strategies

### Upgrade All

```bash
uv lock --upgrade
uv sync  # Apply upgrades
```

### Upgrade Specific Packages

```bash
uv lock --upgrade-package requests
uv lock --upgrade-package "requests>=2.32"  # With constraint
```

### Pin a Package Version

```bash
uv add "requests==2.31.0"  # Pin to exact version
```

### View Dependency Tree

```bash
uv tree                    # Full dependency tree
uv tree --depth 1          # First level only
uv tree --invert           # Show reverse dependencies
uv tree --package requests # Show tree for specific package
```

## Resolution Modes

Control how uv selects versions during resolution:

```bash
# Latest (default) — newest compatible versions
uv lock

# Lowest — minimum acceptable versions (for testing lower bounds)
uv lock --resolution lowest

# Lowest-Direct — minimum for direct deps, latest for transitive
uv lock --resolution lowest-direct
```

### Configuration

```toml
[tool.uv]
resolution = "lowest"  # or "lowest-direct"
```

### Pre-release Handling

```bash
# Allow pre-releases for all packages
uv lock --prerelease allow

# Allow for specific packages
uv lock --prerelease-package torch=allow
```

```toml
[tool.uv]
prerelease = "if-necessary"  # default
prerelease-package = { torch = "allow" }
```

### Constraints and Overrides

Constraints narrow versions without adding dependencies:

```toml
[tool.uv]
constraint-dependencies = ["numpy<2"]
```

Overrides replace declared requirements (fix broken upstream bounds):

```toml
[tool.uv]
override-dependencies = ["numpy>=1.26"]
```

### Dependency Exclusions

Remove packages from the resolution entirely:

```toml
[tool.uv]
exclude-dependencies = ["unwanted-package"]
```

## Exporting

Export the lock file to other formats:

### requirements.txt

```bash
# Print to stdout
uv export --format requirements.txt

# Write to file
uv export --format requirements.txt --output-file requirements.txt

# Without hashes
uv export --format requirements.txt --no-hashes

# Production only (no dev)
uv export --format requirements.txt --no-dev

# With specific extras
uv export --format requirements.txt --extra network
```

### pylock.toml (PEP 751)

```bash
uv export --format pylock.toml
uv export --format pylock.toml --output-file pylock.toml
```

### CycloneDX SBOM

```bash
uv export --format cyclonedx1.5
uv export --format cyclonedx1.5 --output-file sbom.json
```

## CI/CD Best Practices

### Use --locked in CI

Always use `--locked` to ensure the committed lock file matches `pyproject.toml`:

```bash
uv sync --locked          # Fails if lock file is stale
uv sync --locked --no-dev # Production install
```

### Reproducible Resolutions

Pin resolution to a date to avoid new releases breaking builds:

```toml
[tool.uv]
exclude-newer = "2026-08-17T00:00:00Z"
```

### Check Lock File in PRs

```bash
uv lock --check  # Exit code 1 if lock file needs updating
```

## Common Pitfalls

1. **`--locked` vs `--frozen`** — `--locked` fails if the lock is stale (CI safety); `--frozen` skips the check entirely (speed)
2. **Forgetting to commit `uv.lock`** — The lock file must be in version control for reproducibility
3. **Using `uv sync` without `--no-dev` in production** — Dev dependencies add attack surface
4. **Not running `uv lock` after editing `pyproject.toml`** — Manual edits don't auto-update the lock
