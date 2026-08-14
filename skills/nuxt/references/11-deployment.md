# Nuxt — Deployment

> Source: [nuxt.com/docs/getting-started/deployment](https://nuxt.com/docs/getting-started/deployment)

## Table of Contents

- [Rendering Modes](#rendering-modes)
- [Building for Production](#building-for-production)
- [Nitro Presets](#nitro-presets)
- [Node.js Server](#nodejs-server)
- [Static Hosting](#static-hosting)
- [Serverless Providers](#serverless-providers)
- [Edge Providers](#edge-providers)
- [Hybrid Rendering](#hybrid-rendering)
- [Prerendering](#prerendering)
- [Common Pitfalls](#common-pitfalls)

## Rendering Modes

| Mode | Command | Output | Use Case |
|------|---------|--------|----------|
| SSR (default) | `nuxt build` | Server + client bundles | Dynamic content, SEO |
| SSG | `nuxt generate` | Static HTML files | Blogs, docs, marketing |
| SPA | `ssr: false` + `nuxt build` | Client-only bundle | Dashboards, admin panels |
| Hybrid | Route rules | Mix of SSR/SSG/SPA | Complex apps |

## Building for Production

### SSR Build (Default)

```bash
nuxt build
```

Produces `.output/` directory with:
- Server entry point (`.output/server/index.mjs`)
- Client bundles and static assets (`.output/public/`)
- Runtime configuration (`.output/nitro.json`)

### Static Site Generation

```bash
nuxt generate
```

Pre-renders all routes to static HTML. Equivalent to `nuxt build --prerender`.

### Preview Production Build

```bash
nuxt preview
```

Starts a local server using the production build for testing before deployment.

## Nitro Presets

Nitro presets configure the server for specific hosting platforms. Set via:

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'node-server' // or any preset name
  }
})
```

Or via environment variable:

```bash
NITRO_PRESET=cloudflare-pages nuxt build
```

### Common Presets

| Preset | Platform | Notes |
|--------|----------|-------|
| `node-server` | Any Node.js host | Default, most compatible |
| `node-cluster` | Node.js with clustering | Multi-core servers |
| `vercel` | Vercel | Auto-detected |
| `netlify` | Netlify | Auto-detected |
| `cloudflare-pages` | Cloudflare Pages | Edge runtime |
| `cloudflare-module` | Cloudflare Workers | Edge runtime |
| `aws-lambda` | AWS Lambda | Via API Gateway |
| `firebase` | Firebase Hosting | Cloud Functions |
| `deno-server` | Deno Deploy | Deno runtime |
| `bun` | Bun runtime | Bun server |
| `static` | Any static host | Pre-rendered only |

## Node.js Server

The default deployment target. Works on any Node.js hosting:

```bash
# Build
nuxt build

# Run
NODE_ENV=production node .output/server/index.mjs
```

### Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` or `NITRO_PORT` | `3000` | Server port |
| `HOST` or `NITRO_HOST` | `0.0.0.0` | Server host |
| `NITRO_SSL_CERT` | — | SSL certificate path |
| `NITRO_SSL_KEY` | — | SSL key path |

### PM2 Process Manager

```javascript
// ecosystem.config.cjs
module.exports = {
  apps: [
    {
      name: 'NuxtApp',
      port: 3000,
      exec_mode: 'cluster',
      instances: 'max',
      script: './.output/server/index.mjs'
    }
  ]
}
```

```bash
pm2 start ecosystem.config.cjs
```

### Cluster Mode

```bash
NITRO_PRESET=node_cluster nuxt build
```

Distributes workload across CPU cores using round-robin strategy.

## Static Hosting

### Full Static Generation (SSG)

```bash
nuxt generate
```

All pages pre-rendered to HTML at build time. Deploy the `.output/public/` directory to any static host (GitHub Pages, Netlify, Vercel, S3, etc.).

### Client-Side Only (SPA)

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  ssr: false
})
```

```bash
nuxt generate  # Outputs index.html + JS bundles
```

### Fallback Pages

Nuxt generates fallback pages for client-side routing:
- `200.html` — SPA fallback for unmatched routes
- `404.html` — Not-found fallback (maintains 404 status)

Configure your hosting to serve `200.html` for all unmatched routes.

## Serverless Providers

### Vercel

Auto-detected when deploying via Vercel:

```bash
# No special config needed — just deploy
vercel
```

Or set explicitly:

```typescript
export default defineNuxtConfig({
  nitro: { preset: 'vercel' }
})
```

### Netlify

Auto-detected on Netlify:

```toml
# netlify.toml
[build]
  command = "nuxt build"
  publish = ".output/public"
```

### AWS Lambda

```typescript
export default defineNuxtConfig({
  nitro: { preset: 'aws-lambda' }
})
```

Deploy the `.output/server/` as a Lambda function with API Gateway.

### Firebase

```typescript
export default defineNuxtConfig({
  nitro: { preset: 'firebase' }
})
```

```bash
firebase deploy
```

## Edge Providers

### Cloudflare Pages

```typescript
export default defineNuxtConfig({
  nitro: { preset: 'cloudflare-pages' }
})
```

```bash
npx wrangler pages deploy .output/public
```

### Cloudflare Workers

```typescript
export default defineNuxtConfig({
  nitro: { preset: 'cloudflare-module' }
})
```

### Deno Deploy

```typescript
export default defineNuxtConfig({
  nitro: { preset: 'deno-server' }
})
```

## Hybrid Rendering

Mix rendering strategies per route using `routeRules`:

```typescript
export default defineNuxtConfig({
  routeRules: {
    // Static pages — prerendered at build time
    '/': { prerender: true },
    '/about': { prerender: true },

    // SSR pages — rendered on each request
    '/dashboard/**': { ssr: true },

    // SPA pages — client-side rendering only
    '/admin/**': { ssr: false },

    // ISR — incremental static regeneration
    '/blog/**': { isr: 3600 },       // Revalidate every hour
    '/products/**': { isr: true },   // Revalidate on next request

    // Static with SWR — stale-while-revalidate
    '/api/stats': { swr: 600 },      // Cache for 10 minutes

    // CORS headers
    '/api/**': {
      cors: true,
      headers: {
        'Access-Control-Allow-Origin': '*'
      }
    },

    // Redirects
    '/old-page': { redirect: '/new-page' },
    '/old-blog/**': { redirect: '/blog/**' }
  }
})
```

### Route Rule Options

| Rule | Effect |
|------|--------|
| `prerender: true` | Pre-render at build time |
| `ssr: false` | Client-side rendering only |
| `isr: number` | Incremental static regeneration (seconds) |
| `swr: number` | Stale-while-revalidate caching |
| `cors: true` | Add CORS headers |
| `redirect: string` | HTTP redirect |
| `headers: object` | Custom response headers |
| `appLayout: string` | Set layout for matched routes |

## Prerendering

### Selective Prerendering

Prerender specific routes:

```typescript
export default defineNuxtConfig({
  routeRules: {
    '/': { prerender: true },
    '/about': { prerender: true },
    '/blog/**': { prerender: true }
  }
})
```

### Prerender Hints

Nuxt crawls `<NuxtLink>` targets to discover routes for prerendering. For dynamic routes not linked from crawlable pages, add them manually:

```typescript
export default defineNuxtConfig({
  nitro: {
    prerender: {
      routes: ['/sitemap.xml', '/robots.txt'],
      crawlLinks: true  // Follow links in prerendered pages
    }
  }
})
```

### Ignoring Routes

```typescript
export default defineNuxtConfig({
  nitro: {
    prerender: {
      ignore: ['/dynamic', '/admin']
    }
  }
})
```

### Build-Time Data

During prerendering, `useFetch` and `useAsyncData` make real API calls. Ensure your API endpoints are available during the build.

## Common Pitfalls

- **Missing static fallback** — SPA and hybrid deployments need the hosting platform to serve `200.html` for client-side routes. Without this, direct URL access returns 404.
- **Environment variables in static builds** — `runtimeConfig` values are baked in at build time for static/prerendered pages. Use `NUXT_PUBLIC_*` variables during `nuxt generate`.
- **Cloudflare script injection** — Cloudflare's "Rocket Loader" and "Email Address Obfuscation" features inject scripts that break hydration. Disable them in Cloudflare dashboard.
- **Prerendering API dependencies** — `nuxt generate` calls your API routes during build. If the API server isn't running, prerendering fails. Use mock data or ensure the API is accessible.
- **ISR without provider support** — `isr` route rules require hosting provider support (Vercel, Netlify). On a plain Node.js server, use `swr` instead.
- **Subpath deployment** — When deploying to a subpath (e.g., `/app/`), set `app.baseURL: '/app/'` in `nuxt.config.ts` or use `NUXT_APP_BASE_URL`.
