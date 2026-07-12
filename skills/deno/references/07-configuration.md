# Configuration

> Source: https://docs.deno.com/runtime/fundamentals/configuration/

## Table of Contents

- [deno.json Overview](#denojson-overview)
- [Import Maps](#import-maps)
- [Tasks](#tasks)
- [Compiler Options](#compiler-options)
- [Linting Configuration](#linting-configuration)
- [Formatting Configuration](#formatting-configuration)
- [Testing Configuration](#testing-configuration)
- [Workspaces](#workspaces)
- [Lock Files](#lock-files)
- [Node Modules Directory](#node-modules-directory)
- [Permissions in Config](#permissions-in-config)

## deno.json Overview

`deno.json` (or `deno.jsonc` for comments) is the single configuration file for Deno's entire toolchain. It replaces `tsconfig.json`, `.eslintrc`, `.prettierrc`, and parts of `package.json`.

```jsonc
{
  // Package identity (for publishing to JSR)
  "name": "@myorg/my-package",
  "version": "1.0.0",

  // Import map (dependencies)
  "imports": {
    "@std/assert": "jsr:@std/assert@^1.0.0",
    "zod": "npm:zod@^3.23.0"
  },

  // Tasks (like npm scripts)
  "tasks": {
    "dev": "deno run --watch --allow-all main.ts",
    "start": "deno run --allow-net --allow-read main.ts",
    "test": "deno test --allow-all"
  },

  // TypeScript compiler options
  "compilerOptions": {
    "jsx": "react-jsx",
    "jsxImportSource": "react"
  },

  // Linter configuration
  "lint": {
    "rules": {
      "exclude": ["no-unused-vars"]
    }
  },

  // Formatter configuration
  "fmt": {
    "indentWidth": 2,
    "singleQuote": false,
    "lineWidth": 80
  },

  // Module exports (for published packages)
  "exports": "./mod.ts",

  // File inclusion/exclusion
  "exclude": ["dist/", "coverage/", "node_modules/"]
}
```

### Configuration Precedence

CLI flags > `deno.json` > `.editorconfig` > built-in defaults

### File Discovery

Deno auto-discovers `deno.json` or `deno.jsonc` by walking up from the current directory. You can also specify explicitly:

```bash
deno run --config=path/to/deno.json main.ts
```

## Import Maps

The `imports` field defines a mapping from bare specifiers to versioned packages:

```jsonc
{
  "imports": {
    // JSR packages
    "@std/assert": "jsr:@std/assert@^1.0.0",
    "@std/path": "jsr:@std/path@^1.0.0",
    "@std/http": "jsr:@std/http@^1.0.0",

    // npm packages
    "zod": "npm:zod@^3.23.0",
    "hono": "npm:hono@^4.0.0",
    "drizzle-orm": "npm:drizzle-orm@^0.33.0",

    // Path aliases
    "@/": "./src/",
    "#db": "./src/lib/database.ts",
    "#config": "./src/config.ts"
  }
}
```

### Scoped Imports

```jsonc
{
  "imports": {
    // Map all @std/ packages
    "@std/": "jsr:@std/"
  }
}
```

### Catalog Protocol (v2.8+)

For workspaces, share dependency versions via a catalog:

```jsonc
{
  "catalog": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "workspace": ["./apps/web", "./packages/ui"]
}
```

Members reference: `"react": "catalog:"` in their `package.json`.

## Tasks

Define command shortcuts similar to npm scripts:

```jsonc
{
  "tasks": {
    // Simple commands
    "dev": "deno run --watch --allow-all main.ts",
    "start": "deno run --allow-net --allow-env main.ts",
    "test": "deno test --allow-all --coverage",
    "check": "deno check main.ts",

    // Chained commands
    "ci": "deno ci && deno fmt --check && deno lint && deno test --allow-all",

    // With environment variables
    "dev:db": "DATABASE_URL=postgres://localhost/dev deno run --allow-all server.ts",

    // Cross-platform pipe
    "coverage": "deno test --coverage=./cov && deno coverage ./cov --lcov > lcov.info",

    // Using deno x for package binaries
    "migrate": "deno x npm:drizzle-kit migrate"
  }
}
```

### Task Shell Syntax

Deno's task runner uses its own cross-platform shell supporting:
- `&&` — sequential execution (fail on error)
- `||` — fallback on error
- `|` — piping
- `>` / `>>` — output redirection
- `$(command)` — command substitution
- Environment variable expansion: `$PORT`, `${PORT:-8000}`

### Running Tasks

```bash
deno task dev
deno task test
deno task ci

# List available tasks
deno task

# Run a workspace member's task
deno task --cwd=packages/api dev
```

## Compiler Options

TypeScript configuration within `deno.json`:

```jsonc
{
  "compilerOptions": {
    // JSX (for React/Preact)
    "jsx": "react-jsx",
    "jsxImportSource": "react",

    // Strictness (all true by default)
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    // Decorators
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,

    // Library (rarely needed)
    "lib": ["deno.window", "dom"]
  }
}
```

## Linting Configuration

```jsonc
{
  "lint": {
    // Include/exclude patterns
    "include": ["src/"],
    "exclude": ["src/generated/"],

    // Rule configuration
    "rules": {
      // Disable specific rules
      "exclude": ["no-unused-vars", "require-await"],

      // Enable additional rules beyond recommended
      "include": ["ban-untagged-todo", "no-console"],

      // Use specific rule tags
      "tags": ["recommended"]
    },

    // Lint plugins (v2.8+)
    "plugins": ["./lint-rules/no-magic-numbers.ts"]
  }
}
```

### Inline Ignore Directives

```typescript
// deno-lint-ignore no-explicit-any
const data: any = {};

// deno-lint-ignore no-unused-vars
const _unused = "placeholder";

// Ignore for next line
// deno-lint-ignore no-console
console.log("debug");
```

## Formatting Configuration

```jsonc
{
  "fmt": {
    // Include/exclude
    "include": ["src/"],
    "exclude": ["src/generated/"],

    // Formatting options
    "useTabs": false,
    "indentWidth": 2,
    "lineWidth": 80,
    "singleQuote": false,
    "proseWrap": "always",
    "semiColons": true
  }
}
```

## Testing Configuration

```jsonc
{
  "test": {
    // Include/exclude test files
    "include": ["tests/", "src/**/*_test.ts"],
    "exclude": ["tests/fixtures/"]
  }
}
```

## Workspaces

Define a monorepo with multiple packages:

```jsonc
// Root deno.json
{
  "workspace": ["./packages/core", "./packages/cli", "./apps/web"],

  // Shared dependencies
  "imports": {
    "@std/assert": "jsr:@std/assert@^1.0.0",
    "zod": "npm:zod@^3.23.0"
  },

  // Workspace-level tasks
  "tasks": {
    "test:all": "deno test --allow-all",
    "lint:all": "deno lint"
  }
}
```

```jsonc
// packages/core/deno.json
{
  "name": "@myorg/core",
  "version": "1.0.0",
  "exports": "./mod.ts"
}
```

### Pattern Matching

```jsonc
{
  "workspace": [
    "packages/*",       // First-level directories
    "apps/**",          // Recursive
    "!packages/legacy"  // Exclude
  ]
}
```

### Inter-Workspace Imports

Members can import from each other using their `name`:

```typescript
// In apps/web/main.ts
import { validate } from "@myorg/core";
```

### Publishing Workspace Members

```bash
# Publish a specific member
cd packages/core
deno publish

# Opt out of publishing
// In packages/internal/deno.json
{ "publish": false }
```

## Lock Files

```jsonc
{
  // Default: true (auto-generate deno.lock)
  "lock": true,

  // Disable lock file
  "lock": false,

  // Custom path
  "lock": "./deps.lock"
}
```

### CI Usage

```bash
# Install from lock file (fails if out of date)
deno ci

# Regenerate lock file
deno install --lock-write
```

## Node Modules Directory

Control how `node_modules` is managed:

```jsonc
{
  // No local node_modules (default — uses global cache)
  "nodeModulesDir": "none",

  // Auto-create node_modules on install
  "nodeModulesDir": "auto",

  // Manual: require explicit deno install
  "nodeModulesDir": "manual"
}
```

### Linker Strategy

```jsonc
{
  "nodeModulesDir": "auto",
  // pnpm-style isolated layout (default)
  "nodeModulesLinker": "isolated",
  // npm-style hoisted layout (for compat)
  "nodeModulesLinker": "hoisted"
}
```

## Permissions in Config

Set default permissions for `deno run`:

```jsonc
{
  "permissions": {
    "allow-net": ["api.example.com:443"],
    "allow-read": ["./data", "./config"],
    "allow-env": ["DATABASE_URL", "PORT"],
    "deny-write": ["/etc", "/usr"]
  }
}
```

## File Exclusion

Global exclude applies to all tools (lint, fmt, test, etc.):

```jsonc
{
  "exclude": [
    "node_modules/",
    "dist/",
    "coverage/",
    ".git/",
    "*.generated.ts"
  ]
}
```

## Common Pitfalls

1. **deno.json vs package.json** — use `deno.json` for Deno tooling, `package.json` for npm compatibility
2. **Trailing slash in imports** — `"@/": "./src/"` maps a directory; `"@/lib": "./src/lib.ts"` maps a file
3. **Workspace member priority** — member tasks override root tasks of the same name
4. **Lock file in CI** — always use `deno ci` (not `deno install`) for reproducible builds
5. **JSONC support** — use `.jsonc` extension if you want comments and trailing commas
