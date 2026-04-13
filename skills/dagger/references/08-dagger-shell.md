# Dagger Shell

> Source: https://docs.dagger.io/features/shell | Version: 0.20.x

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
- [Pipe Operator](#pipe-operator)
- [Core Commands](#core-commands)
- [Working with Containers](#working-with-containers)
- [Working with Directories](#working-with-directories)
- [Subshells and Variables](#subshells-and-variables)
- [Interactive Debugging](#interactive-debugging)
- [Shell vs CLI](#shell-vs-cli)
- [Common Pitfalls](#common-pitfalls)

## Overview

Dagger Shell is an interactive Bash-like environment for exploring and chaining Dagger API calls. It provides autocomplete, pipe operators, and a familiar shell experience for building and testing pipelines interactively.

Key features:
- Bash-like syntax with pipe operator (`|`)
- Autocomplete for Dagger API methods
- Interactive container terminal access
- Subshell support for complex compositions
- Direct access to Dagger modules and functions

## Getting Started

```bash
# Start interactive Dagger Shell
dagger

# Run a single shell command
dagger shell 'container | from alpine | with-exec echo hello | stdout'

# Run from a script file
dagger shell < pipeline.sh
```

## Pipe Operator

The pipe operator (`|`) chains Dagger API calls, passing the result of one call as the receiver of the next:

```bash
# Each | chains the next method call on the returned object
container | from alpine | with-exec uname -a | stdout
# Equivalent to: dag.container().from_("alpine").with_exec(["uname", "-a"]).stdout()
```

### Multi-line Pipes

```bash
container \
  | from python:3.12 \
  | with-directory /app . \
  | with-workdir /app \
  | with-exec pip install -r requirements.txt \
  | with-exec pytest -v \
  | stdout
```

## Core Commands

### Container Operations

```bash
# Create from base image
container | from alpine

# Execute commands
container | from alpine | with-exec echo "Hello"

# Get stdout
container | from alpine | with-exec cat /etc/os-release | stdout

# Get stderr
container | from alpine | with-exec ls /nonexistent | stderr

# Build from Dockerfile
container | build .
container | build . --dockerfile Dockerfile.prod
```

### Directory Operations

```bash
# List directory entries
directory | entries

# Read a file
directory | file README.md | contents

# Get from Git
git https://github.com/dagger/dagger | branch main | tree | entries
```

### Module Functions

```bash
# Call functions from current module
my-pipeline | build --source=.
my-pipeline | test --source=.

# Call functions from remote modules
github.com/user/module@v1.0 | build --source=.
```

## Working with Containers

### Building Images

```bash
# Multi-step build
container \
  | from node:20 \
  | with-directory /app . \
  | with-workdir /app \
  | with-exec npm ci \
  | with-exec npm run build

# Publish to registry
container \
  | from node:20 \
  | with-directory /app . \
  | with-exec npm ci \
  | with-exec npm run build \
  | publish ttl.sh/my-app:latest
```

### Environment and Configuration

```bash
# Set environment variables
container | from alpine \
  | with-env-variable NODE_ENV production \
  | with-env-variable PORT 8080

# Set entrypoint
container | from python:3.12 \
  | with-entrypoint python -m app

# Set working directory
container | from node:20 | with-workdir /app
```

### Cache Volumes

```bash
container | from python:3.12 \
  | with-mounted-cache /root/.cache/pip $(cache-volume pip-cache) \
  | with-exec pip install flask
```

## Working with Directories

### Host Directories

```bash
# Current directory
directory | entries

# Specific subdirectory
directory src | entries

# Files
directory | file package.json | contents
```

### Creating Files

```bash
container | from alpine \
  | with-new-file /hello.txt "Hello from Dagger Shell!" \
  | with-exec cat /hello.txt \
  | stdout
```

### Filtering

```bash
# Exclude paths
directory | without-directory node_modules | without-file .env | entries
```

## Subshells and Variables

### Subshells

Use `$()` for subshell expressions:

```bash
# Use a built container as a base for another step
container | from $(container | from node:20 | with-exec npm -g install typescript) \
  | with-exec tsc --version | stdout
```

### Combining Commands

```bash
# Build and then test in separate containers
container | from python:3.12 \
  | with-directory /app . \
  | with-exec pip install -r requirements.txt \
  | with-exec pytest -v \
  | stdout
```

## Interactive Debugging

### Terminal Access

Open an interactive terminal inside any container state:

```bash
# Debug a build step
container | from python:3.12 \
  | with-directory /app . \
  | with-exec pip install -r requirements.txt \
  | terminal

# You're now inside the container — inspect, debug, test
# Exit with Ctrl+D or 'exit'
```

### Inspecting State

```bash
# Check what files exist
container | from alpine | with-directory /app . \
  | with-exec ls -la /app | stdout

# Check environment
container | from alpine | with-exec env | stdout

# Check installed packages
container | from python:3.12 | with-exec pip list | stdout
```

## Shell vs CLI

| Feature | Dagger Shell | Dagger CLI |
|---------|-------------|------------|
| Syntax | Pipe-based (`\|`) | Subcommand-based (`call`) |
| Interactive | Yes | No |
| Autocomplete | Yes | Basic |
| Debugging | `terminal` command | `--debug` flag |
| Scripting | Shell scripts | Module functions |
| Use case | Exploration, prototyping | CI/CD, automation |

### When to Use Shell
- Exploring the Dagger API interactively
- Prototyping pipeline steps before writing module code
- Debugging container state with `terminal`
- Quick one-off tasks

### When to Use CLI
- CI/CD pipelines
- Automated workflows
- Calling module functions with typed arguments
- Production deployments

## Common Pitfalls

1. **Quoting arguments**: Multi-word arguments need quoting: `with-exec "echo hello world"`
2. **Pipe vs shell pipe**: Dagger `|` is not a Unix pipe — it chains API methods
3. **Missing `stdout`**: Without `stdout` at the end, command output isn't displayed
4. **Shell not found**: Ensure Dagger CLI is installed and in your PATH
5. **Docker not running**: Dagger Shell requires a container runtime
