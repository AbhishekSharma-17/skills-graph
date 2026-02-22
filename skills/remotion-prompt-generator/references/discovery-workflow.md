# Discovery Workflow — Gathering User Requirements

Before generating a prompt for the Remotion Dev skill, you MUST gather sufficient information from the user. This file defines the discovery process, follow-up questions, and requirement validation.

## Contents

- [The Discovery Framework](#the-discovery-framework)
- [Required Information Categories](#required-information-categories)
- [Follow-Up Question Bank](#follow-up-question-bank)
- [Progressive Questioning Strategy](#progressive-questioning-strategy)
- [Requirement Validation Checklist](#requirement-validation-checklist)
- [Handling Vague Requests](#handling-vague-requests)
- [User Asset Inventory](#user-asset-inventory)

---

## The Discovery Framework

Every video prompt needs answers to these 6 dimensions:

| Dimension | Question | Why It Matters |
|-----------|----------|---------------|
| **Purpose** | What is this video for? | Determines tone, length, call-to-action |
| **Audience** | Who will watch this? | Affects complexity, language, style |
| **Platform** | Where will it be published? | Determines dimensions, duration limits, safe zones |
| **Content** | What should appear in the video? | Defines scenes, text, images, data |
| **Style** | What should it look and feel like? | Colors, fonts, animation pace, mood |
| **Assets** | What files/resources does the user have? | Logos, images, audio, brand guidelines |

## Required Information Categories

### Category 1: Purpose & Goal (MUST HAVE)

| Information | Example Answers | Default If Missing |
|------------|----------------|-------------------|
| Video type | Marketing, explainer, social, data-viz | Ask — cannot default |
| Primary goal | Drive signups, explain feature, entertain | Ask — cannot default |
| Call-to-action | "Sign up now", "Learn more", website URL | No CTA (informational) |
| Key message | "Our product saves 10 hours/week" | Ask — cannot default |

### Category 2: Platform & Format (MUST HAVE)

| Information | Example Answers | Default If Missing |
|------------|----------------|-------------------|
| Target platform | YouTube, TikTok, Instagram, LinkedIn, website | YouTube (16:9, 1920x1080) |
| Aspect ratio | 16:9, 9:16, 1:1, 4:5 | 16:9 |
| Duration | 15s, 30s, 60s, 2min | 30 seconds |
| FPS | 30, 60 | 30 |

### Category 3: Content & Scenes (MUST HAVE)

| Information | Example Answers | Default If Missing |
|------------|----------------|-------------------|
| Number of scenes | 3-5 scenes, single scene | 3-4 scenes |
| Scene descriptions | "Intro with logo", "Feature showcase", "CTA" | Ask — generate suggestions |
| Text content | Headlines, taglines, bullet points | Ask or suggest based on purpose |
| Data to visualize | JSON, CSV, numbers, statistics | N/A unless data-viz type |

### Category 4: Visual Style (NICE TO HAVE)

| Information | Example Answers | Default If Missing |
|------------|----------------|-------------------|
| Color palette | Brand colors, hex codes, "dark mode" | Modern dark (#0f172a, #3b82f6, #ffffff) |
| Font preference | Sans-serif, specific fonts, "techy" | Inter (clean, professional) |
| Animation style | Bouncy, smooth, minimal, energetic | Spring animations, moderate pace |
| Mood/tone | Professional, playful, dramatic, minimal | Match purpose (marketing=energetic, edu=calm) |
| Background | Solid color, gradient, pattern, image | Dark gradient |

### Category 5: Audio (NICE TO HAVE)

| Information | Example Answers | Default If Missing |
|------------|----------------|-------------------|
| Background music | Upbeat, ambient, corporate, none | Suggest based on mood |
| Voiceover | Yes/no, text-to-speech, pre-recorded | No voiceover |
| Sound effects | Whoosh, pop, click, none | Subtle transition sounds |

### Category 6: Assets (MUST GATHER)

| Information | Example Answers | Default If Missing |
|------------|----------------|-------------------|
| Logo file | PNG/SVG uploaded or in public/ | Placeholder or text-only |
| Product screenshots | Images of the product/app | Use mockup placeholders |
| Brand guidelines | Color codes, font names, style rules | Use modern defaults |
| Custom images | Photos, illustrations, icons | Use solid colors and shapes |
| Audio files | Music tracks, voiceover recordings | No audio or suggest TTS |

## Follow-Up Question Bank

### Tier 1: Essential Questions (Always Ask)

1. **"What type of video do you want to create?"**
   - Marketing/promotional, explainer, social media content, data visualization, educational, product showcase, event promo, personalized

2. **"Where will this video be published?"**
   - YouTube, TikTok, Instagram (Feed/Reels/Stories), LinkedIn, Twitter/X, website embed, presentation, internal team

3. **"How long should the video be?"**
   - 15 seconds (social media teaser), 30 seconds (standard ad), 60 seconds (explainer), 2+ minutes (detailed walkthrough)

4. **"What is the main message or goal?"**
   - What should the viewer DO or FEEL after watching?

### Tier 2: Content Questions (Ask Based on Type)

5. **"What text/headlines should appear in the video?"**
   - Title, tagline, bullet points, call-to-action text

6. **"Do you have any assets to include?"**
   - Logos, product screenshots, images, audio files, brand colors

7. **"How many scenes/sections should the video have?"**
   - Quick scene breakdown: intro, main content, CTA

8. **"What data should be visualized?"** (for data-viz)
   - Numbers, comparisons, trends, charts

### Tier 3: Style Questions (Ask If Not Obvious)

9. **"What visual style are you going for?"**
   - Modern/minimal, bold/energetic, professional/corporate, playful/fun, dark/moody, bright/colorful

10. **"Any specific brand colors or fonts to use?"**
    - Hex codes, font names, existing brand guidelines

11. **"What kind of animations feel right?"**
    - Bouncy/spring, smooth/elegant, fast-paced, minimal/subtle

12. **"Should there be background music or voiceover?"**
    - Genre preference, mood, text-to-speech, pre-recorded

### Tier 4: Advanced Questions (Only When Relevant)

13. **"Should the video be data-driven/personalized?"**
    - Dynamic content from API, per-user customization, batch rendering

14. **"Do you need captions/subtitles?"**
    - Language, style (word-by-word highlight, traditional)

15. **"Any specific transitions between scenes?"**
    - Fade, slide, wipe, flip, zoom, custom

16. **"What resolution and frame rate?"**
    - HD (1080p), 4K, 30fps, 60fps

## Progressive Questioning Strategy

**DO NOT ask all questions at once.** Follow this progressive flow:

```
Step 1: Understand the WHAT (Tier 1 questions)
   |
   v
Step 2: Fill in CONTENT details (Tier 2 based on video type)
   |
   v
Step 3: Determine STYLE (Tier 3 if not already clear)
   |
   v
Step 4: Advanced specs (Tier 4 only if relevant)
   |
   v
Step 5: Summarize & confirm before generating prompt
```

**Batch questions when possible** — ask 2-3 related questions together, not one at a time.

**Smart defaults** — if the user says "TikTok marketing video for my SaaS", you already know:
- Platform: TikTok (9:16, 1080x1920)
- Type: Marketing
- Duration: 15-60 seconds
- Style: Likely energetic, modern
- Only need: content details, assets, specific messaging

## Requirement Validation Checklist

Before generating the prompt, verify you have:

```
[ ] Video type identified
[ ] Target platform and dimensions determined
[ ] Duration specified or defaulted
[ ] Main message / key content defined
[ ] Scene structure outlined (at least rough)
[ ] Visual style direction (colors, mood, animation feel)
[ ] Asset inventory (what the user has vs. needs placeholders)
[ ] Call-to-action defined (if applicable)
```

**Minimum viable prompt** requires at least: type + platform + duration + main message + scene outline.

## Handling Vague Requests

When the user is vague, use the **Anchor and Expand** technique:

| User Says | Anchor (What We Know) | Expand (What to Ask) |
|-----------|----------------------|---------------------|
| "Make me a video" | They want a video | What kind? What for? Where? |
| "Marketing video" | Type = marketing | Product/service? Platform? Key message? |
| "Something cool for TikTok" | Platform = TikTok, 9:16 | What content? What product/topic? Style? |
| "Promote my app" | Type = marketing, has an app | App name? Key features? Screenshots? Target audience? |
| "Data visualization" | Type = data-viz | What data? What story? Chart types? |

**When truly stuck, suggest 3 options:**
- "I could help you create: (A) a 30-second product launch video, (B) a 15-second TikTok teaser, or (C) a 60-second explainer. Which sounds closest?"

## User Asset Inventory

Always check what assets the user has available:

```
ASSET CHECKLIST:
[ ] Logo (PNG/SVG) — for intro/outro and watermarks
[ ] Product screenshots — for feature showcases
[ ] Brand colors — hex codes for consistent styling
[ ] Brand fonts — specific typeface preferences
[ ] Images/photos — for backgrounds or content
[ ] Audio files — background music or voiceover
[ ] Data files — JSON/CSV for data-driven videos
[ ] Video clips — for compositing or backgrounds
[ ] Brand guidelines doc — comprehensive style rules
[ ] Existing videos — for reference/style matching
```

**If user has uploaded files**, reference them explicitly in the prompt:
- "Use the logo at `public/logo.png`"
- "Product screenshots are at `public/screenshots/`"
- "Brand colors: primary #3b82f6, secondary #10b981"

**If user has NO assets**, the prompt should specify:
- Placeholder shapes and colors
- Text-only design approach
- Where the user can later swap in real assets
