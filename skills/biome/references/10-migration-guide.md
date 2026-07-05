# Biome — Migration Guide

> Source: [biomejs.dev/guides/migrate-eslint-prettier](https://biomejs.dev/guides/migrate-eslint-prettier/)

## Table of Contents
- [Migration Overview](#migration-overview)
- [Step 1: Install Biome](#step-1-install-biome)
- [Step 2: Migrate Prettier Config](#step-2-migrate-prettier-config)
- [Step 3: Migrate ESLint Config](#step-3-migrate-eslint-config)
- [Step 4: Suppress Existing Violations](#step-4-suppress-existing-violations)
- [Step 5: Update Editor Settings](#step-5-update-editor-settings)
- [Step 6: Update CI Pipeline](#step-6-update-ci-pipeline)
- [Step 7: Remove Old Tools](#step-7-remove-old-tools)
- [ESLint Rule Mapping](#eslint-rule-mapping)
- [Prettier Option Mapping](#prettier-option-mapping)
- [Handling Missing Rules](#handling-missing-rules)
- [Gradual Migration Strategy](#gradual-migration-strategy)
- [Common Pitfalls](#common-pitfalls)

---

## Migration Overview

Biome provides automated migration commands that convert ESLint and Prettier configs into a `biome.json`. The process:

1. Install Biome alongside existing tools
2. Migrate configs with `biome migrate`
3. Suppress current violations for gradual cleanup
4. Update editor and CI
5. Remove ESLint and Prettier

## Step 1: Install Biome

```bash
npm i -D --save-exact @biomejs/biome
npx @biomejs/biome init
```

## Step 2: Migrate Prettier Config

```bash
npx @biomejs/biome migrate prettier --write
```

This reads your Prettier config (`.prettierrc`, `.prettierrc.json`, `prettier.config.js`, etc.) and converts options to `biome.json` formatter settings. It also migrates `.prettierignore` patterns.

**Supported config formats:** JSON, YAML (partial), JavaScript (requires Node.js)
**Not supported:** TOML, JSON5

### What Gets Migrated

| Prettier Option | Biome Equivalent |
|-----------------|------------------|
| `tabWidth` | `formatter.indentWidth` |
| `useTabs` | `formatter.indentStyle` |
| `printWidth` | `formatter.lineWidth` |
| `endOfLine` | `formatter.lineEnding` |
| `semi` | `javascript.formatter.semicolons` |
| `singleQuote` | `javascript.formatter.quoteStyle` |
| `trailingComma` | `javascript.formatter.trailingCommas` |
| `bracketSpacing` | `formatter.bracketSpacing` |
| `arrowParens` | `javascript.formatter.arrowParentheses` |
| `jsxSingleQuote` | `javascript.formatter.jsxQuoteStyle` |

## Step 3: Migrate ESLint Config

```bash
npx @biomejs/biome migrate eslint --write
```

This reads your ESLint config (`.eslintrc`, `.eslintrc.json`, `eslint.config.js`, etc.) and maps rules to Biome equivalents.

```bash
# Include "inspired" rules (not direct ports but similar intent)
npx @biomejs/biome migrate eslint --write --include-inspired
```

### What Gets Migrated

- ESLint core rules → Biome equivalents
- `@typescript-eslint` rules → Biome equivalents
- `eslint-plugin-react` rules → Biome react domain
- `eslint-plugin-react-hooks` rules → Biome react domain
- `eslint-plugin-jsx-a11y` rules → Biome a11y group
- `.eslintignore` patterns → `files.includes` with negation
- `extends` and shared configs → resolved and merged

**Limitations:**
- Requires Node.js to resolve ESLint plugins
- YAML configs not supported
- Custom ESLint rules have no automatic mapping

## Step 4: Suppress Existing Violations

After migration, your codebase likely has many new violations. Suppress them all to adopt immediately:

```bash
# Add biome-ignore comments to all current violations
npx @biomejs/biome lint --suppress --reason "TODO: fix during biome migration" ./src
```

This adds inline suppression comments:

```typescript
// biome-ignore lint/suspicious/noExplicitAny: TODO: fix during biome migration
const data: any = fetchData();
```

Then fix violations incrementally — search for the suppression reason to find them:

```bash
grep -r "TODO: fix during biome migration" src/
```

## Step 5: Update Editor Settings

### VS Code

```json
// .vscode/settings.json
{
  "editor.defaultFormatter": "biomejs.biome",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports.biome": "explicit"
  },
  // Disable old extensions
  "prettier.enable": false,
  "eslint.enable": false
}
```

```json
// .vscode/extensions.json
{
  "recommendations": ["biomejs.biome"],
  "unwantedRecommendations": ["esbenp.prettier-vscode", "dbaeumer.vscode-eslint"]
}
```

## Step 6: Update CI Pipeline

### GitHub Actions

```yaml
# .github/workflows/code-quality.yml
name: Code Quality
on: [push, pull_request]

jobs:
  biome:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npx @biomejs/biome ci --reporter=github ./src
```

### GitLab CI

```yaml
biome:
  stage: lint
  script:
    - npm ci
    - npx @biomejs/biome ci --reporter=gitlab ./src
```

Replace old ESLint/Prettier CI steps.

## Step 7: Remove Old Tools

```bash
# Remove ESLint
npm uninstall eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin \
  eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-jsx-a11y \
  eslint-plugin-import eslint-config-prettier eslint-plugin-prettier

# Remove Prettier
npm uninstall prettier prettier-plugin-organize-imports

# Remove lint-staged (if only used for ESLint/Prettier)
npm uninstall lint-staged

# Delete config files
rm -f .eslintrc* .eslintignore .prettierrc* .prettierignore
rm -f eslint.config.* prettier.config.*
```

## ESLint Rule Mapping

Common ESLint rules and their Biome equivalents:

| ESLint Rule | Biome Rule |
|-------------|------------|
| `no-unused-vars` | `correctness/noUnusedVariables` |
| `no-console` | `suspicious/noConsole` |
| `no-debugger` | `suspicious/noDebugger` |
| `eqeqeq` | `suspicious/noDoubleEquals` |
| `no-var` | `style/noVar` |
| `prefer-const` | `style/useConst` |
| `no-eval` | `security/noGlobalEval` |
| `@typescript-eslint/no-explicit-any` | `suspicious/noExplicitAny` |
| `@typescript-eslint/no-unused-vars` | `correctness/noUnusedVariables` |
| `react-hooks/exhaustive-deps` | `correctness/useExhaustiveDependencies` |
| `react-hooks/rules-of-hooks` | `correctness/useHookAtTopLevel` |
| `jsx-a11y/alt-text` | `a11y/useAltText` |
| `import/no-default-export` | `style/noDefaultExport` |

## Prettier Option Mapping

| Prettier | Biome |
|----------|-------|
| `tabWidth: 4` | `"indentWidth": 4` |
| `useTabs: true` | `"indentStyle": "tab"` |
| `printWidth: 100` | `"lineWidth": 100` |
| `semi: false` | `"semicolons": "asNeeded"` |
| `singleQuote: true` | `"quoteStyle": "single"` |
| `trailingComma: "es5"` | `"trailingCommas": "es5"` |
| `bracketSpacing: false` | `"bracketSpacing": false` |
| `arrowParens: "avoid"` | `"arrowParentheses": "asNeeded"` |
| `endOfLine: "crlf"` | `"lineEnding": "crlf"` |

## Handling Missing Rules

Some ESLint rules have no Biome equivalent. Options:

1. **Check if it's in nursery** — experimental rules may already exist
2. **Use GritQL plugins** — write a custom rule
3. **Keep ESLint for specific rules** — run both tools (not recommended long-term)
4. **Accept the gap** — many ESLint rules are redundant with TypeScript's own checks

## Gradual Migration Strategy

For large codebases, migrate incrementally:

### Phase 1: Formatter Only
```json
{
  "formatter": { "enabled": true },
  "linter": { "enabled": false }
}
```
Remove Prettier, keep ESLint temporarily.

### Phase 2: Add Recommended Rules
```json
{
  "formatter": { "enabled": true },
  "linter": { "enabled": true, "rules": { "preset": "recommended" } }
}
```
Suppress all existing violations.

### Phase 3: Enable Strict Rules
Enable `noExplicitAny`, `noDefaultExport`, etc. as the team fixes violations.

### Phase 4: Full Migration
Remove ESLint entirely. Enable type-aware rules.

## Common Pitfalls

### Formatting diff noise
Biome and Prettier produce slightly different output for edge cases. Run `biome format --write` on the entire codebase in a single commit to avoid noisy diffs.

### lint-staged removal
Biome's `--staged` flag replaces lint-staged for Biome-supported files. If you still need lint-staged for other tools (e.g., stylelint for SCSS), keep it but remove the ESLint/Prettier entries.

### Monorepo configuration
In monorepos, install Biome at the root. Each package can have its own `biome.json` that extends the root config via `"extends"`.

### CI speed difference
Biome CI runs are typically 10-50x faster. Adjust CI timeouts if they were generous for slow ESLint runs.
