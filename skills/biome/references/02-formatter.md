# Biome — Formatter

> Source: [biomejs.dev/formatter](https://biomejs.dev/formatter/)

## Table of Contents
- [Philosophy](#philosophy)
- [Global Options](#global-options)
- [JavaScript / TypeScript Options](#javascript--typescript-options)
- [JSON Options](#json-options)
- [CSS Options](#css-options)
- [HTML Options](#html-options)
- [CLI Usage](#cli-usage)
- [Suppressing Formatting](#suppressing-formatting)
- [EditorConfig Support](#editorconfig-support)
- [Prettier Differences](#prettier-differences)
- [Formatting Broken Code](#formatting-broken-code)
- [Common Configurations](#common-configurations)

---

## Philosophy

Biome adopts Prettier's opinionated approach: minimal options, consistent output, end debates about style. The formatter intentionally limits configuration to prevent bikeshedding. If Prettier formats it one way, Biome almost certainly does too (97% compatibility).

## Global Options

These apply to all supported languages:

```json
{
  "formatter": {
    "enabled": true,
    "indentStyle": "tab",
    "indentWidth": 2,
    "lineWidth": 80,
    "lineEnding": "lf",
    "attributePosition": "auto",
    "bracketSpacing": true,
    "trailingNewline": true,
    "formatWithErrors": false
  }
}
```

| Option | Default | Values | Description |
|--------|---------|--------|-------------|
| `enabled` | `true` | `true` / `false` | Enable/disable formatter |
| `indentStyle` | `"tab"` | `"tab"` / `"space"` | Indentation character |
| `indentWidth` | `2` | 1-24 | Spaces per indent level |
| `lineWidth` | `80` | 1-320 | Column limit before wrapping |
| `lineEnding` | `"lf"` | `"lf"` / `"crlf"` / `"cr"` | Line ending character |
| `attributePosition` | `"auto"` | `"auto"` / `"multiline"` | HTML/JSX attribute placement |
| `bracketSpacing` | `true` | `true` / `false` | Spaces in object literals `{ x }` |
| `trailingNewline` | `true` | `true` / `false` | Newline at end of file |
| `formatWithErrors` | `false` | `true` / `false` | Format files with syntax errors |

## JavaScript / TypeScript Options

```json
{
  "javascript": {
    "formatter": {
      "quoteStyle": "double",
      "jsxQuoteStyle": "double",
      "quoteProperties": "asNeeded",
      "trailingCommas": "all",
      "semicolons": "always",
      "arrowParentheses": "always",
      "bracketSameLine": false,
      "operatorLinebreak": "after"
    }
  }
}
```

| Option | Default | Values | Description |
|--------|---------|--------|-------------|
| `quoteStyle` | `"double"` | `"double"` / `"single"` | String quote character |
| `jsxQuoteStyle` | `"double"` | `"double"` / `"single"` | JSX attribute quotes |
| `quoteProperties` | `"asNeeded"` | `"asNeeded"` / `"preserve"` | Object property quoting |
| `trailingCommas` | `"all"` | `"all"` / `"es5"` / `"none"` | Trailing comma style |
| `semicolons` | `"always"` | `"always"` / `"asNeeded"` | Semicolon insertion |
| `arrowParentheses` | `"always"` | `"always"` / `"asNeeded"` | Arrow function parens |
| `bracketSameLine` | `false` | `true` / `false` | JSX closing bracket placement |
| `operatorLinebreak` | `"after"` | `"after"` / `"before"` | Operator position on line break |

## JSON Options

```json
{
  "json": {
    "formatter": {
      "trailingCommas": "none",
      "bracketSpacing": true
    }
  }
}
```

## CSS Options

```json
{
  "css": {
    "formatter": {
      "quoteStyle": "double"
    }
  }
}
```

## HTML Options

```json
{
  "html": {
    "formatter": {
      "attributePosition": "auto",
      "bracketSameLine": false,
      "whitespaceSensitivity": "css",
      "selfCloseVoidElements": "never",
      "indentScriptAndStyle": false
    }
  }
}
```

| Option | Default | Values | Description |
|--------|---------|--------|-------------|
| `whitespaceSensitivity` | `"css"` | `"css"` / `"strict"` / `"ignore"` | How whitespace is handled |
| `selfCloseVoidElements` | `"never"` | `"never"` / `"always"` | `<br>` vs `<br />` |
| `indentScriptAndStyle` | `false` | `true` / `false` | Indent `<script>` and `<style>` contents |

## CLI Usage

```bash
# Check formatting (dry run, reports differences)
npx @biomejs/biome format ./src

# Apply formatting
npx @biomejs/biome format --write ./src

# Format specific files
npx @biomejs/biome format --write src/index.ts src/utils.ts

# Format only staged files
npx @biomejs/biome format --write --staged

# Format changed files since default branch
npx @biomejs/biome format --write --changed

# Override options via CLI
npx @biomejs/biome format --write --indent-style=space --indent-width=4 ./src

# Watch mode (re-format on changes)
npx @biomejs/biome format --write --watch ./src
```

## Suppressing Formatting

### Suppress an entire file

```javascript
// biome-ignore-all format: this file uses custom formatting
const matrix = [
  [1, 0, 0],
  [0, 1, 0],
  [0, 0, 1],
];
```

### Suppress a single node

```javascript
// biome-ignore format: alignment matters here
const routes = {
  home:     "/",
  about:    "/about",
  contact:  "/contact",
};
```

### Via configuration (disable for specific files)

```json
{
  "overrides": [
    {
      "includes": ["*.min.js", "vendor/**"],
      "formatter": { "enabled": false }
    }
  ]
}
```

## EditorConfig Support

Biome can read `.editorconfig` files (v1.9+):

```json
{
  "formatter": {
    "useEditorconfig": true
  }
}
```

When enabled, `.editorconfig` settings are read but `biome.json` always takes precedence for any overlapping settings.

## Prettier Differences

Biome is 97% compatible with Prettier. Key differences:

| Aspect | Biome Default | Prettier Default |
|--------|---------------|------------------|
| Indent style | Tabs | Spaces |
| Trailing commas | `"all"` | `"all"` (same since Prettier 3) |
| Quote style | Double | Double |

Intentional deviations where Biome improves on Prettier:
- Better parenthesization in certain edge cases
- More consistent handling of template literals
- Improved TypeScript type formatting in some scenarios

To match Prettier defaults exactly during migration:

```json
{
  "formatter": {
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 80
  }
}
```

Or use the migration command: `npx @biomejs/biome migrate prettier --write`

## Formatting Broken Code

Biome's error-resilient parser can format files with syntax errors. Enable this for editor format-on-save during active development:

```json
{
  "formatter": {
    "formatWithErrors": true
  }
}
```

The formatter skips regions it cannot parse and formats the rest. This is especially useful when typing — your file is always in a "broken" state mid-keystroke.

## Common Configurations

### Match Prettier Defaults

```json
{
  "formatter": {
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 80
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "double",
      "trailingCommas": "all",
      "semicolons": "always"
    }
  }
}
```

### Airbnb-like Style

```json
{
  "formatter": {
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "trailingCommas": "all",
      "semicolons": "always",
      "arrowParentheses": "always"
    }
  }
}
```

### Standard JS Style

```json
{
  "formatter": {
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 80
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "asNeeded",
      "trailingCommas": "none"
    }
  }
}
```
