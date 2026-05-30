# SvelteKit — Environment Variables & Configuration

> Source: [svelte.dev/docs/kit/$env-static-private](https://svelte.dev/docs/kit/$env-static-private)

## Table of Contents

- [Overview](#overview)
- [$env/static/private](#envstaticprivate)
- [$env/static/public](#envstaticpublic)
- [$env/dynamic/private](#envdynamicprivate)
- [$env/dynamic/public](#envdynamicpublic)
- [$app Modules](#app-modules)
- [svelte.config.js Options](#svelteconfigjs-options)
- [Vite Configuration](#vite-configuration)

## Overview

SvelteKit provides four modules for environment variables, divided by two axes:

| | **Private** (server-only) | **Public** (server + client) |
|---|---|---|
| **Static** (build-time) | `$env/static/private` | `$env/static/public` |
| **Dynamic** (runtime) | `$env/dynamic/private` | `$env/dynamic/public` |

**Private** variables can only be imported in server-side code (`+page.server.ts`, `hooks.server.ts`, `$lib/server/`). Importing them in client code causes a build error.

**Public** variables must be prefixed with `PUBLIC_` and are safe to expose to the browser.

## $env/static/private

Inlined at build time. Tree-shaken and dead-code eliminated. Best for secrets used in server-side code.

```bash
# .env
DATABASE_URL=postgresql://localhost:5432/mydb
API_SECRET=sk_live_abc123
STRIPE_WEBHOOK_SECRET=whsec_xyz
```

```ts
// src/routes/api/webhook/+server.ts
import { DATABASE_URL, API_SECRET, STRIPE_WEBHOOK_SECRET } from '$env/static/private';

export const POST: RequestHandler = async ({ request }) => {
  // These values are replaced at build time
  const signature = request.headers.get('stripe-signature');
  // Use STRIPE_WEBHOOK_SECRET to verify...
};
```

### Build-Time Behavior

Static imports are replaced with literal strings during `vite build`. This enables dead-code elimination:

```ts
import { FEATURE_FLAG } from '$env/static/private';

// If FEATURE_FLAG is empty, this entire block is removed from the build
if (FEATURE_FLAG) {
  // ...
}
```

## $env/static/public

Build-time variables safe for the browser. Must be prefixed with `PUBLIC_`:

```bash
# .env
PUBLIC_API_URL=https://api.example.com
PUBLIC_APP_NAME=My App
PUBLIC_SENTRY_DSN=https://abc@sentry.io/123
```

```svelte
<!-- Can be used in ANY file, including .svelte components -->
<script>
  import { PUBLIC_API_URL, PUBLIC_APP_NAME } from '$env/static/public';
</script>

<h1>{PUBLIC_APP_NAME}</h1>
```

## $env/dynamic/private

Runtime values read from the environment when the app runs (not at build time). Useful when the same build is deployed to multiple environments:

```ts
// src/lib/server/db.ts
import { env } from '$env/dynamic/private';

// env.DATABASE_URL is read at runtime, not baked into the build
export const db = createClient(env.DATABASE_URL);
```

```ts
// Access any env var by name
import { env } from '$env/dynamic/private';

const secret = env.MY_SECRET; // string | undefined
```

### When to Use Dynamic vs Static

- **Static:** Most cases. Faster (inlined), tree-shakeable, type-safe imports.
- **Dynamic:** When the same build artifact deploys to multiple environments (staging vs production) with different env vars.

## $env/dynamic/public

Runtime public variables accessible in the browser:

```svelte
<script>
  import { env } from '$env/dynamic/public';
</script>

<p>API: {env.PUBLIC_API_URL}</p>
```

**Note:** Dynamic public variables cannot be tree-shaken and add to bundle size. Prefer static public when possible.

## $app Modules

SvelteKit provides several `$app/*` modules beyond navigation and stores:

### $app/environment

```ts
import { browser, dev, building, version } from '$app/environment';

// browser: true in browser, false during SSR
// dev: true in development (npm run dev)
// building: true during vite build
// version: from config.kit.version.name
```

### $app/forms

```ts
import { enhance, applyAction, deserialize } from '$app/forms';
// enhance: progressive enhancement for forms
// applyAction: manually apply a form action result
// deserialize: deserialize form action response
```

### $app/navigation

```ts
import {
  goto,
  invalidate,
  invalidateAll,
  preloadData,
  preloadCode,
  beforeNavigate,
  afterNavigate,
  onNavigate
} from '$app/navigation';
```

### $app/state (Svelte 5)

```svelte
<script>
  import { page, navigating, updated } from '$app/state';
</script>

<p>{page.url.pathname}</p>
{#if navigating.to}
  <LoadingBar />
{/if}
```

### $app/paths

```ts
import { base, assets } from '$app/paths';

// base: base path from config (e.g., '/my-app')
// assets: assets URL (CDN or base path)

const href = `${base}/about`;
const imgSrc = `${assets}/images/logo.png`;
```

## svelte.config.js Options

```js
import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
export default {
  preprocess: vitePreprocess(),

  kit: {
    // Deployment adapter
    adapter: adapter({
      out: 'build',
      precompress: true,
      envPrefix: 'APP_'
    }),

    // Import aliases
    alias: {
      '$components': 'src/lib/components',
      '$server': 'src/lib/server',
      '$utils': 'src/lib/utils'
    },

    // CSRF protection
    csrf: {
      checkOrigin: true  // Verify Origin header (default: true)
    },

    // Environment variable prefix
    env: {
      publicPrefix: 'PUBLIC_',  // Default prefix for public vars
      privatePrefix: ''          // Default prefix for private vars
    },

    // Path configuration
    paths: {
      base: '',        // Base URL path
      assets: '',      // CDN URL for static assets
      relative: true   // Use relative paths in output
    },

    // Prerendering
    prerender: {
      concurrency: 1,
      crawl: true,
      entries: ['*'],
      handleHttpError: 'fail',
      handleMissingId: 'warn'
    },

    // App version (for $app/stores updated)
    version: {
      name: Date.now().toString(),
      pollInterval: 0  // ms, 0 = disabled
    },

    // Output directory
    outDir: '.svelte-kit'
  }
};
```

## Vite Configuration

```ts
// vite.config.ts
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],

  server: {
    port: 5173,
    host: true,    // Listen on all interfaces
    proxy: {
      '/external-api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/external-api/, '')
      }
    }
  },

  build: {
    target: 'es2022'
  },

  // Optimization settings
  optimizeDeps: {
    include: ['lodash-es']
  }
});
```

## .env Files

SvelteKit uses Vite's `.env` file loading:

| File | Loaded | Git |
|------|--------|-----|
| `.env` | Always | Commit |
| `.env.local` | Always | Gitignore |
| `.env.development` | `dev` only | Commit |
| `.env.production` | `build` only | Commit |
| `.env.development.local` | `dev` only | Gitignore |
| `.env.production.local` | `build` only | Gitignore |

Precedence: `.env.local` > `.env.[mode]` > `.env`

## Common Pitfalls

1. **Missing `PUBLIC_` prefix** — Client-accessible vars must start with `PUBLIC_`. SvelteKit blocks non-prefixed vars from client code.
2. **Using `process.env`** — Don't use `process.env` in SvelteKit. Use the `$env` modules instead.
3. **Static vs dynamic confusion** — Static vars are baked into the build. If you need per-environment config from the same build, use dynamic.
4. **Importing private in client code** — Importing from `$env/static/private` in a `.svelte` file causes a build error. Use it only in server files.
5. **Missing `.env` in production** — Static vars don't need `.env` at runtime (they're baked in). Dynamic vars do.

## Related

- Hooks → `06-hooks.md`
- Deployment → `12-deployment.md`
- Overview & Setup → `00-overview.md`
