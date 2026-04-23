# Cloudflare Pages & Static Assets

> Source: [developers.cloudflare.com/pages](https://developers.cloudflare.com/pages/)

## Table of Contents

- [Workers vs Pages](#workers-vs-pages)
- [Static Assets in Workers](#static-assets-in-workers)
- [Pages Functions](#pages-functions)
- [Pages Middleware](#pages-middleware)
- [Framework Integration](#framework-integration)
- [Build Configuration](#build-configuration)
- [Custom Routing](#custom-routing)
- [Environment Variables](#environment-variables)
- [Common Patterns](#common-patterns)

## Workers vs Pages

| Feature | Workers | Pages |
|---------|---------|-------|
| Static files | Via `[assets]` binding | Built-in |
| Server logic | Full Worker | Functions (file-based routing) |
| Git deploy | Via CI/CD | Built-in Git integration |
| Preview URLs | Manual | Automatic per branch |
| Framework support | Manual setup | First-class (Next.js, Astro, etc.) |

Pages is being unified into Workers — new projects can use Workers with static assets directly.

## Static Assets in Workers

Serve static files alongside Worker logic:

```toml
# wrangler.toml
name = "my-app"
main = "src/index.ts"
compatibility_date = "2026-04-23"

[assets]
directory = "./public"       # Static files directory
binding = "ASSETS"           # Optional: access assets programmatically
```

```typescript
interface Env {
  ASSETS: Fetcher;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // API routes handled by Worker
    if (url.pathname.startsWith("/api/")) {
      return handleAPI(request, env);
    }

    // Everything else served from static assets
    return env.ASSETS.fetch(request);
  },
};
```

### Asset Behavior

- Static assets are served with proper MIME types
- Assets are cached at the edge automatically
- `index.html` is served for directory paths
- 404 falls through to Worker logic if `serve_directly` is enabled

### Serve Directly

```toml
[assets]
directory = "./dist"

# Serve assets directly without invoking Worker (faster)
[assets.serve_directly]
enabled = true
```

When enabled, matching static files bypass the Worker entirely for maximum performance.

## Pages Functions

File-based routing for serverless functions:

```
my-project/
├── public/              # Static assets
│   ├── index.html
│   └── styles.css
├── functions/           # Server functions (auto-routed)
│   ├── api/
│   │   ├── users.ts     # /api/users
│   │   ├── users/
│   │   │   └── [id].ts  # /api/users/:id
│   │   └── health.ts    # /api/health
│   └── _middleware.ts   # Middleware (runs on all routes)
└── wrangler.toml
```

### Function Handler

```typescript
// functions/api/users.ts

interface Env {
  DB: D1Database;
}

// GET /api/users
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { results } = await context.env.DB.prepare("SELECT * FROM users").all();
  return Response.json(results);
};

// POST /api/users
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const body = await context.request.json<{ name: string; email: string }>();
  const result = await context.env.DB.prepare(
    "INSERT INTO users (name, email) VALUES (?, ?) RETURNING *",
  ).bind(body.name, body.email).first();
  return Response.json(result, { status: 201 });
};
```

### Dynamic Routes

```typescript
// functions/api/users/[id].ts

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const userId = context.params.id;
  const user = await context.env.DB.prepare("SELECT * FROM users WHERE id = ?")
    .bind(userId)
    .first();

  if (!user) return new Response("Not Found", { status: 404 });
  return Response.json(user);
};

export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const userId = context.params.id;
  await context.env.DB.prepare("DELETE FROM users WHERE id = ?")
    .bind(userId)
    .run();
  return new Response(null, { status: 204 });
};
```

### Catch-All Routes

```typescript
// functions/api/[...path].ts
export const onRequest: PagesFunction = async (context) => {
  const path = context.params.path; // string[]
  return Response.json({ path });
};
```

### EventContext (PagesFunction Parameter)

```typescript
interface EventContext<Env, Params, Data> {
  request: Request;
  env: Env;
  params: Params;           // URL parameters
  data: Data;               // Data from middleware
  next: () => Promise<Response>;  // Call next handler/middleware
  waitUntil: (promise: Promise<any>) => void;
  passThroughOnException: () => void;
}
```

## Pages Middleware

```typescript
// functions/_middleware.ts
export const onRequest: PagesFunction<Env> = async (context) => {
  // Run before the handler
  const start = Date.now();

  // Authentication
  const token = context.request.headers.get("Authorization");
  if (context.request.url.includes("/api/admin") && !token) {
    return new Response("Unauthorized", { status: 401 });
  }

  // Call the next handler
  const response = await context.next();

  // Run after the handler
  const duration = Date.now() - start;
  response.headers.set("X-Response-Time", `${duration}ms`);

  return response;
};
```

### Nested Middleware

```
functions/
├── _middleware.ts        # Runs on ALL routes
└── api/
    ├── _middleware.ts    # Runs on /api/* routes only
    ├── public/
    │   └── health.ts    # No auth needed
    └── admin/
        ├── _middleware.ts  # Extra auth for /api/admin/*
        └── users.ts
```

Middleware executes from outermost to innermost, then back up.

## Framework Integration

### Cloudflare Vite Plugin (Recommended)

```bash
npm install @cloudflare/vite-plugin
```

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import { cloudflare } from "@cloudflare/vite-plugin";

export default defineConfig({
  plugins: [cloudflare()],
});
```

### Next.js on Pages

```bash
npm create cloudflare@latest my-nextjs-app -- --framework next
```

### Astro on Pages

```bash
npm create cloudflare@latest my-astro-app -- --framework astro
```

### SvelteKit on Pages

```bash
npm create cloudflare@latest my-svelte-app -- --framework svelte
```

## Build Configuration

```toml
# wrangler.toml for Pages
name = "my-site"
compatibility_date = "2026-04-23"

[build]
command = "npm run build"

[assets]
directory = "./dist"
```

### Pages-specific build settings (dashboard or wrangler):

```toml
# Build output directory varies by framework:
# Next.js: .next
# Astro: dist
# SvelteKit: .svelte-kit/cloudflare
# Vite/React: dist
```

## Custom Routing

### _routes.json

Control which routes invoke Functions vs serve static assets:

```json
{
  "version": 1,
  "include": ["/api/*", "/auth/*"],
  "exclude": ["/assets/*", "/*.ico", "/*.png"]
}
```

- `include` — Routes that invoke Functions
- `exclude` — Routes served as static assets (bypass Functions)
- Exclusions take precedence over inclusions

### _headers

Set custom headers for static assets:

```
/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*.html
  Cache-Control: public, max-age=0, must-revalidate
  X-Frame-Options: DENY
```

### _redirects

```
/old-page /new-page 301
/blog/* /posts/:splat 302
/docs https://docs.example.com 301
```

## Environment Variables

```bash
# Set via Wrangler
wrangler pages secret put API_KEY

# Or set via dashboard
# Settings > Environment Variables
```

```toml
# wrangler.toml
[vars]
PUBLIC_URL = "https://example.com"

[env.preview.vars]
PUBLIC_URL = "https://preview.example.com"
```

## Common Patterns

### SPA Fallback

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Try static assets first
    if (url.pathname.startsWith("/api/")) {
      return handleAPI(request, env);
    }

    const assetResponse = await env.ASSETS.fetch(request);
    if (assetResponse.status !== 404) {
      return assetResponse;
    }

    // SPA fallback — serve index.html for all unknown routes
    return env.ASSETS.fetch(new Request(new URL("/index.html", request.url)));
  },
};
```

### Hybrid SSR + Static

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Server-rendered pages
    if (url.pathname === "/" || url.pathname.startsWith("/blog/")) {
      const html = await renderPage(url.pathname, env);
      return new Response(html, {
        headers: { "Content-Type": "text/html", "Cache-Control": "s-maxage=60" },
      });
    }

    // Static assets
    return env.ASSETS.fetch(request);
  },
};
```

## Common Pitfalls

- **Functions directory** — Pages Functions must be in a `functions/` directory (not `src/`). File names map directly to routes.
- **Export names** — Use `onRequestGet`, `onRequestPost`, etc. for method-specific handlers. `onRequest` handles all methods.
- **_routes.json** — Exclude static asset patterns to avoid unnecessary Function invocations.
- **Preview deployments** — Each git branch gets a unique preview URL. Preview uses `env.preview` variables.
- **Build output** — Make sure `[assets].directory` points to your framework's build output.
