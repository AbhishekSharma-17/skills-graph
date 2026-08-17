---
name: uv
description: "Extremely fast Python package and project manager written in Rust, replacing pip, pip-tools, pipx, poetry, pyenv, twine, and virtualenv. MANDATORY TRIGGERS: uv, astral uv, uv python, uv sync, uv lock, uv add, uv run, uvx, uv pip, uv init, uv build, uv publish, uv tool, python package manager rust. Also trigger when the user wants to manage Python projects, install Python versions, run scripts with inline dependencies, manage virtual environments, publish to PyPI, or migrate from pip/poetry/pipenv. When in doubt about whether to use this skill for Python packaging or project management tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["python", "uv", "package-manager", "astral", "rust", "pip", "virtualenv", "pyproject"]
---

# uv — Extremely Fast Python Package & Project Manager

> Source: [uv documentation](https://docs.astral.sh/uv/) | PyPI: `uv` | v0.12.x

## Reference Files

| # | File | Read When |
|---|------|-----------|
| 00 | [Overview](references/00-overview.md) | Understanding what uv is, installation, quick start, architecture |
| 01 | [Projects](references/01-projects.md) | Creating projects with uv init, project structure, pyproject.toml |
| 02 | [Dependencies](references/02-dependencies.md) | Adding, removing, managing dependencies, sources, extras, dev groups |
| 03 | [Locking & Syncing](references/03-lockfile-sync.md) | Lock files, uv sync, resolution strategies, exporting |
| 04 | [Scripts](references/04-scripts.md) | Running scripts, inline metadata (PEP 723), shebang, uv run |
| 05 | [Python Versions](references/05-python-versions.md) | Installing, listing, pinning, managing Python versions |
| 06 | [Tools](references/06-tools.md) | uvx, uv tool run/install, tool environments, managing CLI tools |
| 07 | [Workspaces](references/07-workspaces.md) | Monorepo management, workspace members, shared lockfiles |
| 08 | [Pip Interface](references/08-pip-interface.md) | Drop-in pip replacement, uv pip install/compile/sync, migration |
| 09 | [Publishing](references/09-publishing.md) | Building packages, publishing to PyPI, trusted publishing |
| 10 | [Configuration](references/10-configuration.md) | uv.toml, pyproject.toml settings, environment variables |
| 11 | [Resolution & Caching](references/11-resolution-caching.md) | Resolution strategies, caching, performance, reproducibility |
| 12 | [Integrations](references/12-integrations.md) | Docker, GitHub Actions, CI/CD, pre-commit, FastAPI |

## Installation

```bash
# Standalone (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh          # macOS / Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Via package managers
brew install uv               # Homebrew
pip install uv                # PyPI
pipx install uv               # pipx

# Self-update
uv self update
```

## Quick Reference

- Docs: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
- PyPI: https://pypi.org/project/uv/
- Changelog: https://github.com/astral-sh/uv/blob/main/CHANGELOG.md
