# Dagger Core Types

> Source: https://docs.dagger.io/getting-started/core-types | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Container](#container)
- [Directory](#directory)
- [File](#file)
- [Secret](#secret)
- [Service](#service)
- [CacheVolume](#cachevolume)
- [Socket](#socket)
- [Type Composition Patterns](#type-composition-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Dagger provides a set of core types that represent the fundamental building blocks of CI/CD pipelines. These types hold data (state) and enable isolated execution within containers. All types are immutable — operations return new instances rather than modifying existing ones.

Types are available across all SDKs with language-idiomatic naming (e.g., `with_exec` in Python, `WithExec` in Go, `withExec` in TypeScript).

## Container

The primary type for building and running containerized workloads.

### Creating Containers

```python
# From a base image
ctr = dag.container().from_("python:3.12-slim")

# From scratch (empty container)
ctr = dag.container()

# From a Dockerfile
ctr = dag.container().build(source_dir)
ctr = dag.container().build(source_dir, dockerfile="Dockerfile.prod")
```

### Executing Commands

```python
# Run a command
ctr = ctr.with_exec(["pip", "install", "-r", "requirements.txt"])

# Capture stdout
output = await ctr.with_exec(["python", "--version"]).stdout()

# Capture stderr
errors = await ctr.with_exec(["pytest"]).stderr()

# Get exit code (non-zero raises error by default)
ctr = ctr.with_exec(["test", "-f", "/app/config.json"])
```

### Adding Files and Directories

```python
# Mount a host directory
ctr = ctr.with_directory("/app", source)

# Add a single file
ctr = ctr.with_file("/app/config.json", config_file)

# Create a new file inline
ctr = ctr.with_new_file("/app/.env", contents="NODE_ENV=production")

# Mount from a remote git repo
ctr = ctr.with_directory("/src", dag.git("https://github.com/user/repo").branch("main").tree())
```

### Configuration

```python
# Set working directory
ctr = ctr.with_workdir("/app")

# Set environment variables
ctr = ctr.with_env_variable("NODE_ENV", "production")

# Set entrypoint
ctr = ctr.with_entrypoint(["python", "-m", "app"])

# Expose ports
ctr = ctr.with_exposed_port(8080)

# Set user
ctr = ctr.with_user("nonroot")

# Set labels
ctr = ctr.with_label("org.opencontainers.image.version", "1.0.0")
```

### Publishing

```python
# Push to a registry
ref = await ctr.publish("ghcr.io/myorg/myapp:latest")

# Multi-platform publish
platforms = ["linux/amd64", "linux/arm64"]
variants = [ctr.with_platform(p) for p in platforms]
ref = await dag.container().publish("ghcr.io/myorg/myapp:latest", platform_variants=variants)
```

### Exporting

```python
# Export as tar
await ctr.export("/tmp/image.tar")

# Export as OCI tarball
await ctr.as_tarball()
```

### Interactive Debugging

```python
# Open a terminal inside the container (Dagger Shell only)
# container | from alpine | terminal
```

## Directory

Represents a filesystem directory, either from the host, a container, or a remote source.

### Creating Directories

```python
# Current host directory
src = dag.current_module().source()

# Specific host path (passed as function argument)
# Host directories must be explicitly passed — no implicit host access

# From a git repository
src = dag.git("https://github.com/user/repo").branch("main").tree()

# From a container's filesystem
build_output = ctr.directory("/app/dist")

# Empty directory
empty = dag.directory()
```

### Operations

```python
# List entries
entries = await src.entries()

# Get a file
readme = src.file("README.md")

# Get a subdirectory
tests_dir = src.directory("tests")

# Add/overwrite a file
src = src.with_file("config.json", config_file)

# Add a new file inline
src = src.with_new_file("VERSION", contents="1.0.0")

# Add a subdirectory
src = src.with_directory("vendor", vendor_dir)

# Remove a path
src = src.without_file("secrets.json")
src = src.without_directory("node_modules")

# Glob filter
src = src.glob("**/*.py")

# Export to host
await src.export("/tmp/output")
```

## File

Represents a single file.

```python
# Get from a directory
f = src.file("package.json")

# Read contents
content = await f.contents()

# Get file name
name = await f.name()

# Get file size
size = await f.size()

# Export to host
await f.export("/tmp/package.json")
```

## Secret

Securely holds sensitive values (passwords, tokens, keys). Secrets are never exposed in logs, cache keys, or container filesystem layers.

```python
# From environment variable
token = dag.set_secret("github-token", os.environ["GITHUB_TOKEN"])

# Use in a container
ctr = ctr.with_secret_variable("GITHUB_TOKEN", token)

# Mount as a file
ctr = ctr.with_mounted_secret("/run/secrets/api-key", api_key_secret)

# From CLI (passed as function argument of type Secret)
@dagger.function
async def deploy(registry_password: dagger.Secret) -> str:
    ...
```

See [06-secrets](06-secrets.md) for advanced providers (Vault, 1Password, AWS).

## Service

Represents a running network service (database, API server, cache).

```python
# Create a service from a container
db = (
    dag.container()
    .from_("postgres:16")
    .with_env_variable("POSTGRES_PASSWORD", "test")
    .with_exposed_port(5432)
    .as_service()
)

# Bind to another container
app = (
    dag.container()
    .from_("python:3.12")
    .with_service_binding("db", db)
    .with_exec(["python", "-c", "import psycopg2; conn = psycopg2.connect(host='db')"])
)

# Start and get endpoint
endpoint = await db.endpoint(port=5432, scheme="tcp")
```

See [05-services](05-services.md) for networking patterns.

## CacheVolume

Persists data across function executions, ideal for package manager caches.

```python
# Create or reuse a named cache volume
pip_cache = dag.cache_volume("pip-cache")
npm_cache = dag.cache_volume("npm-cache")

# Mount in a container
ctr = (
    dag.container()
    .from_("python:3.12")
    .with_mounted_cache("/root/.cache/pip", pip_cache)
    .with_exec(["pip", "install", "-r", "requirements.txt"])
)
```

## Socket

Represents a Unix socket, typically used for Docker socket forwarding.

```python
# Mount Docker socket (for Docker-in-Docker scenarios)
ctr = ctr.with_unix_socket("/var/run/docker.sock", dag.host().unix_socket("/var/run/docker.sock"))
```

## Type Composition Patterns

### Chaining (Fluent API)

All types support method chaining — each method returns a new instance:

```python
result = await (
    dag.container()
    .from_("node:20")
    .with_directory("/app", source)
    .with_workdir("/app")
    .with_mounted_cache("/app/node_modules", dag.cache_volume("node-modules"))
    .with_exec(["npm", "ci"])
    .with_exec(["npm", "test"])
    .stdout()
)
```

### Extracting Artifacts

```python
# Get build output from a container
build_dir = (
    dag.container()
    .from_("node:20")
    .with_directory("/app", source)
    .with_exec(["npm", "run", "build"])
    .directory("/app/dist")
)

# Use in another container
deploy_ctr = (
    dag.container()
    .from_("nginx:alpine")
    .with_directory("/usr/share/nginx/html", build_dir)
)
```

## Common Pitfalls

1. **Trying to access host directly**: Functions are sandboxed — pass directories as arguments
2. **Forgetting `await`**: In Python, terminal operations (stdout, contents, publish) are async
3. **Not using `from_` in Python**: The method is `from_()` with underscore to avoid Python keyword conflict
4. **Mutating vs chaining**: Types are immutable; always use the return value
5. **Large context directories**: Filter with `.without_directory("node_modules")` before mounting
