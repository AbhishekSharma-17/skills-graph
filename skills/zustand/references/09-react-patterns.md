# React Patterns

> Source: https://zustand.docs.pmnd.rs

## Table of Contents
- [Context + Zustand](#context--zustand)
- [Store Factories](#store-factories)
- [Multiple Store Instances](#multiple-store-instances)
- [SSR and Next.js](#ssr-and-nextjs)
- [React Server Components](#react-server-components)
- [Suspense Integration](#suspense-integration)
- [Common React Patterns](#common-react-patterns)

## Context + Zustand

While Zustand stores are typically module-level singletons, combining with React Context enables:
- Multiple independent store instances (per-widget, per-route)
- Props-driven initial state
- Testability through dependency injection

```typescript
import { createContext, useContext, useRef } from 'react'
import { createStore, useStore } from 'zustand'

// Define the store type
interface CounterState {
  count: number
  increment: () => void
  decrement: () => void
}

type CounterStore = ReturnType<typeof createCounterStore>

// Store factory
const createCounterStore = (initialCount = 0) =>
  createStore<CounterState>()((set) => ({
    count: initialCount,
    increment: () => set((s) => ({ count: s.count + 1 })),
    decrement: () => set((s) => ({ count: s.count - 1 })),
  }))

// Context
const CounterContext = createContext<CounterStore | null>(null)

// Provider component
function CounterProvider({
  children,
  initialCount,
}: {
  children: React.ReactNode
  initialCount?: number
}) {
  const storeRef = useRef<CounterStore | null>(null)
  if (!storeRef.current) {
    storeRef.current = createCounterStore(initialCount)
  }
  return (
    <CounterContext value={storeRef.current}>
      {children}
    </CounterContext>
  )
}

// Custom hook to consume the context store
function useCounterStore<T>(selector: (state: CounterState) => T): T {
  const store = useContext(CounterContext)
  if (!store) throw new Error('useCounterStore must be used within CounterProvider')
  return useStore(store, selector)
}

// Usage — multiple independent instances
function App() {
  return (
    <div>
      <CounterProvider initialCount={0}>
        <Counter label="A" />
      </CounterProvider>
      <CounterProvider initialCount={100}>
        <Counter label="B" />
      </CounterProvider>
    </div>
  )
}

function Counter({ label }: { label: string }) {
  const count = useCounterStore((s) => s.count)
  const increment = useCounterStore((s) => s.increment)
  return <button onClick={increment}>{label}: {count}</button>
}
```

## Store Factories

Create parameterized stores for reusable patterns:

```typescript
import { createStore, useStore } from 'zustand'

interface FormState<T> {
  values: T
  errors: Partial<Record<keyof T, string>>
  touched: Partial<Record<keyof T, boolean>>
  setField: <K extends keyof T>(field: K, value: T[K]) => void
  setError: (field: keyof T, error: string) => void
  touch: (field: keyof T) => void
  reset: () => void
}

function createFormStore<T extends Record<string, unknown>>(initialValues: T) {
  return createStore<FormState<T>>()((set) => ({
    values: initialValues,
    errors: {},
    touched: {},
    setField: (field, value) =>
      set((state) => ({
        values: { ...state.values, [field]: value },
      })),
    setError: (field, error) =>
      set((state) => ({
        errors: { ...state.errors, [field]: error },
      })),
    touch: (field) =>
      set((state) => ({
        touched: { ...state.touched, [field]: true },
      })),
    reset: () => set({ values: initialValues, errors: {}, touched: {} }),
  }))
}

// Usage with a specific form
const loginFormStore = createFormStore({ email: '', password: '' })

function LoginForm() {
  const email = useStore(loginFormStore, (s) => s.values.email)
  const setField = useStore(loginFormStore, (s) => s.setField)

  return (
    <input
      value={email}
      onChange={(e) => setField('email', e.target.value)}
    />
  )
}
```

## Multiple Store Instances

For components that need their own isolated state (lists of editors, tabs):

```typescript
import { createStore, useStore } from 'zustand'
import { createContext, useContext, useMemo } from 'react'

interface EditorState {
  content: string
  cursor: number
  setContent: (content: string) => void
  setCursor: (pos: number) => void
}

type EditorStore = ReturnType<typeof createEditorStore>

const createEditorStore = (initial: string) =>
  createStore<EditorState>()((set) => ({
    content: initial,
    cursor: 0,
    setContent: (content) => set({ content }),
    setCursor: (cursor) => set({ cursor }),
  }))

const EditorContext = createContext<EditorStore | null>(null)

function useEditorStore<T>(selector: (state: EditorState) => T) {
  const store = useContext(EditorContext)
  if (!store) throw new Error('Missing EditorProvider')
  return useStore(store, selector)
}

function EditorPanel({ initialContent }: { initialContent: string }) {
  const store = useMemo(() => createEditorStore(initialContent), [])
  return (
    <EditorContext value={store}>
      <EditorToolbar />
      <EditorCanvas />
    </EditorContext>
  )
}

// Multiple tabs, each with their own editor state
function App() {
  return (
    <div className="tabs">
      <EditorPanel initialContent="# File 1" />
      <EditorPanel initialContent="# File 2" />
      <EditorPanel initialContent="# File 3" />
    </div>
  )
}
```

## SSR and Next.js

Zustand works with SSR but requires care around hydration:

```typescript
// store/counter.ts
import { create } from 'zustand'

interface CounterState {
  count: number
  increment: () => void
}

export const useCounterStore = create<CounterState>()((set) => ({
  count: 0,
  increment: () => set((s) => ({ count: s.count + 1 })),
}))
```

**Next.js App Router — initializing from server data:**
```typescript
// app/page.tsx (Server Component)
import { CounterInitializer } from './counter-initializer'

export default async function Page() {
  const initialCount = await fetchCount() // Server-side fetch
  return (
    <>
      <CounterInitializer count={initialCount} />
      <ClientCounter />
    </>
  )
}

// counter-initializer.tsx (Client Component)
'use client'
import { useRef } from 'react'
import { useCounterStore } from '@/store/counter'

export function CounterInitializer({ count }: { count: number }) {
  const initialized = useRef(false)
  if (!initialized.current) {
    useCounterStore.setState({ count })
    initialized.current = true
  }
  return null
}
```

**With persist middleware + SSR (avoiding hydration mismatch):**
```typescript
'use client'
import { useEffect, useState } from 'react'

function ThemeToggle() {
  const [hydrated, setHydrated] = useState(false)
  const theme = usePreferencesStore((s) => s.theme)

  useEffect(() => {
    setHydrated(true)
  }, [])

  // Render nothing or a placeholder during SSR
  if (!hydrated) return <div className="h-8 w-8" />

  return <button>{theme === 'dark' ? 'Light' : 'Dark'}</button>
}
```

## React Server Components

Zustand is a client-side library. In the App Router:

```typescript
// Server Component — cannot use Zustand directly
// app/dashboard/page.tsx
export default async function DashboardPage() {
  const data = await fetchDashboardData()
  return <DashboardClient initialData={data} />
}

// Client Component — uses Zustand
// app/dashboard/dashboard-client.tsx
'use client'
import { useEffect } from 'react'
import { useDashboardStore } from '@/store/dashboard'

export function DashboardClient({ initialData }: { initialData: Data }) {
  useEffect(() => {
    useDashboardStore.setState({ data: initialData })
  }, [initialData])

  const data = useDashboardStore((s) => s.data)
  return <Dashboard data={data} />
}
```

## Suspense Integration

Zustand doesn't natively support Suspense for data fetching, but you can integrate:

```typescript
// Throw a promise to suspend
const useDataStore = create<DataState>()((set) => ({
  data: null,
  promise: null as Promise<void> | null,

  fetch: () => {
    const promise = api.getData().then((data) => {
      set({ data, promise: null })
    })
    set({ promise })
  },
}))

function DataComponent() {
  const { data, promise, fetch } = useDataStore()

  if (promise) throw promise // Suspense catches this
  if (!data) {
    fetch()
    throw useDataStore.getState().promise
  }

  return <div>{data.name}</div>
}
```

## Common React Patterns

**Resetting store on route change:**
```typescript
import { useEffect } from 'react'
import { usePathname } from 'next/navigation'

function RouteResetProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  useEffect(() => {
    usePageStore.setState(initialPageState)
  }, [pathname])

  return <>{children}</>
}
```

**Conditional store selection:**
```typescript
function UserWidget({ showEmail }: { showEmail: boolean }) {
  const name = useUserStore((s) => s.name)
  // Only subscribe to email when needed
  const email = useUserStore((s) => (showEmail ? s.email : null))

  return (
    <div>
      {name}
      {email && <span>{email}</span>}
    </div>
  )
}
```

**Store in custom hooks:**
```typescript
function useAuth() {
  const user = useAuthStore((s) => s.user)
  const login = useAuthStore((s) => s.login)
  const logout = useAuthStore((s) => s.logout)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return { user, login, logout, isAuthenticated }
}
```
