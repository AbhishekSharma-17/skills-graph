# uv — Python Versions

> Source: [Python versions](https://docs.astral.sh/uv/concepts/python-versions/)

## Table of Contents

- [Installing Python](#installing-python)
- [Listing Versions](#listing-versions)
- [Finding Versions](#finding-versions)
- [Pinning Versions](#pinning-versions)
- [Upgrading Versions](#upgrading-versions)
- [Version Request Formats](#version-request-formats)
- [Supported Implementations](#supported-implementations)
- [Special Variants](#special-variants)
- [Discovery Order](#discovery-order)
- [Configuration](#configuration)

## Installing Python

uv bundles downloadable CPython and PyPy distributions. By default, versions are downloaded automatically as needed, but explicit installation is also supported:

```bash
# Install a specific version
uv python install 3.12
uv python install 3.12.3

# Install multiple versions
uv python install 3.10 3.11 3.12 3.13

# Install with version constraint
uv python install '>=3.11,<3.13'

# Install a specific implementation
uv python install pypy
uv python install pypy@3.10

# Install latest stable
uv python install

# Install and make default (adds python/python3 to PATH)
uv python install --default 3.12

# Uninstall a managed version
uv python uninstall 3.10
uv python uninstall --all
```

### Installation Directory

Python executables are installed to `~/.local/bin/` (Unix) or `%APPDATA%\Python\` (Windows) by default. Version-specific executables like `python3.12` are always added; generic `python` and `python3` require `--default`.

## Listing Versions

```bash
# Show installed and available versions
uv python list

# Filter by version
uv python list 3.13

# Filter by implementation
uv python list pypy

# Show all patch versions (not just latest)
uv python list --all-versions

# Show only installed versions
uv python list --only-installed

# Show only downloads (not installed)
uv python list --only-downloads
```

Output format shows installation status, version, path, and source:

```
cpython-3.13.2-macos-aarch64-none    /Users/user/.local/share/uv/python/...
cpython-3.12.9-macos-aarch64-none    <download available>
```

## Finding Versions

Locate a specific Python executable:

```bash
# Find first available Python
uv python find

# Find with version constraint
uv python find '>=3.11'
uv python find 3.12

# Find system Python only (not managed)
uv python find --system

# Find managed Python only
uv python find --managed
```

Returns the full path to the Python executable.

## Pinning Versions

Create a `.python-version` file to set the default for a project:

```bash
# Pin for the current project
uv python pin 3.12

# Pin globally (user-level default)
uv python pin --global 3.13

# Pin to a specific patch version
uv python pin 3.12.3
```

The `.python-version` file:
- Contains a single version string (e.g., `3.12`)
- Is read by uv, pyenv, and other tools
- Should be committed to version control
- Is created automatically by `uv init`

## Upgrading Versions

Upgrade managed Python installations to the latest patch release:

```bash
# Upgrade a specific version
uv python upgrade 3.12    # 3.12.3 → 3.12.5

# Upgrade all installed versions
uv python upgrade
```

Upgrades are:
- Only supported for uv-managed versions (not system Python)
- Only across patch versions (3.12.x → 3.12.y), not minor versions
- Virtual environments automatically adopt new patch versions

## Version Request Formats

uv accepts many formats for specifying Python versions:

| Format | Example | Meaning |
|--------|---------|---------|
| Major | `3` | Latest Python 3.x |
| Major.Minor | `3.12` | Latest Python 3.12.x |
| Major.Minor.Patch | `3.12.3` | Exact version |
| Version range | `>=3.12,<3.14` | Version constraint |
| Variant shortcut | `3.13t` | Free-threaded 3.13 |
| Debug shortcut | `3.12.0d` | Debug build |
| Explicit variant | `3.13+freethreaded` | Free-threaded (explicit) |
| Implementation | `cpython` | Latest CPython |
| Impl + version | `cpython@3.12` | CPython 3.12 |
| Impl + version | `pypy3.11` | PyPy for Python 3.11 |
| Path | `/usr/bin/python3` | Specific executable |

## Supported Implementations

| Implementation | Aliases | Notes |
|---------------|---------|-------|
| CPython | `cpython`, `cp` | Default, most common |
| PyPy | `pypy`, `pp` | JIT-compiled, up to Python 3.11 |
| GraalPy | `graalpy`, `gp` | GraalVM-based |
| Pyodide | `pyodide` | WebAssembly/Emscripten port |

Implementation names are case-insensitive.

## Special Variants

### Free-Threaded Python (3.13+)

Python without the GIL (Global Interpreter Lock):

```bash
# Install free-threaded build
uv python install 3.13t
uv python install 3.13+freethreaded

# Use in a project
uv run --python 3.13t script.py
```

For Python 3.13, free-threaded builds must be explicitly requested. Python 3.14+ allows automatic selection but prefers GIL-enabled builds.

### Debug Builds

Python compiled with debug symbols and assertions:

```bash
uv python install 3.13d
uv python install 3.13+debug
```

Debug builds are only selected when explicitly requested or when no stable build matches.

### Pre-release Versions

```bash
# Install pre-release Python
uv python install 3.14

# Pre-releases activate only when:
# - No stable version matches the request
# - The version is explicitly specified
```

## Discovery Order

When searching for a Python interpreter, uv checks:

1. **Managed Python** — Installed by uv in `UV_PYTHON_INSTALL_DIR`
2. **PATH entries** — `python`, `python3`, `python3.x` on Unix; `python.exe` on Windows
3. **Windows-specific** — Registry entries, Microsoft Store, `py` launcher

Virtual environment interpreters take precedence when detected.

### Project Resolution

For projects, uv uses this priority:
1. `.python-version` file in project directory
2. `requires-python` in `pyproject.toml`
3. First compatible version found via discovery

## Configuration

### Automatic Downloads

Control whether uv downloads Python automatically:

```toml
# In pyproject.toml or uv.toml
[tool.uv]
python-downloads = "automatic"   # Default: download as needed
python-downloads = "manual"      # Only via uv python install
```

```bash
# Environment variable
UV_PYTHON_DOWNLOADS=manual uv run script.py
```

### Python Preference

Control preference between managed and system Python:

```toml
[tool.uv]
python-preference = "managed"       # Default: prefer managed, use system as fallback
python-preference = "only-managed"  # Never use system Python
python-preference = "system"        # Prefer system over managed
python-preference = "only-system"   # Never use managed Python
```

```bash
# CLI flags
uv run --managed-python script.py
uv run --no-managed-python script.py
```

### Custom Install Directory

```bash
UV_PYTHON_INSTALL_DIR=/opt/python uv python install 3.12
```

## Common Pitfalls

1. **System Python vs managed** — uv prefers its own managed Python by default; use `python-preference` to change
2. **Free-threaded requires explicit request** — `uv python install 3.13` installs the GIL-enabled version
3. **Upgrade is patch-only** — `uv python upgrade 3.12` goes from 3.12.3 to 3.12.5, not to 3.13
4. **pyenv shims can interfere** — If using pyenv alongside uv, set `python-preference = "managed"` to avoid conflicts
5. **Virtual env Python tracking** — Envs track the minor version; patch upgrades are adopted automatically
