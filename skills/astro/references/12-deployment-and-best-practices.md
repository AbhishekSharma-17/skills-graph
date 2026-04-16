# Deployment & Best Practices

> Source: https://docs.astro.build/en/guides/deploy/ and community best practices 2026

## Table of Contents

- [Deployment Checklist](#deployment-checklist)
- [Static Hosting](#static-hosting)
- [Serverless / Edge Hosting](#serverless--edge-hosting)
- [Images](#images)
- [Performance Best Practices](#performance-best-practices)
- [SEO Checklist](#seo-checklist)
- [Security Headers](#security-headers)
- [Monitoring](#monitoring)
- [Common Pitfalls](#common-pitfalls)

## Deployment Checklist

Before the first deploy:

- [ ] `site` is set in `astro.config.mjs` to the production URL.
- [ ] `base` is set if deploying to a subpath (e.g., `/docs/`).
- [ ] `output` is correct for your needs (`static` or `server`).
- [ ] Adapter installed and configured if using SSR.
- [ ] All `PUBLIC_*` env vars declared in `astro:env` schema.
- [ ] Secrets (`DATABASE_URL`, API keys) set in the hosting platform — **never in committed `.env`**.
- [ ] `astro check` passes.
- [ ] `astro build` succeeds locally.
- [ ] `astro preview` (or adapter-specific preview) verified.
- [ ] `sitemap.xml` and `robots.txt` generated / configured.
- [ ] 404 and 500 pages exist.
- [ ] Analytics configured (Partytown'd or Vercel/Cloudflare Web Analytics).

## Static Hosting

Any static file host works. Deploy `dist/` after `npm run build`.

### GitHub Pages

```yaml
# .github/workflows/deploy.yml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-pages-artifact@v3
        with: { path: ./dist }
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

Set `site: "https://<user>.github.io"` and `base: "/<repo>/"` for project sites.

### Cloudflare Pages (Static)

1. Connect repo in Pages dashboard.
2. Build command: `npm run build`. Output directory: `dist`.
3. Environment variables: add `NODE_VERSION=22`.

### Netlify / Vercel (Static)

Zero config — they auto-detect Astro and set defaults. Push to Git and deploy previews are automatic.

### S3 + CloudFront

```bash
aws s3 sync dist/ s3://my-bucket/ --delete
aws cloudfront create-invalidation --distribution-id XXX --paths "/*"
```

Use `trailingSlash: "always"` with `build.format: "directory"` so `/about/` resolves to `about/index.html` cleanly with S3 website hosting.

## Serverless / Edge Hosting

### Cloudflare Workers (recommended for most SSR use cases)

```js
import cloudflare from "@astrojs/cloudflare";

export default defineConfig({
  output: "server",
  adapter: cloudflare({
    platformProxy: { enabled: true },
  }),
});
```

Deploy with Wrangler or Pages. Access KV, R2, D1:

```ts
// src/middleware.ts
export const onRequest = defineMiddleware(async (ctx, next) => {
  const { KV } = ctx.locals.runtime.env;
  const cached = await KV.get(ctx.url.pathname);
  // ...
});
```

Type the runtime bindings via `src/env.d.ts`:

```ts
type Runtime = import("@astrojs/cloudflare").Runtime<Env>;
declare namespace App {
  interface Locals extends Runtime {
    user: { id: string } | null;
  }
}
```

### Vercel

Push to Git; Vercel auto-detects Astro. Configure ISR and edge in the adapter options. Set secrets via the Vercel dashboard or `vercel env`.

### Node (your own server, Docker, PM2)

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS run
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./
ENV HOST=0.0.0.0 PORT=4321
EXPOSE 4321
CMD ["node", "dist/server/entry.mjs"]
```

## Images

Astro's built-in image service optimizes local and remote images at build/request time.

### Local Images (recommended)

```astro
---
import { Image } from "astro:assets";
import hero from "~/assets/hero.jpg";
---
<Image src={hero} alt="Hero" widths={[480, 800, 1200]} sizes="(max-width: 768px) 100vw, 800px" />
```

Generates AVIF/WebP, sets `width`/`height`, emits a responsive `srcset`.

### Remote Images

Must be allowlisted:

```js
// astro.config.mjs
export default defineConfig({
  image: {
    domains: ["images.unsplash.com"],
    remotePatterns: [{ protocol: "https", hostname: "**.example.com" }],
  },
});
```

```astro
<Image src="https://images.unsplash.com/photo-xyz" alt="x" width={800} height={600} />
```

### `<Picture>` for Art Direction

```astro
---
import { Picture } from "astro:assets";
import hero from "~/assets/hero.jpg";
---
<Picture src={hero} alt="Hero" formats={["avif", "webp"]} widths={[480, 800, 1200]} />
```

## Performance Best Practices

### Audit Hydration Cost

Every `client:load` adds to the critical path. Run:

```bash
npm run build
du -sh dist/_astro/
```

Big `_astro/` folder = lots of JS. Demote `client:load` to `client:visible` where possible.

### Prefer `.astro` Over Framework Components for Static Content

A React `<Button>` with `client:load` ships React runtime + the button. A `.astro` `<Button>` ships zero JS.

### Enable Prefetching

```js
export default defineConfig({
  prefetch: { prefetchAll: true, defaultStrategy: "viewport" },
});
```

### Compress CSS and JS

Astro + Vite do this by default. Verify `dist/_astro/*.css` and `*.js` are minified.

### Use `transition:persist` for Third-Party Widgets

Reinitialization on every nav is expensive; persist long-running widgets.

### Image Discipline

- Always set `width` and `height` (or use imported images which set them automatically). Prevents CLS.
- Use `loading="eager"` only for above-the-fold hero images.
- Use `loading="lazy"` (the default in `<Image>`) for everything else.

## SEO Checklist

Every page should have:

```astro
---
const canonical = new URL(Astro.url.pathname, Astro.site).href;
---
<head>
  <title>{title} — My Site</title>
  <meta name="description" content={description} />
  <link rel="canonical" href={canonical} />
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <meta property="og:image" content={ogImage} />
  <meta property="og:url" content={canonical} />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="robots" content="index,follow" />
</head>
```

Additionally:

- `@astrojs/sitemap` integration installed and `site` configured.
- `src/pages/robots.txt.ts` or `public/robots.txt`.
- JSON-LD structured data where relevant (articles, products).
- View transitions enabled for smoother UX signals.
- Minimal layout shift — use `<Image>` with intrinsic dimensions.

## Security Headers

Set via middleware (see `08-middleware.md`) or CDN rules. A good baseline:

```ts
response.headers.set("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload");
response.headers.set("X-Content-Type-Options", "nosniff");
response.headers.set("X-Frame-Options", "DENY");
response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
response.headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
response.headers.set(
  "Content-Security-Policy",
  "default-src 'self'; img-src 'self' data: https:; script-src 'self'; style-src 'self' 'unsafe-inline'",
);
```

**Astro 6 introduces a stable `experimental.csp` option** that auto-generates per-page nonces and hashes.

## Monitoring

- **Cloudflare Web Analytics** / **Vercel Analytics** — zero-JS (or lightweight) drop-ins that report Core Web Vitals without cookies.
- **Sentry** — browser + server error reporting; the official `@sentry/astro` integration wraps both.
- **OpenTelemetry** — for custom instrumentation of endpoints/actions. See the `opentelemetry` skill for patterns.
- **Logs** — adapter-specific: `wrangler tail` for Workers, Vercel Logs, Netlify Function Logs.

## Common Pitfalls

- **Missing `site` → broken sitemap, RSS, and canonical URLs.**
- **Prerendered pages with dynamic data** — if you see stale prices / stock levels, the page was baked at build time. Switch to `prerender = false` or use Server Islands.
- **Environment variable shadowing** — `PUBLIC_*` vars are inlined at build. Changing them requires a rebuild, not just a restart.
- **Adapter not reinstalled after upgrade** — `npm run build` complains about missing entry point. Re-run `astro add <adapter>`.
- **Server islands on pure-static projects** — require `output: "server"` or `"hybrid"`.
- **`astro preview` ≠ production** — it uses `@astrojs/node` for previewing but may miss adapter-specific behaviors. Deploy to a staging env for full verification.
- **Static 404 not working on some hosts** — Netlify/Vercel serve `404.html` automatically; S3 + CloudFront require explicit error page mapping.
- **Not pruning `client:*` directives** before launch — audit all islands; remove or demote any that don't truly need instant hydration.
