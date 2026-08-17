# uv — Tools

> Source: [Tool concepts](https://docs.astral.sh/uv/concepts/tools/) | [Using tools guide](https://docs.astral.sh/uv/guides/tools/)

## Table of Contents

- [Overview](#overview)
- [Running Tools (uvx)](#running-tools-uvx)
- [Installing Tools](#installing-tools)
- [Managing Installed Tools](#managing-installed-tools)
- [Version Management](#version-management)
- [Extra Dependencies](#extra-dependencies)
- [Python Version Control](#python-version-control)
- [uvx vs uv run](#uvx-vs-uv-run)

## Overview

uv provides two ways to run Python CLI tools:

1. **`uvx` / `uv tool run`** — Run tools in temporary, cached environments (like `npx`)
2. **`uv tool install`** — Install tools permanently with executables on PATH

`uvx` is an exact alias for `uv tool run` — the two commands are interchangeable.

## Running Tools (uvx)

Run any Python CLI tool without installing it globally:

```bash
# Run a tool (latest version)
uvx ruff check .
uvx black --check .
uvx mypy src/
uvx httpie GET https://httpbin.org/json

# Run with full command
uv tool run ruff check .

# Run from a package with a different command name
uvx --from 'httpie' http GET https://httpbin.org/json

# Run a specific version
uvx ruff@0.6.0 check .

# Force latest version (bypass cache)
uvx ruff@latest check .

# Run with version constraint
uvx 'ruff>=0.5,<0.7' check .
```

### Cached Environments

- First invocation downloads and caches the tool environment
- Subsequent runs reuse the cached environment (fast)
- Cached environments are stored in uv's cache directory
- Cleared with `uv cache clean`

### When the Package Name Differs from the Command

Some packages provide commands with different names:

```bash
# Package is 'httpie', command is 'http'
uvx --from httpie http GET https://example.com

# Package is 'jupyter', command is 'jupyter'
uvx --from jupyter jupyter notebook

# Package is 'aws-cli-v2', command is 'aws'
uvx --from aws-cli-v2 aws s3 ls
```

## Installing Tools

Install tools permanently so their executables are always on PATH:

```bash
# Install a tool
uv tool install ruff
uv tool install black

# Install a specific version
uv tool install ruff==0.5.0

# Install with extras
uv tool install 'mkdocs[material]'

# Install from a URL
uv tool install git+https://github.com/astral-sh/ruff

# Reinstall (force)
uv tool install --reinstall ruff
```

### What Happens

- Creates a dedicated virtual environment for the tool
- Links executables to `~/.local/bin/` (or platform equivalent)
- Environment persists until explicitly uninstalled
- Tool environments are isolated — tools can't interfere with each other

### PATH Setup

After first installation, you may need to add the bin directory to PATH:

```bash
# Add to shell profile (one-time setup)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

## Managing Installed Tools

```bash
# List installed tools with versions
uv tool list

# Show executables provided by installed tools
uv tool list --show-paths

# Uninstall a tool
uv tool uninstall ruff

# Uninstall all tools
uv tool uninstall --all

# Upgrade a tool to latest
uv tool upgrade ruff

# Upgrade all installed tools
uv tool upgrade --all

# Upgrade specific dependency within a tool
uv tool upgrade black --upgrade-package click

# Reinstall all packages in a tool environment
uv tool upgrade black --reinstall

# Show tool installation directory
uv tool dir
```

## Version Management

### Default Behavior

- **uvx**: Uses latest version on first run, then cached version thereafter
- **uv tool install**: Installs the version specified (or latest) and pins it

### Specifying Versions

```bash
# Exact version
uvx ruff@0.6.0 check .
uv tool install ruff==0.6.0

# Version range
uvx 'ruff>=0.5,<0.7' check .

# Latest (bypass cache)
uvx ruff@latest check .
```

### Upgrading

```bash
# Upgrade a specific tool
uv tool upgrade ruff

# Upgrade all tools
uv tool upgrade --all

# Upgrade while respecting original constraints
uv tool upgrade black   # If installed with ==0.24.*, stays within that range
```

## Extra Dependencies

### --with (Add Dependencies)

Include additional packages in the tool's environment:

```bash
# Add a plugin/extension
uvx --with mkdocs-material mkdocs serve
uv tool install mkdocs --with mkdocs-material --with mkdocs-minify-plugin

# Add a specific version
uvx --with 'click>=8.0' my-tool
```

### --with-executables-from

Include packages AND expose their executables:

```bash
uv tool install --with-executables-from package1,package2 main-tool
```

This is different from `--with`, which only adds packages as dependencies without exposing their CLI commands.

## Python Version Control

### Setting the Python Version for Tools

```bash
# Run with specific Python
uvx --python 3.11 ruff check .

# Install with specific Python
uv tool install --python 3.12 ruff
```

### Python Version Persistence

Installed tools are tied to their Python version. If that Python version is uninstalled, the tool environment breaks and needs to be reinstalled:

```bash
# Reinstall after Python version change
uv tool install --reinstall ruff
```

## uvx vs uv run

| Feature | `uvx` / `uv tool run` | `uv run` |
|---------|----------------------|----------|
| **Purpose** | Run CLI tools | Run project commands/scripts |
| **Isolation** | Always isolated from project | Uses project environment |
| **Caching** | Cached tool environments | Project .venv |
| **Dependencies** | Tool's own deps only | Project + specified deps |
| **Version default** | Latest, then cached | From project lock file |
| **Best for** | Linters, formatters, CLI tools | Project scripts, tests |

### When to Use Which

```bash
# Use uvx for standalone tools
uvx ruff check .
uvx black --check .
uvx httpie GET https://api.example.com

# Use uv run for project-related commands
uv run pytest
uv run python main.py
uv run flask run
```

## Common Patterns

### Linting and Formatting

```bash
uvx ruff check . --fix
uvx ruff format .
uvx black .
uvx isort .
uvx mypy src/
uvx pyright src/
```

### Documentation

```bash
uvx --with mkdocs-material mkdocs serve
uvx sphinx-build docs/ docs/_build
uvx pdoc --html my_package
```

### Code Generation

```bash
uvx cookiecutter gh:audreyfeldroy/cookiecutter-pypackage
uvx copier copy gh:org/template my-project
```

### Database Tools

```bash
uvx pgcli postgresql://user:pass@localhost/db
uvx litecli my_database.db
uvx sqlfluff lint queries/
```

## Common Pitfalls

1. **Tool environments are not meant for direct modification** — Don't activate or pip install into them
2. **Cached uvx environments are disposable** — `uv cache clean` removes them; use `uv tool install` for persistence
3. **Python version dependency** — If you uninstall a Python version, tools using it break
4. **Package vs command name** — Use `--from` when the PyPI package name differs from the CLI command name
