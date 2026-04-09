# Design Engineering — Overview & Philosophy

## Table of Contents

- [Core Philosophy](#core-philosophy)
- [The AI Slop Test](#the-ai-slop-test)
- [Implementation Principles](#implementation-principles)
- [Config Dials System](#config-dials-system)
  - [DESIGN_VARIANCE (1-10)](#design_variance-1-10)
  - [MOTION_INTENSITY (1-10)](#motion_intensity-1-10)
  - [VISUAL_DENSITY (1-10)](#visual_density-1-10)
- [Absolute Zero — Banned Anti-Patterns](#absolute-zero--banned-anti-patterns)
  - [Absolute Bans (CSS-Level)](#absolute-bans-css-level)
  - [Banned Defaults](#banned-defaults)
- [Core Principles](#core-principles)
- [Lifecycle Guide — Which Reference for What Phase](#lifecycle-guide--which-reference-for-what-phase)

---

## Core Philosophy

Design engineering, not decoration. Every visual decision serves function, hierarchy, or brand.

A distinctive interface should make someone ask "how was this made?" not "which AI made this?" The goal is production-grade work that feels intentionally designed for its specific context — not generic output that could belong to any project.

Three non-negotiable commitments:

1. **Intentionality over intensity.** Bold maximalism and refined minimalism both work. The key is committing to a clear conceptual direction and executing it with precision. What fails is hedging — safe choices that avoid commitment.

2. **Context determines everything.** Theme, typography, spacing, motion, and color are all derived from who uses the product, when, where, and why. There are no universal defaults. A hospital portal and a trading terminal demand fundamentally different approaches, and neither should look like the other.

3. **Variation across projects.** No two interfaces should converge on the same aesthetic. Vary between light and dark themes, different fonts, different layout strategies, different moods. If the last project used a serif display font, look for a sans, monospace, or display face on this one.

---

## The AI Slop Test

**Critical quality check**: If you showed this interface to someone and said "AI made this," would they believe you immediately? If yes, that is the problem.

The AI slop test is the final quality gate applied to every piece of work. It catches the statistical biases that LLMs carry from training data — the patterns that make output feel generated rather than designed.

Common AI design fingerprints to watch for:

- Cyan-on-dark, purple-to-blue gradients, neon accents on dark backgrounds
- Gradient text using `background-clip: text`
- Side-stripe borders on cards (`border-left: 4px solid`)
- Identical 3-column card grids with icon + heading + text
- Hero metric layouts (big number, small label, supporting stats)
- Everything centered with identical padding
- Rounded rectangles with generic drop shadows
- Glassmorphism used everywhere decoratively
- Sparklines that look sophisticated but convey nothing
- Default fonts (Inter, Roboto) or the "second favorite" monoculture
- Bounce/elastic easing that feels dated
- Generic placeholder names ("John Doe", "Acme Corp")
- AI copywriting cliches ("Elevate", "Seamless", "Unleash", "Next-Gen")

Review every output against this list. The test is not "does it look good?" The test is "does it look distinctively, intentionally, specifically designed for this project?"

---

## Implementation Principles

Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. Never converge on common choices across generations.

The model is capable of extraordinary creative work. Do not hold back. Show what can truly be created when thinking outside the box and committing fully to a distinctive vision.

Key implementation rules:

- **Production-grade and functional** — working code, not mockups
- **Visually striking and memorable** — a clear aesthetic point-of-view
- **Cohesive** — every element reinforces the same design language
- **Meticulously refined** — every detail considered

---

## Config Dials System

Three configuration dials control the intensity of design output. The standard baseline is **(8, 6, 4)**. These values drive layout decisions, animation complexity, and information density across all design work.

Adapt these values dynamically based on what the user explicitly requests. Use the baseline (or user-overridden) values as global variables to drive layout, motion, and density decisions.

### DESIGN_VARIANCE (1-10)

Controls how conventional or experimental the layout is.

| Level | Behavior |
|-------|----------|
| **1-3 (Predictable)** | Flexbox `justify-center`, strict 12-column symmetrical grids, equal paddings. Safe, conventional layouts. |
| **4-5 (Slightly Offset)** | Negative margin overlapping (`margin-top: -2rem`), varied image aspect ratios (e.g., 4:3 next to 16:9), left-aligned headers over center-aligned data. |
| **6-7 (Clearly Offset)** | More aggressive asymmetry. Mixed alignment strategies within sections. Intentional grid-breaking for emphasis. |
| **8-9 (Asymmetric)** | Masonry layouts, CSS Grid with fractional units (e.g., `grid-template-columns: 2fr 1fr 1fr`), massive empty zones (`padding-left: 20vw`). Centered hero sections are banned at these levels. |
| **10 (Artsy Chaos)** | Fully experimental compositions. Unconventional spatial relationships. Maximum creative freedom. |

**Mobile override (levels 4-10):** Any asymmetric layout above `md:` must aggressively fall back to a strict, single-column layout (`w-full`, `px-4`, `py-8`) on viewports below 768px to prevent horizontal scrolling and layout breakage.

### MOTION_INTENSITY (1-10)

Controls the presence and complexity of animation.

| Level | Behavior |
|-------|----------|
| **1-2 (Static)** | No automatic animations at all. Only CSS `:hover` and `:active` state transitions. |
| **3 (Minimal)** | Basic hover and active states. Simple, fast transitions (under 200ms). |
| **4-5 (Fluid CSS)** | CSS transitions with custom cubic-beziers (e.g., `transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1)`). Animation-delay cascades for load-in reveals. Strictly `transform` and `opacity` only. Use `will-change: transform` sparingly. |
| **6-7 (Choreographed)** | Staggered reveals on scroll. Purposeful entrance animations. Spring physics for interactive elements (`type: "spring", stiffness: 100, damping: 20`). Continuous micro-animations on status indicators. |
| **8-9 (Advanced Choreography)** | Complex scroll-triggered reveals or parallax. Framer Motion hooks. Magnetic hover physics on buttons. Perpetual micro-interactions (pulse, typewriter, float, shimmer). Layout transitions with `layoutId`. |
| **10 (Cinematic)** | Full scroll-driven sequences. GSAP ScrollTrigger for scrolltelling. 3D/WebGL canvas backgrounds. Video-frame scrubbing tied to scroll position. |

**Performance rule:** Never use `window.addEventListener('scroll')` — use IntersectionObserver or Framer Motion's `whileInView`. At levels 8+, isolate perpetual animations in their own memoized client components to prevent parent re-renders.

### VISUAL_DENSITY (1-10)

Controls how much information is packed into the viewport.

| Level | Behavior |
|-------|----------|
| **1-2 (Art Gallery)** | Vast whitespace. Huge section gaps (`py-24` to `py-40`). Everything feels very expensive and clean. Single focal points per viewport. |
| **3 (Museum)** | Generous spacing but with purposeful content grouping. Breathing room is the primary design element. |
| **4-5 (Daily App)** | Standard spacing for web applications. Comfortable padding. Clear content hierarchy through spacing variation. |
| **6-7 (Productive)** | Tighter spacing, more content per viewport. Cards and containers used where they communicate hierarchy. Information-rich but not cramped. |
| **8-9 (Dashboard)** | Compact layouts. Small paddings. 1px line separators instead of card containers. Data-dense with clear scan patterns. |
| **10 (Cockpit)** | Maximum density. Tiny paddings. No card boxes — just hairline separators. Everything packed. Monospace font (`font-mono`) mandatory for all numbers. |

**Density rule (levels 8+):** Generic card containers are banned. Use logic-grouping via `border-t`, `divide-y`, or purely negative space. Data metrics should breathe without being boxed unless elevation (z-index) is functionally required.

---

## Absolute Zero — Banned Anti-Patterns

These patterns instantly identify output as AI-generated. They are never acceptable regardless of context.

### Absolute Bans (CSS-Level)

**Ban 1: Side-stripe borders on cards/list items/callouts/alerts**
- Pattern: `border-left:` or `border-right:` with width greater than 1px
- Includes hard-coded colors AND CSS variables
- Forbidden: `border-left: 3px solid red`, `border-left: 4px solid var(--color-warning)`, etc.
- This is the single most overused "design touch" in admin, dashboard, and medical UIs
- Rewrite: use full borders, background tints, leading numbers/icons, or no visual indicator at all

**Ban 2: Gradient text**
- Pattern: `background-clip: text` combined with a gradient background
- Forbidden: any combination that makes text fill come from a `linear-gradient`, `radial-gradient`, or `conic-gradient`
- Rewrite: use a single solid color for text. For emphasis, use weight or size, not gradient fill.

### Banned Defaults

| Category | Banned | Use Instead |
|----------|--------|-------------|
| **Fonts** | Inter, Roboto, Arial, Open Sans, Helvetica, Syne, and the full reflex-font list | Unique fonts matched to brand personality via the 4-step font selection procedure |
| **Icons** | Thick-stroked Lucide, FontAwesome, Material defaults | Ultra-light precise lines: Phosphor Light, Remix Line, Radix |
| **Borders** | Generic 1px solid gray | Hairline borders with tinted colors, or no borders at all |
| **Shadows** | Harsh dark drop shadows (`shadow-md`, `rgba(0,0,0,0.3)`) | Diffused ambient shadows tinted to background hue |
| **Layouts** | Edge-to-edge sticky navbars, symmetrical 3-column Bootstrap grids | Floating nav pills, asymmetric grids with whitespace |
| **Motion** | `linear` or `ease-in-out`, bounce/elastic easing | Custom cubic-beziers, exponential easing (ease-out-quart/quint/expo) |
| **Colors** | Pure black (#000), pure white (#fff), AI purple/blue palette | Tinted near-blacks, tinted near-whites, brand-derived palettes |
| **Content** | "John Doe", "Acme", "99.99%", emojis in code | Creative realistic names, contextual brands, organic data |

---

## Core Principles

1. **Purposeful, not decorative.** Every visual element serves function, hierarchy, or brand identity. If a design element cannot justify its existence, remove it.

2. **Accessibility first.** WCAG compliance is a floor, not a ceiling. Color contrast, keyboard navigation, screen reader support, and reduced motion preferences are non-negotiable starting points.

3. **Performance-conscious.** Animate only `transform` and `opacity`. Apply `backdrop-blur` only to fixed/sticky elements. Isolate heavy animations in dedicated components. Never sacrifice frame rate for visual flair.

4. **Context-aware.** Derive every major decision — theme, typography, density, motion — from the actual users, their environment, and their state of mind. Never apply universal defaults.

5. **Anti-generic.** Actively combat the statistical biases of AI output. Reject reflex font choices, ban known AI aesthetic patterns, vary approach across projects, and apply the AI slop test to every deliverable.

6. **Bold and committed.** Choose a clear aesthetic direction and execute it with conviction. Timid, hedged, "safe" design is worse than a strong direction that needs iteration. The point is to choose, not to retreat.

---

## Lifecycle Guide — Which Reference for What Phase

| Phase | What You Do | Reference to Read |
|-------|-------------|-------------------|
| **PLAN** | Gather project context, understand users, define brand | `01-context-gathering.md` |
| **SHAPE** | Discovery interview, produce design brief | `02-shape-discovery.md` |
| **BUILD** | Implement structure, layout, typography, color, states | `03-craft-flow.md` + domain references (spatial, typography, color, interaction) |
| **STYLE** | Apply design system, check against config dials | This file (`00-overview.md`) for dials and anti-patterns |
| **REVIEW** | Run AI slop test, check every state, check responsive | This file (`00-overview.md`) for the slop test checklist |
| **REFINE** | Visual iteration in browser, fix discrepancies | `03-craft-flow.md` (Step 4: Visual Iteration) |
| **HARDEN** | Performance guardrails, accessibility audit, edge cases | Domain references (responsive, interaction, motion) |
| **UPGRADE** | Apply style archetypes, advanced patterns | `style-archetypes/` directory for vibe and layout archetypes |

Start at PLAN for new projects. Start at SHAPE for new features in existing projects. Start at BUILD for small tweaks with clear direction. Always finish with REVIEW.
