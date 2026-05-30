# SvelteKit — Styling, Transitions & Animations

> Source: [svelte.dev/docs/svelte/styles](https://svelte.dev/docs/svelte/styles)

## Table of Contents

- [Scoped CSS](#scoped-css)
- [Global Styles](#global-styles)
- [Dynamic Styles](#dynamic-styles)
- [CSS Variables](#css-variables)
- [Tailwind CSS Integration](#tailwind-css-integration)
- [Transitions](#transitions)
- [Animations](#animations)
- [Motion (spring, tweened)](#motion-spring-tweened)

## Scoped CSS

Styles in `<style>` blocks are scoped to the component by default. Svelte adds unique class selectors at compile time:

```svelte
<p>This is red</p>

<style>
  /* Only affects <p> in THIS component */
  p {
    color: red;
    font-weight: bold;
  }
</style>
```

### Unused CSS

Svelte warns about unused CSS selectors at compile time. Selectors that don't match any markup in the component are flagged.

## Global Styles

### :global Modifier

```svelte
<style>
  /* Scoped — only this component */
  .card {
    padding: 1rem;
  }

  /* Global — affects entire app */
  :global(body) {
    margin: 0;
    font-family: system-ui;
  }

  /* Mixed — .card is scoped, but .title inside it is global */
  .card :global(.title) {
    font-size: 1.5rem;
  }

  /* Global block */
  :global {
    .markdown h1 { font-size: 2rem; }
    .markdown p { line-height: 1.6; }
  }
</style>
```

### Global Stylesheet

```css
/* src/app.css */
:root {
  --color-primary: #3b82f6;
  --color-bg: #ffffff;
}

body {
  margin: 0;
  font-family: system-ui, sans-serif;
}
```

```svelte
<!-- src/routes/+layout.svelte -->
<script>
  import '../app.css';
  let { children } = $props();
</script>

{@render children()}
```

## Dynamic Styles

### Class Directive

```svelte
<script>
  let active = $state(false);
  let type = $state('primary');
</script>

<!-- Boolean toggle -->
<div class:active>...</div>

<!-- Shorthand when class name matches variable -->
<div class:active={active}>...</div>

<!-- Computed class -->
<div class="btn btn-{type}">...</div>

<!-- Multiple classes -->
<div
  class:active
  class:disabled={!enabled}
  class:large={size === 'lg'}
>...</div>

<!-- Object syntax with template -->
<div class={`card ${variant} ${isActive ? 'active' : ''}`}>...</div>
```

### Style Directive

```svelte
<script>
  let color = $state('#ff0000');
  let size = $state(16);
</script>

<p style:color style:font-size="{size}px">
  Dynamic styles
</p>

<!-- Important modifier -->
<p style:color="red" style:--custom="value">
  With CSS variables
</p>

<!-- Conditional styles -->
<div
  style:opacity={loading ? 0.5 : 1}
  style:pointer-events={loading ? 'none' : 'auto'}
>
  Content
</div>
```

### Inline Style

```svelte
<div style="color: {color}; font-size: {size}px;">...</div>
```

## CSS Variables

### Component-Level CSS Variables

```svelte
<!-- Spinner.svelte -->
<div class="spinner"></div>

<style>
  .spinner {
    width: var(--size, 40px);
    height: var(--size, 40px);
    border-color: var(--color, #3b82f6);
  }
</style>
```

```svelte
<!-- Parent — set CSS variables as props -->
<Spinner --size="24px" --color="red" />
```

This compiles to a wrapper element with `style="--size: 24px; --color: red;"`.

## Tailwind CSS Integration

### Setup

```bash
npx sv add tailwindcss
```

Or manually:

```bash
npm install -D @tailwindcss/vite tailwindcss
```

```ts
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()]
});
```

```css
/* src/app.css */
@import 'tailwindcss';
```

### Usage in Components

```svelte
<div class="flex items-center gap-4 p-6 bg-white rounded-lg shadow-md">
  <img class="w-12 h-12 rounded-full" src={avatar} alt="" />
  <div>
    <h3 class="text-lg font-semibold text-gray-900">{name}</h3>
    <p class="text-sm text-gray-500">{role}</p>
  </div>
</div>
```

### Conditional Tailwind Classes

```svelte
<button
  class="px-4 py-2 rounded font-medium
    {variant === 'primary' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'}
    {disabled ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-90'}"
>
  {label}
</button>
```

## Transitions

Built-in transitions for elements entering and leaving the DOM:

### Basic Transitions

```svelte
<script>
  import { fade, fly, slide, scale, blur, draw } from 'svelte/transition';
  let visible = $state(true);
</script>

<button onclick={() => visible = !visible}>Toggle</button>

{#if visible}
  <p transition:fade>Fades in and out</p>
  <p transition:fly={{ y: 200, duration: 500 }}>Flies in from below</p>
  <p transition:slide>Slides in/out</p>
  <p transition:scale={{ start: 0.5 }}>Scales in/out</p>
  <p transition:blur={{ amount: 10 }}>Blurs in/out</p>
{/if}
```

### In/Out Transitions

Different transitions for entering and leaving:

```svelte
{#if visible}
  <p in:fly={{ y: -50 }} out:fade>
    Flies in, fades out
  </p>
{/if}
```

### Transition Parameters

```svelte
<div transition:fly={{
  x: 0,
  y: 200,
  duration: 400,
  delay: 100,
  easing: quintOut
}}>
  Content
</div>
```

### Transition Events

```svelte
<div
  transition:fade
  onintrostart={() => console.log('intro started')}
  onintroend={() => console.log('intro ended')}
  onoutrostart={() => console.log('outro started')}
  onoutroend={() => console.log('outro ended')}
>
  Tracked
</div>
```

### Custom Transitions

```ts
// src/lib/transitions/typewriter.ts
import type { TransitionConfig } from 'svelte/transition';

export function typewriter(node: HTMLElement, { speed = 1 }): TransitionConfig {
  const text = node.textContent ?? '';
  const duration = text.length / (speed * 0.01);

  return {
    duration,
    tick(t) {
      const i = Math.trunc(text.length * t);
      node.textContent = text.slice(0, i);
    }
  };
}
```

### Local Transitions

By default, transitions play when any parent block is added/removed. Use `|local` to only play when the element's own block changes:

```svelte
{#each items as item}
  <div transition:slide|local>
    {item.name}
  </div>
{/each}
```

## Animations

The `animate:` directive handles layout changes in keyed each blocks:

```svelte
<script>
  import { flip } from 'svelte/animate';
  import { fade } from 'svelte/transition';
</script>

{#each items as item (item.id)}
  <div
    animate:flip={{ duration: 300 }}
    in:fade
    out:fade
  >
    {item.name}
  </div>
{/each}
```

`flip` (First-Last-Invert-Play) smoothly animates elements when they're reordered, added, or removed.

## Motion (spring, tweened)

Smooth value interpolation for continuous animations:

### Spring

```svelte
<script>
  import { spring } from 'svelte/motion';

  let coords = spring({ x: 50, y: 50 }, {
    stiffness: 0.1,
    damping: 0.25
  });
</script>

<svelte:window onmousemove={(e) => coords.set({ x: e.clientX, y: e.clientY })} />

<div style="transform: translate({$coords.x}px, {$coords.y}px)">
  Follows cursor
</div>
```

### Tweened

```svelte
<script>
  import { tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';

  let progress = tweened(0, { duration: 400, easing: cubicOut });
</script>

<button onclick={() => progress.set(100)}>Complete</button>

<div class="bar" style="width: {$progress}%"></div>
```

## Common Pitfalls

1. **Expecting global styles in `<style>`** — Component styles are scoped. Use `:global()` or a separate CSS file for global styles.
2. **Transition on wrong element** — `transition:` only works on elements that are conditionally rendered (`{#if}`, `{#each}`)
3. **Missing key in animated each** — `animate:flip` requires a keyed each block: `{#each items as item (item.id)}`
4. **Over-using transitions** — Excessive animation distracts users. Use subtle, purposeful transitions only.

## Related

- Components → `09-components.md`
- Runes & Reactivity → `02-runes-reactivity.md`
