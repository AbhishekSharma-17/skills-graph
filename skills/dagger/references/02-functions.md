# Dagger Functions

> Source: https://docs.dagger.io/getting-started/functions | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Function Basics](#function-basics)
- [Python Functions](#python-functions)
- [Go Functions](#go-functions)
- [TypeScript Functions](#typescript-functions)
- [Arguments and Return Types](#arguments-and-return-types)
- [Default Values](#default-values)
- [Documentation](#documentation)
- [Calling Functions](#calling-functions)
- [Cross-Language Calls](#cross-language-calls)
- [Common Pitfalls](#common-pitfalls)

## Overview

Dagger Functions are individual units of computation that perform a specific task. They combine operations on Dagger types (Container, Directory, etc.) with custom logic, written in a programming language using a type-safe Dagger SDK, and packaged in Dagger modules.

Key properties:
- **Sandboxed**: Functions run in containers, no implicit host access
- **Type-safe**: Arguments and return values are typed
- **Composable**: Functions can call other functions, even across languages
- **Cacheable**: Results are automatically cached based on inputs
- **Testable**: Run locally with `dagger call` before pushing to CI

## Function Basics

### Lifecycle

1. Write functions using an SDK (Python, Go, TypeScript, etc.)
2. Functions are discovered automatically by the Dagger Engine
3. Call functions via CLI (`dagger call`), Dagger Shell, or other functions
4. Engine executes each function in a containerized sandbox
5. Results are cached and returned

### Naming

Functions are exposed in a kebab-case form via the CLI:
- Python `def build_app()` → `dagger call build-app`
- Go `func BuildApp()` → `dagger call build-app`
- TypeScript `buildApp()` → `dagger call build-app`

## Python Functions

```python
import dagger
from dagger import dag, function, object_type

@object_type
class MyPipeline:
    @function
    async def build(self, source: dagger.Directory) -> dagger.Container:
        """Build the application container."""
        return (
            dag.container()
            .from_("python:3.12-slim")
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
        )

    @function
    async def test(self, source: dagger.Directory) -> str:
        """Run tests and return output."""
        ctr = await self.build(source)
        return await ctr.with_exec(["pytest", "-v"]).stdout()

    @function
    async def publish(
        self,
        source: dagger.Directory,
        registry: str = "ttl.sh",
        tag: str = "latest",
    ) -> str:
        """Build and publish container image."""
        ctr = await self.build(source)
        return await ctr.publish(f"{registry}/my-app:{tag}")
```

### Python Decorators
- `@object_type`: Marks a class as a Dagger module object
- `@function`: Exposes a method as a Dagger Function
- `dag`: Global accessor for the Dagger API client

### Python Async
Python functions should be `async def` since most Dagger operations are asynchronous. Use `await` on terminal operations like `stdout()`, `publish()`, `contents()`.

## Go Functions

```go
package main

import (
    "context"
    "dagger/my-pipeline/internal/dagger"
)

type MyPipeline struct{}

// Build the application container.
func (m *MyPipeline) Build(source *dagger.Directory) *dagger.Container {
    return dag.Container().
        From("python:3.12-slim").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"pip", "install", "-r", "requirements.txt"})
}

// Run tests and return output.
func (m *MyPipeline) Test(ctx context.Context, source *dagger.Directory) (string, error) {
    return m.Build(source).
        WithExec([]string{"pytest", "-v"}).
        Stdout(ctx)
}

// Build and publish container image.
func (m *MyPipeline) Publish(
    ctx context.Context,
    source *dagger.Directory,
    // +optional
    // +default="ttl.sh"
    registry string,
    // +optional
    // +default="latest"
    tag string,
) (string, error) {
    return m.Build(source).
        Publish(ctx, registry+"/my-app:"+tag)
}
```

### Go Conventions
- Receiver type is your module struct
- Public methods (capitalized) are exposed as functions
- Use `context.Context` for async terminal operations
- Comments on parameters use `// +optional`, `// +default="value"`
- Return `(T, error)` for operations that can fail

## TypeScript Functions

```typescript
import { dag, Container, Directory, func, object } from "@dagger.io/dagger"

@object()
class MyPipeline {
  @func()
  build(source: Directory): Container {
    return dag
      .container()
      .from("python:3.12-slim")
      .withDirectory("/app", source)
      .withWorkdir("/app")
      .withExec(["pip", "install", "-r", "requirements.txt"])
  }

  @func()
  async test(source: Directory): Promise<string> {
    return this.build(source)
      .withExec(["pytest", "-v"])
      .stdout()
  }

  @func()
  async publish(
    source: Directory,
    registry: string = "ttl.sh",
    tag: string = "latest"
  ): Promise<string> {
    return this.build(source)
      .publish(`${registry}/my-app:${tag}`)
  }
}
```

### TypeScript Decorators
- `@object()`: Marks a class as a Dagger module object
- `@func()`: Exposes a method as a Dagger Function

## Arguments and Return Types

### Supported Argument Types
| Type | Description |
|------|-------------|
| `str` / `string` | Plain text |
| `int` / `int` | Integer numbers |
| `float` / `float64` | Floating point |
| `bool` / `bool` | Boolean |
| `dagger.Container` | Container reference |
| `dagger.Directory` | Directory reference |
| `dagger.File` | File reference |
| `dagger.Secret` | Secret value |
| `dagger.Service` | Running service |
| `dagger.CacheVolume` | Cache volume |
| `list[T]` / `[]T` | List of any supported type |
| `enum` | Enumerated values |

### Return Types
Functions can return any supported type. Common patterns:
- `Container` — for pipeline stages (enables chaining)
- `Directory` — for build outputs
- `str` / `string` — for command output or published references
- `Service` — for background services

## Default Values

```python
@function
async def build(
    self,
    source: dagger.Directory,
    base_image: str = "python:3.12-slim",
    install_dev: bool = False,
) -> dagger.Container:
    ctr = dag.container().from_(base_image)
    if install_dev:
        ctr = ctr.with_exec(["pip", "install", "-r", "requirements-dev.txt"])
    return ctr
```

CLI usage:
```bash
dagger call build --source=. --base-image=python:3.11 --install-dev
```

## Documentation

Function and parameter documentation becomes CLI help text:

```python
@function
async def deploy(
    self,
    source: dagger.Directory,
    environment: str = "staging",
) -> str:
    """Deploy the application to the target environment.

    Args:
        source: Application source directory
        environment: Target environment (staging or production)
    """
    ...
```

```bash
$ dagger call deploy --help
Deploy the application to the target environment.

Arguments:
  --source       Application source directory
  --environment  Target environment (staging or production) [default: "staging"]
```

## Calling Functions

### From CLI
```bash
# Call a function in the current module
dagger call test --source=.

# Call from a remote module
dagger call -m github.com/user/module@v1.0 build --source=.

# Chain calls
dagger call build --source=. publish --registry=ghcr.io/myorg
```

### From Another Function
```python
@function
async def ci(self, source: dagger.Directory) -> str:
    # Call your own functions
    await self.test(source)
    return await self.publish(source)
```

### From Dagger Shell
```bash
my-pipeline | test --source=.
my-pipeline | build --source=. | publish ttl.sh/test
```

## Cross-Language Calls

Functions can call modules written in other languages:

```python
@function
async def lint(self, source: dagger.Directory) -> str:
    """Use a Go-based linting module."""
    return await (
        dag.golangci_lint()  # Go module from Daggerverse
        .run(source)
        .stdout()
    )
```

Install a dependency:
```bash
dagger install github.com/dagger/dagger/modules/golangci-lint@v0.20.0
```

## Common Pitfalls

1. **Forgetting `self`**: Python functions need `self` as the first parameter
2. **Missing `@function` decorator**: Functions without the decorator aren't exposed
3. **Host access**: Functions can't access the host filesystem — pass directories as arguments
4. **Sync vs async**: In Python, use `async def` and `await` for terminal operations
5. **Naming conflicts**: Python uses `from_()` instead of `from()`, `import_()` instead of `import()`
6. **Not returning containers**: Return `Container` from build stages to enable chaining
