---
name: zustand
description: "Lightweight React state management with hooks-based API, flux principles, and zero boilerplate. MANDATORY TRIGGERS: zustand, bear store, pmndrs state, useStore, create store zustand. Also trigger when the user wants React state management without Redux boilerplate, needs global client state in React, asks about store slices or zustand middleware (persist/immer/devtools), or discusses preventing re-renders with selectors. When in doubt about whether to use this skill for React state management tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["react", "state-management", "zustand", "hooks", "typescript", "frontend"]
---

# Zustand

> v5.0.14 | https://zustand.docs.pmnd.rs | https://github.com/pmndrs/zustand

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Starting with Zustand, comparing state management options, understanding core philosophy |
| [01-core-concepts.md](references/01-core-concepts.md) | Creating stores, using set/get, subscribing to state, accessing state outside React |
| [02-selectors.md](references/02-selectors.md) | Selecting state, preventing re-renders, useShallow, equality functions |
| [03-actions-updates.md](references/03-actions-updates.md) | Defining actions, async operations, setState patterns, transient updates |
| [04-middleware.md](references/04-middleware.md) | Middleware overview, composition order, combining persist/devtools/immer |
| [05-persist-middleware.md](references/05-persist-middleware.md) | Persisting state to storage, migrations, partialize, custom storage engines |
| [06-immer-middleware.md](references/06-immer-middleware.md) | Mutable-style updates for nested state, combining with other middleware |
| [07-slices-pattern.md](references/07-slices-pattern.md) | Modular store composition, cross-slice communication, scaling stores |
| [08-typescript.md](references/08-typescript.md) | TypeScript patterns, StateCreator typing, middleware generics, store interfaces |
| [09-react-patterns.md](references/09-react-patterns.md) | Context + Zustand, store factories, SSR, multiple instances, React 18+ patterns |
| [10-testing.md](references/10-testing.md) | Testing stores and components, mocking, resetting state between tests |
| [11-performance.md](references/11-performance.md) | Optimization strategies, derived state, avoiding unnecessary re-renders |
| [12-migration-recipes.md](references/12-migration-recipes.md) | Migrating from Redux/v4, common recipes, vanilla store usage |

## Installation

```bash
npm install zustand
# or
pnpm add zustand
# or
yarn add zustand
```

## Quick Reference

- [Official Docs](https://zustand.docs.pmnd.rs)
- [GitHub Repository](https://github.com/pmndrs/zustand)
- [npm Package](https://www.npmjs.com/package/zustand)
