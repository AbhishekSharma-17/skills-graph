# Zustand Overview

> Source: https://zustand.docs.pmnd.rs | https://github.com/pmndrs/zustand

## What is Zustand?

Zustand (German for "state") is a lightweight, fast, and scalable state management library for React. Built by the pmndrs (Poimandres) collective, it provides a hooks-based API with flux principles, zero boilerplate, and no providers required.

At ~1KB gzipped, Zustand is one of the smallest state management solutions available while handling complex scenarios like the zombie child problem, React concurrency, and context loss between mixed renderers.

## When to Use Zustand

**Use Zustand when you need:**
- Global client state (UI state, settings, auth tokens, feature flags)
- Shared state across unrelated components without prop drilling
- State accessible outside React (event handlers, WebSocket callbacks, utilities)
- Simple alternative to Redux without reducers, action types, or dispatch
- State persistence (localStorage, sessionStorage, async storage)

**Consider alternatives when:**
- Server state caching/synchronization needed → TanStack Query
- Atomic/granular reactivity for fine-grained updates → Jotai
- Complex enterprise state with strict patterns → Redux Toolkit
- Component-local state only → useState/useReducer

## Core Philosophy

1. **Minimal API surface** — One function (`create`) does everything
2. **No providers** — Stores are accessible anywhere without wrapping components
3. **Selective subscriptions** — Components only re-render when their selected state changes
4. **Framework agnostic core** — Vanilla store works outside React
5. **Middleware composable** — Persist, immer, devtools stack naturally

## Installation

```bash
npm install zustand
```

**Peer dependencies:** React 18+ (v5 dropped React <18 support)

**Optional middleware packages:**
```bash
npm install immer          # For immer middleware
```

## Quick Start

```typescript
import { create } from 'zustand'

interface CounterState {
  count: number
  increment: () => void
  decrement: () => void
  reset: () => void
}

const useCounterStore = create<CounterState>()((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
  reset: () => set({ count: 0 }),
}))

function Counter() {
  const count = useCounterStore((state) => state.count)
  const increment = useCounterStore((state) => state.increment)

  return (
    <div>
      <span>{count}</span>
      <button onClick={increment}>+</button>
    </div>
  )
}
```

## Architecture at a Glance

```
┌─────────────────────────────────────────────┐
│                 Zustand Store                │
├─────────────────────────────────────────────┤
│  State        │  Actions        │  Computed  │
│  { count: 0 } │  increment()    │  derived() │
│  { user: .. } │  fetchUser()    │            │
├─────────────────────────────────────────────┤
│              Middleware Stack                │
│  persist → devtools → immer → store         │
├─────────────────────────────────────────────┤
│           Subscription System               │
│  selector → equality check → re-render      │
└─────────────────────────────────────────────┘
         │                    │
    React Components     Vanilla JS
    (useStore hook)      (getState/subscribe)
```

## Comparison with Other Solutions

| Feature | Zustand | Redux Toolkit | Jotai | React Context |
|---------|---------|---------------|-------|---------------|
| Bundle size | ~1KB | ~12KB | ~3KB | 0 (built-in) |
| Boilerplate | Minimal | Moderate | Minimal | Moderate |
| Provider needed | No | Yes | Yes | Yes |
| DevTools | Middleware | Built-in | Extension | No |
| Persistence | Middleware | Manual | Atomized | Manual |
| Outside React | Yes | Yes | Limited | No |
| Learning curve | Low | Medium | Low | Low |
| TypeScript DX | Excellent | Excellent | Good | Good |

## Key Concepts Preview

- **Store** — A hook containing state and actions, created with `create()`
- **Selector** — Function passed to the hook to pick specific state
- **Action** — Function inside the store that calls `set()` to update state
- **Middleware** — Wrapper that enhances store behavior (persist, devtools, immer)
- **Slice** — Modular piece of state composed into a larger store
- **Vanilla store** — Framework-agnostic store created with `createStore()`

## Ecosystem

| Package | Purpose |
|---------|---------|
| `zustand` | Core library with React bindings |
| `zustand/middleware` | persist, devtools, immer, subscribeWithSelector, combine |
| `zustand/middleware/immer` | Immer integration for mutable-style updates |
| `zustand/react/shallow` | useShallow hook for array/object selectors |
| `zustand/vanilla` | Framework-agnostic store (no React dependency) |
| `zustand/traditional` | createWithEqualityFn for custom equality |

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v5.0 | Oct 2024 | Dropped React <18, native useSyncExternalStore, smaller bundle |
| v4.0 | Jun 2022 | Simplified API, deprecated createContext |
| v3.0 | Mar 2021 | Middleware overhaul, TypeScript improvements |
