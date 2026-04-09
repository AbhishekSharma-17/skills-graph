# Creative Arsenal

Advanced UI patterns and interaction paradigms for building visually striking, memorable interfaces. This is a pattern library -- pair it with a primary style archetype (Minimalist, Brutalist, or High-End Agency) or with the general design references for a complete aesthetic system.

## Table of Contents

- [Hero Paradigms](#hero-paradigms)
- [Navigation Patterns](#navigation-patterns)
- [Layout and Grid Patterns](#layout-and-grid-patterns)
- [Cards and Containers](#cards-and-containers)
- [Scroll Animations](#scroll-animations)
- [Galleries and Media](#galleries-and-media)
- [Typography Effects](#typography-effects)
- [Micro-Interactions and Effects](#micro-interactions-and-effects)
- [The Motion-Engine Bento Paradigm](#the-motion-engine-bento-paradigm)
- [Pre-Flight Check](#pre-flight-check)

---

## Hero Paradigms

Stop doing centered text over a dark image. Use asymmetric hero sections instead.

**Asymmetric Split Hero**
- Text cleanly aligned to left or right
- Background features a high-quality, relevant image with a subtle stylistic fade (darkening or lightening gracefully into the background color depending on light/dark mode)
- Never center both text and image symmetrically

**Curtain Reveal Hero**
- Hero section parts in the middle like a curtain on scroll
- Content revealed behind the parting halves

**Zoom Parallax Hero**
- Central background image zooms in/out seamlessly as the user scrolls
- Creates depth without complex 3D setup

**Split Screen Scroll Hero**
- Two screen halves sliding in opposite directions on scroll
- Content on each half can be independent

---

## Navigation Patterns

### Mac OS Dock Magnification

Navbar at the edge of the viewport. Icons scale fluidly on hover, creating a magnification effect centered on the cursor position.

### Magnetic Button

Buttons that physically pull toward the cursor within a defined proximity radius. Use Framer Motion `useMotionValue` and `useTransform` -- never `useState` for continuous position tracking.

### Fluid Island Nav

A pill-shaped UI component (`rounded-full`, `mt-6`, `mx-auto`, `w-max`) that morphs to show status/alerts. Detached from the viewport edge.

### Gooey Menu

Sub-items detach from the main button like a viscous liquid. Uses SVG filter blur and contrast trick for the gooey effect.

### Contextual Radial Menu

A circular menu expanding exactly at the click coordinates. Actions arranged on a radial arc.

### Floating Speed Dial

A FAB (floating action button) that springs out into a curved line of secondary actions with staggered animation.

### Mega Menu Reveal

Full-screen dropdowns that stagger-fade complex content. Links and sections enter with cascade delays.

---

## Layout and Grid Patterns

### Bento Grid 2.0

Asymmetric, tile-based grouping inspired by Apple Control Center. Use CSS Grid with varied `col-span` and `row-span` values. Never a uniform grid.

```
Row 1: col-span-8 | col-span-4
Row 2: col-span-4 | col-span-4 | col-span-4
```

Mobile collapse: `grid-cols-1` with generous `gap-6`.

### Masonry Layout

Staggered grid without fixed row heights. Items fill vertical space organically. Use CSS `columns` property or JavaScript-based masonry for precise control.

### Chroma Grid

Grid borders or tiles showing subtle, continuously animating color gradients. The grid itself becomes a visual element, not just a structural one.

### Split Screen Scroll

Two halves of the viewport sliding in opposite directions on scroll. Requires scroll position tracking and inverse `translateY` values.

---

## Cards and Containers

### Parallax Tilt Card

A 3D-tilting card that tracks mouse coordinates. Uses `perspective`, `rotateX`, and `rotateY` transforms calculated from cursor position relative to card center.

```css
transform: perspective(1000px) rotateX(var(--rx)) rotateY(var(--ry));
transition: transform 0.1s ease;
```

### Spotlight Border Card

Card borders illuminate dynamically under the cursor. A radial gradient follows the mouse position along the card edge, creating a light-tracking effect.

### Glassmorphism Panel (True Implementation)

Go beyond basic `backdrop-blur`. True frosted glass requires:
- `backdrop-blur-xl` or higher
- 1px inner border: `border-white/10`
- Subtle inner shadow: `shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]`
- Simulates physical edge refraction

### Holographic Foil Card

Iridescent, rainbow light reflections shifting on hover. Uses CSS `conic-gradient` or `linear-gradient` with `hue-rotate` animation tied to mouse position.

### Morphing Modal

A button that seamlessly expands into its own full-screen dialog container. Uses Framer Motion `layoutId` for shared element transition between button and modal states.

### Tinder Swipe Stack

A physical stack of cards the user can swipe away. Uses drag gestures with spring physics for snap-back or dismiss behavior.

---

## Scroll Animations

### Sticky Scroll Stack

Cards stick to the top of the viewport and physically stack over each other as the user scrolls. Each card has a slightly smaller scale or offset to create depth.

### Horizontal Scroll Hijack

Vertical scroll translates into a smooth horizontal gallery pan. The section is pinned (`position: sticky`) while horizontal content translates based on scroll progress.

### Locomotive Scroll Sequence

Video or 3D sequences where the playback framerate is tied directly to the scrollbar position. Scroll forward to advance, scroll backward to rewind.

### Scroll Progress Path

SVG vector lines or routes that draw themselves as the user scrolls. Uses `stroke-dashoffset` animated by scroll position via `IntersectionObserver` or scroll-driven animations.

### Liquid Swipe Transition

Page transitions that wipe the screen like a viscous liquid using SVG path morphing or clip-path animation.

---

## Galleries and Media

### Dome Gallery

A 3D gallery feeling like a panoramic dome. Images arranged on the inner surface of a sphere or cylinder using CSS 3D transforms.

### Coverflow Carousel

3D carousel with the center item focused and edge items angled back. Uses `perspective`, `translateZ`, and `rotateY` for the depth effect.

### Drag-to-Pan Grid

A boundless grid the user can freely drag in any compass direction. Content extends beyond the viewport in all directions.

### Accordion Image Slider

Narrow vertical or horizontal image strips that expand fully on hover/click. Uses CSS Grid or Flexbox with `flex-grow` transitions.

### Hover Image Trail

The mouse leaves a trail of popping/fading images behind it. Each image spawns at the cursor position and fades out with a delay.

### Glitch Effect Image

Brief RGB-channel shifting digital distortion on hover. Uses CSS `mix-blend-mode` with offset copies of the image in red, green, and blue.

---

## Typography Effects

### Kinetic Marquee

Endless text bands that reverse direction or speed up on scroll. Uses CSS `@keyframes` with `translateX` animation. Scroll velocity can modulate speed.

### Text Mask Reveal

Massive typography acting as a transparent window to a video or image background. Uses `background-clip: text` with `-webkit-text-fill-color: transparent`.

### Text Scramble Effect

Matrix-style character decoding on load or hover. Characters cycle through random glyphs before settling on the final letter. Use `requestAnimationFrame` for smooth updates.

### Circular Text Path

Text curved along a spinning circular SVG path using `<textPath>` element. The circle rotates continuously with a slow `animation-duration`.

### Gradient Stroke Animation

Outlined text with a gradient continuously running along the stroke. Uses SVG text with animated `stroke-dashoffset` and gradient fills.

### Variable Font Animation

Animating font-weight, font-width, or custom axes of a variable font on hover or scroll. Creates fluid typographic transitions impossible with static fonts.

---

## Micro-Interactions and Effects

### Perpetual Micro-Loops

When motion intensity is elevated, embed continuous infinite micro-animations in standard components:
- **Pulse:** Breathing scale animation on status dots and avatars
- **Typewriter:** Cycling text in search bars and command inputs
- **Float:** Gentle vertical oscillation on cards and badges
- **Shimmer:** Light reflection sweeping across skeleton loaders and surfaces
- **Carousel:** Auto-advancing horizontal content strips

Apply premium spring physics: `type: "spring", stiffness: 100, damping: 20` for all interactive elements. No linear easing.

### Magnetic Physics

Buttons that pull toward the cursor within a proximity radius. Use Framer Motion `useMotionValue` and `useTransform` exclusively -- never `useState` for continuous position tracking (causes performance collapse on mobile).

### Staggered Orchestration

Never mount lists or grids instantly. Use cascade reveals:

```css
/* CSS approach */
animation-delay: calc(var(--index) * 100ms);

/* Framer Motion approach */
staggerChildren: 0.1
```

The parent `variants` and children MUST reside in the identical Client Component tree. If data is fetched asynchronously, pass data as props into a centralized parent motion wrapper.

### Particle Explosion Button

CTAs that shatter into particles upon success confirmation. Particles radiate from the button center with randomized velocity and fade.

### Directional Hover Aware Button

Hover fill that enters from the exact side the mouse entered. Calculates entry angle from mouse coordinates relative to button edges.

### Ripple Click Effect

Visual waves rippling precisely from the click coordinates outward. Spawns a circle element at `event.clientX/Y` that scales and fades.

### Animated SVG Line Drawing

Vectors that draw their own contours in real-time using `stroke-dasharray` and `stroke-dashoffset` animation.

### Mesh Gradient Background

Organic, lava-lamp-like animated color blobs in the background. Uses multiple layered radial gradients with offset animation cycles.

---

## The Motion-Engine Bento Paradigm

When generating modern SaaS dashboards or feature sections, use this "Bento 2.0" architecture with perpetual physics. Goes beyond static cards into a "Vercel-core meets Dribbble-clean" aesthetic.

### Core Design Philosophy

| Property | Specification |
|----------|--------------|
| Background | `#f9fafb` |
| Card surface | `#ffffff` with `border-slate-200/50` (1px) |
| Card radius | `rounded-[2.5rem]` for all major containers |
| Shadow | Diffusion shadow: `shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]` |
| Typography | `Geist`, `Satoshi`, or `Cabinet Grotesk`. `tracking-tight` for headers |
| Labels | Titles and descriptions placed **outside and below** cards (gallery-style) |
| Inner padding | Generous `p-8` or `p-10` inside cards |

### Animation Engine Specs (Perpetual Motion)

All cards must contain perpetual micro-interactions:

- **Spring physics:** No linear easing. Use `type: "spring", stiffness: 100, damping: 20`
- **Layout transitions:** Heavily utilize Framer Motion `layout` and `layoutId` props for smooth re-ordering, resizing, and shared element transitions
- **Infinite loops:** Every card has an active state that loops infinitely (Pulse, Typewriter, Float, or Carousel) so the dashboard feels alive
- **Performance:** Wrap dynamic lists in `<AnimatePresence>`. Any perpetual motion or infinite loop MUST be memoized (`React.memo`) and completely isolated in its own microscopic Client Component. Never trigger re-renders in the parent layout

### Micro-Animation Archetypes (The 5-Card System)

Implement these when constructing Bento grids (e.g., Row 1: 3 cols, Row 2: 2 cols split 70/30):

**1. The Intelligent List**

A vertical stack of items with an infinite auto-sorting loop. Items swap positions using `layoutId`, simulating an AI prioritizing tasks in real-time. The reordering animates smoothly via spring physics.

**2. The Command Input**

A search/AI bar with a multi-step typewriter effect. Cycles through complex prompts including:
- Blinking cursor animation
- "Processing" state with a shimmering loading gradient
- Text appearing character by character with realistic timing variance

**3. The Live Status**

A scheduling interface with "breathing" status indicators. Includes a pop-up notification badge that:
- Emerges with an overshoot spring effect
- Stays visible for 3 seconds
- Vanishes with a smooth exit animation

**4. The Wide Data Stream**

A horizontal infinite carousel of data cards or metrics. The loop must be seamless using `x: ["0%", "-100%"]` with a speed that feels effortless and continuous, not rushed.

**5. The Contextual UI (Focus Mode)**

A document view that animates:
1. A staggered highlight of a text block (line by line or phrase by phrase)
2. A float-in of a floating action toolbar with micro-icons
3. Toolbar appears with spring physics after highlight completes

---

## Pre-Flight Check

Evaluate code against this matrix before outputting. This is the last filter.

### Architecture and State

- [ ] Global state used appropriately (avoiding deep prop-drilling, not arbitrarily)
- [ ] `useEffect` animations contain strict cleanup functions
- [ ] CPU-heavy perpetual animations isolated in their own Client Components
- [ ] GSAP/ThreeJS never mixed with Framer Motion in the same component tree

### Layout and Responsiveness

- [ ] Mobile layout collapse (`w-full`, `px-4`, `max-w-7xl mx-auto`) guaranteed for high-variance designs
- [ ] Full-height sections use `min-h-[100dvh]` instead of `h-screen`
- [ ] Grid used over complex flexbox percentage math

### Visual Quality

- [ ] Empty, loading, and error states provided
- [ ] Cards omitted in favor of spacing where possible (when density allows)
- [ ] No emojis in code, markup, text content, or alt text
- [ ] No banned fonts (Inter), icons, or generic AI patterns
- [ ] Shadows tinted to background hue, not generic black

### Performance

- [ ] Grain/noise filters on fixed, pointer-events-none pseudo-elements only
- [ ] Animations use only `transform` and `opacity` (no `top`, `left`, `width`, `height`)
- [ ] Z-indexes reserved for systemic layers only (nav, modals, overlays)
- [ ] `backdrop-blur` only on fixed/sticky elements
- [ ] Magnetic hover uses `useMotionValue`/`useTransform`, never `useState`
