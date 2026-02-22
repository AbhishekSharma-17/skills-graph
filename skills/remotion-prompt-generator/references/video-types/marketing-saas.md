# Marketing & SaaS Video Prompts

Detailed guidance for generating prompts for marketing, product launch, SaaS demo, and promotional videos.

## Contents

- [Common Marketing Video Structures](#common-marketing-video-structures)
- [SaaS Product Launch Template](#saas-product-launch-template)
- [Feature Showcase Template](#feature-showcase-template)
- [Testimonial Video Template](#testimonial-video-template)
- [Key Marketing Prompt Elements](#key-marketing-prompt-elements)
- [Example Prompt: SaaS Launch](#example-prompt-saas-launch)

---

## Common Marketing Video Structures

### Structure 1: Problem-Solution (30-60s)
```
Scene 1 (3s): Hook — bold problem statement
Scene 2 (5s): Pain point — elaborate the problem
Scene 3 (5s): Solution intro — product name + tagline
Scene 4 (10s): Feature showcase — 3-4 key features
Scene 5 (5s): Social proof — stats or testimonials
Scene 6 (3s): CTA — clear action + URL/button
```

### Structure 2: Feature Highlight (15-30s)
```
Scene 1 (2s): Logo + product name entrance
Scene 2 (3-4s per feature): Feature 1 with screenshot
Scene 3 (3-4s per feature): Feature 2 with screenshot
Scene 4 (3-4s per feature): Feature 3 with screenshot
Scene 5 (3s): CTA with pricing or free trial
```

### Structure 3: Teaser/Announcement (15s)
```
Scene 1 (3s): Hook — "Introducing..." with spring animation
Scene 2 (5s): Product visual — screenshot or demo
Scene 3 (4s): Key benefit — one strong value proposition
Scene 4 (3s): CTA — "Try it free" + website
```

### Structure 4: Before/After (30s)
```
Scene 1 (3s): "Before" label with pain visualization
Scene 2 (7s): Problem scenario (cluttered, slow, difficult)
Scene 3 (3s): Transition — product logo/name
Scene 4 (7s): "After" scenario (clean, fast, easy)
Scene 5 (3s): Product shot + CTA
```

## SaaS Product Launch Template

**When the user says:** "I want a product launch video for my SaaS"

**Gather these specifics:**
1. Product name and tagline
2. Key problem it solves
3. Top 3 features to highlight
4. Target audience (developers, marketers, founders, etc.)
5. Available assets (logo, screenshots, demo videos)
6. Pricing/CTA ("Start free", "Book a demo", specific URL)
7. Brand colors and fonts
8. Desired platform (YouTube, social, website hero)

**Default structure (30 seconds):**

```
Scene 1 — Hook (0-90 frames, 3s)
  Background: Dark gradient (#0f172a → #1e1b4b)
  Text: Bold problem statement (72px, white, spring-scale entrance)
  Animation: Text springs in from scale 0

Scene 2 — Solution Reveal (90-210 frames, 4s)
  Background: Same gradient
  Logo: Spring-scale from center (bouncy preset)
  Text: Product name (96px, primary color) + tagline (36px, gray)
  Animation: Logo springs in, then text fades in 15 frames later

Scene 3 — Feature Showcase (210-480 frames, 9s)
  Layout: Split screen — text left, screenshot right
  3 features shown sequentially (3s each):
    Feature text slides from left (spring, snappy)
    Screenshot slides from right with shadow + rounded corners
  Transition between features: fade (15 frames)

Scene 4 — Social Proof (480-600 frames, 4s)
  Background: Slightly lighter shade
  Metric cards: "10,000+ users" / "4.9/5 rating" / "99.9% uptime"
  Animation: Cards stagger in from bottom (5-frame delay each)

Scene 5 — CTA (600-750 frames, 5s)
  Background: Brand primary color, full
  Text: "Start your free trial" (64px, white, spring-scale)
  URL: website.com (36px, white, fade-in after 15 frames)
  Logo: Small, bottom center (fade-in)

Total: 750 frames at 30fps = 25 seconds
```

## Feature Showcase Template

**Per-feature scene structure:**
```
[Feature Icon/Emoji] — spring-scale entrance
[Feature Title] — slide from left, bold, primary color
[Feature Description] — fade in, 1-2 lines, secondary color
[Screenshot/Demo] — slide from right with shadow
```

**Feature transition pattern:**
- Current feature fades out (15 frames)
- Next feature slides in from same direction (consistency)
- Keep icon/emoji as visual anchor

## Testimonial Video Template

**Scene structure:**
```
Scene 1: Customer quote in large text, centered
  "[Quote text here]"
  — Customer Name, Company
Scene 2: Product screenshot they referenced
Scene 3: Key metric/result
  "Saved 10 hours/week" with counting animation
```

## Key Marketing Prompt Elements

**Always include in marketing video prompts:**

| Element | Why | Default |
|---------|-----|---------|
| Brand colors (hex) | Consistency with brand | Modern dark palette |
| Logo placement | Brand recognition | Intro splash + corner watermark |
| CTA text + action | Conversion goal | "Learn more at website.com" |
| Social proof numbers | Trust building | Skip if not available |
| Platform dimensions | Correct output | 1920x1080 for YouTube |
| Hook in first 3s | Attention capture | Bold problem statement |

**Marketing-specific animation preferences:**
- Spring animations for key elements (energetic feel)
- Quick transitions (12-15 frames)
- Stagger effects for lists/features
- Counting numbers for statistics
- Pulse animation on CTA buttons

## Example Prompt: SaaS Launch

```markdown
# Video Specification: StreamFlow Pro — Product Launch

## 1. Project Overview
- **Type:** Marketing / Product Launch
- **Goal:** Drive free trial signups for StreamFlow Pro, a workflow automation tool
- **Target Platform:** YouTube (also cut for TikTok vertical)
- **Dimensions:** 1920x1080 (16:9)
- **Duration:** 30 seconds (900 frames at 30fps)
- **FPS:** 30

## 2. Visual Style
- **Color Palette:** Primary: #7c3aed, Secondary: #3b82f6, Accent: #06b6d4, Background: #0f172a, Text: #f8fafc
- **Font:** Inter (headings: bold 700, body: regular 400)
- **Mood:** Modern, energetic, trustworthy
- **Animation Style:** Spring (snappy preset for text, bouncy for logo)
- **Background:** Dark gradient from #0f172a to #1e1b4b (135deg)

## 3. Assets
- **Logo:** `public/streamflow-logo.png` (white version)
- **Screenshots:** `public/screenshots/dashboard.png`, `public/screenshots/workflow-builder.png`
- **Audio:** No background music (will be added in post)
- **Fonts:** Inter via @remotion/google-fonts

## 4. Scene Breakdown

### Scene 1: Hook (frames 0-90, 3s)
- **Background:** Gradient #0f172a → #1e1b4b
- **Text:** "Still managing workflows manually?" (72px, bold, white, centered)
- **Animation:** Text enters via spring-scale (bouncy: mass 1, damping 8, stiffness 100)
- **Transition:** fade over 15 frames

### Scene 2: Product Reveal (frames 90-210, 4s)
- **Background:** Same gradient
- **Logo:** Center, 300px wide, spring-scale entrance (snappy preset)
- **Text below logo:** "StreamFlow Pro" (96px, #7c3aed) + "Automate everything." (36px, #94a3b8)
- **Animation:** Logo springs in frame 90-120, text fades in frames 120-150
- **Transition:** slide from right over 20 frames

### Scene 3: Features (frames 210-570, 12s, 3 features x 4s each)
- **Layout:** Split — text left 45%, screenshot right 55%
- **Feature 1 (frames 210-330):**
  - Title: "Visual Workflow Builder" (48px, #7c3aed, slide-from-left spring)
  - Desc: "Drag and drop to create complex automations" (24px, #cbd5e1, fade-in)
  - Screenshot: dashboard.png with rounded corners (16px), shadow, slide-from-right
- **Feature 2 (frames 330-450):**
  - Title: "Real-Time Analytics" (same style)
  - Desc: "Track every workflow execution live"
  - Screenshot: workflow-builder.png (same treatment)
- **Feature 3 (frames 450-570):**
  - Title: "50+ Integrations" (same style)
  - Desc: "Connect Slack, GitHub, Jira, and more"
  - Visual: Grid of integration logos (stagger entrance, 3-frame delay each)

### Scene 4: Social Proof (frames 570-690, 4s)
- **Background:** #1e1b4b (slightly lighter)
- **3 metric cards** centered in a row:
  - "10,000+" (counting animation 0→10,000 over 40 frames) "Teams"
  - "4.9/5" (spring-scale) "Rating"
  - "99.9%" (counting animation) "Uptime"
- **Animation:** Cards stagger from bottom (8-frame delay each, spring snappy)

### Scene 5: CTA (frames 690-900, 7s)
- **Background:** Solid #7c3aed
- **Text:** "Start automating today" (64px, white, spring-scale bouncy)
- **URL:** "streamflow.io/try" (36px, white, fade-in at frame 730)
- **Logo:** 80px, bottom center, fade-in at frame 750
- **Button visual:** Rounded rect behind "Start Free Trial" text, pulse animation

## 5. Animation Details
- **Entrance style:** Spring (snappy for text, bouncy for logo/images)
- **Text animation:** Spring-scale for headlines, fade-in for descriptions
- **Transition timing:** 15-20 frames between scenes
- **Easing:** Spring-based (no linear animations)

## 6. Audio Specification
- **Background music:** None (added in post-production)
- **Sound effects:** None

## 7. Typography
- **Heading:** Inter, 48-96px, Bold 700, white
- **Body:** Inter, 24-36px, Regular 400, #cbd5e1
- **Accent text:** Inter, 36-48px, Semi-bold 600, #7c3aed

## 8. Technical Requirements
- **Codec:** h264
- **Quality:** CRF 18 (high quality)
- **Output:** streamflow-launch.mp4

## 12. Reference
- **Remotion packages:** remotion, @remotion/transitions, @remotion/google-fonts/Inter
```
