# uv — Projects

> Source: [Projects guide](https://docs.astral.sh/uv/guides/projects/) | [Project concepts](https://docs.astral.sh/uv/concepts/projects/)

## Table of Contents

- [Creating Projects](#creating-projects)
- [Project Structure](#project-structure)
- [pyproject.toml Anatomy](#pyprojecttoml-anatomy)
- [Packaged vs Application Projects](#packaged-vs-application-projects)
- [Running Commands](#running-commands)
- [Version Management](#version-management)
- [Virtual Environment](#virtual-environment)
- [Project Commands Reference](#project-commands-reference)

## Creating Projects

### Basic Initialization

```bash
# Create a new project in a new directory
uv init my-project
cd my-project

# Initialize in the current directory
uv init

# Initialize with a specific Python version
uv init --python 3.12

# Create a library (packaged) project
uv init --lib my-library

# Create an application project (default)
uv init --app my-app

# Create with a specific build backend
uv init --build-backend hatch
uv init --build-backend setuptools
uv init --build-backend flit
uv init --build-backend maturin    # for Rust extensions
uv init --build-backend scikit-build  # for C/C++ extensions
```

### What Gets Generated

```
my-project/
├── .git/                  # Git repository initialized
├── .gitignore             # Includes .venv/, __pycache__/, etc.
├── .python-version        # Pinned Python version (e.g., "3.12")
├── pyproject.toml         # Project metadata and dependencies
├── README.md              # Empty README
└── src/
    └── my_project/
        └── __init__.py    # Package entry point
```

## Project Structure

### Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, tool configuration |
| `uv.lock` | Resolved dependency lock file (auto-generated) |
| `.python-version` | Default Python version for the project |
| `.venv/` | Virtual environment (auto-created, not committed) |

### .python-version

Specifies the Python version used to create the virtual environment:

```bash
# Pin a version
uv python pin 3.12

# Pin globally (user-level default)
uv python pin --global 3.13
```

The file contains a single version string like `3.12` and is respected by other tools like pyenv.

### uv.lock

- Human-readable TOML format with exact resolved versions
- Cross-platform — captures resolution for all platforms simultaneously
- **Must be committed** to version control for reproducible installs
- Never edit manually — managed entirely by `uv lock`

## pyproject.toml Anatomy

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My awesome project"
readme = "README.md"
license = "MIT"
requires-python = ">=3.12"
authors = [
    { name = "Your Name", email = "you@example.com" }
]
dependencies = [
    "fastapi>=0.115.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
my-cli = "my_project.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.8.0"]
test = ["pytest>=8.0", "pytest-cov>=5.0"]
lint = ["ruff>=0.8.0", "mypy>=1.13"]

[tool.uv]
dev-dependencies = []  # Legacy format, prefer dependency-groups
default-groups = ["dev"]

[tool.uv.sources]
# Custom dependency sources (git, path, index, workspace)
```

### requires-python

Controls which Python versions your project supports. uv uses this to:
- Select the Python version for the virtual environment
- Resolve dependencies compatible across all specified versions
- Generate a universal lock file

```toml
requires-python = ">=3.10"          # Python 3.10+
requires-python = ">=3.10,<3.13"    # Python 3.10-3.12
```

## Packaged vs Application Projects

### Application (Default)

```bash
uv init my-app          # or uv init --app my-app
```

- Not intended for publishing to PyPI
- Has a `src/` layout but no build system by default
- Use for web apps, scripts, services

### Library (Packaged)

```bash
uv init --lib my-library
```

- Intended for publishing to PyPI
- Includes a `[build-system]` table
- Installed into the virtual environment in editable mode
- Use for reusable Python packages

## Running Commands

### uv run

Executes commands within the project environment. Automatically:
1. Creates `.venv/` if it doesn't exist
2. Verifies `uv.lock` is up-to-date
3. Syncs the environment with the lock file
4. Runs the command

```bash
# Run a Python script
uv run python main.py

# Run a module
uv run -m pytest

# Run an installed script
uv run flask run -p 3000

# Pass arguments (use -- to separate uv args from command args)
uv run -- python -c "print('hello')"

# Run with extra dependencies not in the project
uv run --with rich python script.py

# Run without syncing (faster, uses existing env)
uv run --frozen python main.py
```

### Manual Environment Activation

If you prefer traditional activation:

```bash
uv sync                          # Ensure environment is up-to-date
source .venv/bin/activate         # macOS / Linux
.venv\Scripts\activate            # Windows
python main.py                    # Now use python directly
```

## Version Management

```bash
# View current version
uv version                    # my-project 0.1.0
uv version --short            # 0.1.0
uv version --output-format json

# Set version
uv version 1.0.0
uv version 1.0.0 --dry-run    # Preview without changing

# Bump version
uv version --bump major       # 0.1.0 → 1.0.0
uv version --bump minor       # 0.1.0 → 0.2.0
uv version --bump patch       # 0.1.0 → 0.1.1
uv version --bump alpha       # 0.1.0 → 0.1.1a1
uv version --bump rc          # 0.1.0 → 0.1.1rc1

# Bump without triggering lock/sync
uv version --bump patch --frozen
```

## Virtual Environment

uv automatically creates and manages a `.venv/` directory in the project root:

- Created automatically on first `uv run` or `uv sync`
- Uses the Python version from `.python-version` or `requires-python`
- Never needs manual activation when using `uv run`
- Add `.venv/` to `.gitignore` (done by default with `uv init`)

```bash
# View environment info
uv run python --version
uv run python -c "import sys; print(sys.prefix)"
```

## Project Commands Reference

| Command | Purpose |
|---------|---------|
| `uv init` | Create a new project |
| `uv add <pkg>` | Add a dependency |
| `uv remove <pkg>` | Remove a dependency |
| `uv sync` | Sync environment with lock file |
| `uv lock` | Update the lock file |
| `uv run <cmd>` | Run a command in the project environment |
| `uv tree` | Display dependency tree |
| `uv build` | Build source and wheel distributions |
| `uv publish` | Publish to a package index |
| `uv version` | View or set the project version |
| `uv export` | Export lock file to other formats |

### Useful Flags

| Flag | Purpose |
|------|---------|
| `--locked` | Fail if lock file is out of date (CI) |
| `--frozen` | Skip lock file update checks |
| `--no-dev` | Exclude development dependencies |
| `--all-extras` | Include all optional dependency groups |
| `--group <name>` | Target a specific dependency group |
| `--package <name>` | Target a specific workspace package |
