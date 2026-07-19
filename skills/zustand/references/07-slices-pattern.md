# Slices Pattern

> Source: https://zustand.docs.pmnd.rs/learn/guides/slices-pattern

## Table of Contents
- [Overview](#overview)
- [Creating Individual Slices](#creating-individual-slices)
- [Composing Slices](#composing-slices)
- [Cross-Slice Communication](#cross-slice-communication)
- [TypeScript Slices](#typescript-slices)
- [Middleware with Slices](#middleware-with-slices)
- [Scaling Patterns](#scaling-patterns)

## Overview

As stores grow, the slices pattern enables modular state management by dividing a monolithic store into smaller, focused units. Each slice owns a specific domain (auth, cart, UI) and can be developed and tested independently.

```
┌─────────── Bound Store ───────────┐
│                                    │
│  ┌─────────┐  ┌─────────┐        │
│  │ Auth    │  │ Cart    │        │
│  │ Slice   │  │ Slice   │        │
│  └─────────┘  └─────────┘        │
│  ┌─────────┐  ┌─────────┐        │
│  │ UI      │  │ Product │        │
│  │ Slice   │  │ Slice   │        │
│  └─────────┘  └─────────┘        │
│                                    │
│  ┌────────────────────────���───┐   │
│  │     Middleware (persist,   │   │
│  │     devtools, immer)       │   │
│  └────────────────────────────┘   │
└────────────────────────────────────┘
```

## Creating Individual Slices

Each slice is a function that receives `set` and `get` and returns its state + actions:

```typescript
// slices/authSlice.ts
import { StateCreator } from 'zustand'

export interface AuthSlice {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const createAuthSlice: StateCreator<
  AppState,  // Full combined state type
  [],        // No middleware mutators on slice level
  [],        // No middleware mutators on slice level
  AuthSlice  // This slice's type
> = (set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  login: async (email, password) => {
    const { user, token } = await authApi.login(email, password)
    set({ user, token, isAuthenticated: true })
  },

  logout: () => {
    set({ user: null, token: null, isAuthenticated: false })
  },
})
```

```typescript
// slices/cartSlice.ts
export interface CartSlice {
  items: CartItem[]
  total: number
  addItem: (product: Product, qty: number) => void
  removeItem: (id: string) => void
  clearCart: () => void
}

export const createCartSlice: StateCreator<
  AppState, [], [], CartSlice
> = (set, get) => ({
  items: [],
  total: 0,

  addItem: (product, qty) =>
    set((state) => {
      const items = [...state.items]
      const existing = items.find((i) => i.productId === product.id)
      if (existing) {
        existing.quantity += qty
      } else {
        items.push({ productId: product.id, product, quantity: qty })
      }
      return {
        items,
        total: items.reduce((sum, i) => sum + i.product.price * i.quantity, 0),
      }
    }),

  removeItem: (id) =>
    set((state) => {
      const items = state.items.filter((i) => i.productId !== id)
      return {
        items,
        total: items.reduce((sum, i) => sum + i.product.price * i.quantity, 0),
      }
    }),

  clearCart: () => set({ items: [], total: 0 }),
})
```

## Composing Slices

Combine slices into a single store using the spread operator:

```typescript
// store.ts
import { create } from 'zustand'
import { createAuthSlice, AuthSlice } from './slices/authSlice'
import { createCartSlice, CartSlice } from './slices/cartSlice'
import { createUISlice, UISlice } from './slices/uiSlice'

export type AppState = AuthSlice & CartSlice & UISlice

export const useAppStore = create<AppState>()((...a) => ({
  ...createAuthSlice(...a),
  ...createCartSlice(...a),
  ...createUISlice(...a),
}))
```

**Usage in components:**
```typescript
function CartBadge() {
  const itemCount = useAppStore((state) => state.items.length)
  return <Badge count={itemCount} />
}

function UserMenu() {
  const user = useAppStore((state) => state.user)
  const logout = useAppStore((state) => state.logout)
  return user ? <button onClick={logout}>{user.name}</button> : null
}
```

## Cross-Slice Communication

Use `get()` to access state/actions from other slices:

```typescript
// slices/checkoutSlice.ts
export interface CheckoutSlice {
  isProcessing: boolean
  checkout: () => Promise<void>
}

export const createCheckoutSlice: StateCreator<
  AppState, [], [], CheckoutSlice
> = (set, get) => ({
  isProcessing: false,

  checkout: async () => {
    const { items, total, user, clearCart } = get()

    if (!user) throw new Error('Must be logged in')
    if (items.length === 0) throw new Error('Cart is empty')

    set({ isProcessing: true })
    try {
      await orderApi.create({
        userId: user.id,
        items,
        total,
      })
      clearCart() // Call action from CartSlice
    } finally {
      set({ isProcessing: false })
    }
  },
})
```

## TypeScript Slices

The full TypeScript pattern with `StateCreator`:

```typescript
import { StateCreator } from 'zustand'

// Define each slice interface
export interface FishSlice {
  fishes: number
  addFish: () => void
}

export interface BearSlice {
  bears: number
  addBear: () => void
  eatFish: () => void // Cross-slice action
}

// Combined state
type AppState = FishSlice & BearSlice

// Slice creators with full typing
export const createFishSlice: StateCreator<
  AppState, [], [], FishSlice
> = (set) => ({
  fishes: 0,
  addFish: () => set((state) => ({ fishes: state.fishes + 1 })),
})

export const createBearSlice: StateCreator<
  AppState, [], [], BearSlice
> = (set) => ({
  bears: 0,
  addBear: () => set((state) => ({ bears: state.bears + 1 })),
  eatFish: () => set((state) => ({ fishes: Math.max(0, state.fishes - 1) })),
})

// Combined store
const useStore = create<AppState>()((...a) => ({
  ...createFishSlice(...a),
  ...createBearSlice(...a),
}))
```

## Middleware with Slices

**Important:** Apply middleware only at the combined store level, never inside individual slices.

```typescript
import { devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

// Correct: middleware wraps the combined store
const useAppStore = create<AppState>()(
  devtools(
    persist(
      immer((...a) => ({
        ...createAuthSlice(...a),
        ...createCartSlice(...a),
        ...createUISlice(...a),
      })),
      {
        name: 'app-store',
        partialize: (state) => ({
          user: state.user,
          token: state.token,
          items: state.items,
        }),
      }
    ),
    { name: 'AppStore' }
  )
)
```

**With immer, slices use mutation syntax:**
```typescript
// When immer middleware is applied at store level,
// all slices can use mutation syntax in set()
export const createCartSlice: StateCreator<
  AppState,
  [['zustand/immer', never]],  // Declare immer mutator
  [],
  CartSlice
> = (set) => ({
  items: [],
  addItem: (product, qty) =>
    set((state) => {
      state.items.push({ productId: product.id, product, quantity: qty })
    }),
})
```

## Scaling Patterns

**File structure for large apps:**
```
src/
├── store/
│   ├── index.ts              # Combined store export
│   ├── types.ts              # AppState type
│   └── slices/
│       ├── auth.ts
│       ├── cart.ts
│       ├── ui.ts
│       ├── notifications.ts
│       └── products.ts
```

**Separate stores vs. slices:**
```typescript
// Option A: Single combined store (slices pattern)
// Best when: slices need to communicate, shared middleware
const useAppStore = create<AppState>()(/* combined */)

// Option B: Multiple independent stores
// Best when: completely independent domains, no cross-communication
const useAuthStore = create<AuthState>()(/* ... */)
const useCartStore = create<CartState>()(/* ... */)
const useUIStore = create<UIState>()(/* ... */)
```

**Decision guide:**
| Scenario | Approach |
|----------|----------|
| Cart needs auth state for checkout | Slices (combined store) |
| Theme toggle independent of all other state | Separate store |
| Notifications triggered by multiple domains | Slices (cross-slice access) |
| Feature flag store used app-wide | Separate store (simple, standalone) |

## Common Pitfalls

1. **Applying middleware inside slices** — Always apply at the combined store level
2. **Circular slice dependencies** — Use `get()` for lazy access instead of importing other slices directly
3. **Slice name collisions** — Ensure no two slices export the same state key or action name
4. **Over-slicing** — Don't create a slice for a single boolean; group related state logically
