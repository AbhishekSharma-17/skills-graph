# Typography

## Table of Contents

- [Font Selection Procedure](#font-selection-procedure)
- [Banned Reflex Fonts](#banned-reflex-fonts)
- [Font Pairing](#font-pairing)
- [Type Scale](#type-scale)
- [Hierarchy](#hierarchy)
- [Line Length and Readability](#line-length-and-readability)
- [Vertical Rhythm](#vertical-rhythm)
- [Web Font Loading](#web-font-loading)
- [OpenType Features](#opentype-features)
- [Typography System Architecture](#typography-system-architecture)
- [Accessibility](#accessibility)
- [Assessment Checklist](#assessment-checklist)
- [Typography Improvement Process](#typography-improvement-process)

---

## Font Selection Procedure

The most common AI typography failure is reaching for the same "tasteful" font for every editorial brief, the same "modern" font for every tech brief, the same "elegant serif" for every premium brief. Those reflexes produce monoculture across projects. The right font is one whose physical character matches *this specific* brand, audience, and moment.

### The 5-Step Process

1. **Define brand voice in 3 concrete words.** Not "modern" or "elegant" -- those are dead categories. Try "warm and mechanical and opinionated" or "calm and clinical and careful" or "fast and dense and unimpressed" or "handmade and a little weird."

2. **Physical object analogy.** Imagine the font as a physical object the brand could ship: a typewriter ribbon, a hand-lettered shop sign, a 1970s mainframe terminal manual, a fabric label on the inside of a coat, a museum exhibit caption, a tax form, a children's book printed on cheap newsprint. Whichever physical object fits the three words is pointing at the right *kind* of typeface.

3. **Reject reflex fonts.** Before browsing, acknowledge your defaults. If you find yourself reaching for the same display font you used last time, make yourself pick something else. Reject the first thing that "looks designy" -- that is your trained-everywhere reflex.

4. **Browse catalogs with the physical object in mind.** Sources: Google Fonts, Pangram Pangram, Adobe Fonts, Future Fonts, ABC Dinamo. Keep the physical object metaphor active while browsing.

5. **Cross-check against anti-reflexes:**
   - A technical/utilitarian brief does NOT need a serif "for warmth." Most tech tools should look like tech tools.
   - An editorial/premium brief does NOT need the same expressive serif everyone is using right now. Premium can be Swiss-modern, neo-grotesque, literal monospace, or a quiet humanist sans.
   - A children's product does NOT need a rounded display font. Kids' books use real type.
   - A "modern" brief does NOT need a geometric sans. The most modern thing you can do is not use the font everyone else is using.

### System Fonts Are Underrated

`-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui` looks native, loads instantly, and is highly readable. Consider this for apps where performance matters more than personality.

### Invisible Defaults to Avoid When Personality Matters

Inter, Roboto, Open Sans, Lato, Montserrat. These are everywhere, making your design feel generic. They are fine for documentation or tools where personality is not the goal -- but if you want distinctive design, look elsewhere.

---

## Banned Reflex Fonts

These fonts are banned by default because they have become AI-design reflexes -- reached for automatically without genuine consideration. Using them produces monoculture across projects.

**Serif reflexes:** Fraunces, Newsreader, Lora, Crimson Text, Playfair Display, Crimson Pro, Libre Baskerville, Source Serif Pro

**Sans-serif reflexes:** DM Sans, Outfit, Syne, Space Grotesk, Plus Jakarta Sans, General Sans, Cabinet Grotesk, Satoshi

**NOTE:** These bans can be overridden by specific style archetypes. If a style archetype explicitly calls for one of these fonts, the archetype takes precedence. The ban exists to prevent *default* reaching -- not to prohibit deliberate, justified use.

---

## Font Pairing

**The non-obvious truth:** You often do not need a second font. One well-chosen font family in multiple weights creates cleaner hierarchy than two competing typefaces. Only add a second font when you need genuine contrast (e.g., display headlines + body serif).

When pairing, contrast on multiple axes:
- **Serif + Sans** (structure contrast)
- **Geometric + Humanist** (personality contrast)
- **Condensed display + Wide body** (proportion contrast)

**Never pair fonts that are similar but not identical** (e.g., two geometric sans-serifs). They create visual tension without clear hierarchy.

Limit to 2-3 font families maximum per project.

---

## Type Scale

### Modular Scale

Use fewer sizes with more contrast. A 5-size system covers most needs:

| Role | Typical Ratio | Use Case |
|------|---------------|----------|
| xs | 0.75rem | Captions, legal text |
| sm | 0.875rem | Secondary UI, metadata |
| base | 1rem (16px+) | Body text |
| lg | 1.25-1.5rem | Subheadings, lead text |
| xl+ | 2-4rem | Headlines, hero text |

Popular ratios: **1.25** (major third), **1.333** (perfect fourth), **1.5** (perfect fifth). Pick one ratio of at least 1.25 and commit to it. Muddy hierarchy comes from too many sizes too close together (14px, 15px, 16px, 18px).

### Fixed vs Fluid Sizing

**App UIs (dashboards, data-dense interfaces):** Use a fixed `rem`-based type scale, optionally adjusted at 1-2 breakpoints. Fluid sizing undermines the spatial predictability that dense, container-based layouts need. No major design system (Material, Polaris, Primer, Carbon) uses fluid type in product UI.

**Marketing / content pages:** Use fluid sizing via `clamp(min, preferred, max)` for headings and display text. The middle value (e.g., `5vw + 1rem`) controls scaling rate -- higher vw = faster scaling. Add a rem offset so it does not collapse to 0 on small screens. Keep body text fixed even on marketing pages.

---

## Hierarchy

### Building Clear Hierarchy

Combine multiple dimensions -- do not rely on size alone:

| Tool | Strong Hierarchy | Weak Hierarchy |
|------|------------------|----------------|
| **Size** | 3:1 ratio or more | <2:1 ratio |
| **Weight** | Bold vs Regular | Medium vs Regular |
| **Color** | High contrast | Similar tones |
| **Space** | Surrounded by whitespace | Crowded |

The best hierarchy uses 2-3 dimensions at once: a heading that is larger, bolder, AND has more space above it.

### Minimum Requirements

- At least 3 distinct typographic levels visible at a glance (heading, body, caption)
- Font sizes should not be too close together (14px and 15px is invisible difference)
- Weight contrasts must be strong enough (Medium vs Regular is barely visible -- use Bold vs Regular)
- Varied weights and sizes, not just one font at slightly different sizes

### Weight Strategy

- Define clear roles for each weight and stick to them
- Do not use more than 3-4 weights (Regular, Medium, Semibold, Bold is plenty)
- Load only the weights you actually use (each weight adds to page load)

---

## Line Length and Readability

### Optimal Line Length

**65-75 characters per line** is optimal. Enforce with `max-width` on text containers using `ch` units:

```css
.prose {
  max-width: 65ch;
}
```

Line-height scales inversely with line length -- narrow columns need tighter leading, wide columns need more.

### Body Text Minimum

- Body text must be at least **16px / 1rem**
- Smaller than this strains eyes and fails WCAG on mobile
- Use `rem` for font sizes to respect user browser settings, never `px` for body text

### Contrast

- Ensure sufficient contrast between text and background
- Increase line-height slightly for light-on-dark text (add 0.05-0.1 to normal line-height) -- perceived weight is lighter, so text needs more breathing room

---

## Vertical Rhythm

Your `line-height` should be the base unit for ALL vertical spacing. If body text has `line-height: 1.5` on `16px` type (= 24px), spacing values should be multiples of 24px. This creates subconscious harmony -- text and space share a mathematical foundation.

### Line-Height by Context

| Context | Line-Height |
|---------|-------------|
| Headings (large display) | 1.1-1.2 |
| Subheadings | 1.2-1.3 |
| Body text | 1.5-1.7 |
| Light-on-dark text | Add 0.05-0.1 to normal |

### Letter-Spacing

- Slightly open for small caps and uppercase text
- Default or tight for large display text
- Apply intentionally, not as a blanket default

---

## Web Font Loading

The layout shift problem: fonts load late, text reflows, and users see content jump.

### Metric-Matched Fallbacks

```css
/* 1. Use font-display: swap for visibility */
@font-face {
  font-family: 'CustomFont';
  src: url('font.woff2') format('woff2');
  font-display: swap;
}

/* 2. Match fallback metrics to minimize shift */
@font-face {
  font-family: 'CustomFont-Fallback';
  src: local('Arial');
  size-adjust: 105%;
  ascent-override: 90%;
  descent-override: 20%;
  line-gap-override: 10%;
}

body {
  font-family: 'CustomFont', 'CustomFont-Fallback', sans-serif;
}
```

Tools like Fontaine calculate these overrides automatically.

### Performance Checklist

- Use `font-display: swap` for all custom fonts
- Subset fonts to include only needed character ranges
- Use `woff2` format (best compression)
- Preload critical fonts with `<link rel="preload">`
- Load only the weights you actually use
- Define metric-matched fallbacks to prevent layout shift

---

## OpenType Features

Most developers do not know these exist. Use them for polish:

```css
/* Tabular numbers for data alignment */
.data-table { font-variant-numeric: tabular-nums; }

/* Proper fractions */
.recipe-amount { font-variant-numeric: diagonal-fractions; }

/* Small caps for abbreviations */
abbr { font-variant-caps: all-small-caps; }

/* Disable ligatures in code */
code { font-variant-ligatures: none; }

/* Enable kerning */
body { font-kerning: normal; }
```

### Variable Fonts

Variable fonts contain multiple weights/widths in a single file. Benefits:
- Fewer HTTP requests (one file instead of multiple weights)
- Fine-grained weight control (any value, not just 400/700)
- Smaller total file size when using 3+ weights

Check what features your font supports at Wakamai Fondue (wakamaifondue.com).

---

## Typography System Architecture

Name tokens semantically, not by value:

| Do | Do Not |
|----|--------|
| `--text-body` | `--font-size-16` |
| `--text-heading` | `--font-size-32` |
| `--text-caption` | `--font-size-12` |

Include font stacks, size scale, weights, line-heights, and letter-spacing in your token system. Semantic names survive redesigns -- value names do not.

---

## Accessibility

- **Never disable zoom:** `user-scalable=no` breaks accessibility. If your layout breaks at 200% zoom, fix the layout.
- **Use rem/em for font sizes:** This respects user browser settings. Never use `px` for body text.
- **Minimum 16px body text:** Smaller strains eyes and fails WCAG on mobile.
- **Touch targets:** Text links need padding or line-height that creates 44px+ tap targets.
- **Contrast ratios:** All text must meet WCAG AA (4.5:1 for normal text, 3:1 for large text).
- **Decorative fonts:** Never use decorative or display fonts for body text.

---

## Assessment Checklist

1. **Font choices:** Do fonts match the brand personality? Are reflex fonts avoided? Are there 2-3 families maximum?
2. **Hierarchy:** Can you identify heading vs body vs caption instantly? Are there at least 3 distinct levels?
3. **Sizing/scale:** Is there a consistent modular scale? Is body text 16px+? Is the sizing strategy appropriate (fixed for apps, fluid for marketing)?
4. **Readability:** Are line lengths 65-75ch? Is line-height appropriate per context? Is contrast sufficient?
5. **Consistency:** Are same-role elements styled identically throughout? Are weights used consistently?
6. **Performance:** Are web fonts loading efficiently? Are metric-matched fallbacks defined? Is layout shift minimized?
7. **Personality:** Does the typography reflect the brand, or does it look like every other website?

---

## Typography Improvement Process

1. **Assess current state** -- identify what is weak or generic (fonts, hierarchy, sizing, readability, consistency)
2. **Select fonts** -- follow the 5-step selection procedure; replace invisible defaults if personality matters
3. **Establish type scale** -- pick a modular ratio (1.25+), define 5 sizes, choose fixed or fluid strategy
4. **Build hierarchy** -- combine size + weight + color + space for strong differentiation across levels
5. **Fix readability** -- set max-width in ch units, adjust line-height per context, ensure 16px+ body
6. **Refine details** -- tabular numbers, letter-spacing, OpenType features, semantic token names
7. **Optimize loading** -- font-display: swap, metric overrides, subset, preload critical fonts
8. **Verify** -- hierarchy visible at a glance, readable in long passages, consistent throughout, performant
