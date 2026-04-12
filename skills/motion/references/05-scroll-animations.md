# Scroll Animations

> Source: https://motion.dev/docs/react-scroll-animations | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [Scroll-Triggered (whileInView)](#scroll-triggered-whileinview)
- [useScroll Hook](#usescroll-hook)
- [useTransform with Scroll](#usetransform-with-scroll)
- [Progress Bar](#progress-bar)
- [Parallax Effect](#parallax-effect)
- [Scroll Direction Detection](#scroll-direction-detection)
- [Horizontal Scrolling](#horizontal-scrolling)
- [Element Scroll Progress](#element-scroll-progress)
- [Performance](#performance)

## Overview

Motion supports two scroll animation paradigms:

1. **Scroll-triggered**: Animations activate when elements enter/leave the viewport (`whileInView`)
2. **Scroll-linked**: Animation values are directly tied to scroll position (`useScroll` + `useTransform`)

## Scroll-Triggered (whileInView)

The simplest scroll animation — combine `initial` + `whileInView`:

```tsx
<motion.div
  initial={{ opacity: 0, y: 50 }}
  whileInView={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.6, ease: "easeOut" }}
/>
```

### Animate Only Once

```tsx
<motion.div
  initial={{ opacity: 0, y: 50 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}
/>
```

### Control Trigger Threshold

```tsx
<motion.div
  whileInView={{ opacity: 1 }}
  viewport={{
    amount: 0.5,      // Trigger when 50% visible
    // amount: "some"  // Any part visible (default)
    // amount: "all"   // Fully visible
  }}
/>
```

### Viewport Margin

Trigger before/after element actually enters the viewport:

```tsx
<motion.div
  whileInView={{ opacity: 1 }}
  viewport={{ margin: "-100px" }}  // Trigger 100px before entering
/>
```

### Custom Scroll Container

```tsx
function ScrollContainer() {
  const containerRef = useRef(null)

  return (
    <div ref={containerRef} style={{ overflow: "auto", height: 400 }}>
      <motion.div
        whileInView={{ opacity: 1 }}
        viewport={{ root: containerRef }}
      />
    </div>
  )
}
```

### Staggered Reveal

```tsx
const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
}

function RevealList({ items }) {
  return (
    <motion.ul
      variants={containerVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
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

## useScroll Hook

Returns four motion values tracking scroll position and progress:

```tsx
import { useScroll } from "motion/react"

function Component() {
  const {
    scrollX,          // Absolute horizontal scroll (pixels)
    scrollY,          // Absolute vertical scroll (pixels)
    scrollXProgress,  // Horizontal scroll progress (0 to 1)
    scrollYProgress,  // Vertical scroll progress (0 to 1)
  } = useScroll()
}
```

### Page Scroll (Default)

```tsx
const { scrollYProgress } = useScroll()
// scrollYProgress: 0 at top → 1 at bottom of page
```

### Container Scroll

```tsx
const containerRef = useRef(null)
const { scrollYProgress } = useScroll({ container: containerRef })

return (
  <div ref={containerRef} style={{ overflow: "auto", height: 400 }}>
    {/* Long content */}
  </div>
)
```

### Element Scroll Progress

Track an element's progress through the viewport:

```tsx
const elementRef = useRef(null)
const { scrollYProgress } = useScroll({
  target: elementRef,
  offset: ["start end", "end start"],
  // "start end" = element's top meets viewport bottom (0)
  // "end start" = element's bottom meets viewport top (1)
})

return <div ref={elementRef}>Tracked element</div>
```

### Offset Options

The `offset` array defines when progress is 0 and when it's 1:

```tsx
// Default: element enters to element leaves viewport
offset: ["start end", "end start"]

// Element center crosses viewport center
offset: ["center center", "center center"]

// Element top reaches viewport top
offset: ["start start", "end start"]

// Custom pixel offsets
offset: ["start end", "end 200px"]
```

Format: `"<target-edge> <container-edge>"` where edges are `start`, `center`, `end`, or pixel/percentage values.

## useTransform with Scroll

Map scroll progress to animation values:

```tsx
import { useScroll, useTransform, motion } from "motion/react"

function ParallaxHero() {
  const { scrollYProgress } = useScroll()

  const opacity = useTransform(scrollYProgress, [0, 0.3], [1, 0])
  const y = useTransform(scrollYProgress, [0, 0.3], [0, -100])
  const scale = useTransform(scrollYProgress, [0, 0.3], [1, 0.8])

  return (
    <motion.div style={{ opacity, y, scale }}>
      <h1>Hero Title</h1>
    </motion.div>
  )
}
```

## Progress Bar

Reading progress indicator:

```tsx
function ProgressBar() {
  const { scrollYProgress } = useScroll()

  return (
    <motion.div
      style={{
        scaleX: scrollYProgress,
        transformOrigin: "left",
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: 4,
        backgroundColor: "#3b82f6",
        zIndex: 50,
      }}
    />
  )
}
```

## Parallax Effect

Move elements at different speeds relative to scroll:

```tsx
function ParallaxSection() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  })

  const backgroundY = useTransform(scrollYProgress, [0, 1], ["-20%", "20%"])
  const textY = useTransform(scrollYProgress, [0, 1], ["0%", "-50%"])

  return (
    <section ref={ref} style={{ position: "relative", overflow: "hidden" }}>
      <motion.div
        style={{ y: backgroundY, position: "absolute", inset: 0 }}
      >
        <img src="/bg.jpg" style={{ width: "100%", height: "120%" }} />
      </motion.div>
      <motion.h2 style={{ y: textY, position: "relative" }}>
        Parallax Title
      </motion.h2>
    </section>
  )
}
```

## Scroll Direction Detection

```tsx
import { useScroll, useMotionValueEvent } from "motion/react"

function ScrollDirectionIndicator() {
  const { scrollY } = useScroll()
  const [direction, setDirection] = useState<"up" | "down">("up")

  useMotionValueEvent(scrollY, "change", (current) => {
    const previous = scrollY.getPrevious()
    if (current > previous) {
      setDirection("down")
    } else {
      setDirection("up")
    }
  })

  return <div>Scrolling: {direction}</div>
}
```

### Auto-Hiding Header

```tsx
function AutoHideHeader() {
  const { scrollY } = useScroll()
  const [hidden, setHidden] = useState(false)

  useMotionValueEvent(scrollY, "change", (latest) => {
    const previous = scrollY.getPrevious()
    setHidden(latest > previous && latest > 100)
  })

  return (
    <motion.header
      animate={{ y: hidden ? "-100%" : "0%" }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      style={{ position: "fixed", top: 0, width: "100%" }}
    >
      Header content
    </motion.header>
  )
}
```

## Horizontal Scrolling

Convert vertical scroll into horizontal movement:

```tsx
function HorizontalScroll({ children }) {
  const containerRef = useRef(null)
  const { scrollYProgress } = useScroll({ target: containerRef })
  const x = useTransform(scrollYProgress, [0, 1], ["0%", "-75%"])

  return (
    <div ref={containerRef} style={{ height: "300vh" }}>
      <div style={{ position: "sticky", top: 0, overflow: "hidden" }}>
        <motion.div style={{ x, display: "flex" }}>
          {children}
        </motion.div>
      </div>
    </div>
  )
}
```

## Element Scroll Progress

Track how far an element has scrolled through the viewport:

```tsx
function ScrollRevealCard() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "center center"],
  })

  const scale = useTransform(scrollYProgress, [0, 1], [0.8, 1])
  const opacity = useTransform(scrollYProgress, [0, 1], [0.3, 1])

  return (
    <motion.div ref={ref} style={{ scale, opacity }}>
      Card content
    </motion.div>
  )
}
```

## Performance

Motion runs scroll-linked animations on the browser's native `ScrollTimeline` where possible, achieving fully hardware-accelerated 120fps animations without JavaScript on the main thread.

For best performance:
- Prefer animating `transform` and `opacity` (GPU-accelerated)
- Use `useTransform` instead of `useMotionValueEvent` + `set()` when possible
- Avoid triggering React re-renders in scroll callbacks

## Related
- [04-gestures](04-gestures.md) — InView gesture details
- [08-motion-values](08-motion-values.md) — useTransform and useSpring
- [11-performance](11-performance.md) — Scroll animation optimization
