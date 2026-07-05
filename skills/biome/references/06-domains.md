# Biome — Domains

> Source: [biomejs.dev/linter](https://biomejs.dev/linter/) | Version: 2.5.x

## Table of Contents
- [What Are Domains](#what-are-domains)
- [Available Domains](#available-domains)
- [Auto-Detection](#auto-detection)
- [Manual Configuration](#manual-configuration)
- [React Domain](#react-domain)
- [Solid Domain](#solid-domain)
- [Next.js Domain](#nextjs-domain)
- [Test Domain](#test-domain)
- [Node.js Domain](#nodejs-domain)
- [Project Domain](#project-domain)
- [Combining Domains](#combining-domains)

---

## What Are Domains

Domains are Biome's way of grouping technology-specific lint rules. Instead of installing separate ESLint plugins for React, testing libraries, and Node.js, Biome bundles framework-specific rules and activates them automatically based on your `package.json` dependencies.

Domains solve the ESLint plugin fatigue problem: no more `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, `eslint-plugin-testing-library`, etc.

## Available Domains

| Domain | Detects Via | Covers |
|--------|-------------|--------|
| `react` | `react` in dependencies | React component patterns, hooks, JSX |
| `solid` | `solid-js` in dependencies | Solid.js reactivity, destructuring, signals |
| `next` | `next` in dependencies | Next.js specific patterns and conventions |
| `test` | `vitest`, `jest`, `mocha`, etc. | Testing patterns and assertions |
| `node` | `@types/node` in dependencies | Node.js API usage patterns |
| `project` | Always available | Type-aware cross-module rules |

## Auto-Detection

When `package.json` lists a framework as a dependency, Biome automatically enables the corresponding domain's recommended rules. No configuration needed:

```json
// package.json
{
  "dependencies": {
    "react": "^19.0.0",
    "next": "^15.0.0"
  },
  "devDependencies": {
    "vitest": "^3.0.0"
  }
}
```

With this `package.json`, Biome automatically enables `react`, `next`, and `test` domain rules.

## Manual Configuration

Override auto-detection or enable/disable domains explicitly:

```json
{
  "linter": {
    "domains": {
      "react": "recommended",
      "solid": "off",
      "test": "all",
      "project": "recommended"
    }
  }
}
```

Values:
- `"recommended"` — enable curated subset
- `"all"` — enable every rule in the domain
- `"off"` — disable the domain entirely

## React Domain

Covers rules from `eslint-plugin-react`, `eslint-plugin-react-hooks`, and `eslint-plugin-jsx-a11y`.

### Key React Rules

| Rule | Category | What It Catches |
|------|----------|-----------------|
| `useExhaustiveDependencies` | correctness | Missing/extra deps in hooks |
| `useHookAtTopLevel` | correctness | Hooks in conditionals/loops |
| `noChildrenProp` | correctness | Passing `children` as prop AND as children |
| `useJsxKeyInIterable` | correctness | Missing `key` in `.map()` JSX |
| `noUnstableNestedComponents` | correctness | Component definitions inside render |
| `noDirectMutationState` | suspicious | `this.state.x = y` mutations |
| `useButtonType` | a11y | `<button>` without `type` |
| `noUselessFragments` | complexity | Unnecessary `<></>`  |
| `noStringRefs` | suspicious | Legacy string refs |

### Configuration

```json
{
  "linter": {
    "domains": {
      "react": "recommended"
    },
    "rules": {
      "correctness": {
        "useExhaustiveDependencies": {
          "level": "error",
          "options": {
            "hooks": [
              { "name": "useQuery", "stableResult": true }
            ]
          }
        }
      }
    }
  },
  "javascript": {
    "jsxRuntime": "transparent"
  }
}
```

The `jsxRuntime` option controls whether `React` must be in scope for JSX:
- `"transparent"` — new JSX transform (React 17+), no import needed
- `"reactClassic"` — old transform, requires `import React`

## Solid Domain

Rules specific to Solid.js's fine-grained reactivity model.

### Key Solid Rules

| Rule | What It Catches |
|------|-----------------|
| `noSolidDestructuredProps` | Destructuring props (breaks reactivity) |

```jsx
// Error: destructuring breaks Solid reactivity tracking
function Counter({ count, onIncrement }) {
  return <button onClick={onIncrement}>{count}</button>;
}

// Fixed: access props as a single object
function Counter(props) {
  return <button onClick={props.onIncrement}>{props.count}</button>;
}
```

## Next.js Domain

Rules for Next.js App Router and Pages Router patterns.

### Key Next.js Rules

| Rule | What It Catches |
|------|-----------------|
| `noHeadElement` | Using `<head>` instead of `next/head` |
| `noImgElement` | Using `<img>` instead of `next/image` |
| `noDocumentImportInPage` | Importing `next/document` outside `_document` |
| `noHeadImportInDocument` | Importing `next/head` inside `_document` |

```jsx
// Error: noImgElement — use Next.js Image for optimization
<img src="/hero.jpg" alt="Hero" />

// Fixed
import Image from "next/image";
<Image src="/hero.jpg" alt="Hero" width={800} height={400} />
```

## Test Domain

Rules for testing frameworks (Vitest, Jest, Mocha, etc.).

### Key Test Rules

| Rule | What It Catches |
|------|-----------------|
| `noDuplicateTestHooks` | Duplicate `beforeEach` / `afterEach` in same scope |
| `noFocusedTests` | `.only` left in test files (blocks CI) |
| `noSkippedTests` | `.skip` left in test files |
| `noExportsInTest` | Exporting from test files |
| `useExpectType` | Missing type assertions in type tests |

```typescript
// Error: noFocusedTests — blocks other tests in CI
describe("auth", () => {
  it.only("should log in", () => {  // will be the only test that runs!
    expect(login()).toBe(true);
  });
});

// Fixed — remove .only before committing
describe("auth", () => {
  it("should log in", () => {
    expect(login()).toBe(true);
  });
});
```

## Node.js Domain

Rules for Node.js-specific patterns and deprecated APIs.

### Key Node Rules

| Rule | What It Catches |
|------|-----------------|
| `noProcessEnv` | Direct `process.env` access (prefer configuration objects) |
| `noDeprecatedNodejsApi` | Deprecated Node.js APIs |

## Project Domain

The project domain contains type-aware rules that require the Scanner. See the [Type-Aware Rules](05-type-aware-rules.md) reference for details.

Key rules: `noFloatingPromises`, `noMisusedPromises`, `noUndeclaredDependencies`.

## Combining Domains

Domains compose cleanly. A typical full-stack Next.js project:

```json
{
  "linter": {
    "domains": {
      "react": "recommended",
      "next": "recommended",
      "test": "recommended",
      "node": "recommended",
      "project": "recommended"
    },
    "rules": {
      "preset": "recommended"
    }
  }
}
```

Domain rules work alongside category rules. A rule can belong to both a category (e.g., `correctness`) and a domain (e.g., `react`). Enabling either activates the rule.
