# Testing

> Source: https://zustand.docs.pmnd.rs/learn/guides/testing

## Table of Contents
- [Testing Philosophy](#testing-philosophy)
- [Resetting Stores Between Tests](#resetting-stores-between-tests)
- [Testing Store Logic](#testing-store-logic)
- [Testing Components](#testing-components)
- [Mocking Stores](#mocking-stores)
- [Integration Testing Patterns](#integration-testing-patterns)
- [Vitest and Jest Setup](#vitest-and-jest-setup)

## Testing Philosophy

Zustand recommends testing through components rather than testing stores in isolation. This ensures you test actual user behavior, not implementation details. However, unit testing store logic directly is also valid for complex business logic.

## Resetting Stores Between Tests

Stores are module-level singletons — state persists across tests unless explicitly reset:

```typescript
// test-utils.ts
import { act } from '@testing-library/react'

// Reset a specific store
export function resetStore(store: { setState: Function; getInitialState?: Function }) {
  const initialState = store.getInitialState?.() ?? {}
  act(() => {
    store.setState(initialState, true)
  })
}
```

**Using afterEach for automatic reset:**
```typescript
import { afterEach } from 'vitest'
import { useCounterStore } from '@/store/counter'
import { useAuthStore } from '@/store/auth'

afterEach(() => {
  useCounterStore.setState({ count: 0 }, true)
  useAuthStore.setState({ user: null, token: null, isAuthenticated: false }, true)
})
```

**Store with getInitialState (recommended pattern):**
```typescript
const initialState = {
  count: 0,
  items: [],
}

interface StoreState {
  count: number
  items: Item[]
  increment: () => void
}

const useStore = create<StoreState>()((set) => ({
  ...initialState,
  increment: () => set((s) => ({ count: s.count + 1 })),
}))

// Expose for testing
useStore.getInitialState = () => initialState
```

## Testing Store Logic

Test store actions directly without rendering components:

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { useCartStore } from '@/store/cart'

describe('Cart Store', () => {
  beforeEach(() => {
    useCartStore.setState({ items: [], total: 0 }, true)
  })

  it('adds an item to cart', () => {
    const product = { id: '1', name: 'Widget', price: 9.99 }
    useCartStore.getState().addItem(product, 2)

    const state = useCartStore.getState()
    expect(state.items).toHaveLength(1)
    expect(state.items[0].quantity).toBe(2)
    expect(state.total).toBeCloseTo(19.98)
  })

  it('increments quantity for existing item', () => {
    const product = { id: '1', name: 'Widget', price: 9.99 }
    useCartStore.getState().addItem(product, 1)
    useCartStore.getState().addItem(product, 3)

    const state = useCartStore.getState()
    expect(state.items).toHaveLength(1)
    expect(state.items[0].quantity).toBe(4)
  })

  it('removes an item', () => {
    const product = { id: '1', name: 'Widget', price: 9.99 }
    useCartStore.getState().addItem(product, 1)
    useCartStore.getState().removeItem('1')

    expect(useCartStore.getState().items).toHaveLength(0)
    expect(useCartStore.getState().total).toBe(0)
  })
})
```

**Testing async actions:**
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuthStore } from '@/store/auth'
import * as authApi from '@/api/auth'

vi.mock('@/api/auth')

describe('Auth Store', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, token: null, isLoading: false, error: null }, true)
  })

  it('handles successful login', async () => {
    const mockUser = { id: '1', email: 'test@example.com' }
    vi.mocked(authApi.login).mockResolvedValue({
      user: mockUser,
      token: 'abc123',
    })

    await useAuthStore.getState().login('test@example.com', 'password')

    const state = useAuthStore.getState()
    expect(state.user).toEqual(mockUser)
    expect(state.token).toBe('abc123')
    expect(state.isLoading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('handles login failure', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid credentials'))

    await useAuthStore.getState().login('bad@email.com', 'wrong')

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.error).toBe('Invalid credentials')
    expect(state.isLoading).toBe(false)
  })
})
```

## Testing Components

Use React Testing Library to test components that consume Zustand stores:

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { useCounterStore } from '@/store/counter'
import { Counter } from '@/components/Counter'

describe('Counter Component', () => {
  beforeEach(() => {
    useCounterStore.setState({ count: 0 }, true)
  })

  it('displays the count', () => {
    render(<Counter />)
    expect(screen.getByText('Count: 0')).toBeInTheDocument()
  })

  it('increments on button click', async () => {
    render(<Counter />)
    fireEvent.click(screen.getByRole('button', { name: /increment/i }))
    expect(screen.getByText('Count: 1')).toBeInTheDocument()
  })

  it('renders with pre-set state', () => {
    useCounterStore.setState({ count: 42 })
    render(<Counter />)
    expect(screen.getByText('Count: 42')).toBeInTheDocument()
  })
})
```

## Mocking Stores

For isolated component testing, mock the entire store:

```typescript
import { vi } from 'vitest'
import { create } from 'zustand'

// Mock the store module
vi.mock('@/store/auth', () => ({
  useAuthStore: create(() => ({
    user: { id: '1', name: 'Test User', email: 'test@test.com' },
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  })),
}))

// Or mock per-test
import { useAuthStore } from '@/store/auth'

it('shows logout button when authenticated', () => {
  useAuthStore.setState({ isAuthenticated: true, user: mockUser })
  render(<UserMenu />)
  expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument()
})

it('shows login button when not authenticated', () => {
  useAuthStore.setState({ isAuthenticated: false, user: null })
  render(<UserMenu />)
  expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
})
```

## Integration Testing Patterns

Testing store interactions across components:

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useCartStore } from '@/store/cart'
import { ProductList } from '@/components/ProductList'
import { CartSummary } from '@/components/CartSummary'

describe('Shopping flow', () => {
  beforeEach(() => {
    useCartStore.setState({ items: [], total: 0 }, true)
  })

  it('adding product updates cart badge', async () => {
    render(
      <>
        <ProductList products={mockProducts} />
        <CartSummary />
      </>
    )

    fireEvent.click(screen.getByTestId('add-product-1'))

    await waitFor(() => {
      expect(screen.getByTestId('cart-count')).toHaveTextContent('1')
    })
  })
})
```

**Testing subscriptions:**
```typescript
it('fires subscription on state change', () => {
  const listener = vi.fn()
  const unsub = useCounterStore.subscribe(listener)

  useCounterStore.getState().increment()

  expect(listener).toHaveBeenCalledTimes(1)
  expect(listener).toHaveBeenCalledWith(
    expect.objectContaining({ count: 1 }),
    expect.objectContaining({ count: 0 })
  )

  unsub()
})
```

## Vitest and Jest Setup

**Vitest setup (recommended):**
```typescript
// vitest.setup.ts
import { afterEach } from 'vitest'
import '@testing-library/jest-dom/vitest'

// Global store reset (optional — prefer per-test reset)
afterEach(() => {
  // Reset specific stores if needed
})
```

**Jest setup:**
```typescript
// jest.setup.ts
import '@testing-library/jest-dom'
```

**Test utilities:**
```typescript
// test-utils.tsx
import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'

function AllProviders({ children }: { children: React.ReactNode }) {
  return <>{children}</> // Zustand needs no providers!
}

export function renderWithStore(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllProviders, ...options })
}

export function setupStore(overrides: Partial<AppState> = {}) {
  useAppStore.setState(overrides)
}
```

## Common Testing Pitfalls

1. **State leaking between tests** — Always reset stores in `beforeEach` or `afterEach`
2. **Testing implementation, not behavior** — Prefer asserting what the user sees over checking internal store state
3. **Forgetting act() wrapper** — State updates from outside React need `act()` in tests
4. **Async state not awaited** — Use `waitFor` for async actions that update state
5. **Module-level store initialization** — Stores initialize once; mocks must be set up before import or use `vi.mock`
