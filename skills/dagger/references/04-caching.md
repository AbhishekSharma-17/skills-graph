# Dagger Caching

> Source: https://docs.dagger.io/features/caching | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Layer Caching](#layer-caching)
- [Volume Caching](#volume-caching)
- [Function Call Caching](#function-call-caching)
- [Cache Volumes by Package Manager](#cache-volumes-by-package-manager)
- [Cache Invalidation](#cache-invalidation)
- [Dagger Cloud Cache](#dagger-cloud-cache)
- [Performance Tips](#performance-tips)
- [Common Pitfalls](#common-pitfalls)

## Overview

Dagger aggressively caches everything by default, using content-addressed storage. This means that if the inputs to an operation haven't changed, the cached result is reused automatically. There are three main caching mechanisms:

1. **Layer caching**: Caches container build steps and API call results
2. **Volume caching**: Persists filesystem data across executions
3. **Function call caching**: Caches return values from module function calls

## Layer Caching

Dagger automatically caches the step-wise instructions and arguments that go into building a container image, including the result of each step. This is analogous to Docker layer caching but managed by the Dagger Engine.

### How It Works

```python
@function
async def build(self, source: dagger.Directory) -> dagger.Container:
    return (
        dag.container()
        .from_("python:3.12-slim")              # Layer 1: cached
        .with_exec(["apt-get", "update"])        # Layer 2: cached if Layer 1 unchanged
        .with_exec(["apt-get", "install", "-y", "gcc"])  # Layer 3: cached if Layer 2 unchanged
        .with_directory("/app", source)          # Layer 4: invalidated if source changes
        .with_exec(["pip", "install", "-r", "requirements.txt"])  # Layer 5: re-runs if Layer 4 changed
    )
```

### Optimization: Order Matters

Place infrequently changing operations first:

```python
# GOOD: Dependencies before source code
@function
async def build(self, source: dagger.Directory) -> dagger.Container:
    return (
        dag.container()
        .from_("node:20")
        # Copy only package files first (changes rarely)
        .with_file("/app/package.json", source.file("package.json"))
        .with_file("/app/package-lock.json", source.file("package-lock.json"))
        .with_workdir("/app")
        .with_exec(["npm", "ci"])  # Cached until package files change
        # Copy source code last (changes frequently)
        .with_directory("/app/src", source.directory("src"))
        .with_exec(["npm", "run", "build"])
    )
```

```python
# BAD: Source code before dependencies
@function
async def build(self, source: dagger.Directory) -> dagger.Container:
    return (
        dag.container()
        .from_("node:20")
        .with_directory("/app", source)  # Any source change invalidates everything below
        .with_workdir("/app")
        .with_exec(["npm", "ci"])  # Re-runs even if dependencies didn't change
        .with_exec(["npm", "run", "build"])
    )
```

## Volume Caching

Cache volumes persist filesystem contents across Dagger Engine sessions. They are especially useful for package manager caches where dependencies are locked to specific versions.

### Creating Cache Volumes

```python
@function
async def build(self, source: dagger.Directory) -> dagger.Container:
    pip_cache = dag.cache_volume("pip-cache")
    apt_cache = dag.cache_volume("apt-cache")

    return (
        dag.container()
        .from_("python:3.12-slim")
        .with_mounted_cache("/var/cache/apt/archives", apt_cache)
        .with_exec(["apt-get", "update"])
        .with_exec(["apt-get", "install", "-y", "gcc"])
        .with_mounted_cache("/root/.cache/pip", pip_cache)
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exec(["pip", "install", "-r", "requirements.txt"])
    )
```

### Cache Volume Behavior
- Named by a string key (e.g., `"pip-cache"`)
- Persisted on the Dagger Engine host
- Shared across function executions using the same key
- Content survives Engine restarts
- Not content-addressed — always mounted as-is

## Function Call Caching

When a Dagger Function is called with the same arguments, the Engine can return the cached result without re-executing the function. This applies to both your own functions and dependency functions.

```python
# If source hasn't changed, the second call returns cached result
result1 = await self.build(source)  # Executes
result2 = await self.build(source)  # Returns cached result
```

## Cache Volumes by Package Manager

### Python (pip/uv)

```python
pip_cache = dag.cache_volume("pip-cache")
ctr = (
    dag.container()
    .from_("python:3.12")
    .with_mounted_cache("/root/.cache/pip", pip_cache)
    .with_exec(["pip", "install", "-r", "requirements.txt"])
)
```

### Node.js (npm/pnpm/yarn)

```python
npm_cache = dag.cache_volume("npm-cache")
node_modules = dag.cache_volume("node-modules")
ctr = (
    dag.container()
    .from_("node:20")
    .with_mounted_cache("/root/.npm", npm_cache)
    .with_mounted_cache("/app/node_modules", node_modules)
    .with_directory("/app", source)
    .with_workdir("/app")
    .with_exec(["npm", "ci"])
)
```

### Go

```python
go_cache = dag.cache_volume("go-build-cache")
go_mod = dag.cache_volume("go-mod-cache")
ctr = (
    dag.container()
    .from_("golang:1.22")
    .with_mounted_cache("/root/.cache/go-build", go_cache)
    .with_mounted_cache("/go/pkg/mod", go_mod)
    .with_directory("/app", source)
    .with_workdir("/app")
    .with_exec(["go", "build", "./..."])
)
```

### Rust (Cargo)

```python
cargo_cache = dag.cache_volume("cargo-cache")
target_cache = dag.cache_volume("cargo-target")
ctr = (
    dag.container()
    .from_("rust:1.77")
    .with_mounted_cache("/usr/local/cargo/registry", cargo_cache)
    .with_mounted_cache("/app/target", target_cache)
    .with_directory("/app", source)
    .with_workdir("/app")
    .with_exec(["cargo", "build", "--release"])
)
```

### APT (Debian/Ubuntu)

```python
apt_cache = dag.cache_volume("apt-cache")
ctr = (
    dag.container()
    .from_("debian:bookworm-slim")
    .with_mounted_cache("/var/cache/apt/archives", apt_cache)
    .with_exec(["apt-get", "update"])
    .with_exec(["apt-get", "install", "-y", "curl", "git"])
)
```

## Cache Invalidation

### Busting Layer Cache

```python
import datetime

@function
async def build_nightly(self, source: dagger.Directory) -> dagger.Container:
    """Force fresh build by injecting a changing environment variable."""
    return (
        dag.container()
        .from_("python:3.12")
        .with_env_variable("CACHE_BUST", datetime.datetime.now().isoformat())
        .with_directory("/app", source)
        .with_exec(["pip", "install", "-r", "requirements.txt"])
    )
```

### Selective Invalidation

Place cache-busting env vars strategically:

```python
@function
async def build(self, source: dagger.Directory, bust_deps: bool = False) -> dagger.Container:
    ctr = dag.container().from_("node:20")
    if bust_deps:
        ctr = ctr.with_env_variable("DEPS_BUST", "true")
    return (
        ctr
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exec(["npm", "ci"])
    )
```

## Dagger Cloud Cache

Dagger Cloud provides distributed caching across CI runners:

- **Cross-runner sharing**: Cache is shared across all CI jobs in your organization
- **26 global regions**: Cache distributed close to your runners
- **Automatic**: No configuration beyond setting `DAGGER_CLOUD_TOKEN`
- **Cost**: Included in Dagger Cloud subscription ($50/month for up to 10 users)

```yaml
# GitHub Actions with Dagger Cloud caching
env:
  DAGGER_CLOUD_TOKEN: ${{ secrets.DAGGER_CLOUD_TOKEN }}
```

## Performance Tips

1. **Copy dependency files first**: Separate dependency installation from source code
2. **Use cache volumes**: Always cache package manager directories
3. **Minimize context**: Pass only needed directories, exclude `node_modules`, `.git`, etc.
4. **Parallelize stages**: Independent operations can run concurrently
5. **Pin base images**: Avoid cache misses from floating tags like `latest`

## Common Pitfalls

1. **Not using cache volumes**: Package managers re-download everything each run
2. **Wrong operation order**: Putting source copy before dependency install invalidates cache
3. **Using `latest` tags**: Base image changes invalidate all subsequent layers
4. **Large contexts**: Mounting entire repos including build artifacts wastes cache
5. **Forgetting apt cache**: System package installation is slow without caching
