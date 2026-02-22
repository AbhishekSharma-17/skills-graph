# Intelligent Inference Engine — From Vague Input to Detailed Prompt

When users give vague or incomplete descriptions, DO NOT just ask questions. First, ANALYZE what they said, INFER everything possible, MAP it to Remotion's best capabilities, and PROPOSE a complete plan. Only ask about what truly cannot be inferred.

## Contents

- [The Inference-First Principle](#the-inference-first-principle)
- [Signal Extraction Table](#signal-extraction-table)
- [Keyword-to-Capability Mapping](#keyword-to-capability-mapping)
- [Auto-Fill Decision Engine](#auto-fill-decision-engine)
- [Context Clue Mining](#context-clue-mining)
- [Uploaded Asset Analysis](#uploaded-asset-analysis)
- [Industry Auto-Detection](#industry-auto-detection)
- [Smart Scene Generation](#smart-scene-generation)
- [The Inference Pipeline](#the-inference-pipeline)
- [Vague Prompt Examples with Full Inference](#vague-prompt-examples-with-full-inference)
- [What Remotion Does Best — Recommendation Matrix](#what-remotion-does-best--recommendation-matrix)

---

## The Inference-First Principle

**RULE: Infer first, ask second, generate third.**

When a user says something vague like "make me a cool video for my startup", you should NOT respond with 10 questions. Instead:

1. **Extract every signal** from their words (startup = SaaS/tech, cool = modern/energetic)
2. **Auto-fill smart defaults** for everything not stated (dark theme, spring animations, 30s, 16:9)
3. **Check uploaded files** — if they uploaded logos, screenshots, or data, USE THEM
4. **Propose a complete plan** with your inferences explained
5. **Ask only 2-3 critical questions** that genuinely cannot be inferred
6. **Let the user correct** your assumptions rather than starting from scratch

This approach is faster, more helpful, and shows expertise.

## Signal Extraction Table

Every word the user says is a signal. Extract aggressively:

### Product/Business Signals

| User Says | Infer |
|-----------|-------|
| "startup", "SaaS", "app", "platform", "tool" | Tech product → dark mode, blue/purple palette, Inter font, spring animations |
| "e-commerce", "store", "shop", "product" | E-commerce → clean/white bg, product-focused, price displays, "Shop Now" CTA |
| "agency", "service", "consulting" | Service business → professional, portfolio showcase, "Book a Call" CTA |
| "restaurant", "food", "cafe" | Food/hospitality → warm colors, appetizing imagery, location/hours CTA |
| "real estate", "property", "listing" | Real estate → elegant serif fonts, gold/navy, Ken Burns photo animation |
| "crypto", "web3", "blockchain", "token" | Crypto → neon colors, dark bg, futuristic font, particle effects |
| "fitness", "gym", "health", "wellness" | Health/fitness → energetic, bright accents, action-oriented CTA |
| "education", "course", "teaching", "learn" | Education → calm palette, clear typography, step-by-step structure |
| "finance", "fintech", "banking", "invest" | Finance → navy/green, conservative animations, trust signals |
| "gaming", "game", "esports" | Gaming → neon, high contrast, fast animations, impact fonts |

### Purpose Signals

| User Says | Infer |
|-----------|-------|
| "launch", "announce", "introducing", "new" | Product launch → Problem-Solution structure, reveal moment |
| "promote", "marketing", "ad", "advertise" | Marketing → energetic pace, CTA-focused, social proof |
| "explain", "how it works", "tutorial" | Explainer → educational pace, step-by-step, diagram-style |
| "social", "TikTok", "Reel", "viral" | Social media → vertical 9:16, hook-first, fast cuts, captions |
| "report", "metrics", "dashboard", "data" | Data visualization → charts, counting numbers, clean layout |
| "testimonial", "review", "case study" | Social proof → quote formatting, customer names, metric results |
| "hiring", "recruitment", "join us" | Recruitment → company culture, team photos, "Apply Now" CTA |
| "event", "conference", "webinar" | Event promo → date/location prominent, speakers, "Register" CTA |
| "onboarding", "welcome", "getting started" | Onboarding → friendly pace, step-by-step, warm colors |
| "recap", "summary", "highlights" | Compilation → multiple clips/images, fast transitions |

### Platform Signals

| User Says | Infer |
|-----------|-------|
| "TikTok", "Reel", "Short" | 9:16 (1080x1920), 15-60s, hook in 1-2s, captions mandatory |
| "YouTube" | 16:9 (1920x1080), 30s-5min, hook in 3s |
| "LinkedIn" | 16:9 (1920x1080), 30-60s, professional tone, captions |
| "Instagram feed" | 1:1 (1080x1080) or 4:5 (1080x1350), 15-60s |
| "Twitter", "X" | 16:9 (1280x720), 15-30s, punchy |
| "website", "landing page", "hero" | 16:9 (1920x1080), 10-30s loop, autoplay, no audio |
| "presentation", "pitch deck" | 16:9 (1920x1080), slide-based pacing |
| "email" | 1:1 or 16:9, 10-15s GIF or short MP4, autoplay |

### Style Signals

| User Says | Infer |
|-----------|-------|
| "cool", "modern", "sleek" | Dark bg, spring animations, gradient accents |
| "professional", "corporate", "clean" | Light or muted bg, smooth animations, serif or neutral sans |
| "fun", "playful", "energetic" | Bright colors, bouncy springs, fast pace |
| "minimal", "simple", "subtle" | Lots of whitespace, fade transitions, few elements per scene |
| "dramatic", "epic", "cinematic" | Slow pace, dark bg, heavy spring, orchestral feel |
| "techy", "futuristic" | Neon accents, dark bg, monospace font elements, particle bg |
| "luxury", "premium", "elegant" | Gold accents, serif fonts, slow smooth animations |
| "bold", "impactful", "attention-grabbing" | Large text, spring-scale pop, high contrast |

### Duration Signals

| User Says | Infer |
|-----------|-------|
| "quick", "short", "teaser", "snappy" | 10-15 seconds |
| (no duration mentioned, social platform) | 15-30 seconds |
| (no duration mentioned, YouTube/website) | 30-60 seconds |
| "detailed", "walkthrough", "comprehensive" | 60-120 seconds |
| "overview", "introduction" | 30-60 seconds |
| "ad", "commercial" | 15-30 seconds |

## Keyword-to-Capability Mapping

When the user mentions a concept, map it to the best Remotion capability:

| User Concept | Best Remotion Approach | Packages Needed |
|-------------|----------------------|-----------------|
| "animated text" | `interpolate` + `spring` on text | `remotion` |
| "transitions between scenes" | `<TransitionSeries>` with built-in transitions | `@remotion/transitions` |
| "charts", "graphs" | `interpolate` on SVG/div heights, or D3 integration | `remotion` (+ d3 optional) |
| "counting numbers" | `Math.floor(interpolate(frame, ...))` | `remotion` |
| "logo animation" | `spring()` scale/rotate on logo image | `remotion` |
| "product screenshots" | `<Img>` with shadow, rounded corners, slide entrance | `remotion` |
| "background music" | `<Html5Audio>` with volume control | `remotion` |
| "captions", "subtitles" | `@remotion/captions` with word-by-word or sentence style | `@remotion/captions` |
| "3D elements" | `<ThreeCanvas>` with React Three Fiber | `@remotion/three` |
| "Lottie animations" | `<Lottie>` component | `@remotion/lottie` |
| "GIF" | Render with GIF codec or use `@remotion/gif` for input | `@remotion/gif` |
| "particles", "noise" | `@remotion/noise` for Perlin noise backgrounds | `@remotion/noise` |
| "SVG animation" | `@remotion/paths` for path tracing | `@remotion/paths` |
| "personalized per user" | Input props with Zod schema + `calculateMetadata` | `remotion`, `zod` |
| "data from API" | `delayRender` + `continueRender` + fetch | `remotion` |
| "multiple formats" | Multiple `<Composition>` entries (landscape + vertical) | `remotion` |
| "music visualizer" | Audio visualization APIs + frequency bars | `remotion` |

## Auto-Fill Decision Engine

For EVERY prompt field, follow this decision tree:

```
Can I infer this from what the user said?
  |
  +-- YES → Use the inference (document it in your response)
  |
  +-- PARTIALLY → Use the best guess + flag it for user confirmation
  |
  +-- NO → Check if there's a smart default
       |
       +-- YES → Use the default (document it)
       |
       +-- NO → Is this REQUIRED for the prompt?
            |
            +-- YES → Ask the user (batch with other questions)
            |
            +-- NO → Omit from prompt
```

### Smart Defaults Table

| Field | Smart Default | Condition |
|-------|--------------|-----------|
| FPS | 30 | Always (unless user says "smooth" → 60) |
| Codec | h264 | Always |
| CRF | 18 | Always (high quality) |
| Font | Inter | Unless industry/style suggests otherwise |
| Heading weight | Bold 700 | Always |
| Body weight | Regular 400 | Always |
| Entrance animation | spring (snappy) | For professional; (bouncy) for playful |
| Transition | fade, 15 frames | Default; slide for sequential content |
| Background | Gradient #0f172a → #1e1b4b | For dark themes |
| Background | #ffffff | For light/clean themes |
| Text color | #f8fafc | On dark backgrounds |
| Text color | #1e293b | On light backgrounds |
| Scene count | 4-5 | For 30s video; scale proportionally |
| Hook duration | 2-3 seconds | For social; 3-5 for YouTube |
| CTA duration | 3-5 seconds | Always last scene |

## Context Clue Mining

Look beyond the explicit request for additional context:

### From the Conversation History
- Did the user mention their company/product name earlier? → Use it in the video
- Did they discuss a specific feature or problem? → Make it the video focus
- Have they mentioned a target audience? → Adjust tone and complexity

### From Uploaded Files
- **Image files (.png, .jpg, .svg):**
  - Logo? → Use as intro/outro element and corner watermark
  - Screenshots? → Use in feature showcase scenes
  - Photos? → Use as backgrounds or content elements
  - Check file names for clues: "logo-dark.png", "dashboard-screenshot.png"

- **Data files (.json, .csv):**
  - Structured data? → Suggest data-driven video with charts
  - User metrics? → Suggest personalized video

- **Document files (.md, .txt, .pdf):**
  - Brand guidelines? → Extract colors, fonts, logo usage rules
  - Marketing copy? → Extract headlines, taglines, feature descriptions
  - Script? → Use as voiceover/caption text

### From the User's Workspace
- Look at the project structure for clues about the tech stack
- Check for existing Remotion projects (package.json with remotion dependency)
- Look for `public/` folder with existing assets

## Uploaded Asset Analysis

**CRITICAL: When the user has uploaded or mentioned assets, the prompt MUST reference them.**

### Asset Detection and Integration Rules

```
IF user uploaded logo file:
  → Scene 1: Logo splash with spring-scale entrance
  → All scenes: Small logo watermark in corner (0.3 opacity)
  → Final scene: Logo centered above CTA

IF user uploaded product screenshots:
  → Create feature showcase scenes (one per screenshot)
  → Apply standard treatment: rounded corners, shadow, slide entrance
  → Reference exact file paths in prompt

IF user uploaded brand colors or mentioned hex codes:
  → Override ALL default colors with brand colors
  → Map: primary → headlines/accents, secondary → supporting elements
  → Derive background and text colors from the palette

IF user uploaded audio file:
  → Set as background music in Audio Specification section
  → Use calculateMetadata to match video duration to audio duration
  → Add audio visualization if music-focused

IF user uploaded data (JSON/CSV):
  → Create data-driven video structure
  → Add Props schema based on data structure
  → Include chart/metric animations matching the data type

IF user said "I have logos and all those things":
  → Ask: "Can you share the logo files and any brand colors/fonts?"
  → Meanwhile, design the prompt with placeholders clearly marked
  → Use: `public/logo.png (REPLACE WITH ACTUAL LOGO PATH)`
```

## Industry Auto-Detection

When you detect an industry, automatically load the right style package:

| Detected Industry | Palette | Font | Animation | Structure | CTA |
|------------------|---------|------|-----------|-----------|-----|
| **SaaS/Tech** | Modern Dark or Startup Bold | Inter | Spring snappy | Problem → Solution → Features → Proof → CTA | "Start free trial" |
| **E-commerce** | Clean Light or brand colors | Montserrat | Quick, energetic | Product → Features → Price → "Shop Now" | "Shop Now" / "Get X% off" |
| **Finance** | Corporate | Roboto/Lora | Smooth, conservative | Hook metric → Problem → Solution → Trust → CTA | "Get started" / "Learn more" |
| **Real Estate** | Warm gold/navy | Playfair Display | Slow, elegant | Hero photo → Stats → Tour → Agent → CTA | "Schedule a tour" |
| **Education** | Warm Minimal | Nunito | Gentle, clear | Question → Concept → Steps → Summary → CTA | "Start learning" |
| **Healthcare** | Teal/soft blue | Nunito/Open Sans | Gentle, reassuring | Concern → Solution → Benefits → Trust → CTA | "Book a consultation" |
| **Events** | Event brand | Montserrat | Dramatic, energetic | Name → Date/Location → Speakers → CTA | "Register now" |
| **Crypto/Web3** | Neon | Space Grotesk | Fast, dynamic | Token name → Value prop → Metrics → Community → CTA | "Join now" |
| **Creator/Personal** | Custom/bold | Varies | Personality-driven | Hook → Tips/Content → Personal → CTA | "Follow for more" |
| **Agency** | Corporate or Startup Bold | Inter | Professional | Result → Problem → Service → Proof → CTA | "Book a call" |

## Smart Scene Generation

When the user gives no scene breakdown, auto-generate one based on video type and duration:

### Auto-Scene Templates

**For 15-second videos (450 frames at 30fps):**
```
Scene 1: Hook (0-60, 2s) — Bold text or visual
Scene 2: Core message (60-300, 8s) — Main content
Scene 3: CTA (300-450, 5s) — Action + branding
```

**For 30-second videos (900 frames at 30fps):**
```
Scene 1: Hook (0-90, 3s) — Attention grabber
Scene 2: Context/Problem (90-270, 6s) — Setup
Scene 3: Solution/Features (270-600, 11s) — Core content (split into sub-scenes if needed)
Scene 4: Proof (600-720, 4s) — Social proof or data
Scene 5: CTA (720-900, 6s) — Call to action + brand
```

**For 60-second videos (1800 frames at 30fps):**
```
Scene 1: Hook (0-90, 3s)
Scene 2: Problem (90-300, 7s)
Scene 3: Solution intro (300-480, 6s)
Scene 4: Feature 1 (480-720, 8s)
Scene 5: Feature 2 (720-960, 8s)
Scene 6: Feature 3 (960-1200, 8s)
Scene 7: Social proof (1200-1440, 8s)
Scene 8: CTA (1440-1800, 12s)
```

### Auto-Text Generation

When the user hasn't provided specific text, generate contextual placeholders:

| Scene Type | Auto-Generated Text Pattern |
|-----------|---------------------------|
| Hook | "[Pain point question]?" or "Introducing [Product]" |
| Problem | "You're still [doing thing] the hard way" |
| Solution | "[Product Name] — [One-line tagline]" |
| Feature | "[Feature Name]: [One-line benefit]" |
| Social proof | "[Number]+ [users/customers/teams] trust [Product]" |
| CTA | "[Action verb] at [website]" |

**IMPORTANT:** Mark auto-generated text clearly in the prompt with `(suggested — confirm with user)` so the Remotion Dev skill and the user know these are proposals, not confirmed copy.

## The Inference Pipeline

Follow this exact sequence when processing ANY user request:

```
STEP 1: EXTRACT SIGNALS
  - Read every word for product, purpose, platform, style, duration signals
  - Check uploaded files and conversation history
  - Note what is STATED vs INFERRED vs UNKNOWN

STEP 2: MAP TO REMOTION
  - For each inferred need, identify the best Remotion capability
  - List required @remotion/ packages
  - Flag anything that pushes Remotion's limits

STEP 3: AUTO-FILL
  - Apply Smart Defaults Table for all UNKNOWN fields
  - Apply Industry Auto-Detection for style/palette/fonts
  - Generate Auto-Scene Template based on duration

STEP 4: COMPOSE DRAFT PLAN
  - Write a short summary: "Based on what you described, here's what I'm thinking:"
  - List your inferences: "Industry: SaaS (from 'startup'), Style: Modern dark, Duration: 30s"
  - Show the proposed scene structure
  - Highlight what you auto-filled vs. what you need from them

STEP 5: ASK ONLY CRITICAL GAPS (max 2-3 questions)
  - Only ask what CANNOT be inferred or defaulted
  - Typically: specific text/copy, exact assets, and any strong preferences
  - Use AskUserQuestion tool with smart options based on your inferences

STEP 6: GENERATE FULL PROMPT
  - After user confirms/adjusts, produce the complete 12-section prompt
  - Reference ALL uploaded assets by path
  - Include frame-precise timing
  - Mark any remaining assumptions with (defaulted — adjust if needed)
```

## Vague Prompt Examples with Full Inference

### Example 1: "make me a video for my saas product"

**Signal extraction:**
- "SaaS product" → Tech/SaaS industry, dark theme, spring animations
- "video" → General marketing (default to product launch structure)
- No platform → Default YouTube 16:9
- No duration → Default 30 seconds

**Auto-filled:**
- Palette: Modern Dark (#0f172a bg, #3b82f6 primary)
- Font: Inter Bold/Regular
- Animation: Spring snappy
- Structure: Hook → Reveal → Features → Proof → CTA
- FPS: 30, Codec: h264, CRF: 18

**What to ask (2 questions only):**
1. "What's your product name and main value proposition?"
2. "Do you have a logo, screenshots, or brand colors? If so, share them."

**Everything else gets smart defaults that the user can adjust.**

### Example 2: "something cool for tiktok"

**Signal extraction:**
- "TikTok" → 9:16 (1080x1920), 15-30s, hook in 1s, captions needed
- "cool" → Modern, energetic, dark bg, neon or vibrant accents
- No topic → Need to ask about content

**Auto-filled:**
- Dimensions: 1080x1920
- Duration: 15 seconds (short TikTok)
- Safe zones: top 150px, bottom 250px, right 100px
- Style: Neon palette, fast transitions (10 frames), spring bouncy
- Captions: word-by-word highlight style

**What to ask (2 questions):**
1. "What's the video about? (product promo, tips, announcement, fun fact?)"
2. "Do you have any assets to include (logo, images, etc.)?"

### Example 3: "i need a marketing video, i have logos and screenshots"

**Signal extraction:**
- "marketing video" → Product marketing, energetic pace
- "logos and screenshots" → Assets available, design around them
- No platform → Default YouTube 16:9
- No industry → Ask or infer from assets

**Auto-filled:**
- Structure: Feature showcase with screenshot scenes
- Logo: Intro splash + corner watermark + outro
- Screenshots: One per feature scene, split layout (text left, image right)
- Style: Modern Dark (default until brand colors received)

**What to ask (2 questions):**
1. "Can you share the logo and screenshot files? Also, what's the product name?"
2. "Which platform is this for? (YouTube, TikTok, LinkedIn, website?)"

### Example 4: "data visualization for quarterly metrics"

**Signal extraction:**
- "data visualization" → Data-viz type, charts, counting animations
- "quarterly metrics" → Business data, likely KPIs, professional tone
- Implies: dashboard-style, metric cards, bar/line charts

**Auto-filled:**
- Type: Data & Analytics
- Style: Corporate palette, smooth animations
- Structure: Title → KPI cards → Chart → Trend → Summary
- Elements: Counting number animations, staggered card entrances, chart draws
- Duration: 30-45 seconds

**What to ask (1-2 questions):**
1. "What specific metrics should be shown? (revenue, users, growth %, etc.)"
2. "Do you have the data as JSON/CSV, or should I use placeholder numbers?"

## What Remotion Does Best — Recommendation Matrix

When analyzing what kind of video to suggest, use this capability-fit matrix:

| Capability | Fit Score | Best Use Case | Avoid |
|-----------|:---------:|---------------|-------|
| **Text animations** | 10/10 | Any text-heavy video | — |
| **Data visualization** | 9/10 | Dashboards, reports, KPIs | Real-time streaming data |
| **Product screenshots** | 9/10 | SaaS demos, feature tours | — |
| **Logo animation** | 9/10 | Intros, outros, branding | — |
| **Scene transitions** | 9/10 | Multi-scene videos | — |
| **Personalized batch** | 9/10 | Year-in-review, per-user | — |
| **Social media vertical** | 8/10 | TikTok, Reels, Shorts | — |
| **Captions/subtitles** | 8/10 | Any video with dialogue | — |
| **Chart animations** | 8/10 | Bar, line, pie charts | Real-time updating |
| **Audio visualization** | 7/10 | Music videos, podcasts | Live audio |
| **Image slideshows** | 7/10 | Real estate, portfolio | Complex image effects |
| **3D elements** | 5/10 | Simple 3D, logos | Complex scenes (slow render) |
| **Complex motion graphics** | 4/10 | Simple versions OK | After Effects-level |
| **Video compositing** | 4/10 | Basic overlays | Complex multi-layer |
| **Live-action integration** | 3/10 | Overlays on video clips | Real-time |

**Always recommend what Remotion does at 7/10 or above. For 4-6/10, warn about limitations. Below 4/10, suggest alternatives.**
