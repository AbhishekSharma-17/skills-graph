# Bun — Frontend Development

> Source: [bun.sh/docs/bundler/html](https://bun.sh/docs/bundler/html) | [bun.sh/docs/bundler/fullstack](https://bun.sh/docs/bundler/fullstack)

## Table of Contents

- [Overview](#overview)
- [HTML Imports](#html-imports)
- [Zero-Config Frontend Development](#zero-config-frontend-development)
- [Fullstack Dev Server](#fullstack-dev-server)
- [Hot Module Replacement](#hot-module-replacement)
- [React Fast Refresh](#react-fast-refresh)
- [Asset Pipeline](#asset-pipeline)
- [Framework Integration](#framework-integration)
- [Production Builds](#production-builds)
- [Environment Variables in Frontend Code](#environment-variables-in-frontend-code)
- [Proxy Configuration for API Backends](#proxy-configuration-for-api-backends)
- [Common Fullstack Patterns](#common-fullstack-patterns)
- [Comparison with Vite and Webpack](#comparison-with-vite-and-webpack)
- [Common Pitfalls](#common-pitfalls)

## Overview

Bun includes a built-in frontend development server and bundler requiring zero configuration. Import HTML files in server code and Bun automatically bundles, serves, and hot-reloads all referenced JS, TS, CSS, and assets — no Vite, Webpack, or Parcel needed.

Two modes:
- **Standalone**: `bun ./index.html` — frontend-only app with HMR
- **Fullstack**: import HTML files inside `Bun.serve()` — integrated frontend + API server

## HTML Imports

```typescript
import homepage from "./index.html";
// Returns an HTMLBundle object Bun.serve() understands
```

```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
  <title>My App</title>
  <link rel="stylesheet" href="./styles/main.css" />
</head>
<body>
  <div id="root"></div>
  <script type="module" src="./src/index.tsx"></script>
</body>
</html>
```

Bun automatically bundles all `<script>` and `<link>` references, handles TypeScript and JSX/TSX, processes CSS `@import`, and content-hashes static assets.

## Zero-Config Frontend Development

```bash
# Start dev server with HMR — no config files needed
bun ./index.html
# Serves at http://localhost:3000, HMR enabled
```

```html
<!-- index.html — everything you need -->
<!DOCTYPE html>
<html>
<head><link rel="stylesheet" href="./app.css" /></head>
<body>
  <div id="app"></div>
  <script type="module" src="./app.tsx"></script>
</body>
</html>
```

```typescript
// app.tsx — TypeScript + JSX works out of the box
import { createRoot } from "react-dom/client";
function App() { return <h1>Hello from Bun</h1>; }
createRoot(document.getElementById("app")!).render(<App />);
```

```css
/* app.css — @import works */
@import "./reset.css";
#app { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; }
```

## Fullstack Dev Server

```typescript
// server.ts
import homepage from "./client/index.html";

const server = Bun.serve({
  port: 3000,
  static: { "/": homepage },  // HTML imports served with HMR in dev

  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/api/users") return Response.json(await getUsers());
    if (url.pathname === "/api/health") return Response.json({ status: "ok" });
    return new Response("Not Found", { status: 404 });
  },
});
console.log(`Server running at ${server.url}`);
```

```typescript
// Multi-page application
import landing from "./pages/landing.html";
import dashboard from "./pages/dashboard.html";
import settings from "./pages/settings.html";

Bun.serve({
  static: { "/": landing, "/dashboard": dashboard, "/settings": settings },
  fetch(req) {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/api/")) return handleApi(req);
    return new Response("Not Found", { status: 404 });
  },
});
```

## Hot Module Replacement

```typescript
// counter.ts — preserve state across HMR updates
let count = 0;
export function getCount() { return count; }
export function increment() { count++; render(); }
function render() { document.getElementById("count")!.textContent = String(count); }

if (import.meta.hot) {
  import.meta.hot.accept();
  import.meta.hot.dispose((data) => { data.count = count; });  // save state
  if (import.meta.hot.data?.count !== undefined) {
    count = import.meta.hot.data.count;  // restore state
    render();
  }
}
```

| Method | Purpose |
|--------|---------|
| `import.meta.hot.accept()` | Accept updates for this module |
| `import.meta.hot.accept(cb)` | Accept with callback receiving new module |
| `import.meta.hot.dispose(cb)` | Cleanup before module is replaced |
| `import.meta.hot.data` | Persistent data object surviving HMR updates |
| `import.meta.hot.decline()` | Refuse updates (triggers full reload) |
| `import.meta.hot.invalidate()` | Force full reload |

CSS changes are always hot-replaced without any `import.meta.hot` code.

## React Fast Refresh

When React is detected, Bun automatically enables React Fast Refresh — no configuration needed:

```tsx
import { useState } from "react";

export function App() {
  const [count, setCount] = useState(0);  // state preserved across HMR
  return (
    <div>
      <h1>Count: {count}</h1>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
// Editing this file re-renders with new code while preserving count
```

Fast Refresh works for function components with or without hooks, and default or named exports. Full reload triggers for: files exporting non-component values alongside components, class components, or syntax errors.

## Asset Pipeline

```html
<img src="./images/logo.png" />  <!-- copied and content-hashed -->
<style>
  @font-face { font-family: "Custom"; src: url("./fonts/custom.woff2") format("woff2"); }
</style>
```

```typescript
import logoUrl from "./images/logo.png";  // "/assets/logo-a1b2c3d4.png"
import styles from "./component.module.css";  // CSS modules — returns class name object
import config from "./config.json";           // parsed JSON object
import readme from "./README.txt" with { type: "text" };  // raw string
```

CSS processing: `@import` resolution and bundling, URL rewriting, CSS modules (`.module.css`). Vendor prefixing not included — use modern CSS or add PostCSS.

## Framework Integration

```tsx
// React — works out of the box
import { createRoot } from "react-dom/client";
import { App } from "./App";
createRoot(document.getElementById("root")!).render(<App />);

// Preact — set jsxImportSource in tsconfig.json: "preact"
import { render } from "preact";
render(<App />, document.getElementById("root")!);

// Solid — set jsxImportSource in tsconfig.json: "solid-js"
import { render } from "solid-js/web";
render(() => <App />, document.getElementById("root")!);

// Vanilla TypeScript
async function loadData() {
  const data = await fetch("/api/data").then(r => r.json());
  document.getElementById("app")!.innerHTML =
    `<h1>${data.title}</h1><ul>${data.items.map((i: string) => `<li>${i}</li>`).join("")}</ul>`;
}
loadData();
```

## Production Builds

```bash
bun build ./index.html --outdir dist
bun build ./index.html --outdir dist --minify
bun build ./index.html --outdir dist --minify --sourcemap=external
bun build ./index.html --outdir dist --public-path="https://cdn.example.com/"
```

```typescript
const result = await Bun.build({
  entrypoints: ["./index.html"],
  outdir: "./dist",
  minify: true,
  sourcemap: "external",
  naming: { entry: "[name]-[hash].[ext]", asset: "assets/[name]-[hash].[ext]" },
});
if (!result.success) {
  for (const log of result.logs) console.error(log.message);
  process.exit(1);
}
```

```typescript
// Serve production build with SPA fallback + cache headers
import { serve, file } from "bun";
serve({
  port: 8080,
  async fetch(req) {
    const url = new URL(req.url);
    let path = url.pathname === "/" ? "/index.html" : url.pathname;
    const f = file(`./dist${path}`);
    if (await f.exists()) {
      return new Response(f, {
        headers: {
          ...(path.match(/-[a-f0-9]{8}\./) && {
            "Cache-Control": "public, max-age=31536000, immutable",
          }),
        },
      });
    }
    return new Response(file("./dist/index.html"));  // SPA fallback
  },
});
```

## Environment Variables in Frontend Code

`process.env.*` references in frontend code are replaced with literal values at build time:

```typescript
const apiUrl = process.env.API_URL;        // replaced at build time
const debug = process.env.DEBUG === "true";
async function fetchData() {
  return fetch(`${process.env.API_URL}/api/data`).then(r => r.json());
}
```

```bash
API_URL=http://localhost:3000 bun ./index.html         # dev
API_URL=https://api.example.com bun build ./index.html --outdir dist --minify
```

```bash
# .env
API_URL=http://localhost:3000
APP_TITLE=My App
DEBUG=true
```

Only variables referenced in frontend code are included in the bundle.

## Proxy Configuration for API Backends

```typescript
import homepage from "./client/index.html";

Bun.serve({
  port: 3000,
  static: { "/": homepage },

  async fetch(req) {
    const url = new URL(req.url);
    // Proxy /api/* to a separate backend to avoid CORS issues
    if (url.pathname.startsWith("/api/")) {
      return fetch(`http://localhost:8080${url.pathname}${url.search}`, {
        method: req.method, headers: req.headers, body: req.body,
      });
    }
    return new Response("Not Found", { status: 404 });
  },
});
```

## Common Fullstack Patterns

### API + SPA with Client-Side Routing

```typescript
import app from "./client/index.html";

Bun.serve({
  port: 3000,
  static: { "/": app },
  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/api/")) return handleApiRoute(req);
    // Fallback enables React Router, etc.
    return new Response(Bun.file("./client/index.html"), {
      headers: { "Content-Type": "text/html" },
    });
  },
});
```

### Server-Rendered Initial Data

```typescript
Bun.serve({
  port: 3000,
  static: { "/": homepage },
  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/dashboard") {
      const user = await getCurrentUser(req);
      const html = await Bun.file("./client/dashboard.html").text();
      const injected = html.replace(
        "<!--SERVER_DATA-->",
        `<script>window.__INITIAL_DATA__ = ${JSON.stringify(user)}</script>`
      );
      return new Response(injected, { headers: { "Content-Type": "text/html" } });
    }
    return new Response("Not Found", { status: 404 });
  },
});
```

## Comparison with Vite and Webpack

| Feature | Bun | Vite | Webpack |
|---------|-----|------|---------|
| **Config required** | None | `vite.config.ts` | `webpack.config.js` |
| **TypeScript** | Native | Via esbuild | Via `ts-loader` |
| **JSX/TSX** | Native | Via esbuild | Via `babel-loader` |
| **HMR** | Built-in | Built-in | Via `webpack-dev-server` |
| **React Fast Refresh** | Automatic | Plugin required | Plugin required |
| **CSS Modules** | Built-in | Built-in | Via `css-loader` |
| **Dev server startup** | Instant | Fast (pre-bundles deps) | Slow (full bundle) |
| **Plugin ecosystem** | Bun plugins | Vite/Rollup plugins | Webpack loaders/plugins |
| **Fullstack integration** | `Bun.serve()` + HTML imports | Middleware mode | Dev middleware |
| **Dependencies** | Zero (built-in) | npm packages | npm packages |

## Common Pitfalls

1. **Expecting Vite plugin compatibility** — Bun has its own plugin API; Vite and Rollup plugins do not work directly
2. **Using `process.env` for secrets in frontend code** — All `process.env` references are replaced at build time and visible in the client bundle; never reference `DATABASE_URL` or `API_SECRET` in frontend files
3. **Forgetting SPA fallback** — Client-side routers require the server to return `index.html` for all non-asset paths; direct navigation to `/dashboard` returns 404 without a fallback
4. **Assuming CSS vendor prefixing** — Bun's CSS processing does not add vendor prefixes; use modern CSS `@supports` or add a PostCSS step
5. **Not setting `--public-path` for CDN deployment** — Without it, asset URLs are relative; browsers request assets from the wrong origin when serving from a CDN subdomain
6. **Importing HTML outside of `Bun.serve()` context** — HTML imports are designed for `Bun.serve()`'s `static` property; other uses may not behave as expected
7. **Mixing HMR APIs across frameworks** — React Fast Refresh and manual `import.meta.hot` code can conflict; let Fast Refresh handle React components automatically
8. **Large unoptimized assets** — The dev server does not compress images or optimize fonts; optimize assets before including them in the project
