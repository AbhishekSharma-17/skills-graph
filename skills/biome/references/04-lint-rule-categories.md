# Biome — Lint Rule Categories

> Source: [biomejs.dev/linter/rules](https://biomejs.dev/linter/rules/)

## Table of Contents
- [Accessibility (a11y)](#accessibility-a11y)
- [Complexity](#complexity)
- [Correctness](#correctness)
- [Performance](#performance)
- [Security](#security)
- [Style](#style)
- [Suspicious](#suspicious)
- [Nursery](#nursery)
- [Cross-Category Patterns](#cross-category-patterns)

---

## Accessibility (a11y)

Rules enforcing WCAG and WAI-ARIA standards for accessible web content. Most correspond to rules from `eslint-plugin-jsx-a11y`.

### Key Rules

| Rule | What It Catches |
|------|-----------------|
| `useAltText` | Missing `alt` on `<img>`, `<area>`, `<input type="image">`, `<object>` |
| `useButtonType` | `<button>` without explicit `type` attribute |
| `useValidAriaProps` | Invalid ARIA attributes |
| `useValidAriaValues` | Invalid ARIA attribute values |
| `useValidAriaRole` | Non-existent ARIA role values |
| `noAccessKey` | `accessKey` usage (inconsistent across browsers) |
| `noAriaUnsupportedOnRole` | ARIA attributes on elements that don't support them |
| `noBlankTarget` | `target="_blank"` without `rel="noreferrer"` |
| `noHeaderScope` | `scope` attribute on non-`<th>` elements |
| `useHeadingContent` | Empty heading elements |
| `useHtmlLang` | Missing `lang` attribute on `<html>` |
| `useIframeTitle` | Missing `title` on `<iframe>` |
| `useKeyWithClickEvents` | Click handlers without keyboard equivalents |
| `useMediaCaption` | `<audio>` and `<video>` without `<track>` captions |
| `useValidLang` | Invalid language codes in `lang` attributes |

### Example

```jsx
// Error: useAltText
<img src="photo.jpg" />

// Fixed
<img src="photo.jpg" alt="Team photo from 2026 offsite" />

// Error: useButtonType
<button onClick={handleClick}>Submit</button>

// Fixed
<button type="button" onClick={handleClick}>Submit</button>
```

## Complexity

Rules that simplify unnecessarily complex or verbose code patterns.

### Key Rules

| Rule | What It Catches |
|------|-----------------|
| `noForEach` | `.forEach()` when a `for...of` loop is clearer |
| `noUselessCatch` | `catch` that just rethrows the error |
| `noUselessConstructor` | Empty or redundant constructor |
| `noUselessTypeConstraint` | `extends unknown` or `extends any` constraints |
| `noUselessRename` | `import { x as x }` or `const { y: y }` |
| `noUselessFragments` | Unnecessary `<></>` React fragments |
| `noUselessLabel` | Labels on non-loop/switch statements |
| `useFlatMap` | `.map().flat()` → `.flatMap()` |
| `useOptionalChain` | `a && a.b && a.b.c` → `a?.b?.c` |
| `useSimplifiedLogicExpression` | Overly complex boolean expressions |
| `useArrowFunction` | Function expressions → arrow functions |
| `noStaticOnlyClass` | Classes with only static members (use a plain object) |

### Example

```typescript
// Error: useOptionalChain
const name = user && user.profile && user.profile.name;

// Fixed
const name = user?.profile?.name;

// Error: useFlatMap
const items = arr.map(fn).flat();

// Fixed
const items = arr.flatMap(fn);
```

## Correctness

The most critical group — detects actual programming bugs.

### Key Rules

| Rule | What It Catches |
|------|-----------------|
| `noConstAssign` | Assigning to `const` variables |
| `noUnusedVariables` | Declared but never-used variables |
| `noUnusedImports` | Imported but never-used modules |
| `noConstantCondition` | `if (true)`, `while (false)`, etc. |
| `noUndeclaredVariables` | References to undeclared identifiers |
| `noUnsafeFinally` | Control flow in `finally` blocks |
| `noVoidTypeReturn` | Returning a value from a void function |
| `noSelfAssign` | `x = x` assignments |
| `noInvalidNewBuiltin` | `new Symbol()`, `new BigInt()` |
| `useExhaustiveDependencies` | Missing deps in React `useEffect` / `useMemo` |
| `useHookAtTopLevel` | Hooks called conditionally or in loops |
| `useIsNan` | `x === NaN` instead of `Number.isNaN(x)` |
| `noUnreachable` | Code after `return`, `throw`, `continue`, `break` |
| `noInvalidUseBeforeDeclaration` | Using variables before declaration |

### Example

```typescript
// Error: noUnusedVariables
const unused = 42;

// Error: useIsNan
if (value === NaN) { }

// Fixed
if (Number.isNaN(value)) { }

// Error: useExhaustiveDependencies
useEffect(() => {
  fetchData(id);
}, []); // missing `id` in deps

// Fixed
useEffect(() => {
  fetchData(id);
}, [id]);
```

## Performance

Rules targeting runtime performance and bundle-size optimization.

### Key Rules

| Rule | What It Catches |
|------|-----------------|
| `noDelete` | `delete obj.key` (deoptimizes V8 hidden classes) |
| `noBarrelFile` | Barrel `index.ts` that re-exports everything (hurts tree-shaking) |
| `noReExportAll` | `export * from './module'` (prevents dead code elimination) |
| `noAccumulatingSpread` | Spread in reduce/loops: `[...acc, item]` (O(n²)) |
| `useTopLevelRegex` | Regex compiled inside functions (recompiled on every call) |

### Example

```typescript
// Error: noAccumulatingSpread — O(n²) complexity
const result = items.reduce((acc, item) => [...acc, item.name], []);

// Fixed — O(n) with push
const result = items.reduce((acc, item) => {
  acc.push(item.name);
  return acc;
}, [] as string[]);

// Error: noDelete — deoptimizes object shape
delete user.password;

// Fixed — assign undefined or use destructuring
const { password, ...safeUser } = user;
```

## Security

Rules preventing common security vulnerabilities.

### Key Rules

| Rule | What It Catches |
|------|-----------------|
| `noDangerouslySetInnerHtml` | React's `dangerouslySetInnerHTML` usage |
| `noDangerouslySetInnerHtmlWithChildren` | Conflicting `children` + `dangerouslySetInnerHTML` |
| `noGlobalEval` | `eval()` calls (code injection risk) |

### Example

```jsx
// Error: noDangerouslySetInnerHtml
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// Fixed — use a sanitization library
import DOMPurify from "dompurify";
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```

## Style

Rules enforcing code consistency and idiomatic patterns. These don't catch bugs but improve readability.

### Key Rules

| Rule | What It Catches |
|------|-----------------|
| `useConst` | `let` that is never reassigned |
| `useImportType` | Import used only as type without `import type` |
| `useExportType` | Export of type without `export type` |
| `useNamingConvention` | Inconsistent naming (configurable) |
| `useFilenamingConvention` | Inconsistent file names |
| `useTemplate` | String concatenation → template literals |
| `useEnumInitializers` | Enum members without explicit values |
| `noCommonJs` | `require()` / `module.exports` in ESM projects |
| `noDefaultExport` | Default exports (prefer named exports) |
| `useShorthandFunctionType` | `{ (): void }` → `() => void` |
| `noNonNullAssertion` | TypeScript `!` non-null assertions |
| `useBlockStatements` | Single-line `if` without braces |
| `noParameterAssign` | Reassigning function parameters |
| `useNumberNamespace` | `parseInt()` → `Number.parseInt()` |

### Example

```typescript
// Error: useConst — never reassigned
let name = "Biome";

// Fixed
const name = "Biome";

// Error: useImportType
import { User } from "./types"; // only used as type

// Fixed
import type { User } from "./types";
```

## Suspicious

Rules detecting code that is likely a bug or unintentional.

### Key Rules

| Rule | What It Catches |
|------|-----------------|
| `noDoubleEquals` | `==` instead of `===` |
| `noExplicitAny` | `any` type usage |
| `noConsole` | `console.log()` left in production code |
| `noDebugger` | `debugger` statements |
| `noAsyncPromiseExecutor` | `new Promise(async (resolve) => ...)` |
| `noConfusingVoidType` | `void` used outside return types |
| `noDuplicateObjectKeys` | Repeated keys in object literals |
| `noEmptyInterface` | `interface Foo {}` with no members |
| `noRedeclare` | Variable redeclaration in same scope |
| `noShadowRestrictedNames` | Shadowing `undefined`, `NaN`, `Infinity` |
| `noImplicitAnyLet` | `let x;` without type annotation |
| `noFallthroughSwitchClause` | Switch cases without `break` or `return` |
| `noMisleadingCharacterClass` | Regex with misleading character classes |
| `useDefaultSwitchClause` | Missing `default` in switch statements |

### Example

```typescript
// Error: noDoubleEquals
if (value == null) { }

// Fixed
if (value === null || value === undefined) { }
// Or: if (value == null) with suppression if intentional

// Error: noAsyncPromiseExecutor
new Promise(async (resolve) => {
  const data = await fetchData();
  resolve(data);
});
```

## Nursery

Experimental rules that are not recommended by default. They must be explicitly enabled:

```json
{
  "linter": {
    "rules": {
      "nursery": {
        "noConsoleLog": "warn",
        "useConsistentMemberAccessibility": "error"
      }
    }
  }
}
```

Nursery rules may change behavior or be removed. Once validated, they graduate to a stable group.

## Cross-Category Patterns

### Strict React Project

```json
{
  "linter": {
    "rules": {
      "preset": "recommended",
      "a11y": { "recommended": true },
      "correctness": { "useExhaustiveDependencies": "error" },
      "security": { "noDangerouslySetInnerHtml": "error" },
      "suspicious": { "noExplicitAny": "error" }
    }
  }
}
```

### Library/Package Rules

```json
{
  "linter": {
    "rules": {
      "preset": "recommended",
      "performance": {
        "noBarrelFile": "error",
        "noReExportAll": "error"
      },
      "style": {
        "noDefaultExport": "error",
        "useImportType": "error"
      }
    }
  }
}
```
