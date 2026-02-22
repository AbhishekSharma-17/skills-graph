# Personalized & Data-Driven Video Prompts

Guidance for year-in-review videos, per-user personalized content, batch video generation, and dynamic data-driven videos.

## Personalized Video Types

### Year-in-Review (GitHub Unwrapped style)
```
Duration: 30-60s
Data: Per-user stats (contributions, repos, languages, etc.)
Scenes:
1. Personalized greeting: "Your [Year] in Review, [Name]"
2. Stat 1: Key metric with counting animation
3. Stat 2: Comparison or ranking
4. Stat 3: Fun fact or highlight
5. Summary card with all stats
6. Share CTA
```

### Customer Journey Video
```
Duration: 15-30s
Data: Customer name, signup date, usage stats, achievements
Scenes:
1. "Welcome, [Name]!" with personalized greeting
2. "You joined on [date]" — timeline visual
3. "[N] tasks completed" — counting animation
4. Milestone celebration — confetti + achievement badge
```

## Data-Driven Prompt Template

**Always include in prompt:**

```markdown
## Data Input
Props schema (Zod):
const inputSchema = z.object({
  userName: z.string(),
  userAvatar: z.string().url().optional(),
  stats: z.array(z.object({
    label: z.string(),
    value: z.number(),
    unit: z.string().optional()
  })),
  highlights: z.array(z.string()),
  theme: z.enum(['dark', 'light']).default('dark')
});

## Dynamic Fields
- All text with [brackets] is replaced per render
- Duration adjusts based on stats.length via calculateMetadata
- Colors can be theme-dependent
```

## Batch Rendering Notes

For prompts intended for batch rendering (1000s of videos):

```
Performance requirements:
- Keep animations simple (springs, fades — no 3D)
- Minimize asset loading (use shared backgrounds)
- Avoid heavy data fetching per render
- Use Lambda for parallel processing
- Include inputProps schema for automation
```

## Personalization Best Practices

| Element | Personalize? | Method |
|---------|:----------:|--------|
| Name/greeting | Yes | Input prop |
| Stats/numbers | Yes | Input prop + counting animation |
| Colors/theme | Optional | Input prop with enum |
| Avatar/photo | Optional | URL input prop |
| Duration | Auto-adjust | calculateMetadata based on data length |
| Audio | Usually shared | Same track for all |
