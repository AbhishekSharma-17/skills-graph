# Hooks and Utilities

> Source: https://motion.dev/docs/react-use-animate | Version: 12.x

## Table of Contents
- [useAnimate](#useanimate)
- [Animation Controls](#animation-controls)
- [useInView](#useinview)
- [useReducedMotion](#usereducedmotion)
- [MotionConfig](#motionconfig)
- [LazyMotion](#lazymotion)
- [useDragControls](#usedragcontrols)
- [useAnimationFrame](#useanimationframe)
- [useTime](#usetime)

## useAnimate

Imperative animation control scoped to a DOM subtree. Returns a `scope` ref and an `animate` function.

### Basic Usage

```tsx
import { useAnimate } from "motion/react"

function Component() {
  const [scope, animate] = useAnimate()

  async function handleClick() {
    // Animate the scoped element
    await animate(scope.current, { scale: 1.2 }, { duration: 0.3 })
    await animate(scope.current, { scale: 1 }, { duration: 0.2 })
  }

  return (
    <div ref={scope} onClick={handleClick}>
      Click to pulse
    </div>
  )
}
```

### Selector-Based Animation

Selectors are scoped to children of the `scope` ref:

```tsx
function StaggeredList() {
  const [scope, animate] = useAnimate()

  async function animateItems() {
    // Only selects <li> inside the scoped element
    await animate(
      "li",
      { opacity: 1, y: 0 },
      { delay: stagger(0.1) }
    )
  }

  return (
    <ul ref={scope}>
      <li style={{ opacity: 0, y: 20 }}>Item 1</li>
      <li style={{ opacity: 0, y: 20 }}>Item 2</li>
      <li style={{ opacity: 0, y: 20 }}>Item 3</li>
    </ul>
  )
}
```

### Sequences (Timeline)

Chain animations sequentially:

```tsx
async function runSequence() {
  await animate(".box", { x: 100 }, { duration: 0.5 })
  await animate(".box", { rotate: 90 }, { duration: 0.3 })
  await animate(".box", { scale: 1.5 }, { duration: 0.4 })
  await animate(".box", { x: 0, rotate: 0, scale: 1 }, { duration: 0.5 })
}
```

### With useInView

Trigger animations when element enters viewport:

```tsx
function RevealOnScroll() {
  const [scope, animate] = useAnimate()
  const isInView = useInView(scope, { once: true })

  useEffect(() => {
    if (isInView) {
      animate(scope.current, { opacity: 1, y: 0 }, { duration: 0.6 })
    }
  }, [isInView])

  return (
    <div ref={scope} style={{ opacity: 0, transform: "translateY(50px)" }}>
      Content
    </div>
  )
}
```

### Exit Animation with usePresence

```tsx
import { useAnimate, usePresence } from "motion/react"

function ExitComponent() {
  const [scope, animate] = useAnimate()
  const [isPresent, safeToRemove] = usePresence()

  useEffect(() => {
    if (!isPresent) {
      animate(scope.current, { opacity: 0, scale: 0.8 }).then(safeToRemove)
    }
  }, [isPresent])

  return <div ref={scope}>Exiting content</div>
}
```

### Automatic Cleanup

When the component unmounts, all animations started via `animate` are automatically stopped and cleaned up.

## Animation Controls

The `animate` function returns animation controls:

```tsx
const [scope, animate] = useAnimate()

function startAnimation() {
  const controls = animate(scope.current, { x: 100 }, { duration: 2 })

  // Control the animation
  controls.pause()
  controls.play()
  controls.stop()
  controls.complete()

  // Adjust speed (0 = paused, 1 = normal, 2 = 2x speed)
  controls.speed = 0.5

  // Get current time
  console.log(controls.time)

  // Scrub to specific time
  controls.time = 1.5

  // Wait for completion
  controls.then(() => console.log("Done"))
}
```

## useInView

Detect when an element enters or leaves the viewport:

```tsx
import { useInView } from "motion/react"

function Component() {
  const ref = useRef(null)
  const isInView = useInView(ref)
  // isInView: boolean, updates on enter/leave

  return <div ref={ref}>{isInView ? "Visible" : "Hidden"}</div>
}
```

### Options

```tsx
const isInView = useInView(ref, {
  once: true,           // Only trigger once (stays true after first enter)
  amount: 0.5,          // 50% visible to trigger ("some" | "all" | number)
  root: containerRef,   // Custom scroll container
  margin: "-100px 0px", // Offset viewport bounds
})
```

## useReducedMotion

Check if the user prefers reduced motion:

```tsx
import { useReducedMotion } from "motion/react"

function Component() {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      animate={shouldReduceMotion
        ? { opacity: 1 }
        : { opacity: 1, y: 0, scale: 1 }
      }
    />
  )
}
```

Returns `true` when the OS has "Reduce motion" enabled.

## MotionConfig

Set default configuration for all child motion components:

```tsx
import { MotionConfig } from "motion/react"

function App() {
  return (
    <MotionConfig
      transition={{ type: "spring", duration: 0.5, bounce: 0.2 }}
      reducedMotion="user"
    >
      {/* All motion components inherit these defaults */}
      <motion.div animate={{ x: 100 }} />
    </MotionConfig>
  )
}
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `transition` | `Transition` | — | Default transition for all children |
| `reducedMotion` | `"never" \| "user" \| "always"` | `"never"` | Reduced motion behavior |
| `nonce` | `string` | — | CSP nonce for style blocks |

### reducedMotion Options

- `"never"` (default) — Ignore OS reduced motion setting
- `"user"` — Respect OS setting. Transforms and layout disable; opacity/color persist
- `"always"` — Force reduced motion (useful for debugging)

## LazyMotion

Load motion features on demand to reduce initial bundle size:

```tsx
import { LazyMotion, domAnimation, m } from "motion/react"

function App() {
  return (
    <LazyMotion features={domAnimation}>
      {/* Use m.div instead of motion.div */}
      <m.div animate={{ opacity: 1 }} />
    </LazyMotion>
  )
}
```

### Feature Bundles

| Bundle | Size | Features |
|--------|------|----------|
| `domAnimation` | ~15KB | Core animations, gestures |
| `domMax` | ~25KB | Everything including layout animations |

### Async Loading

```tsx
const loadFeatures = () =>
  import("motion/react").then((mod) => mod.domMax)

<LazyMotion features={loadFeatures} strict>
  <m.div layout />
</LazyMotion>
```

The `strict` prop ensures only `m` components (not `motion`) are used inside `LazyMotion`, preventing accidental full bundle imports.

## useDragControls

Initiate drag from an external element:

```tsx
import { useDragControls, motion } from "motion/react"

function DragHandle() {
  const controls = useDragControls()

  return (
    <>
      <div onPointerDown={(e) => controls.start(e)}>
        ⠿ Handle
      </div>
      <motion.div drag dragControls={controls} dragListener={false}>
        Draggable content
      </motion.div>
    </>
  )
}
```

## useAnimationFrame

Run a callback on every animation frame with delta time:

```tsx
import { useAnimationFrame } from "motion/react"

function Spinner() {
  const ref = useRef(null)

  useAnimationFrame((time, delta) => {
    // time: total elapsed ms
    // delta: ms since last frame
    if (ref.current) {
      ref.current.style.transform = `rotate(${time * 0.1}deg)`
    }
  })

  return <div ref={ref}>🔄</div>
}
```

Automatically pauses when the component unmounts. Use for continuous animations that don't fit the declarative model.

## useTime

Returns a motion value that updates with elapsed time in milliseconds:

```tsx
import { useTime, useTransform, motion } from "motion/react"

function PulsatingDot() {
  const time = useTime()
  const scale = useTransform(time, (t) => 1 + 0.2 * Math.sin(t / 500))

  return (
    <motion.div
      style={{
        scale,
        width: 20,
        height: 20,
        borderRadius: "50%",
        backgroundColor: "#3b82f6",
      }}
    />
  )
}
```

## Related
- [08-motion-values](08-motion-values.md) — Motion value composition
- [07-animate-presence](07-animate-presence.md) — usePresence for exit control
- [05-scroll-animations](05-scroll-animations.md) — useScroll hook
