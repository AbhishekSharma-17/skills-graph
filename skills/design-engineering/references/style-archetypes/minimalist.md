# Minimalist Editorial

> **Scope note:** Fonts recommended here (Newsreader, Playfair Display, Instrument Serif) override the general reflex-font ban when this archetype is active. The editorial serif stack is central to this aesthetic and is explicitly permitted.

Premium utilitarian minimalism and editorial UI. High-contrast warm monochrome palette, bespoke typographic hierarchies, meticulous structural macro-whitespace, bento-grid layouts, and ultra-flat component architecture with deliberate muted pastel accents. This aesthetic rejects standard SaaS design trends in favor of document-style interfaces analogous to top-tier workspace platforms.

---

## Absolute Negative Constraints

These patterns are banned within the minimalist editorial archetype:

- **Banned fonts:** Inter, Roboto, Open Sans
- **Banned icons:** Lucide, Feather, standard Heroicons (thin-line generic sets)
- **Banned shadows:** Tailwind defaults `shadow-md`, `shadow-lg`, `shadow-xl`. Shadows must be ultra-diffuse with opacity below 0.05
- **Banned backgrounds:** Primary-colored backgrounds on large elements (no bright blue/green/red hero sections)
- **Banned effects:** Gradients, neon colors, 3D glassmorphism (beyond subtle navbar blurs)
- **Banned shapes:** `rounded-full` (pill) on large containers, cards, or primary buttons
- **Banned content:** Emojis anywhere in code/markup/text. Generic placeholders ("John Doe", "Acme Corp", "Lorem Ipsum"). AI copywriting cliches ("Elevate", "Seamless", "Unleash", "Next-Gen", "Game-changer", "Delve")

---

## Typographic Architecture

The interface relies on extreme typographic contrast and premium font selection to establish an editorial feel.

### Primary Sans-Serif (Body, UI, Buttons)

Clean, geometric, or system-native fonts with character.

```
font-family: 'SF Pro Display', 'Geist Sans', 'Helvetica Neue', 'Switzer', sans-serif;
```

### Editorial Serif (Hero Headings, Quotes)

Tight tracking and compressed line-height for architectural impact.

```
font-family: 'Lyon Text', 'Newsreader', 'Playfair Display', 'Instrument Serif', serif;
letter-spacing: -0.02em to -0.04em;
line-height: 1.1;
```

### Monospace (Code, Keystrokes, Metadata)

```
font-family: 'Geist Mono', 'SF Mono', 'JetBrains Mono', monospace;
```

### Text Color Rules

- Body text: never absolute black (`#000000`). Use off-black/charcoal `#111111` or `#2F3437`
- Body line-height: `1.6` for legibility
- Secondary text: muted gray `#787774`

---

## Color Palette

Color is a scarce resource, used only for semantic meaning or subtle accents.

### Base Surfaces

| Role | Hex | Notes |
|------|-----|-------|
| Canvas / Background | `#FFFFFF` or `#F7F6F3` | Pure white or warm bone/off-white |
| Alternate canvas | `#FBFBFA` | Slightly warmer variant |
| Card surface | `#FFFFFF` or `#F9F9F8` | Minimal contrast with canvas |
| Borders / Dividers | `#EAEAEA` or `rgba(0,0,0,0.06)` | Ultra-light gray, structural only |

### Accent Pastels

Exclusively highly desaturated, washed-out pastels for tags, inline code backgrounds, or subtle icon backgrounds.

| Color | Background | Text |
|-------|-----------|------|
| Pale Red | `#FDEBEC` | `#9F2F2D` |
| Pale Blue | `#E1F3FE` | `#1F6C9F` |
| Pale Green | `#EDF3EC` | `#346538` |
| Pale Yellow | `#FBF3DB` | `#956400` |

---

## Component Specifications

### Bento Box Feature Grids

- Asymmetrical CSS Grid layouts
- Cards: exactly `border: 1px solid #EAEAEA`
- Border-radius: crisp `8px` or `12px` maximum
- Internal padding: generous `24px` to `40px`

