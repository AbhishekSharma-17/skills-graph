# Motion Component

> Source: https://motion.dev/docs/react-motion-component | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [Creating Motion Components](#creating-motion-components)
- [Custom Components](#custom-components)
- [Style Prop](#style-prop)
- [Animation Props Reference](#animation-props-reference)
- [Gesture Props Reference](#gesture-props-reference)
- [Drag Props Reference](#drag-props-reference)
- [Layout Props Reference](#layout-props-reference)
- [Viewport Props Reference](#viewport-props-reference)
- [Advanced Props](#advanced-props)
- [Server-Side Rendering](#server-side-rendering)

## Overview

The `<motion />` component is a drop-in replacement for HTML and SVG elements that adds animation capabilities. It extends standard elements with animation props while maintaining full compatibility with existing React props.

Animated values update via the browser's native animation pipeline — not through React re-renders — so complex animations don't cause performance issues.

## Creating Motion Components

### HTML Elements

```tsx
import { motion } from "motion/react"

<motion.div />
<motion.span />
<motion.button />
<motion.input />
<motion.a />
<motion.ul />
<motion.li />
<motion.img />
<motion.form />
<motion.header />
<motion.section />
<motion.nav />
```

### SVG Elements

```tsx
<motion.svg />
<motion.path />
<motion.circle />
<motion.rect />
<motion.line />
<motion.polyline />
<motion.polygon />
<motion.ellipse />
<motion.g />
<motion.text />
```

## Custom Components

Wrap custom React components with `motion.create()` to add animation capabilities. The component **must** forward a ref to the animated DOM element.

### React 19 (ref as prop)

```tsx
function Card({ ref, className, children }) {
  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  )
}

const MotionCard = motion.create(Card)

// Use like any motion component
<MotionCard animate={{ opacity: 1 }} whileHover={{ scale: 1.02 }} />
```

### React 18 (forwardRef)

```tsx
import { forwardRef } from "react"

const Card = forwardRef(({ className, children }, ref) => (
  <div ref={ref} className={className}>
    {children}
  </div>
))

const MotionCard = motion.create(Card)
```

### Custom HTML Elements

```tsx
const MotionCustom = motion.create("custom-element")
// Renders <custom-element /> in the DOM
```

### Important Warning

Never call `motion.create()` inside a render function — it creates a new component on every render, breaking animations:

```tsx
// BAD — creates new component each render
function App() {
  const MotionCard = motion.create(Card) // Don't do this!
  return <MotionCard animate={{ opacity: 1 }} />
}

// GOOD — create outside component
const MotionCard = motion.create(Card)

function App() {
  return <MotionCard animate={{ opacity: 1 }} />
}
```

## Style Prop

The `style` prop is enhanced to support motion values and independent transforms:

```tsx
import { useMotionValue } from "motion/react"

function Component() {
  const x = useMotionValue(0)

  return (
    <motion.div
      style={{
        // Standard CSS
        backgroundColor: "#fff",
        borderRadius: 8,

        // Motion-specific transforms (independent from each other)
        x: 100,
        y: 50,
        rotate: 45,
        scale: 1.2,
        rotateX: 0,
        rotateY: 0,
        skewX: 0,
        skewY: 0,

        // Transform origin
        originX: 0.5,  // 0-1 (fraction) or pixel value
        originY: 0.5,

        // Perspective
        transformPerspective: 1000,

        // Motion values
        x: x,  // Updates without re-renders
      }}
    />
  )
}
```

### Transform vs CSS Transform

Motion's independent transform props (`x`, `y`, `scale`, `rotate`) are preferred over `transform` strings because:
1. Each axis animates independently
2. Hardware-accelerated by default
3. Can be driven by motion values without re-renders

```tsx
// Preferred — independent transforms
<motion.div animate={{ x: 100, rotate: 45, scale: 1.2 }} />

// Avoid — single transform string, less flexible
<motion.div animate={{ transform: "translateX(100px) rotate(45deg) scale(1.2)" }} />
```

## Animation Props Reference

| Prop | Type | Description |
|------|------|-------------|
| `initial` | `Target \| false` | Starting animation values. `false` = start at `animate` values |
| `animate` | `Target \| string` | Target values or variant name |
| `exit` | `Target \| string` | Exit animation values (needs AnimatePresence) |
| `transition` | `Transition` | Animation config (spring, tween, etc.) |
| `variants` | `Variants` | Named animation state map |
| `custom` | `any` | Data passed to dynamic variants |
| `inherit` | `boolean` | Inherit variant changes from parent |

### Callbacks

| Callback | Signature |
|----------|-----------|
| `onUpdate` | `(latest: ResolvedValues) => void` |
| `onAnimationStart` | `(definition: AnimationDefinition) => void` |
| `onAnimationComplete` | `(definition: AnimationDefinition) => void` |

## Gesture Props Reference

| Prop | Type | Description |
|------|------|-------------|
| `whileHover` | `Target \| string` | Animate while hovered |
| `whileTap` | `Target \| string` | Animate while pressed |
| `whileFocus` | `Target \| string` | Animate while focused (`:focus-visible`) |
| `whileDrag` | `Target \| string` | Animate while dragging |
| `whileInView` | `Target \| string` | Animate while in viewport |
| `onHoverStart` | `(event, info) => void` | Hover begins |
| `onHoverEnd` | `(event, info) => void` | Hover ends |
| `onTapStart` | `(event, info) => void` | Press begins |
| `onTap` | `(event, info) => void` | Tap completes |
| `onTapCancel` | `(event, info) => void` | Pointer leaves before release |
| `onPan` | `(event, info) => void` | Pointer moves after 3px threshold |
| `onPanStart` | `(event, info) => void` | Pan begins |
| `onPanEnd` | `(event, info) => void` | Pan ends |

## Drag Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `drag` | `boolean \| "x" \| "y"` | `false` | Enable dragging |
| `dragConstraints` | `Ref \| { top, right, bottom, left }` | — | Drag boundaries |
| `dragElastic` | `number \| { top, right, bottom, left }` | `0.5` | Elasticity outside constraints (0-1) |
| `dragMomentum` | `boolean` | `true` | Apply momentum after release |
| `dragTransition` | `InertiaOptions` | — | Momentum transition config |
| `dragDirectionLock` | `boolean` | `false` | Lock to dominant axis |
| `dragPropagation` | `boolean` | `false` | Allow drag to propagate to parent |
| `dragControls` | `DragControls` | — | Manual drag control |
| `dragListener` | `boolean` | `true` | Listen for drag on this element |
| `dragSnapToOrigin` | `boolean` | `false` | Snap back on release |

## Layout Props Reference

| Prop | Type | Description |
|------|------|-------------|
| `layout` | `boolean \| "position" \| "size" \| "preserve-aspect"` | Auto-animate layout changes |
| `layoutId` | `string` | Shared element transition identifier |
| `layoutDependency` | `any` | Manual dependency for layout recalculation |
| `layoutAnchor` | `{ x: number, y: number }` | Animation anchor point (0-1) |
| `layoutScroll` | `boolean` | Account for scroll offset |
| `layoutRoot` | `boolean` | Mark as fixed/scroll-independent root |

## Viewport Props Reference

| Prop | Type | Description |
|------|------|-------------|
| `viewport` | `ViewportOptions` | Configure viewport detection |
| `viewport.once` | `boolean` | Only animate on first enter |
| `viewport.root` | `RefObject` | Custom scroll container |
| `viewport.amount` | `"some" \| "all" \| number` | Visible fraction to trigger |
| `viewport.margin` | `string` | Margin around viewport (CSS format) |
| `onViewportEnter` | `(entry) => void` | Element enters viewport |
| `onViewportLeave` | `(entry) => void` | Element leaves viewport |

## Advanced Props

### transformTemplate
Override the default transform string generation:

```tsx
<motion.div
  animate={{ x: 100, rotate: 45 }}
  transformTemplate={(_, generated) => `perspective(500px) ${generated}`}
/>
```

### propagate
Control gesture event propagation:

```tsx
<motion.button
  whileTap={{ scale: 0.95 }}
  propagate={{ tap: false }}
/>
```

## Server-Side Rendering

Motion components render their initial state on the server. When `initial={false}`, the `animate` target is used for server output:

```tsx
// Server HTML: style="transform: translateX(100px)"
<motion.div initial={false} animate={{ x: 100 }} />

// Server HTML: style="opacity: 0"
<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} />
```

For Next.js App Router components, use the standard import — the `"use client"` boundary is handled automatically by the `motion/react` entry point.

## Related
- [02-animation-fundamentals](02-animation-fundamentals.md) — Animate, initial, and variants
- [04-gestures](04-gestures.md) — Gesture interaction details
- [06-layout-animations](06-layout-animations.md) — Layout prop deep dive
