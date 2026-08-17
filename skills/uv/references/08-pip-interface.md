# uv — Pip Interface

> Source: [The pip interface](https://docs.astral.sh/uv/pip/)

## Table of Contents

- [Overview](#overview)
- [Virtual Environments](#virtual-environments)
- [Installing Packages](#installing-packages)
- [Uninstalling Packages](#uninstalling-packages)
- [Inspecting Environments](#inspecting-environments)
- [Compiling Requirements](#compiling-requirements)
- [Syncing Environments](#syncing-environments)
- [System Installs](#system-installs)
- [Migration from pip](#migration-from-pip)

## Overview

uv provides a drop-in replacement for `pip`, `pip-tools`, and `virtualenv` commands. These are **low-level commands** for users not yet ready to adopt uv's project-based workflow.

Key distinction: uv does not invoke pip internally. The pip interface is a reimplementation that's 10-100x faster, with some behavioral differences documented in the pip-compatibility guide.

### When to Use the Pip Interface

- Legacy projects without `pyproject.toml`
- Simple scripts that don't need full project management
- CI/CD pipelines using `requirements.txt`
- Gradual migration from pip to uv projects

### When to Use Projects Instead

- New projects (use `uv init` + `uv add`)
- Projects with `pyproject.toml` (use `uv sync` + `uv run`)
- Anything that benefits from lock files and reproducibility

## Virtual Environments

### Creating Environments

```bash
# Create in default location (.venv)
uv venv

# Create in custom location
uv venv my-env

# Create with specific Python version
uv venv --python 3.12
uv venv --python pypy

# Create with system site-packages access
uv venv --system-site-packages

# Create with seed packages (pip, setuptools)
uv venv --seed
```

### Activating Environments

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (cmd)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Deactivate
deactivate
```

### Using Without Activation

uv commands automatically detect the `.venv` in the current directory. You can also specify explicitly:

```bash
UV_VIRTUAL_ENV=.venv uv pip install requests
uv pip install --python .venv/bin/python requests
```

## Installing Packages

```bash
# Install a package
uv pip install requests

# Install with version constraint
uv pip install 'requests>=2.31,<3'

# Install multiple packages
uv pip install requests httpx fastapi

# Install from requirements file
uv pip install -r requirements.txt

# Install with constraints
uv pip install -r requirements.txt -c constraints.txt

# Install with extras
uv pip install 'fastapi[standard]'

# Install from URL
uv pip install 'https://files.pythonhosted.org/.../package.tar.gz'

# Install from git
uv pip install 'git+https://github.com/encode/httpx'

# Install in editable mode
uv pip install -e .
uv pip install -e ./packages/my-lib

# Force reinstall
uv pip install --reinstall requests

# Install with no dependencies
uv pip install --no-deps requests

# Install with specific index
uv pip install --index-url https://custom.pypi.org/simple/ my-package
uv pip install --extra-index-url https://custom.pypi.org/simple/ my-package

# Compile bytecode during install
uv pip install --compile-bytecode requests
```

### Key Flags

| Flag | Purpose |
|------|---------|
| `-r <file>` | Install from requirements file |
| `-c <file>` | Apply constraints file |
| `-e <path>` | Editable install |
| `--reinstall` | Force reinstall |
| `--no-deps` | Skip dependency installation |
| `--index-url` | Override default index |
| `--extra-index-url` | Add additional index |
| `--upgrade` | Allow upgrades |
| `--compile-bytecode` | Pre-compile .pyc files |

## Uninstalling Packages

```bash
# Uninstall a package
uv pip uninstall requests

# Uninstall multiple
uv pip uninstall requests httpx

# Uninstall from requirements file
uv pip uninstall -r requirements.txt
```

## Inspecting Environments

```bash
# List installed packages (pip freeze format)
uv pip freeze

# List with versions
uv pip list

# Show package details
uv pip show requests

# Show dependency tree
uv pip tree

# Check for dependency conflicts
uv pip check
```

## Compiling Requirements

`uv pip compile` replaces `pip-compile` from pip-tools — it resolves a set of requirements into a locked requirements file:

```bash
# Compile from pyproject.toml
uv pip compile pyproject.toml -o requirements.txt

# Compile from requirements.in
uv pip compile requirements.in -o requirements.txt

# Compile from stdin
echo 'requests>=2.31' | uv pip compile - -o requirements.txt

# Compile with constraints
uv pip compile requirements.in -c constraints.txt -o requirements.txt

# Include hashes for security
uv pip compile --generate-hashes requirements.in -o requirements.txt

# Upgrade all packages
uv pip compile --upgrade requirements.in -o requirements.txt

# Upgrade specific package
uv pip compile --upgrade-package requests requirements.in -o requirements.txt

# Use specific Python version for resolution
uv pip compile --python-version 3.11 requirements.in -o requirements.txt

# Include annotations (which source requested each package)
uv pip compile --annotation-style line requirements.in -o requirements.txt

# Resolution strategies
uv pip compile --resolution lowest requirements.in -o requirements.txt
```

## Syncing Environments

`uv pip sync` replaces `pip-sync` from pip-tools — it synchronizes the environment with a requirements file, removing extra packages:

```bash
# Sync environment with requirements
uv pip sync requirements.txt

# Sync from multiple files
uv pip sync requirements.txt dev-requirements.txt

# Dry run
uv pip sync --dry-run requirements.txt

# Force reinstall everything
uv pip sync --reinstall requirements.txt
```

Key difference from `uv pip install`: sync **removes** packages not listed in the requirements file, ensuring the environment exactly matches the specification.

## System Installs

Install packages into the system Python (outside a virtual environment):

```bash
# Explicit system flag
uv pip install --system requests

# Or set environment variable
UV_SYSTEM_PYTHON=1 uv pip install requests
```

Useful in Docker containers and CI where virtual environments are unnecessary:

```dockerfile
ENV UV_SYSTEM_PYTHON=1
RUN uv pip install -r requirements.txt
```

## Migration from pip

### Command Mapping

| pip / pip-tools | uv equivalent |
|----------------|---------------|
| `pip install pkg` | `uv pip install pkg` |
| `pip install -r req.txt` | `uv pip install -r req.txt` |
| `pip install -e .` | `uv pip install -e .` |
| `pip uninstall pkg` | `uv pip uninstall pkg` |
| `pip freeze` | `uv pip freeze` |
| `pip list` | `uv pip list` |
| `pip show pkg` | `uv pip show pkg` |
| `pip-compile req.in` | `uv pip compile req.in` |
| `pip-sync req.txt` | `uv pip sync req.txt` |
| `python -m venv .venv` | `uv venv` |
| `virtualenv .venv` | `uv venv` |

### Key Behavioral Differences

1. **Strict resolution** — uv fails on conflicting requirements instead of silently installing an incompatible version
2. **No implicit upgrades** — Use `--upgrade` or `--upgrade-package` explicitly
3. **Hash verification** — uv strictly enforces hashes when present
4. **Editable installs** — uv uses a different mechanism (`.pth` files) that's more reliable
5. **Universal resolution** — uv considers all platforms by default, not just the current one

### Migrating to the Project Interface

The recommended migration path is from `uv pip` to `uv` project commands:

```bash
# Instead of:
uv pip install -r requirements.txt

# Use:
uv init                    # One-time: create pyproject.toml
uv add requests httpx      # Add dependencies
uv sync                    # Install everything
uv run python main.py      # Run with automatic env management
```

## Common Pitfalls

1. **No auto-activation** — Unlike `uv run`, the pip interface requires an active virtual environment
2. **`uv pip sync` removes extra packages** — It's not additive like `uv pip install`
3. **System installs need explicit flag** — `uv pip install` fails outside a venv unless `--system` is used
4. **Different default resolution** — uv resolves differently than pip in edge cases (stricter by default)
