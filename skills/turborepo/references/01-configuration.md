# Turborepo — Configuration (turbo.json)

> Source: [turborepo.dev/docs/reference/configuration](https://turborepo.dev/docs/reference/configuration)

## Table of Contents

- [Root turbo.json](#root-turbojson)
- [Tasks Configuration](#tasks-configuration)
- [Task Dependencies (dependsOn)](#task-dependencies-dependson)
- [Inputs and Outputs](#inputs-and-outputs)
- [Cache Control](#cache-control)
- [Package Configurations](#package-configurations)
- [Global Configuration](#global-configuration)
- [Full Schema Reference](#full-schema-reference)

## Root turbo.json

Every Turborepo monorepo has a `turbo.json` at the repository root, next to the root `package.json`. This file defines tasks and their relationships.

```jsonc
{
  "$schema": "https://turborepo.dev/schema.json",
  "globalDependencies": ["tsconfig.json"],
  "globalEnv": ["NODE_ENV", "CI"],
  "tasks": {
    // Task definitions go here
  }
}
```

The `$schema` key enables IDE autocompletion and validation.

## Tasks Configuration

Each key in the `tasks` object maps to a script name in your packages' `package.json` files. Turborepo only runs a task in a package if that package has a matching script.

```jsonc
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "tsconfig.json"],
      "outputs": ["dist/**"],
      "outputLogs": "new-only"
    },
    "test": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "test/**"],
      "outputs": [],
      "outputLogs": "full"
    },
    "lint": {
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

## Task Dependencies (dependsOn)

The `dependsOn` key defines what must complete before a task runs.

### Topological Dependencies (`^`)

The `^` prefix means "run this task in all dependencies first":

```jsonc
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"]
      // Before building `apps/web`, build all packages it depends on
    }
  }
}
```

### Same-Package Dependencies

Without `^`, the dependency is within the same package:

```jsonc
{
  "tasks": {
    "test": {
      "dependsOn": ["build"]
      // Run `build` in THIS package before `test`
    }
  }
}
```

### Cross-Package Dependencies

Reference specific packages with `package#task`:

```jsonc
{
  "tasks": {
    "deploy": {
      "dependsOn": ["ui#build", "utils#build"]
      // Wait for specific packages to build
    }
  }
}
```

### No Dependencies

Omit `dependsOn` or set it to `[]` to run the task without waiting:

```jsonc
{
  "tasks": {
    "lint": {}  // Runs immediately, no dependencies
  }
}
```

## Inputs and Outputs

### inputs

Defines which files Turborepo considers when computing the task hash. Only changes to these files cause cache misses.

```jsonc
{
  "tasks": {
    "build": {
      "inputs": [
        "src/**",
        "tsconfig.json",
        "package.json",
        "!src/**/*.test.ts"    // Exclude test files
      ]
    }
  }
}
```

Default behavior (no `inputs` key): all files in the package are considered inputs, minus those in `.gitignore`.

### outputs

Defines which files/directories Turborepo caches after a successful task run.

```jsonc
{
  "tasks": {
    "build": {
      "outputs": [
        "dist/**",
        ".next/**",
        "!.next/cache/**"       // Exclude Next.js internal cache
      ]
    },
    "lint": {
      "outputs": []              // Nothing to cache (side-effect only)
    }
  }
}
```

Glob patterns:
- `dist/**` — all files recursively in `dist/`
- `!dist/temp/**` — exclude specific paths
- `dist` or `dist/` — equivalent to `dist/**`

## Cache Control

### Disabling Cache

```jsonc
{
  "tasks": {
    "dev": {
      "cache": false          // Never cache this task
    }
  }
}
```

### Persistent Tasks

Long-running processes (dev servers, watchers) must be marked persistent:

```jsonc
{
  "tasks": {
    "dev": {
      "cache": false,
      "persistent": true      // Does not exit on its own
    }
  }
}
```

Persistent tasks cannot be depended on by other tasks.

### Interactive Tasks

For tasks that require stdin (e.g., prompts):

```jsonc
{
  "tasks": {
    "setup": {
      "interactive": true     // Enables stdin passthrough
    }
  }
}
```

### Output Logging

Control how task output is displayed:

```jsonc
{
  "tasks": {
    "build": {
      "outputLogs": "new-only"    // Only show output for cache misses
    }
  }
}
```

Values: `"full"` (default), `"hash-only"`, `"new-only"`, `"errors-only"`, `"none"`

## Package Configurations

Individual packages can extend or override root `turbo.json` with their own `turbo.json`:

```jsonc
// packages/ui/turbo.json
{
  "$schema": "https://turborepo.dev/schema.json",
  "extends": ["//"],              // Inherit from root turbo.json
  "tasks": {
    "build": {
      "outputs": ["dist/**", "styles.css"]   // Override outputs for this package
    }
  }
}
```

The `"extends": ["//"]` line means "inherit all task definitions from root, then apply overrides."

Package-level `turbo.json` can only modify tasks — not global configuration like `globalEnv`.

## Global Configuration

### globalDependencies

Files that, when changed, invalidate ALL task caches:

```jsonc
{
  "globalDependencies": [
    "tsconfig.json",
    ".env"
  ]
}
```

### globalEnv

Environment variables included in ALL task hashes:

```jsonc
{
  "globalEnv": ["NODE_ENV", "CI", "VERCEL"]
}
```

### globalPassThroughEnv

Variables available at runtime but NOT included in hashes:

```jsonc
{
  "globalPassThroughEnv": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
}
```

## Full Schema Reference

```jsonc
{
  "$schema": "https://turborepo.dev/schema.json",

  // Global settings
  "globalDependencies": [],         // Files that bust all caches
  "globalEnv": [],                  // Env vars in all hashes
  "globalPassThroughEnv": [],       // Env vars available but not hashed

  // Task definitions
  "tasks": {
    "<task-name>": {
      "dependsOn": [],              // Task dependencies
      "env": [],                    // Per-task env vars for hash
      "passThroughEnv": [],         // Per-task env vars (not hashed)
      "inputs": [],                 // Files considered for hash
      "outputs": [],                // Files to cache
      "cache": true,                // Enable/disable cache
      "persistent": false,          // Long-running task
      "interactive": false,         // Needs stdin
      "outputLogs": "full"          // Log verbosity
    }
  },

  // UI mode for terminal output
  "ui": "stream"                    // "stream" or "tui"
}
```

## Common Pitfalls

1. **Forgetting `^` in dependsOn** — Without `^`, `"dependsOn": ["build"]` means "run build in THIS package first," not "build dependencies first."

2. **Missing outputs** — If you don't specify `outputs`, Turborepo caches nothing. Cache hits will replay logs but not restore files.

3. **Caching dev servers** — Always set `"cache": false` and `"persistent": true` for dev tasks.

4. **Not setting packageManager** — Turborepo 2.x requires the `packageManager` field in root `package.json`.

## Related

- [Caching](02-caching.md) — How caching works in detail
- [Environment Variables](05-environment-variables.md) — Env var configuration
- [Running Tasks](06-running-tasks.md) — CLI usage and filtering
