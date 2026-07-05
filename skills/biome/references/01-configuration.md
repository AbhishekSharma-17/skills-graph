# Biome — Configuration

> Source: [biomejs.dev/reference/configuration](https://biomejs.dev/reference/configuration/)

## Table of Contents
- [Configuration Files](#configuration-files)
- [File Resolution](#file-resolution)
- [Top-Level Structure](#top-level-structure)
- [Schema](#schema)
- [Extends](#extends)
- [File Management](#file-management)
- [VCS Settings](#vcs-settings)
- [Language-Specific Configuration](#language-specific-configuration)
- [Overrides](#overrides)
- [Glob Patterns](#glob-patterns)
- [Environment Variables](#environment-variables)
- [Common Patterns](#common-patterns)

---

## Configuration Files

Biome uses JSON configuration files. Supported names (checked in order):
1. `biome.json`
2. `biome.jsonc` (allows comments)
3. `.biome.json`
4. `.biome.jsonc`

```bash
# Generate default configuration
npx @biomejs/biome init
```

## File Resolution

Biome searches for configuration files starting from the current working directory, walking up through parent directories. The search stops when a file with `"root": true` is found or the filesystem root is reached.

For monorepos, place a root config at the top level and override in subdirectories:

```
project/
├── biome.json          # root: true, shared settings
├── apps/
│   └── web/
│       └── biome.json  # extends root, overrides for web app
└── packages/
    └── ui/
        └── biome.json  # extends root, overrides for UI library
```

## Top-Level Structure

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.0/schema.json",
  "root": true,
  "extends": [],
  "plugins": [],
  "files": {},
  "vcs": {},
  "formatter": {},
  "linter": {},
  "assist": {},
  "javascript": {},
  "json": {},
  "css": {},
  "graphql": {},
  "html": {},
  "overrides": []
}
```

## Schema

Always include `$schema` for IDE autocompletion:

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.0/schema.json"
}
```

## Extends

Inherit configuration from other files or shared configs:

```json
{
  "extends": ["./biome-base.json", "@company/biome-config/biome.json"]
}
```

Settings in the current file override extended settings. Arrays (like rules) are merged.

## File Management

```json
{
  "files": {
    "includes": ["src/**", "tests/**"],
    "ignoreUnknown": true,
    "maxSize": 2097152
  }
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `includes` | `["**"]` | Glob patterns for files to process |
| `ignoreUnknown` | `false` | Skip files Biome can't handle |
| `maxSize` | `1048576` (1 MiB) | Maximum file size in bytes |

Protected files are always ignored: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `composer.lock`.

Use negation patterns to exclude:

```json
{
  "files": {
    "includes": ["**", "!dist/**", "!coverage/**", "!**/*.generated.ts"]
  }
}
```

## VCS Settings

```json
{
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true,
    "defaultBranch": "main"
  }
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `enabled` | `false` | Activate VCS integration |
| `clientKind` | `"git"` | Only Git is currently supported |
| `useIgnoreFile` | `false` | Respect `.gitignore` patterns |
| `defaultBranch` | `"main"` | Branch for `--changed` comparisons |

## Language-Specific Configuration

Each language has its own parser, formatter, and linter settings under a top-level key. Biome treats all JavaScript variants (JS, TS, JSX, TSX) under `javascript`.

### JavaScript / TypeScript

```json
{
  "javascript": {
    "globals": ["$", "jQuery"],
    "jsxRuntime": "transparent",
    "parser": {
      "unsafeParameterDecoratorsEnabled": false
    },
    "formatter": {
      "quoteStyle": "single",
      "trailingCommas": "all",
      "semicolons": "always",
      "arrowParentheses": "always",
      "bracketSameLine": false
    },
    "linter": {
      "enabled": true
    },
    "assist": {
      "enabled": true
    }
  }
}
```

### JSON

```json
{
  "json": {
    "parser": {
      "allowComments": true,
      "allowTrailingCommas": true
    },
    "formatter": {
      "trailingCommas": "none"
    }
  }
}
```

### CSS

```json
{
  "css": {
    "parser": {
      "cssModules": true,
      "tailwindDirectives": true
    },
    "formatter": {
      "quoteStyle": "double"
    }
  }
}
```

### GraphQL

```json
{
  "graphql": {
    "formatter": {
      "quoteStyle": "double"
    }
  }
}
```

### HTML (Experimental)

```json
{
  "html": {
    "formatter": {
      "attributePosition": "auto",
      "bracketSameLine": false,
      "whitespaceSensitivity": "css",
      "selfCloseVoidElements": "never"
    }
  }
}
```

## Overrides

Apply different settings based on file patterns:

```json
{
  "overrides": [
    {
      "includes": ["tests/**"],
      "linter": {
        "rules": {
          "suspicious": {
            "noExplicitAny": "off"
          }
        }
      }
    },
    {
      "includes": ["*.config.ts", "*.config.js"],
      "formatter": {
        "lineWidth": 120
      }
    },
    {
      "includes": ["generated/**"],
      "formatter": { "enabled": false },
      "linter": { "enabled": false }
    }
  ]
}
```

Overrides are evaluated in order; the first matching pattern applies.

## Glob Patterns

| Pattern | Matches |
|---------|---------|
| `*` | Any characters except path separator |
| `**` | Recursive directory matching |
| `[abc]` | Character set |
| `[!abc]` | Negated character set |
| `!pattern` | Exclude pattern |
| `!!pattern` | Force-ignore (prevents scanner traversal) |

Note: `**` must be a complete path component. `src/**.ts` does not work; use `src/**/*.ts`.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `BIOME_CONFIG_PATH` | Override config file location |
| `BIOME_LOG_DIR` | Directory for daemon logs |
| `BIOME_LOG_PREFIX_NAME` | Prefix for log file names |

## Common Patterns

### Minimal Production Config

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.0/schema.json",
  "vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true },
  "formatter": { "indentStyle": "space", "indentWidth": 2, "lineWidth": 100 },
  "javascript": { "formatter": { "quoteStyle": "single", "semicolons": "always" } },
  "linter": { "rules": { "preset": "recommended" } }
}
```

### Strict Config (All Rules)

```json
{
  "linter": {
    "rules": {
      "preset": "all",
      "nursery": { "recommended": false },
      "style": {
        "noDefaultExport": "off"
      }
    }
  }
}
```

### Monorepo Shared Config

```json
// packages/biome-config/biome-base.json
{
  "$schema": "https://biomejs.dev/schemas/2.5.0/schema.json",
  "root": true,
  "formatter": { "indentStyle": "space" },
  "linter": { "rules": { "preset": "recommended" } }
}

// apps/web/biome.json
{
  "extends": ["../../packages/biome-config/biome-base.json"],
  "linter": {
    "rules": {
      "a11y": { "recommended": true }
    }
  }
}
```
