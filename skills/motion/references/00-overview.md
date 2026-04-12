# Motion — Overview

> Source: https://motion.dev/docs/react | Version: 12.x

## Table of Contents
- [What Is Motion](#what-is-motion)
- [Installation](#installation)
- [Migration from Framer Motion](#migration-from-framer-motion)
- [Core Concepts](#core-concepts)
- [Your First Animation](#your-first-animation)
- [Animation Types](#animation-types)
- [Server-Side Rendering](#server-side-rendering)
- [Bundle Size](#bundle-size)

## What Is Motion

Motion (formerly Framer Motion) is a production-grade animation library for React. It provides a declarative API for animations, gestures, layout transitions, scroll effects, and exit animations — all with 120fps GPU-accelerated performance via the Web Animations API.

Key characteristics:
- **Declarative**: Animate with props, not imperative calls
- **Hybrid engine**: Uses native browser APIs (Web Animations API, ScrollTimeline) with JavaScript fallback
- **Type-safe**: Built with TypeScript, full type definitions included
- **Tree-shakable**: Import only what you use
- **31.5K GitHub stars**, 30M+ monthly npm downloads

## Installation

```bash
npm install motion
# or
pnpm add motion
# or
yarn add motion
# or
bun add motion
```

### Import

```tsx
// Standard React import
import { motion } from "motion/react"

// For SSR frameworks (Next.js App Router with "use client")
import * as motion from "motion/react-client"
```

The `motion/react` entry point supports React Server Components (the motion component itself renders on the client). Use `motion/react-client` only when you need to avoid the `"use client"` directive in a client component file.

## Migration from Framer Motion

Framer Motion was renamed to Motion in 2025. Migration requires only an import change:

```tsx
// Before (framer-motion)
import { motion, AnimatePresence } from "framer-motion"

// After (motion)
import { motion, AnimatePresence } from "motion/react"
```

No API changes — all props, hooks, and components work identically.

The `framer-motion` npm package still receives updates but will eventually be deprecated. New projects should use `motion`.

## Core Concepts

### Motion Components
Prefix any HTML or SVG element with `motion.` to add animation capabilities:

```tsx
<motion.div />      // animated div
<motion.span />     // animated span
<motion.svg />      // animated SVG container
<motion.circle />   // animated SVG circle
<motion.path />     // animated SVG path
```

Motion components accept all standard React props plus animation-specific props.

### Animation Props
The primary animation props:

| Prop | Purpose |
|------|---------|
| `animate` | Target values to animate to |
| `initial` | Starting values (before first render) |
| `exit` | Values when removed from DOM (requires AnimatePresence) |
| `transition` | Animation timing and physics configuration |
| `variants` | Named animation states |
| `whileHover` | Animation while pointer hovers |
| `whileTap` | Animation while element is pressed |
| `whileDrag` | Animation while being dragged |
| `whileFocus` | Animation while focused (`:focus-visible` rules) |
| `whileInView` | Animation while visible in viewport |
| `layout` | Animate layout changes automatically |
| `layoutId` | Shared element transitions |

### Animatable Properties
Motion can animate:
- **Transforms**: `x`, `y`, `z`, `scale`, `scaleX`, `scaleY`, `rotate`, `rotateX`, `rotateY`, `rotateZ`, `skewX`, `skewY`
- **CSS**: `opacity`, `backgroundColor`, `color`, `borderRadius`, `boxShadow`, `filter`, `width`, `height`
- **SVG**: `pathLength`, `pathOffset`, `cx`, `cy`, `r`, `d`, `fill`, `stroke`
- **CSS Variables**: `"--custom-property"`
- **Value types**: numbers, strings with units, colors (hex, rgba, hsla, oklch)

## Your First Animation

### Basic Enter Animation

```tsx
import { motion } from "motion/react"

function FadeIn() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      Hello, Motion!
    </motion.div>
  )
}
```

### Interactive Button

```tsx
function AnimatedButton() {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: "spring", stiffness: 400, damping: 17 }}
    >
      Click me
    </motion.button>
  )
}
```

### Toggle with State

```tsx
import { useState } from "react"
import { motion } from "motion/react"

function Toggle() {
  const [isOn, setIsOn] = useState(false)

  return (
    <motion.div
      onClick={() => setIsOn(!isOn)}
      animate={{ backgroundColor: isOn ? "#22c55e" : "#e5e7eb" }}
      style={{
        width: 60,
        height: 32,
        borderRadius: 16,
        display: "flex",
        justifyContent: isOn ? "flex-end" : "flex-start",
        padding: 4,
        cursor: "pointer",
      }}
    >
      <motion.div
        layout
        style={{
          width: 24,
          height: 24,
          borderRadius: 12,
          backgroundColor: "#fff",
        }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
      />
    </motion.div>
  )
}
```

## Animation Types

Motion supports several animation paradigms:

### 1. Enter Animations
Combine `initial` + `animate` for mount animations:
```tsx
<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} />
```

### 2. Gesture Animations
Built-in hover, tap, drag, focus, and viewport detection:
```tsx
<motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }} />
```

### 3. Exit Animations
Animate elements being removed from the DOM:
```tsx
<AnimatePresence>
  {show && <motion.div exit={{ opacity: 0 }} />}
</AnimatePresence>
```

### 4. Layout Animations
Automatically animate size and position changes:
```tsx
<motion.div layout />
```

### 5. Scroll Animations
Trigger or link animations to scroll position:
```tsx
<motion.div whileInView={{ opacity: 1 }} />
```

### 6. SVG Animations
Animate SVG paths, morphing, and drawing effects:
```tsx
<motion.path animate={{ pathLength: 1 }} />
```

## Server-Side Rendering

Motion fully supports SSR. Initial states are rendered server-side:

```tsx
// Server renders: transform: translateX(100px)
<motion.div initial={false} animate={{ x: 100 }} />

// Server renders: opacity: 0
<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} />
```

When `initial={false}`, the `animate` values are used for the server-rendered output.

## Bundle Size

Motion is tree-shakable. Import costs (approximate, gzipped):

| Import | Size |
|--------|------|
| `motion` component only | ~15KB |
| + `AnimatePresence` | ~17KB |
| + `useScroll` | ~18KB |
| + layout animations | ~20KB |
| Full library | ~25KB |

To minimize bundle size:
- Import only the hooks and components you use
- Use `motion/react` (not `motion/react-client`) for automatic code splitting
- Prefer `whileInView` over custom `useScroll` + `useTransform` when possible

## Related
- [01-motion-component](01-motion-component.md) — Component API details
- [02-animation-fundamentals](02-animation-fundamentals.md) — Deep dive into animation props
- [03-transitions](03-transitions.md) — Spring physics and timing configuration
