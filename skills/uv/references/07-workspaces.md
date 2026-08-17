# uv — Workspaces

> Source: [Workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)

## Table of Contents

- [Overview](#overview)
- [Creating a Workspace](#creating-a-workspace)
- [Workspace Layout](#workspace-layout)
- [Configuration](#configuration)
- [Member Dependencies](#member-dependencies)
- [Running Commands](#running-commands)
- [Shared Lock File](#shared-lock-file)
- [When to Use Workspaces](#when-to-use-workspaces)
- [Alternative: Path Dependencies](#alternative-path-dependencies)

## Overview

A workspace is a collection of one or more packages (called workspace members) managed together in a single repository. Inspired by Cargo workspaces, uv workspaces provide:

- **Shared lock file** — All members resolve dependencies together
- **Unified commands** — `uv lock` and `uv sync` operate on the entire workspace
- **Cross-member references** — Members can depend on each other
- **Consistent environments** — Single virtual environment at the workspace root

## Creating a Workspace

### Initialize the Root

```bash
mkdir my-workspace && cd my-workspace
uv init
```

### Add Workspace Configuration

Edit `pyproject.toml` to declare workspace members:

```toml
[project]
name = "my-workspace"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv.workspace]
members = ["packages/*"]
```

### Add Members

```bash
# Create workspace member packages
uv init packages/core
uv init --lib packages/utils
uv init packages/api
```

## Workspace Layout

Typical workspace structure:

```
my-workspace/
├── pyproject.toml          # Root: workspace configuration
├── uv.lock                 # Shared lock file
├── .venv/                  # Shared virtual environment
├── packages/
│   ├── core/
│   │   ├── pyproject.toml  # Member: own dependencies
│   │   └── src/
│   │       └── core/
│   │           └── __init__.py
│   ├── utils/
│   │   ├── pyproject.toml
│   │   └── src/
│   │       └── utils/
│   │           └── __init__.py
│   └── api/
│       ├── pyproject.toml
│       └── src/
│           └── api/
│               └── __init__.py
└── README.md
```

## Configuration

### Root pyproject.toml

```toml
[project]
name = "my-workspace"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv.workspace]
members = [
    "packages/*",          # Glob pattern (most common)
    "libs/shared-utils",   # Explicit path
]
exclude = [
    "packages/deprecated", # Exclude specific directories
    "packages/experimental/*",
]
```

### Requirements

- The `members` key is **mandatory** and accepts glob patterns
- The `exclude` key is optional
- Every included directory must contain a `pyproject.toml`
- Each workspace has exactly one root
- The root is also a workspace member

### Workspace-Level Sources

Sources defined at the root apply to all members:

```toml
# Root pyproject.toml
[tool.uv.sources]
# These apply to all workspace members unless overridden
shared-config = { path = "./config", editable = true }
```

Members can override workspace-level sources in their own `pyproject.toml`.

## Member Dependencies

### Depending on Other Members

Members reference each other using `workspace = true` in sources:

```toml
# packages/api/pyproject.toml
[project]
name = "api"
version = "0.1.0"
dependencies = ["core", "utils"]

[tool.uv.sources]
core = { workspace = true }
utils = { workspace = true }
```

### Editable by Default

Workspace member dependencies are installed in editable mode by default. Changes to member source code are immediately available to dependents without reinstallation.

### External Workspace References

Reference packages from external workspaces:

```toml
[tool.uv.sources]
external-lib = { workspace = "../other-workspace" }
```

### Virtual Dependencies

Install transitive dependencies without installing the package itself:

```toml
[tool.uv.sources]
data-models = { path = "../data-models", package = false }
```

## Running Commands

### Default: Workspace Root

```bash
# Run from workspace root (operates on root package)
uv run python -c "import core; print(core.__version__)"
uv sync
uv lock
```

### Target Specific Members

```bash
# Run commands in a specific member's context
uv run --package api python -m api.server
uv run --package core pytest tests/

# Sync only a specific member's deps
uv sync --package api

# Build a specific member
uv build --package utils
```

The `--package` flag works from any directory within the workspace.

### Running from Member Directories

```bash
cd packages/api
uv run pytest         # Still operates in workspace context
```

## Shared Lock File

All workspace members share a single `uv.lock` at the workspace root:

- `uv lock` resolves dependencies for **all members** simultaneously
- Ensures consistent dependency versions across the entire workspace
- A package used by multiple members gets the same version everywhere
- The lock file captures the union of all member requirements

```bash
# Lock the entire workspace
uv lock

# Check lock file is up-to-date
uv lock --check

# Upgrade a package across the workspace
uv lock --upgrade-package requests
```

### requires-python Intersection

The workspace uses the **intersection** of all members' `requires-python` constraints:

```toml
# packages/core: requires-python = ">=3.10"
# packages/api:  requires-python = ">=3.12"
# Workspace resolves for: >=3.12 (intersection)
```

## When to Use Workspaces

### Good Use Cases

- **Multiple interconnected packages** in one repository
- **Libraries with extensions** (e.g., Rust/C++ via maturin/scikit-build)
- **Plugin systems** where core and plugins share dependencies
- **Microservices** that share common libraries
- **Enforcing separation of concerns** between components

### When NOT to Use Workspaces

- **Conflicting dependency requirements** — All members must be compatible
- **Separate virtual environments needed** — Workspaces share one environment
- **Different Python version requirements** — Workspace takes the intersection
- **Independent release cycles** — Consider separate repositories instead

## Alternative: Path Dependencies

For scenarios requiring more independence than workspaces provide:

```toml
# Instead of workspace = true, use explicit paths
[tool.uv.sources]
shared-utils = { path = "../shared-utils" }
shared-utils = { path = "../shared-utils", editable = true }
```

### Tradeoffs

| Feature | Workspace | Path Dependencies |
|---------|-----------|-------------------|
| Shared lock file | Yes | No |
| `--package` flag | Yes | No |
| Independent envs | No | Yes |
| Conflicting deps | Not supported | Supported |
| Different Python versions | Not supported | Supported |
| `uv run` from root | Yes | Per-package only |

## Common Pitfalls

1. **Members can import undeclared dependencies** — uv doesn't enforce that members only use their declared deps; they may accidentally use deps from other members
2. **requires-python intersection** — If one member needs >=3.12 and another >=3.10, the workspace resolves for >=3.12
3. **All members share one .venv** — You can't have different environments for different members
4. **Missing pyproject.toml** — Every directory matched by `members` glob must contain a `pyproject.toml`
5. **Root is always a member** — The root `pyproject.toml` participates in dependency resolution even if it has no code
