# Animation Fundamentals

> Source: https://motion.dev/docs/react-animation | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [Animate Prop](#animate-prop)
- [Initial Prop](#initial-prop)
- [Animatable Values](#animatable-values)
- [Keyframes](#keyframes)
- [Variants](#variants)
- [Dynamic Variants](#dynamic-variants)
- [CSS Variables](#css-variables)
- [Value Type Conversion](#value-type-conversion)
- [Default Transitions](#default-transitions)
- [Animation Callbacks](#animation-callbacks)

## Overview

Motion's animation system is declarative — you describe target values and Motion handles the transition. Physical properties (transforms) use spring physics by default; appearance properties (opacity, colors) use tween easing.

## Animate Prop

The `animate` prop defines target values. When these values change, Motion automatically transitions to them:

```tsx
// Static target
<motion.div animate={{ opacity: 1, x: 100 }} />

// Dynamic target (re-animates when state changes)
<motion.div animate={{ x: isActive ? 100 : 0 }} />

// Multiple properties
<motion.div
  animate={{
    x: 100,
    y: 50,
    scale: 1.2,
    rotate: 45,
    opacity: 0.8,
    backgroundColor: "#3b82f6",
    borderRadius: "50%",
  }}
/>
```

## Initial Prop

`initial` sets starting values before the first animation:

```tsx
// Fade in from below
<motion.div
  initial={{ opacity: 0, y: 30 }}
  animate={{ opacity: 1, y: 0 }}
/>

// Disable enter animation (start at animate values)
<motion.div initial={false} animate={{ x: 100 }} />
```

When `initial` differs from `animate`, an enter animation plays on mount.

When `initial={false}`:
- No enter animation plays
- Element starts at `animate` values
- Server-side rendered output uses `animate` values

## Animatable Values

### Transform Properties (Independent Axes)

```tsx
<motion.div
  animate={{
    // Translation
    x: 100,          // translateX
    y: 50,           // translateY
    z: 0,            // translateZ

    // Scale
    scale: 1.2,      // uniform scale
    scaleX: 1.5,     // horizontal scale
    scaleY: 0.8,     // vertical scale

    // Rotation (degrees)
    rotate: 45,       // 2D rotation
    rotateX: 30,      // 3D X-axis
    rotateY: 60,      // 3D Y-axis
    rotateZ: 45,      // Same as rotate

    // Skew (degrees)
    skewX: 10,
    skewY: 5,
  }}
/>
```

### CSS Properties

```tsx
<motion.div
  animate={{
    opacity: 0.5,
    backgroundColor: "#ef4444",
    color: "rgb(255, 255, 255)",
    borderRadius: "50%",
    boxShadow: "0 10px 30px rgba(0, 0, 0, 0.3)",
    filter: "blur(4px)",
    width: 200,
    height: 200,

    // These can animate to/from "auto"
    width: "auto",
    height: "auto",
  }}
/>
```

### Color Formats
Motion animates between any color formats: hex, rgb, rgba, hsl, hsla, oklch, oklab, color-mix.

```tsx
<motion.div
  initial={{ backgroundColor: "#ff0000" }}
  animate={{ backgroundColor: "oklch(0.7 0.15 180)" }}
/>
```

## Keyframes

Pass arrays to animate through sequential values:

```tsx
// Simple keyframe sequence
<motion.div animate={{ x: [0, 100, 50, 100] }} />

// Multi-property keyframes
<motion.div
  animate={{
    x: [0, 100, 0],
    opacity: [0, 1, 0.5],
    scale: [0.8, 1.2, 1],
  }}
/>
```

### Wildcard Keyframes

Use `null` to start from the current value:

```tsx
// Start from wherever the element currently is
<motion.div animate={{ x: [null, 100, 0] }} />
```

This is useful for interrupting animations — the new animation starts from the element's current position.

### Keyframe Timing

Control when each keyframe occurs using `times` (0 to 1):

```tsx
<motion.div
  animate={{ x: [0, 100, 200] }}
  transition={{
    duration: 3,
    times: [0, 0.2, 1],  // 0s, 0.6s, 3s
  }}
/>
```

### Per-Keyframe Easing

```tsx
<motion.div
  animate={{ x: [0, 100, 200] }}
  transition={{
    duration: 2,
    ease: ["easeIn", "easeOut"],  // One ease per segment
  }}
/>
```

## Variants

Named animation states that propagate through component trees:

```tsx
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      when: "beforeChildren",
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

function List({ items }) {
  return (
    <motion.ul
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {items.map((item) => (
        <motion.li key={item.id} variants={itemVariants}>
          {item.label}
        </motion.li>
      ))}
    </motion.ul>
  )
}
```

### Variant Propagation

When a parent changes variant, children with matching variant names animate automatically — no need to pass `animate` to children:

```tsx
<motion.nav animate="open" variants={navVariants}>
  {/* These auto-animate to their "open" variant */}
  <motion.a variants={linkVariants}>Home</motion.a>
  <motion.a variants={linkVariants}>About</motion.a>
  <motion.a variants={linkVariants}>Contact</motion.a>
</motion.nav>
```

### Orchestration in Variants

```tsx
const parent = {
  visible: {
    transition: {
      when: "beforeChildren",     // Parent animates first
      staggerChildren: 0.1,       // 100ms between each child
      delayChildren: 0.3,         // Wait 300ms before children start
      staggerDirection: -1,       // Reverse stagger order
    },
  },
}
```

## Dynamic Variants

Variants can be functions that receive the `custom` prop:

```tsx
const variants = {
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1 },
  }),
  hidden: { opacity: 0, y: 20 },
}

function StaggeredList({ items }) {
  return (
    <motion.ul initial="hidden" animate="visible">
      {items.map((item, i) => (
        <motion.li
          key={item.id}
          custom={i}
          variants={variants}
        />
      ))}
    </motion.ul>
  )
}
```

## CSS Variables

Animate CSS custom properties to affect child elements:

```tsx
<motion.div
  initial={{ "--rotate": "0deg" }}
  animate={{ "--rotate": "360deg" }}
  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
  style={{ "--rotate": "0deg" } as React.CSSProperties}
>
  <div style={{ transform: "rotate(var(--rotate))" }}>
    Spinning child
  </div>
</motion.div>
```

Use CSS variables as targets:

```tsx
<motion.div
  animate={{ backgroundColor: "var(--accent-color)" }}
/>
```

## Value Type Conversion

Motion can animate between different CSS units for position properties:

```tsx
// Animate from pixels to percentage
<motion.div
  initial={{ width: "100px" }}
  animate={{ width: "50%" }}
/>

// Animate to "auto"
<motion.div
  initial={{ height: 0 }}
  animate={{ height: "auto" }}
/>
```

Supported conversions: `px` ↔ `%`, `px` ↔ `vh/vw`, number ↔ `"auto"`.

## Default Transitions

Motion chooses sensible defaults based on property type:

| Property Type | Default Transition |
|--------------|-------------------|
| Physical (x, y, scale, rotate) | Spring (`stiffness: 500`, `damping: 25`) |
| Opacity | Tween (`duration: 0.3`, `ease: "easeOut"`) |
| Colors | Tween (`duration: 0.3`) |
| Dimensions (width, height) | Tween (`duration: 0.3`) |

Override per-property:

```tsx
<motion.div
  animate={{ x: 100, opacity: 0.5 }}
  transition={{
    x: { type: "spring", stiffness: 300 },
    opacity: { duration: 0.5, ease: "easeInOut" },
  }}
/>
```

## Animation Callbacks

```tsx
<motion.div
  animate={{ x: 100 }}
  onAnimationStart={(definition) => {
    console.log("Animation started:", definition)
  }}
  onAnimationComplete={(definition) => {
    console.log("Animation complete:", definition)
  }}
  onUpdate={(latest) => {
    // Fires every frame — use sparingly
    console.log("Current x:", latest.x)
  }}
/>
```

## Related
- [03-transitions](03-transitions.md) — Customize spring, tween, and inertia
- [04-gestures](04-gestures.md) — while* gesture animations
- [07-animate-presence](07-animate-presence.md) — Exit animations
