# Performance Optimization

> Source: https://zustand.docs.pmnd.rs

## Table of Contents
- [Re-render Prevention](#re-render-prevention)
- [Selector Optimization](#selector-optimization)
- [Store Design for Performance](#store-design-for-performance)
- [Transient Updates](#transient-updates)
- [Large Collections](#large-collections)
- [DevTools Overhead](#devtools-overhead)
- [Profiling and Debugging](#profiling-and-debugging)

## Re-render Prevention

Zustand's primary performance tool is selective subscription. Components only re-render when their selected state changes:

```typescript
// OPTIMAL — subscribes to single primitive
function CountDisplay() {
  const count = useStore((s) => s.count) // Re-renders only when count changes
  return <span>{count}</span>
}

// SUBOPTIMAL — subscribes to entire store
function CountDisplay() {
  const { count } = useStore() // Re-renders on ANY state change
  return <span>{count}</span>
}
```

**Rule of thumb:** Select the smallest piece of state your component needs.

## Selector Optimization

**Avoid creating new references:**
```typescript
// BAD — new object every call = always re-renders
const userData = useStore((s) => ({
  name: s.user.name,
  avatar: s.user.avatar,
}))

// GOOD — useShallow performs shallow comparison
import { useShallow } from 'zustand/react/shallow'

const userData = useStore(
  useShallow((s) => ({
    name: s.user.name,
    avatar: s.user.avatar,
  }))
)
```

**Avoid inline filter/map:**
```typescript
// BAD — filter creates new array reference every time
const activeItems = useStore((s) => s.items.filter((i) => i.active))
// This causes re-render even when activeItems haven't changed!

// GOOD — wrap with useShallow
const activeItems = useStore(
  useShallow((s) => s.items.filter((i) => i.active))
)

// BETTER — if items change often but active set is stable,
// memoize in the component
function ActiveList() {
  const items = useStore((s) => s.items)
  const activeItems = useMemo(
    () => items.filter((i) => i.active),
    [items]
  )
  return <List items={activeItems} />
}
```

**Stable action references:**
```typescript
// Actions defined in create() have stable references
const increment = useStore((s) => s.increment)
// This NEVER causes re-renders — same function identity always

// You can safely pass actions to memoized children
<MemoizedButton onClick={increment} />
```

## Store Design for Performance

**Split hot and cold state:**
```typescript
// BAD — mouse position updates cause settings to "change"
const useStore = create<State>()((set) => ({
  mousePosition: { x: 0, y: 0 },  // Updates 60fps
  theme: 'dark',                    // Changes rarely
  setMouse: (pos) => set({ mousePosition: pos }),
}))

// GOOD — separate stores for different update frequencies
const useMouseStore = create<MouseState>()((set) => ({
  position: { x: 0, y: 0 },
  setPosition: (pos) => set({ position: pos }),
}))

const useSettingsStore = create<SettingsState>()((set) => ({
  theme: 'dark',
  setTheme: (theme) => set({ theme }),
}))
```

**Normalize data to avoid deep equality checks:**
```typescript
// BAD — deep nested array, any update replaces entire tree
interface State {
  conversations: {
    id: string
    messages: Message[]
    participants: User[]
  }[]
}

// GOOD — normalized, select by ID
interface State {
  conversations: Record<string, Conversation>
  messages: Record<string, Message>
  messagesByConversation: Record<string, string[]> // ID arrays
}

// Component selects single conversation
function ConversationView({ id }: { id: string }) {
  const conversation = useStore((s) => s.conversations[id])
  // Only re-renders when THIS conversation changes
  return <div>{conversation.title}</div>
}
```

## Transient Updates

For high-frequency updates (animations, mouse tracking, scroll position), bypass React rendering entirely:

```typescript
interface AnimationState {
  progress: number
  setProgress: (p: number) => void
}

const useAnimationStore = create<AnimationState>()((set) => ({
  progress: 0,
  setProgress: (progress) => set({ progress }),
}))

// Direct DOM manipulation — no React re-renders
function ProgressBar() {
  const barRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const unsub = useAnimationStore.subscribe((state) => {
      if (barRef.current) {
        barRef.current.style.width = `${state.progress}%`
      }
    })
    return unsub
  }, [])

  return <div ref={barRef} className="progress-bar" />
}

// Drive updates from requestAnimationFrame
function startAnimation() {
  let frame: number
  const animate = () => {
    const { progress, setProgress } = useAnimationStore.getState()
    if (progress < 100) {
      setProgress(progress + 0.5)
      frame = requestAnimationFrame(animate)
    }
  }
  frame = requestAnimationFrame(animate)
  return () => cancelAnimationFrame(frame)
}
```

## Large Collections

**Virtualization + selective subscription:**
```typescript
// Only the visible items re-render
function VirtualizedList() {
  const itemIds = useStore(useShallow((s) => s.itemIds)) // Array of IDs

  return (
    <VirtualList
      count={itemIds.length}
      itemSize={50}
      renderItem={(index) => <ListItem id={itemIds[index]} />}
    />
  )
}

// Each item subscribes to its own data
function ListItem({ id }: { id: string }) {
  const item = useStore((s) => s.items[id])
  return <div>{item.name}</div>
}
```

**Pagination pattern:**
```typescript
interface PaginatedState {
  pages: Record<number, Item[]>
  currentPage: number
  loadPage: (page: number) => Promise<void>
}

function CurrentPageItems() {
  const page = useStore((s) => s.currentPage)
  const items = useStore((s) => s.pages[s.currentPage] ?? [])
  // Only re-renders when current page's items change
  return <ItemList items={items} />
}
```

## DevTools Overhead

Redux DevTools can cause performance issues with large or frequent state updates:

```typescript
// Disable in production
devtools(storeFn, {
  enabled: process.env.NODE_ENV === 'development',
})

// Limit DevTools history
devtools(storeFn, {
  maxAge: 25, // Keep only last 25 state changes
})

// Skip noisy actions
const setMouse = (pos: Position) =>
  set({ mousePosition: pos }, undefined, { type: 'mouse/move', skip: true })
```

## Profiling and Debugging

**Track re-renders:**
```typescript
function useWhyDidYouRender(storeName: string) {
  const renderCount = useRef(0)
  renderCount.current++

  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[${storeName}] render #${renderCount.current}`)
    }
  })
}

// Add to suspected components
function ExpensiveComponent() {
  useWhyDidYouRender('ExpensiveComponent')
  const data = useStore((s) => s.data)
  return <HeavyRender data={data} />
}
```

**Subscription debugging:**
```typescript
// Log all state changes with diff
if (process.env.NODE_ENV === 'development') {
  useStore.subscribe((state, prev) => {
    const changes = Object.entries(state).filter(
      ([key, val]) => val !== (prev as any)[key]
    )
    console.log('Changed keys:', changes.map(([k]) => k))
  })
}
```

**Performance checklist:**

| Issue | Symptom | Fix |
|-------|---------|-----|
| Entire store selected | All components re-render | Use specific selectors |
| New object in selector | Component re-renders without state change | Use `useShallow` |
| Frequent transient state | Janky animations | Use `subscribe` + refs |
| Large normalized data | Slow on any update | Select by ID, virtualize lists |
| DevTools with large state | UI freezes | Disable in prod, limit history |
| Deep nested updates | Excessive spreading | Use immer middleware |
