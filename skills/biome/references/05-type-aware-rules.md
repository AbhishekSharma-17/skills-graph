# Biome — Type-Aware Rules

> Source: [biomejs.dev/linter](https://biomejs.dev/linter/) | Version: 2.5.x

## Table of Contents
- [Overview](#overview)
- [How It Works](#how-it-works)
- [Enabling Type-Aware Rules](#enabling-type-aware-rules)
- [Key Type-Aware Rules](#key-type-aware-rules)
- [The Scanner](#the-scanner)
- [Configuration](#configuration)
- [Performance Considerations](#performance-considerations)
- [Comparison with typescript-eslint](#comparison-with-typescript-eslint)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Overview

Since Biome v2, type-aware lint rules are available that can reason about the types in your code — without requiring the TypeScript compiler (`tsc`). Biome achieves this through its own type inference engine, developed with sponsorship from Vercel.

Type-aware rules detect bugs that purely syntactic rules cannot catch, such as floating Promises, misused Promise patterns, and unnecessary type assertions.

## How It Works

Biome uses a **Scanner** to build a module graph and perform type inference. This is fundamentally different from typescript-eslint's approach:

| Aspect | Biome | typescript-eslint |
|--------|-------|-------------------|
| Inference engine | Custom Rust implementation | TypeScript compiler |
| `tsconfig.json` | Not required | Required |
| Speed | Fast (incremental Rust) | Slow (full tsc program) |
| Accuracy | Partial inference (growing) | Full TypeScript inference |
| Setup | Opt-in via config | Requires project references |

The Scanner builds a module dependency graph from your source files, resolves imports, and infers types for expressions, variables, and function return types.

## Enabling Type-Aware Rules

Type-aware rules live in the **project** domain. Enable them by activating project-domain rules:

```json
{
  "linter": {
    "rules": {
      "correctness": {
        "noUndeclaredDependencies": "error"
      },
      "suspicious": {
        "noFloatingPromises": "error",
        "noMisusedPromises": "error"
      },
      "nursery": {
        "noUnnecessaryConditions": "warn"
      }
    }
  }
}
```

Or enable all project-domain rules at once:

```json
{
  "linter": {
    "domains": {
      "project": "all"
    }
  }
}
```

## Key Type-Aware Rules

### noFloatingPromises

Detects Promises that are created but never awaited or returned.

```typescript
// Error: floating Promise — result is never awaited
async function processData() {
  fetchData(); // Returns Promise but not awaited
}

// Fixed
async function processData() {
  await fetchData();
}

// Also fixed — explicit void discard
async function processData() {
  void fetchData(); // explicitly fire-and-forget
}
```

### noMisusedPromises

Catches Promises used in non-Promise contexts.

```typescript
// Error: Promise used as boolean condition
async function checkData() {
  const data = fetchData();
  if (data) { // Always truthy — it's a Promise object!
    console.log("has data");
  }
}

// Fixed
async function checkData() {
  const data = await fetchData();
  if (data) {
    console.log("has data");
  }
}

// Error: Promise passed to Array.forEach (not awaited)
[1, 2, 3].forEach(async (n) => {
  await processItem(n);
});

// Fixed — use for...of
for (const n of [1, 2, 3]) {
  await processItem(n);
}
```

### noUndeclaredDependencies

Flags imports from packages not listed in `package.json`.

```typescript
// Error: 'lodash' not in package.json dependencies
import { debounce } from "lodash";

// Fixed: add to package.json, then the import is valid
```

### noUnnecessaryConditions (nursery)

Detects conditions that are always true or always false based on type inference.

```typescript
// Error: condition is always true — 'name' is string, never nullish
function greet(name: string) {
  if (name) { // string is always truthy (except "")
    return `Hello, ${name}`;
  }
}
```

## The Scanner

The Scanner is Biome's module resolution and type inference engine. It activates automatically when project-domain rules are enabled and builds:

1. **Module graph** — maps import/export relationships between files
2. **Type information** — infers types for variables, expressions, and return values
3. **Dependency graph** — resolves package dependencies from `package.json`

The Scanner reads your project structure to understand module boundaries and infer types without `tsconfig.json`.

## Configuration

### Minimal type-aware setup

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.0/schema.json",
  "linter": {
    "enabled": true,
    "rules": {
      "preset": "recommended",
      "suspicious": {
        "noFloatingPromises": "error",
        "noMisusedPromises": "error"
      }
    }
  }
}
```

### Full project-domain activation

```json
{
  "linter": {
    "domains": {
      "project": "recommended"
    }
  }
}
```

### Disabling the Scanner for performance

If you only use syntactic rules and want to avoid the Scanner overhead:

```json
{
  "linter": {
    "domains": {
      "project": "off"
    }
  }
}
```

## Performance Considerations

Type-aware rules roughly double lint execution time due to the Scanner building a module graph. On a 10,000-file project:

| Mode | Time |
|------|------|
| Syntactic only | ~0.8s |
| With type-aware | ~1.6s |

This is still dramatically faster than typescript-eslint with type checking (which can take 30-60s on the same project).

Tips for managing performance:
- Enable only the type-aware rules you actually need
- Use `files.includes` to limit Scanner scope to source directories
- The Scanner is incremental in daemon/LSP mode, so subsequent runs are fast

## Comparison with typescript-eslint

### What Biome covers today

- Floating Promises detection
- Misused Promises (conditions, forEach, etc.)
- Undeclared dependencies
- Unnecessary conditions (partial)
- Basic type narrowing

### What typescript-eslint covers that Biome doesn't yet

- Full generic type inference
- Conditional types
- Mapped types
- Template literal types
- Complex type guards
- `no-unsafe-*` family of rules

Biome's type inference is actively being expanded. For projects requiring full type-aware coverage, typescript-eslint remains more comprehensive but significantly slower.

## Common Patterns

### Async/Await Heavy Projects

```json
{
  "linter": {
    "rules": {
      "suspicious": {
        "noFloatingPromises": "error",
        "noMisusedPromises": "error"
      },
      "correctness": {
        "noUndeclaredDependencies": "error"
      }
    }
  }
}
```

### Gradual Adoption

Start with `"warn"` to see the impact without breaking CI:

```json
{
  "linter": {
    "rules": {
      "suspicious": {
        "noFloatingPromises": "warn",
        "noMisusedPromises": "warn"
      }
    }
  }
}
```

## Troubleshooting

### Scanner not finding modules

Ensure your `package.json` is accessible from the project root. The Scanner resolves modules relative to the nearest `package.json`.

### False positives with dynamic imports

The Scanner has limited support for dynamic `import()` expressions and `require()`. Type-aware rules may produce false positives for dynamically loaded modules.

### Performance regression after enabling type-aware rules

Use `--only` to run type-aware rules selectively in CI:

```bash
# Run only type-aware rules (slower pass)
npx @biomejs/biome lint --only=suspicious/noFloatingPromises --only=suspicious/noMisusedPromises ./src

# Run syntactic rules in a separate, fast pass
npx @biomejs/biome lint --skip=suspicious/noFloatingPromises --skip=suspicious/noMisusedPromises ./src
```
