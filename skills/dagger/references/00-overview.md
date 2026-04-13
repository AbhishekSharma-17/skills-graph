# Dagger Overview

> Source: https://docs.dagger.io | Version: 0.20.x

## Table of Contents
- [What Is Dagger](#what-is-dagger)
- [Why Dagger](#why-dagger)
- [Core Architecture](#core-architecture)
- [Supported Languages](#supported-languages)
- [Installation](#installation)
- [First Pipeline](#first-pipeline)
- [Key Concepts Summary](#key-concepts-summary)
- [When to Use Dagger](#when-to-use-dagger)
- [When NOT to Use Dagger](#when-not-to-use-dagger)

## What Is Dagger

Dagger is a programmable CI/CD engine that runs pipelines inside containers. Instead of writing pipelines in YAML, shell scripts, or proprietary DSLs, you write them in real programming languages (Python, Go, TypeScript, PHP, Java, .NET, Elixir, Rust) with full type safety, IDE support, and testability.

Dagger acts as a composition engine for containerized workflows. Every pipeline step runs in an isolated container, ensuring reproducibility across local development machines and CI environments.

**Key proposition**: Write once, run anywhere. The same pipeline runs identically on your laptop and in GitHub Actions, GitLab CI, Jenkins, or any other CI runner.

## Why Dagger

### Problems with Traditional CI/CD
- **YAML sprawl**: Complex pipelines become unmaintainable YAML files
- **No local testing**: CI-only pipelines can't run locally, slowing feedback loops
- **Vendor lock-in**: Pipelines tied to specific CI platforms (GitHub Actions, GitLab CI)
- **No type safety**: YAML-based pipelines have no compile-time checks
- **Script fragility**: Shell scripts glued into CI configs break silently

### How Dagger Solves These
- **Code, not config**: Write pipelines in languages you already know
- **Local-first**: Run the exact same pipeline locally before pushing
- **Portable**: Same pipeline code works on any CI platform
- **Type-safe**: Full IDE support with autocomplete and error checking
- **Containerized**: Every step runs in isolation, no "works on my machine"
- **Cached**: Aggressive content-addressed caching speeds up iterations

## Core Architecture

```
┌──────────────────────────────────────────┐
│              Your Pipeline Code          │
│     (Python / Go / TypeScript / ...)     │
├──────────────────────────────────────────┤
│           Dagger SDK (per-language)       │
│     Type-safe bindings, async support    │
├──────────────────────────────────────────┤
│              Dagger API (GraphQL)         │
│     Container, Directory, File, etc.     │
├──────────────────────────────────────────┤
│             Dagger Engine                 │
│     Container runtime, caching, exec     │
├──────────────────────────────────────────┤
│           Container Runtime              │
│     Docker, Podman, nerdctl, etc.        │
└──────────────────────────────────────────┘
```

- **Dagger Engine**: Core runtime that executes pipelines, manages caching, and orchestrates containers
- **Dagger SDK**: Language-specific bindings generated from the API schema
- **Dagger CLI**: Command-line interface for running functions and interactive exploration
- **Dagger Shell**: Bash-like interactive environment for chaining Dagger API calls
- **Dagger Cloud**: Optional SaaS for telemetry, caching, and pipeline visualization

## Supported Languages

| Language | SDK Status | Package |
|----------|-----------|---------|
| Go | Stable | `dagger.io/dagger` |
| Python | Stable | `dagger-io` (PyPI) |
| TypeScript | Stable | `@dagger.io/dagger` (npm) |
| PHP | Stable | `dagger-php-sdk` |
| Java | Stable | Maven artifact |
| .NET | Community | NuGet package |
| Elixir | Community | Hex package |
| Rust | Community | Crate |

All SDKs are generated from the same GraphQL API schema, ensuring consistent behavior across languages.

## Installation

### Prerequisites
- A container runtime: Docker Desktop, Podman, nerdctl, or OrbStack
- Docker must be running before using Dagger

### CLI Installation

```bash
# macOS (Homebrew)
brew install dagger/tap/dagger

# macOS/Linux (curl)
curl -fsSL https://dl.dagger.io/dagger/install.sh | BIN_DIR=/usr/local/bin sh

# Specific version
DAGGER_VERSION=0.20.3 curl -fsSL https://dl.dagger.io/dagger/install.sh | sh

# Windows
winget install Dagger.Cli

# Verify
dagger version
```

### Python SDK Setup

```bash
pip install dagger-io
# or
uv add dagger-io
```

### Initialize a Module

```bash
# Create a new Dagger module
dagger init --sdk=python --name=my-pipeline
dagger init --sdk=go --name=my-pipeline
dagger init --sdk=typescript --name=my-pipeline
```

This creates a `dagger.json` manifest and SDK-specific source files.

## First Pipeline

### Using Dagger Shell (Interactive)

```bash
# Start the Dagger Shell
dagger

# Run a container
container | from alpine | with-exec echo "Hello Dagger" | stdout

# Build and publish
container | from node:20 | with-directory /app . | \
  with-exec npm install | with-exec npm run build | \
  publish ttl.sh/my-app
```

### Using Python SDK

```python
import dagger

@dagger.function
async def build(source: dagger.Directory) -> dagger.Container:
    """Build a Node.js application."""
    return (
        dag.container()
        .from_("node:20")
        .with_directory("/app", source)
        .with_workdir("/app")
        .with_exec(["npm", "install"])
        .with_exec(["npm", "run", "build"])
    )

@dagger.function
async def test(source: dagger.Directory) -> str:
    """Run tests and return output."""
    return await (
        build(source)
        .with_exec(["npm", "test"])
        .stdout()
    )
```

### Using Go SDK

```go
func (m *MyPipeline) Build(source *dagger.Directory) *dagger.Container {
    return dag.Container().
        From("node:20").
        WithDirectory("/app", source).
        WithWorkdir("/app").
        WithExec([]string{"npm", "install"}).
        WithExec([]string{"npm", "run", "build"})
}
```

### Using TypeScript SDK

```typescript
@func()
async build(source: Directory): Promise<Container> {
    return dag
        .container()
        .from("node:20")
        .withDirectory("/app", source)
        .withWorkdir("/app")
        .withExec(["npm", "install"])
        .withExec(["npm", "run", "build"])
}
```

## Key Concepts Summary

| Concept | Description |
|---------|-------------|
| **Types** | Core building blocks (Container, Directory, File, Secret, Service, CacheVolume) |
| **Functions** | Units of computation that operate on types, written in SDK languages |
| **Modules** | Packages of functions, shareable and composable across languages |
| **Toolchains** | Pre-built module sets for common workflows (Node.js, Python, Go, etc.) |
| **Checks** | Validation functions that run automatically on code changes |
| **Daggerverse** | Community registry for discovering and sharing modules |
| **Dagger Shell** | Interactive CLI for exploring and chaining API calls |
| **Dagger Cloud** | Optional SaaS for telemetry, caching distribution, and tracing |

## When to Use Dagger

- You want portable CI/CD that works locally and in any CI runner
- Your pipelines are complex enough that YAML becomes unmaintainable
- You need to test CI pipelines locally before pushing
- You want type-safe pipeline definitions with IDE support
- Multiple teams use different CI platforms but need consistent pipelines
- You want reusable pipeline components shared across projects

## When NOT to Use Dagger

- Very simple CI (a single `npm test` step) — plain CI YAML may suffice
- Environments without container runtime access
- Serverless CI/CD that doesn't support Docker-in-Docker
- When your team is already happy with their current CI/CD setup and maintenance cost is low

## Common Pitfalls

1. **Forgetting to start Docker**: Dagger needs a container runtime running
2. **Mounting entire host filesystem**: Only pass specific directories as arguments
3. **Ignoring caching**: Not using cache volumes for package managers wastes time
4. **Mixing host and container paths**: Remember that functions run inside containers
5. **Not pinning module versions**: Always use versioned module references in production
