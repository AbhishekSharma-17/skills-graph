# uv — Dependencies

> Source: [Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/)

## Table of Contents

- [Adding Dependencies](#adding-dependencies)
- [Removing Dependencies](#removing-dependencies)
- [Updating Dependencies](#updating-dependencies)
- [Dependency Sources](#dependency-sources)
- [Optional Dependencies (Extras)](#optional-dependencies-extras)
- [Development Dependencies](#development-dependencies)
- [Dependency Groups](#dependency-groups)
- [Platform-Specific Dependencies](#platform-specific-dependencies)
- [Dependency Specifiers](#dependency-specifiers)

## Adding Dependencies

```bash
# Add a package (latest compatible version)
uv add requests

# Add with version constraint
uv add "requests>=2.31"
uv add "requests>=2.31,<3"

# Add multiple packages
uv add requests httpx fastapi

# Import from requirements.txt
uv add -r requirements.txt

# Import with constraints
uv add -r requirements.txt -c constraints.txt
```

This updates `pyproject.toml` and regenerates `uv.lock`:

```toml
[project]
dependencies = [
    "httpx>=0.27.2",
    "requests>=2.31",
]
```

## Removing Dependencies

```bash
# Remove a package
uv remove requests

# Remove from dev dependencies
uv remove --dev pytest

# Remove from a specific group
uv remove --group lint ruff

# Remove from optional dependencies
uv remove --optional network httpx
```

## Updating Dependencies

```bash
# Change version constraint (re-add with new constraint)
uv add "requests>2.30,<2.33"

# Force upgrade to latest within constraints
uv lock --upgrade-package requests

# Upgrade all packages
uv lock --upgrade

# Upgrade and sync in one step
uv sync --upgrade-package requests
```

## Dependency Sources

The `[tool.uv.sources]` table specifies where to find packages beyond PyPI.

### Git Dependencies

```bash
# From HTTPS
uv add git+https://github.com/encode/httpx

# From SSH
uv add git+ssh://[email protected]/encode/httpx

# Specific tag
uv add git+https://github.com/encode/httpx --tag 0.27.0

# Specific branch
uv add git+https://github.com/encode/httpx --branch main

# Specific commit
uv add git+https://github.com/encode/httpx --rev abc123

# Subdirectory of a repo
uv add "git+https://github.com/org/monorepo#subdirectory=libs/mylib"
```

Resulting pyproject.toml:

```toml
[tool.uv.sources]
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.0" }
```

### Local Path Dependencies

```bash
# Wheel file
uv add /path/to/package-0.1.0-py3-none-any.whl

# Local directory
uv add ~/projects/my-library/

# Editable install (for active development)
uv add --editable ../my-library/
```

```toml
[tool.uv.sources]
my-library = { path = "../my-library", editable = true }
```

### URL Dependencies

```bash
uv add "https://files.pythonhosted.org/packages/.../httpx-0.27.0.tar.gz"
```

### Custom Index Dependencies

```bash
uv add torch --index pytorch=https://download.pytorch.org/whl/cpu
```

```toml
[tool.uv.sources]
torch = { index = "pytorch" }

[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

### Workspace Member Dependencies

```toml
[tool.uv.sources]
shared-utils = { workspace = true }
```

## Optional Dependencies (Extras)

Optional dependencies let consumers install only what they need:

```bash
# Add to an optional group
uv add httpx --optional network
uv add matplotlib --optional plot
```

```toml
[project.optional-dependencies]
network = ["httpx>=0.27.0"]
plot = ["matplotlib>=3.6.3"]
excel = ["openpyxl>=3.1.0", "xlrd>=2.0.1"]
```

Consumers install with:

```bash
uv add "my-package[network,plot]"
# or: pip install "my-package[network,plot]"
```

Include optional groups during development:

```bash
uv sync --extra network --extra plot
uv sync --all-extras
```

## Development Dependencies

Dev dependencies are local-only — excluded from published packages.

```bash
# Add to default dev group
uv add --dev pytest
uv add --dev ruff mypy

# Uses the dependency-groups standard
```

```toml
[dependency-groups]
dev = [
    "pytest>=8.1.1",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]
```

### Sync Options for Dev Dependencies

```bash
uv sync                 # Includes dev group by default
uv sync --no-dev        # Exclude all dev dependencies
uv sync --no-group dev  # Exclude specific group
```

## Dependency Groups

Organize dependencies into logical groups (PEP 735):

```bash
# Add to named groups
uv add --group lint ruff mypy
uv add --group test pytest pytest-cov
uv add --group docs sphinx
```

```toml
[dependency-groups]
dev = [
    { include-group = "lint" },
    { include-group = "test" },
]
lint = ["ruff>=0.8.0", "mypy>=1.13.0"]
test = ["pytest>=8.0", "pytest-cov>=5.0"]
docs = ["sphinx>=7.0"]
```

### Nested Groups

Groups can include other groups:

```toml
[dependency-groups]
dev = [
    { include-group = "lint" },
    { include-group = "test" },
    "ipython>=8.0",
]
```

### Default Groups

Control which groups sync by default:

```toml
[tool.uv]
default-groups = ["dev", "lint"]    # Specific groups
default-groups = "all"              # All groups
```

### Sync with Groups

```bash
uv sync --group test              # Include test group
uv sync --all-groups              # Include all groups
uv sync --only-group test         # Only test group (no project deps)
uv sync --no-group lint           # Exclude lint group
uv sync --no-default-groups       # Exclude all default groups
```

### Python Version Requirements for Groups

Restrict a group to specific Python versions:

```toml
[tool.uv.dependency-groups]
dev = { requires-python = ">=3.12" }
```

## Platform-Specific Dependencies

Use environment markers (PEP 508) to restrict dependencies by platform:

```bash
uv add "jax; sys_platform == 'linux'"
uv add "numpy; python_version >= '3.11'"
uv add "pywin32; sys_platform == 'win32'"
```

```toml
[project]
dependencies = [
    "jax; sys_platform == 'linux'",
    "numpy; python_version >= '3.11'",
    "pywin32; sys_platform == 'win32'",
]
```

Platform-specific sources:

```toml
[tool.uv.sources]
torch = [
    { index = "pytorch-cpu", marker = "sys_platform != 'linux'" },
    { index = "pytorch-gpu", marker = "sys_platform == 'linux'" },
]
```

## Dependency Specifiers

Standard PEP 508 version syntax:

| Syntax | Meaning |
|--------|---------|
| `foo>=1.2.3` | Minimum version |
| `foo>=1.2,<2` | Version range |
| `foo!=1.4.0` | Exclude specific version |
| `foo~=1.2` | Compatible release (>=1.2, <2.0) |
| `foo==2.1.*` | Wildcard match |
| `foo==2` | Exact version (matches 2.0.0) |
| `foo[extra1,extra2]` | With extras |
| `foo; python_version<'3.10'` | Environment marker |

### Controlling Version Bounds

```bash
# Default: lower bound only (>=)
uv add requests          # "requests>=2.32.3"

# Exact constraint
uv add "requests==2.32.3"

# Compatible release
uv add "requests~=2.32"

# Bounded range
uv add "requests>=2.31,<3"
```

## Disabling Sources

To verify your package works without custom sources:

```bash
uv lock --no-sources      # Ignore tool.uv.sources during resolution
uv build --no-sources     # Build without custom sources
```

## Common Pitfalls

1. **Don't mix `uv add` with manual edits carelessly** — `uv add` regenerates the lock file; manual edits to dependencies in `pyproject.toml` require `uv lock` afterward
2. **Editable installs are for development only** — Use `uv add --no-editable` for production path dependencies
3. **Index dependencies need `explicit = true`** — Otherwise all packages query that index
4. **`--dev` targets the `dev` group** — Use `--group <name>` for other groups
