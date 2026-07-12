# Modules and Dependency Management

> Source: https://docs.deno.com/runtime/fundamentals/modules/

## Table of Contents

- [Module System Fundamentals](#module-system-fundamentals)
- [Import Specifiers](#import-specifiers)
- [Import Maps in deno.json](#import-maps-in-denojson)
- [Dependency Management CLI](#dependency-management-cli)
- [Lock Files](#lock-files)
- [Import Attributes](#import-attributes)
- [Import Metadata](#import-metadata)
- [Vendoring](#vendoring)
- [Publishing to JSR](#publishing-to-jsr)

## Module System Fundamentals

Deno uses ECMAScript modules (ESM) as its primary module system. All imports use the standard `import`/`export` syntax with mandatory file extensions for local imports.

```typescript
// Local imports require full file extensions
import { add } from "./math.ts";
import { config } from "./config.json" with { type: "json" };

// Dynamic imports
const module = await import("./lazy-module.ts");
```

CommonJS (`require()`) is supported for Node.js compatibility but ESM is strongly preferred for new code.

## Import Specifiers

Deno supports multiple specifier types for importing packages:

### JSR Specifier (Recommended for Deno-native packages)

```typescript
import { camelCase } from "jsr:@luca/cases@^1.0.0";
import { parseArgs } from "jsr:@std/cli@^1.0.0";
```

Format: `jsr:@scope/package@version/path`

### npm Specifier (Node.js packages)

```typescript
import express from "npm:express@^4.18.0";
import { z } from "npm:zod@^3.22.0";
import chalk from "npm:chalk@5";
```

Format: `npm:package@version` or `npm:@scope/package@version`

### URL Imports (Direct from HTTP)

```typescript
import { serve } from "https://deno.land/std@0.220.0/http/server.ts";
```

### node: Built-in Modules

```typescript
import * as path from "node:path";
import * as fs from "node:fs/promises";
import { EventEmitter } from "node:events";
```

### Bare Specifiers (via Import Maps)

```typescript
// Requires mapping in deno.json "imports" field
import { z } from "zod";
import { db } from "@/lib/database";
```

## Import Maps in deno.json

The `imports` field in `deno.json` maps bare specifiers to versioned packages, centralizing dependency management:

```jsonc
{
  "imports": {
    // JSR packages
    "@std/assert": "jsr:@std/assert@^1.0.0",
    "@std/path": "jsr:@std/path@^1.0.0",

    // npm packages
    "zod": "npm:zod@^3.23.0",
    "hono": "npm:hono@^4.0.0",
    "drizzle-orm": "npm:drizzle-orm@^0.33.0",

    // Path aliases
    "@/": "./src/",
    "#config": "./config/mod.ts"
  }
}
```

Usage in code becomes clean:

```typescript
import { assertEquals } from "@std/assert";
import { z } from "zod";
import { db } from "@/lib/database.ts";
```

### Scoped Imports

Map package sub-paths with trailing slashes:

```jsonc
{
  "imports": {
    "@std/": "jsr:@std/"
  }
}
```

## Dependency Management CLI

### Adding Dependencies

```bash
# Add from JSR
deno add jsr:@std/assert
deno add jsr:@luca/cases

# Add from npm
deno add npm:zod
deno add npm:express

# Add multiple at once
deno add jsr:@std/path npm:chalk
```

This updates the `imports` field in `deno.json` automatically.

### Removing Dependencies

```bash
deno remove zod
deno remove @std/assert
```

### Checking for Updates

```bash
# Show outdated dependencies
deno outdated

# Update all dependencies
deno outdated --update

# Update specific package
deno outdated --update zod
```

### Installing from Lock File

```bash
# Install dependencies (creates node_modules if needed)
deno install

# CI-safe install (fails if lock file is out of date)
deno ci
```

### Dependency Tree Inspection

```bash
# Show why a package is in the tree
deno why npm:some-package

# Show module dependency graph
deno info main.ts

# Show info about a specific module
deno info npm:express
```

## Lock Files

`deno.lock` ensures reproducible builds by recording exact dependency versions and integrity hashes.

```bash
# Auto-generated on first run
deno run main.ts  # Creates/updates deno.lock

# Verify integrity (CI)
deno ci  # Fails if lock is stale

# Regenerate lock file
deno install --lock-write
```

Configure in `deno.json`:

```jsonc
{
  // Disable lock file (not recommended)
  "lock": false,

  // Custom lock file path
  "lock": "./deps.lock"
}
```

### Auto-Seeding from Other Lock Formats

Deno 2.9+ can seed `deno.lock` from existing lock files:
- `package-lock.json` (npm)
- `yarn.lock` (Yarn)
- `pnpm-lock.yaml` (pnpm)
- `bun.lock` (Bun)

## Import Attributes

Import non-JavaScript resources using `with` assertions:

```typescript
// JSON
import config from "./config.json" with { type: "json" };

// Text files
import readme from "./README.md" with { type: "text" };

// Binary data (Uint8Array)
import wasm from "./module.wasm" with { type: "bytes" };

// CSS (for web frameworks)
import styles from "./app.css" with { type: "css" };
```

## Import Metadata

Every module has access to `import.meta` properties:

```typescript
// Current module's URL
console.log(import.meta.url);
// file:///home/user/project/main.ts

// Is this the entry point?
if (import.meta.main) {
  startApp();
}

// File system paths (local modules only)
console.log(import.meta.filename); // /home/user/project/main.ts
console.log(import.meta.dirname);  // /home/user/project

// Resolve a specifier relative to current module
const workerUrl = import.meta.resolve("./worker.ts");
```

## Vendoring

Vendor dependencies locally for offline usage or auditing:

```bash
# Download all dependencies to vendor/ directory
deno vendor main.ts

# Use vendored dependencies
deno run --import-map=vendor/import_map.json main.ts
```

Or configure in `deno.json`:

```jsonc
{
  "vendor": true
}
```

This creates a `vendor/` directory with all remote dependencies and an import map pointing to them.

## Publishing to JSR

Publish Deno-native packages to JSR (jsr.io):

```jsonc
// deno.json
{
  "name": "@myorg/my-package",
  "version": "1.0.0",
  "exports": "./mod.ts"
}
```

```bash
# Publish (requires JSR account)
deno publish

# Dry run
deno publish --dry-run

# Bump version before publishing
deno bump-version patch
deno publish
```

### Package Exports

Define public entry points:

```jsonc
{
  "name": "@myorg/utils",
  "version": "1.0.0",
  "exports": {
    ".": "./mod.ts",
    "./strings": "./src/strings.ts",
    "./numbers": "./src/numbers.ts"
  }
}
```

## Deferred Module Evaluation

Use `import defer` for lazy loading (Stage 3 proposal):

```typescript
import defer * as heavyModule from "./heavy-computation.ts";

// Module is NOT evaluated until first property access
if (needsComputation) {
  const result = heavyModule.compute(data); // Evaluates here
}
```

## Common Patterns

### Centralized Dependencies File

```typescript
// deps.ts (optional pattern for smaller projects)
export { assertEquals, assertExists } from "jsr:@std/assert";
export { z } from "npm:zod";
export type { InferOutput } from "npm:zod";
```

### Version Pinning Strategy

```jsonc
{
  "imports": {
    // Use caret for libraries (minor updates OK)
    "zod": "npm:zod@^3.23.0",

    // Pin exact version for critical deps
    "drizzle-orm": "npm:drizzle-orm@0.33.2",

    // Use tilde for patch-only updates
    "@std/assert": "jsr:@std/assert@~1.0.3"
  }
}
```

## Common Pitfalls

1. **Missing file extensions** — Deno requires `.ts`/`.js` in local imports
2. **Bare specifiers without import map** — `import "lodash"` fails without `deno.json` mapping
3. **Version conflicts** — use `deno why` to diagnose duplicate packages
4. **Stale cache** — run `deno cache --reload main.ts` to force re-download
5. **Lock file drift** — use `deno ci` in CI to catch lock file issues
