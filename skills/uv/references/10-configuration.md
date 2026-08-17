# uv — Configuration

> Source: [Configuration](https://docs.astral.sh/uv/concepts/config/) | [Settings reference](https://docs.astral.sh/uv/reference/settings/)

## Table of Contents

- [Configuration Files](#configuration-files)
- [Precedence Order](#precedence-order)
- [pyproject.toml Settings](#pyprojecttoml-settings)
- [uv.toml Settings](#uvtoml-settings)
- [Environment Variables](#environment-variables)
- [Common Configuration Patterns](#common-configuration-patterns)

## Configuration Files

uv reads configuration from two file types:

### pyproject.toml

Project-level configuration under `[tool.uv]`:

```toml
[tool.uv]
python-preference = "managed"
dev-dependencies = []
default-groups = ["dev"]
```

### uv.toml

Standalone configuration file (same options, without the `[tool.uv]` prefix):

```toml
# uv.toml
python-preference = "managed"
python-downloads = "automatic"
```

### Where uv Looks for Config

1. Project `pyproject.toml` or `uv.toml` (in project directory)
2. User-level `uv.toml` (in `~/.config/uv/uv.toml` or platform equivalent)
3. System-level `uv.toml`

## Precedence Order

From highest to lowest priority:

1. **CLI flags** — `--python 3.12`, `--no-dev`, etc.
2. **Environment variables** — `UV_PYTHON=3.12`, `UV_NO_DEV=1`
3. **Project config** — `pyproject.toml` `[tool.uv]` or local `uv.toml`
4. **User config** — `~/.config/uv/uv.toml`
5. **Defaults** — Built-in defaults

## pyproject.toml Settings

### Project Management

```toml
[tool.uv]
# Default dependency groups to install
default-groups = ["dev"]
# default-groups = "all"  # Install all groups

# Legacy dev dependencies (prefer dependency-groups)
dev-dependencies = ["pytest>=8.0"]

# Python version preference
python-preference = "managed"
# Options: "managed", "only-managed", "system", "only-system"

# Automatic Python downloads
python-downloads = "automatic"
# Options: "automatic", "manual"
```

### Resolution Settings

```toml
[tool.uv]
# Resolution mode
resolution = "highest"
# Options: "highest" (default), "lowest", "lowest-direct"

# Pre-release handling
prerelease = "if-necessary"
# Options: "if-necessary" (default), "allow", "disallow"

# Per-package pre-release
prerelease-package = { torch = "allow" }

# Constraint dependencies
constraint-dependencies = ["numpy<2"]

# Override upstream requirements
override-dependencies = ["numpy>=1.26"]

# Exclude packages from resolution
exclude-dependencies = ["unwanted-package"]

# Pin resolution to a date
exclude-newer = "2026-08-17T00:00:00Z"

# Per-package date pinning
exclude-newer-package = { setuptools = "2026-01-01" }

# Fork strategy for multi-platform resolution
fork-strategy = "requires-python"
# Options: "requires-python" (default), "fewest"
```

### Index Configuration

```toml
# Package indexes
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true  # Only used for packages explicitly mapped to this index

[[tool.uv.index]]
name = "private"
url = "https://private.example.com/simple/"
authenticate = "always"

# Index strategy
[tool.uv]
index-strategy = "first-index"
# Options: "first-index" (default), "unsafe-first-match", "unsafe-best-match"
```

### Dependency Sources

```toml
[tool.uv.sources]
# Git source
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.0" }

# Local path (editable)
my-lib = { path = "../my-lib", editable = true }

# Workspace member
shared = { workspace = true }

# Custom index
torch = { index = "pytorch" }

# Platform-specific
torch = [
    { index = "pytorch-cpu", marker = "sys_platform != 'linux'" },
    { index = "pytorch-gpu", marker = "sys_platform == 'linux'" },
]
```

### Workspace Configuration

```toml
[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/deprecated"]
```

### Build Configuration

```toml
[tool.uv]
# Compile bytecode during install
compile-bytecode = false

# Link mode for installations
link-mode = "hardlink"
# Options: "hardlink" (default), "copy", "symlink"

# No binary distributions (build from source)
no-binary-package = ["numpy"]

# No source distributions (binary only)
no-build-package = ["tensorflow"]
```

### Dependency Group Settings

```toml
[tool.uv.dependency-groups]
dev = { requires-python = ">=3.12" }
```

## uv.toml Settings

Same options as `[tool.uv]` but in standalone format:

```toml
# ~/.config/uv/uv.toml (user-level defaults)

python-preference = "managed"
python-downloads = "automatic"
compile-bytecode = false
link-mode = "hardlink"

# Default index
[[index]]
name = "company-pypi"
url = "https://pypi.company.com/simple/"
```

## Environment Variables

### Core Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_PYTHON` | Default Python version | `3.12` |
| `UV_PYTHON_PREFERENCE` | Python discovery preference | `managed` |
| `UV_PYTHON_DOWNLOADS` | Auto-download behavior | `manual` |
| `UV_CACHE_DIR` | Cache directory location | `/tmp/uv-cache` |
| `UV_LINK_MODE` | Installation link mode | `copy` |
| `UV_COMPILE_BYTECODE` | Pre-compile .pyc | `1` |

### Project Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_PROJECT_ENVIRONMENT` | Custom venv path | `.venv-custom` |
| `UV_NO_DEV` | Exclude dev deps | `1` |
| `UV_FROZEN` | Skip lock checks | `1` |
| `UV_LOCKED` | Fail if lock stale | `1` |
| `UV_SYSTEM_PYTHON` | Use system Python | `1` |

### Index Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_INDEX_URL` | Default index URL | `https://pypi.org/simple/` |
| `UV_EXTRA_INDEX_URL` | Additional index | `https://custom.pypi.org/simple/` |
| `UV_INDEX_STRATEGY` | Resolution strategy | `first-index` |
| `UV_INDEX_<NAME>_USERNAME` | Index authentication | `myuser` |
| `UV_INDEX_<NAME>_PASSWORD` | Index authentication | `mytoken` |

### Publishing Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_PUBLISH_TOKEN` | PyPI API token | `pypi-AgEI...` |
| `UV_PUBLISH_USERNAME` | PyPI username | `__token__` |
| `UV_PUBLISH_PASSWORD` | PyPI password | `pypi-AgEI...` |
| `UV_PUBLISH_URL` | Custom publish URL | `https://upload.pypi.org/legacy/` |
| `UV_PUBLISH_NO_ATTESTATIONS` | Disable attestations | `1` |

### Network Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_HTTP_TIMEOUT` | HTTP timeout seconds | `30` |
| `UV_CONCURRENT_DOWNLOADS` | Max parallel downloads | `50` |
| `UV_CONCURRENT_BUILDS` | Max parallel builds | `16` |
| `UV_CONCURRENT_INSTALLS` | Max parallel installs | `8` |
| `ALL_PROXY` / `HTTPS_PROXY` | Proxy settings | `http://proxy:8080` |

### Misc Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_NO_PROGRESS` | Disable progress bars | `1` |
| `UV_NO_COLOR` | Disable color output | `1` |
| `UV_NATIVE_TLS` | Use system TLS | `1` |
| `VIRTUAL_ENV` | Active virtual env | `.venv` |

## Common Configuration Patterns

### Production Docker

```toml
[tool.uv]
compile-bytecode = true
link-mode = "copy"
python-downloads = "manual"
```

### CI/CD

```bash
UV_FROZEN=1 UV_NO_PROGRESS=1 uv sync --no-dev
```

### Private Registry

```toml
[[tool.uv.index]]
name = "company"
url = "https://pypi.company.com/simple/"
authenticate = "always"
```

```bash
export UV_INDEX_COMPANY_USERNAME="deploy"
export UV_INDEX_COMPANY_PASSWORD="$DEPLOY_TOKEN"
```

### Reproducible Builds

```toml
[tool.uv]
exclude-newer = "2026-08-17T00:00:00Z"
```

### Offline Development

```bash
UV_OFFLINE=1 uv sync --frozen
```
