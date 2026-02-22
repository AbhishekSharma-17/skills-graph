# Entertainment & Media Video Prompts

Guidance for music visualizers, podcast audiograms, event promos, and creative media content.

## Music Visualizer

### Audio Visualization Types
```
1. Bar Equalizer: 16-32 frequency bars reacting to audio
2. Waveform: Continuous wave matching audio amplitude
3. Circular Spectrum: Bars arranged in a circle
4. Particle React: Particles that move/scale with beats
5. Ring Pulse: Concentric rings expanding on beats
```

### Visualizer Prompt Template
```
Scene: Full duration (matches audio length)
Background: Dark (#0a0a0a)
Visualizer: [type] centered
Colors: Gradient across frequency (low=blue, mid=purple, high=pink)
Audio: [path to audio file]
Additional elements:
  - Track title (top, fade-in first 2s)
  - Artist name (below title)
  - Album art (corner, small)
Packages: @remotion/media, remotion (useAudioData)
```

## Podcast Audiogram

### Standard Audiogram (30-60s)
```
Layout (1080x1080 or 1080x1920):
  - Podcast artwork (top center, 200-300px)
  - Show name (below artwork)
  - Waveform visualization (center, reacting to audio)
  - Caption text (bottom, word-by-word or sentence)
  - Episode number/date (small, top corner)

Background: Brand color or gradient
Audio: Podcast clip (trimmed to highlight)
Captions: Auto-generated or provided SRT
```

## Event Promo

### Event Announcement (15-30s)
```
Scene 1 (3s): Event name — large, dramatic entrance
Scene 2 (5s): Date + Location — slide in with icons
Scene 3 (5-10s): Speaker/performer lineup — stagger entrance
Scene 4 (3s): "Get Tickets" CTA + URL
```

### Conference Speaker Card (10-15s)
```
Scene 1: Speaker photo with circle mask + name
Scene 2: Talk title + session time
Scene 3: Conference logo + register CTA
```

## Style Guidelines

| Type | Colors | Animation | Music |
|------|--------|-----------|-------|
| Music Visualizer | Neon, dark bg | Reactive to audio | The track itself |
| Podcast | Brand colors | Subtle, waveform | Podcast audio clip |
| Event Promo | Event brand | Energetic, dramatic | Upbeat/cinematic |
| Conference | Professional | Clean, organized | Corporate ambient |
