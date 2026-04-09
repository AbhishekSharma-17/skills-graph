# High-End Agency

Engineer $150k+ agency-level digital experiences with haptic depth, cinematic spatial rhythm, obsessive micro-interactions, and flawless fluid motion. Every output must exude Apple-esque / Linear-tier design language while never generating the exact same layout or aesthetic twice.

## Table of Contents

- [The "Absolute Zero" Directive](#the-absolute-zero-directive)
- [Creative Variance Engine](#creative-variance-engine)
- [Haptic Micro-Aesthetics](#haptic-micro-aesthetics)
- [Motion Choreography](#motion-choreography)
- [Performance Guardrails](#performance-guardrails)
- [Execution Protocol](#execution-protocol)
- [Pre-Output Checklist](#pre-output-checklist)

---

## The "Absolute Zero" Directive

If generated code includes ANY of the following, the design instantly fails.

### Banned Fonts

Inter, Roboto, Arial, Open Sans, Helvetica. Assume premium fonts are available: `Geist`, `Clash Display`, `PP Editorial New`, `Plus Jakarta Sans`.

### Banned Icons

Standard thick-stroked Lucide, FontAwesome, or Material Icons. Use only ultra-light, precise lines: Phosphor Light, Remix Line.

### Banned Borders and Shadows

- Generic `1px solid gray` borders
- Harsh, dark drop shadows (`shadow-md`, `rgba(0,0,0,0.3)`)

### Banned Layouts

- Edge-to-edge sticky navbars glued to the top
- Symmetrical 3-column Bootstrap-style grids without massive whitespace gaps

### Banned Motion

- Standard `linear` or `ease-in-out` transitions
- Instant state changes without interpolation

---

## Creative Variance Engine

Before writing code, select ONE combination from each category based on the prompt context. This ensures uniquely tailored but always premium output.

### Vibe and Texture Archetypes (Pick 1)

**Ethereal Glass** (SaaS / AI / Tech)
- Deepest OLED black (`#050505`)
- Radial mesh gradients (subtle glowing purple/emerald orbs) in background
- Vantablack cards with heavy `backdrop-blur-2xl` and pure `white/10` hairlines
- Wide geometric Grotesk typography

**Editorial Luxury** (Lifestyle / Real Estate / Agency)
- Warm creams (`#FDFBF7`), muted sage, or deep espresso tones
- High-contrast Variable Serif fonts for massive headings
- Subtle CSS noise/film-grain overlay (`opacity-[0.03]`) for physical paper feel

**Soft Structuralism** (Consumer / Health / Portfolio)
- Silver-grey or completely white backgrounds
- Massive bold Grotesk typography
- Airy, floating components with unbelievably soft, highly diffused ambient shadows

### Layout Archetypes (Pick 1)

**The Asymmetrical Bento**
- Masonry-like CSS Grid with varying card sizes (e.g., `col-span-8 row-span-2` next to stacked `col-span-4` cards)
- Breaks visual monotony
- **Mobile collapse:** Falls back to single-column stack (`grid-cols-1`) with generous vertical gaps (`gap-6`). All `col-span` overrides reset to `col-span-1`

**The Z-Axis Cascade**
- Elements stacked like physical cards, slightly overlapping with varying depths of field
- Subtle rotation (`-2deg` or `3deg`) to break the digital grid
- **Mobile collapse:** Remove all rotations and negative-margin overlaps below `768px`. Stack vertically with standard spacing. Overlapping elements cause touch-target conflicts on mobile

**The Editorial Split**
- Massive typography on the left half (`w-1/2`), with interactive scrollable horizontal image pills or staggered cards on the right
- **Mobile collapse:** Converts to full-width vertical stack (`w-full`). Typography block on top, interactive content below with horizontal scroll preserved if needed

### Mobile Override (Universal)

Any asymmetric layout above `md:` MUST aggressively fall back to `w-full`, `px-4`, `py-8` on viewports below `768px`. Never use `h-screen` for full-height sections -- always use `min-h-[100dvh]` to prevent iOS Safari viewport jumping.

---

## Haptic Micro-Aesthetics

### The Double-Bezel (Doppelrand / Nested Architecture)

Never place a premium card, image, or container flatly on the background. They must look like physical, machined hardware -- a glass plate sitting in an aluminum tray.

**Outer Shell:**
```
- Subtle background: bg-black/5 or bg-white/5
- Hairline outer border: ring-1 ring-black/5 or border border-white/10
- Specific padding: p-1.5 or p-2
- Large outer radius: rounded-[2rem]
```

**Inner Core:**
```
- Distinct background color
- Inner highlight: shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)]
- Mathematically calculated smaller radius: rounded-[calc(2rem-0.375rem)]
- Creates concentric curves between shell and core
```

### Button-in-Button Trailing Icon

Primary interactive buttons must be fully rounded pills (`rounded-full`) with generous padding (`px-6 py-3`).

When a button has an arrow (`->` or arrow icon), it never sits naked next to the text. It must be nested inside its own distinct circular wrapper:

```
w-8 h-8 rounded-full bg-black/5 dark:bg-white/10
flex items-center justify-center
```

Placed completely flush with the main button's right inner padding.

### Spatial Rhythm and Tension

- **Macro-whitespace:** Double your standard padding. Use `py-24` to `py-40` for sections. Allow the design to breathe heavily.
- **Eyebrow tags:** Precede major H1/H2s with a microscopic pill-shaped badge:

```
rounded-full px-3 py-1 text-[10px] uppercase tracking-[0.2em] font-medium
```

---

## Motion Choreography

Never use default transitions. All motion must simulate real-world mass and spring physics.

**Global timing function:**
```css
transition: all 700ms cubic-bezier(0.32, 0.72, 0, 1);
```

### The Fluid Island Nav

- **Closed state:** Navbar is a floating glass pill detached from the top (`mt-6`, `mx-auto`, `w-max`, `rounded-full`)
- **Hamburger morph:** The 2-3 hamburger lines fluidly rotate and translate to form a perfect X (`rotate-45` and `-rotate-45` with absolute positioning). Not a visibility toggle -- a physical transformation
- **Modal expansion:** Menu opens as a massive, screen-filling overlay with heavy glass effect (`backdrop-blur-3xl bg-black/80` or `bg-white/80`)
- **Staggered mask reveal:** Navigation links fade in and slide up (`translate-y-12 opacity-0` to `translate-y-0 opacity-100`) with staggered delay (`delay-100`, `delay-150`, `delay-200` for each item)

### Magnetic Button Hover Physics

Use the `group` utility. On hover, do not just change background color:

- Scale entire button down slightly: `active:scale-[0.98]` (simulates physical pressing)
- Nested inner icon circle translates diagonally: `group-hover:translate-x-1 group-hover:-translate-y-[1px]`
- Icon scales up slightly: `scale-105`
- Creates internal kinetic tension between button body and icon

### Scroll Interpolation (Entry Animations)

Elements never appear statically on load. As they enter the viewport:

```
Initial:  translate-y-16 blur-md opacity-0
Final:    translate-y-0 blur-0 opacity-100
Duration: 800ms+
```

For JavaScript-driven scroll reveals, use `IntersectionObserver` or Framer Motion `whileInView`. Never use `window.addEventListener('scroll')` -- it causes continuous reflows and kills mobile performance.

---

## Performance Guardrails

### GPU-Safe Animation

Never animate `top`, `left`, `width`, or `height`. Animate exclusively via `transform` and `opacity`. Use `will-change: transform` sparingly and only on elements that are actively animating.

### Blur Constraints

Apply `backdrop-blur` only to fixed or sticky elements (navbars, overlays). Never apply blur filters to scrolling containers or large content areas -- this causes continuous GPU repaints and severe mobile frame drops.

### Grain and Noise Overlays

Apply noise textures exclusively to fixed, `pointer-events-none` pseudo-elements:

```css
position: fixed;
inset: 0;
z-index: 50;
pointer-events: none;
```

Never attach them to scrolling containers.

### Z-Index Discipline

Do not use arbitrary `z-50` or `z-[9999]`. Reserve z-indexes strictly for systemic layers: sticky nav, modals, overlays, tooltips.

---

## Execution Protocol

Follow this exact sequence when generating UI code:

1. **Silent thought** -- Roll the Variance Engine. Choose Vibe and Layout Archetypes based on the prompt context to ensure unique output
2. **Scaffold** -- Establish background texture, macro-whitespace scale, and massive typography sizes
3. **Architect** -- Build the DOM using Double-Bezel (Doppelrand) technique for all major cards, inputs, and feature grids. Use exaggerated squircle radii (`rounded-[2rem]`)
4. **Choreograph** -- Inject custom `cubic-bezier` transitions, staggered navigation reveals, and button-in-button hover physics
5. **Output** -- Deliver flawless, pixel-perfect code. No basic generic fallbacks

---

## Pre-Output Checklist

Evaluate code against this matrix before delivering. This is the last filter.

- [ ] No banned fonts, icons, borders, shadows, layouts, or motion patterns are present
- [ ] A Vibe Archetype and Layout Archetype were consciously selected and applied
- [ ] All major cards and containers use Double-Bezel nested architecture (outer shell + inner core)
- [ ] CTA buttons use Button-in-Button trailing icon pattern where applicable
- [ ] Section padding is at minimum `py-24` -- the layout breathes heavily
- [ ] All transitions use custom cubic-bezier curves -- no `linear` or `ease-in-out`
- [ ] Scroll entry animations are present -- no element appears statically
- [ ] Layout collapses gracefully below `768px` to single-column with `w-full` and `px-4`
- [ ] All animations use only `transform` and `opacity` -- no layout-triggering properties
- [ ] `backdrop-blur` is only applied to fixed/sticky elements, never to scrolling content
- [ ] The overall impression reads as "$150k agency build", not "template with nice fonts"
