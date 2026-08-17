# uv — Integrations

> Source: [Docker](https://docs.astral.sh/uv/guides/integration/docker/) | [GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/)

## Table of Contents

- [Docker](#docker)
- [GitHub Actions](#github-actions)
- [GitLab CI/CD](#gitlab-cicd)
- [Pre-commit](#pre-commit)
- [FastAPI](#fastapi)
- [PyTorch](#pytorch)

## Docker

### Installing uv in Docker

The recommended approach copies uv from the official distroless image:

```dockerfile
FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
```

Pin to a specific version for reproducible builds:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/
```

### Basic Project Installation

```dockerfile
FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

WORKDIR /app
COPY . /app

ENV UV_NO_DEV=1
RUN uv sync --locked

CMD ["uv", "run", "my_app"]
```

Add `.venv` to `.dockerignore` to exclude local virtual environments.

### Optimized Multi-Layer Build

Separate dependency installation from project code for better layer caching:

```dockerfile
FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

WORKDIR /app

# Install dependencies (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"
CMD ["my_app"]
```

### Production Multi-Stage Build

Minimize final image size by separating build and runtime stages:

```dockerfile
# Build stage
FROM python:3.12-slim-trixie AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

# Runtime stage (no uv needed)
FROM python:3.12-slim-trixie
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
CMD ["my_app"]
```

### Docker Best Practices

```dockerfile
# Compile bytecode for faster startup
ENV UV_COMPILE_BYTECODE=1

# Use copy mode (required for multi-stage)
ENV UV_LINK_MODE=copy

# Disable Python downloads (use base image Python)
ENV UV_PYTHON_DOWNLOADS=0
```

### Docker Compose Watch

Hot-reload for development:

```yaml
services:
  app:
    build: .
    develop:
      watch:
        - action: sync
          path: .
          target: /app
          ignore:
            - .venv/
        - action: rebuild
          path: ./pyproject.toml
```

```bash
docker compose watch
```

### Using the pip Interface in Docker

For simpler images without project management:

```dockerfile
FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

ENV UV_SYSTEM_PYTHON=1
RUN uv pip install --system -r requirements.txt
```

### Available Docker Images

Pre-built images at `ghcr.io/astral-sh/uv`:

| Image | Description |
|-------|-------------|
| `ghcr.io/astral-sh/uv:latest` | Distroless (binary only, for COPY --from) |
| `ghcr.io/astral-sh/uv:debian` | Debian-based with uv |
| `ghcr.io/astral-sh/uv:alpine` | Alpine-based with uv |
| `ghcr.io/astral-sh/uv:python3.12` | Debian + Python 3.12 + uv |
| `ghcr.io/astral-sh/uv:python3.12-alpine` | Alpine + Python 3.12 + uv |

Pin versions: `ghcr.io/astral-sh/uv:0.12.5-python3.12`

## GitHub Actions

### Official Setup Action

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v9
        with:
          version: "0.12.5"
          enable-cache: true

      - run: uv python install

      - run: uv sync --locked --all-extras --dev

      - run: uv run pytest tests/
```

### Matrix Testing (Multiple Python Versions)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v9
        with:
          version: "0.12.5"
          python-version: ${{ matrix.python-version }}
          enable-cache: true

      - run: uv sync --locked --dev

      - run: uv run pytest tests/
```

### Lint + Type Check + Test

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v9
        with:
          version: "0.12.5"
      - run: uvx ruff check .
      - run: uvx ruff format --check .

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v9
        with:
          version: "0.12.5"
      - run: uv sync --locked --dev
      - run: uv run mypy src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v9
        with:
          version: "0.12.5"
          enable-cache: true
      - run: uv sync --locked --dev
      - run: uv run pytest tests/ --cov
```

### Manual Cache Configuration

```yaml
env:
  UV_CACHE_DIR: /tmp/.uv-cache

steps:
  - uses: actions/cache@v4
    with:
      path: /tmp/.uv-cache
      key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
      restore-keys: |
        uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
        uv-${{ runner.os }}

  - run: uv sync --locked
  - run: uv cache prune --ci
```

### Private Repository Dependencies

```yaml
steps:
  - run: echo "${{ secrets.MY_PAT }}" | gh auth login --with-token
  - run: gh auth setup-git
  - run: uv sync --locked
```

## GitLab CI/CD

```yaml
image: ghcr.io/astral-sh/uv:python3.12

variables:
  UV_CACHE_DIR: .uv-cache

cache:
  key: uv-$CI_COMMIT_REF_SLUG
  paths:
    - .uv-cache

test:
  script:
    - uv sync --locked --dev
    - uv run pytest tests/
  after_script:
    - uv cache prune --ci
```

## Pre-commit

Use uv with pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Or run pre-commit itself via uv:

```bash
uvx pre-commit run --all-files
uvx pre-commit install
```

## FastAPI

### Project Setup

```bash
uv init my-api
cd my-api
uv add fastapi 'uvicorn[standard]'
```

### Development Server

```bash
uv run -- uvicorn app.main:app --reload --port 8000
```

### Dockerfile for FastAPI

```dockerfile
FROM python:3.12-slim-trixie AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM python:3.12-slim-trixie
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## PyTorch

PyTorch requires a custom index for CPU/GPU variants:

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

For GPU (CUDA):

```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu121"
explicit = true
```

Platform-specific (CPU for macOS, GPU for Linux):

```toml
[tool.uv.sources]
torch = [
    { index = "pytorch-cpu", marker = "sys_platform == 'darwin'" },
    { index = "pytorch-gpu", marker = "sys_platform == 'linux'" },
]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[[tool.uv.index]]
name = "pytorch-gpu"
url = "https://download.pytorch.org/whl/cu121"
explicit = true
```

## Common Pitfalls

1. **Docker: forgetting `.venv` in `.dockerignore`** — Local venvs get copied into the image
2. **Docker: missing `UV_LINK_MODE=copy`** — Hard links don't work across Docker layers
3. **GitHub Actions: not pinning uv version** — Can cause unexpected CI failures
4. **Not using `--locked` in CI** — Allows stale lock files to pass silently
5. **PyTorch: wrong index URL** — CPU vs GPU indexes must match your deployment target
