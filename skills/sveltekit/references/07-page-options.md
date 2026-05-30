# SvelteKit — Page Options & Rendering Modes

> Source: [svelte.dev/docs/kit/page-options](https://svelte.dev/docs/kit/page-options)

## Table of Contents

- [Overview](#overview)
- [SSR (Server-Side Rendering)](#ssr-server-side-rendering)
- [CSR (Client-Side Rendering)](#csr-client-side-rendering)
- [Prerendering (SSG)](#prerendering-ssg)
- [Trailing Slash](#trailing-slash)
- [Page Options Per Route](#page-options-per-route)
- [Rendering Modes Comparison](#rendering-modes-comparison)
- [Project Types](#project-types)

## Overview

SvelteKit lets you control rendering behavior on a per-route basis by exporting options from `+page.ts`, `+page.server.ts`, `+layout.ts`, or `+layout.server.ts`. This flexibility lets you mix SSR, SSG, and SPA modes within a single application.

## SSR (Server-Side Rendering)

**Default: `true`**

SvelteKit renders pages on the server before sending HTML to the client, where it gets hydrated into an interactive app.

```ts
// src/routes/+page.ts
export const ssr = true; // default, not needed explicitly
```

### Disabling SSR

```ts
// src/routes/admin/+page.ts
export const ssr = false;
```

When `ssr = false`:
- An empty HTML shell is sent to the client
- The page renders entirely in the browser
- Useful for pages that depend on browser-only APIs (`window`, `document`, `canvas`)

**Warning:** Disabling SSR hurts SEO and initial load performance. Only disable when the page genuinely cannot render on the server.

### SSR-Only Considerations

```svelte
<script>
  import { browser } from '$app/environment';

  // Guard browser-only code:
  if (browser) {
    const map = new google.maps.Map(element);
  }

  // Or use onMount (only runs in browser):
  import { onMount } from 'svelte';
  onMount(() => {
    // Safe to use window, document, etc.
  });
</script>
```

## CSR (Client-Side Rendering)

**Default: `true`**

Controls whether JavaScript is sent to the client for hydration and interactivity.

```ts
// Disable CSR — pure HTML/CSS, no JavaScript shipped
export const csr = false;
```

When `csr = false`:
- No JavaScript is sent to the browser
- The page is purely HTML/CSS
- Interactive elements (onclick, forms with `use:enhance`) don't work
- Perfect for static content pages (blog posts, documentation, about pages)

```ts
// src/routes/blog/[slug]/+page.ts
export const csr = false;    // No JS needed for reading a blog post
export const prerender = true; // Generate static HTML at build time
```

## Prerendering (SSG)

**Default: `false` (or `'auto'` for some configurations)**

Generates static HTML files at build time. Pages are served as static files — no server needed at runtime.

```ts
// src/routes/about/+page.ts
export const prerender = true;
```

### Auto-Detection

```ts
// 'auto' — SvelteKit decides based on whether the page uses dynamic features
export const prerender = 'auto';
```

### Prerendering Dynamic Routes

SvelteKit crawls links to discover pages to prerender. For dynamic routes not linked from other pages, use `entries()`:

```ts
// src/routes/blog/[slug]/+page.server.ts
export const prerender = true;

export async function entries() {
  const posts = await getAllPosts();
  return posts.map((post) => ({ slug: post.slug }));
}
```

### Prerender Configuration

```js
// svelte.config.js
export default {
  kit: {
    prerender: {
      // Pages to prerender that aren't discoverable by crawling
      entries: ['/', '/about', '/sitemap.xml'],

      // How to handle HTTP errors during prerendering
      handleHttpError: 'warn',   // 'fail' | 'warn' | 'ignore' | handler function

      // How to handle missing IDs in links
      handleMissingId: 'warn',

      // Concurrent prerendering
      concurrency: 4
    }
  }
};
```

### Requirements for Prerendering

- Page cannot use `url.searchParams` (no query parameters at build time)
- Page cannot use server-only features that depend on runtime data
- `ssr` must be `true` (prerendering requires server-side rendering)
- Form actions are not available on prerendered pages

## Trailing Slash

Controls whether URLs have a trailing slash:

```ts
export const trailingSlash = 'never';  // /about (default)
export const trailingSlash = 'always'; // /about/
export const trailingSlash = 'ignore'; // both work
```

This affects:
- How links are generated
- How prerendered files are named
- How redirects work for mismatched URLs

## Page Options Per Route

Options cascade from layouts to pages. Set them at the layout level to apply to all child routes:

```ts
// src/routes/(marketing)/+layout.ts
// All marketing pages are prerendered
export const prerender = true;
export const csr = false;
```

```ts
// src/routes/(app)/+layout.ts
// App pages need full interactivity
export const ssr = true;
export const csr = true;
export const prerender = false;
```

```ts
// src/routes/(app)/canvas/+page.ts
// Override: this specific page can't SSR
export const ssr = false;
```

### Precedence

Page-level options override layout-level options. The most specific (deepest) value wins.

## Rendering Modes Comparison

| Mode | SSR | CSR | Prerender | Use Case |
|------|-----|-----|-----------|----------|
| **Default (SSR + hydration)** | true | true | false | Most pages — SEO + interactivity |
| **SSG (Static)** | true | true | true | Marketing, docs, blog — fast, cacheable |
| **SSG no JS** | true | false | true | Pure content pages — minimal payload |
| **SPA** | false | true | false | Admin dashboards, canvas apps — browser-only |
| **SSR no JS** | true | false | false | Progressive enhancement — works without JS |

### Common Configurations

```ts
// Blog post — static, no JS
export const prerender = true;
export const csr = false;

// Marketing landing page — static, with animations
export const prerender = true;

// Dashboard — SPA mode
export const ssr = false;

// API-driven dynamic page — standard SSR
// (no exports needed, defaults are correct)
```

## Project Types

SvelteKit supports building different project types with the same codebase:

### Full SSR Application

```js
// svelte.config.js
import adapter from '@sveltejs/adapter-node';
export default { kit: { adapter: adapter() } };
```

### Fully Static Site (SSG)

```js
// svelte.config.js
import adapter from '@sveltejs/adapter-static';
export default {
  kit: {
    adapter: adapter({ fallback: undefined })
  }
};
```

```ts
// src/routes/+layout.ts
export const prerender = true; // Prerender everything
```

### Single-Page Application (SPA)

```js
// svelte.config.js
import adapter from '@sveltejs/adapter-static';
export default {
  kit: {
    adapter: adapter({ fallback: '200.html' })
  }
};
```

```ts
// src/routes/+layout.ts
export const ssr = false; // No server rendering
```

### Hybrid (Mixed Modes)

No global setting needed. Set per route:

```
src/routes/
├── (marketing)/        ← prerender = true, csr = false
│   ├── +layout.ts
│   ├── +page.svelte     → / (static)
│   └── pricing/
│       └── +page.svelte → /pricing (static)
├── (app)/              ← ssr = true, csr = true
│   ├── +layout.ts
│   ├── dashboard/
│   │   └── +page.svelte → /dashboard (SSR)
│   └── canvas/
│       ├── +page.ts     → ssr = false (SPA override)
│       └── +page.svelte → /canvas (SPA)
```

## Common Pitfalls

1. **Prerendering pages with form actions** — Form actions require a running server; they don't work on prerendered pages
2. **SSR=false hurts SEO** — Search engines see an empty page. Only disable for authenticated/internal tools.
3. **Forgetting `entries()`** — Dynamic routes (`[slug]`) aren't prerendered unless linked from a prerendered page or listed in `entries()`
4. **CSR=false breaks interactivity** — No event handlers, no `use:enhance`, no client-side navigation
5. **Conflicting prerender + dynamic data** — Prerendered pages can't read `url.searchParams` or cookies at runtime

## Related

- Routing → `01-routing.md`
- Loading Data → `03-loading-data.md`
- Deployment → `12-deployment.md`
