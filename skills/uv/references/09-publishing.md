# uv — Publishing

> Source: [Publishing packages](https://docs.astral.sh/uv/guides/package/)

## Table of Contents

- [Building Packages](#building-packages)
- [Build Backends](#build-backends)
- [Publishing to PyPI](#publishing-to-pypi)
- [Authentication](#authentication)
- [Trusted Publishing](#trusted-publishing)
- [Custom Indexes](#custom-indexes)
- [Version Management](#version-management)
- [Attestations](#attestations)
- [Testing Published Packages](#testing-published-packages)

## Building Packages

`uv build` creates source distributions (sdist) and binary distributions (wheels):

```bash
# Build the current project
uv build

# Build a specific source
uv build path/to/project

# Build a specific workspace member
uv build --package my-library

# Build only source distribution
uv build --sdist

# Build only wheel
uv build --wheel

# Build without custom sources (verify publishability)
uv build --no-sources

# Output to custom directory
uv build --out-dir dist/
```

Output:

```
dist/
├── my_package-0.1.0-py3-none-any.whl
└── my_package-0.1.0.tar.gz
```

### Pre-Build Verification

Always run `uv build --no-sources` before publishing to verify your package builds correctly without `[tool.uv.sources]` overrides:

```bash
uv build --no-sources
```

This simulates what happens when someone installs your package from PyPI (where custom sources are not available).

## Build Backends

uv supports multiple build backends. Specify in `pyproject.toml`:

### Hatchling (Default)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Setuptools

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"
```

### Flit

```toml
[build-system]
requires = ["flit_core>=3.4"]
build-backend = "flit_core.buildapi"
```

### Maturin (Rust Extensions)

```toml
[build-system]
requires = ["maturin>=1.0"]
build-backend = "maturin"
```

### scikit-build (C/C++ Extensions)

```toml
[build-system]
requires = ["scikit-build-core>=0.10"]
build-backend = "scikit_build_core.build"
```

### uv's Own Build Backend

```bash
uv init --build-backend uv
```

```toml
[build-system]
requires = ["uv>=0.12,<0.13"]
build-backend = "uv"
```

## Publishing to PyPI

```bash
# Publish to PyPI
uv publish

# Publish specific files
uv publish dist/my_package-0.1.0.tar.gz dist/my_package-0.1.0-py3-none-any.whl

# Publish from custom directory
uv publish dist/*

# Dry run
uv publish --dry-run
```

### Typical Workflow

```bash
# 1. Bump version
uv version --bump patch

# 2. Build
uv build

# 3. Verify build
uv build --no-sources

# 4. Publish
uv publish
```

## Authentication

### Token-Based (Recommended)

```bash
# Via flag
uv publish --token pypi-AgEIcH...

# Via environment variable
UV_PUBLISH_TOKEN=pypi-AgEIcH... uv publish
```

### Username/Password

```bash
# Via flags
uv publish --username __token__ --password pypi-AgEIcH...

# Via environment variables
UV_PUBLISH_USERNAME=__token__
UV_PUBLISH_PASSWORD=pypi-AgEIcH...
uv publish
```

### Keyring Integration

uv can read credentials from the system keyring:

```bash
uv publish --keyring-provider subprocess
```

## Trusted Publishing

For GitHub Actions, use trusted publishing (no credentials needed):

### Setup

1. Go to your PyPI project settings
2. Add a "trusted publisher" with your GitHub repository details
3. Configure the GitHub Actions workflow:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v9
        with:
          version: "0.12.5"
      - run: uv build

      # Optional: smoke test
      - run: uv run --with ./dist/*.whl --no-project -- python -c "import my_package"

      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: release
    permissions:
      id-token: write  # Required for trusted publishing
      attestations: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - uses: astral-sh/setup-uv@v9
        with:
          version: "0.12.5"

      - run: uv publish dist/*
```

## Custom Indexes

Publish to private registries or TestPyPI:

### TestPyPI

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
explicit = true
```

```bash
uv publish --index testpypi
```

### Private Registry

```toml
[[tool.uv.index]]
name = "private"
url = "https://private.example.com/simple/"
publish-url = "https://private.example.com/upload/"
```

```bash
uv publish --index private --token <token>
```

## Version Management

uv provides built-in version management:

```bash
# View current version
uv version                        # my-package 0.1.0
uv version --short                # 0.1.0

# Set exact version
uv version 1.0.0

# Preview changes
uv version 2.0.0 --dry-run

# Bump semantically
uv version --bump major           # 0.1.0 → 1.0.0
uv version --bump minor           # 0.1.0 → 0.2.0
uv version --bump patch           # 0.1.0 → 0.1.1
uv version --bump stable          # 1.0.0a1 → 1.0.0

# Pre-release bumps
uv version --bump alpha           # 0.1.0 → 0.1.1a1
uv version --bump beta            # 0.1.0 → 0.1.1b1
uv version --bump rc              # 0.1.0 → 0.1.1rc1

# Bump without triggering lock/sync
uv version --bump patch --frozen
```

## Attestations

uv automatically handles PEP 740 attestations:

```bash
# Publish with attestations (default)
uv publish

# Skip attestations (if registry doesn't support them)
uv publish --no-attestations
```

Attestations provide cryptographic proof of build provenance, linking published packages to their source repository.

## Testing Published Packages

After publishing, verify the package installs correctly:

```bash
# Test installation from PyPI
uv run --with my-package --no-project -- python -c "import my_package; print(my_package.__version__)"

# Force re-download (bypass cache)
uv run --refresh-package my-package --with my-package --no-project -- python -c "import my_package"

# Test from TestPyPI
uv run --index-url https://test.pypi.org/simple/ --with my-package --no-project -- python -c "import my_package"
```

## Common Pitfalls

1. **Forgetting `--no-sources` during build** — Custom sources won't be available to consumers installing from PyPI
2. **Missing `[build-system]`** — Required for publishable packages; `uv init --lib` includes it automatically
3. **Version not bumped** — PyPI rejects re-uploads of the same version
4. **Attestation errors** — Use `--no-attestations` if your registry doesn't support PEP 740
5. **TestPyPI dependencies** — TestPyPI may not have all your dependencies; use `--extra-index-url` to fall back to PyPI
