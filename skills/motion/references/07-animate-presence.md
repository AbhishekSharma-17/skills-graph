# AnimatePresence

> Source: https://motion.dev/docs/react-animate-presence | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [Basic Exit Animation](#basic-exit-animation)
- [Mode Prop](#mode-prop)
- [Props Reference](#props-reference)
- [Hooks](#hooks)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Overview

`AnimatePresence` enables exit animations for components that are removed from the React tree. Without it, removed elements disappear instantly because React unmounts them immediately.

```tsx
import { AnimatePresence, motion } from "motion/react"
```

How it works:
1. `AnimatePresence` monitors its direct children
2. When a child is removed, it keeps it in the DOM
3. The child's `exit` animation plays
4. After animation completes, the element is removed from the DOM

## Basic Exit Animation

```tsx
function Notification({ show, message }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="notification"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
        >
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
```

### Key Requirement

Every direct child of `AnimatePresence` must have a unique, stable `key` prop:

```tsx
<AnimatePresence>
  {items.map((item) => (
    <motion.div
      key={item.id}     // Stable, unique key
      exit={{ opacity: 0 }}
    />
  ))}
</AnimatePresence>
```

Do **not** use array indices as keys — React can't track removals properly.

## Mode Prop

Controls how entering and exiting children are handled.

### sync (Default)

Enter and exit animations happen simultaneously:

```tsx
<AnimatePresence mode="sync">
  <motion.div key={activeId} exit={{ opacity: 0 }}>
    {content}
  </motion.div>
</AnimatePresence>
```

Both old and new elements exist at the same time during transition. Use CSS positioning to handle overlap:

```tsx
<AnimatePresence mode="sync">
  <motion.div
    key={activeId}
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    style={{ position: "absolute" }}  // Prevent layout conflict
  />
</AnimatePresence>
```

### wait

The exiting child completes its animation before the entering child starts:

```tsx
<AnimatePresence mode="wait">
  <motion.div
    key={activeTab}
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -20 }}
  >
    {tabContent}
  </motion.div>
</AnimatePresence>
```

Only supports **one child** at a time. Best for sequential transitions like page navigation or tab switching.

Tip: Use `ease: "easeIn"` on exit and `ease: "easeOut"` on enter for smooth sequential flow.

### popLayout

Exiting elements are immediately removed from the layout flow (positioned absolutely), allowing surrounding elements to reflow instantly:

```tsx
<AnimatePresence mode="popLayout">
  {items.map((item) => (
    <motion.li
      key={item.id}
      layout
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
    />
  ))}
</AnimatePresence>
```

Works well with `layout` prop for list animations. Custom components must use `forwardRef`:

```tsx
// Required for popLayout mode
const ListItem = forwardRef(({ children }, ref) => (
  <motion.li ref={ref} layout exit={{ opacity: 0 }}>
    {children}
  </motion.li>
))
```

## Props Reference

### initial

Disable initial animations on first render:

```tsx
<AnimatePresence initial={false}>
  {/* Children present on mount won't play enter animation */}
  <motion.div
    key={activeSlide}
    initial={{ x: 300 }}    // This won't play on first render
    animate={{ x: 0 }}
    exit={{ x: -300 }}
  />
</AnimatePresence>
```

### custom

Pass dynamic data to exiting components (whose props can't be updated after removal):

```tsx
function Carousel({ images, direction }) {
  return (
    <AnimatePresence custom={direction}>
      <motion.img
        key={images[currentIndex].src}
        custom={direction}
        variants={{
          enter: (dir) => ({ x: dir > 0 ? 300 : -300 }),
          center: { x: 0 },
          exit: (dir) => ({ x: dir > 0 ? -300 : 300 }),
        }}
        initial="enter"
        animate="center"
        exit="exit"
      />
    </AnimatePresence>
  )
}
```

Access custom data in child components with `usePresenceData()`:

```tsx
function ExitingChild() {
  const data = usePresenceData()
  // data = whatever was passed to AnimatePresence's custom prop
}
```

### onExitComplete

Fires when all exiting children have finished their animations:

```tsx
<AnimatePresence onExitComplete={() => {
  // Scroll to top, update URL, etc.
  window.scrollTo(0, 0)
}}>
  {show && <motion.div exit={{ opacity: 0 }} />}
</AnimatePresence>
```

### propagate

Allow child AnimatePresence instances to react to parent exits:

```tsx
<AnimatePresence>
  {show && (
    <motion.section exit={{ opacity: 0 }}>
      <AnimatePresence propagate>
        {/* These also animate out when parent section exits */}
        <motion.div exit={{ x: -100 }} />
      </AnimatePresence>
    </motion.section>
  )}
</AnimatePresence>
```

Default: `false`. Set to `true` to cascade exit animations.

## Hooks

### useIsPresent

Check if a component is being removed:

```tsx
import { useIsPresent } from "motion/react"

function ListItem() {
  const isPresent = useIsPresent()
  // isPresent = true when mounted, false when exiting

  return (
    <motion.li
      style={{
        position: isPresent ? "relative" : "absolute",
      }}
    />
  )
}
```

### usePresence

Manual control over when the element is removed from the DOM:

```tsx
import { usePresence } from "motion/react"

function CustomExitComponent() {
  const [isPresent, safeToRemove] = usePresence()

  useEffect(() => {
    if (!isPresent) {
      // Run custom exit logic
      performCustomAnimation().then(() => {
        safeToRemove()  // Now React can unmount this component
      })
    }
  }, [isPresent, safeToRemove])

  return <div>Custom animated content</div>
}
```

### usePresenceData

Access the `custom` prop from AnimatePresence:

```tsx
import { usePresenceData } from "motion/react"

function Slide() {
  const direction = usePresenceData()
  // direction = value from AnimatePresence custom={direction}
}
```

## Common Patterns

### Page Transitions

```tsx
function PageTransition({ children, key }) {
  return (
    <AnimatePresence mode="wait">
      <motion.main
        key={key}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
      >
        {children}
      </motion.main>
    </AnimatePresence>
  )
}
```

### Toast Notifications

```tsx
function ToastContainer({ toasts, removeToast }) {
  return (
    <div style={{ position: "fixed", bottom: 16, right: 16 }}>
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, x: 100, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.9 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
          >
            {toast.message}
            <button onClick={() => removeToast(toast.id)}>×</button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
```

### Modal with Backdrop

```tsx
function Modal({ isOpen, onClose, children }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: "fixed",
              inset: 0,
              backgroundColor: "#000",
            }}
          />
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: "spring", duration: 0.5, bounce: 0.2 }}
            style={{
              position: "fixed",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
            }}
          >
            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
```

## Troubleshooting

### Exit Animation Not Playing
- Ensure direct children have unique, stable `key` props
- Wrap the conditional inside `AnimatePresence`, not outside
- Check that `exit` prop is defined on the motion component

### Layout Issues with mode="sync"
- Exiting elements remain in DOM during animation — use `position: absolute` or `popLayout` mode

### forwardRef Required
- `popLayout` mode requires custom components to forward refs
- React 19: components can receive `ref` as a regular prop

## Related
- [02-animation-fundamentals](02-animation-fundamentals.md) — Variants for exit states
- [06-layout-animations](06-layout-animations.md) — Combine with layout transitions
- [12-patterns-and-recipes](12-patterns-and-recipes.md) — Full pattern implementations
