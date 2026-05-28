# Turborepo — Overview & Setup

> Source: [turborepo.dev/docs](https://turborepo.dev/docs) | Package: `turbo` v2.9.x

## What Is Turborepo

Turborepo is a high-performance build system for JavaScript and TypeScript monorepos, written in Rust. It orchestrates tasks across multiple packages in a single repository, using content-aware caching to skip work that has already been done.

Built and maintained by Vercel, Turborepo is used by Netflix, Airbnb, Microsoft, and thousands of open-source projects. It works with any package manager (npm, yarn, pnpm, bun) and integrates with your existing `package.json` scripts.

## When to Use Turborepo

**Use Turborepo when:**
- You manage multiple packages (apps, libraries, configs) in one repo
- Build times are growing as you add packages
- You want to share code between apps without publishing to npm
- CI pipelines rebuild unchanged packages unnecessarily
- Teams need consistent tooling across multiple projects

**Don't use Turborepo when:**
- You have a single package with no workspace structure
- You need a full-featured monorepo tool with project graph visualization (consider Nx)
- Your project is not JavaScript/TypeScript

## Core Concepts

### Task Orchestration
Turborepo reads your `turbo.json` to understand task dependencies and runs them in the correct order with maximum parallelism.

### Content-Aware Caching
Every task's output is cached based on a hash of its inputs (source files, environment variables, dependency versions). When inputs haven't changed, Turborepo replays the cached output — turning minutes-long builds into milliseconds.

### Workspaces
Turborepo builds on your package manager's workspace protocol. Packages declared in your root `package.json` workspaces field are automatically discovered.

### Remote Caching
Cache artifacts can be shared across machines (CI, teammates) via Vercel Remote Cache or a self-hosted server, so no one rebuilds what someone else already built.

## Installation

### New Monorepo

```bash
npx create-turbo@latest
```

This scaffolds a monorepo with:
- Two apps (`apps/web`, `apps/docs`)
- Shared packages (`packages/ui`, `packages/eslint-config`, `packages/typescript-config`)
- A root `turbo.json` with common tasks
- Package manager workspace configuration

### Add to Existing Monorepo

```bash
# Install as dev dependency at the workspace root
npm install turbo --save-dev

# Create turbo.json
cat > turbo.json << 'EOF'
{
  "$schema": "https://turborepo.dev/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "!.next/cache/**"]
    },
    "lint": {
      "dependsOn": ["^build"]
    },
    "test": {
      "dependsOn": ["^build"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
EOF
```

### Verify Installation

```bash
# Check turbo is available
npx turbo --version

# Run all build tasks
npx turbo run build

# Run multiple tasks
npx turbo run build lint test
```

## Minimal turbo.json

```jsonc
{
  "$schema": "https://turborepo.dev/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],       // Run dependencies' build first
      "outputs": ["dist/**"]         // Cache these output files
    },
    "test": {
      "dependsOn": ["^build"]        // Ensure libs are built before testing
    },
    "lint": {},                       // No dependencies, run in parallel
    "dev": {
      "cache": false,                // Never cache dev server
      "persistent": true             // Long-running process
    }
  }
}
```

## Minimum Root package.json

```json
{
  "name": "my-monorepo",
  "private": true,
  "packageManager": "pnpm@9.15.0",
  "workspaces": ["apps/*", "packages/*"],
  "devDependencies": {
    "turbo": "^2.9.0"
  },
  "scripts": {
    "build": "turbo run build",
    "dev": "turbo run dev",
    "lint": "turbo run lint",
    "test": "turbo run test"
  }
}
```

**Note:** Turborepo 2.x requires the `packageManager` field in your root `package.json`. This tells Turborepo which package manager (and version) to expect.

## Directory Structure Convention

```
my-monorepo/
├── turbo.json                 # Turborepo configuration
├── package.json               # Root package.json with workspaces
├── pnpm-workspace.yaml        # (pnpm only) workspace config
├── apps/
│   ├── web/                   # Next.js application
│   │   ├── package.json
│   │   └── src/
│   └── api/                   # Backend service
│       ├── package.json
│       └── src/
├── packages/
│   ├── ui/                    # Shared component library
│   │   ├── package.json
│   │   └── src/
│   ├── utils/                 # Shared utilities
│   │   ├── package.json
│   │   └── src/
│   └── tsconfig/              # Shared TypeScript configs
│       ├── package.json
│       └── base.json
└── .gitignore
```

## How Caching Works (Simplified)

1. You run `turbo run build`
2. Turborepo hashes each task's inputs: source files, env vars, dependency outputs
3. If a matching hash exists in cache → replay outputs (instant)
4. If no match → run the task, store outputs in `.turbo/cache`

```
$ turbo run build

 Tasks:    4 successful, 4 total
 Cached:   3 cached, 4 total           # 3 out of 4 were cache hits
   Time:   432ms >>> FULL TURBO         # Near-instant
```

## Package Manager Support

| Manager | Workspace Config | Notes |
|---------|-----------------|-------|
| **npm** | `package.json` workspaces field | Built-in since npm 7 |
| **pnpm** | `pnpm-workspace.yaml` | Recommended for large repos |
| **yarn** | `package.json` workspaces field | Classic and Berry supported |
| **bun** | `package.json` workspaces field | Supported since Turborepo 2.x |

## Upgrading Turborepo

```bash
# Automatic upgrade with codemods
npx @turbo/codemod migrate

# Manual version bump
npm install turbo@latest --save-dev
```

The `migrate` codemod handles breaking changes between major versions (e.g., `pipeline` → `tasks` in v2.0).

## Related

- [Configuration](01-configuration.md) — Full turbo.json reference
- [Caching](02-caching.md) — Deep dive into caching behavior
- [Workspace Structure](04-workspace-structure.md) — Organizing apps and packages
