# Dagger Modules

> Source: https://docs.dagger.io/features/modules | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Creating a Module](#creating-a-module)
- [Module Structure](#module-structure)
- [Module Configuration](#module-configuration)
- [Dependencies](#dependencies)
- [Installing Modules](#installing-modules)
- [Cross-Language Composition](#cross-language-composition)
- [Module Development Workflow](#module-development-workflow)
- [Publishing to the Daggerverse](#publishing-to-the-daggerverse)
- [Best Practices](#best-practices)

## Overview

A Dagger module is a collection of Dagger Functions packaged for sharing and reuse. Modules follow principles similar to Go modules:

- **Source distribution**: Code is distributed as source, built locally, and cached
- **Git as source of truth**: Versioned via Git tags (semver)
- **Dependency pinning**: Installed versions are locked in `dagger.json`
- **Natural isolation**: Container-based execution prevents dependency conflicts
- **Cross-language**: A Python module can depend on Go or TypeScript modules

## Creating a Module

### Initialize

```bash
# Create a new module in the current directory
dagger init --sdk=python --name=my-cicd

# Create in a subdirectory
mkdir ci && cd ci
dagger init --sdk=go --name=ci

# With a specific SDK version
dagger init --sdk=typescript --name=my-module
```

### Generated Files

After `dagger init --sdk=python --name=my-cicd`:

```
.
├── dagger.json          # Module manifest
├── pyproject.toml       # Python project configuration
├── uv.lock              # Dependency lock file
└── src/
    └── main/
        └── __init__.py  # Your functions go here
```

## Module Structure

### Python Module

```python
# src/main/__init__.py
import dagger
from dagger import dag, function, object_type

@object_type
class MyCicd:
    @function
    async def build(self, source: dagger.Directory) -> dagger.Container:
        """Build the project."""
        return (
            dag.container()
            .from_("python:3.12")
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["pip", "install", "."])
        )

    @function
    async def test(self, source: dagger.Directory) -> str:
        """Run tests."""
        ctr = await self.build(source)
        return await ctr.with_exec(["pytest"]).stdout()

    @function
    async def lint(self, source: dagger.Directory) -> str:
        """Run linting."""
        ctr = await self.build(source)
        return await ctr.with_exec(["ruff", "check", "."]).stdout()
```

### Go Module

```go
// main.go
package main

import (
    "context"
    "dagger/my-cicd/internal/dagger"
)

type MyCicd struct{}

func (m *MyCicd) Build(source *dagger.Directory) *dagger.Container {
    return dag.Container().
        From("golang:1.22").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"go", "build", "./..."})
}

func (m *MyCicd) Test(ctx context.Context, source *dagger.Directory) (string, error) {
    return m.Build(source).
        WithExec([]string{"go", "test", "./..."}).
        Stdout(ctx)
}
```

## Module Configuration

### dagger.json

```json
{
  "name": "my-cicd",
  "sdk": "python",
  "engineVersion": "v0.20.3",
  "dependencies": [
    {
      "name": "golang",
      "source": "github.com/dagger/dagger/modules/golang@v0.20.0"
    }
  ],
  "source": "."
}
```

Key fields:
- `name`: Module name (used in `dag.<name>()` calls)
- `sdk`: Language SDK (python, go, typescript, php, java)
- `engineVersion`: Minimum Dagger Engine version
- `dependencies`: List of installed dependency modules
- `source`: Path to module source relative to dagger.json

## Dependencies

### Adding Dependencies

```bash
# Install a module from the Daggerverse
dagger install github.com/dagger/dagger/modules/golang@v0.20.0

# Install from a specific branch
dagger install github.com/user/module@main

# Install a local module
dagger install ./modules/shared-utils
```

### Using Dependencies

After installing, dependencies are available via `dag`:

```python
@function
async def lint_go(self, source: dagger.Directory) -> str:
    """Lint Go code using the official Go module."""
    return await (
        dag.golang()  # Installed dependency
        .with_source(source)
        .lint()
    )
```

### Updating Dependencies

```bash
# Update a specific dependency
dagger install github.com/dagger/dagger/modules/golang@v0.21.0

# The lock in dagger.json is updated automatically
```

## Installing Modules

### From Daggerverse

```bash
# Browse: https://daggerverse.dev
dagger install github.com/purpleclay/daggerverse/helm@v0.4.0
dagger install github.com/aweris/daggerverse/gh@v0.1.0
```

### From Private Repositories

```bash
# SSH authentication works if your git config supports it
dagger install git@github.com:myorg/private-module.git@v1.0.0
```

### Version Pinning

Always pin to a specific version tag in production:
```bash
# Good — pinned version
dagger install github.com/user/module@v1.2.3

# Risky — floating reference
dagger install github.com/user/module@main
```

## Cross-Language Composition

One of Dagger's most powerful features: modules can call each other regardless of language.

```python
# Python function calling a Go module and a TypeScript module
@function
async def ci(self, source: dagger.Directory) -> str:
    # Go module for building
    build = dag.golang().with_source(source).build()

    # TypeScript module for deployment
    url = await dag.deploy_tool().deploy(build, env="staging")

    return url
```

The Dagger Engine handles all serialization and cross-language communication through the shared GraphQL API.

## Module Development Workflow

### Local Development

```bash
# Run a function during development
dagger call build --source=.

# Use the develop command to regenerate SDK bindings
dagger develop

# Run with verbose output
dagger call --debug build --source=.
```

### Testing Modules

```bash
# Test functions directly
dagger call test --source=.

# Interactive debugging with Dagger Shell
dagger
> build --source=. | terminal
```

### Monorepo Support

Multiple modules can coexist in a single repository:

```
repo/
├── modules/
│   ├── frontend/
│   │   └── dagger.json
│   ├── backend/
│   │   └── dagger.json
│   └── shared/
│       └── dagger.json
├── src/
└── README.md
```

## Publishing to the Daggerverse

1. Push module source to a public Git repository
2. Tag with semver: `git tag v1.0.0 && git push --tags`
3. Visit https://daggerverse.dev and submit your module URL
4. The Daggerverse indexes your module and makes it discoverable

Requirements:
- Public Git repository
- Semver-compliant version tags
- Valid `dagger.json` at the module root

## Best Practices

1. **Single responsibility**: Each module should handle one concern (build, test, deploy)
2. **Pin dependencies**: Always use version tags, never floating refs in production
3. **Document functions**: Docstrings become CLI help text
4. **Return containers**: Return `Container` from build stages to enable downstream chaining
5. **Use cache volumes**: Mount package manager caches for faster builds
6. **Keep modules small**: Smaller modules are easier to test and reuse
7. **Version your modules**: Use semver tags for stable references
8. **Test locally first**: Run `dagger call` before pushing to CI
