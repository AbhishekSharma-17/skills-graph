# Astro Overview

> Source: https://docs.astro.build/en/getting-started/ | Astro v5.17 (stable), v6 beta

## What is Astro

Astro is an all-in-one web framework purpose-built for **content-driven websites** — blogs, marketing sites, documentation, portfolios, and e-commerce. It prioritizes content delivery speed by shipping **zero JavaScript by default** and selectively hydrating only the interactive components a page actually needs.

Astro was acquired by **Cloudflare** in January 2026 and continues as an open-source project with deep integration into Cloudflare Workers.

## When to Use Astro

Choose Astro when:

- The site is **content-first**: blogs, docs, marketing, landing pages, e-commerce fronts.
- You want **multi-framework freedom**: mix React, Vue, Svelte, Solid, Preact, Lit in one project.
- You want **SEO and Core Web Vitals** to be easy — Astro ships no JS unless you explicitly opt in.
- You want **SSG-first, SSR-optional** — pages can be prerendered at build or rendered on-demand per request.
- You want **Markdown/MDX/JSON** as first-class data with type-safe schemas (Content Collections).

Astro is **not** the right fix for highly dynamic app-shell SaaS UIs (prefer Next.js, Remix, or SvelteKit for that — although Astro can still host a React SPA via `client:only`).

## Core Concepts at a Glance

| Concept | One-liner |
|---------|-----------|
| **Islands Architecture** | Static HTML + small interactive "islands" — only hydrate what needs JS |
| **`.astro` components** | HTML + frontmatter (TS/JS) — no JS sent to browser |
| **Framework components** | React/Vue/Svelte/Solid/Preact — opt in per instance with `client:*` |
| **Content Collections** | Type-safe content sources (Markdown, MDX, JSON, APIs) via Content Layer |
| **File-based routing** | `src/pages/*.astro` → URL paths |
| **Rendering modes** | Static (default), on-demand (SSR), or hybrid per-route |
| **Adapters** | Ship to Node, Cloudflare, Vercel, Netlify, Deno, Bun, AWS |

## Installation

```bash
# Interactive scaffolding (recommended)
npm create astro@latest

# Name the project, pick starter template, install deps
# Answer prompts:
#   - Where should we create your new project?
#   - How would you like to start your new project? (empty/blog/starter)
#   - Install dependencies? (Y)
#   - Do you plan to write TypeScript? (Y — strict recommended)
#   - Initialize a git repository? (Y)

cd my-astro-site
npm run dev
```

## Minimum Requirements

- **Node.js** 18.20.8 or higher (20.3+ or 22+ recommended; 19.x not supported).
- Or **Bun** 1.x (via `bun create astro@latest`).
- Or **Deno** 2.x (experimental adapter).

## Project Layout (Default)

```
my-astro-site/
├── astro.config.mjs     # Framework configuration
├── tsconfig.json        # TypeScript config (extends astro/tsconfigs/strict)
├── package.json
├── public/              # Static assets served as-is (favicon, robots.txt)
└── src/
    ├── pages/           # File-based routes — each .astro/.md/.mdx becomes a URL
    │   └── index.astro
    ├── layouts/         # Reusable page shells
    ├── components/      # .astro + framework components
    ├── content/         # Content Collections (Markdown/MDX/JSON)
    ├── styles/          # Global CSS
    └── env.d.ts         # Astro type shims
```

Only `src/pages/` and `public/` have conventional meaning. Everything else is convention, not enforcement.

## Your First Page

`src/pages/index.astro`:

```astro
---
// Component frontmatter — runs on the server at build or request time
const title = "Hello, Astro";
const items = ["Fast", "Content-first", "Zero-JS by default"];
---
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
  </head>
  <body>
    <h1>{title}</h1>
    <ul>
      {items.map((item) => <li>{item}</li>)}
    </ul>
  </body>
</html>
```

Run `npm run dev`, open `http://localhost:4321`, and you have a working site with zero JS shipped.

## The Commands You Will Use Daily

| Command | What it does |
|---------|--------------|
| `npm run dev` | Start dev server with HMR at `localhost:4321` |
| `npm run build` | Build for production into `./dist/` |
| `npm run preview` | Preview the production build locally |
| `npx astro add <integration>` | Install + configure an integration (tailwind, react, mdx, ...) |
| `npx astro check` | Type-check + validate templates (like `tsc` for `.astro`) |
| `npx astro sync` | Generate content collection types (`src/content/config.ts`) |
| `npx astro info` | Dump environment info (useful for bug reports) |

## Islands, In One Example

```astro
---
import Counter from "../components/Counter.jsx"; // React component
import Nav from "../components/Nav.astro";       // Zero-JS component
---
<Nav />                                 <!-- Static HTML, 0 bytes of JS -->
<Counter client:visible />              <!-- Hydrated when scrolled into view -->
<Counter client:idle count={5} />       <!-- Hydrated after main thread idle -->
<Counter client:load count={10} />      <!-- Hydrated immediately on page load -->
```

Every other component on the page remains pure HTML. The cost of each island is its own bundle — nothing more.

## What Astro 5 Brought

- **Content Layer** — pluggable content loading (Markdown, MDX, APIs, CMSs) with type-safe queries.
- **Server Islands** — defer slow server-rendered sections, stream them in after the shell.
- **`astro:env`** — type-safe environment variable schema.
- **Astro Actions** — type-safe RPC between client and server with built-in form handling.
- **Sessions** (experimental) — opaque session cookies backed by a pluggable store.

## What Astro 6 (Beta, Jan 2026) Is Bringing

- **Vite 7 / Environment API** — unified build pipeline for browser + worker runtimes.
- **Workerd dev server** — local dev runs on the exact Cloudflare Workers runtime you deploy to.
- **Stable Live Content Collections** — revalidate content without a rebuild.
- **Stable CSP** — first-class Content Security Policy generation.
- **Built-in fonts API** — self-host Google Fonts / local fonts with zero layout shift.

Use Astro 5.17 for production today. Track Astro 6 betas if you want the Workers runtime unification.

## Next Steps

- **New to the syntax?** Read `03-astro-components.md`.
- **Building a blog or docs site?** Go straight to `04-content-collections.md`.
- **Need interactivity?** Read `05-islands-and-client-directives.md`.
- **Need SSR or an API?** Read `06-rendering-modes.md` and `09-endpoints-and-api-routes.md`.
- **Deploying?** Read `11-integrations-and-adapters.md` and `12-deployment-and-best-practices.md`.
