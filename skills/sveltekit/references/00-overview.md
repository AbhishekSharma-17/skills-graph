# SvelteKit — Overview & Setup

> Source: [svelte.dev/docs/kit](https://svelte.dev/docs/kit) | Package: `@sveltejs/kit` v2.57.x / `svelte` v5.55.x

## What Is SvelteKit

SvelteKit is a full-stack web framework built on top of Svelte and Vite. It provides everything needed to build production web applications: file-based routing, server-side rendering, code splitting, data loading, form handling, and deployment adapters for every major hosting platform.

Svelte compiles components into efficient imperative JavaScript at build time — no virtual DOM, no runtime framework overhead. SvelteKit layers a full-stack application framework on top, handling routing, data loading, and server-side concerns.

Built and maintained by the Svelte core team (Rich Harris, now at Vercel), SvelteKit is used by Apple, The New York Times, Spotify, Square, and thousands of production applications. It has 86.7K GitHub stars (Svelte) and 93% developer satisfaction in the 2026 State of JS survey.

## When to Use SvelteKit

**Use SvelteKit when:**
- You want a full-stack framework with minimal boilerplate
- Performance and small bundle sizes are priorities
- You need flexibility between SSR, SSG, and SPA modes per route
- You want progressive enhancement (forms work without JavaScript)
- You prefer a compiler-first approach over runtime frameworks
- You need deployment flexibility (Node, Vercel, Cloudflare, static)

**Consider alternatives when:**
- Your team has deep React expertise and prefers that ecosystem (Next.js)
- You need a massive plugin/component ecosystem (React/Next.js)
- You are building a purely static blog (Astro may be simpler)
- You need server-only rendering without client JS (Astro)

## Core Architecture

### Compiler-First
Svelte compiles `.svelte` files into vanilla JavaScript at build time. There is no runtime framework shipped to the browser. Components become imperative DOM update instructions, resulting in smaller bundles and faster execution.

### Svelte 5 Runes
Svelte 5 introduced runes — explicit reactive primitives (`$state`, `$derived`, `$effect`) replacing the old `$:` reactive statements. Runes work in `.svelte`, `.svelte.ts`, and `.svelte.js` files, enabling reactive state outside components.

### File-Based Routing
Routes map directly to the filesystem inside `src/routes/`. A file at `src/routes/blog/[slug]/+page.svelte` creates a dynamic route at `/blog/:slug`.

### Server-First
SvelteKit defaults to server-side rendering. Pages render on the server, get hydrated on the client, and subsequent navigations are client-side. You can opt into prerendering (SSG) or client-only (SPA) per route.

## Project Structure

```
my-app/
├── src/
│   ├── routes/              # File-based routing
│   │   ├── +page.svelte     # Home page component
│   │   ├── +page.server.ts  # Server-side data loading
│   │   ├── +layout.svelte   # Root layout
│   │   ├── +layout.server.ts # Layout data loading
│   │   ├── +error.svelte    # Error page
│   │   ├── about/
│   │   │   └── +page.svelte # /about page
│   │   └── api/
│   │       └── health/
│   │           └── +server.ts # API endpoint
│   ├── lib/                 # Shared code ($lib alias)
│   │   ├── components/      # Reusable components
│   │   ├── server/          # Server-only utilities ($lib/server)
│   │   └── utils.ts         # Shared utilities
│   ├── params/              # Parameter matchers
│   ├── hooks.server.ts      # Server hooks (middleware)
│   ├── hooks.client.ts      # Client hooks
│   ├── app.html             # HTML template
│   ├── app.css              # Global styles
│   └── app.d.ts             # Type declarations
├── static/                  # Static assets (served as-is)
├── svelte.config.js         # SvelteKit configuration
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript config
└── package.json
```

## Installation & Setup

### New Project

```bash
# Create with the Svelte CLI
npx sv create my-app

# Interactive prompts:
#   - Template: SvelteKit minimal / demo / library
#   - Type checking: TypeScript (recommended)
#   - Add-ons: Prettier, ESLint, Vitest, Playwright, Tailwind, etc.

cd my-app
npm install
npm run dev        # Start dev server at localhost:5173
```

### Manual Setup

```bash
npm install @sveltejs/kit @sveltejs/adapter-auto @sveltejs/vite-plugin-svelte svelte vite
```

```js
// svelte.config.js
import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter()
  }
};
```

```ts
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()]
});
```

### App Shell Template

```html
<!-- src/app.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

## Key Commands

```bash
npm run dev          # Start development server (Vite HMR)
npm run build        # Production build
npm run preview      # Preview production build locally
npx sv add           # Add integrations (Tailwind, Drizzle, Lucia, etc.)
npx sv check         # Run svelte-check for type errors
```

## Configuration (svelte.config.js)

```js
import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
    alias: {
      '$components': 'src/lib/components',
      '$utils': 'src/lib/utils'
    },
    csrf: {
      checkOrigin: true     // CSRF protection (default: true)
    },
    paths: {
      base: '',             // Base path prefix
      assets: ''            // CDN URL for assets
    },
    prerender: {
      handleHttpError: 'warn'
    },
    version: {
      name: Date.now().toString()  // App version for polling
    }
  }
};
```

## The $lib Alias

`$lib` is a special import alias that resolves to `src/lib/`. It works everywhere — components, server code, and route files.

```svelte
<script>
  import Button from '$lib/components/Button.svelte';
  import { formatDate } from '$lib/utils';
</script>
```

Server-only code goes in `$lib/server/`. Importing from `$lib/server` in client-side code produces a build error, preventing accidental exposure of secrets.

```ts
// src/lib/server/db.ts — only importable in server code
import { DATABASE_URL } from '$env/static/private';
export const db = createClient(DATABASE_URL);
```

## TypeScript Support

SvelteKit has first-class TypeScript support. Type declarations are auto-generated in `.svelte-kit/types/`:

```ts
// src/app.d.ts
declare global {
  namespace App {
    interface Error {
      message: string;
      code?: string;
    }
    interface Locals {
      user?: { id: string; name: string };
    }
    interface PageData {}
    interface PageState {}
    interface Platform {}
  }
}

export {};
```

Load functions and form actions are fully typed. Run `npx sv check` to validate types across your entire project.

## Common Pitfalls

1. **Forgetting the `+` prefix** — Route files must start with `+` (e.g., `+page.svelte`, not `page.svelte`)
2. **Importing server code on client** — Use `$lib/server/` to ensure server-only modules cannot leak to the browser
3. **Not using the `$lib` alias** — Relative imports (`../../lib/`) break when routes are restructured; always use `$lib`
4. **Ignoring CSRF** — SvelteKit checks the `Origin` header by default; don't disable `csrf.checkOrigin` without reason
5. **Missing `app.html`** — The `%sveltekit.head%` and `%sveltekit.body%` placeholders are required in the template

## Related

- Routing → `01-routing.md`
- Runes & Reactivity → `02-runes-reactivity.md`
- Loading Data → `03-loading-data.md`
- Deployment → `12-deployment.md`
