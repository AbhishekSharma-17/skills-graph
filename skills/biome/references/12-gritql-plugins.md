# Biome — GritQL Plugins

> Source: [biomejs.dev](https://biomejs.dev/) | Version: 2.5.x

## Table of Contents
- [Overview](#overview)
- [What Is GritQL](#what-is-gritql)
- [Plugin Configuration](#plugin-configuration)
- [Writing Custom Rules](#writing-custom-rules)
- [Pattern Syntax](#pattern-syntax)
- [Metavariables](#metavariables)
- [Conditions and Constraints](#conditions-and-constraints)
- [Examples](#examples)
- [Testing Plugins](#testing-plugins)
- [Using biome search](#using-biome-search)
- [Limitations](#limitations)

---

## Overview

Biome supports custom lint rules via GritQL, a declarative pattern query language. GritQL plugins let you create project-specific rules without writing Rust code, addressing the gap left by ESLint's JavaScript-based plugin ecosystem.

GritQL rules can:
- Detect patterns in your code (like ESLint custom rules)
- Suggest fixes (rewrites)
- Target specific file patterns

## What Is GritQL

GritQL is a pattern-matching language for code. It treats code as a tree and lets you query for structural patterns:

```grit
// Find all console.log calls
`console.log($message)`
```

GritQL is syntax-aware — it matches AST nodes, not raw text. `console.log($message)` matches the actual call expression, not a string that happens to contain "console.log".

## Plugin Configuration

Register plugins in `biome.json`:

```json
{
  "plugins": [
    "./biome-plugins/no-company-secrets.grit",
    {
      "path": "./biome-plugins/naming-rules.grit",
      "includes": ["src/**"]
    }
  ]
}
```

### Plugin with File Filtering

```json
{
  "plugins": [
    {
      "path": "./biome-plugins/react-patterns.grit",
      "includes": ["src/components/**/*.tsx"]
    },
    {
      "path": "./biome-plugins/api-patterns.grit",
      "includes": ["src/api/**/*.ts"]
    }
  ]
}
```

## Writing Custom Rules

A GritQL plugin file contains one or more pattern definitions:

```grit
// biome-plugins/no-moment.grit
// Prevent usage of moment.js (use date-fns or dayjs instead)

`import $_ from "moment"` => .  // Remove the import

`import { $imports } from "moment"` => .  // Remove named imports

`require("moment")` => .  // Remove require
```

### Rule Structure

```grit
// Description of what this rule does
// @level error|warn|info

// Pattern to match => optional replacement
`pattern` => `replacement`

// Or just detect without replacement
`pattern`
```

## Pattern Syntax

### Literal Matching

```grit
// Match exact code
`console.log("hello")`

// Match any argument
`console.log($arg)`

// Match method calls
`$obj.toString()`
```

### Wildcards

```grit
// $name matches any single node
`const $name = $value`

// $_ matches but doesn't capture
`import $_ from "lodash"`

// $...args matches multiple nodes
`console.log($...args)`
```

### Alternatives

```grit
// Match either pattern
or {
  `console.log($msg)`,
  `console.warn($msg)`,
  `console.error($msg)`
}
```

### Negation

```grit
// Match function declarations that are NOT async
`function $name($...params) { $body }` where {
  not `async function $name($...params) { $body }`
}
```

## Metavariables

Metavariables (`$name`) capture matched nodes for use in conditions and rewrites:

```grit
// Capture and reuse
`var $name = $value` => `const $name = $value`

// Capture for condition checking
`fetch($url)` where {
  $url <: not `"/api/$_"`  // Only match non-API fetches
}
```

### Multiple Captures

```grit
// Match and restructure
`$obj[$key] = $value` => `$obj.set($key, $value)`
```

## Conditions and Constraints

### Where Clause

```grit
`import $name from "$module"` where {
  $module <: r"^\\.\\./"  // Only relative parent imports
}
```

### String Constraints

```grit
// Regex match
$name <: r"^_"  // starts with underscore

// Contains
$name <: includes "test"

// Not
$name <: not "default"
```

### Combining Conditions

```grit
`const $name: $type = $value` where {
  $type <: `any`,
  $name <: not r"^_"
}
```

## Examples

### Ban Specific Imports

```grit
// biome-plugins/no-lodash.grit
// Ban lodash — use native methods or lodash-es
// @level error

or {
  `import $_ from "lodash"`,
  `import { $_ } from "lodash"`,
  `require("lodash")`
}
```

### Enforce Naming Convention

```grit
// biome-plugins/no-hungarian.grit
// Ban Hungarian notation prefixes
// @level warn

`const $name = $value` where {
  $name <: or {
    r"^str[A-Z]",
    r"^num[A-Z]",
    r"^bool[A-Z]",
    r"^arr[A-Z]",
    r"^obj[A-Z]"
  }
}
```

### Enforce API Patterns

```grit
// biome-plugins/use-custom-fetch.grit
// Require using our custom fetch wrapper
// @level error

`fetch($...args)` => `apiFetch($...args)` where {
  not within `function apiFetch($...params) { $body }`
}
```

### Migrate Deprecated API

```grit
// biome-plugins/migrate-api.grit
// Migrate from old API to new API
// @level warn

`oldApi.createUser($data)` => `newApi.users.create($data)`
`oldApi.getUser($id)` => `newApi.users.get($id)`
`oldApi.deleteUser($id)` => `newApi.users.delete($id)`
```

### Prevent Test Anti-patterns

```grit
// biome-plugins/test-patterns.grit
// No sleeping in tests
// @level error

`await sleep($duration)` where {
  within or {
    `it($...args)`,
    `test($...args)`,
    `describe($...args)`
  }
}
```

## Testing Plugins

### Using biome search

Test your patterns before making them lint rules:

```bash
# Search for pattern matches
npx @biomejs/biome search "console.log($msg)" ./src

# Search with more complex patterns
npx @biomejs/biome search 'import $_ from "lodash"' ./src
```

### Dry Run

Add the plugin to your config and run lint in report-only mode:

```bash
npx @biomejs/biome lint ./src
```

Check the output before setting the rule to `"error"`.

## Using biome search

The `biome search` command uses GritQL for ad-hoc code search (experimental):

```bash
# Find all useState calls
npx @biomejs/biome search "useState($initial)" ./src

# Find all try-catch with empty catch
npx @biomejs/biome search "try { $body } catch($e) {}" ./src

# Find all TODO comments (limited — GritQL is AST-based, not text-based)
npx @biomejs/biome search '// TODO: $msg' ./src
```

## Limitations

- **No type information** — GritQL operates on syntax, not types
- **No cross-file analysis** — each file is analyzed independently
- **Experimental** — the plugin API may change between versions
- **No JavaScript plugins** — unlike ESLint, you can't write plugins in JS/TS
- **Limited fix capabilities** — rewrites work for simple transformations; complex multi-step fixes are not supported
- **No plugin registry** — plugins are local files, no npm distribution yet

### When to Use GritQL vs. Request a Built-in Rule

Use GritQL for:
- Project-specific conventions
- Temporary migration patterns
- Company-internal API enforcement

Request a built-in rule for:
- Language-wide best practices
- Framework-specific patterns shared across the community
- Performance or security concerns
