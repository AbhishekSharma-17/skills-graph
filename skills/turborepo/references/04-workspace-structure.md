# Turborepo — Workspace Structure

> Source: [turborepo.dev/docs/crafting-your-repository/structuring-a-repository](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository)

## Table of Contents

- [Directory Conventions](#directory-conventions)
- [Internal Packages](#internal-packages)
- [Creating an Internal Package](#creating-an-internal-package)
- [Package Types](#package-types)
- [Managing Dependencies](#managing-dependencies)
- [Shared Configurations](#shared-configurations)
- [Common Pitfalls](#common-pitfalls)

## Directory Conventions

Turborepo uses your package manager's workspace feature to discover packages. The conventional structure splits packages into two top-level directories:

```
my-monorepo/
├── apps/           # Deployable applications and services
│   ├── web/        # Next.js frontend
│   ├── api/        # Express/Fastify backend
│   └── mobile/     # React Native app
├── packages/       # Shared libraries and configs
│   ├── ui/         # Component library
│   ├── utils/      # Shared utilities
│   ├── db/         # Database client and schemas
│   ├── eslint-config/   # Shared ESLint config
│   └── tsconfig/        # Shared TypeScript config
├── turbo.json
├── package.json
└── pnpm-workspace.yaml  # (pnpm only)
```

### Root package.json

```json
{
  "name": "my-monorepo",
  "private": true,
  "packageManager": "pnpm@9.15.0",
  "workspaces": ["apps/*", "packages/*"]
}
```

### pnpm-workspace.yaml (pnpm only)

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

## Internal Packages

Internal packages are packages within your monorepo that are consumed by other packages but not published to npm. They are the primary mechanism for sharing code in a Turborepo monorepo.

### Compilation Strategies

There are three strategies for how internal packages make their code available:

#### 1. Just-in-Time (JIT) Packages — Recommended

The consuming application (e.g., Next.js) compiles the package at build time. No separate build step needed.

```jsonc
// packages/ui/package.json
{
  "name": "@repo/ui",
  "exports": {
    ".": "./src/index.ts"     // Point directly to TypeScript source
  }
}
```

**Pros:** Simplest setup, no build step, instant changes in dev
**Cons:** Requires the consuming bundler to support TypeScript transpilation

#### 2. Compiled Packages

The package has its own build step that produces compiled output:

```jsonc
// packages/ui/package.json
{
  "name": "@repo/ui",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "default": "./dist/index.js"
    }
  },
  "scripts": {
    "build": "tsc --build"
  }
}
```

**Pros:** Works with any consumer, faster consumer builds
**Cons:** Requires `^build` dependency in turbo.json, slower dev iteration

#### 3. Publishable Packages

Packages intended for npm publication with full build and versioning:

```jsonc
// packages/ui/package.json
{
  "name": "@myorg/ui",
  "version": "1.2.3",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.mjs",
      "require": "./dist/index.cjs"
    }
  }
}
```

## Creating an Internal Package

### Step-by-Step

1. Create the directory and package.json:

```bash
mkdir -p packages/utils
```

```json
// packages/utils/package.json
{
  "name": "@repo/utils",
  "private": true,
  "type": "module",
  "exports": {
    ".": "./src/index.ts"
  },
  "devDependencies": {
    "typescript": "^5.6.0"
  }
}
```

2. Create source files:

```typescript
// packages/utils/src/index.ts
export function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

export function slugify(text: string): string {
  return text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
}
```

3. Add tsconfig.json (if using compiled strategy):

```json
// packages/utils/tsconfig.json
{
  "extends": "@repo/tsconfig/base.json",
  "compilerOptions": {
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

4. Install in a consuming app:

```bash
# pnpm
pnpm add @repo/utils --filter @repo/web --workspace

# npm
npm install @repo/utils -w apps/web

# yarn
yarn workspace @repo/web add @repo/utils
```

5. Use in the consuming app:

```typescript
// apps/web/src/page.tsx
import { formatDate, slugify } from '@repo/utils';
```

### Using turbo gen

Automate workspace creation:

```bash
npx turbo gen workspace
```

This runs an interactive prompt to scaffold a new package with the correct structure.

## Package Types

### Application Packages (`apps/`)

- Deployable (web apps, APIs, mobile apps)
- Usually not imported by other packages
- Have their own build/dev/test scripts
- Examples: Next.js app, Express API, Electron app

### Library Packages (`packages/`)

- Shared code consumed by apps and other packages
- May or may not have build scripts (JIT vs compiled)
- Examples: UI component library, shared utilities, API clients

### Configuration Packages (`packages/`)

- Share tooling configuration across packages
- Typically no build step
- Examples: ESLint config, TypeScript config, Prettier config

## Managing Dependencies

### Internal Dependencies

Use your package manager's workspace protocol:

```jsonc
// apps/web/package.json
{
  "dependencies": {
    "@repo/ui": "workspace:*",       // pnpm/yarn
    "@repo/utils": "*"               // npm (resolved via workspaces)
  }
}
```

### External Dependencies

Install dependencies in the package that uses them, not at the root:

```bash
# Install React in the web app
pnpm add react react-dom --filter @repo/web

# Install in a specific package
pnpm add zod --filter @repo/utils
```

**Root-level devDependencies** are appropriate for monorepo-wide tools:

```json
// Root package.json
{
  "devDependencies": {
    "turbo": "^2.9.0",
    "prettier": "^3.0.0"
  }
}
```

### Version Consistency

To enforce consistent external dependency versions across packages, use your package manager's features:

- **pnpm:** `pnpm.overrides` in root `package.json`
- **yarn:** `resolutions` in root `package.json`
- **npm:** `overrides` in root `package.json`

```json
{
  "pnpm": {
    "overrides": {
      "react": "^19.0.0",
      "typescript": "^5.6.0"
    }
  }
}
```

## Shared Configurations

### TypeScript Config Package

```json
// packages/tsconfig/package.json
{
  "name": "@repo/tsconfig",
  "private": true,
  "files": ["base.json", "nextjs.json", "react-library.json"]
}
```

```json
// packages/tsconfig/base.json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  }
}
```

Usage in packages:

```json
// packages/ui/tsconfig.json
{
  "extends": "@repo/tsconfig/react-library.json",
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### ESLint Config Package

```json
// packages/eslint-config/package.json
{
  "name": "@repo/eslint-config",
  "private": true,
  "exports": {
    "./next": "./next.js",
    "./library": "./library.js"
  }
}
```

## Common Pitfalls

1. **Installing dependencies at root instead of per-package** — This defeats Turborepo's ability to prune unused dependencies and makes `turbo prune` less effective for Docker builds.

2. **Circular dependencies** — Package A depends on B which depends on A. Turborepo will error. Restructure by extracting shared code into a third package.

3. **Forgetting workspace protocol** — When adding internal deps, use `workspace:*` (pnpm/yarn) to ensure the local version is used.

4. **Missing package.json exports** — Without the `exports` field, consumers may not be able to import from your package correctly.

5. **Inconsistent TypeScript versions** — Different packages using different TS versions causes type incompatibilities. Pin with overrides.

## Related

- [Overview](00-overview.md) — Monorepo directory structure
- [Configuration](01-configuration.md) — Package-level turbo.json
- [Code Generation](10-generators.md) — Scaffolding new workspaces
