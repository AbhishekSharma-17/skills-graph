# Animation & Effects Guide

Comprehensive reference for specifying animations, transitions, effects, motion patterns, and timing in Remotion video prompts.

## Contents

- [Animation Types Matrix](#animation-types-matrix)
- [Spring Physics Presets](#spring-physics-presets)
- [Transition Catalog](#transition-catalog)
- [Text Animation Patterns](#text-animation-patterns)
- [Scene Composition Patterns](#scene-composition-patterns)
- [Advanced Effects](#advanced-effects)
- [Timing & Pacing Guide](#timing-and-pacing-guide)
- [3D Animation Basics](#3d-animation-basics)

---

## Animation Types Matrix

### Entrance Animations

| Animation | Best For | Feel | Frames Needed |
|-----------|---------|------|---------------|
| **Spring scale** | Logos, icons, buttons | Bouncy, energetic | 20-40 |
| **Fade in** | Text, backgrounds, overlays | Subtle, elegant | 15-30 |
| **Slide from left** | Section content, lists | Directional flow | 20-30 |
| **Slide from right** | Alternating content | Directional flow | 20-30 |
| **Slide from bottom** | CTAs, secondary elements | Rising, important | 20-30 |
| **Scale up (linear)** | Backgrounds, shapes | Smooth growth | 15-25 |
| **Rotate in** | Icons, decorative elements | Dynamic, playful | 25-35 |
| **Typewriter** | Headlines, code | Technical, deliberate | Varies by text length |
| **Word by word** | Captions, subtitles | Engaging, readable | 5-8 frames per word |
| **Stagger** | Lists, grids, multi-element | Sequential, organized | 5-10 frame delay per item |
| **Blur to sharp** | Images, text reveal | Cinematic, focus | 20-30 |
| **Clip reveal** | Creative reveals | Dramatic, artistic | 20-40 |

### Exit Animations

| Animation | Best For | Frames Needed |
|-----------|---------|---------------|
| **Fade out** | Universal | 15-20 |
| **Scale down** | Logos, icons | 15-25 |
| **Slide out** | Content blocks | 15-25 |
| **Blur out** | Transitions, scene endings | 15-25 |

### Looping / Continuous

| Animation | Best For | Implementation |
|-----------|---------|----------------|
| **Pulse** | Buttons, CTAs, attention | Scale oscillation (1.0 → 1.05 → 1.0) |
| **Float** | Icons, decorative elements | TranslateY oscillation (-5px → 5px) |
| **Rotate** | Loading indicators, decorative | Continuous rotation |
| **Shimmer** | Text, premium elements | Gradient position shift |
| **Breathe** | Backgrounds, ambient | Opacity oscillation (0.8 → 1.0) |
| **Parallax** | Backgrounds, depth layers | Different speed per layer |

## Spring Physics Presets

Named presets for specifying spring feel in prompts:

| Preset Name | Mass | Damping | Stiffness | Use For |
|-------------|------|---------|-----------|---------|
| `bouncy` | 1 | 8 | 100 | Fun, playful UIs |
| `snappy` | 0.5 | 15 | 200 | Professional, quick |
| `gentle` | 1 | 20 | 80 | Elegant, smooth |
| `heavy` | 3 | 12 | 100 | Dramatic impact |
| `elastic` | 0.8 | 5 | 120 | Toy-like, cartoon |
| `crisp` | 0.3 | 20 | 300 | Sharp, precise |
| `wobbly` | 2 | 6 | 80 | Jelly-like, fun |

**In prompt, specify as:**
"Logo enters with `bouncy` spring animation (mass: 1, damping: 8, stiffness: 100)"

## Transition Catalog

### Built-in Transitions (`@remotion/transitions`)

| Transition | Visual | Best For |
|-----------|--------|----------|
| `fade()` | Crossfade opacity | Universal, elegant |
| `slide({ direction: 'from-left' })` | Push from left | Sequential flow |
| `slide({ direction: 'from-right' })` | Push from right | Alternating scenes |
| `slide({ direction: 'from-top' })` | Push from top | Vertical flow |
| `slide({ direction: 'from-bottom' })` | Push from bottom | Rising scenes |
| `wipe({ direction: 'from-left' })` | Wipe over | Energetic transitions |
| `flip()` | 3D flip | Dramatic reveals |
| `clockWipe()` | Circular clock motion | Creative, unique |
| `iris()` | Circular center reveal | Cinematic, spotlight |
| `zoom()` | Scale transition | Focus/drill-down |

### Transition Timing

| Speed | Frames (30fps) | Seconds | When to Use |
|-------|----------------|---------|-------------|
| **Quick** | 8-12 | 0.3-0.4s | Fast-paced social content |
| **Standard** | 15-20 | 0.5-0.7s | Most videos |
| **Smooth** | 25-30 | 0.8-1.0s | Elegant, cinematic |
| **Dramatic** | 40-60 | 1.3-2.0s | Slow reveals, tension |

### Transition Patterns by Video Type

| Video Type | Recommended Transitions |
|-----------|------------------------|
| Marketing/SaaS | `slide` + `fade`, energetic pace |
| Social Media | Quick `wipe` or `slide`, fast cuts |
| Data Visualization | `fade` only, let data speak |
| Educational | `slide` from consistent direction |
| Corporate | `fade` and slow `slide`, professional |
| Entertainment | Mix of `flip`, `iris`, `clockWipe` |
| Real Estate | Slow `fade` and `slide`, cinematic |

## Text Animation Patterns

### Pattern 1: Typewriter
```
Characters appear one by one, cursor optional
Speed: 2-4 frames per character
Best for: Headlines, code, technical content
```

### Pattern 2: Word-by-Word Highlight
```
All words visible but dim, each word lights up sequentially
Speed: 6-10 frames per word
Best for: Captions, subtitles, TikTok-style
```

### Pattern 3: Line-by-Line Fade
```
Each line of text fades in sequentially
Delay: 10-15 frames between lines
Best for: Bullet points, feature lists
```

### Pattern 4: Scale Pop
```
Text starts at scale 0, springs to 1.0
Spring: snappy preset
Best for: Headlines, key numbers, CTAs
```

### Pattern 5: Slide and Settle
```
Text slides in from left/bottom, decelerates to position
Easing: easeOut or spring with high damping
Best for: Professional, clean presentations
```

### Pattern 6: Split Word Stagger
```
Each word enters independently with slight delay
Delay: 3-5 frames per word, slide-from-bottom
Best for: Dramatic headlines, impactful statements
```

### Pattern 7: Counting Number
```
Number counts from 0 to target value
Duration: 30-60 frames
Best for: Statistics, metrics, KPIs
```

### Pattern 8: Gradient Text Reveal
```
Text appears as color sweeps across it left-to-right
Implementation: clipPath or mask animation
Best for: Premium, branded reveals
```

## Scene Composition Patterns

### Pattern: Hero Center
```
+----------------------------------+
|                                  |
|          [HEADLINE]              |
|         [Subheading]            |
|                                  |
|        [Product Image]           |
|                                  |
|          [CTA Button]            |
+----------------------------------+
```
Best for: Product launches, key messages

### Pattern: Split Screen
```
+----------------------------------+
|                |                  |
|   [Text/Info]  |   [Image/Demo]  |
|                |                  |
|                |                  |
+----------------------------------+
```
Best for: Feature showcases, before/after

### Pattern: Stacked Cards
```
+----------------------------------+
|   +--------+                     |
|   | Card 1 |  +--------+        |
|   +--------+  | Card 2 |        |
|               +--------+        |
|                  +--------+     |
|                  | Card 3 |     |
|                  +--------+     |
+----------------------------------+
```
Best for: Feature lists, pricing tiers

### Pattern: Full-Bleed Image
```
+----------------------------------+
|  [Full background image/video]   |
|                                  |
|     [Overlay gradient]           |
|        [Text on top]            |
|                                  |
+----------------------------------+
```
Best for: Cinematic, emotional, real estate

### Pattern: Data Dashboard
```
+----------------------------------+
|  [Title]              [Logo]     |
|  +--------+ +--------+ +------+ |
|  | Chart  | | Metric | |Metric| |
|  |        | |  #1    | | #2   | |
|  +--------+ +--------+ +------+ |
|  [Bottom annotation / source]    |
+----------------------------------+
```
Best for: Analytics, reports, KPIs

### Pattern: Vertical Story (9:16)
```
+-----------+
|  [Hook]   |  Top: attention grabber
|           |
|  [Main    |  Middle: content
|  Content] |
|           |
|  [CTA]    |  Bottom: call to action
+-----------+
```
Best for: TikTok, Reels, Shorts

## Advanced Effects

### Particle Effects (via `@remotion/noise`)
- Floating particles in background
- Confetti burst (celebration moments)
- Snow/rain effects
- Dust motes (atmospheric)

### SVG Path Animations (via `@remotion/paths`)
- Drawing/tracing SVG paths over time
- Logo reveal by path drawing
- Line art animations
- Custom shape morphing

### Light Leak Overlays (via `@remotion/light-leaks`)
- Warm color bleeds between scenes
- Cinematic sun flare effects
- Vintage film look

### Shape Animations (via `@remotion/shapes`)
- Animated geometric patterns
- Background decorative elements
- Morphing shape transitions

### Audio Visualization
- Bar equalizer (frequency visualization)
- Waveform display (audio amplitude)
- Circular spectrum analyzer
- Beat-reactive elements (scale/color pulse on beat)

## Timing and Pacing Guide

### Scene Duration Guidelines

| Content Type | Recommended Duration | Frames (30fps) |
|-------------|---------------------|----------------|
| Logo intro | 1.5-3 seconds | 45-90 |
| Text headline | 2-4 seconds | 60-120 |
| Feature point | 3-5 seconds | 90-150 |
| Image showcase | 3-5 seconds | 90-150 |
| Data/chart animation | 4-6 seconds | 120-180 |
| CTA outro | 2-4 seconds | 60-120 |
| Transition | 0.3-1 second | 10-30 |

### Pacing by Video Mood

| Mood | Scene Duration | Transition Speed | Animation Complexity |
|------|---------------|------------------|---------------------|
| Energetic/Fast | 1.5-3s per scene | Quick (8-12f) | Many, overlapping |
| Professional | 3-5s per scene | Standard (15-20f) | Clean, sequential |
| Cinematic | 4-7s per scene | Smooth (25-40f) | Minimal, dramatic |
| Educational | 4-8s per scene | Standard (15-20f) | Clear, supportive |
| Social/Viral | 1-3s per scene | Quick (8-15f) | Bold, attention-grabbing |

### The 3-Second Rule
For social media: if nothing interesting happens in the first 3 seconds (90 frames at 30fps), viewers scroll away. The first scene must be a **hook** — bold text, surprising visual, or dramatic entrance.

## 3D Animation Basics

### When to Use 3D
- Product showcase rotating models
- Logo with depth and perspective
- Particle systems for backgrounds
- Globe/map visualizations
- Abstract geometric art

### 3D Performance Warning
- **CPU-only on Lambda** — no GPU acceleration
- 3D renders are significantly slower
- Keep polygon count low for reasonable render times
- Prefer 2D alternatives when possible (transforms with perspective for faux-3D)

### Faux-3D Techniques (2D that looks 3D)
- CSS `perspective` + `rotateX/Y` (limited Remotion support)
- Layered parallax (3+ layers at different speeds)
- Shadow + slight rotation for depth
- Scale + blur for depth of field illusion
