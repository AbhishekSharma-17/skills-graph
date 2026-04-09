# Anti-Patterns Bible

The definitive list of banned patterns, AI design tells, and generic aesthetics to avoid. These patterns are the fingerprints of AI-generated work from 2024-2025. A distinctive interface should make someone ask "how was this made?" not "which AI made this?"

## Table of Contents

- [Visual Bans](#visual-bans)
- [Typography Bans](#typography-bans)
- [Layout Bans](#layout-bans)
- [Content Bans](#content-bans)
- [Component Bans](#component-bans)
- [Code Bans](#code-bans)
- [Interaction Bans](#interaction-bans)
- [The AI Slop Test](#the-ai-slop-test)

---

## Visual Bans

**No neon glows or glow effects.** Do not use default `box-shadow` glows or outer glows. Use inner borders or subtle tinted shadows instead. Neon-on-dark is the most overused AI aesthetic.

**No pure black (#000000).** Use off-black, zinc-950, charcoal, or tinted dark (#0a0a0a, #121212, or a dark navy). Pure black never appears in nature and creates harsh contrast.

**No pure white (#ffffff).** Always tint slightly. Pure white is equally unnatural.

**No oversaturated accents (>80% saturation).** Desaturate accents so they blend elegantly with neutrals. Screaming colors cheapen the design.

**No AI purple/blue gradient.** The purple-to-blue gradient aesthetic is the most common AI design fingerprint. Replace with neutral bases and a single, considered accent. This includes cyan-on-dark and neon accents on dark backgrounds.

**No gradient text.** Never use `background-clip: text` combined with a gradient background. Gradient text is decorative rather than meaningful and is a top AI design tell. Use a single solid color for text. If emphasis is needed, use weight or size.

**No generic shadows.** Tint shadows to match the background hue. Use colored shadows (dark blue shadow on a blue background) instead of pure black at low opacity. No harsh, dark drop shadows (`rgba(0,0,0,0.3)`).

**No thick-stroked generic icons.** Standard thick-stroked Lucide, FontAwesome, or Material Icons are banned. Use ultra-light, precise lines (Phosphor Light, Remix Line, Heroicons) or a custom set.

**No edge-to-edge navbars without containment.** Edge-to-edge sticky navbars glued to the top look generic. Use floating glass pill navbars, contained navbars with max-width, or alternative navigation patterns.

**No side-stripe borders on cards.** Never use `border-left` or `border-right` with width greater than 1px as a colored accent stripe on cards, list items, callouts, or alerts. This is the single most overused "design touch" in admin and dashboard UIs. Use full borders, background tints, leading numbers/icons, or no visual indicator at all.

**No glassmorphism as decoration.** Blur effects, glass cards, glow borders used decoratively rather than purposefully are AI slop. If using glassmorphism, go beyond `backdrop-filter: blur` -- add a 1px inner border and subtle inner shadow for realism.

**No sparklines as decoration.** Tiny charts that look sophisticated but convey nothing meaningful.

---

## Typography Bans

**No Inter/Roboto/Arial/Open Sans/Helvetica as default.** These are the default AI font choices. Choose deliberately. Good alternatives: Geist, Outfit, Cabinet Grotesk, Satoshi -- but do not converge on these either. Follow a deliberate font selection process for each project.

**No Syne.** The most overused "distinctive" display font and an instant AI design tell. Never use it.

**No reflex fonts from training data.** Also avoid: Fraunces, Newsreader, Lora, Crimson Pro, Playfair Display, Cormorant, DM Sans, DM Serif Display, Plus Jakarta Sans, Instrument Sans, Instrument Serif, Space Mono, Space Grotesk, IBM Plex families. These are training-data defaults that create monoculture.

**No browser-default fonts.** System fonts appearing because no font was specified is an obvious oversight.

**No oversized headlines without hierarchy.** The first heading should not scream. Control hierarchy with weight and color, not just massive scale. Sizes need contrast -- at least 1.25 ratio between steps.

**No paragraphs wider than 75 characters.** Cap body text at 65-75ch for readability.

**No monospace as lazy "developer" shorthand.** Use monospace only for actual code or data. Never as a generic "technical vibes" choice.

**No single font family for entire pages.** Pair a distinctive display font with a refined body font.

**No serif fonts on dashboards.** Serif fonts are for editorial and creative contexts. Dashboard and software UIs use exclusively sans-serif.

---

## Layout Bans

**No symmetrical 3-column card grids.** The generic "3 equal cards horizontally" feature row is the most common AI layout. Replace with a 2-column zig-zag, asymmetric grid, horizontal scroll, or masonry layout.

**No centered-everything layouts.** Left-aligned text with asymmetric layouts feels more designed. Centered layouts are the safe, boring default.

**No `h-screen` (use `min-h-[100dvh]`).** `h-screen` causes catastrophic layout jumping on mobile browsers (iOS Safari viewport bug). Always use `min-h-[100dvh]`.

**No equal-height-everything.** Allow variable heights or use masonry when content varies in length. Forced equal heights look rigid and generic.

**No cards-inside-cards nesting.** Visual noise. Flatten the hierarchy. Cards exist only when elevation communicates hierarchy.

**No uniform border-radius everywhere.** Vary the radius: tighter on inner elements, softer on containers. Uniform radius looks templated.

**No complex flexbox percentage math.** Replace `w-[calc(33%-1rem)]` with CSS Grid (`grid grid-cols-3 gap-6`) for reliable structures.

**No identical card grids.** Same-sized cards with icon + heading + text, repeated endlessly. Break the pattern with varied sizes, asymmetry, or alternative layouts.

**No hero metric layout template.** Big number, small label, supporting stats, gradient accent -- this is AI dashboard slop.

---

## Content Bans

**No generic placeholder names.** "John Doe", "Jane Smith", "Sarah Chan", "Jack Su" are banned. Use highly creative, realistic-sounding names with diversity.

**No fake round numbers.** Avoid 99.99%, 50%, $100.00, or basic phone numbers like 1234567. Use organic, messy data: 47.2%, $99.00, +1 (312) 847-1928.

**No AI copywriting cliches.** Banned words and phrases: "Elevate", "Revolutionize", "Seamless", "Cutting-edge", "Unleash", "Next-Gen", "Game-changer", "Delve", "Tapestry", "In the world of...", "Harness", "Supercharge", "Empower". Write plain, specific language with concrete verbs.

**No exclamation marks in UI copy.** Remove them from success messages, headers, and buttons. Be confident, not loud.

**No "Oops!" in error messages.** Be direct: "Connection failed. Please try again." Never cute, never condescending.

**No Lorem Ipsum in production.** Never use placeholder Latin text. Write real draft copy, even if approximate.

**No startup slop names.** "Acme Corp", "Nexus", "SmartFlow", "Synapse" are banned. Invent premium, contextual brand names.

**No identical dates on blog posts.** Randomize dates to appear real.

**No duplicate avatars.** Use unique assets for every distinct person. Never use standard SVG "egg" or Lucide user icons for avatars.

**No Title Case On Every Header.** Use sentence case instead.

**No passive voice in UI.** "We couldn't save your changes" not "Mistakes were made."

---

## Component Bans

**No pill badges everywhere.** Pill-shaped "New" and "Beta" badges on everything. Try square badges, flags, or plain text labels.

**No sun/moon toggle.** The light/dark toggle as a sun/moon switch is generic. Use a dropdown, system preference detection, or integrate it into settings.

**No 3-card testimonial rows.** 3-card carousel testimonials with dots are AI slop. Replace with a masonry wall, embedded social posts, or a single rotating quote.

**No modal overuse.** Modals for everything is lazy. Use inline editing, slide-over panels, or expandable sections for simple actions.

**No accordion FAQ sections.** Use a side-by-side list, searchable help, or inline progressive disclosure.

**No pricing tower pattern (3 columns with highlighted middle).** Highlight the recommended tier with color and emphasis, not just extra height or a "Popular" badge.

**No generic card look.** Border + shadow + white background is the default. Remove the border, or use only background color, or use only spacing. Cards should exist only when elevation communicates hierarchy.

**No rounded rectangles with generic drop shadows.** Safe, forgettable, could be any AI output.

**No footer link farm with 4 columns.** Simplify. Focus on main navigational paths and legally required links.

---

## Code Bans

**No div soup.** Use semantic HTML: `<nav>`, `<main>`, `<article>`, `<aside>`, `<section>`.

**No inline styles.** Move all styling to the project's styling system (Tailwind, CSS modules, styled-components).

**No arbitrary z-index.** Never use z-index: 9999 or random values. Establish a clean z-index scale in theme/variables. Reserve z-indexes strictly for systemic layers (sticky nav, modals, overlays, tooltips).

**No broken Unsplash links.** Do not use Unsplash. Use reliable placeholders like `https://picsum.photos/seed/{name}/800/600` or SVG UI Avatars.

**No import hallucinations.** Verify every import actually exists in `package.json` or project dependencies before using it.

**No custom cursors.** They are outdated and ruin performance/accessibility.

**No hardcoded pixel widths.** Use relative units (`%`, `rem`, `em`, `max-width`) for flexible layouts.

**No console.log in production.** Remove all debug artifacts before shipping.

**No commented-out dead code.** Clean codebase means no zombie code.

**No missing alt text.** Describe image content for screen readers. Never leave `alt=""` or `alt="image"` on meaningful images.

**No missing meta tags.** Add proper `<title>`, description, `og:image`, and social sharing meta tags.

---

## Interaction Bans

**No linear or ease-in-out transitions.** Use exponential easing (ease-out-quart/quint/expo) for natural deceleration. All motion must simulate real-world physics. Custom cubic-beziers like `cubic-bezier(0.32, 0.72, 0, 1)` are preferred.

**No bounce or elastic easing.** They feel dated and tacky. Real objects decelerate smoothly, they do not wobble. Spring physics with proper stiffness and damping is acceptable; cartoon bounce is not.

**No layout property animations.** Never animate `top`, `left`, `width`, `height`, `padding`, or `margin`. Use `transform` and `opacity` exclusively for GPU-accelerated, smooth animation. For height animations, use `grid-template-rows` transitions instead.

**No hover-dependent functionality.** Hover states are enhancements, not gates. All functionality must be accessible without hover (touch devices, keyboard navigation).

**No `window.addEventListener('scroll')`.** Use Intersection Observer or framework-specific scroll hooks. Direct scroll listeners cause continuous reflows and kill mobile performance.

**No instant state changes without interpolation.** Every state change needs a transition (200-300ms minimum). Elements should never just appear -- they should fade, translate, or scale in.

**No `will-change` everywhere.** Use it sparingly and only on elements that are actively animating. Overuse creates unnecessary GPU layers and wastes memory.

**No `backdrop-blur` on scrolling containers.** Apply blur filters only to fixed or sticky elements (navbars, overlays). Blur on scrolling content causes continuous GPU repaints and severe mobile frame drops.

**No `useState` for continuous animations.** In React, never use `useState` for magnetic hover, mouse tracking, or continuous animations. Use `useMotionValue` and `useTransform` (Framer Motion) outside the React render cycle to prevent performance collapse on mobile.

---

## Performance Anti-Patterns

**No grain/noise on scrolling containers.** Apply noise textures exclusively to fixed, `pointer-events-none` pseudo-elements. Never attach to scrolling containers -- causes continuous GPU repaints.

**No GSAP mixed with Framer Motion.** Never mix animation libraries in the same component tree. Use Framer Motion for UI interactions. Use GSAP exclusively for isolated full-page scrolltelling or canvas backgrounds, wrapped in strict useEffect cleanup.

**No infinite animations without isolation.** Any perpetual motion or infinite loop must be memoized (`React.memo`) and isolated in its own Client Component. Never trigger re-renders in the parent layout.

**No unclean animation lifecycles.** All `useEffect` animations must contain strict cleanup functions. Cancel subscriptions, clear timers, abort pending requests on unmount.

---

## The AI Slop Test

A 10-point checklist to verify your output does not look AI-generated. If you answer "yes" to 3 or more, redesign.

1. **Purple-blue gradient?** Any purple-to-blue gradients, cyan accents, or neon-on-dark color schemes?
2. **Inter or default fonts?** Using Inter, Roboto, system defaults, or any font from the reflex list?
3. **3-column card grid?** Three equal cards in a row as a feature section?
4. **Generic shadows?** Untinted black drop shadows on rounded rectangles?
5. **Gradient text?** Using `background-clip: text` with a gradient for headlines?
6. **Side-stripe borders?** Colored `border-left` wider than 1px on cards, alerts, or list items?
7. **AI copywriting?** Words like "Seamless", "Elevate", "Unleash", "Next-Gen" anywhere in the copy?
8. **Placeholder names?** "John Doe", "Jane Smith", "Acme Corp" in the UI?
9. **Missing states?** No loading, empty, or error states implemented?
10. **Static interactions?** No hover effects, no transitions, no animation on state changes?

The goal: if you showed this interface to someone and said "AI made this," they should NOT believe you immediately. A distinctive interface provokes curiosity, not recognition. Bold means distinctive. Premium means intentional. Every element should justify its existence.

---

## Quick Reference: What to Use Instead

| Banned Pattern | Replacement |
|---------------|-------------|
| Inter / Roboto / Arial | Geist, Outfit, Cabinet Grotesk, Satoshi (but vary per project) |
| Pure black #000000 | Off-black #0a0a0a, tinted dark, dark navy |
| Purple-blue gradient | Neutral base + single considered accent color |
| 3-column equal cards | 2-column zig-zag, asymmetric grid, masonry, horizontal scroll |
| `h-screen` | `min-h-[100dvh]` |
| Generic box-shadow | Tinted shadow matching background hue |
| Gradient text | Solid color text with weight/size emphasis |
| Side-stripe border | Full borders, background tints, leading icons, or no indicator |
| Lucide/Feather icons | Phosphor, Heroicons, Radix Icons, or custom set |
| `ease-in-out` transitions | `ease-out-quart` / custom cubic-bezier |
| `border-left: 4px solid` | Background tint, full border, or spatial separation |
| Sun/moon toggle | Dropdown, system preference, or settings integration |
| "John Doe" placeholder | Creative, diverse, realistic names |
| "Oops!" error messages | Direct, clear: "Connection failed. Please try again." |
| Accordion FAQ | Side-by-side list, searchable help, inline disclosure |
| Modal for everything | Inline editing, slide-over panels, expandable sections |
| `window.addEventListener('scroll')` | IntersectionObserver or framework scroll hooks |
| Animate width/height | Animate transform/opacity only |

---

## The Absolute Bans (CSS-Level)

These specific CSS patterns must be match-and-refused. If you find yourself writing any of these, stop and rewrite with a different structure entirely.

**Ban 1: Side-stripe borders**
```css
/* BANNED -- any border-left/right > 1px */
border-left: 3px solid red;
border-left: 4px solid var(--color-warning);
border-right: 5px solid oklch(...);
```
Includes hard-coded colors AND CSS variables. Never acceptable regardless of color, radius, or opacity. Do not just swap to `box-shadow inset` either.

**Ban 2: Gradient text**
```css
/* BANNED -- background-clip: text + gradient */
background: linear-gradient(135deg, purple, blue);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```
Any combination that makes text fill come from a gradient. Use a single solid color for text.
