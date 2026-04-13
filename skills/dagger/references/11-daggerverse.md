# Daggerverse

> Source: https://daggerverse.dev | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Discovering Modules](#discovering-modules)
- [Installing Modules](#installing-modules)
- [Popular Modules](#popular-modules)
- [Publishing Your Module](#publishing-your-module)
- [Module Versioning](#module-versioning)
- [Module Documentation](#module-documentation)
- [Private Modules](#private-modules)
- [Common Pitfalls](#common-pitfalls)

## Overview

The Daggerverse is a free service that indexes all publicly available Dagger modules. It serves as a discovery and distribution platform for reusable pipeline components, similar to npm for JavaScript or PyPI for Python.

Browse at: https://daggerverse.dev

Key features:
- **Discovery**: Search for modules by name, language, or functionality
- **Documentation**: Auto-generated docs from module functions and docstrings
- **Versioning**: Semver-based version tags from Git
- **Cross-language**: Modules in any language can be consumed from any other language

## Discovering Modules

### Web Interface

Visit https://daggerverse.dev to:
- Browse featured and trending modules
- Search by keyword (e.g., "golang", "docker", "helm")
- View module documentation, functions, and parameters
- See installation instructions

### CLI Discovery

```bash
# List functions from a remote module
dagger functions -m github.com/purpleclay/daggerverse/helm@v0.4.0

# Get help for a specific function
dagger call -m github.com/purpleclay/daggerverse/helm@v0.4.0 lint --help
```

## Installing Modules

### As a Dependency

```bash
# Install a module as a dependency of your module
dagger install github.com/purpleclay/daggerverse/helm@v0.4.0

# This updates dagger.json with the dependency
```

### Direct Invocation

Call a module without installing it:

```bash
# Run a function from a remote module directly
dagger call -m github.com/shykes/daggerverse/hello@v0.1.2 hello --greeting="bonjour" --name="monde"

# Use in Dagger Shell
dagger shell 'github.com/shykes/daggerverse/hello@v0.1.2 | hello --greeting=hi --name=world'
```

### Version Pinning

```bash
# Pin to a specific version tag
dagger install github.com/user/module@v1.2.3

# Pin to a specific commit
dagger install github.com/user/module@abc1234
```

## Popular Modules

### Language Toolchains

| Module | Description | Install |
|--------|-------------|---------|
| golang | Go build, test, lint | `github.com/dagger/dagger/modules/golang` |
| node | Node.js build and test | `github.com/dagger/dagger/modules/node` |
| python | Python build and test | `github.com/dagger/dagger/modules/python` |
| rust | Rust build and test | Community modules |

### DevOps Tools

| Module | Description | Install |
|--------|-------------|---------|
| helm | Kubernetes Helm charts | `github.com/purpleclay/daggerverse/helm` |
| kubectl | Kubernetes management | Community modules |
| terraform | IaC execution | Community modules |

### Utilities

| Module | Description | Install |
|--------|-------------|---------|
| gh | GitHub CLI operations | `github.com/aweris/daggerverse/gh` |
| wolfi | Wolfi OS base images | `github.com/dagger/dagger/modules/wolfi` |

### Using an Installed Module

```python
@dagger.function
async def build_go(self, source: dagger.Directory) -> dagger.Container:
    """Build Go project using the official Go module."""
    return (
        dag.golang()
        .with_source(source)
        .build()
    )

@dagger.function
async def lint_go(self, source: dagger.Directory) -> str:
    """Lint Go code."""
    return await (
        dag.golang()
        .with_source(source)
        .lint()
        .stdout()
    )
```

## Publishing Your Module

### Prerequisites

1. Module source in a public Git repository
2. Valid `dagger.json` at the module root
3. Semver-compliant version tags

### Steps

```bash
# 1. Ensure your module is in a public git repo
git remote -v

# 2. Tag a release
git tag v1.0.0
git push --tags

# 3. Submit to Daggerverse
# Visit https://daggerverse.dev and enter your module URL:
# github.com/youruser/yourrepo/path/to/module@v1.0.0
```

### Module URL Format

```
github.com/<owner>/<repo>[/<path>]@<version>
```

Examples:
- `github.com/myorg/pipelines@v1.0.0` — root module
- `github.com/myorg/pipelines/modules/deploy@v1.0.0` — nested module

### Monorepo Publishing

Multiple modules can exist in one repository:

```
repo/
├── modules/
│   ├── frontend/
│   │   └── dagger.json    → github.com/myorg/repo/modules/frontend@v1.0
│   ├── backend/
│   │   └── dagger.json    → github.com/myorg/repo/modules/backend@v1.0
│   └── deploy/
│       └── dagger.json    → github.com/myorg/repo/modules/deploy@v1.0
```

## Module Versioning

### Tagging Strategy

```bash
# Root module
git tag v1.0.0

# Nested module (path-based tags)
git tag modules/frontend/v1.0.0
```

### Version Selection

- **Exact version**: `@v1.2.3` — recommended for production
- **Branch**: `@main` — latest on branch, not recommended for production
- **Commit**: `@abc1234` — specific commit hash

### Updating Dependencies

```bash
# Update to a newer version
dagger install github.com/user/module@v2.0.0

# Check for available updates
dagger functions -m github.com/user/module@latest
```

## Module Documentation

Documentation is auto-generated from:

1. **Function docstrings**: Become function descriptions
2. **Parameter names and types**: Listed with type information
3. **Default values**: Shown in parameter documentation
4. **Module-level comments**: Appear as module description

### Writing Good Documentation

```python
@dagger.object_type
class Deploy:
    """Deployment utilities for Kubernetes clusters.

    Provides functions for building, pushing, and deploying
    containerized applications to Kubernetes.
    """

    @dagger.function
    async def push(
        self,
        image: dagger.Container,
        registry: str,
        tag: str = "latest",
    ) -> str:
        """Push a container image to a registry.

        Args:
            image: Built container image to push
            registry: Target registry URL (e.g., ghcr.io/myorg)
            tag: Image tag (default: latest)

        Returns:
            Published image reference
        """
        return await image.publish(f"{registry}/app:{tag}")
```

## Private Modules

### Using Private Git Repos

```bash
# SSH authentication (uses your git config)
dagger install git@github.com:myorg/private-module.git@v1.0.0

# Or configure SSH in CI
eval "$(ssh-agent -s)"
ssh-add - <<< "$SSH_PRIVATE_KEY"
dagger call -m git@github.com:myorg/private-module.git@v1.0 build --source=.
```

### Organization Modules

Dagger Cloud provides a Modules tab for tracking organization modules:
- Module inventory with versions
- Dependency visualization
- Usage analytics across projects

## Common Pitfalls

1. **Floating versions**: Using `@main` instead of `@v1.0.0` causes reproducibility issues
2. **Missing tags**: Ensure Git tags are pushed: `git push --tags`
3. **Private repo access**: SSH keys need to be configured for private module access
4. **Breaking changes**: Follow semver — major version bumps for breaking changes
5. **Large modules**: Keep modules focused on a single concern for better reusability
6. **Undocumented functions**: Functions without docstrings are harder to discover and use
