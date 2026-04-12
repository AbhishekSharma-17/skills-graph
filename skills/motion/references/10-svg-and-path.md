# SVG and Path Animations

> Source: https://motion.dev/docs/react-animation | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [SVG Motion Components](#svg-motion-components)
- [Path Animations](#path-animations)
- [Line Drawing Effect](#line-drawing-effect)
- [SVG Attributes](#svg-attributes)
- [Morphing Paths](#morphing-paths)
- [Animated Icons](#animated-icons)
- [Complex SVG Patterns](#complex-svg-patterns)

## Overview

Motion provides full SVG animation support. All SVG elements can be wrapped with `motion.` prefix, and SVG-specific properties like `pathLength`, `cx`, `r`, `fill`, and `stroke` are animatable.

## SVG Motion Components

```tsx
<motion.svg viewBox="0 0 100 100">
  <motion.circle />
  <motion.rect />
  <motion.path />
  <motion.line />
  <motion.polyline />
  <motion.polygon />
  <motion.ellipse />
  <motion.g />
  <motion.text />
</motion.svg>
```

## Path Animations

### pathLength

The most powerful SVG animation prop. It represents the path's drawn length as a value from 0 to 1:

```tsx
<motion.svg viewBox="0 0 100 100" width={200} height={200}>
  <motion.circle
    cx={50}
    cy={50}
    r={40}
    fill="none"
    stroke="#3b82f6"
    strokeWidth={3}
    initial={{ pathLength: 0 }}
    animate={{ pathLength: 1 }}
    transition={{ duration: 2, ease: "easeInOut" }}
  />
</motion.svg>
```

### pathOffset

Offset where the path drawing starts:

```tsx
<motion.path
  d="M 10 80 C 40 10, 65 10, 95 80"
  fill="none"
  stroke="#3b82f6"
  strokeWidth={2}
  initial={{ pathLength: 0.3, pathOffset: 0 }}
  animate={{ pathOffset: 1 }}
  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
/>
```

### pathSpacing

Controls the gap in dashed path animations:

```tsx
<motion.circle
  cx={50}
  cy={50}
  r={40}
  fill="none"
  stroke="#3b82f6"
  strokeWidth={2}
  animate={{ pathLength: 0.5, pathSpacing: 0.5 }}
/>
```

## Line Drawing Effect

Draw a complex SVG path from start to finish:

```tsx
function DrawingIcon() {
  return (
    <motion.svg
      viewBox="0 0 24 24"
      width={48}
      height={48}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <motion.path
        d="M12 2L2 7l10 5 10-5-10-5z"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.5, ease: "easeInOut" }}
      />
      <motion.path
        d="M2 17l10 5 10-5"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.5, ease: "easeInOut", delay: 0.5 }}
      />
      <motion.path
        d="M2 12l10 5 10-5"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.5, ease: "easeInOut", delay: 1 }}
      />
    </motion.svg>
  )
}
```

### With Scroll

```tsx
function ScrollDrawing() {
  const { scrollYProgress } = useScroll()

  return (
    <motion.svg viewBox="0 0 100 100">
      <motion.path
        d="M 10 80 Q 50 10 90 80"
        fill="none"
        stroke="#3b82f6"
        strokeWidth={3}
        style={{ pathLength: scrollYProgress }}
      />
    </motion.svg>
  )
}
```

## SVG Attributes

Animate any SVG attribute:

```tsx
// Circle attributes
<motion.circle
  animate={{
    cx: 50,
    cy: 50,
    r: [20, 40, 20],          // Pulsing radius
    fill: "#3b82f6",
    stroke: "#1e40af",
    strokeWidth: [1, 3, 1],
    opacity: 1,
  }}
  transition={{ duration: 2, repeat: Infinity }}
/>

// Rectangle attributes
<motion.rect
  animate={{
    x: 10,
    y: 10,
    width: [50, 80, 50],
    height: [50, 80, 50],
    rx: [5, 25, 5],            // Border radius
    fill: ["#ef4444", "#3b82f6", "#22c55e"],
  }}
  transition={{ duration: 3, repeat: Infinity }}
/>

// Transform on SVG elements
<motion.g animate={{ rotate: 360 }} transition={{ duration: 4, repeat: Infinity, ease: "linear" }}>
  <circle cx={50} cy={20} r={5} fill="#3b82f6" />
</motion.g>
```

## Morphing Paths

Animate between different `d` path values (paths must have the same number of commands):

```tsx
const paths = {
  circle: "M 50,10 A 40,40 0 1,1 50,90 A 40,40 0 1,1 50,10",
  square: "M 10,10 L 90,10 L 90,90 L 10,90 Z",
  star: "M 50,5 L 63,40 L 98,40 L 70,62 L 80,95 L 50,75 L 20,95 L 30,62 L 2,40 L 37,40 Z",
}

function MorphingShape() {
  const [shape, setShape] = useState("circle")

  return (
    <motion.svg viewBox="0 0 100 100" onClick={() => setShape(/*next*/)}>
      <motion.path
        d={paths[shape]}
        fill="#3b82f6"
        animate={{ d: paths[shape] }}
        transition={{ duration: 0.8, ease: "easeInOut" }}
      />
    </motion.svg>
  )
}
```

Note: Path morphing requires both paths to have the same number of path commands. Use a library like `flubber` for complex morphs between arbitrary paths.

## Animated Icons

### Check Mark

```tsx
function AnimatedCheck({ isChecked }) {
  return (
    <motion.svg viewBox="0 0 24 24" width={24} height={24}>
      {/* Circle background */}
      <motion.circle
        cx={12}
        cy={12}
        r={10}
        fill="none"
        stroke={isChecked ? "#22c55e" : "#d1d5db"}
        strokeWidth={2}
        animate={{ pathLength: isChecked ? 1 : 0 }}
        transition={{ duration: 0.4 }}
      />
      {/* Check mark */}
      <motion.path
        d="M7 13l3 3 7-7"
        fill="none"
        stroke="#22c55e"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: isChecked ? 1 : 0 }}
        transition={{ duration: 0.3, delay: isChecked ? 0.2 : 0 }}
      />
    </motion.svg>
  )
}
```

### Hamburger to X

```tsx
function MenuIcon({ isOpen }) {
  return (
    <motion.svg viewBox="0 0 24 24" width={24} height={24}>
      <motion.line
        x1={3} y1={6} x2={21} y2={6}
        stroke="currentColor" strokeWidth={2} strokeLinecap="round"
        animate={isOpen ? { rotate: 45, y1: 12, y2: 12 } : {}}
      />
      <motion.line
        x1={3} y1={12} x2={21} y2={12}
        stroke="currentColor" strokeWidth={2} strokeLinecap="round"
        animate={isOpen ? { opacity: 0 } : { opacity: 1 }}
      />
      <motion.line
        x1={3} y1={18} x2={21} y2={18}
        stroke="currentColor" strokeWidth={2} strokeLinecap="round"
        animate={isOpen ? { rotate: -45, y1: 12, y2: 12 } : {}}
      />
    </motion.svg>
  )
}
```

## Complex SVG Patterns

### Loading Spinner

```tsx
function Spinner() {
  return (
    <motion.svg viewBox="0 0 50 50" width={40} height={40}>
      <motion.circle
        cx={25}
        cy={25}
        r={20}
        fill="none"
        stroke="#3b82f6"
        strokeWidth={4}
        strokeLinecap="round"
        initial={{ pathLength: 0.2, rotate: 0 }}
        animate={{ pathLength: [0.2, 0.8, 0.2], rotate: 360 }}
        transition={{
          pathLength: { duration: 1.5, repeat: Infinity, ease: "easeInOut" },
          rotate: { duration: 2, repeat: Infinity, ease: "linear" },
        }}
      />
    </motion.svg>
  )
}
```

### Animated Chart Bar

```tsx
function BarChart({ data }) {
  const barWidth = 30
  const gap = 10
  const maxValue = Math.max(...data.map((d) => d.value))

  return (
    <motion.svg viewBox={`0 0 ${data.length * (barWidth + gap)} 200`}>
      {data.map((item, i) => (
        <motion.rect
          key={item.label}
          x={i * (barWidth + gap)}
          width={barWidth}
          fill="#3b82f6"
          rx={4}
          initial={{ height: 0, y: 200 }}
          animate={{
            height: (item.value / maxValue) * 180,
            y: 200 - (item.value / maxValue) * 180,
          }}
          transition={{ delay: i * 0.1, type: "spring", bounce: 0.3 }}
        />
      ))}
    </motion.svg>
  )
}
```

## Related
- [02-animation-fundamentals](02-animation-fundamentals.md) — Core animation props
- [05-scroll-animations](05-scroll-animations.md) — Scroll-linked SVG drawing
- [12-patterns-and-recipes](12-patterns-and-recipes.md) — Full component patterns
