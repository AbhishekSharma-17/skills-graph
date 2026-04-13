# Dagger Common Patterns

> Source: https://docs.dagger.io/cookbook | Version: 0.20.x

## Table of Contents
- [Build Patterns](#build-patterns)
- [Test Patterns](#test-patterns)
- [Deploy Patterns](#deploy-patterns)
- [Multi-Platform Builds](#multi-platform-builds)
- [Monorepo Patterns](#monorepo-patterns)
- [Complete CI Pipeline](#complete-ci-pipeline)
- [Dockerfile Integration](#dockerfile-integration)
- [Git Operations](#git-operations)
- [Matrix Builds](#matrix-builds)
- [Common Pitfalls](#common-pitfalls)

## Build Patterns

### Python Application

```python
@dagger.function
async def build_python(self, source: dagger.Directory) -> dagger.Container:
    """Build a Python application with cached dependencies."""
    pip_cache = dag.cache_volume("pip-cache")

    return (
        dag.container()
        .from_("python:3.12-slim")
        .with_mounted_cache("/root/.cache/pip", pip_cache)
        .with_file("/app/requirements.txt", source.file("requirements.txt"))
        .with_workdir("/app")
        .with_exec(["pip", "install", "-r", "requirements.txt"])
        .with_directory("/app", source)
        .with_entrypoint(["python", "-m", "app"])
    )
```

### Node.js Application

```python
@dagger.function
async def build_node(self, source: dagger.Directory) -> dagger.Container:
    """Build a Node.js application with cached node_modules."""
    npm_cache = dag.cache_volume("npm-cache")

    return (
        dag.container()
        .from_("node:20-slim")
        .with_mounted_cache("/root/.npm", npm_cache)
        .with_file("/app/package.json", source.file("package.json"))
        .with_file("/app/package-lock.json", source.file("package-lock.json"))
        .with_workdir("/app")
        .with_exec(["npm", "ci"])
        .with_directory("/app/src", source.directory("src"))
        .with_exec(["npm", "run", "build"])
    )
```

### Go Application

```python
@dagger.function
async def build_go(self, source: dagger.Directory) -> dagger.File:
    """Build a Go binary with static linking."""
    go_cache = dag.cache_volume("go-build-cache")
    mod_cache = dag.cache_volume("go-mod-cache")

    binary = (
        dag.container()
        .from_("golang:1.22")
        .with_mounted_cache("/root/.cache/go-build", go_cache)
        .with_mounted_cache("/go/pkg/mod", mod_cache)
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_env_variable("CGO_ENABLED", "0")
        .with_exec(["go", "build", "-ldflags", "-s -w", "-o", "/app/bin/server", "./cmd/server"])
        .file("/app/bin/server")
    )

    return binary
```

### Multi-Stage Build

```python
@dagger.function
async def build_multistage(self, source: dagger.Directory) -> dagger.Container:
    """Multi-stage build: compile in full image, run in slim image."""
    # Build stage
    builder = (
        dag.container()
        .from_("golang:1.22")
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_env_variable("CGO_ENABLED", "0")
        .with_exec(["go", "build", "-o", "/app/server", "./cmd/server"])
    )

    # Runtime stage
    return (
        dag.container()
        .from_("gcr.io/distroless/static:nonroot")
        .with_file("/server", builder.file("/app/server"))
        .with_entrypoint(["/server"])
        .with_exposed_port(8080)
    )
```

## Test Patterns

### Unit Tests

```python
@dagger.function
async def test(self, source: dagger.Directory) -> str:
    """Run unit tests."""
    return await (
        self.build(source)
        .with_exec(["pytest", "-v", "--tb=short"])
        .stdout()
    )
```

### Integration Tests with Services

```python
@dagger.function
async def integration_test(self, source: dagger.Directory) -> str:
    """Run integration tests with a real database."""
    db = (
        dag.container()
        .from_("postgres:16")
        .with_env_variable("POSTGRES_PASSWORD", "test")
        .with_env_variable("POSTGRES_DB", "testdb")
        .with_exposed_port(5432)
        .as_service()
    )

    return await (
        self.build(source)
        .with_service_binding("db", db)
        .with_env_variable("DATABASE_URL", "postgresql://postgres:test@db:5432/testdb")
        .with_exec(["pytest", "tests/integration/", "-v"])
        .stdout()
    )
```

### Parallel Test Execution

```python
@dagger.function
async def test_all(self, source: dagger.Directory) -> str:
    """Run multiple test suites in parallel."""
    import asyncio

    base = await self.build(source)

    unit, integration, e2e = await asyncio.gather(
        base.with_exec(["pytest", "tests/unit/"]).stdout(),
        base.with_exec(["pytest", "tests/integration/"]).stdout(),
        base.with_exec(["pytest", "tests/e2e/"]).stdout(),
    )

    return f"Unit:\n{unit}\nIntegration:\n{integration}\nE2E:\n{e2e}"
```

## Deploy Patterns

### Container Registry Publish

```python
@dagger.function
async def publish(
    self,
    source: dagger.Directory,
    registry: str,
    tag: str,
    password: dagger.Secret,
    username: str = "ci",
) -> str:
    """Build and publish to a container registry."""
    ctr = await self.build(source)
    return await (
        ctr
        .with_registry_auth(registry, username, password)
        .publish(f"{registry}/myapp:{tag}")
    )
```

### Deploy to Kubernetes

```python
@dagger.function
async def deploy_k8s(
    self,
    source: dagger.Directory,
    kubeconfig: dagger.Secret,
    namespace: str = "default",
) -> str:
    """Deploy to Kubernetes using kubectl."""
    return await (
        dag.container()
        .from_("bitnami/kubectl:latest")
        .with_mounted_secret("/root/.kube/config", kubeconfig)
        .with_directory("/manifests", source.directory("k8s"))
        .with_exec(["kubectl", "apply", "-f", "/manifests/", "-n", namespace])
        .stdout()
    )
```

## Multi-Platform Builds

```python
@dagger.function
async def build_multiplatform(
    self,
    source: dagger.Directory,
    registry: str,
    tag: str,
    password: dagger.Secret,
) -> str:
    """Build and publish multi-platform image."""
    platforms = ["linux/amd64", "linux/arm64"]

    variants = []
    for platform in platforms:
        ctr = (
            dag.container(platform=dagger.Platform(platform))
            .from_("python:3.12-slim")
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
            .with_entrypoint(["python", "-m", "app"])
        )
        variants.append(ctr)

    return await (
        dag.container()
        .with_registry_auth(registry, "ci", password)
        .publish(f"{registry}/myapp:{tag}", platform_variants=variants)
    )
```

## Monorepo Patterns

### Selective Builds

```python
@dagger.function
async def build_service(
    self,
    source: dagger.Directory,
    service: str,
) -> dagger.Container:
    """Build a specific service from a monorepo."""
    service_dir = source.directory(f"services/{service}")
    shared_dir = source.directory("shared")

    return (
        dag.container()
        .from_("python:3.12-slim")
        .with_directory(f"/app/services/{service}", service_dir)
        .with_directory("/app/shared", shared_dir)
        .with_workdir(f"/app/services/{service}")
        .with_exec(["pip", "install", "-r", "requirements.txt"])
    )
```

### Build All Services

```python
@dagger.function
async def build_all(self, source: dagger.Directory) -> list[str]:
    """Build all services in the monorepo."""
    import asyncio

    services = ["api", "worker", "web"]
    tasks = [
        self.build_and_publish(source, svc)
        for svc in services
    ]
    return await asyncio.gather(*tasks)
```

## Complete CI Pipeline

```python
@dagger.object_type
class Ci:
    @dagger.function
    async def build(self, source: dagger.Directory) -> dagger.Container:
        """Build the application."""
        pip_cache = dag.cache_volume("pip-cache")
        return (
            dag.container()
            .from_("python:3.12-slim")
            .with_mounted_cache("/root/.cache/pip", pip_cache)
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
        )

    @dagger.function
    async def lint(self, source: dagger.Directory) -> str:
        """Run linting."""
        ctr = await self.build(source)
        return await ctr.with_exec(["ruff", "check", "."]).stdout()

    @dagger.function
    async def test(self, source: dagger.Directory) -> str:
        """Run tests."""
        ctr = await self.build(source)
        return await ctr.with_exec(["pytest", "-v"]).stdout()

    @dagger.function
    async def publish(
        self,
        source: dagger.Directory,
        registry: str,
        tag: str,
        password: dagger.Secret,
    ) -> str:
        """Build and publish."""
        ctr = await self.build(source)
        return await (
            ctr
            .with_registry_auth(registry, "ci", password)
            .publish(f"{registry}/myapp:{tag}")
        )

    @dagger.function
    async def ci(
        self,
        source: dagger.Directory,
        registry: str | None = None,
        tag: str = "latest",
        password: dagger.Secret | None = None,
    ) -> str:
        """Full CI pipeline: lint, test, optionally publish."""
        await self.lint(source)
        await self.test(source)

        if registry and password:
            return await self.publish(source, registry, tag, password)
        return "Lint and tests passed."
```

## Dockerfile Integration

### Build from Dockerfile

```python
@dagger.function
async def build_from_dockerfile(
    self,
    source: dagger.Directory,
    dockerfile: str = "Dockerfile",
) -> dagger.Container:
    """Build from an existing Dockerfile."""
    return dag.container().build(source, dockerfile=dockerfile)
```

### With Build Args

```python
@dagger.function
async def build_with_args(self, source: dagger.Directory) -> dagger.Container:
    """Build with custom build arguments."""
    return dag.container().build(
        source,
        dockerfile="Dockerfile",
        build_args=[
            dagger.BuildArg(name="NODE_ENV", value="production"),
            dagger.BuildArg(name="APP_VERSION", value="1.0.0"),
        ],
    )
```

## Git Operations

```python
@dagger.function
async def clone_and_build(self) -> dagger.Container:
    """Clone a public repo and build it."""
    source = (
        dag.git("https://github.com/user/repo")
        .branch("main")
        .tree()
    )
    return await self.build(source)
```

## Matrix Builds

```python
@dagger.function
async def test_matrix(self, source: dagger.Directory) -> str:
    """Test across multiple Python versions."""
    import asyncio

    versions = ["3.10", "3.11", "3.12"]
    results = await asyncio.gather(*[
        self._test_version(source, v) for v in versions
    ])
    return "\n".join(f"Python {v}: {r}" for v, r in zip(versions, results))

async def _test_version(self, source: dagger.Directory, version: str) -> str:
    pip_cache = dag.cache_volume(f"pip-{version}")
    return await (
        dag.container()
        .from_(f"python:{version}-slim")
        .with_mounted_cache("/root/.cache/pip", pip_cache)
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exec(["pip", "install", "-r", "requirements.txt"])
        .with_exec(["pytest", "-v"])
        .stdout()
    )
```

## Common Pitfalls

1. **Not caching dependencies**: Always use `with_mounted_cache` for package managers
2. **Copying everything**: Filter out `node_modules`, `.git`, `__pycache__` before mounting
3. **Sequential when parallel is possible**: Use `asyncio.gather` for independent operations
4. **Hardcoded values**: Use function arguments for registry, tag, and environment settings
5. **Missing error handling**: Add proper error messages for failed pipeline steps
6. **Not testing locally**: Always `dagger call` locally before pushing CI changes
