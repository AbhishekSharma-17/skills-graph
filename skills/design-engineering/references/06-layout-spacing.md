# Layout & Spacing

## Table of Contents

- [4pt Base Scale](#4pt-base-scale)
- [Semantic Token Names](#semantic-token-names)
- [Self-Adjusting Grids](#self-adjusting-grids)
- [Container Queries](#container-queries)
- [Visual Hierarchy](#visual-hierarchy)
- [Cards Are Optional](#cards-are-optional)
- [Breaking Card Grid Monotony](#breaking-card-grid-monotony)
- [Depth and Elevation](#depth-and-elevation)
- [Optical Adjustments](#optical-adjustments)
- [Touch Targets](#touch-targets)
- [Layout Assessment](#layout-assessment)
- [Layout Improvement Process](#layout-improvement-process)

---

## 4pt Base Scale

**Use 4pt, not 8pt.** 8pt systems are too coarse -- you will frequently need 12px (between 8 and 16). A 4pt base provides the granularity needed for real UI work:

| Token | Value | Typical Use |
|-------|-------|-------------|
| 4px | 0.25rem | Micro gaps, icon padding |
| 8px | 0.5rem | Tight spacing, inline elements |
| 12px | 0.75rem | Form field padding, compact lists |
| 16px | 1rem | Standard component padding |
| 24px | 1.5rem | Section padding, card gaps |
| 32px | 2rem | Group separation |
| 48px | 3rem | Major section breaks |
| 64px | 4rem | Page section spacing |
| 96px | 6rem | Hero/major division spacing |

Use `gap` for sibling spacing instead of margins -- it eliminates margin collapse and cleanup hacks.

Apply `clamp()` for fluid spacing that breathes on larger screens.

---

## Semantic Token Names

Name by relationship, not value:

| Do | Do Not |
|----|--------|
| `--space-xs` | `--spacing-4` |
| `--space-sm` | `--spacing-8` |
| `--space-md` | `--spacing-16` |
| `--space-lg` | `--spacing-32` |
| `--space-xl` | `--spacing-48` |
| `--space-2xl` | `--spacing-64` |
| `--space-3xl` | `--spacing-96` |

Semantic names survive redesigns. Value names create confusion when the scale changes.

Framework scales (Tailwind, etc.) and rem-based tokens both work. What matters is that values come from a defined set, not arbitrary numbers.

---

## Self-Adjusting Grids

### The Responsive Grid Without Breakpoints

```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-lg);
}
```

Columns are at least 280px wide, as many as fit per row, leftovers stretch to fill. No media queries needed.

### Named Grid Areas for Complex Layouts

For page-level layouts, use named grid areas and redefine them at breakpoints:

```css
.page {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar main"
    "footer footer";
}

@media (max-width: 768px) {
  .page {
    grid-template-areas:
      "header"
      "main"
      "sidebar"
      "footer";
  }
}
```

### Choosing the Right Layout Tool

- **Flexbox for 1D layouts:** Rows of items, nav bars, button groups, card contents, most component internals. Flex is simpler and more appropriate for the majority of layout tasks.
- **Grid for 2D layouts:** Page-level structure, dashboards, data-dense interfaces, anything where rows AND columns need coordinated control.
- **Do not default to Grid** when Flexbox with `flex-wrap` would be simpler and more flexible.

---

## Container Queries

Viewport queries are for page layouts. **Container queries are for components:**

```css
.card-container {
  container-type: inline-size;
}

.card {
  display: grid;
  gap: var(--space-md);
}

/* Card layout changes based on its container, not viewport */
@container (min-width: 400px) {
  .card {
    grid-template-columns: 120px 1fr;
  }
}
```

**Why this matters:** A card in a narrow sidebar stays compact, while the same card in a main content area expands -- automatically, without viewport hacks. Container queries make components truly portable.

---

## Visual Hierarchy

### The Squint Test

Blur your eyes (or screenshot and blur). Can you still identify:
- The most important element?
- The second most important?
- Clear groupings?

**If everything looks the same weight blurred, you have a hierarchy problem.**

### Hierarchy Through Multiple Dimensions

Do not rely on size alone. Combine:

| Tool | Strong Hierarchy | Weak Hierarchy |
|------|------------------|----------------|
| **Size** | 3:1 ratio or more | <2:1 ratio |
| **Weight** | Bold vs Regular | Medium vs Regular |
| **Color** | High contrast | Similar tones |
| **Position** | Top/left (primary) | Bottom/right |
| **Space** | Surrounded by white space | Crowded |

The best hierarchy uses 2-3 dimensions at once.

### Space as a Design Tool

Use the fewest dimensions needed for clear hierarchy. Space alone can be enough -- generous whitespace around an element draws the eye. Some of the most sophisticated designs achieve rhythm with just space and weight. Add color or size contrast only when simpler means are not sufficient.

### Reading Flow

In LTR languages, the eye naturally scans top-left to bottom-right, but primary action placement depends on context (bottom-right in dialogs, top in navigation).

---

## Cards Are Optional

Cards are overused. Do not reach for cards by default -- spacing and alignment create visual grouping naturally.

### When to Use Cards

- Content is truly distinct and actionable
- Items need visual comparison in a grid
- Content needs clear interaction boundaries (clickable, draggable)

### When Not to Use Cards

- Simple lists of related content (spacing suffices)
- Nested within other cards (**never nest cards inside cards**)
- When spacing, typography, and subtle dividers achieve the same grouping

---

## Breaking Card Grid Monotony

When card grids are appropriate, avoid the icon + heading + text pattern repeated identically:

### Techniques

- **Vary card sizes:** Make featured items larger, span multiple columns
- **Mix card types:** Combine image cards, stat cards, text cards in one grid
- **Use feature cards:** One large card with 2-3 smaller cards beside it
- **Intersperse non-card content:** Quotes, stats, or CTAs between card groups
- **Alternate layouts:** Some cards horizontal, some vertical

### Avoid

- Identical card grids everywhere (icon + heading + text, repeated endlessly)
- Default hero metric layout (big number, small label, stats, gradient) as a template unless displaying actual user data
- Centering everything -- left-aligned with asymmetric layouts often feels more designed

---

## Depth and Elevation

### Z-Index Scale

Create a semantic z-index scale instead of arbitrary numbers:

| Level | z-index | Use |
|-------|---------|-----|
| Base | 0 | Default content |
| Dropdown | 10 | Menus, popovers |
| Sticky | 20 | Sticky headers, toolbars |
| Modal backdrop | 30 | Overlay behind modals |
| Modal | 40 | Modal dialogs |
| Toast | 50 | Notifications, alerts |
| Tooltip | 60 | Tooltips, hover info |

Never use arbitrary z-index values (999, 9999).

### Shadow Scale

Build a consistent elevation scale:

| Level | Use | Guidance |
|-------|-----|----------|
| sm | Cards at rest, subtle separation | Barely visible |
| md | Hover states, slight lift | Noticeable but subtle |
| lg | Dropdowns, popovers | Clear elevation |
| xl | Modals, dialogs | Strong separation |

**Shadows should be subtle.** If you can clearly see it, it is probably too strong. Use elevation to reinforce hierarchy, not as decoration.

---

## Optical Adjustments

### Visual vs Mathematical Centering

Geometrically centered elements can look off-center due to visual weight distribution:

- **Play icons** in circles need to shift right (~2-3% of container width) because the triangle's visual center is left of its geometric center
- **Arrows** shift toward their direction
- **Text at `margin-left: 0`** looks indented due to letterform whitespace -- use negative margin (`-0.05em`) to optically align

### When to Adjust

Only nudge if you are confident it actually looks wrong. Do not adjust speculatively. Optical adjustments are small (1-3px) and purposeful.

---

## Touch Targets

### 44px Minimum

Buttons and interactive elements need at least 44px touch targets for accessibility, but they do not need to visually appear that large.

### Separating Visual Size from Hit Area

```css
.icon-button {
  width: 24px;   /* Visual size */
  height: 24px;
  position: relative;
}

.icon-button::before {
  content: '';
  position: absolute;
  inset: -10px;  /* Expand tap target to 44px */
}
```

This keeps the visual design compact while ensuring touch accessibility.

---

## Layout Assessment

Evaluate the current layout across these dimensions:

1. **Spacing consistency:** Are values from a defined scale, or arbitrary? Is all spacing equal (no rhythm)?
2. **Visual hierarchy:** Does the squint test pass? Can you identify primary, secondary, and groupings?
3. **Grid structure:** Is there a clear underlying structure? Are identical card grids used everywhere?
4. **Rhythm and variety:** Is there alternating tight/generous spacing? Or is every section structured the same way?
5. **Density:** Is the layout too cramped or too sparse? Does density match the content type (data-dense UIs tighter, marketing pages more air)?
6. **Responsiveness:** Does the layout adapt gracefully across screen sizes?

---

## Layout Improvement Process

1. **Establish spacing system** -- adopt a consistent scale (4pt base or framework scale). Replace all arbitrary values with tokens from the defined set.

2. **Create visual rhythm** -- tight grouping (8-12px) for related elements, generous separation (48-96px) between distinct sections. Varied spacing within sections, not every row at the same gap.

3. **Choose the right layout tools** -- Flexbox for 1D (rows, nav bars, component internals), Grid for 2D (page structure, dashboards). Do not default to Grid when Flex would be simpler.

4. **Break monotony** -- avoid identical card grids everywhere. Vary sizes, span columns, mix card types with non-card content. Use asymmetric compositions when appropriate.

5. **Strengthen hierarchy** -- apply the squint test. Use 2-3 dimensions (size, weight, color, space) for clear differentiation. Create content groupings through proximity and separation.

6. **Manage depth** -- build a semantic z-index scale, consistent shadow tokens. Use elevation to reinforce hierarchy, not as decoration.

7. **Make optical adjustments** -- visually center elements that look off despite geometric centering. Ensure touch targets meet 44px minimum while keeping visual design compact.

8. **Verify** -- squint test passes, spacing is consistent, hierarchy is clear within 2 seconds, layout is responsive, density matches content type.
