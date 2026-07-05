# Biome — Linter Basics

> Source: [biomejs.dev/linter](https://biomejs.dev/linter/)

## Table of Contents
- [Overview](#overview)
- [Rule Naming Convention](#rule-naming-convention)
- [Rule Groups](#rule-groups)
- [Severity Levels](#severity-levels)
- [Presets](#presets)
- [Enabling and Disabling Rules](#enabling-and-disabling-rules)
- [Rule Options](#rule-options)
- [Safe and Unsafe Fixes](#safe-and-unsafe-fixes)
- [Suppressions](#suppressions)
- [Group-Level Configuration](#group-level-configuration)
- [CLI Usage](#cli-usage)
- [Common Patterns](#common-patterns)

---

## Overview

Biome's linter performs static analysis across JavaScript, TypeScript, JSX, TSX, JSON, CSS, GraphQL, and HTML. It ships with 509+ rules ported from ESLint, typescript-eslint, eslint-plugin-react, eslint-plugin-jsx-a11y, and other popular sources. The linter is independent from the formatter — they handle different concerns.

## Rule Naming Convention

Rules follow a consistent naming pattern:

- **`use*`** — enforce a best practice (e.g., `useConst`, `useOptionalChain`)
- **`no*`** — prohibit a pattern (e.g., `noDebugger`, `noExplicitAny`)

Rules are identified by their group and name: `correctness/noUnusedVariables`, `style/useConst`.

## Rule Groups

Biome organizes rules into 8 categories:

| Group | Purpose | Example Rules |
|-------|---------|---------------|
| **a11y** | Accessibility standards (ARIA, semantic HTML) | `noAccessKey`, `useAltText`, `useValidAriaProps` |
| **complexity** | Reduce unnecessary code complexity | `noForEach`, `noUselessCatch`, `useFlatMap` |
| **correctness** | Detect real programming errors | `noConstAssign`, `noUnusedVariables`, `noConstantCondition` |
| **nursery** | Experimental rules (not recommended by default) | New rules under validation |
| **performance** | Runtime and bundle-size optimization | `noDelete`, `noBarrelFile`, `noAccumulatingSpread` |
| **security** | Vulnerability prevention | `noDangerouslySetInnerHtml`, `noGlobalEval` |
| **style** | Code consistency and idioms | `useConst`, `useNamingConvention`, `noCommonJs` |
| **suspicious** | Likely bugs and common mistakes | `noDoubleEquals`, `noExplicitAny`, `noConsole` |

## Severity Levels

Each rule can be set to one of four severity levels:

| Level | Behavior | Exit Code |
|-------|----------|-----------|
| `"error"` | Halts CI, shown as error in editor | Non-zero |
| `"warn"` | Continues execution, shown as warning | Zero (unless `--error-on-warnings`) |
| `"info"` | Informational only, never fails CI | Zero |
| `"off"` | Rule completely disabled | — |

```json
{
  "linter": {
    "rules": {
      "suspicious": {
        "noExplicitAny": "warn",
        "noConsole": "info"
      },
      "correctness": {
        "noUnusedVariables": "error"
      }
    }
  }
}
```

## Presets

The `preset` field provides rule presets:

```json
{
  "linter": {
    "rules": {
      "preset": "recommended"
    }
  }
}
```

| Preset | Description |
|--------|-------------|
| `"recommended"` | Curated set of rules that catch common bugs (default) |
| `"all"` | Enable every stable rule |
| `"none"` | Start from zero, enable rules individually |

Individual rule settings override the preset:

```json
{
  "linter": {
    "rules": {
      "preset": "recommended",
      "style": {
        "noDefaultExport": "error"
      },
      "suspicious": {
        "noExplicitAny": "off"
      }
    }
  }
}
```

## Enabling and Disabling Rules

### Enable a specific rule

```json
{
  "linter": {
    "rules": {
      "style": {
        "useNamingConvention": "warn"
      }
    }
  }
}
```

### Disable a specific rule

```json
{
  "linter": {
    "rules": {
      "suspicious": {
        "noExplicitAny": "off"
      }
    }
  }
}
```

### Enable an entire group

```json
{
  "linter": {
    "rules": {
      "a11y": {
        "recommended": true
      }
    }
  }
}
```

### Disable an entire group

```json
{
  "linter": {
    "rules": {
      "a11y": {
        "recommended": false
      }
    }
  }
}
```

## Rule Options

Some rules accept configuration:

```json
{
  "linter": {
    "rules": {
      "style": {
        "useNamingConvention": {
          "level": "warn",
          "options": {
            "strictCase": false,
            "conventions": [
              {
                "selector": { "kind": "function" },
                "formats": ["camelCase", "PascalCase"]
              }
            ]
          }
        }
      }
    }
  }
}
```

## Safe and Unsafe Fixes

Biome classifies lint fixes into two categories:

**Safe fixes** — guaranteed to not change program semantics:
```bash
# Apply safe fixes
npx @biomejs/biome lint --write ./src
npx @biomejs/biome check --write ./src
```

**Unsafe fixes** — may alter behavior (e.g., removing unused variables):
```bash
# Apply both safe and unsafe fixes
npx @biomejs/biome lint --write --unsafe ./src
npx @biomejs/biome check --write --unsafe ./src
```

In editors, safe fixes can apply automatically on save. Unsafe fixes show as manual code actions.

## Suppressions

### Suppress a specific rule on one line

```typescript
// biome-ignore lint/suspicious/noExplicitAny: legacy API requires any
const data: any = fetchLegacyApi();
```

### Suppress multiple rules

```typescript
// biome-ignore lint/suspicious/noExplicitAny lint/style/useConst: migration
var data: any = response;
```

### Suppress all lint rules for a file

```typescript
// biome-ignore-all lint: generated file, do not lint
```

### Suppress during migration (bulk)

```bash
# Add suppression comments to all current violations
npx @biomejs/biome lint --suppress --reason "migration to biome" ./src
```

This is invaluable when adopting Biome on an existing codebase — suppress all current issues, then fix them incrementally.

## Group-Level Configuration

Control entire groups at once:

```json
{
  "linter": {
    "rules": {
      "preset": "none",
      "correctness": { "recommended": true },
      "suspicious": { "recommended": true },
      "security": { "all": true },
      "style": { "recommended": false }
    }
  }
}
```

## CLI Usage

```bash
# Lint files (report only)
npx @biomejs/biome lint ./src

# Lint and fix safe issues
npx @biomejs/biome lint --write ./src

# Lint and fix all issues (including unsafe)
npx @biomejs/biome lint --write --unsafe ./src

# Lint only specific rules
npx @biomejs/biome lint --only=correctness/noUnusedVariables ./src

# Lint skipping specific rules
npx @biomejs/biome lint --skip=style ./src

# Lint only specific domains
npx @biomejs/biome lint --only=react ./src

# Lint staged files only
npx @biomejs/biome lint --staged ./src

# Watch mode
npx @biomejs/biome lint --watch ./src
```

## Common Patterns

### Strict TypeScript Project

```json
{
  "linter": {
    "rules": {
      "preset": "recommended",
      "correctness": {
        "noUnusedVariables": "error",
        "noUnusedImports": "error",
        "useExhaustiveDependencies": "warn"
      },
      "suspicious": {
        "noExplicitAny": "error",
        "noConsole": "warn"
      },
      "style": {
        "useConst": "error",
        "noDefaultExport": "error",
        "useImportType": "error"
      }
    }
  }
}
```

### Relaxed Development Config

```json
{
  "linter": {
    "rules": {
      "preset": "recommended",
      "suspicious": {
        "noExplicitAny": "warn",
        "noConsole": "off"
      },
      "style": {
        "noNonNullAssertion": "warn"
      }
    }
  }
}
```
