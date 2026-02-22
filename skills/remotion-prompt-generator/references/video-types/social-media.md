# Social Media Video Prompts

Guidance for generating prompts for TikTok, Instagram Reels, YouTube Shorts, LinkedIn, and other social platforms.

## Contents

- [Platform Specs Quick Reference](#platform-specs-quick-reference)
- [Social Video Structures](#social-video-structures)
- [The Hook Formula](#the-hook-formula)
- [TikTok / Reels / Shorts Template](#tiktok-reels-shorts-template)
- [LinkedIn Video Template](#linkedin-video-template)
- [Caption Integration](#caption-integration)

---

## Platform Specs Quick Reference

| Platform | Dimensions | Max Duration | FPS | Key Constraint |
|----------|-----------|-------------|-----|----------------|
| TikTok | 1080x1920 (9:16) | 10 min | 30 | Hook in 1-2s, safe zones critical |
| Instagram Reels | 1080x1920 (9:16) | 90s | 30 | Bottom 250px for captions |
| YouTube Shorts | 1080x1920 (9:16) | 60s | 30 | Title overlay at bottom |
| Instagram Feed | 1080x1080 (1:1) or 1080x1350 (4:5) | 60s | 30 | Autoplay muted by default |
| LinkedIn | 1920x1080 (16:9) | 10 min | 30 | Professional tone, captions important |
| Twitter/X | 1280x720 (16:9) | 2:20 | 30 | Quick, punchy, autoplay muted |

## Social Video Structures

### Structure 1: Hook-Content-CTA (15s)
```
Scene 1 (2s): HOOK — Bold text, pattern interrupt
Scene 2 (8-10s): Content — 2-3 key points, fast-paced
Scene 3 (3s): CTA — Follow, link in bio, share
```

### Structure 2: List/Tips Format (30s)
```
Scene 1 (2s): Hook — "3 things you didn't know about..."
Scene 2 (7s): Tip 1 — visual + text
Scene 3 (7s): Tip 2 — visual + text
Scene 4 (7s): Tip 3 — visual + text
Scene 5 (3s): CTA — "Follow for more" / "Save this"
```

### Structure 3: Before/After (15s)
```
Scene 1 (1s): "Before" label (plain, boring visual)
Scene 2 (5s): Before state
Scene 3 (1s): Quick transition (wipe/slide)
Scene 4 (5s): After state (stunning, polished visual)
Scene 5 (3s): Product/CTA
```

### Structure 4: Quote/Inspiration (10-15s)
```
Scene 1 (8-10s): Quote text animating word-by-word
Scene 2 (3s): Author attribution + brand
```

## The Hook Formula

The first 1-3 seconds determine if the viewer stays. Every social media prompt MUST define an attention-grabbing hook.

**Hook Types:**

| Type | Example | Visual Treatment |
|------|---------|-----------------|
| **Question** | "Are you still doing X manually?" | Large text, spring-scale pop |
| **Bold claim** | "This saved me 100 hours" | Impact font, number counting |
| **Contrast** | "Everyone does X, but Y works better" | Split screen, vs. visual |
| **Pattern interrupt** | Unexpected visual or color flash | Bright color burst, quick zoom |
| **Statistic** | "87% of marketers don't know this" | Large number, counting animation |
| **Challenge** | "Try this and watch what happens" | Energetic, fast text entrance |

**Hook Animation Specs:**
- Text: Spring-scale (bouncy) or quick slide-from-bottom
- Duration: Maximum 2 seconds (60 frames at 30fps)
- Font size: 64-80px on vertical, filling 40%+ of screen width
- Color: High contrast (white on dark, or bright on dark)

## TikTok / Reels / Shorts Template

**Prompt structure for vertical social video:**

```markdown
## Project Overview
- **Dimensions:** 1080x1920 (9:16)
- **Duration:** [15 | 30 | 60] seconds
- **FPS:** 30

## Safe Zones
- Top margin: 150px (profile/follow button)
- Bottom margin: 250px (caption/description area)
- Right margin: 100px (like/comment/share buttons)
- Left margin: 40px

## Scene Breakdown

### Scene 1: Hook (frames 0-60, 2s)
- Full-width bold text in safe zone center
- Spring-scale entrance (bouncy)
- Background: solid dark or brand color
- Font: 72px bold, high contrast

### Scene 2-N: Content (frames 60-[end-90])
- Each point: 5-8 seconds
- Text + visual stacked vertically
- Quick transitions (10-frame slide or cut)
- Keep text within safe zones

### Final Scene: CTA (last 90 frames, 3s)
- "Follow for more" or brand handle
- Logo (small, centered)
- Fade in over 20 frames
```

**Vertical layout pattern:**
```
+--[safe zone frame]--+
|                     |
|   [HOOK TEXT]       |   Large, centered, bold
|                     |
|   [Supporting       |   Smaller, below hook
|    visual/text]     |
|                     |
|   [CTA / handle]    |   Bottom of safe zone
|                     |
+---------------------+
```

## LinkedIn Video Template

LinkedIn requires a more professional, informative approach:

```markdown
## Project Overview
- **Dimensions:** 1920x1080 (16:9)
- **Duration:** 30-60 seconds
- **Mood:** Professional, authoritative, clean

## Style Notes
- Subtle animations (gentle springs, smooth fades)
- Corporate font (Inter, Roboto)
- Muted color palette or brand-aligned
- Always include captions (many watch muted)
- Company logo watermark in corner

## Typical Structure
Scene 1 (3s): Insight/hook — "Here's what I learned..."
Scene 2-4 (20-40s): 3 key points with supporting visuals
Scene 5 (5s): Takeaway + CTA ("Comment your thoughts")
```

## Caption Integration

**For social media, captions are near-mandatory** (most viewers watch muted).

**Caption styles to specify in prompt:**

| Style | Description | Best For |
|-------|-------------|----------|
| **Word-by-word highlight** | Each word brightens as spoken | TikTok, energetic content |
| **Traditional subtitle** | Full sentence at bottom | LinkedIn, professional |
| **Karaoke style** | Words fill with color left to right | Music-related |
| **Bouncing text** | Active word scales up slightly | Playful, fun |
| **Background box** | Semi-transparent box behind text | Readability on busy backgrounds |

**Caption prompt specification:**
```
Captions:
- Style: word-by-word highlight
- Font: Inter Bold, 36px
- Active color: #ffffff
- Inactive color: #ffffff40 (25% opacity)
- Background: rounded rect, #00000080
- Position: bottom-third of safe zone
- Timing: synced to audio/script
```
