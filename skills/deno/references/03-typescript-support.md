# TypeScript Support

> Source: https://docs.deno.com/runtime/fundamentals/typescript/

## Table of Contents

- [First-Class TypeScript](#first-class-typescript)
- [Execution vs Type Checking](#execution-vs-type-checking)
- [deno check Command](#deno-check-command)
- [Compiler Options](#compiler-options)
- [JSX Support](#jsx-support)
- [Declaration Files](#declaration-files)
- [JavaScript Support](#javascript-support)
- [Common Patterns](#common-patterns)

## First-Class TypeScript

Deno runs TypeScript natively — no `tsc`, no `ts-node`, no build step:

```bash
# Just run it
deno run server.ts

# No tsconfig.json needed
# No node_modules needed
# No compilation step needed
```

Key differences from the Node.js TypeScript experience:
- No `dist/` output directory
- No source maps to configure
- No `tsconfig.json` required (sensible defaults)
- Full language support (enums, namespaces, parameter properties, decorators)
- Real file extensions in imports (`"./foo.ts"`, not `"./foo"`)

## Execution vs Type Checking

Deno deliberately separates execution from type checking:

### Execution (Fast Path)
When you `deno run`, Deno strips types and hands JavaScript to V8. Type errors do NOT prevent execution:

```bash
# Runs even if there are type errors
deno run main.ts
```

This is intentional — fast iteration during development without waiting for type checking.

### Type Checking (Correctness Path)

```bash
# Explicit type checking (equivalent to tsc --noEmit)
deno check main.ts

# Check and then run
deno run --check main.ts

# Check all files including remote/npm deps
deno check --all main.ts
```

### Recommended CI Workflow

```bash
# Separate steps for clear error messages
deno check main.ts        # Type errors
deno lint                  # Style/bug issues
deno test --allow-all     # Runtime correctness
```

## deno check Command

`deno check` validates types without executing code. Strict mode is ON by default.

```bash
# Check a single file and its dependencies
deno check main.ts

# Check multiple entry points
deno check src/server.ts src/cli.ts

# Include remote modules in checking
deno check --all main.ts

# Also type-check JavaScript files
deno check --check-js main.ts

# Use faster native TypeScript compiler (experimental)
deno check --unstable-tsgo main.ts
```

### What deno check Enforces

With strict mode defaults:
- `noImplicitAny` — no implicit `any` types
- `strictNullChecks` — null/undefined handled explicitly
- `strictFunctionTypes` — function type contravariance
- `strictBindCallApply` — correct bind/call/apply types
- `strictPropertyInitialization` — class properties initialized
- `noImplicitReturns` — all code paths return
- `noImplicitThis` — no implicit `this` typing
- `alwaysStrict` — emit `"use strict"` in every file

## Compiler Options

Configure TypeScript behavior in `deno.json`:

```jsonc
{
  "compilerOptions": {
    // Target (default: esnext)
    "target": "ES2022",

    // Module resolution
    "module": "preserve",

    // JSX configuration
    "jsx": "react-jsx",
    "jsxImportSource": "react",

    // Strictness (all true by default)
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,

    // Decorators
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,

    // Path mapping (use "imports" field instead)
    // "paths": {} — NOT recommended, use import maps

    // Library types
    "lib": ["deno.window", "deno.unstable"]
  }
}
```

### Available lib Options

| Value | Description |
|-------|-------------|
| `deno.window` | Deno global scope (default) |
| `deno.worker` | Deno Web Worker scope |
| `deno.unstable` | Unstable Deno APIs |
| `dom` | Browser DOM types (for SSR frameworks) |
| `dom.iterable` | DOM iterable APIs |

### Defaults You Rarely Need to Change

Deno's defaults are strict and modern:
- `strict: true`
- `module: "preserve"`
- `target: "esnext"`
- `moduleResolution: "bundler"`
- `verbatimModuleSyntax: true`
- `isolatedModules: true`

## JSX Support

### React JSX (Automatic Transform)

```jsonc
// deno.json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "jsxImportSource": "react"
  },
  "imports": {
    "react": "npm:react@^18.3.0",
    "react-dom": "npm:react-dom@^18.3.0"
  }
}
```

```tsx
// No need to import React for JSX
export function App() {
  return <h1>Hello from Deno!</h1>;
}
```

### Preact JSX

```jsonc
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "jsxImportSource": "preact"
  },
  "imports": {
    "preact": "npm:preact@^10.0.0"
  }
}
```

### Per-File JSX Pragma

Override the global config for individual files:

```tsx
/** @jsxImportSource react */
export function Component() {
  return <div>Uses React in this file</div>;
}
```

### Fresh Framework JSX (Preact)

```jsonc
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "jsxImportSource": "preact"
  },
  "imports": {
    "preact": "https://esm.sh/preact@10.22.0",
    "preact/": "https://esm.sh/preact@10.22.0/"
  }
}
```

## Declaration Files

### Providing Types for JavaScript

Use `@ts-self-types` directive to point a `.js` file to its declarations:

```javascript
// @ts-self-types="./math.d.ts"
export function add(a, b) {
  return a + b;
}
```

### Annotating Imports

Use `@ts-types` to associate types with an import:

```typescript
// @ts-types="npm:@types/express"
import express from "npm:express";
```

### Type-Only Imports

```typescript
import type { Config } from "./types.ts";
import { type Handler, serve } from "./server.ts";
```

### Triple-Slash Directives

Reference ambient type declarations:

```typescript
/// <reference types="npm:@types/node" />
/// <reference lib="deno.unstable" />
```

## JavaScript Support

Deno runs JavaScript files directly. TypeScript is optional:

```bash
deno run script.js
```

### Type Checking JavaScript

Enable type checking for `.js` files:

```javascript
// @ts-check — enables checking for this file

/** @type {string} */
const name = "Deno";

/** @param {number} x */
function double(x) {
  return x * 2;
}
```

Or globally:

```jsonc
{
  "compilerOptions": {
    "checkJs": true
  }
}
```

### JSDoc Type Annotations

```javascript
/**
 * @typedef {{ name: string, age: number }} User
 */

/**
 * @param {User} user
 * @returns {string}
 */
function greet(user) {
  return `Hello, ${user.name}!`;
}
```

## Common Patterns

### Ambient Type Declarations

Create a `types.d.ts` for global type augmentation:

```typescript
// types.d.ts
declare global {
  interface Window {
    __APP_VERSION__: string;
  }
}

export {};
```

Reference it in `deno.json`:

```jsonc
{
  "compilerOptions": {
    "types": ["./types.d.ts"]
  }
}
```

### Conditional Types for Platform

```typescript
// Works in both Deno and Node
const isDeno = typeof Deno !== "undefined";

if (isDeno) {
  // Deno-specific code
  const file = await Deno.readTextFile("./config.json");
}
```

### Importing npm Packages with Types

```typescript
// Most npm packages include types
import { z } from "npm:zod";

// For packages without built-in types
// @ts-types="npm:@types/lodash"
import _ from "npm:lodash";
```

## Common Pitfalls

1. **Type errors don't prevent execution** — `deno run` won't catch them; use `deno check` in CI
2. **No automatic .d.ts discovery** — unlike tsc, Deno won't auto-find adjacent declaration files
3. **import type is enforced** — with `verbatimModuleSyntax`, type-only imports must use `import type`
4. **Enums work differently** — const enums are inlined; regular enums produce runtime objects
5. **No paths in tsconfig** — use the `imports` field in `deno.json` instead
6. **DOM types not included by default** — add `"lib": ["deno.window", "dom"]` if needed for SSR
