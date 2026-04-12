# Transitions

> Source: https://motion.dev/docs/react-transitions | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [Spring Animations](#spring-animations)
- [Tween Animations](#tween-animations)
- [Inertia Animations](#inertia-animations)
- [Easing Functions](#easing-functions)
- [Per-Property Transitions](#per-property-transitions)
- [Orchestration](#orchestration)
- [Repeat and Loop](#repeat-and-loop)
- [MotionConfig Defaults](#motionconfig-defaults)

## Overview

The `transition` prop controls how values animate between states. It can be set on any animation prop (`animate`, `whileHover`, `exit`, etc.) or globally via `MotionConfig`.

```tsx
<motion.div
  animate={{ x: 100 }}
  transition={{ type: "spring", stiffness: 300, damping: 20 }}
/>
```

## Spring Animations

Springs create natural-feeling motion with physics-based behavior. Two configuration modes:

### Duration-Based Spring (Recommended for Most Cases)

```tsx
<motion.div
  animate={{ x: 100 }}
  transition={{
    type: "spring",
    duration: 0.8,    // Total duration in seconds
    bounce: 0.25,     // 0 = no bounce, 1 = very bouncy
  }}
/>
```

| Param | Default | Range | Description |
|-------|---------|-------|-------------|
| `duration` | 0.8 | > 0 | Animation duration in seconds |
| `bounce` | 0.25 | 0–1 | Bounciness factor |

### Physics-Based Spring

```tsx
<motion.div
  animate={{ scale: 1.2 }}
  transition={{
    type: "spring",
    stiffness: 400,   // Higher = snappier
    damping: 17,       // Higher = less oscillation
    mass: 1,           // Higher = more sluggish
    velocity: 0,       // Initial velocity
  }}
/>
```

| Param | Default | Description |
|-------|---------|-------------|
| `stiffness` | 1 | Spring tension. Higher = faster, snappier |
| `damping` | 10 | Resistance force. 0 = infinite oscillation |
| `mass` | 1 | Weight of the element. Higher = slower |
| `velocity` | current | Initial velocity (auto-detected from gestures) |
| `restDelta` | 0.01 | Distance threshold to consider animation done |
| `restSpeed` | 0.01 | Speed threshold to consider animation done |

### Common Spring Presets

```tsx
// Snappy button press
{ type: "spring", stiffness: 400, damping: 17 }

// Gentle float
{ type: "spring", stiffness: 100, damping: 15 }

// Bouncy entrance
{ type: "spring", duration: 0.6, bounce: 0.5 }

// No bounce, smooth
{ type: "spring", duration: 0.4, bounce: 0 }

// Stiff, no overshoot
{ type: "spring", stiffness: 500, damping: 30 }
```

## Tween Animations

Time-based animations with easing curves:

```tsx
<motion.div
  animate={{ opacity: 1 }}
  transition={{
    type: "tween",
    duration: 0.5,     // Seconds
    ease: "easeInOut",
    delay: 0.2,        // Seconds before starting
  }}
/>
```

| Param | Default | Description |
|-------|---------|-------------|
| `duration` | 0.3 | Animation duration in seconds |
| `ease` | "easeOut" | Easing function (see below) |
| `delay` | 0 | Delay before animation starts. Can be negative |
| `from` | current | Override starting value |

Note: `type: "tween"` is implied when you set `duration` without `bounce`:

```tsx
// These are equivalent
transition={{ type: "tween", duration: 0.5 }}
transition={{ duration: 0.5 }}
```

## Inertia Animations

Decelerate from a starting velocity. Used by default after `drag` release:

```tsx
<motion.div
  drag
  dragTransition={{
    power: 0.8,        // Multiplier for velocity
    timeConstant: 700, // Time to decelerate (ms)
    min: -200,         // Lower bound
    max: 200,          // Upper bound
    bounceStiffness: 500,
    bounceDamping: 25,
  }}
/>
```

| Param | Default | Description |
|-------|---------|-------------|
| `power` | 0.8 | Velocity multiplier (0-1) |
| `timeConstant` | 700 | Deceleration time in ms |
| `min` | — | Lower bound constraint |
| `max` | — | Upper bound constraint |
| `bounceStiffness` | 500 | Spring stiffness at boundaries |
| `bounceDamping` | 10 | Spring damping at boundaries |
| `modifyTarget` | — | Function to snap to grid/points |

## Easing Functions

### Named Easings

```tsx
transition={{ ease: "linear" }}
transition={{ ease: "easeIn" }}
transition={{ ease: "easeOut" }}
transition={{ ease: "easeInOut" }}
transition={{ ease: "circIn" }}
transition={{ ease: "circOut" }}
transition={{ ease: "circInOut" }}
transition={{ ease: "backIn" }}
transition={{ ease: "backOut" }}
transition={{ ease: "backInOut" }}
transition={{ ease: "anticipate" }}  // backIn + overshoot
```

### Cubic Bezier

```tsx
transition={{ ease: [0.42, 0, 0.58, 1] }}      // ease-in-out
transition={{ ease: [0.22, 1, 0.36, 1] }}       // ease-out (smooth)
transition={{ ease: [0.68, -0.55, 0.27, 1.55] }} // bounce-like
```

### Custom Easing Function

```tsx
transition={{
  ease: (t: number) => t * t,  // quadratic ease-in
  duration: 1,
}}
```

### Per-Keyframe Easing

```tsx
<motion.div
  animate={{ x: [0, 100, 200] }}
  transition={{
    duration: 2,
    ease: ["easeIn", "easeOut"],  // One per segment
  }}
/>
```

## Per-Property Transitions

Configure different transitions for each animated property:

```tsx
<motion.div
  animate={{ x: 100, opacity: 0.5, scale: 1.2 }}
  transition={{
    // Default for all properties
    default: { type: "spring", stiffness: 300 },

    // Override for specific properties
    x: { type: "spring", stiffness: 500, damping: 30 },
    opacity: { duration: 0.4, ease: "easeOut" },
    scale: { type: "spring", bounce: 0.4 },
  }}
/>
```

For layout animations, use the `layout` key:

```tsx
<motion.div
  layout
  animate={{ opacity: 1 }}
  transition={{
    opacity: { duration: 0.2 },
    layout: { type: "spring", duration: 0.6, bounce: 0.2 },
  }}
/>
```

## Orchestration

Control animation timing between parent and children:

### delayChildren

```tsx
const container = {
  visible: {
    transition: {
      delayChildren: 0.3,  // Wait 300ms, then animate children
    },
  },
}
```

### staggerChildren

```tsx
const container = {
  visible: {
    transition: {
      staggerChildren: 0.1,       // 100ms between each child
      staggerDirection: 1,        // 1 = forwards, -1 = reverse
    },
  },
}
```

### when

```tsx
const container = {
  visible: {
    opacity: 1,
    transition: {
      when: "beforeChildren",  // Parent completes before children start
      // or: "afterChildren"   // Children complete before parent starts
    },
  },
}
```

### Combined Example

```tsx
const menuVariants = {
  closed: { opacity: 0, height: 0 },
  open: {
    opacity: 1,
    height: "auto",
    transition: {
      when: "beforeChildren",
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
}

const itemVariants = {
  closed: { opacity: 0, x: -20 },
  open: { opacity: 1, x: 0 },
}
```

## Repeat and Loop

```tsx
// Repeat 3 times
transition={{ repeat: 3 }}

// Repeat forever
transition={{ repeat: Infinity }}

// Repeat types
transition={{
  repeat: Infinity,
  repeatType: "loop",     // Restart from beginning each time
}}

transition={{
  repeat: Infinity,
  repeatType: "reverse",  // Alternate direction each cycle
}}

transition={{
  repeat: Infinity,
  repeatType: "mirror",   // Swap from/to values each cycle
}}

// Delay between repeats
transition={{
  repeat: Infinity,
  repeatType: "reverse",
  repeatDelay: 0.5,       // 500ms pause between cycles
}}
```

### Pulse Animation Example

```tsx
<motion.div
  animate={{ scale: [1, 1.1, 1] }}
  transition={{
    duration: 2,
    repeat: Infinity,
    ease: "easeInOut",
  }}
/>
```

## MotionConfig Defaults

Set default transitions for all child motion components:

```tsx
import { MotionConfig } from "motion/react"

function App() {
  return (
    <MotionConfig
      transition={{ type: "spring", duration: 0.5, bounce: 0.2 }}
    >
      {/* All motion components inherit this transition */}
      <motion.div animate={{ x: 100 }} />
      <motion.div animate={{ opacity: 0.5 }} />
    </MotionConfig>
  )
}
```

Children can still override with their own `transition` prop.

### Reduced Motion

```tsx
<MotionConfig reducedMotion="user">
  {/* Respects OS "Reduce motion" setting */}
  {/* Transforms and layout animations disable; opacity persists */}
</MotionConfig>

// Options: "never" (default) | "user" | "always"
```

## Related
- [02-animation-fundamentals](02-animation-fundamentals.md) — Animate and initial props
- [08-motion-values](08-motion-values.md) — useSpring for spring-driven values
- [11-performance](11-performance.md) — Choosing performant transitions
