# Asset & Styling Guide

Comprehensive guide for specifying visual assets, branding, colors, fonts, dimensions, and platform-specific requirements in Remotion video prompts.

## Contents

- [Platform-Specific Safe Zones](#platform-specific-safe-zones)
- [Logo Placement Patterns](#logo-placement-patterns)
- [Image Treatment Patterns](#image-treatment-patterns)
- [Background Patterns](#background-patterns)
- [Branding Integration](#branding-integration)
- [Text Sizing Guidelines](#text-sizing-guidelines)
- [Aspect Ratio Reference](#aspect-ratio-reference)

---

## Platform-Specific Safe Zones

Each platform has UI elements that overlay video content. Keep critical content within safe zones.

### TikTok / Instagram Reels (9:16, 1080x1920)

```
+---------------------------+
|    ← Profile pic/follow   |  Top 150px: avoid text
|                           |
|                           |
|      SAFE ZONE            |
|      (main content)       |
|                           |
|                           |
|    ← Like/comment/share   |  Right 100px: avoid
|    ← Caption area         |  Bottom 250px: avoid
+---------------------------+
```

- **Top safe margin:** 150px from top
- **Bottom safe margin:** 250px from bottom
- **Right safe margin:** 100px from right
- **Left safe margin:** 40px from left

### YouTube (16:9, 1920x1080)

```
+------------------------------------------------+
|                                                |
|            SAFE ZONE                           |
|            (nearly full canvas)                |
|                                                |
|    ← Progress bar area    Bottom 60px: avoid   |
+------------------------------------------------+
```

- **Bottom safe margin:** 60px (progress bar)
- **All other sides:** 40px margin recommended

### Instagram Feed Square (1:1, 1080x1080)

- **All sides:** 40px safe margin
- **Bottom:** 80px for caption overlay on mobile

### LinkedIn (16:9, 1920x1080)

- **Bottom:** 80px for engagement bar
- **All sides:** 60px for professional padding

## Logo Placement Patterns

| Pattern | Position | Size | When to Use |
|---------|----------|------|-------------|
| **Intro splash** | Center | 200-400px wide | First 1-3 seconds, scale-in animation |
| **Corner watermark** | Top-left or bottom-right | 60-100px wide | Persistent throughout, 0.3-0.5 opacity |
| **Outro badge** | Center | 150-300px wide | Last 2-3 seconds with fade-in |
| **Section header** | Left-aligned with text | 40-60px wide | Next to titles |

**Logo Animation Patterns:**
- `spring-scale` from 0 to 1 (bouncy entrance)
- `fade-in` over 20 frames (subtle appearance)
- `slide-from-top` with spring (playful)
- `rotate-in` 360 degrees (dynamic)

## Image Treatment Patterns

| Treatment | CSS/Style | Effect |
|-----------|-----------|--------|
| **Rounded corners** | `borderRadius: 12` | Modern, friendly |
| **Shadow** | `boxShadow: '0 20px 40px rgba(0,0,0,0.3)'` | Depth, floating |
| **Border** | `border: '2px solid #3b82f6'` | Defined, highlighted |
| **Gradient overlay** | Absolute div with gradient on top | Text readability |
| **Blur background** | `filter: 'blur(20px)'` behind main image | Depth of field |
| **Tilt/perspective** | `transform: 'perspective(800px) rotateY(5deg)'` | 3D depth |
| **Mask/clip** | `clipPath: 'circle(50%)'` | Creative shapes |

**Product Screenshot Treatment:**
```
- Container with rounded corners (borderRadius: 16)
- Subtle shadow (0 25px 50px rgba(0,0,0,0.25))
- Scale: 0.8 of scene width for breathing room
- Optional: device mockup frame (browser/phone)
- Entry: spring-scale from 0.8 to 1.0
```

## Background Patterns

### Solid Colors
```
background: '#0f172a'  // Dark blue-black (modern)
background: '#ffffff'  // Clean white (minimal)
background: '#18181b'  // Near black (dramatic)
background: '#fafaf9'  // Warm white (friendly)
```

### Gradients
```
// Dark gradient (popular for tech)
background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)'

// Warm gradient
background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)'

// Ocean gradient
background: 'linear-gradient(180deg, #0c4a6e 0%, #0369a1 50%, #0ea5e9 100%)'

// Sunset gradient
background: 'linear-gradient(135deg, #1c1917 0%, #78350f 50%, #dc2626 100%)'
```

### Animated Backgrounds
- **Floating shapes** — circles/squares with slow drift animation
- **Particle field** — small dots moving slowly (use `@remotion/noise`)
- **Gradient shift** — colors slowly transition over video duration
- **Grid pattern** — subtle dotted/lined grid with low opacity
- **Radial pulse** — expanding circles from center

## Branding Integration

### Extracting Brand Identity from User Input

| User Provides | Extract For Prompt |
|--------------|-------------------|
| Website URL | Color palette, fonts, logo style, overall aesthetic |
| Logo file | Dominant colors, brand feel, placement guidance |
| "We're a fintech startup" | Corporate-modern style, trust-building colors (blues/greens) |
| "Fun social app" | Vibrant colors, playful animations, energetic pace |
| Hex color codes | Direct palette integration |
| Competitor reference | Style matching or differentiation strategy |

### Industry-Default Styles

| Industry | Colors | Fonts | Animation Feel |
|----------|--------|-------|---------------|
| SaaS/Tech | Blue, purple, dark bg | Inter, Manrope | Spring, modern |
| Finance | Blue, green, white bg | Roboto, Lora | Smooth, professional |
| Healthcare | Teal, white, soft blue | Nunito, Open Sans | Gentle, reassuring |
| E-commerce | Brand-specific, vibrant | Montserrat, Poppins | Energetic, quick |
| Education | Warm colors, friendly | Nunito, Quicksand | Playful, clear |
| Real Estate | Gold, navy, cream | Playfair Display, Raleway | Elegant, smooth |
| Gaming | Neon, dark, high contrast | Bangers, Russo One | Fast, dynamic |
| Food/Restaurant | Warm reds, greens, earth tones | Pacifico, Lato | Appetizing, organic |

## Text Sizing Guidelines

### For 1920x1080 (16:9)

| Element | Font Size | Weight | Line Height |
|---------|-----------|--------|-------------|
| Hero title | 72-96px | Bold (700) | 1.1 |
| Scene heading | 48-64px | Bold (700) | 1.2 |
| Subheading | 36-48px | Semi-bold (600) | 1.3 |
| Body text | 24-32px | Regular (400) | 1.5 |
| Caption | 18-24px | Regular (400) | 1.4 |
| Watermark | 14-16px | Light (300) | 1.0 |

### For 1080x1920 (9:16 vertical)

| Element | Font Size | Weight |
|---------|-----------|--------|
| Hero title | 64-80px | Bold (700) |
| Heading | 44-56px | Bold (700) |
| Body text | 28-36px | Regular (400) |
| Caption | 22-28px | Regular (400) |

**Rule of thumb:** Vertical videos need ~80% the font size of landscape, but with more padding.

### For 1080x1080 (1:1 square)

| Element | Font Size | Weight |
|---------|-----------|--------|
| Hero title | 56-72px | Bold (700) |
| Heading | 40-52px | Bold (700) |
| Body text | 24-32px | Regular (400) |

## Aspect Ratio Reference

| Ratio | Resolution | Frames Math (30fps) | Use Case |
|-------|-----------|---------------------|----------|
| 16:9 | 1920x1080 | 15s=450, 30s=900, 60s=1800 | YouTube, LinkedIn, presentations |
| 9:16 | 1080x1920 | 15s=450, 30s=900, 60s=1800 | TikTok, Reels, Shorts |
| 1:1 | 1080x1080 | 15s=450, 30s=900, 60s=1800 | Instagram feed, Twitter |
| 4:5 | 1080x1350 | 15s=450, 30s=900, 60s=1800 | Instagram portrait |
| 4K | 3840x2160 | 15s=450, 30s=900, 60s=1800 | High-quality YouTube |
