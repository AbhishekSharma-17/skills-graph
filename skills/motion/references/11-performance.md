# Performance

> Source: https://motion.dev/docs/react-motion-component | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [How Motion Achieves Performance](#how-motion-achieves-performance)
- [GPU-Accelerated Properties](#gpu-accelerated-properties)
- [Avoiding React Re-Renders](#avoiding-react-re-renders)
- [Bundle Size Optimization](#bundle-size-optimization)
- [Layout Animation Performance](#layout-animation-performance)
- [Scroll Animation Performance](#scroll-animation-performance)
- [Measuring Performance](#measuring-performance)
- [Common Pitfalls](#common-pitfalls)
- [Performance Checklist](#performance-checklist)

## Overview

Motion achieves 120fps animations by leveraging the browser's native animation pipeline (Web Animations API) and bypassing React's rendering cycle. Understanding these internals helps you write performant animations.

## How Motion Achieves Performance

### Hybrid Engine

Motion uses a hybrid approach:
1. **Web Animations API (WAAPI)**: For simple animations (opacity, transforms) — runs on the compositor thread, 120fps
2. **JavaScript fallback**: For complex animations (layout, color interpolation) — runs on main thread but optimized
3. **ScrollTimeline API**: For scroll-linked animations — hardware-accelerated, off main thread

### No React Re-Renders

Animated values update the DOM directly via motion values, not through React state. This means:
- No virtual DOM diffing during animations
- No component re-renders during transitions
- Multiple elements can animate simultaneously without reconciliation cost

## GPU-Accelerated Properties

These properties are composited on the GPU and run at 120fps:

| Property | Motion Syntax |
|----------|--------------|
| Transform | `x`, `y`, `z`, `scale`, `rotate` |
| Opacity | `opacity` |
| Filter | `filter` (blur, brightness, etc.) |
| Clip path | `clipPath` |

These properties trigger layout/paint and are slower:

| Property | Impact |
|----------|--------|
| `width`, `height` | Layout + paint |
| `top`, `left`, `right`, `bottom` | Layout + paint |
| `margin`, `padding` | Layout + paint |
| `borderRadius` | Paint |
| `backgroundColor` | Paint |
| `boxShadow` | Paint |

### Best Practice

```tsx
// FAST — GPU-accelerated transform
<motion.div animate={{ x: 100, scale: 1.2, opacity: 0.5 }} />

// SLOWER — triggers layout
<motion.div animate={{ width: 200, left: 100 }} />

// WORKAROUND — use transform instead of position
<motion.div animate={{ x: 100 }} />  // Instead of animate={{ left: 100 }}
```

## Avoiding React Re-Renders

### Use Motion Values Instead of State

```tsx
// BAD — re-renders on every frame
function BadExample() {
  const [x, setX] = useState(0)

  return (
    <motion.div
      drag
      onDrag={(_, info) => setX(info.offset.x)}
      style={{ x }}
    >
      Position: {x}
    </motion.div>
  )
}

// GOOD — no re-renders
function GoodExample() {
  const x = useMotionValue(0)

  return (
    <motion.div drag="x" style={{ x }}>
      <motion.span>{useTransform(x, (v) => Math.round(v))}</motion.span>
    </motion.div>
  )
}
```

### Use useTransform Instead of useMotionValueEvent + setState

```tsx
// BAD — triggers re-render
const { scrollYProgress } = useScroll()
const [opacity, setOpacity] = useState(1)

useMotionValueEvent(scrollYProgress, "change", (v) => {
  setOpacity(1 - v)  // Re-render every scroll frame!
})

// GOOD — no re-renders
const { scrollYProgress } = useScroll()
const opacity = useTransform(scrollYProgress, [0, 1], [1, 0])

return <motion.div style={{ opacity }} />
```

### Minimize onUpdate Usage

```tsx
// AVOID — fires every frame
<motion.div
  animate={{ x: 100 }}
  onUpdate={(latest) => {
    // This fires 60-120 times during the animation
    expensiveOperation(latest.x)
  }}
/>

// BETTER — use motion value event
const x = useMotionValue(0)
useMotionValueEvent(x, "animationComplete", () => {
  // Fires once when done
  onComplete()
})
```

## Bundle Size Optimization

### Tree Shaking

Import only what you need:

```tsx
// Full import (~25KB gzipped)
import { motion, AnimatePresence, useScroll } from "motion/react"

// Minimal import (~15KB gzipped)
import { motion } from "motion/react"
```

### LazyMotion

Load animation features on demand:

```tsx
import { LazyMotion, domAnimation, m } from "motion/react"

// Only ~15KB instead of ~25KB
function App() {
  return (
    <LazyMotion features={domAnimation}>
      <m.div animate={{ opacity: 1 }} />
    </LazyMotion>
  )
}
```

### Dynamic Import

```tsx
const loadFeatures = () =>
  import("motion/react").then((mod) => mod.domMax)

<LazyMotion features={loadFeatures}>
  {/* Features loaded async, page renders immediately */}
</LazyMotion>
```

### Feature Bundles

| Bundle | Size | Includes |
|--------|------|----------|
| `domAnimation` | ~15KB | Animation, gestures, scroll |
| `domMax` | ~25KB | + layout animations, AnimatePresence advanced |

## Layout Animation Performance

Layout animations use CSS transforms under the hood, but require JavaScript measurement:

```tsx
// Motion measures before/after layout, then animates with transforms
<motion.div layout />
```

### Tips

1. **Minimize layout scope**: Only add `layout` to elements that actually move
2. **Use `layout="position"` or `layout="size"`** when you only need one dimension
3. **Add `layout` to distorted children** to correct scale artifacts
4. **Avoid deep layout trees** — each `layout` element requires measurement

```tsx
// GOOD — minimal layout scope
<motion.div layout="position">
  <p>This text won't distort</p>
</motion.div>

// EXPENSIVE — many layout measurements
<motion.div layout>
  <motion.div layout>
    <motion.div layout>
      <motion.p layout>Deep nesting</motion.p>
    </motion.div>
  </motion.div>
</motion.div>
```

## Scroll Animation Performance

### Hardware-Accelerated Scroll

Motion uses the browser's native `ScrollTimeline` API where available:

```tsx
// GPU-accelerated — runs off main thread
<motion.div
  style={{
    opacity: scrollYProgress,  // Motion detects this can use ScrollTimeline
  }}
/>
```

### When JavaScript Fallback Is Used

- Custom transform functions: `useTransform(scroll, (v) => v * 2)`
- Non-standard value mappings
- Browser doesn't support ScrollTimeline

### Tips

```tsx
// FAST — direct scroll-to-style binding
const { scrollYProgress } = useScroll()
<motion.div style={{ scaleX: scrollYProgress }} />

// SLOWER — custom transform requires JS
const custom = useTransform(scrollYProgress, (v) => Math.sin(v * Math.PI))
<motion.div style={{ opacity: custom }} />
```

## Measuring Performance

### Chrome DevTools

1. Open Performance tab
2. Enable "Web Vitals" in settings
3. Record during animation
4. Look for:
   - Long tasks (>50ms) during animation
   - Layout thrashing (multiple layout/paint cycles)
   - Dropped frames

### MotionScore

Motion provides a built-in performance analysis tool:
- Visit https://motion.dev/motionscore
- Analyzes your page's animation performance
- Provides actionable recommendations

## Common Pitfalls

### Animating Width/Height

```tsx
// SLOW — triggers layout every frame
<motion.div animate={{ width: 200, height: 300 }} />

// FAST — use scale transform
<motion.div animate={{ scaleX: 2, scaleY: 1.5 }} />

// ACCEPTABLE — width/height to "auto" (Motion uses transform internally)
<motion.div animate={{ height: "auto" }} />
```

### Too Many Layout Elements

```tsx
// SLOW — 100 elements all measuring layout
{items.map(item => <motion.div layout key={item.id} />)}

// BETTER — only animate items that actually move
{items.map(item => (
  <motion.div layout={item.isMoving} key={item.id} />
))}
```

### Expensive Callbacks in Animation

```tsx
// AVOID — DOM read in animation callback
<motion.div onUpdate={() => {
  const rect = element.getBoundingClientRect()  // Forces layout!
}} />
```

## Performance Checklist

1. Prefer `x`, `y`, `scale`, `rotate`, `opacity` over layout-triggering properties
2. Use motion values instead of React state for animated values
3. Use `useTransform` instead of `useMotionValueEvent` + `setState`
4. Add `layout` prop only to elements that need it
5. Use `LazyMotion` + `domAnimation` to reduce bundle size
6. Avoid `onUpdate` callbacks unless absolutely necessary
7. Use `viewport={{ once: true }}` for scroll-triggered animations
8. Test with Chrome DevTools Performance tab
9. Use `will-change: transform` sparingly (Motion manages this automatically)

## Related
- [08-motion-values](08-motion-values.md) — Render-free value updates
- [06-layout-animations](06-layout-animations.md) — Layout animation internals
- [09-hooks-and-utilities](09-hooks-and-utilities.md) — LazyMotion for code splitting
