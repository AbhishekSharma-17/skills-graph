# Actions and State Updates

> Source: https://zustand.docs.pmnd.rs

## Table of Contents
- [Defining Actions](#defining-actions)
- [Synchronous Updates](#synchronous-updates)
- [Async Actions](#async-actions)
- [Batch Updates](#batch-updates)
- [Transient Updates](#transient-updates)
- [setState from Outside](#setstate-from-outside)
- [Action Patterns](#action-patterns)

## Defining Actions

Actions are functions inside the store that call `set` to update state. They have access to both `set` (update state) and `get` (read current state):

```typescript
interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

const useAuthStore = create<AuthState>()((set, get) => ({
  user: null,
  token: null,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const { user, token } = await authApi.login(email, password)
      set({ user, token, isLoading: false })
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false })
    }
  },

  logout: () => {
    set({ user: null, token: null })
    authApi.revokeToken(get().token)
  },

  refreshToken: async () => {
    const { token } = get()
    if (!token) return
    const newToken = await authApi.refresh(token)
    set({ token: newToken })
  },
}))
```

## Synchronous Updates

**Object merge (shallow):**
```typescript
set({ count: 10 })
set({ user: { name: 'Alice' } }) // Replaces entire user object
```

**Updater function (access previous state):**
```typescript
set((state) => ({ count: state.count + 1 }))
set((state) => ({
  items: [...state.items, newItem],
}))
```

**Replace entire state:**
```typescript
set(newCompleteState, true) // Second arg = replace mode
```

**Nested object updates (immutable):**
```typescript
set((state) => ({
  settings: {
    ...state.settings,
    theme: {
      ...state.settings.theme,
      primaryColor: '#3b82f6',
    },
  },
}))
```

## Async Actions

Actions can be async — no special middleware needed:

```typescript
const useProductStore = create<ProductState>()((set, get) => ({
  products: [],
  isLoading: false,
  error: null,

  fetchProducts: async (category?: string) => {
    set({ isLoading: true, error: null })
    try {
      const products = await api.getProducts({ category })
      set({ products, isLoading: false })
    } catch (err) {
      set({
        error: (err as Error).message,
        isLoading: false,
      })
    }
  },

  createProduct: async (data: CreateProductInput) => {
    const product = await api.createProduct(data)
    set((state) => ({
      products: [...state.products, product],
    }))
    return product
  },

  deleteProduct: async (id: string) => {
    // Optimistic update
    const previousProducts = get().products
    set((state) => ({
      products: state.products.filter((p) => p.id !== id),
    }))
    try {
      await api.deleteProduct(id)
    } catch {
      // Rollback on failure
      set({ products: previousProducts })
    }
  },
}))
```

## Batch Updates

Multiple `set` calls in the same synchronous block are automatically batched by React 18+:

```typescript
const useStore = create<State>()((set) => ({
  count: 0,
  name: '',
  resetAll: () => {
    // React 18 batches these into a single re-render
    set({ count: 0 })
    set({ name: '' })
  },
  // Or combine into one set call (preferred)
  resetAllBetter: () => {
    set({ count: 0, name: '' })
  },
}))
```

For async operations, each `set` after an `await` triggers its own render:

```typescript
const fetchData = async () => {
  set({ loading: true })        // Render 1
  const data = await fetch(url) // Async boundary
  set({ data, loading: false }) // Render 2 (separate from Render 1)
}
```

## Transient Updates

For frequent updates that shouldn't trigger re-renders (animations, mouse position):

```typescript
interface CursorState {
  position: { x: number; y: number }
  setPosition: (x: number, y: number) => void
}

const useCursorStore = create<CursorState>()((set) => ({
  position: { x: 0, y: 0 },
  setPosition: (x, y) => set({ position: { x, y } }),
}))

// Subscribe without causing re-renders
function Cursor() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Direct subscription — bypasses React rendering
    const unsub = useCursorStore.subscribe((state) => {
      if (ref.current) {
        ref.current.style.transform =
          `translate(${state.position.x}px, ${state.position.y}px)`
      }
    })
    return unsub
  }, [])

  return <div ref={ref} className="cursor" />
}
```

## setState from Outside

Update stores from anywhere — event handlers, utilities, third-party integrations:

```typescript
// Keyboard shortcut handler
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    useModalStore.setState({ isOpen: false })
  }
  if (e.ctrlKey && e.key === 'z') {
    useHistoryStore.getState().undo()
  }
})

// Axios interceptor
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  }
)

// WebSocket handler
socket.on('notification', (data) => {
  useNotificationStore.setState((state) => ({
    notifications: [data, ...state.notifications],
    unreadCount: state.unreadCount + 1,
  }))
})
```

## Action Patterns

**Conditional updates:**
```typescript
const useCartStore = create<CartState>()((set, get) => ({
  items: [],
  addItem: (product: Product, quantity: number) => {
    const existing = get().items.find((i) => i.productId === product.id)
    if (existing) {
      set((state) => ({
        items: state.items.map((i) =>
          i.productId === product.id
            ? { ...i, quantity: i.quantity + quantity }
            : i
        ),
      }))
    } else {
      set((state) => ({
        items: [...state.items, { productId: product.id, product, quantity }],
      }))
    }
  },
}))
```

**Debounced actions:**
```typescript
import { debounce } from 'lodash-es'

const useSearchStore = create<SearchState>()((set) => ({
  query: '',
  results: [],
  isSearching: false,

  setQuery: (query: string) => {
    set({ query })
    debouncedSearch(query)
  },
}))

const debouncedSearch = debounce(async (query: string) => {
  if (!query.trim()) {
    useSearchStore.setState({ results: [], isSearching: false })
    return
  }
  useSearchStore.setState({ isSearching: true })
  const results = await searchApi(query)
  useSearchStore.setState({ results, isSearching: false })
}, 300)
```

**Action composition (calling other actions):**
```typescript
const useStore = create<State>()((set, get) => ({
  items: [],
  selectedId: null,

  selectItem: (id: string) => set({ selectedId: id }),
  clearSelection: () => set({ selectedId: null }),

  deleteSelected: async () => {
    const { selectedId } = get()
    if (!selectedId) return
    await api.delete(selectedId)
    set((state) => ({
      items: state.items.filter((i) => i.id !== selectedId),
      selectedId: null,
    }))
  },
}))
```

## Common Pitfalls

1. **Forgetting to spread nested state** — `set({ user: { name: 'new' } })` replaces the entire user object; use `set(s => ({ user: { ...s.user, name: 'new' } }))` for partial updates
2. **Stale closures in async** — Always use `get()` inside async callbacks rather than capturing state at the start
3. **Mutating state** — Never modify state objects directly; always create new references
4. **Over-updating** — Avoid calling `set` in rapid loops; batch where possible
