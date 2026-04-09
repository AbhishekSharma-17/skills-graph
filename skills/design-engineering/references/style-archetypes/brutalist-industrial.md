# Brutalist Industrial

> **Scope note:** Playfair Display and other traditionally banned serif fonts are permitted within this archetype for textural contrast. They must be subjected to heavy post-processing (halftone filters, 1-bit dithering) to degrade vector perfection and create textural juxtaposition against clean sans-serifs.

Interfaces that synthesize mid-century Swiss Typographic design, industrial manufacturing manuals, and retro-futuristic aerospace/military terminal interfaces. Rigid modular grids, extreme typographic scale contrast, purely utilitarian color palettes, and programmatic simulation of analog degradation. The objective is raw functionality, mechanical precision, and high data density, deliberately discarding conventional consumer UI patterns.

---

## Visual Archetypes

**Pick ONE per project and commit. Do not alternate or mix both modes within the same interface.**

### Swiss Industrial Print (Light Mode)

Derived from 1960s corporate identity systems and heavy machinery blueprints.

- High-contrast light modes with newsprint/off-white substrates
- Monolithic, heavy sans-serif typography
- Unforgiving structural grids outlined by visible dividing lines
- Aggressive, asymmetric negative space punctuated by oversized, viewport-bleeding numerals or letterforms
- Heavy use of primary red as alert/accent color

### Tactical Telemetry / CRT Terminal (Dark Mode)

Derived from classified military databases, legacy mainframes, and aerospace HUDs.

- Dark mode exclusivity
- High-density tabular data presentation
- Absolute dominance of monospaced typography
- Technical framing devices (ASCII brackets, crosshairs)
- Simulated hardware limitations (phosphor glow, scanlines, low bit-depth rendering)

---

## Typographic Architecture

Typography is the primary structural and decorative infrastructure. Imagery is secondary. The system demands extreme variance in scale, weight, and spacing.

### Macro-Typography (Structural Headers)

**Classification:** Neo-Grotesque / Heavy Sans-Serif

**Font stack:** Neue Haas Grotesk (Black), Inter (Extra Bold/Black), Archivo Black, Roboto Flex (Heavy), Monument Extended

| Parameter | Value |
|-----------|-------|
| Scale | Massive fluid type: `clamp(4rem, 10vw, 15rem)` |
| Letter-spacing | Extremely tight, often negative: `-0.03em` to `-0.06em` |
| Line-height | Highly compressed: `0.85` to `0.95` |
| Casing | Exclusively UPPERCASE for structural impact |

Glyphs should form solid architectural blocks through tight tracking.

### Micro-Typography (Data and Telemetry)

**Classification:** Monospace / Technical Sans

**Font stack:** JetBrains Mono, IBM Plex Mono, Space Mono, VT323, Courier Prime

| Parameter | Value |
|-----------|-------|
| Scale | Fixed and small: `10px` to `14px` (`0.7rem` to `0.875rem`) |
| Letter-spacing | Generous: `0.05em` to `0.1em` (simulates mechanical typewriter spacing) |
| Line-height | Standard to tight: `1.2` to `1.4` |
| Casing | Exclusively UPPERCASE for all metadata, navigation, unit IDs, coordinates |

### Textural Contrast (Artistic Disruption)

**Classification:** High-Contrast Serif

**Font stack:** Playfair Display, EB Garamond, Times New Roman

Used exceedingly sparingly. Must be subjected to heavy post-processing (halftone filters, 1-bit dithering) to degrade vector perfection and create textural juxtaposition against the clean sans-serifs.

---

## Color System

Gradients, soft drop shadows, and modern translucency are strictly prohibited. Colors simulate physical media or primitive emissive displays.

**Choose ONE substrate palette per project. Never mix light and dark substrates within the same interface.**

### Swiss Industrial Print (Light Substrate)

