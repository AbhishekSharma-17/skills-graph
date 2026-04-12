# Layout Animations

> Source: https://motion.dev/docs/react-layout-animations | Version: 12.x

## Table of Contents
- [Overview](#overview)
- [Basic Layout Animation](#basic-layout-animation)
- [What Triggers Layout Animations](#what-triggers-layout-animations)
- [Layout Prop Options](#layout-prop-options)
- [Shared Element Transitions (layoutId)](#shared-element-transitions-layoutid)
- [LayoutGroup](#layoutgroup)
- [Transitions for Layout](#transitions-for-layout)
- [Scroll Containers](#scroll-containers)
- [Troubleshooting](#troubleshooting)
- [Common Patterns](#common-patterns)

## Overview

Layout animations automatically animate element position and size when the DOM layout changes. Add the `layout` prop to any motion component, and any React render that changes its size or position will be animated.

Motion performs layout animations using CSS `transform` (translate + scale), not width/height, for optimal performance.

## Basic Layout Animation

```tsx
// Any layout change to this div will animate
<motion.div layout />
```

### Animated Flexbox

```tsx
function Toggle() {
  const [isOn, setIsOn] = useState(false)

  return (
    <div
      onClick={() => setIsOn(!isOn)}
      style={{
        display: "flex",
        justifyContent: isOn ? "flex-end" : "flex-start",
        width: 80,
        padding: 8,
        borderRadius: 40,
        backgroundColor: isOn ? "#22c55e" : "#d1d5db",
        cursor: "pointer",
      }}
    >
      <motion.div
        layout
        style={{
          width: 32,
          height: 32,
          borderRadius: 16,
          backgroundColor: "#fff",
        }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
      />
    </div>
  )
}
```

## What Triggers Layout Animations

Layout animations activate on **any React re-render** that changes the element's computed position or size:

- CSS changes (flexbox alignment, grid placement, margins, padding)
- Sibling elements added/removed
- Parent size changes
- Content changes that affect sizing
- Window resize (when it affects layout)

They do **not** trigger from:
- Scroll position changes (unless `layoutScroll` is set)
- Transforms (already handled by animation system)

## Layout Prop Options

```tsx
// Animate both position and size
<motion.div layout />
// Same as:
<motion.div layout={true} />

// Animate only position (ignore size changes)
<motion.div layout="position" />

// Animate only size (ignore position changes)
<motion.div layout="size" />

// Preserve aspect ratio during size animation
<motion.div layout="preserve-aspect" />
```

## Shared Element Transitions (layoutId)

Connect different elements across renders with `layoutId`. When a new component with a matching `layoutId` mounts, it animates from the previous element's position.

### Basic Shared Transition

```tsx
function Tabs({ activeTab }) {
  return (
    <div style={{ display: "flex", gap: 16 }}>
      {tabs.map((tab) => (
        <button key={tab.id} onClick={() => setActiveTab(tab.id)}>
          {tab.label}
          {activeTab === tab.id && (
            <motion.div
              layoutId="active-tab"
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                height: 2,
                backgroundColor: "#3b82f6",
              }}
            />
          )}
        </button>
      ))}
    </div>
  )
}
```

### Expand/Collapse with layoutId

```tsx
function ExpandableCard({ item }) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <>
      {!isExpanded ? (
        <motion.div
          layoutId={`card-${item.id}`}
          onClick={() => setIsExpanded(true)}
          style={{ width: 200, height: 120, borderRadius: 12 }}
        >
          <motion.h3 layoutId={`title-${item.id}`}>{item.title}</motion.h3>
        </motion.div>
      ) : (
        <motion.div
          layoutId={`card-${item.id}`}
          onClick={() => setIsExpanded(false)}
          style={{ width: 400, height: 300, borderRadius: 16 }}
        >
          <motion.h3 layoutId={`title-${item.id}`}>{item.title}</motion.h3>
          <p>{item.description}</p>
        </motion.div>
      )}
    </>
  )
}
```

### With AnimatePresence

For smooth crossfade between shared elements:

```tsx
<AnimatePresence>
  {isOpen && (
    <motion.div
      layoutId="modal"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    />
  )}
</AnimatePresence>
```

The transition from the element being animated **to** is used for the shared transition.

## LayoutGroup

Synchronize layout animations across components that don't share a parent re-render:

```tsx
import { LayoutGroup } from "motion/react"

function App() {
  return (
    <LayoutGroup>
      <Accordion />   {/* Independent component */}
      <Accordion />   {/* Re-renders independently */}
      <Accordion />   {/* But layout changes coordinate */}
    </LayoutGroup>
  )
}
```

Without `LayoutGroup`, components that re-render independently won't coordinate their layout animations.

### Named Groups

```tsx
<LayoutGroup id="sidebar">
  {/* layoutId values are scoped to this group */}
  <motion.div layoutId="item" />
</LayoutGroup>

<LayoutGroup id="main">
  {/* This "item" layoutId is separate from sidebar's */}
  <motion.div layoutId="item" />
</LayoutGroup>
```

## Transitions for Layout

```tsx
// Default transition for layout animations
<motion.div
  layout
  transition={{ type: "spring", stiffness: 300, damping: 25 }}
/>

// Separate layout transition from other animations
<motion.div
  layout
  animate={{ opacity: 0.5 }}
  transition={{
    opacity: { duration: 0.2 },
    layout: { type: "spring", duration: 0.6, bounce: 0.2 },
  }}
/>
```

### Layout Anchor

Control the animation origin point:

```tsx
<motion.li
  layout
  layoutAnchor={{ x: 0.5, y: 0.5 }}  // Animate from center
  // Default is top-left (0, 0)
/>
```

## Scroll Containers

### Scrollable Parent

When layout-animated elements are inside a scrollable container, add `layoutScroll`:

```tsx
<motion.div layoutScroll style={{ overflow: "auto", height: 400 }}>
  <motion.div layout>
    {/* Layout animations account for scroll offset */}
  </motion.div>
</motion.div>
```

### Fixed Containers

For fixed-position elements, use `layoutRoot`:

```tsx
<motion.div layoutRoot style={{ position: "fixed" }}>
  <motion.div layout>
    {/* Correct scroll offset calculations */}
  </motion.div>
</motion.div>
```

## Troubleshooting

### Content Looks Stretched

When a parent scales, children stretch. Fix by adding `layout` to children:

```tsx
// Problem: text stretches during parent scale
<motion.div layout>
  <p>This text will stretch</p>
</motion.div>

// Solution: add layout to child
<motion.div layout>
  <motion.p layout>This text stays crisp</motion.p>
</motion.div>
```

### display: inline Elements

Transforms don't work on inline elements. Ensure layout-animated elements are `block`, `inline-block`, or `flex`:

```tsx
// Won't work
<motion.span layout>Text</motion.span>

// Fix
<motion.span layout style={{ display: "inline-block" }}>Text</motion.span>
```

### Border Radius Distortion

During scale animations, border radius can distort. Motion corrects this automatically when set via `style`:

```tsx
// Automatic correction
<motion.div layout style={{ borderRadius: 12 }} />

// May distort if set via className
<motion.div layout className="rounded-xl" />
```

### Scrollbar Jumping

Layout changes that add/remove scrollbars cause layout jumps:

```css
/* Reserve scrollbar space to prevent layout shift */
html {
  scrollbar-gutter: stable;
}
```

## Common Patterns

### Reorderable List

```tsx
<AnimatePresence>
  {items.map((item) => (
    <motion.div
      key={item.id}
      layout
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ layout: { type: "spring", stiffness: 300, damping: 25 } }}
    >
      {item.label}
    </motion.div>
  ))}
</AnimatePresence>
```

### Expanding Search Bar

```tsx
function SearchBar() {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <motion.div
      layout
      style={{ width: isExpanded ? 400 : 200 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
    >
      <motion.input
        layout
        onFocus={() => setIsExpanded(true)}
        onBlur={() => setIsExpanded(false)}
        style={{ width: "100%" }}
      />
    </motion.div>
  )
}
```

## Related
- [07-animate-presence](07-animate-presence.md) — Exit animations with layout
- [01-motion-component](01-motion-component.md) — Layout props reference
- [11-performance](11-performance.md) — Layout animation performance tips
