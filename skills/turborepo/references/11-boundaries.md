# Turborepo — Boundaries

> Source: [turborepo.dev/docs/reference/boundaries](https://turborepo.dev/docs/reference/boundaries)

## Overview

Turborepo Boundaries enforce architectural rules across your monorepo by detecting:

- Importing files from outside a package's directory
- Importing packages not declared as dependencies in `package.json`
- Importing packages that violate tag-based rules

Boundaries help maintain clean dependency graphs and prevent accidental coupling between packages that shouldn't depend on each other.

## Enabling Boundaries

### Basic Setup

Add `boundaries: true` to your root `turbo.json`:

```jsonc
// turbo.json
{
  "$schema": "https://turborepo.dev/schema.json",
  "boundaries": true,
  "tasks": { ... }
}
```

### Run Boundary Checks

```bash
# Check all boundary rules
turbo boundaries

# Check and report violations
turbo ls --boundaries
```

## Built-in Checks

With `boundaries: true`, Turborepo automatically enforces:

### 1. No Cross-Package File Imports

A package cannot import files directly from another package's source directory:

```typescript
// packages/web/src/app.ts

// BAD: Direct file import from another package
import { Button } from "../../packages/ui/src/Button";

// GOOD: Import through the package's public API
import { Button } from "@repo/ui";
```

### 2. No Undeclared Dependencies

A package cannot import another package unless it's listed in its `package.json` dependencies:

```jsonc
// apps/web/package.json
{
  "dependencies": {
    "@repo/ui": "workspace:*"     // Declared — import allowed
    // @repo/utils NOT listed — import would be a violation
  }
}
```

```typescript
// apps/web/src/page.ts
import { Button } from "@repo/ui";     // OK — declared dependency
import { slugify } from "@repo/utils"; // VIOLATION — not in dependencies
```

## Tags

Tags allow you to define custom rules about which packages can depend on which.

### Defining Tags

Add tags in package-level `turbo.json` files:

```jsonc
// packages/ui/turbo.json
{
  "$schema": "https://turborepo.dev/schema.json",
  "extends": ["//"],
  "tags": ["ui", "public"]
}
```

```jsonc
// packages/internal-api/turbo.json
{
  "$schema": "https://turborepo.dev/schema.json",
  "extends": ["//"],
  "tags": ["internal"]
}
```

```jsonc
// apps/web/turbo.json
{
  "$schema": "https://turborepo.dev/schema.json",
  "extends": ["//"],
  "tags": ["app"]
}
```

### Defining Rules

Rules are declared in the root `turbo.json`:

```jsonc
// turbo.json
{
  "boundaries": {
    "rules": [
      {
        "tag": "app",
        "deny": ["internal"]
        // Apps cannot depend on packages tagged "internal"
      },
      {
        "tag": "internal",
        "dependents": {
          "allow": ["internal"]
          // Only other internal packages can depend on internal packages
        }
      }
    ]
  }
}
```

### Rule Types

#### Deny Rule

Prevents packages with a tag from depending on packages with specified tags:

```jsonc
{
  "tag": "frontend",
  "deny": ["backend-only"]
  // Frontend packages cannot import backend-only packages
}
```

#### Allow Rule (via dependents)

Restricts which packages can depend on packages with a tag:

```jsonc
{
  "tag": "internal-api",
  "dependents": {
    "allow": ["backend"]
    // Only backend packages can import internal-api packages
  }
}
```

### Using Package Names in Rules

You can reference specific package names instead of tags:

```jsonc
{
  "boundaries": {
    "rules": [
      {
        "tag": "app",
        "deny": ["@repo/db"]
        // Apps cannot directly depend on the database package
      }
    ]
  }
}
```

## Transitive Dependencies

Boundary rules apply transitively. If:
- Package A depends on Package B
- Package B depends on Package C
- Package A has a "deny" rule for Package C's tag

Then Package A violates the boundary, even though the dependency is indirect.

## Common Architectural Patterns

### Layer Architecture

```jsonc
{
  "boundaries": {
    "rules": [
      {
        "tag": "ui",
        "deny": ["data", "infra"]
        // UI layer cannot access data or infrastructure
      },
      {
        "tag": "data",
        "deny": ["ui"]
        // Data layer cannot access UI
      },
      {
        "tag": "infra",
        "dependents": {
          "allow": ["data"]
          // Only data layer can use infrastructure packages
        }
      }
    ]
  }
}
```

### Public vs Internal Packages

```jsonc
{
  "boundaries": {
    "rules": [
      {
        "tag": "internal",
        "dependents": {
          "allow": ["internal"]
          // Only internal packages can depend on other internal packages
        }
      }
    ]
  }
}
```

### Team Boundaries

```jsonc
{
  "boundaries": {
    "rules": [
      {
        "tag": "team-a",
        "deny": ["team-b-internal"]
      },
      {
        "tag": "team-b",
        "deny": ["team-a-internal"]
      }
    ]
  }
}
```

## CI Integration

Run boundary checks in CI to prevent violations from being merged:

```yaml
# .github/workflows/ci.yml
- name: Check boundaries
  run: pnpm turbo boundaries
```

## Common Pitfalls

1. **Forgetting transitive dependencies** — A deny rule blocks indirect dependencies too. If A → B → C and A denies C's tag, that's a violation.

2. **Missing tags** — Packages without tags aren't affected by tag-based rules. Be intentional about which packages get tags.

3. **Undeclared dependencies slipping through** — The built-in check catches missing `package.json` entries, but only if `boundaries` is enabled.

4. **Too many rules** — Start with the built-in checks (`boundaries: true`) and add tag rules gradually as architectural patterns emerge.

## Related

- [Workspace Structure](04-workspace-structure.md) — Package organization
- [Configuration](01-configuration.md) — turbo.json reference
- [CI/CD Integration](07-ci-cd.md) — Running checks in CI
