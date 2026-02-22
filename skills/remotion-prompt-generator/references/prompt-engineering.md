# Prompt Engineering — How to Structure Remotion Dev Prompts

This file defines the exact structure, format, and best practices for generating prompts that the Remotion Dev skill can use to produce professional video code.

## Contents

- [Prompt Output Format](#prompt-output-format)
- [The 12 Prompt Sections](#the-12-prompt-sections)
- [Scene Description Format](#scene-description-format)
- [Animation Specification Language](#animation-specification-language)
- [Color and Style Specification](#color-and-style-specification)
- [Audio Specification](#audio-specification)
- [Data-Driven Specification](#data-driven-specification)
- [Prompt Quality Checklist](#prompt-quality-checklist)

---

## Prompt Output Format

Every generated prompt MUST follow this structured format. The Remotion Dev skill expects clear, unambiguous specifications.

```markdown
# Video Specification: [Video Title]

## 1. Project Overview
- **Type:** [Marketing | Explainer | Social | Data-Viz | Education | E-commerce | Entertainment | Personalized]
- **Goal:** [One-sentence purpose]
- **Target Platform:** [YouTube | TikTok | Instagram Reels | LinkedIn | Website | etc.]
- **Dimensions:** [width]x[height] (e.g., 1920x1080)
- **Aspect Ratio:** [16:9 | 9:16 | 1:1 | 4:5]
- **Duration:** [X seconds] ([X * fps] frames at [fps] fps)
- **FPS:** [30 | 60]

## 2. Visual Style
- **Color Palette:** [Primary: #hex, Secondary: #hex, Accent: #hex, Background: #hex, Text: #hex]
- **Font:** [Font name] (weight: [regular/bold/etc.])
- **Mood:** [Professional | Playful | Dramatic | Minimal | Energetic | Calm]
- **Animation Style:** [Spring (bouncy) | Smooth (eased) | Fast-paced | Minimal]
- **Background:** [Solid #hex | Gradient from #hex to #hex | Pattern | Image path]

## 3. Assets
- **Logo:** [path or "none — use text branding"]
- **Images:** [list of paths or "generate placeholder shapes"]
- **Audio:** [path to music file or "no background music"]
- **Fonts:** [Google Font name or local path]
- **Additional:** [any other files]

## 4. Scene Breakdown

### Scene 1: [Scene Name] (frames 0-[N], [X seconds])
- **Background:** [description]
- **Elements:** [what appears]
- **Text:** "[exact text to display]"
- **Animation:** [how elements enter, animate, exit]
- **Transition to next:** [fade | slide | wipe | cut | etc.]

### Scene 2: [Scene Name] (frames [N]-[M], [X seconds])
...

### Scene N: [Scene Name] (frames [X]-[end], [X seconds])
...

## 5. Animation Details
- **Entrance style:** [spring/fade/slide with specific config]
- **Text animation:** [typewriter/fade-in/word-by-word/scale-in]
- **Transition timing:** [frames per transition]
- **Easing:** [default easing curve]

## 6. Audio Specification
- **Background music:** [path/none/suggest genre]
- **Volume:** [0-1 scale]
- **Sound effects:** [list with timing]
- **Voiceover:** [text-to-speech text or audio path]

## 7. Typography
- **Heading font:** [font, size, weight, color]
- **Body font:** [font, size, weight, color]
- **Caption font:** [font, size, weight, color]
- **Text shadow:** [yes/no, config]

## 8. Technical Requirements
- **Codec:** [h264 | h265 | vp9]
- **Quality (CRF):** [18 for high, 23 for medium, 28 for small file]
- **Rendering:** [local | lambda | server]
- **Output filename:** [suggested name]

## 9. Data Input (if data-driven)
- **Props schema:** [Zod schema or TypeScript interface]
- **Sample data:** [JSON example]
- **Dynamic fields:** [what changes per render]

## 10. Captions/Subtitles (if applicable)
- **Style:** [word-by-word highlight | traditional | TikTok-style]
- **Font:** [font, size, color, background]
- **Position:** [bottom-center, top, custom]

## 11. Responsive Notes
- **Safe zones:** [areas to avoid for platform UI overlays]
- **Text minimum size:** [for readability on mobile]

## 12. Reference
- **Inspiration:** [links or descriptions of similar videos]
- **Remotion packages needed:** [list of @remotion/ packages]
- **Special instructions:** [any additional notes]
```

## The 12 Prompt Sections

### Section Priority

| Section | Priority | When to Include |
|---------|----------|----------------|
| 1. Project Overview | REQUIRED | Always |
| 2. Visual Style | REQUIRED | Always |
| 3. Assets | REQUIRED | Always (even if "none") |
| 4. Scene Breakdown | REQUIRED | Always — this is the core |
| 5. Animation Details | REQUIRED | Always |
| 6. Audio Specification | RECOMMENDED | When audio desired |
| 7. Typography | RECOMMENDED | When specific fonts matter |
| 8. Technical Requirements | OPTIONAL | For advanced users |
| 9. Data Input | CONDITIONAL | Only for data-driven videos |
| 10. Captions | CONDITIONAL | Only when captions needed |
| 11. Responsive Notes | RECOMMENDED | For social media platforms |
| 12. Reference | OPTIONAL | When inspiration exists |

## Scene Description Format

Each scene MUST specify:

```
### Scene [N]: [Descriptive Name] (frames [start]-[end], [duration]s)

**Layout:**
- [Describe spatial arrangement of elements]

**Elements (in render order — first = back, last = front):**
1. Background: [solid color / gradient / image / video]
2. [Element name]: [position, size, content]
3. [Element name]: [position, size, content]
4. Text: "[exact text]" — [font, size, color, position]

**Animation Timeline:**
- Frame 0-[N]: [Element] [enters/appears] via [animation type]
- Frame [N]-[M]: [Element] [transforms/moves] via [animation type]
- Frame [M]-[end]: [Element] [exits/fades] via [animation type]

**Transition:** [type] over [N] frames to Scene [N+1]
```

### Scene Description Best Practices

1. **Be explicit about timing** — frame numbers, not vague "after a beat"
2. **Specify exact text** — don't say "product name", say "StreamFlow Pro"
3. **Define positions** — "centered", "top-left with 60px margin", "bottom-third"
4. **Name colors by hex** — not "blue" but "#3b82f6"
5. **Describe animations precisely** — "spring entrance from left (damping: 12)" not "slides in"

## Animation Specification Language

Use these standardized terms in prompts:

### Entrance Animations

| Term | Remotion Implementation | Visual Effect |
|------|------------------------|---------------|
| `fade-in` | `interpolate(frame, [0, 30], [0, 1])` | Opacity 0 to 1 |
| `spring-in` | `spring({ fps, frame })` | Bouncy scale from 0 to 1 |
| `slide-from-left` | `interpolate(frame, [0, 30], [-100, 0])` on translateX | Slides from off-screen left |
| `slide-from-right` | `interpolate(frame, [0, 30], [100, 0])` on translateX | Slides from off-screen right |
| `slide-from-bottom` | `interpolate(frame, [0, 30], [100, 0])` on translateY | Rises from below |
| `scale-up` | `interpolate(frame, [0, 20], [0, 1])` on scale | Grows from nothing |
| `spring-scale` | `spring()` on scale | Bouncy growth |
| `typewriter` | `text.slice(0, Math.floor(frame / 2))` | Characters appear one by one |
| `word-by-word` | Staggered opacity per word | Words appear sequentially |
| `rotate-in` | `interpolate(frame, [0, 30], [-90, 0])` on rotate | Spins into position |

### Exit Animations

| Term | Visual Effect |
|------|---------------|
| `fade-out` | Opacity 1 to 0 |
| `slide-out-left` | Moves off-screen left |
| `slide-out-right` | Moves off-screen right |
| `scale-down` | Shrinks to nothing |
| `blur-out` | Blur increases + opacity decreases |

### Continuous Animations

| Term | Visual Effect |
|------|---------------|
| `pulse` | Gentle scale oscillation (1.0 -> 1.05 -> 1.0) |
| `float` | Subtle up-down hover |
| `rotate` | Continuous rotation |
| `shimmer` | Subtle color/opacity wave |
| `parallax` | Elements move at different speeds |

### Spring Configurations

| Feel | Config | Use For |
|------|--------|---------|
| Bouncy | `{ mass: 1, damping: 8, stiffness: 100 }` | Playful, fun entrances |
| Snappy | `{ mass: 0.5, damping: 15, stiffness: 200 }` | Professional, quick pops |
| Gentle | `{ mass: 1, damping: 20, stiffness: 80 }` | Smooth, elegant motion |
| Heavy | `{ mass: 3, damping: 12, stiffness: 100 }` | Dramatic, weighted feel |

## Color and Style Specification

### Pre-Built Palettes (suggest to users who have no preference)

| Palette Name | Primary | Secondary | Accent | Background | Text |
|-------------|---------|-----------|--------|------------|------|
| **Modern Dark** | #3b82f6 | #8b5cf6 | #06b6d4 | #0f172a | #f8fafc |
| **Clean Light** | #2563eb | #16a34a | #f59e0b | #ffffff | #1e293b |
| **Startup Bold** | #7c3aed | #ec4899 | #f97316 | #18181b | #fafafa |
| **Corporate** | #1e40af | #047857 | #b45309 | #f8fafc | #1e293b |
| **Neon** | #00ff87 | #ff00ff | #00d4ff | #0a0a0a | #ffffff |
| **Warm Minimal** | #d97706 | #dc2626 | #059669 | #fffbeb | #1c1917 |
| **Ocean** | #0ea5e9 | #06b6d4 | #14b8a6 | #0c4a6e | #f0f9ff |
| **Sunset** | #f97316 | #ef4444 | #eab308 | #1c1917 | #fef3c7 |

### Font Recommendations

| Category | Font | Feel |
|----------|------|------|
| **Clean/Modern** | Inter | Professional, versatile |
| **Bold/Impact** | Montserrat | Strong headings |
| **Friendly** | Nunito | Rounded, approachable |
| **Tech** | JetBrains Mono | Code, technical |
| **Elegant** | Playfair Display | Serif, sophisticated |
| **Playful** | Bangers | Comic, energetic |
| **Corporate** | Roboto | Google-style neutral |
| **Editorial** | Lora | Magazine, editorial |

## Audio Specification

### Audio Mood Mapping

| Video Mood | Music Genre | Tempo |
|-----------|-------------|-------|
| Professional/Corporate | Ambient electronic, soft piano | 80-100 BPM |
| Energetic/Launch | Upbeat electronic, pop rock | 120-140 BPM |
| Playful/Fun | Bouncy synth, chiptune | 110-130 BPM |
| Dramatic/Epic | Orchestral, cinematic | 70-90 BPM |
| Calm/Educational | Lo-fi, acoustic guitar | 70-90 BPM |
| Tech/Futuristic | Synthwave, deep bass | 100-120 BPM |
| Minimal | Subtle ambient pads | 60-80 BPM |

## Data-Driven Specification

For videos with dynamic data, include a Zod schema:

```typescript
// Example for a metrics dashboard video
const inputSchema = z.object({
  companyName: z.string(),
  logo: z.string().url().optional(),
  metrics: z.array(z.object({
    label: z.string(),
    value: z.number(),
    change: z.number(), // percentage change
    color: z.string().optional()
  })),
  period: z.string(), // e.g., "Q4 2025"
  theme: z.enum(['dark', 'light']).default('dark')
});
```

## Prompt Quality Checklist

Before delivering the prompt, verify:

```
COMPLETENESS:
[ ] Project overview is filled with all required fields
[ ] Every scene has frame numbers, duration, and elements
[ ] All text content is specified exactly (no placeholders like "[product name]")
[ ] Colors are hex codes, not names
[ ] Fonts are specific names, not categories
[ ] Animation types use the standardized terms from this file

ACTIONABILITY:
[ ] A developer could build this without asking questions
[ ] Scene descriptions are spatially clear (positions defined)
[ ] Animation timing is frame-precise
[ ] Asset paths are specified or explicitly marked as placeholders

CONSISTENCY:
[ ] Total scene durations add up to video duration
[ ] Color palette is consistent across scenes
[ ] Animation style is consistent (all spring OR all smooth, not mixed randomly)
[ ] Typography hierarchy is clear (heading vs body vs caption)

FEASIBILITY:
[ ] Nothing specified is beyond Remotion's capabilities
[ ] 3D elements flagged as performance-heavy if present
[ ] Duration is reasonable for the platform
[ ] Resolution is standard for the platform
```
