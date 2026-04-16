# View Transitions

> Source: https://docs.astro.build/en/guides/view-transitions/

View Transitions give your multi-page site **SPA-like navigation**: smooth fades, slides, and morphs between pages without a full reload. Astro uses the browser-native **View Transitions API** where available (Chromium-based browsers) and falls back to a same-DOM simulation elsewhere.

## Enabling

Add the `<ClientRouter />` component to a shared layout:

```astro
---
// src/layouts/Default.astro
import { ClientRouter } from "astro:transitions";
const { title } = Astro.props;
---
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <ClientRouter />
  </head>
  <body>
    <slot />
  </body>
</html>
```

That single `<ClientRouter />` intercepts clicks on `<a>` tags, fetches the next page's HTML, diffs it against the current DOM, and runs transition animations.

## What Happens Under the Hood

1. User clicks `<a href="/about">`.
2. Astro's client router fetches `/about` HTML.
3. The old DOM snapshot is captured (via `document.startViewTransition`).
4. The new DOM is swapped in.
5. Browser animates from old → new based on transition names and CSS animations.
6. Browser history is updated — back/forward work normally.

For unsupported browsers, Astro falls back to: same DOM diff, but without native CSS transitions. The navigation still works, just less glossy.

## Default Animations

All pages transition with a subtle fade out/in by default. You control it at three scopes:

### Per-Page Root

```astro
---
import { fade, slide } from "astro:transitions";
---
<html transition:animate={fade({ duration: "0.4s" })}>
```

Or disable transitions for a specific page:

```astro
<html transition:animate="none">
```

### Per-Element

Any element inside a page can participate:

```astro
<img src={heroImage} transition:name="hero" />
```

If another page has an element with the same `transition:name`, the browser morphs between them seamlessly — great for shared hero images, avatars, or headings that persist across routes.

### Element Animations

```astro
---
import { fade, slide } from "astro:transitions";
---
<header transition:animate={slide({ duration: "0.3s" })}>
  Site Header
</header>
```

Built-in animations:

| Name | Effect |
|------|--------|
| `fade()` | Cross-fade opacity |
| `slide({ duration })` | Slide in/out horizontally (direction-aware by navigation) |
| `"initial"` | Browser's default behavior |
| `"none"` | Disable animation entirely |

## Custom Animations

Pass a CSS keyframes-backed object:

```astro
---
const zoom = {
  forwards: {
    old: { name: "zoom-out-old", duration: "0.3s", easing: "ease-in", fillMode: "forwards" },
    new: { name: "zoom-in-new", duration: "0.3s", easing: "ease-out", fillMode: "backwards" },
  },
  backwards: {
    old: { name: "zoom-out-new", duration: "0.3s", easing: "ease-in", fillMode: "forwards" },
    new: { name: "zoom-in-old", duration: "0.3s", easing: "ease-out", fillMode: "backwards" },
  },
};
---
<main transition:animate={zoom}>
  <slot />
</main>

<style is:global>
  @keyframes zoom-in-new  { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
  @keyframes zoom-out-old { from { opacity: 1; } to { opacity: 0; } }
  @keyframes zoom-in-old  { from { opacity: 0; } to { opacity: 1; } }
  @keyframes zoom-out-new { from { opacity: 1; transform: scale(1); } to { opacity: 0; transform: scale(1.05); } }
</style>
```

## Preserving State Across Pages

By default, a full DOM swap wipes form state, video players, third-party widgets. Mark an element to **persist**:

```astro
<iframe
  src="https://www.youtube.com/embed/abc"
  transition:persist="player"
></iframe>
```

Every page using the same `transition:persist="player"` will reuse the same iframe element. Perfect for:

- Audio/video players continuing playback across nav
- Scroll positions
- Stateful third-party widgets (maps, chat)
- Form inputs that should survive navigation (rare — use cookies/localStorage instead)

Framework components also persist their state if marked:

```astro
<Counter client:load transition:persist />
```

## Lifecycle Events

The client router fires events on `document`. Hook in for analytics or state updates:

```ts
document.addEventListener("astro:before-preparation", (event) => {
  console.log("Navigation starting:", event.to.href);
});

document.addEventListener("astro:before-swap", (event) => {
  // Old DOM still visible, new DOM parsed but not yet applied
  // event.newDocument is the incoming <html>
});

document.addEventListener("astro:after-swap", () => {
  // New DOM is live, transitions running
});

document.addEventListener("astro:page-load", () => {
  // Full transition complete — fire on initial load AND after every nav
  initializePageScripts();
});
```

### Why `astro:page-load` and not `DOMContentLoaded`?

`DOMContentLoaded` fires only on the initial page load. Scripts written for multi-page apps using view transitions must use `astro:page-load` to re-run their initialization after every navigation.

```astro
<script>
  document.addEventListener("astro:page-load", () => {
    document.querySelectorAll(".counter").forEach((el) => {
      el.addEventListener("click", () => console.log("clicked"));
    });
  });
</script>
```

## Programmatic Navigation

```ts
import { navigate } from "astro:transitions/client";

await navigate("/new-page");
await navigate("/blog", { history: "replace" });        // replaceState
await navigate("/search?q=foo", { formData: myFormData });  // POST + navigate
```

## Skipping Transitions for Specific Links

```astro
<a href="/legacy" data-astro-reload>Full page load</a>
<a href="/external" data-astro-history="replace">Replace history</a>
```

Available attributes:

| Attribute | Effect |
|-----------|--------|
| `data-astro-reload` | Force a full page reload (no transition) |
| `data-astro-history="push" \| "replace" \| "auto"` | Control history entry |
| `data-astro-prefetch` | Prefetch the page on hover/focus |

## Prefetching for Instant Nav

Built-in prefetcher (separate from View Transitions, but often paired):

```js
// astro.config.mjs
export default defineConfig({
  prefetch: {
    prefetchAll: true,
    defaultStrategy: "viewport",        // "load" | "viewport" | "hover" | "tap"
  },
});
```

Opt out per-link: `<a href="/x" data-astro-prefetch="false">X</a>`.

## Accessibility

- Transitions respect `prefers-reduced-motion: reduce`. Astro automatically falls back to a short cross-fade (or nothing) for users who request reduced motion.
- Focus management: after nav, focus is moved to `<body>` by default. Set `tabindex="-1"` on a main heading and `document.querySelector("h1")?.focus()` in `astro:page-load` if you need more controlled focus.
- Announce navigation to screen readers: Astro adds `aria-live="assertive"` to a `<h1>` automatically when present — use meaningful `h1`s.

## Common Pitfalls

- **Scripts with inline `DOMContentLoaded` listeners break after navigation** — switch to `astro:page-load`, or use `<script is:inline>` with a one-time init guard.
- **Element identity mismatch** — two elements with the same `transition:name` must be on both pages, or the transition falls back silently.
- **Third-party widgets that self-mount on DOMContentLoaded** — they won't re-initialize after navigation. Wrap with `transition:persist` to keep them alive, or re-init in `astro:page-load`.
- **Forgetting to add `<ClientRouter />` to every shared layout** — pages without it fall back to full reloads.
- **CSS-only animations blocking transitions** — `transition: all` on `<html>`/`<body>` can interfere with the browser's transition pseudo-elements. Scope transitions explicitly.
- **Expecting native browser View Transitions in Safari/Firefox as of April 2026** — Safari shipped partial support; Firefox still behind a flag. Astro's simulation works everywhere, just without the GPU-accelerated morph.
