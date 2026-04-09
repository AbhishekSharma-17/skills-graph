# DevTools & Testing

> Source: [TanStack Query Docs — DevTools](https://tanstack.com/query/v5/docs/framework/react/devtools) | [Testing](https://tanstack.com/query/v5/docs/framework/react/guides/testing)

## Table of Contents

- [React Query DevTools](#react-query-devtools)
- [DevTools Configuration](#devtools-configuration)
- [ESLint Plugin](#eslint-plugin)
- [Testing Setup](#testing-setup)
- [Testing Queries](#testing-queries)
- [Testing Mutations](#testing-mutations)
- [Mocking Network Requests](#mocking-network-requests)
- [Testing Custom Hooks](#testing-custom-hooks)
- [Testing with Suspense](#testing-with-suspense)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## React Query DevTools

Install and add the DevTools to your app:

```bash
npm install @tanstack/react-query-devtools
```

```tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

### What DevTools Show

- All active, inactive, and stale queries
- Query data, status, and metadata
- Cache state and timing
- Manual refetch, invalidate, and remove operations
- Mutation state and history

### Production Build

DevTools are **automatically excluded** from production builds when using `@tanstack/react-query-devtools` (it checks `process.env.NODE_ENV`).

### Floating Mode vs Embedded

```tsx
// Floating button (default) — toggle panel
<ReactQueryDevtools initialIsOpen={false} />

// Embedded in a specific location
import { ReactQueryDevtools } from '@tanstack/react-query-devtools/production'
<ReactQueryDevtools initialIsOpen={true} />
```

---

## DevTools Configuration

```tsx
<ReactQueryDevtools
  initialIsOpen={false}        // Start closed
  buttonPosition="bottom-left" // Button position: 'bottom-left' | 'bottom-right' | 'top-left' | 'top-right'
  position="bottom"            // Panel position: 'top' | 'bottom' | 'left' | 'right'
  client={queryClient}         // Optional: specific client (defaults to context)
/>
```

---

## ESLint Plugin

```bash
npm install -D @tanstack/eslint-plugin-query
```

```js
// eslint.config.js (flat config)
import pluginQuery from '@tanstack/eslint-plugin-query'

export default [
  ...pluginQuery.configs['flat/recommended'],
]
```

### Rules

| Rule | Description |
|------|-------------|
| `exhaustive-deps` | Ensures queryKey includes all variables used in queryFn |
| `no-rest-destructuring` | Warns against rest destructuring query results |
| `stable-query-client` | Ensures QueryClient is created stably |
| `no-unstable-deps` | Detects unstable dependencies in query options |

---

## Testing Setup

Create a test wrapper with a fresh QueryClient per test:

```tsx
// test/utils.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,       // Don't retry in tests
        gcTime: Infinity,   // Don't garbage collect during test
      },
    },
  })
}

export function createWrapper() {
  const queryClient = createTestQueryClient()
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

export function renderWithClient(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) {
  const queryClient = createTestQueryClient()
  return {
    ...render(ui, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
      ...options,
    }),
    queryClient,
  }
}
```

### Critical: Fresh Client Per Test

```tsx
// WRONG — shared client leaks state between tests
const queryClient = new QueryClient()

// CORRECT — new client per test
function createTestQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}
```

---

## Testing Queries

### Basic Query Test

```tsx
import { screen, waitFor } from '@testing-library/react'
import { renderWithClient } from './test/utils'

test('renders todos', async () => {
  const { queryClient } = renderWithClient(<TodoList />)

  // Wait for query to resolve
  await waitFor(() => {
    expect(screen.getByText('Buy groceries')).toBeInTheDocument()
  })
})
```

### Pre-Seeding Cache

```tsx
test('renders with pre-seeded data', () => {
  const queryClient = createTestQueryClient()

  // Seed the cache before rendering
  queryClient.setQueryData(['todos'], [
    { id: 1, title: 'Test Todo', completed: false },
  ])

  render(
    <QueryClientProvider client={queryClient}>
      <TodoList />
    </QueryClientProvider>,
  )

  expect(screen.getByText('Test Todo')).toBeInTheDocument()
})
```

---

## Testing Mutations

```tsx
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

test('creates a new todo', async () => {
  const user = userEvent.setup()
  renderWithClient(<AddTodoForm />)

  await user.type(screen.getByRole('textbox'), 'New Todo')
  await user.click(screen.getByRole('button', { name: /add/i }))

  await waitFor(() => {
    expect(screen.getByText('New Todo')).toBeInTheDocument()
  })
})
```

### Testing Mutation Side Effects

```tsx
test('invalidates todos after adding', async () => {
  const user = userEvent.setup()
  const { queryClient } = renderWithClient(<AddTodoForm />)

  const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

  await user.click(screen.getByRole('button', { name: /add/i }))

  await waitFor(() => {
    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ['todos'] }),
    )
  })
})
```

---

## Mocking Network Requests

### With MSW (Mock Service Worker) — Recommended

```bash
npm install -D msw
```

```tsx
// mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/todos', () => {
    return HttpResponse.json([
      { id: 1, title: 'Test Todo', completed: false },
    ])
  }),

  http.post('/api/todos', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({ id: 2, ...body, completed: false })
  }),
]

// mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
```

```tsx
// test setup (vitest.setup.ts)
import { server } from './mocks/server'

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

### Override Handlers Per Test

```tsx
import { server } from './mocks/server'
import { http, HttpResponse } from 'msw'

test('shows error on fetch failure', async () => {
  server.use(
    http.get('/api/todos', () => {
      return HttpResponse.json({ message: 'Server error' }, { status: 500 })
    }),
  )

  renderWithClient(<TodoList />)

  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument()
  })
})
```

---

## Testing Custom Hooks

```tsx
import { renderHook, waitFor } from '@testing-library/react'
import { createWrapper } from './test/utils'

test('useTodos returns todos', async () => {
  const { result } = renderHook(() => useTodos(), {
    wrapper: createWrapper(),
  })

  await waitFor(() => {
    expect(result.current.isSuccess).toBe(true)
  })

  expect(result.current.data).toHaveLength(2)
  expect(result.current.data?.[0].title).toBe('Test Todo')
})
```

---

## Testing with Suspense

```tsx
test('renders todos with suspense', async () => {
  renderWithClient(
    <Suspense fallback={<div>Loading...</div>}>
      <TodoList /> {/* Uses useSuspenseQuery */}
    </Suspense>,
  )

  // Initially shows fallback
  expect(screen.getByText('Loading...')).toBeInTheDocument()

  // Then shows data
  await waitFor(() => {
    expect(screen.getByText('Test Todo')).toBeInTheDocument()
  })
})
```

---

## Common Patterns

### Disable Retries and Background Refetch in Tests

```tsx
const testClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: false,
    },
  },
})
```

### Test Loading and Error States

```tsx
test('shows loading state', () => {
  renderWithClient(<TodoList />)
  expect(screen.getByText('Loading...')).toBeInTheDocument()
})

test('shows error state', async () => {
  server.use(
    http.get('/api/todos', () => HttpResponse.error()),
  )

  renderWithClient(<TodoList />)

  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument()
  })
})
```

---

## Common Pitfalls

1. **Shared QueryClient across tests** — Creates flaky tests. Always create a fresh client.

2. **Retry: 3 in tests** — Default retry causes slow tests and unexpected behavior. Set `retry: false`.

3. **Not waiting for async operations** — Use `waitFor` from Testing Library, not manual timeouts.

4. **Testing implementation details** — Test what the user sees, not internal cache state.

5. **Forgetting to reset MSW handlers** — `server.resetHandlers()` in `afterEach` prevents handler leaks between tests.

---

## Related

- **00-overview.md** — Initial setup
- **11-typescript.md** — Type-safe patterns
- **01-queries.md** — useQuery reference
