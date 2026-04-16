# Integrations & Adapters

> Source: https://docs.astro.build/en/guides/integrations-guide/ and https://astro.build/integrations

Astro is composable via **integrations** — small plugins that extend the build pipeline with new file types, new components, new endpoints, or deployment targets. **Adapters** are a specific kind of integration that enables SSR on a particular platform.

## Table of Contents

- [The `astro add` CLI](#the-astro-add-cli)
- [Framework Integrations](#framework-integrations)
- [Tailwind CSS v4](#tailwind-css-v4)
- [MDX](#mdx)
- [Common Integrations](#common-integrations)
- [Adapters](#adapters)
- [Writing a Custom Integration](#writing-a-custom-integration)
- [Common Pitfalls](#common-pitfalls)

## The `astro add` CLI

The fast path — installs the package, updates `astro.config.mjs`, updates `tsconfig.json` where needed, and installs framework types:

```bash
npx astro add react tailwind mdx
npx astro add @astrojs/node
npx astro add @astrojs/cloudflare
```

The `--yes` flag skips prompts. Use it in CI.

## Framework Integrations

Mix-and-match in one project. Each integration enables its framework's `.jsx`/`.vue`/`.svelte` files.

```bash
npx astro add react          # @astrojs/react
npx astro add vue            # @astrojs/vue
npx astro add svelte         # @astrojs/svelte
npx astro add solid          # @astrojs/solid-js
npx astro add preact         # @astrojs/preact
npx astro add lit            # @astrojs/lit
npx astro add alpinejs       # @astrojs/alpinejs
```

Post-install config:

```js
// astro.config.mjs
import react from "@astrojs/react";
import svelte from "@astrojs/svelte";

export default defineConfig({
  integrations: [
    react({ include: ["**/react/*"] }),       // Scope to specific paths
    svelte({ include: ["**/svelte/*"] }),
  ],
});
```

## Tailwind CSS v4

As of Astro 4.x+, the recommended approach is the **Tailwind Vite plugin** (Tailwind v4 style), not the legacy `@astrojs/tailwind` integration.

```bash
npm install tailwindcss @tailwindcss/vite
```

```js
// astro.config.mjs
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  vite: { plugins: [tailwindcss()] },
});
```

```css
/* src/styles/global.css */
@import "tailwindcss";
```

```astro
---
import "~/styles/global.css";
---
<h1 class="text-4xl font-bold text-sky-500">Hello</h1>
```

The old integration still works but is frozen at Tailwind v3. New projects should use v4 + Vite plugin — much faster.

## MDX

For Markdown + JSX (embed components in content):

```bash
npx astro add mdx
```

```mdx
---
title: "Interactive Post"
---
import Counter from "../../components/Counter.jsx";

# Welcome

Here's a counter you can click:

<Counter client:load initialCount={3} />
```

MDX works with Content Collections automatically. See `04-content-collections.md`.

## Common Integrations

### `@astrojs/sitemap`

Generates `sitemap-index.xml` + `sitemap-*.xml` at build time.

```bash
npx astro add sitemap
```

```js
// astro.config.mjs
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://example.com",   // REQUIRED for sitemap
  integrations: [sitemap({
    filter: (page) => !page.includes("/admin/"),
    i18n: {
      defaultLocale: "en",
      locales: { en: "en-US", fr: "fr-FR" },
    },
  })],
});
```

### `@astrojs/rss`

RSS feed generation via an endpoint (see `09-endpoints-and-api-routes.md` for the pattern).

### `@astrojs/partytown`

Runs third-party scripts (analytics, Hotjar) inside a web worker so they don't block the main thread.

```bash
npx astro add partytown
```

```astro
<script type="text/partytown" src="https://www.googletagmanager.com/gtag/js?id=G-XXX"></script>
```

### `@astrojs/db`

Astro's built-in database (powered by libSQL/Turso), with type-safe schema + migrations.

```bash
npx astro add db
```

```ts
// db/config.ts
import { defineDb, defineTable, column } from "astro:db";

const Comment = defineTable({
  columns: {
    id: column.number({ primaryKey: true, autoIncrement: true }),
    postId: column.text(),
    body: column.text(),
    createdAt: column.date({ default: new Date() }),
  },
});

export default defineDb({ tables: { Comment } });
```

```astro
---
import { db, Comment } from "astro:db";
const comments = await db.select().from(Comment);
---
```

### `astro-icon`

Tree-shaken SVG icons from Iconify — hundreds of thousands of icons, ship only what you use.

```bash
npm install astro-icon @iconify-json/lucide
```

```js
import icon from "astro-icon";

export default defineConfig({
  integrations: [icon({ include: { lucide: ["home", "settings"] } })],
});
```

```astro
---
import { Icon } from "astro-icon/components";
---
<Icon name="lucide:home" class="w-6 h-6" />
```

## Adapters

Adapters transform your build output for a specific runtime. Required for `output: "server"` or when any route is non-prerendered.

### Node

```bash
npx astro add node
```

```js
import node from "@astrojs/node";

export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),   // or "middleware" to embed in Express/Fastify
});
```

Build produces `dist/server/entry.mjs`. Run: `node dist/server/entry.mjs`.

### Cloudflare

```bash
npx astro add cloudflare
```

```js
import cloudflare from "@astrojs/cloudflare";

export default defineConfig({
  output: "server",
  adapter: cloudflare({
    imageService: "compile",                 // "compile" | "cloudflare" | "passthrough"
    platformProxy: { enabled: true },         // KV / R2 / D1 bindings in dev
  }),
});
```

Deploy with `wrangler deploy` or Cloudflare Pages. Runtime bindings (KV, R2, D1) available via `Astro.locals.runtime.env`.

### Vercel

```bash
npx astro add vercel
```

```js
import vercel from "@astrojs/vercel";

export default defineConfig({
  output: "server",
  adapter: vercel({
    imageService: true,
    webAnalytics: { enabled: true },
    isr: {
      expiration: 60 * 60,                   // Revalidate hourly
      exclude: ["/preview/[...path]"],
    },
  }),
});
```

Deploys to Vercel Edge or Serverless Functions based on your route usage.

### Netlify

```bash
npx astro add netlify
```

```js
import netlify from "@astrojs/netlify";

export default defineConfig({
  output: "server",
  adapter: netlify({ edgeMiddleware: true }),
});
```

### Other Adapters

- `@deno/astro-adapter` — Deno Deploy.
- `@astrojs/bun` (community) — Bun runtime.
- `astro-aws` (community) — AWS Lambda / Amplify.
- `@astrojs/aws` — official AWS adapter (beta).

## Writing a Custom Integration

Integrations follow a lifecycle-hook pattern:

```ts
// src/integrations/my-integration.ts
import type { AstroIntegration } from "astro";

export default function myIntegration(options: { prefix?: string } = {}): AstroIntegration {
  return {
    name: "my-integration",
    hooks: {
      "astro:config:setup": ({ updateConfig, injectRoute, injectScript, logger }) => {
        logger.info(`Setting up with prefix: ${options.prefix ?? "/"}`);

        injectRoute({
          pattern: `${options.prefix ?? ""}/_my-endpoint`,
          entrypoint: new URL("./routes/endpoint.ts", import.meta.url).pathname,
        });

        injectScript("page", `console.log("hello from my integration")`);

        updateConfig({
          vite: { define: { __MY_FLAG__: JSON.stringify(true) } },
        });
      },
      "astro:build:done": ({ dir, routes }) => {
        // Post-process build artifacts
      },
    },
  };
}
```

### Common Hooks

| Hook | When it fires |
|------|---------------|
| `astro:config:setup` | Before config resolves — use `updateConfig`, `injectRoute`, `injectScript` |
| `astro:config:done` | After config resolves — inspect final config |
| `astro:server:setup` | Dev server starting |
| `astro:build:setup` | Before production build |
| `astro:build:generated` | After pages generated but before output is finalized |
| `astro:build:done` | Build complete — inspect `dir` and `routes` |

## Common Pitfalls

- **Order of integrations matters** — integrations that inject routes should run before integrations that process them. Tailwind typically goes last; adapters always last.
- **Using `@astrojs/tailwind` + Tailwind v4** — incompatible. Use the Vite plugin instead.
- **Hydration mismatch with framework SSR** — class instances / `Date.now()` / random IDs generated during SSR differ on the client. Use `client:only` or make the rendering deterministic.
- **Forgetting `site` in config** — breaks sitemap, RSS, canonical URLs, OG tags.
- **Cloudflare runtime APIs (KV, D1, R2) missing in dev** — enable `platformProxy: { enabled: true }` in the adapter config.
- **Vercel adapter + custom image domains** — update `image.domains` in `astro.config.mjs`; Vercel doesn't auto-allow them.
