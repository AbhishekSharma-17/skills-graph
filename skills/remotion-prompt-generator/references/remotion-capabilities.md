# Remotion Capabilities — What It Can (and Cannot) Do

Remotion is a React-based programmatic video creation framework. Every frame is a React render. Videos are defined as compositions with width, height, fps, and durationInFrames.

## Contents

- [Core Architecture](#core-architecture)
- [Supported Output Formats](#supported-output-formats)
- [Platform Dimensions](#platform-dimensions)
- [Animation System](#animation-system)
- [Asset Support](#asset-support)
- [Audio Capabilities](#audio-capabilities)
- [Data-Driven Videos](#data-driven-videos)
- [3D Support](#3d-support)
- [Rendering Options](#rendering-options)
- [Key Limitations](#key-limitations)
- [Packages Ecosystem](#packages-ecosystem)

---

## Core Architecture

Remotion treats video as a **function of time**. Each frame is rendered as a React component snapshot.

**Building Blocks:**

| Concept | What It Does |
|---------|-------------|
| `<Composition>` | Defines a video: component + width + height + fps + durationInFrames |
| `<Sequence>` | Time-shifts child components — controls when elements appear/disappear |
| `<AbsoluteFill>` | Full-size absolute-positioned wrapper (default layout container) |
| `useCurrentFrame()` | Returns current frame number — the core animation driver |
| `useVideoConfig()` | Returns { fps, durationInFrames, width, height } |
| `interpolate()` | Maps frame ranges to value ranges (opacity, position, scale, rotation) |
| `spring()` | Physics-based animation with mass, damping, stiffness |
| `<TransitionSeries>` | Animated transitions between scenes (fade, slide, wipe, flip, etc.) |

**How Duration Works:**
- Duration is in frames, not seconds
- 30fps * 5 seconds = 150 frames
- 60fps * 10 seconds = 600 frames
- Common fps: 30 (standard), 60 (smooth), 24 (cinematic)

## Supported Output Formats

| Format | Codec | Use Case |
|--------|-------|----------|
| MP4 | H.264 | Standard video, best compatibility |
| MP4 | H.265/HEVC | Smaller file, modern devices |
| WebM | VP8/VP9 | Web embedding |
| GIF | — | Short loops, memes |
| PNG sequence | — | Post-processing in other tools |
| Still (PNG/JPEG) | — | Thumbnails, social cards |
| Transparent video | ProRes | Overlays for video editors |
| Audio only | AAC/MP3 | Faster when no video needed |

## Platform Dimensions

| Platform | Aspect Ratio | Resolution | Notes |
|----------|-------------|------------|-------|
| YouTube (landscape) | 16:9 | 1920x1080 | Standard HD |
| YouTube (4K) | 16:9 | 3840x2160 | High quality |
| TikTok / Reels / Shorts | 9:16 | 1080x1920 | Vertical format |
| Instagram Feed (square) | 1:1 | 1080x1080 | Square posts |
| Instagram Feed (portrait) | 4:5 | 1080x1350 | Tallest feed format |
| LinkedIn | 16:9 | 1920x1080 | Professional |
| Twitter/X | 16:9 | 1280x720 | Compact |
| Facebook | 16:9 or 1:1 | 1920x1080 | Feed videos |
| Presentations | 16:9 | 1920x1080 | Slide decks |

## Animation System

**`interpolate(frame, inputRange, outputRange, options)`**
- Maps frame numbers to any CSS property value
- Options: `extrapolateLeft`, `extrapolateRight` ('clamp', 'extend', 'identity')
- Supports `Easing.bezier()` for custom curves

**`spring({ fps, frame, config })`**
- Physics-based: mass (0.1-5), damping (0-100), stiffness (0-200)
- Low damping = bouncy, high damping = snappy
- Natural feel for entrances, scaling, positions

**Built-in Transitions (via `@remotion/transitions`):**
- `fade()` — opacity crossfade
- `slide()` — directional push (left, right, up, down)
- `wipe()` — reveal with sliding edge
- `flip()` — 3D card flip
- `clockWipe()` — circular clock reveal
- `iris()` — circular center reveal
- `zoom()` — scale transition
- Custom transitions possible

## Asset Support

| Asset Type | Component | Features |
|-----------|-----------|----------|
| Images | `<Img>` | Auto-wait for load, all web formats (PNG, JPG, WebP, GIF) |
| Videos | `<OffthreadVideo>` | Trim, volume, playback rate, mute |
| Audio | `<Html5Audio>` | Volume, playback rate, pitch, mute |
| Fonts | `loadFont()` | Google Fonts (400+), local fonts (woff2) |
| GIFs | `@remotion/gif` | Synchronized with timeline |
| Lottie | `@remotion/lottie` | After Effects animations |
| SVG | Native JSX | Path animations via `@remotion/paths` |
| 3D Models | `@remotion/three` | GLTF/GLB via React Three Fiber |

**Asset Loading:**
- `staticFile('path')` — loads from `public/` folder
- Direct imports — bundled with webpack
- Remote URLs — fetched during render (use `delayRender()`)

## Audio Capabilities

- Synchronized playback with video timeline
- Volume control (static or animated per frame)
- Playback rate and pitch adjustment
- Audio visualization (waveform, frequency bars)
- Multiple audio tracks layered
- Text-to-Speech integration (Azure, Google, OpenAI Whisper)
- Audio-only rendering (faster)
- Beat detection for music sync

## Data-Driven Videos

**Input Props System:**
- Pass JSON data as props to compositions
- Zod schema validation for type safety
- `calculateMetadata()` for dynamic duration/dimensions based on data
- `delayRender()` / `continueRender()` for async data fetching

**Use Cases:**
- Personalized videos (name, stats, images per user)
- Chart/graph animations from datasets
- Auto-generated reports from APIs
- Batch rendering thousands of variants

## 3D Support

**React Three Fiber (`@remotion/three`):**
- Full Three.js integration
- 3D models (GLTF/GLB)
- Lighting, materials, shadows
- Camera animations
- Particle systems
- Custom shaders (limited on Lambda — CPU only, no GPU)

## Rendering Options

| Method | Speed | Cost | Best For |
|--------|-------|------|----------|
| Local CLI | Moderate | Free | Development, small batches |
| Node.js API | Moderate | Infrastructure | Server-side automation |
| AWS Lambda | Fast (4x) | ~$0.01/render | Production at scale |
| GCP Cloud Run | Fast | Variable | GCP-native teams |
| GitHub Actions | Slow | Free tier | CI/CD pipelines |

## Key Limitations

**Cannot Do:**
- Real-time live streaming (renders to files only)
- Interactive video playback (output is static MP4)
- Visual drag-and-drop editing (code-only)
- GPU-accelerated rendering on Lambda (CPU only)
- Complex After Effects-level motion graphics

**CSS Limitations:**
- No `perspective` / `perspective-origin`
- No `-webkit-text-stroke`
- No `writing-mode`
- Limited gradient backgrounds
- No `z-index` (render order = layer order)

**Performance Notes:**
- 3D/heavy effects increase render time significantly
- Very long videos (>2hr) may timeout on Lambda
- First frames render slower (initialization)
- Concurrent rendering has diminishing returns — benchmark first

## Packages Ecosystem

| Package | Purpose |
|---------|---------|
| `remotion` | Core library |
| `@remotion/player` | Embed video player in React apps |
| `@remotion/lambda` | AWS Lambda rendering |
| `@remotion/renderer` | Node.js rendering API |
| `@remotion/transitions` | Scene transitions |
| `@remotion/three` | React Three Fiber 3D |
| `@remotion/captions` | Subtitle/caption utilities |
| `@remotion/google-fonts` | Type-safe Google Fonts |
| `@remotion/gif` | GIF support |
| `@remotion/lottie` | Lottie animation support |
| `@remotion/paths` | SVG path animations |
| `@remotion/shapes` | Shape rendering |
| `@remotion/noise` | Perlin/Simplex noise |
| `@remotion/animation-utils` | Helper functions |
| `@remotion/tailwind` | TailwindCSS support |
| `@remotion/skia` | React Native Skia graphics |

## Quick Decision Guide

| If User Wants... | Remotion Can? | Notes |
|------------------|:------------:|-------|
| Marketing video with text + images | Yes | Core strength |
| Data visualization animation | Yes | Use interpolate + charts |
| Social media vertical video | Yes | 1080x1920, 9:16 |
| Personalized video at scale | Yes | Input props + Lambda |
| 3D product showcase | Partial | Three.js, but CPU-only rendering |
| Live stream overlay | No | Renders to file only |
| Complex particle effects | Partial | Performance depends on complexity |
| Music video with visualizer | Yes | Audio visualization APIs |
| Podcast audiogram | Yes | Official template exists |
| Code animation walkthrough | Yes | Code Hike template |
