# uv — Overview

> Source: [uv documentation](https://docs.astral.sh/uv/) | GitHub: [astral-sh/uv](https://github.com/astral-sh/uv) (88.8K stars)

## What Is uv?

uv is an extremely fast Python package and project manager, written in Rust by [Astral](https://astral.sh) (the creators of Ruff). It is a single tool that replaces **pip**, **pip-tools**, **pipx**, **poetry**, **pyenv**, **twine**, and **virtualenv** — providing a unified, fast experience for the entire Python development lifecycle.

uv is 10-100x faster than pip for dependency resolution and installation.

## When to Use uv

- **New Python projects** — `uv init` sets up a complete project structure
- **Dependency management** — Add, remove, lock, and sync dependencies
- **Python version management** — Install and switch between Python versions (replaces pyenv)
- **Running scripts** — Execute scripts with automatic dependency management
- **Publishing packages** — Build and publish to PyPI
- **CI/CD pipelines** — Fast, reproducible installs in Docker and GitHub Actions
- **Tool execution** — Run Python CLI tools without global installation (replaces pipx)

## Key Features

| Feature | Description |
|---------|-------------|
| **Speed** | 10-100x faster than pip, written in Rust |
| **Universal lockfile** | Cross-platform `uv.lock` for reproducible builds |
| **Python management** | Install and manage Python versions directly |
| **Project management** | Full `pyproject.toml`-based project lifecycle |
| **Script support** | PEP 723 inline metadata for standalone scripts |
| **Tool execution** | `uvx` runs tools in isolated environments |
| **pip compatibility** | Drop-in replacement for pip commands |
| **Workspace support** | Cargo-style monorepo workspaces |
| **Global cache** | Deduplicates dependencies across projects |

## Installation

### Standalone Installer (Recommended)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Pin a specific version
curl -LsSf https://astral.sh/uv/0.12.5/install.sh | sh
```

### Package Managers

```bash
brew install uv          # Homebrew (macOS)
pip install uv           # PyPI
pipx install uv          # pipx
conda install uv         # Conda
winget install astral-sh.uv  # Windows
```

### Self-Update

```bash
uv self update           # Update to latest
uv self update 0.12.5    # Update to specific version
```

## Quick Start

### Create a New Project

```bash
uv init my-project
cd my-project
```

This creates:
```
my-project/
├── .git/
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
└── src/
    └── my_project/
        └── __init__.py
```

### Add Dependencies

```bash
uv add requests fastapi
uv add --dev pytest ruff
```

### Run Code

```bash
uv run python main.py
uv run pytest
uv run -- flask run -p 3000
```

### Run a Script with Dependencies

```python
# /// script
# dependencies = ["requests", "rich"]
# requires-python = ">=3.12"
# ///

import requests
from rich import print as rprint

resp = requests.get("https://httpbin.org/json")
rprint(resp.json())
```

```bash
uv run script.py
```

### Install and Use Python Versions

```bash
uv python install 3.12 3.13
uv python pin 3.12
uv python list
```

### Run CLI Tools

```bash
uvx ruff check .
uvx black --check .
uvx httpie GET https://httpbin.org/json
```

## Architecture

uv operates around a few core concepts:

1. **Projects** — Defined by `pyproject.toml`, managed with `uv init/add/remove/sync/lock/run`
2. **Virtual environments** — Automatically created in `.venv/`, never needs manual activation
3. **Lock files** — `uv.lock` captures exact resolved versions for reproducibility
4. **Cache** — Global cache deduplicates packages across all projects
5. **Python discovery** — Managed Python installations + system Python discovery

### Command Categories

```
# Project management
uv init / add / remove / sync / lock / run / tree / build / publish

# Python version management
uv python install / list / find / pin / uninstall / upgrade

# Tool management
uvx (alias: uv tool run) / uv tool install / list / uninstall / upgrade

# pip-compatible interface
uv pip install / uninstall / freeze / compile / sync
uv venv

# Utility
uv cache clean / prune
uv self update
uv version
```

## Comparison with Other Tools

| Feature | uv | pip + venv | Poetry | PDM |
|---------|----|-----------:|-------:|----:|
| Speed | Fastest (Rust) | Slow | Moderate | Moderate |
| Python management | Built-in | No | No | No |
| Lock file | Universal | No | poetry.lock | pdm.lock |
| Tool execution | `uvx` | No | No | No |
| Workspace support | Yes | No | No | Yes |
| pip compatibility | Full | N/A | No | Partial |
| pyproject.toml | Native | Partial | Native | Native |

## Common Pitfalls

1. **Don't edit `uv.lock` manually** — It's managed by uv and will be overwritten
2. **Use `uv run` instead of activating venvs** — uv handles environments automatically
3. **Add `.venv/` to `.gitignore`** — Virtual environments should not be committed
4. **Use `--locked` in CI** — Ensures the lock file is up-to-date and fails if not
5. **Use `uv sync` not `uv pip install`** — The project interface is preferred for project work
