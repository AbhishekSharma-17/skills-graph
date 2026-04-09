# Motion & Delight

## Table of Contents

- [Motion Principles](#motion-principles)
- [Duration Rules](#duration-rules)
- [Easing](#easing)
- [Transform and Opacity Only](#transform-and-opacity-only)
- [Staggered Animations](#staggered-animations)
- [Reduced Motion](#reduced-motion)
- [Perceived Performance](#perceived-performance)
- [Animation Categories](#animation-categories)
- [Delight Principles](#delight-principles)
- [Delight Opportunities](#delight-opportunities)
- [Delight Techniques](#delight-techniques)
- [Overdrive Toolkit](#overdrive-toolkit)
- [Animation Assessment](#animation-assessment)
- [Performance](#performance)

---

## Motion Principles

Motion in interfaces serves three purposes. If an animation does not fulfill at least one, remove it.

1. **Purposeful, not decorative.** Every animation needs a reason -- feedback, orientation, or hierarchy. Animation that exists only to look impressive draws attention to itself rather than the content.

2. **Amplifies hierarchy.** Motion directs attention. The most important element should animate first or most prominently. Stagger reveals so the eye follows a logical reading order.

3. **Maintains context.** Transitions preserve spatial relationships. When a list item expands into a detail view, the animation should communicate where the content came from and where it goes back to.

**Exit animations are faster than entrances** -- use approximately 75% of enter duration. Users want to leave a state quickly but arrive gradually.

---

## Duration Rules

Timing matters more than easing. These durations feel right for most UI:

| Duration | Category | Examples |
|----------|----------|----------|
| **100-150ms** | Micro-feedback | Button press, toggle, color change, checkbox |
| **200-300ms** | State changes | Menu open, tooltip, hover states, tab switch |
| **300-500ms** | Layout changes | Accordion, modal, drawer, expand/collapse |
| **500-800ms** | Complex/page | Page load, hero reveals, entrance sequences |

### Guidelines

- Feedback durations over 500ms feel laggy -- keep micro-interactions fast
- State changes in the 200-300ms range feel responsive without being jarring
- Entrance animations can be longer because users are arriving, not waiting
- Exit animations should be 75% of entrance duration

---

## Easing

**Do not use the CSS `ease` default.** It is a compromise that is rarely optimal.

### Recommended Curves

```css
/* Entrances - elements appearing (ease-out family) */
--ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);    /* Smooth, refined - recommended default */
--ease-out-quint: cubic-bezier(0.22, 1, 0.36, 1);   /* Slightly snappier */
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);     /* Confident, decisive */

/* Exits - elements leaving (ease-in family) */
--ease-in: cubic-bezier(0.7, 0, 0.84, 0);

/* State toggles - there and back (ease-in-out) */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
```

### Why Exponential Curves

Exponential easing (quart, quint, expo) feels natural because it mimics real physics -- friction and deceleration. Objects in the real world do not move with linear or generic easing.

### Spring Physics for Premium Feel

Spring physics (mass, tension, damping) produce motion that feels physical and alive. Instead of a fixed duration and bezier curve, springs settle naturally. Use for:
- Drag-and-drop repositioning
- Toggle switches
- Modal entrances
- Any interaction where "weight" and "bounce" enhance the feel

Libraries: motion (formerly Framer Motion), React Spring, GSAP, Popmotion, or a custom spring solver.

### Banned Easing Curves

**Avoid bounce and elastic curves.** They were trendy in 2015 but now feel tacky and amateurish. Real objects do not bounce when they stop -- they decelerate smoothly. Overshoot effects draw attention to the animation itself rather than the content.

```css
/* DO NOT USE */
/* bounce: cubic-bezier(0.34, 1.56, 0.64, 1); */
/* elastic: cubic-bezier(0.68, -0.6, 0.32, 1.6); */
```

---

## Transform and Opacity Only

**Never animate layout properties:** `width`, `height`, `top`, `left`, `margin`, `padding`. These cause layout recalculation on every frame and destroy performance.

Only animate `transform` and `opacity` -- they are GPU-accelerated and composited without triggering layout.

### Height Animations

For accordion/expand/collapse patterns, use `grid-template-rows: 0fr` to `1fr` instead of animating `height` directly:

```css
.accordion-content {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 300ms var(--ease-out-quart);
}

.accordion-content.open {
  grid-template-rows: 1fr;
}

.accordion-content > div {
  overflow: hidden;
}
```

---

## Staggered Animations

Cascade delays for lists and grids to create choreographed reveals:

```css
.item {
  animation: fade-slide-up 400ms var(--ease-out-quart) both;
  animation-delay: calc(var(--index) * 60ms);
}
```

Set the `--index` custom property on each item: `style="--index: 0"`, `style="--index: 1"`, etc.

### Rules

- **Cap total stagger time:** 10 items at 60ms = 600ms total. For many items, reduce per-item delay or cap the staggered count.
- **Stagger range:** 50-100ms per item depending on complexity.
- **Do not stagger everything.** Reserve stagger for meaningful reveals (page load, section entry), not every list render.

---

## Reduced Motion

This is not optional. Vestibular disorders affect approximately 35% of adults over 40.

### Implementation

```css
/* Define animations normally */
.card {
  animation: slide-up 500ms var(--ease-out-quart);
}

/* Provide meaningful alternative for reduced motion */
@media (prefers-reduced-motion: reduce) {
  .card {
    animation: fade-in 200ms ease-out;  /* Crossfade instead of spatial motion */
  }
}
```

### Nuclear Option (Use Sparingly)

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### What to Preserve in Reduced Motion

- Progress bars (functional, not decorative)
- Loading spinners (can be slowed, not removed)
- Focus indicators (accessibility requirement)
- Opacity changes (non-vestibular, generally safe)

Remove or simplify: spatial movement, parallax, zoom effects, auto-playing animations.

---

## Perceived Performance

### The 80ms Threshold

Our brains buffer sensory input for approximately 80ms to synchronize perception. Anything under 80ms feels instant and simultaneous. This is your target for micro-interaction feedback.

### Active vs Passive Time

Passive waiting (staring at a spinner) feels longer than active engagement. Strategies:

- **Preemptive start:** Begin transitions immediately while loading (skeleton UI, iOS app zoom). Users perceive work happening.
- **Early completion:** Show content progressively -- do not wait for everything. Streaming HTML, progressive images, video buffering.
- **Optimistic UI:** Update the interface immediately, handle failures gracefully. Use for low-stakes actions (likes, toggles, saves); avoid for payments or destructive operations.

### Easing and Time Perception

Ease-in (accelerating toward completion) makes tasks feel shorter because the peak-end effect weights final moments heavily. Use ease-in toward the end of a loading/processing sequence to compress perceived duration.

### Caution

Too-fast responses can decrease perceived value. Users may distrust instant results for complex operations (search, analysis). Sometimes a brief delay signals "real work" is happening.

---

## Animation Categories

### Entrance Animations

- **Page load choreography:** Stagger element reveals (100-150ms delays), fade + slide combinations
- **Hero section:** Dramatic entrance for primary content (scale, parallax, creative effects)
- **Content reveals:** Scroll-triggered animations using IntersectionObserver
- **Modal/drawer entry:** Smooth slide + fade, backdrop fade, focus management

### Micro-Interactions

- **Button feedback:** Hover (subtle scale 1.02-1.05, color shift, shadow increase), Click (quick scale down then up 0.95 to 1, ripple), Loading (spinner or pulse)
- **Form interactions:** Focus (border transition, slight glow), Validation (shake on error, checkmark on success)
- **Toggle switches:** Smooth slide + color transition (200-300ms)
- **Checkboxes/radio:** Checkmark animation, scale pulse
- **Like/favorite:** Scale + rotation, particle effects, color transition

### State Transitions

- **Show/hide:** Fade + slide (not instant), 200-300ms
- **Expand/collapse:** Grid-template-rows transition, icon rotation
- **Loading states:** Skeleton screen fades, spinner animations, progress bars
- **Success/error:** Color transitions, icon animations, gentle scale pulse
- **Enable/disable:** Opacity transitions, cursor changes

### Navigation and Flow

- **Page transitions:** Crossfade between routes, shared element transitions
- **Tab switching:** Slide indicator, content fade/slide
- **Carousel/slider:** Smooth transforms, snap points, momentum
- **Scroll effects:** Parallax layers, sticky headers with state changes, scroll progress indicators

### Feedback and Guidance

- **Hover hints:** Tooltip fade-ins, cursor changes, element highlights
- **Drag and drop:** Lift effect (shadow + scale), drop zone highlights, smooth repositioning
- **Copy/paste:** Brief highlight flash, "copied" confirmation
- **Focus flow:** Highlight path through form or workflow

### Celebration

- **Success celebrations:** Confetti burst, checkmark draw animation, scale + fade confirmation
- **Milestone recognition:** Streak counters, progress bar celebrations at 100%, badge unlocks
- **Empty states:** Subtle floating animations on illustrations

---

## Delight Principles

### Delight Amplifies, Never Blocks

- Delight moments should be quick (under 1 second)
- Never delay core functionality for delight
- Make delight skippable or subtle
- Respect user's time and task focus

### Surprise Proportional to Context

- Match delight to emotional moment (celebrate success, empathize with errors)
- Respect the user's state (do not be playful during critical errors)
- Hide delightful details for users to discover
- Do not announce every delight moment

### Appropriate to Brand

- Match brand personality and audience expectations
- Cultural sensitivity (what is delightful varies by culture)
- Banking app is not gaming app -- but banks can be warm
- The domain dictates the ceiling for expressiveness

### Compounds Over Time

- Delight should remain fresh with repeated use
- Vary responses (not the same animation every time)
- Reveal deeper layers with continued use
- Build anticipation through patterns

---

## Delight Opportunities

### Success States
Completed actions deserve acknowledgment: save, send, publish, submit. Confetti for milestones, animated checkmarks for routine completions, personalized messages for achievements.

### Empty States
First-time experiences and onboarding moments. Custom illustrations (not stock icons), encouraging copy specific to the product, subtle floating animations.

### Loading States
Waiting periods that could be engaging instead of frustrating. Product-specific loading messages (not generic AI filler), progress indication with encouraging context, skeleton screens with subtle animation.

**Avoid cliched loading messages:** "Herding pixels", "Teaching robots to dance", "Consulting the magic 8-ball" -- these are AI-slop copy. Write messages specific to what your product actually does.

### Achievements
Milestones, streaks, completions. First-time actions get special treatment, streak tracking with celebration, progress toward goals, anniversary celebrations.

### Interactions
Hover states, clicks, drags. Icons that animate on hover, satisfying button press feedback, smooth drag-and-drop with spring physics, custom cursors for branded experiences.

### Errors
Softening frustrating moments. Friendly illustrations, warm copy that empathizes, clear guidance on what to do next.

### Easter Eggs
Hidden discoveries for curious users. Konami code unlocks, console messages for developers, hover reveals on logos, seasonal touches, time-of-day variations.

---

## Delight Techniques

### Micro-Interactions

```css
/* Satisfying button press */
.button {
  transition: transform 0.1s, box-shadow 0.1s;
}
.button:hover {
  transform: translateY(-2px);
  transition: transform 0.2s var(--ease-out-quart);
}
.button:active {
  transform: translateY(2px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
```

### Personality in Copy

Error messages, empty states, tooltips, and labels are all opportunities for voice. Match copy personality to brand -- do not force humor where it does not belong, but do not be robotic either.

### Illustrations and Visual Personality

Custom illustrations for empty states, error states, loading, and success. Consistent icon style matching brand personality. Background effects (particles, gradient mesh, geometric patterns) used sparingly.

### Satisfying Interactions

- Drag-and-drop: lift effect, snap animation, undo toast
- Toggle switches: spring physics, color transition, haptic feedback on mobile
- Form inputs: animate on focus, celebrate valid input, auto-grow textareas
- Progress: bars that celebrate at 100%, badge unlocks with animation

### Sound Design (When Appropriate)

- Subtle audio cues for notifications, success, errors
- Respect system sound settings, provide mute option
- Keep volumes quiet (subtle cues, not alarms)
- Do not play on every interaction (sound fatigue)
- Requires user gesture to start (Web Audio API requirement)

---

## Overdrive Toolkit

For interfaces that need to go beyond conventional limits. Every technique must degrade gracefully -- the experience without the enhancement must still be good.

### Cinematic Transitions

- **View Transitions API:** Shared element morphing between states. Same-document: all browsers; cross-document: no Firefox. Use for list-to-detail, button-to-dialog morphs.
- **`@starting-style`:** Animate elements from `display: none` to visible with CSS only. All browsers.
- **Spring physics:** Natural motion with mass, tension, damping. Libraries: motion (Framer Motion), React Spring, GSAP, Popmotion.

### Scroll and Property Animation

- **Scroll-driven animations** (`animation-timeline: scroll()`): CSS-only parallax, progress bars, reveal sequences. Chrome/Edge/Safari; Firefox flag only -- always provide static fallback.
- **`@property`:** Register custom CSS properties with types, enabling animation of gradients and complex values CSS cannot normally interpolate.
- **Web Animations API:** JavaScript-driven animations with CSS performance. Composable, cancellable, reversible.

### GPU Rendering

- **WebGL:** Shader effects, post-processing, particle systems. Libraries: Three.js, OGL, regl.
- **WebGPU:** Next-gen GPU compute (Chrome/Edge; Safari partial; Firefox flag). Always fall back to WebGL2.
- **Canvas 2D / OffscreenCanvas:** Custom rendering off the main thread via Web Workers.
- **SVG filter chains:** Displacement maps, turbulence, morphology for organic distortion.

### Performance-Critical

- **Web Workers:** Move computation off the main thread for anything that would cause jank.
- **WASM:** Near-native performance for computation-heavy features (image processing, physics, codecs).

### Progressive Enhancement

```css
@supports (animation-timeline: scroll()) {
  .hero { animation-timeline: scroll(); }
}
```
```javascript
if ('gpu' in navigator) { /* WebGPU */ }
else if (canvas.getContext('webgl2')) { /* WebGL2 fallback */ }
```

---

## Animation Assessment

### Identify Opportunities

- **Missing feedback:** Actions without visual acknowledgment
- **Jarring transitions:** Instant state changes that feel abrupt
- **Unclear relationships:** Spatial or hierarchical connections that are not obvious
- **Lack of delight:** Functional but joyless interactions
- **Missed guidance:** Opportunities to direct attention

### Plan Strategy Across Layers

- **Hero moment:** The ONE signature animation (page load, hero section, key interaction)
- **Feedback layer:** Which interactions need acknowledgment
- **Transition layer:** Which state changes need smoothing
- **Delight layer:** Where to surprise and create joy

One well-orchestrated experience beats scattered animations everywhere. Focus on high-impact moments.

### Implement with Proper Timing

- Match duration to purpose (100ms for feedback, 300ms for transitions, 500ms for complex)
- Use exponential easing curves, not CSS defaults
- Animate only transform and opacity
- Stagger lists and grids with capped total duration
- Respect prefers-reduced-motion with meaningful alternatives

---

## Performance

### Rules

- **GPU acceleration:** Use `transform` and `opacity` exclusively. These composite on the GPU without triggering layout.
- **will-change:** Use sparingly, only when animation is imminent (`:hover`, `.animating`). Preemptive use wastes GPU memory.
- **requestAnimationFrame:** Always use for JS-driven animations. Never `setInterval` or `setTimeout` for animation loops.
- **IntersectionObserver:** Use instead of scroll event listeners for scroll-triggered animations. Unobserve after animating once.
- **60fps target:** If dropping below 50fps, simplify. Test on real mid-range devices.
- **Lazy initialization:** Heavy resources (WebGL contexts, WASM modules) only when near viewport.
- **Pause off-screen:** Kill rendering you cannot see. Use `contain` to minimize paint area.

### Motion Tokens

Create reusable tokens for consistency across the project:

```css
:root {
  --duration-instant: 100ms;
  --duration-fast: 200ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.7, 0, 0.84, 0);
}
```
