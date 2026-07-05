# Biome — Assist & Import Sorting

> Source: [biomejs.dev/assist](https://biomejs.dev/assist/) | Version: 2.5.x

## Table of Contents
- [What Is Assist](#what-is-assist)
- [Import Sorting](#import-sorting)
- [Sorting Algorithm](#sorting-algorithm)
- [Import Groups](#import-groups)
- [Configuration](#configuration)
- [CLI Usage](#cli-usage)
- [Suppressing Import Sorting](#suppressing-import-sorting)
- [Editor Integration](#editor-integration)
- [Migration from Other Tools](#migration-from-other-tools)
- [Common Patterns](#common-patterns)

---

## What Is Assist

Biome's **Assist** is the third tool alongside the formatter and linter. It provides code actions — automated transformations that go beyond formatting and linting. The primary assist action is **import organization** (`organizeImports`), which sorts and groups import/export statements.

Assist is enabled by default and runs as part of `biome check`.

## Import Sorting

Biome sorts imports by "distance" — modules that are "farther" from the user (built-in, third-party) go first, modules "closer" (local files) go last.

### Before

```typescript
import { render } from "@testing-library/react";
import { useState } from "react";
import path from "node:path";
import { Button } from "./components/Button";
import type { User } from "../types";
import { z } from "zod";
import styles from "./App.module.css";
```

### After (sorted by Biome)

```typescript
import path from "node:path";
import { useState } from "react";
import { render } from "@testing-library/react";
import { z } from "zod";
import type { User } from "../types";
import { Button } from "./components/Button";
import styles from "./App.module.css";
```

## Sorting Algorithm

Biome applies a natural sort order with these priority levels:

1. **Node.js built-ins** — `node:fs`, `node:path`, `fs`, `path`
2. **Third-party packages** — `react`, `zod`, `@testing-library/react`
3. **Internal aliases** — `@/utils`, `~/components` (configurable)
4. **Relative parent** — `../types`, `../../utils`
5. **Relative sibling** — `./components`, `./utils`

Within each group:
- **Bare imports** before **named imports** — `import "side-effect"` first
- **Value imports** before **type imports** — `import { x }` before `import type { T }`
- **Alphabetical** within the same category

Exported names within a single import statement are also sorted:

```typescript
// Before
import { z, ZodSchema, ZodError, string } from "zod";

// After
import { string, z, ZodError, ZodSchema } from "zod";
```

## Import Groups

Groups separate imports visually with blank lines. Biome's default groups:

```
[node built-ins]

[third-party packages]

[relative imports]
```

### Custom Groups

Configure custom groups using the `organizeImports` assist action:

```json
{
  "assist": {
    "actions": {
      "source": {
        "organizeImports": {
          "level": "error",
          "options": {
            "groups": [
              [":PACKAGE:node"],
              [":BLANK_LINE:"],
              [":PACKAGE:"],
              [":BLANK_LINE:"],
              ["@company/**"],
              [":BLANK_LINE:"],
              ["./**", "../**"]
            ]
          }
        }
      }
    }
  }
}
```

Special group tokens:
- `:PACKAGE:` — matches package imports
- `:PACKAGE:node` — matches Node.js built-in imports
- `:BLANK_LINE:` — inserts a visual separator between groups

## Configuration

### Enable/Disable Import Sorting

```json
{
  "assist": {
    "enabled": true,
    "actions": {
      "source": {
        "organizeImports": "error"
      }
    }
  }
}
```

Severity levels for import sorting:
- `"error"` — CI fails if imports are unsorted
- `"warn"` — reports but doesn't fail CI
- `"info"` — informational only
- `"off"` — disabled

### Disable for Specific Files

```json
{
  "overrides": [
    {
      "includes": ["scripts/**"],
      "assist": {
        "actions": {
          "source": {
            "organizeImports": "off"
          }
        }
      }
    }
  ]
}
```

## CLI Usage

```bash
# Check import ordering (report only)
npx @biomejs/biome check ./src

# Fix import ordering
npx @biomejs/biome check --write ./src

# Only organize imports (skip lint + format)
npx @biomejs/biome lint --only=assist/source/organizeImports ./src

# Check imports in CI
npx @biomejs/biome ci ./src
```

Import sorting is included in `biome check` alongside formatting and linting — there's no separate command.

## Suppressing Import Sorting

### Suppress for a file

```typescript
// biome-ignore-all assist/source/organizeImports: custom import order required
import "./polyfills";
import { config } from "./config";
import React from "react";
```

### Suppress for a specific import block

```typescript
// biome-ignore assist/source/organizeImports: side-effect import must be first
import "./instrument";

import { app } from "./app";
```

### Preserve blank line separators

Biome respects existing blank lines between import groups. If your imports already have meaningful grouping via blank lines, Biome sorts within each group but preserves the blank line separators.

## Editor Integration

### VS Code — Sort on Save

```json
// .vscode/settings.json
{
  "editor.codeActionsOnSave": {
    "source.organizeImports.biome": "explicit"
  }
}
```

### IntelliJ — Organize Imports Action

In IntelliJ settings, bind the Biome "Organize Imports" code action to your preferred shortcut (default: Ctrl+Alt+O / Cmd+Alt+O).

## Migration from Other Tools

### From `eslint-plugin-import` / `eslint-plugin-simple-import-sort`

Biome's import sorting replaces:
- `eslint-plugin-import/order`
- `eslint-plugin-simple-import-sort`
- `prettier-plugin-organize-imports`

Remove these plugins and their config after migrating to Biome.

### From `isort` (Python-style)

Biome only handles JavaScript/TypeScript imports. Python projects still need `isort` or `ruff`.

## Common Patterns

### Monorepo with Workspace Packages

```json
{
  "assist": {
    "actions": {
      "source": {
        "organizeImports": {
          "level": "error",
          "options": {
            "groups": [
              [":PACKAGE:node"],
              [":BLANK_LINE:"],
              [":PACKAGE:"],
              [":BLANK_LINE:"],
              ["@myorg/**"],
              [":BLANK_LINE:"],
              ["./**", "../**"]
            ]
          }
        }
      }
    }
  }
}
```

Result:

```typescript
import fs from "node:fs";

import { z } from "zod";

import { logger } from "@myorg/logging";
import { db } from "@myorg/database";

import { handler } from "./handler";
import type { Config } from "../types";
```

### Side-Effect Imports First

Side-effect imports (`import "module"`) are naturally sorted before named imports, so `import "./polyfills"` appears before `import { x } from "./utils"`.

### Type Imports Last (Within Group)

```typescript
import { createApp } from "vue";
import type { App, Plugin } from "vue";
```

Biome places value imports before type-only imports within the same source module.