| Role | Hex | Notes |
|------|-----|-------|
| Background | `#F4F4F0` or `#EAE8E3` | Matte, unbleached documentation paper |
| Foreground | `#050505` to `#111111` | Carbon ink |
| Accent | `#E61919` or `#FF2A2A` | Aviation/Hazard Red -- the ONLY accent color |

Red is used for: strike-throughs, thick structural dividing lines, or vital data highlights. Nothing else.

### Tactical Telemetry (Dark Substrate)

| Role | Hex | Notes |
|------|-----|-------|
| Background | `#0A0A0A` or `#121212` | Deactivated CRT (avoid pure `#000000`) |
| Foreground | `#EAEAEA` | White phosphor, primary text color |
| Accent | `#E61919` or `#FF2A2A` | Aviation/Hazard Red, same rules as light |
| Terminal Green | `#4AF626` | Optional, single specific element only |

Terminal Green: use ONLY for one status indicator or one data readout. Never as a general text color. Omit entirely if it lacks a clear purpose.

---

## Layout and Spatial Engineering

The layout must appear mathematically engineered. Reject conventional web padding in favor of visible compartmentalization.

### The Blueprint Grid

- Strict CSS Grid architectures
- Elements anchored precisely to grid tracks and intersections -- nothing floats
- Use `display: grid; gap: 1px;` with contrasting parent/child background colors to generate razor-thin dividing lines without complex border declarations

### Visible Compartmentalization

- Extensive solid borders (`1px` or `2px solid`) to delineate zones of information
- Horizontal rules (`<hr>`) spanning full container width to segregate operational units

### Bimodal Density

Layouts oscillate between:
- **Dense zones:** Tightly packed monospace metadata clustered together
- **Vast negative space:** Calculated expanses framing macro-typography

### Geometry

- Absolute rejection of `border-radius` -- all corners exactly 90 degrees
- Mechanical rigidity is the visual language

---

## UI Components and Symbology

Standard web UI conventions are replaced with utilitarian, industrial graphic elements.

### ASCII Syntax Decoration

```
Framing:      [ DELIVERY SYSTEMS ]    < RE-IND >
Directional:  >>>    ///    \\\\
```

### Industrial Markers

Prominent integration of registration, copyright, and trademark symbols functioning as structural geometric elements rather than legal text:

```
®  ©  ™
```

### Technical Assets

- Crosshairs (`+`) at grid intersections
- Repeating vertical lines (barcodes)
- Thick horizontal warning stripes
- Randomized string data: `REV 2.6`, `UNIT / D-01`
- Simulating active mechanical processes

---

## Post-Processing Effects

Simulated analog degradation engineered into the frontend via CSS and SVG filters. Prevents the design from appearing purely digital.

### Halftone and 1-Bit Dithering

Transform continuous-tone images or large serif typography into dot-matrix patterns.

```css
/* Achieved via CSS mix-blend-mode overlays combined with SVG radial dot patterns */
mix-blend-mode: multiply;
/* Combined with an SVG radial dot pattern overlay */
```

### CRT Scanlines (Terminal Mode Only)

```css
background: repeating-linear-gradient(
  0deg,
  transparent,
  transparent 2px,
  rgba(0, 0, 0, 0.1) 2px,
  rgba(0, 0, 0, 0.1) 4px
);
```

### Mechanical Noise

Global, low-opacity SVG static/noise filter applied to the DOM root. Introduces unified physical grain across both dark and light modes.

---

## Web Engineering Directives

### Grid Determinism

Use `display: grid; gap: 1px;` with contrasting parent/child background colors. This generates mathematically perfect, razor-thin dividing lines without complex border declarations.

### Semantic Rigidity

Construct the DOM using precise semantic tags to reflect the technical nature of the telemetry:

- `<data>` for machine-readable values
- `<samp>` for sample output
- `<kbd>` for keyboard input representation
- `<output>` for computation results
- `<dl>` for definition/description lists

### Typography Clamping

Implement CSS `clamp()` functions exclusively for macro-typography. Ensures massive text scales aggressively while maintaining structural integrity across viewports.

```css
font-size: clamp(4rem, 10vw, 15rem);
```
