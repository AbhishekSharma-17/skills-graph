# CLI Toolchain

> Source: https://docs.deno.com/runtime/reference/cli/

## Table of Contents

- [Execution Commands](#execution-commands)
- [Development Tools](#development-tools)
- [Dependency Management](#dependency-management)
- [Build and Compile](#build-and-compile)
- [Project Scaffolding](#project-scaffolding)
- [Publishing and Registry](#publishing-and-registry)
- [Utility Commands](#utility-commands)

## Execution Commands

### deno run

Execute a script with specified permissions:

```bash
# Basic execution
deno run main.ts

# With permissions
deno run --allow-net --allow-read server.ts

# Watch mode (restart on changes)
deno run --watch main.ts

# Watch with HMR (hot module replacement)
deno run --watch-hmr main.ts

# Run with type checking
deno run --check main.ts

# Run remote script
deno run https://examples.deno.land/http-server.ts

# Pass arguments to script
deno run main.ts -- --port 3000 --debug
```

### deno serve

Start an HTTP server from a default export:

```typescript
// server.ts
export default {
  fetch(request: Request): Response {
    return new Response("Hello!");
  },
} satisfies Deno.ServeDefaultExport;
```

```bash
# Start server (auto-detects port from export or uses 8000)
deno serve server.ts

# With options
deno serve --port 3000 --parallel server.ts
```

### deno task

Run tasks defined in `deno.json`:

```jsonc
{
  "tasks": {
    "dev": "deno run --watch --allow-all main.ts",
    "build": "deno compile --output=dist/app main.ts",
    "test": "deno test --allow-all --coverage",
    "lint": "deno lint && deno fmt --check"
  }
}
```

```bash
deno task dev
deno task build
deno task test

# List available tasks
deno task

# Run task in a workspace member
deno task --cwd=packages/api dev
```

Task features (v2.9+):
- Input-based caching (skip if inputs unchanged)
- Concurrency flags for parallel execution
- Lifecycle environment variables

### deno eval

Execute code from the command line:

```bash
deno eval "console.log(1 + 2)"
deno eval --print "Deno.version"

# TypeScript
deno eval --ext=ts "const x: number = 42; console.log(x)"
```

### deno repl

Start an interactive session:

```bash
deno repl
deno repl --eval "import { z } from 'npm:zod'"
```

## Development Tools

### deno test

Run tests:

```bash
# Run all tests
deno test

# Run with permissions
deno test --allow-all

# Filter by name
deno test --filter "user creation"

# Specific files
deno test tests/auth_test.ts

# Watch mode
deno test --watch

# Parallel execution
deno test --parallel

# Only changed files (git-aware)
deno test --changed

# Coverage
deno test --coverage=./cov
deno coverage ./cov --lcov > lcov.info

# JUnit output for CI
deno test --reporter=junit > results.xml

# Fail fast
deno test --fail-fast

# Sharding (split across CI machines)
deno test --shard=1/4  # Run 1st quarter of tests
```

### deno bench

Run benchmarks:

```typescript
// bench.ts
Deno.bench("URL parsing", () => {
  new URL("https://example.com/path?query=value");
});

Deno.bench("JSON parse", () => {
  JSON.parse('{"key": "value", "count": 42}');
});
```

```bash
deno bench
deno bench --filter "parse"
```

### deno lint

Lint source code:

```bash
# Lint all files
deno lint

# Specific files/directories
deno lint src/

# Fix auto-fixable issues
deno lint --fix

# JSON output for tooling
deno lint --json

# Check specific rules
deno lint --rules-include=no-unused-vars,no-explicit-any
```

### deno fmt

Format code:

```bash
# Format all files
deno fmt

# Check without modifying (CI)
deno fmt --check

# Specific files
deno fmt src/main.ts

# Configuration options
deno fmt --indent-width=4 --single-quote --line-width=100

# Supported formats: .ts, .tsx, .js, .jsx, .json, .jsonc, .md, .html, .css
```

### deno check

Type-check without running:

```bash
deno check main.ts
deno check --all main.ts      # Include remote deps
deno check src/**/*.ts         # Multiple files
```

### deno doc

Generate documentation:

```bash
# Print docs to terminal
deno doc main.ts

# Generate HTML documentation
deno doc --html --output=docs/ mod.ts

# Lint documentation (check JSDoc coverage)
deno doc --lint mod.ts

# Show docs for a symbol
deno doc main.ts MyClass
```

## Dependency Management

### deno add / deno remove

```bash
# Add packages
deno add jsr:@std/assert
deno add npm:express
deno add jsr:@std/path npm:zod

# Remove packages
deno remove @std/assert
deno remove express
```

### deno install

Install dependencies:

```bash
# Install all deps from deno.json/package.json
deno install

# Install and create node_modules
deno install --node-modules-dir

# Install a global CLI tool
deno install --global --allow-all -n serve jsr:@std/http/file-server

# Force reinstall
deno install --reload
```

### deno outdated

Check and update dependencies:

```bash
# Show outdated packages
deno outdated

# Update all packages
deno outdated --update

# Update specific package
deno outdated --update npm:zod
```

### deno audit

Security vulnerability scanning:

```bash
# Check for vulnerabilities
deno audit

# Auto-fix by upgrading to patched versions
deno audit fix
```

### deno ci

CI-safe dependency installation:

```bash
# Fails if deno.lock is stale or missing
deno ci
```

### deno why

Explain dependency presence:

```bash
deno why npm:some-transitive-dep
```

### deno info

Module and dependency inspection:

```bash
# Show dependency tree
deno info main.ts

# Machine-readable output
deno info --json main.ts

# Show cache info
deno info
```

## Build and Compile

### deno compile

Create standalone executables:

```bash
# Basic compilation
deno compile --allow-net --allow-read server.ts

# Specify output path
deno compile --output=dist/myapp main.ts

# Cross-compile for other platforms
deno compile --target=x86_64-unknown-linux-gnu main.ts
deno compile --target=x86_64-pc-windows-msvc main.ts
deno compile --target=aarch64-apple-darwin main.ts

# Include files in binary
deno compile --include=./assets --include=./config main.ts

# Produce installer (v2.9+)
deno compile --output=dist/app.deb main.ts  # Linux .deb
deno compile --output=dist/app.msi main.ts  # Windows .msi
```

Available targets:
- `x86_64-unknown-linux-gnu`
- `aarch64-unknown-linux-gnu`
- `x86_64-pc-windows-msvc`
- `x86_64-apple-darwin`
- `aarch64-apple-darwin`

### deno pack

Create npm-compatible tarball:

```bash
deno pack  # Generates .tgz for publishing to npm
```

## Project Scaffolding

### deno init

Bootstrap a new project:

```bash
# Create in current directory
deno init

# Create in new directory
deno init my-project

# Create with specific template
deno init --lib  # Library project
```

### deno create

Generate from templates:

```bash
# Create from a template
deno create fresh my-fresh-app
deno create vite my-vite-app
```

## Publishing and Registry

### deno publish

Publish to JSR:

```bash
# Publish (requires JSR account)
deno publish

# Dry run
deno publish --dry-run

# Allow slow types (less strict)
deno publish --allow-slow-types
```

### deno bump-version

Increment package version:

```bash
deno bump-version patch  # 1.0.0 -> 1.0.1
deno bump-version minor  # 1.0.0 -> 1.1.0
deno bump-version major  # 1.0.0 -> 2.0.0
```

## Utility Commands

### deno jupyter

Run as Jupyter kernel:

```bash
# Install kernel
deno jupyter --install

# Start Jupyter with Deno kernel available
jupyter notebook
```

### deno coverage

Generate coverage reports:

```bash
deno test --coverage=./cov
deno coverage ./cov              # Print summary
deno coverage ./cov --lcov       # LCOV format
deno coverage ./cov --html       # HTML report
```

### deno upgrade

Update Deno:

```bash
deno upgrade             # Latest stable
deno upgrade --canary    # Latest canary build
deno upgrade --version 2.8.0  # Specific version
```

### deno completions

Shell completion scripts:

```bash
deno completions bash > /etc/bash_completion.d/deno
deno completions zsh > ~/.zsh/completions/_deno
deno completions fish > ~/.config/fish/completions/deno.fish
```

### deno x (dx)

Execute package binaries (like npx):

```bash
# Run a JSR or npm binary
deno x jsr:@std/http/file-server
deno x npm:eslint .
deno x npm:prettier --check .
```

## Common Pitfalls

1. **Forgetting permissions** — `deno run` without flags denies everything
2. **--watch vs --watch-hmr** — HMR preserves state, watch does full restart
3. **deno task vs npm scripts** — task runner uses its own shell syntax (cross-platform)
4. **Global installs** — require `--global` flag explicitly
5. **Compile targets** — must match the deployment platform architecture
