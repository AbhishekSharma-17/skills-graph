# Rendering Modes

> Source: https://docs.astro.build/en/guides/on-demand-rendering/

Astro supports three rendering strategies:

1. **Static (SSG)** — generate HTML at build time. Default.
2. **On-Demand (SSR)** — generate HTML per request at an adapter (Node, Cloudflare, Vercel, etc.).
3. **Hybrid** — both in the same project, controlled per route.

Astro 5+ simplified this: you always configure one `output` mode, and then **opt individual routes out** via `export const prerender`.

## Setting the Output Mode

```js
// astro.config.mjs
export default defineConfig({
  output: "static",            // Default — no adapter required
});
```

```js
export default defineConfig({
  output: "server",            // All routes are on-demand by default
  adapter: node({ mode: "standalone" }),
});
```

## Per-Route Overrides

Regardless of the project-wide `output`, individual pages can flip their mode:

```astro
---
// src/pages/about.astro
export const prerender = true;      // Force static, even in "server" project
---
```

```astro
---
// src/pages/dashboard.astro
export const prerender = false;     // Force SSR, even in "static" project
---
```

**For `prerender = false` to work, your project must have an adapter configured.** Static-only projects cannot have any on-demand routes.

## When to Use Each

| Use Case | Mode |
|----------|------|
| Blog, docs, marketing | Static (SSG) |
| Personalized dashboards, authenticated pages | On-demand (SSR) |
| Mostly-static site with a few dynamic pages (search, user profile) | Hybrid (`output: "server"` + `prerender = true` on static routes) |
| Mostly-dynamic app with a few cached marketing pages | Hybrid (`output: "server"` + default; selected static via `prerender = true`) |

## Static Output

```js
export default defineConfig({
  output: "static",
});
```

- Build produces `dist/` with HTML + assets.
- Deploy anywhere (Netlify, Vercel, Cloudflare Pages, GitHub Pages, S3+CloudFront, Nginx, static file hosting).
- Dynamic routes require `getStaticPaths()`.
- `Astro.redirect` and `Astro.request` are unavailable in pure static mode (except in build-time contexts).

## On-Demand (Server) Output

```js
import node from "@astrojs/node";
export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),
});
```

- Every route generates HTML per request.
- `Astro.request`, `Astro.redirect`, `Astro.clientAddress`, `Astro.cookies` all fully functional.
- Middleware runs per request.
- Actions and endpoints execute at request time.

### Adapter Matrix

| Adapter | Package | Runtime |
|---------|---------|---------|
| Node | `@astrojs/node` | Node.js (standalone server or middleware) |
| Cloudflare | `@astrojs/cloudflare` | Workers / Pages Functions |
| Vercel | `@astrojs/vercel` | Vercel Edge or Serverless Functions |
| Netlify | `@astrojs/netlify` | Netlify Functions / Edge |
| Deno | `@deno/astro-adapter` | Deno Deploy |
| Bun | `@astrojs/bun` *(community)* | Bun runtime |

Configure via `astro add <adapter>` which installs and updates `astro.config.mjs` for you.

## Hybrid Rendering — Full Example

```js
// astro.config.mjs
import { defineConfig } from "astro/config";
import cloudflare from "@astrojs/cloudflare";

export default defineConfig({
  output: "server",
  adapter: cloudflare(),
});
```

```astro
---
// src/pages/index.astro — marketing home, prerender for speed
export const prerender = true;
---
<h1>Welcome</h1>
```

```astro
---
// src/pages/blog/[slug].astro — prerender each post at build time
import { getCollection } from "astro:content";
export const prerender = true;
export async function getStaticPaths() {
  const posts = await getCollection("blog");
  return posts.map((p) => ({ params: { slug: p.id }, props: { post: p } }));
}
const { post } = Astro.props;
---
```

```astro
---
// src/pages/dashboard.astro — dynamic, requires session
const session = Astro.cookies.get("session");
if (!session) return Astro.redirect("/login");
---
```

In this setup:
- `/` and `/blog/*` are emitted as HTML at build time.
- `/dashboard` is rendered per request at the Cloudflare edge.

## Accessing Request Data

**Only available in on-demand routes:**

```astro
---
// SSR-only
const method = Astro.request.method;
const userAgent = Astro.request.headers.get("user-agent");
const ip = Astro.clientAddress;
const cookie = Astro.cookies.get("theme")?.value;

// Set response
Astro.response.headers.set("Cache-Control", "no-store");
Astro.response.status = 200;
---
```

In prerendered pages, `Astro.request` is a synthetic request object — it does not reflect the actual visitor's request (because the page was built once at build time).

## Partial Prerendering Pattern

Need a page that is **mostly static** but with personalized parts? Combine prerendering with **Server Islands** (see `05-islands-and-client-directives.md`):

```astro
---
// src/pages/index.astro
export const prerender = true;
import Recommendations from "~/components/Recommendations.astro";
---
<h1>Static marketing content</h1>

<Recommendations server:defer>
  <p slot="fallback">Loading…</p>
</Recommendations>
```

The shell is cached globally; `<Recommendations>` is fetched per-visitor and streamed in.

## Performance Implications

| Mode | Cold start | Cache-friendly | Dynamic data |
|------|-----------|----------------|--------------|
| Static | 0 ms (CDN hit) | Yes (public CDN) | Requires rebuild OR client-side fetch |
| On-demand (edge) | ~5-50 ms | Partial (HTTP cache headers) | Fresh per request |
| On-demand (Node serverless) | 100-500 ms cold | Partial | Fresh per request |
| Hybrid | Mix | Mix | Mix |

**Rule of thumb:** prerender aggressively. Only opt out of prerendering when you need per-request data.

## Common Pitfalls

- **`output: "static"` + `prerender = false` on any route** → build error: no adapter configured.
- **Using `Astro.cookies.set()` in a prerendered page** → cookies have no effect; the HTML is cached and served without going through Astro.
- **Forgetting `getStaticPaths` for a dynamic prerendered route** → build error.
- **Expecting middleware to run on prerendered routes** → middleware only runs for on-demand routes and only in dev mode for prerendered routes (for HMR). In production, prerendered HTML is served directly by the CDN.
- **Switching output modes mid-project without clearing `.astro/` cache** → occasionally Astro's type generation gets confused. Run `astro sync` after changes.
- **Using `astro preview` to test SSR** → `astro preview` runs the adapter's local preview mode; make sure your env vars are set for it.
