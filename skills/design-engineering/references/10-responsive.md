# Responsive Design

## Table of Contents

- [Mobile-First Approach](#mobile-first-approach)
- [Content-Driven Breakpoints](#content-driven-breakpoints)
- [Fluid Values with clamp()](#fluid-values-with-clamp)
- [Input Method Detection](#input-method-detection)
- [Safe Areas](#safe-areas)
- [Responsive Images](#responsive-images)
- [Layout Adaptation](#layout-adaptation)
- [Adaptation Strategies by Context](#adaptation-strategies-by-context)
- [Touch Adaptation](#touch-adaptation)
- [Testing on Real Devices](#testing-on-real-devices)
- [Common Mistakes to Avoid](#common-mistakes-to-avoid)

---

## Mobile-First Approach

Start with base styles for the smallest screen. Use `min-width` media queries to layer complexity as viewport grows. Desktop-first (`max-width`) forces mobile to download and override unnecessary styles.

```css
/* Base styles: mobile */
.grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Tablet and up */
@media (min-width: 768px) {
  .grid {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .grid > * {
    flex: 1 1 45%;
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .grid > * {
    flex: 1 1 30%;
  }
}
```

### Why Mobile-First

- Forces you to prioritize content and features.
- Mobile loads only what it needs -- no wasted downloads.
- Progressive enhancement is more robust than graceful degradation.
- Smaller screens are the harder constraint to design for.

---

## Content-Driven Breakpoints

Do not chase device sizes. Let content tell you where to break.

### Process

1. Start at the narrowest width (320px).
2. Stretch the viewport until the design breaks or looks wrong.
3. Add a breakpoint at that width.
4. Continue stretching until the next break.

### Common Breakpoints

Three breakpoints usually suffice for most layouts:

| Breakpoint | Typical Use |
|------------|-------------|
| 640px | Small tablets, large phones in landscape |
| 768px | Tablets in portrait |
| 1024px | Tablets in landscape, small desktops |

These are starting points, not rules. Your content may break at 580px or 900px -- use whatever your layout needs.

### Container Queries

When a component's layout depends on its container width (not the viewport), use container queries:

```css
.card-container {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 200px 1fr;
  }
}
```

Container queries make components truly reusable across different layout contexts (sidebar, main content, full-width).

---

## Fluid Values with clamp()

Reduce breakpoint dependency by using `clamp()` for smoothly scaling values:

```css
/* Font size: 1rem at minimum, scales with viewport, caps at 2rem */
h1 {
  font-size: clamp(1.5rem, 1rem + 2vw, 3rem);
}

/* Padding: fluid between 1rem and 3rem */
.section {
  padding: clamp(1rem, 3vw, 3rem);
}

/* Container width: fluid with min and max */
.container {
  width: clamp(320px, 90vw, 1200px);
  margin-inline: auto;
}
```

### When to Use clamp()

- **Typography**: Fluid font sizes that scale smoothly.
- **Spacing**: Padding and margins that adapt without jumps.
- **Container widths**: Max-width patterns with fluid behavior.
- **Gap values**: Grid and flex gaps that scale proportionally.

### When Not to Use clamp()

- When you need a sharp layout change (two columns to one column).
- For values that should remain fixed regardless of viewport.
- When the scaling creates awkward intermediate states.

---

## Input Method Detection

Screen size does not tell you the input method. A laptop may have a touchscreen. A tablet may have a keyboard attached. Use pointer and hover media queries:

```css
/* Fine pointer: mouse, trackpad */
@media (pointer: fine) {
  .button { padding: 8px 16px; }
  .link { text-decoration: underline; }
}

/* Coarse pointer: touch, stylus */
@media (pointer: coarse) {
  .button { padding: 12px 20px; min-height: 44px; }
  .link { padding: 8px 0; }
}

/* Device supports hover */
@media (hover: hover) {
  .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

/* Device does not support hover */
@media (hover: none) {
  /* No hover effects -- use active/focus instead */
  .card:active {
    transform: scale(0.98);
  }
}
```

### Key Principle

Never rely on hover for functionality. Touch users cannot hover. Hover effects should enhance, not enable. Any information revealed on hover must be accessible through another interaction (tap, focus, visible UI).

---

## Safe Areas

Modern phones have notches, camera islands, rounded corners, and home indicators. Use `env()` safe area insets to prevent content from being obscured:

```css
body {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}

/* Combine with your own spacing */
.footer {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}

.sidebar {
  padding-left: max(1.5rem, env(safe-area-inset-left));
}
```

### Enable viewport-fit

You must opt in to safe area insets with the viewport meta tag:

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

Without `viewport-fit=cover`, the browser adds its own padding and `env()` values return 0.

---

## Responsive Images

### srcset with Width Descriptors

Let the browser choose the optimal image based on viewport and device pixel ratio:

```html
<img
  src="hero-800.jpg"
  srcset="
    hero-400.jpg 400w,
    hero-800.jpg 800w,
    hero-1200.jpg 1200w,
    hero-1600.jpg 1600w
  "
  sizes="(max-width: 768px) 100vw, 50vw"
  alt="Product showcase"
>
```

- `srcset` lists available images with their actual pixel widths (`w` descriptors).
- `sizes` tells the browser how wide the image will display at each breakpoint.
- The browser picks the best file based on viewport width AND device pixel ratio.

### Picture Element for Art Direction

Use `<picture>` when you need different crops or compositions at different sizes, not just different resolutions:

```html
<picture>
  <source media="(min-width: 1024px)" srcset="hero-wide.jpg">
  <source media="(min-width: 768px)" srcset="hero-medium.jpg">
  <img src="hero-tall.jpg" alt="Product showcase">
</picture>
```

### Image Format

Use modern formats with fallbacks:

```html
<picture>
  <source srcset="image.avif" type="image/avif">
  <source srcset="image.webp" type="image/webp">
  <img src="image.jpg" alt="Description">
</picture>
```

### Lazy Loading

Use native lazy loading for images below the fold:

```html
<img src="photo.jpg" alt="..." loading="lazy">
```

Never lazy-load the largest contentful paint (LCP) image -- it needs to load immediately.

---

## Layout Adaptation

### Navigation Stages

Navigation should transform across breakpoints, not just hide:

| Viewport | Pattern |
|----------|---------|
| Mobile (< 640px) | Hamburger icon with slide-out drawer or bottom sheet |
| Tablet (640-1024px) | Horizontal compact -- icons with abbreviated labels |
| Desktop (> 1024px) | Full horizontal navigation with labels, possibly with dropdowns |

### Table to Card Transform

Data tables do not work on narrow screens. Transform rows to cards:

```css
/* Desktop: standard table */
@media (min-width: 768px) {
  table { display: table; }
}

/* Mobile: cards */
@media (max-width: 767px) {
  table, thead, tbody, tr, td { display: block; }
  thead { display: none; }
  td::before {
    content: attr(data-label);
    font-weight: bold;
    display: block;
  }
}
```

### Collapsible Content

Use `<details>/<summary>` for content that can collapse on mobile while remaining expanded on desktop:

```html
<details open>
  <summary>Filter options</summary>
  <div class="filter-panel">
    <!-- Filter controls -->
  </div>
</details>
```

```css
@media (min-width: 768px) {
  details > summary { display: none; }
  details[open] .filter-panel { display: block; }
}
```

---

## Adaptation Strategies by Context

### Mobile-Specific

- **Layout**: Single column, vertical stacking, full-width components.
- **Navigation**: Bottom navigation or hamburger menu.
- **Touch targets**: 44px minimum, generous spacing between interactive elements.
- **Thumb zones**: Place primary actions within easy thumb reach (bottom third of screen).
- **Content**: Progressive disclosure, shorter text, 16px minimum font size.
- **Forms**: Single column, large inputs, appropriate keyboard types (`inputmode`).

### Tablet-Specific

- **Layout**: Two-column or master-detail views.
- **Orientation**: Adapt to both portrait and landscape.
- **Input**: Support both touch and pointer.
- **Navigation**: Side drawer or persistent side panel.
- **Density**: Denser than phone but not as dense as desktop.

### Desktop-Specific

- **Layout**: Multi-column, side navigation always visible, multiple information panels.
- **Interaction**: Hover states, keyboard shortcuts, right-click context menus, drag and drop.
- **Content**: More information upfront, data tables with many columns, richer visualizations.
- **Width constraint**: Use `max-width` -- do not stretch layouts to 4K width.

### Print Adaptation

```css
@media print {
  nav, footer, .sidebar, button { display: none; }
  a[href]::after { content: " (" attr(href) ")"; }
  body { font-size: 12pt; color: black; background: white; }
  .page-break { break-before: page; }
}
```

- Remove navigation, interactive elements, and decorative content.
- Show full URLs after links.
- Add page numbers, headers, and print date.
- Use `break-before` and `break-after` for logical page breaks.
- Convert to black and white or limited color.

### Email Adaptation

- Maximum 600px width, single column only.
- Table-based layouts for email client compatibility.
- Inline CSS -- no external stylesheets.
- Large, obvious call-to-action buttons (not text links).
- No hover states -- not reliable in email clients.
- Deep link to web app for complex interactions.

---

## Touch Adaptation

### Minimum Target Size

All interactive elements must be at least 44x44px for touch:

```css
@media (pointer: coarse) {
  button, a, input[type="checkbox"], input[type="radio"] {
    min-width: 44px;
    min-height: 44px;
  }
}
```

### Spacing Between Targets

Add enough spacing between interactive elements to prevent accidental taps. Minimum 8px gap between touch targets.

### Thumb Zone Awareness

On phones held in one hand, the bottom third of the screen is easiest to reach. Place primary actions there:

- Navigation bars at the bottom.
- Primary action buttons (FAB) in the lower right.
- Destructive or secondary actions at the top (harder to tap accidentally).

### Touch Feedback

Provide visual feedback for touch interactions:

```css
@media (pointer: coarse) {
  button:active {
    transform: scale(0.97);
    opacity: 0.9;
  }
}
```

### Swipe Gestures

When implementing swipe gestures:

- Always provide a visible alternative (button, menu item).
- Show hints that swipe is available (partially revealed action).
- Support both left and right swipe where it makes sense.
- Include momentum and bounce physics for natural feel.

---

## Testing on Real Devices

Browser DevTools device emulation is useful for layout testing but misses critical real-world factors:

| DevTools Shows | DevTools Misses |
|----------------|-----------------|
| Layout at various widths | Actual touch interactions |
| Responsive breakpoints | Real CPU/memory constraints |
| Basic viewport behavior | Network latency patterns |
| Approximate rendering | Font rendering differences |
| | Browser chrome and keyboard appearance |
| | Safe area inset behavior |
| | Scroll momentum and overscroll |

### Minimum Real Device Testing

- One real iPhone (latest or recent iOS).
- One real Android phone (mid-range -- reveals performance issues).
- A tablet if your audience uses them.
- Test both portrait and landscape orientations.

### What to Check on Real Devices

- Touch target sizes feel right (not just measure correctly).
- Scrolling feels smooth, not janky.
- Text is readable without zooming.
- Forms work with the on-screen keyboard.
- Fixed/sticky elements behave correctly with keyboard open.
- Images load at appropriate resolution.

---

## Common Mistakes to Avoid

- **Desktop-first design**: Starting with desktop and squeezing into mobile is backwards. Mobile constraints force better prioritization.
- **Device detection vs feature detection**: Do not sniff user agent strings. Use CSS media queries (`@media (pointer: coarse)`) and `@supports` for feature detection.
- **Separate mobile/desktop codebases**: Doubles maintenance, creates inconsistencies. One responsive codebase serves all viewports.
- **Ignoring tablet and landscape**: These are real usage modes. Do not assume portrait-only.
- **Assuming mobile means low-power**: Modern phones are powerful. Adapt presentation, not capability.
- **Overusing `display: none`**: Hidden content is still downloaded. Lazy-load or conditionally render optional content.
- **Fixed-width layouts**: Use relative units (`%`, `rem`, `vw`), `clamp()`, and flexible layout systems (Grid, Flexbox).
- **Forgetting about zoom**: Test at 200% zoom. Fixed layouts and `vw`-only font sizes break under zoom.
