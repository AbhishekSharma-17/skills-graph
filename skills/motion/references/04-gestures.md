# Gestures

> Source: https://motion.dev/docs/react-gestures | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [Hover](#hover)
- [Tap](#tap)
- [Drag](#drag)
- [Pan](#pan)
- [Focus](#focus)
- [InView](#inview)
- [Event Propagation](#event-propagation)
- [Accessibility](#accessibility)
- [Common Patterns](#common-patterns)

## Overview

Motion extends React's event system with gesture recognition for hover, tap, pan, drag, focus, and viewport visibility. Each gesture has:

1. **Event callbacks** — Functions fired on gesture events
2. **`while*` animation props** — Target values active during the gesture, automatically reverting when the gesture ends

All gestures work across mouse, touch, and pen input.

## Hover

Detects pointer hover over a component. More reliable than CSS `:hover` for animations because it handles touch devices correctly.

```tsx
<motion.div
  whileHover={{ scale: 1.05, backgroundColor: "#f0f0f0" }}
  transition={{ type: "spring", stiffness: 300 }}
/>

// With callbacks
<motion.div
  whileHover={{ scale: 1.05 }}
  onHoverStart={(event) => console.log("Hover started")}
  onHoverEnd={(event) => console.log("Hover ended")}
/>
```

### Hover with Variants

```tsx
const cardVariants = {
  rest: { scale: 1, boxShadow: "0 2px 8px rgba(0,0,0,0.1)" },
  hover: { scale: 1.02, boxShadow: "0 8px 24px rgba(0,0,0,0.15)" },
}

<motion.div
  variants={cardVariants}
  initial="rest"
  whileHover="hover"
/>
```

## Tap

Detects press and release on the same component. Fires `tap` on release within bounds, or `tapCancel` if pointer moves outside.

```tsx
<motion.button
  whileTap={{ scale: 0.95 }}
/>

// With callbacks
<motion.button
  whileTap={{ scale: 0.95 }}
  onTapStart={(event, info) => console.log("Tap started at", info.point)}
  onTap={(event, info) => console.log("Tap completed")}
  onTapCancel={(event, info) => console.log("Tap cancelled")}
/>
```

### PointInfo Object

All gesture callbacks receive a `PointInfo` with:

```tsx
{
  point: { x: number, y: number },   // Absolute position
  delta: { x: number, y: number },   // Change since last event
  offset: { x: number, y: number },  // Change since gesture start
  velocity: { x: number, y: number }, // Current velocity
}
```

## Drag

Enables dragging, applying pointer movement to the element's `x`/`y` transforms.

### Basic Drag

```tsx
// Drag in any direction
<motion.div drag />

// Constrain to one axis
<motion.div drag="x" />
<motion.div drag="y" />
```

### Drag Constraints

```tsx
// Pixel constraints
<motion.div
  drag
  dragConstraints={{ top: -100, right: 100, bottom: 100, left: -100 }}
/>

// Ref-based constraints (drag within parent)
function DragContainer() {
  const constraintsRef = useRef(null)

  return (
    <div ref={constraintsRef} style={{ width: 400, height: 400 }}>
      <motion.div drag dragConstraints={constraintsRef} />
    </div>
  )
}
```

### Drag Elastic

Controls how far the element can be dragged beyond constraints:

```tsx
// 0 = no overscroll, 1 = full elastic (default: 0.5)
<motion.div drag dragElastic={0.2} dragConstraints={constraintsRef} />

// Per-side elastic
<motion.div
  drag
  dragElastic={{ top: 0, right: 0.5, bottom: 0, left: 0.5 }}
  dragConstraints={constraintsRef}
/>
```

### Drag Momentum

```tsx
// Disable momentum (stop immediately on release)
<motion.div drag dragMomentum={false} />

// Snap back to origin on release
<motion.div drag dragSnapToOrigin />
```

### Drag Direction Lock

```tsx
// Lock to dominant axis after 10px of movement
<motion.div drag dragDirectionLock />
```

### Manual Drag Controls

```tsx
import { useDragControls, motion } from "motion/react"

function DragFromHandle() {
  const controls = useDragControls()

  return (
    <>
      {/* Drag handle */}
      <div onPointerDown={(e) => controls.start(e)}>
        ⠿ Drag here
      </div>

      {/* Draggable element */}
      <motion.div drag dragControls={controls} dragListener={false}>
        Content moves when handle is dragged
      </motion.div>
    </>
  )
}
```

### Drag Callbacks

```tsx
<motion.div
  drag
  onDragStart={(event, info) => console.log("Drag started")}
  onDrag={(event, info) => console.log("Dragging", info.offset)}
  onDragEnd={(event, info) => console.log("Released", info.velocity)}
  onDirectionLock={(axis) => console.log("Locked to", axis)}
/>
```

## Pan

Recognizes pointer press + move beyond a 3px threshold, without moving the element:

```tsx
<motion.div
  onPan={(event, info) => {
    console.log("Pan offset:", info.offset.x, info.offset.y)
  }}
  onPanStart={(event, info) => console.log("Pan started")}
  onPanEnd={(event, info) => console.log("Pan ended")}
/>
```

Important: For touch devices, set `touch-action: none` on the element to prevent browser scroll interference:

```tsx
<motion.div
  onPan={handlePan}
  style={{ touchAction: "none" }}
/>
```

## Focus

Detects focus using the same rules as CSS `:focus-visible` (keyboard focus, not click focus):

```tsx
<motion.input
  whileFocus={{ scale: 1.02, borderColor: "#3b82f6" }}
/>

<motion.a
  whileFocus={{ scale: 1.1, color: "#3b82f6" }}
  href="/about"
/>
```

## InView

Animates when an element enters or leaves the viewport:

```tsx
<motion.div
  initial={{ opacity: 0, y: 50 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}  // Only animate on first enter
/>
```

### Viewport Options

```tsx
<motion.div
  whileInView={{ opacity: 1 }}
  viewport={{
    once: true,           // Only trigger once
    amount: 0.5,          // 50% visible to trigger ("some" | "all" | number)
    root: scrollRef,      // Custom scroll container
    margin: "-100px 0px", // Offset viewport bounds
  }}
  onViewportEnter={(entry) => console.log("Entered viewport")}
  onViewportLeave={(entry) => console.log("Left viewport")}
/>
```

## Event Propagation

### Stop Propagation from React Components

```tsx
<motion.div whileTap={{ scale: 2 }}>
  <button onPointerDownCapture={(e) => e.stopPropagation()}>
    Click doesn't trigger parent tap
  </button>
</motion.div>
```

### Stop Propagation from Motion Components

```tsx
<motion.button
  whileTap={{ opacity: 0.8 }}
  propagate={{ tap: false }}  // Currently supports "tap" only
>
  Independent tap
</motion.button>
```

## Accessibility

Motion automatically adds accessibility features:

- Elements with `onTap` or `whileTap` receive `tabIndex: 0` (keyboard focusable)
- `Enter` key triggers `onTapStart` and `whileTap`
- `Enter` release triggers `onTap`
- Focus styling respects `:focus-visible` rules

## Common Patterns

### Interactive Card

```tsx
<motion.article
  whileHover={{ y: -4, boxShadow: "0 12px 24px rgba(0,0,0,0.15)" }}
  whileTap={{ scale: 0.98 }}
  transition={{ type: "spring", stiffness: 300, damping: 20 }}
>
  <h3>Card Title</h3>
  <p>Card content</p>
</motion.article>
```

### Drag-to-Dismiss

```tsx
function DragToDismiss({ onDismiss, children }) {
  return (
    <motion.div
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      onDragEnd={(_, info) => {
        if (Math.abs(info.offset.x) > 100) {
          onDismiss()
        }
      }}
    >
      {children}
    </motion.div>
  )
}
```

### Button with Combined Gestures

```tsx
<motion.button
  whileHover={{ scale: 1.05, backgroundColor: "#2563eb" }}
  whileTap={{ scale: 0.95 }}
  whileFocus={{ outline: "2px solid #3b82f6", outlineOffset: "2px" }}
  transition={{ type: "spring", stiffness: 400, damping: 17 }}
>
  Submit
</motion.button>
```

## Related
- [01-motion-component](01-motion-component.md) — Full props reference
- [02-animation-fundamentals](02-animation-fundamentals.md) — Variants for gesture states
- [05-scroll-animations](05-scroll-animations.md) — Scroll-based gestures