### Primary Call-To-Action Buttons

- Background: `#111111`, text: `#FFFFFF`
- Border-radius: `4px` to `6px`, no box-shadow
- Hover: subtle color shift to `#333333` or micro-scale `transform: scale(0.98)`

### Tags and Status Badges

- Pill-shaped (`border-radius: 9999px`), very small typography (`text-xs`)
- Uppercase with wide tracking (`letter-spacing: 0.05em`)
- Background: muted pastels from the accent palette above

### Accordions (FAQ)

- Strip all container boxes
- Separate items only with `border-bottom: 1px solid #EAEAEA`
- Clean, sharp `+` / `-` icon for toggle state

### Keystroke Micro-UIs

Render shortcuts as physical keys using `<kbd>` tags:

```css
border: 1px solid #EAEAEA;
border-radius: 4px;
background: #F7F6F3;
font-family: monospace stack;
```

### Faux-OS Window Chrome

When mocking up software, wrap in a minimalist container with a white top bar containing three small, light gray circles (macOS window controls).

---

## Iconography and Imagery

### Icons

- Use Phosphor Icons (Bold or Fill weights) or Radix UI Icons
- Technical, slightly thicker-stroke aesthetic
- Standardize stroke width across all icons

### Illustrations

Monochromatic, rough continuous-line ink sketches on white background, featuring a single offset geometric shape filled with a muted pastel color.

### Photography

- High-quality, desaturated images with warm tone
- Apply subtle overlays (`opacity: 0.04` warm grain) to blend into monochrome palette
- Never use oversaturated stock photos
- Placeholder: `https://picsum.photos/seed/{context}/1200/800`

### Section Backgrounds

Sections must not feel empty and flat. Add depth without breaking the clean aesthetic:

- Subtle full-width background imagery at very low opacity
- Soft radial light spots (`radial-gradient` with warm tones at `opacity: 0.03`)
- Minimal geometric line patterns

---

## Motion and Micro-Animations

Motion should feel invisible -- present but never distracting. Quiet sophistication, not spectacle.

### Scroll Entry

Elements fade in gently as they enter the viewport:

```css
transform: translateY(12px);
opacity: 0;
/* resolving over 600ms */
transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
```

Use `IntersectionObserver`, never `window.addEventListener('scroll')`.

### Hover States

Cards lift with ultra-subtle shadow shift:

```css
/* from */ box-shadow: 0 0 0 rgba(0,0,0,0);
/* to */   box-shadow: 0 2px 8px rgba(0,0,0,0.04);
transition-duration: 200ms;
```

Buttons: `scale(0.98)` on `:active`.

### Staggered Reveals

Lists and grid items enter with cascade delay:

```css
animation-delay: calc(var(--index) * 80ms);
```

Never mount everything at once.

### Background Ambient Motion (Optional)

- Single, very slow-moving radial gradient blob
- `animation-duration: 20s+`, `opacity: 0.02-0.04`
- Applied to `position: fixed; pointer-events: none` layer
- Never on scrolling containers

### Performance Rules

- Animate exclusively via `transform` and `opacity`
- No layout-triggering properties (`top`, `left`, `width`, `height`)
- Use `will-change: transform` sparingly, only on actively animating elements

---

## Execution Protocol

Follow this sequence when building minimalist editorial interfaces:

1. **Macro-whitespace first.** Use massive vertical padding between sections (`py-24` or `py-32` in Tailwind)
2. **Constrain content width.** Main typography content to `max-w-4xl` or `max-w-5xl`
3. **Apply typographic hierarchy.** Set custom font stacks and monochromatic color variables immediately
4. **Enforce border rules.** Every card, divider, and border must adhere to `1px solid #EAEAEA`
5. **Add scroll-entry animations.** Apply to all major content blocks
6. **Add visual depth.** Use imagery, ambient gradients, or subtle textures -- no empty flat backgrounds
7. **Validate component patterns.** Check all cards, buttons, tags against specs above
8. **Production code.** Output must reflect the editorial aesthetic natively without requiring manual adjustments
