# Color System

## Table of Contents

- [OKLCH Over HSL](#oklch-over-hsl)
- [Tinted Neutrals](#tinted-neutrals)
- [60-30-10 Rule](#60-30-10-rule)
- [Palette Structure](#palette-structure)
- [Strategic Color Addition](#strategic-color-addition)
- [Color Application](#color-application)
- [Contrast and Accessibility](#contrast-and-accessibility)
- [Dark Mode](#dark-mode)
- [Alpha Smell Detection](#alpha-smell-detection)
- [Assessment Checklist](#assessment-checklist)

---

## OKLCH Over HSL

**Stop using HSL.** Use OKLCH (or LCH) instead. It is perceptually uniform, meaning equal steps in lightness *look* equal -- unlike HSL where 50% lightness in yellow looks bright while 50% in blue looks dark.

### OKLCH Function

`oklch(lightness chroma hue)` where:
- **Lightness:** 0-100%
- **Chroma:** roughly 0-0.4 (saturation/intensity)
- **Hue:** 0-360 degrees

### Building Color Variants

To build a primary color and its lighter/darker variants, hold the chroma+hue roughly constant and vary the lightness. **Reduce chroma as you approach white or black** -- high chroma at extreme lightness looks garish.

### Hue Selection

The hue you pick is a brand decision and should not come from a default. Do not reach for blue (hue 250) or warm orange (hue 60) by reflex -- those are the dominant AI-design defaults, not the right answer for any specific brand.

---

## Tinted Neutrals

**Pure gray is dead.** A neutral with zero chroma feels lifeless next to a colored brand. Add a tiny chroma value (0.005-0.015) to all your neutrals, hued toward your brand color. The chroma is small enough not to read as "tinted" consciously, but it creates subconscious cohesion between brand color and UI surfaces.

### Rules for Tinting

- The hue you tint toward should come from THIS project's brand, not from a "warm = friendly, cool = tech" formula
- If your brand color is teal, your neutrals lean toward teal. If amber, they lean toward amber.
- The point is cohesion with the SPECIFIC brand, not a stock palette
- **Avoid** always tinting toward warm orange or always tinting toward cool blue -- those are the two laziest defaults

### Examples

```css
/* Instead of pure gray backgrounds */
background: #f5f5f5;                    /* Dead, lifeless */

/* Use tinted neutrals */
background: oklch(97% 0.01 60);         /* Warm tint */
background: oklch(97% 0.01 250);        /* Cool tint */
```

Never use pure black (`#000`) or pure white (`#fff`) for large areas. Even a chroma of 0.005-0.01 is enough to feel natural without being obviously tinted.

---

## 60-30-10 Rule

This rule is about **visual weight**, not pixel count:

| Proportion | Role | What Goes Here |
|------------|------|----------------|
| **60%** | Dominant | Neutral backgrounds, white space, base surfaces |
| **30%** | Secondary | Text, borders, inactive states, supporting colors |
| **10%** | Accent | CTAs, highlights, focus states, key moments |

### Common Mistake

Using the accent color everywhere because it is "the brand color." Accent colors work *because* they are rare. Overuse kills their power.

### Application

- **Dominant color** (60%): Primary brand color or most used accent
- **Secondary color** (30%): Supporting color for variety
- **Accent color** (10%): High contrast for key moments
- **Neutrals** (remaining): Gray/black/white tinted for structure

---

## Palette Structure

A complete system needs defined roles:

| Role | Purpose | Guidance |
|------|---------|----------|
| **Canvas** | Page background, base layer | Lightest neutral (tinted toward brand) |
| **Surface** | Cards, modals, overlays | 2-3 elevation levels, slightly lighter/darker than canvas |
| **Foreground** | Text, icons | High contrast against surfaces, 2-3 shades (primary, secondary, muted) |
| **Accent/Primary** | Brand, CTAs, key actions | 1 color with 3-5 shades |
| **Semantic: Success** | Positive states, confirmations | Green tones (emerald, forest, mint) |
| **Semantic: Warning** | Caution, attention needed | Orange/amber tones |
| **Semantic: Error** | Failures, destructive actions | Red/pink tones (rose, crimson, coral) |
| **Semantic: Info** | Informational, neutral alerts | Blue tones (sky, ocean, indigo) |

**Skip secondary/tertiary accent colors unless you need them.** Most apps work fine with one accent color. Adding more creates decision fatigue and visual noise. Choose 2-4 colors max beyond neutrals.

### Token Hierarchy

Use two layers: **primitive tokens** (`--blue-500`) and **semantic tokens** (`--color-primary: var(--blue-500)`). For dark mode, only redefine the semantic layer -- primitives stay the same.

---

## Strategic Color Addition

When an interface is too monochromatic, gray, or lacking visual warmth, follow this process:

### 1. Assess the Opportunity

- **Color absence:** Pure grayscale? Limited neutrals? One timid accent?
- **Missed opportunities:** Where could color add meaning, hierarchy, or delight?
- **Context:** What is appropriate for this domain and audience?
- **Brand:** Are there existing brand colors to build from?

### 2. Identify Where Color Adds Value

- **Semantic meaning:** Success, error, warning, info states
- **Hierarchy:** Drawing attention to important elements
- **Categorization:** Different sections, types, or states
- **Emotional tone:** Warmth, energy, trust, creativity
- **Wayfinding:** Helping users navigate and understand structure
- **Delight:** Moments of visual interest and personality

### 3. Create a Purposeful Strategy

- Choose 2-4 colors beyond neutrals
- Assign a dominant color (60% of colored elements)
- Define accent colors for contrast and highlights (30% and 10%)
- Map where each color appears and why

**More color does not equal better.** Strategic color beats rainbow vomit every time. Every color should have a purpose.

---

## Color Application

### Semantic Color

- **Status badges:** Colored backgrounds or borders for states (active, pending, completed)
- **Progress indicators:** Colored bars, rings, or charts showing completion or health
- **State indicators:** Green for success, red for error, orange for warning, blue for info, gray for inactive

### Accent Color

- **Primary actions:** Color the most important buttons and CTAs
- **Links:** Add color to clickable text (maintain accessibility)
- **Icons:** Colorize key icons for recognition and personality
- **Headers/titles:** Add color to section headers or key labels
- **Hover states:** Introduce color on interaction

### Backgrounds and Surfaces

- **Tinted backgrounds:** Replace pure gray with warm or cool neutrals
- **Colored sections:** Subtle background colors to separate areas
- **Gradient backgrounds:** Depth with subtle, intentional gradients (not generic purple-blue)
- **Cards and surfaces:** Tint slightly for warmth

### Data Visualization

- Use color to encode categories or values in charts and graphs
- Color intensity shows density or importance in heatmaps
- Color coding for different datasets or timeframes in comparisons

### Borders and Accents

- **Accent borders:** Colored left/top borders on cards or sections
- **Underlines:** Color underlines for emphasis or active states
- **Dividers:** Subtle colored dividers instead of gray lines
- **Focus rings:** Colored focus indicators matching brand

### Typography Color

- **Colored headings:** Brand colors for section headings (maintain contrast)
- **Highlight text:** Color for emphasis or categories
- **Labels and tags:** Small colored labels for metadata

### Decorative Elements

- Illustrations, geometric shapes in brand colors as backgrounds
- Gradient overlays or mesh backgrounds
- Soft colored blobs for visual interest

---

## Contrast and Accessibility

### WCAG Requirements

| Content Type | AA Minimum | AAA Target |
|--------------|------------|------------|
| Body text | 4.5:1 | 7:1 |
| Large text (18px+ or 14px bold) | 3:1 | 4.5:1 |
| UI components, icons | 3:1 | 4.5:1 |
| Non-essential decorations | None | None |

**Gotcha:** Placeholder text still needs 4.5:1. That light gray placeholder you see everywhere usually fails WCAG.

### Dangerous Color Combinations

- Light gray text on white (the number one accessibility fail)
- **Gray text on any colored background** -- gray looks washed out and dead on color. Use a darker shade of the background color, or transparency
- Red text on green background (or vice versa) -- 8% of men cannot distinguish these
- Blue text on red background (vibrates visually)
- Yellow text on white (almost always fails)
- Thin light text on images (unpredictable contrast)

### Testing

Do not trust your eyes. Use tools:
- WebAIM Contrast Checker
- Browser DevTools: Rendering > Emulate vision deficiencies
- Test for color blindness: verify red/green combinations work for all users
- Never rely on color alone -- use icons, labels, or patterns alongside color

---

## Dark Mode

### Dark Mode Is Not Inverted Light Mode

You cannot just swap colors. Dark mode requires different design decisions:

| Light Mode | Dark Mode |
|------------|-----------|
| Shadows for depth | Lighter surfaces for depth (no shadows) |
| Dark text on light | Light text on dark (reduce font weight) |
| Vibrant accents | Desaturate accents slightly |
| White backgrounds | Never pure black -- use dark gray (oklch 12-18%) |

### Implementation Rules

- **Invert lightness, not hue.** Keep the same brand hue and chroma; only vary lightness.
- **Reduce saturation slightly.** Vibrant colors on dark backgrounds appear more intense.
- **Surface depth from lightness, not shadow.** Build a 3-step surface scale where higher elevations are lighter (e.g., 15% / 20% / 25% lightness).
- **Reduce body text weight.** Light text on dark reads as heavier than dark text on light. Use 350 instead of 400.
- **Use the SAME hue as your brand color** for surface tinting -- do not default to blue.
- **Test contrast.** All text must still meet WCAG requirements in dark mode.

### Token Strategy

Only redefine the semantic token layer for dark mode. Primitive tokens (`--blue-500`) stay the same; semantic tokens (`--color-primary`) get remapped.

---

## Alpha Smell Detection

Heavy use of transparency (`rgba`, `hsla`, alpha channels) usually means an incomplete palette.

### Problems with Alpha

- Creates unpredictable contrast when layered on different backgrounds
- Performance overhead from compositing
- Inconsistency across different surface colors

### When Alpha Is Acceptable

- Focus rings and interactive states where see-through is needed
- Overlays and backdrops by design (modal backdrop, image overlays)
- True glass/blur effects

### The Fix

Define explicit overlay colors for each context instead of relying on transparency. If you find yourself using `rgba(0, 0, 0, 0.1)` repeatedly, that is a missing token in your palette.

---

## Assessment Checklist

1. **Color opportunity:** Has the interface leveraged color for meaning, hierarchy, and personality? Or is it unnecessarily monochromatic?
2. **Balance:** Does the 60-30-10 rule hold? Is the accent color rare enough to have impact?
3. **Hierarchy:** Does color guide attention appropriately? Are primary actions visually prominent?
4. **Accessibility:** Do all text/background combinations meet WCAG AA (4.5:1)? Do UI components meet 3:1? Has color blindness been tested?
5. **Cohesion:** Are neutrals tinted toward the brand? Is the palette consistent throughout? Do same colors mean the same things everywhere?
6. **Dark mode:** If applicable, does dark mode invert lightness (not hue)? Are accents desaturated? Is contrast verified?
7. **No pure grays:** Are all neutrals tinted? Is pure black avoided for large areas?
8. **Alpha usage:** Are transparent colors used sparingly and intentionally, not masking an incomplete palette?
