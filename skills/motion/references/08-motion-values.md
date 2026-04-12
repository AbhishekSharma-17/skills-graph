# Motion Values

> Source: https://motion.dev/docs/react-motion-value | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [useMotionValue](#usemotionvalue)
- [API Methods](#api-methods)
- [useTransform](#usetransform)
- [useSpring](#usespring)
- [useVelocity](#usevelocity)
- [useMotionValueEvent](#usemotionvalueevent)
- [Composing Motion Values](#composing-motion-values)
- [Common Patterns](#common-patterns)

## Overview

Motion values are reactive containers that track state and velocity for animations. They update the DOM directly through Motion's optimized renderer — bypassing React's re-render cycle entirely.

Key benefits:
- **No re-renders**: Value changes update the DOM without React reconciliation
- **Velocity tracking**: Automatically tracks velocity for spring animations
- **Composable**: Chain and transform values using hooks
- **Subscribable**: Listen to changes via events

## useMotionValue

Create a motion value manually:

```tsx
import { useMotionValue, motion } from "motion/react"

function Component() {
  const x = useMotionValue(0)

  return <motion.div style={{ x }} />
}
```

Motion components automatically create motion values for animated properties. Use `useMotionValue` when you need to:
- Share a value across multiple components
- Chain values with composition hooks
- Read values in event handlers
- Control values imperatively

### Connecting to Style

```tsx
function DraggableBox() {
  const x = useMotionValue(0)
  const y = useMotionValue(0)

  return (
    <motion.div
      drag
      style={{ x, y }}
    />
  )
}
```

### Connecting to Animate

```tsx
const x = useMotionValue(0)

// Animate the motion value directly
<motion.div animate={{ x: 100 }} style={{ x }} />
```

## API Methods

```tsx
const x = useMotionValue(0)

// Get current value
const current = x.get()           // 0

// Set value (triggers DOM update, no re-render)
x.set(100)

// Get current velocity (per second)
const vel = x.getVelocity()       // 0 for non-animating values

// Set value and reset velocity to 0, ending any animation
x.jump(200)

// Check if currently animating
const animating = x.isAnimating()  // boolean

// Stop current animation
x.stop()

// Subscribe to events
const unsubscribe = x.on("change", (latest) => {
  console.log("Value changed to:", latest)
})

// Event types: "change", "animationStart", "animationCancel", "animationComplete"

// Cleanup (for vanilla JS usage outside React)
x.destroy()
```

## useTransform

Create derived motion values by mapping one or more source values:

### Input/Output Range Mapping

```tsx
import { useTransform, useMotionValue } from "motion/react"

function Component() {
  const x = useMotionValue(0)

  // Map x: [-200, 0, 200] → opacity: [0, 1, 0]
  const opacity = useTransform(x, [-200, 0, 200], [0, 1, 0])

  // Map x: [-200, 200] → rotate: [-45, 45]
  const rotate = useTransform(x, [-200, 200], [-45, 45])

  return (
    <motion.div drag="x" style={{ x, opacity, rotate }} />
  )
}
```

### Custom Transform Function

```tsx
const x = useMotionValue(0)

// Custom mapping function
const rounded = useTransform(x, (latest) => Math.round(latest))

// Clamp output
const clamped = useTransform(x, (latest) => Math.max(0, Math.min(100, latest)))
```

### Combining Multiple Values

```tsx
const x = useMotionValue(0)
const y = useMotionValue(0)

// Combine x and y into a single derived value
const distance = useTransform([x, y], ([latestX, latestY]) =>
  Math.sqrt(latestX ** 2 + latestY ** 2)
)

// Use for complex CSS values
const boxShadow = useTransform([x, y], ([latestX, latestY]) =>
  `${latestX}px ${latestY}px 20px rgba(0, 0, 0, 0.2)`
)
```

### With Easing

```tsx
// Apply easing to the mapping
const opacity = useTransform(
  scrollYProgress,
  [0, 0.5, 1],
  [0, 1, 0],
  { ease: [easeIn, easeOut] }  // One ease per segment
)
```

## useSpring

Wrap a motion value in spring physics:

```tsx
import { useSpring, useMotionValue } from "motion/react"

function SmoothFollower() {
  const rawX = useMotionValue(0)
  const x = useSpring(rawX, {
    stiffness: 300,
    damping: 30,
    mass: 0.5,
  })

  return (
    <motion.div
      drag="x"
      style={{ x: rawX }}  // Raw drag position
    >
      <motion.div style={{ x }} />  {/* Smooth follower */}
    </motion.div>
  )
}
```

### Spring from Static Value

```tsx
const x = useSpring(0, { stiffness: 100, damping: 20 })

// Later, set a new target
x.set(100)  // Animates with spring physics to 100
```

### Spring Options

```tsx
useSpring(value, {
  stiffness: 300,   // Higher = snappier
  damping: 30,      // Higher = less oscillation
  mass: 1,          // Higher = more sluggish
  restDelta: 0.01,  // Stop threshold (distance)
  restSpeed: 0.01,  // Stop threshold (velocity)
})
```

## useVelocity

Create a motion value that outputs the velocity of another:

```tsx
import { useVelocity, useMotionValue, useTransform } from "motion/react"

function VelocityIndicator() {
  const x = useMotionValue(0)
  const xVelocity = useVelocity(x)

  // Map velocity to visual effect
  const skewX = useTransform(xVelocity, [-1000, 0, 1000], [-20, 0, 20])

  return <motion.div drag="x" style={{ x, skewX }} />
}
```

Useful for physics-like effects where visual output depends on how fast a value is changing.

## useMotionValueEvent

Subscribe to motion value events within a React component (auto-cleans up):

```tsx
import { useMotionValueEvent, useMotionValue } from "motion/react"

function Component() {
  const x = useMotionValue(0)

  useMotionValueEvent(x, "change", (latest) => {
    console.log("x is now:", latest)
  })

  useMotionValueEvent(x, "animationStart", () => {
    console.log("Animation started")
  })

  useMotionValueEvent(x, "animationComplete", () => {
    console.log("Animation complete")
  })

  return <motion.div style={{ x }} animate={{ x: 100 }} />
}
```

Event types:
- `"change"` — Value changed (every frame during animation)
- `"animationStart"` — Animation began
- `"animationCancel"` — Animation was interrupted
- `"animationComplete"` — Animation finished

## Composing Motion Values

Chain transforms for complex reactive pipelines:

```tsx
function ComposedExample() {
  const x = useMotionValue(0)
  const xVelocity = useVelocity(x)
  const smoothVelocity = useSpring(xVelocity, { stiffness: 50, damping: 20 })
  const skew = useTransform(smoothVelocity, [-500, 0, 500], [-15, 0, 15])
  const scale = useTransform(smoothVelocity, [-500, 0, 500], [0.9, 1, 0.9])

  return <motion.div drag="x" style={{ x, skewX: skew, scale }} />
}
```

### Rendering Motion Values as Text

Display animated values as text without re-renders:

```tsx
import { motion, useMotionValue, useTransform } from "motion/react"

function Counter() {
  const count = useMotionValue(0)
  const rounded = useTransform(count, (v) => Math.round(v))

  return (
    <motion.span
      animate={{ "--count": 100 } as any}
      transition={{ duration: 2 }}
    >
      {/* Renders the current value as text */}
      <motion.span>{rounded}</motion.span>
    </motion.span>
  )
}
```

## Common Patterns

### Cursor Follower

```tsx
function CursorFollower() {
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)
  const smoothX = useSpring(mouseX, { stiffness: 300, damping: 30 })
  const smoothY = useSpring(mouseY, { stiffness: 300, damping: 30 })

  useEffect(() => {
    const handleMove = (e: MouseEvent) => {
      mouseX.set(e.clientX)
      mouseY.set(e.clientY)
    }
    window.addEventListener("mousemove", handleMove)
    return () => window.removeEventListener("mousemove", handleMove)
  }, [mouseX, mouseY])

  return (
    <motion.div
      style={{
        x: smoothX,
        y: smoothY,
        position: "fixed",
        width: 20,
        height: 20,
        borderRadius: "50%",
        backgroundColor: "#3b82f6",
        pointerEvents: "none",
        translateX: "-50%",
        translateY: "-50%",
      }}
    />
  )
}
```

### Linked Drag and Opacity

```tsx
function LinkedDragOpacity() {
  const x = useMotionValue(0)
  const opacity = useTransform(x, [-200, 0, 200], [0, 1, 0])
  const backgroundColor = useTransform(
    x,
    [-200, 0, 200],
    ["#ef4444", "#3b82f6", "#22c55e"]
  )

  return (
    <motion.div
      drag="x"
      dragConstraints={{ left: -200, right: 200 }}
      style={{ x, opacity, backgroundColor }}
    />
  )
}
```

## Related
- [03-transitions](03-transitions.md) — Spring configuration for useSpring
- [05-scroll-animations](05-scroll-animations.md) — useScroll returns motion values
- [09-hooks-and-utilities](09-hooks-and-utilities.md) — useAnimate for imperative control
