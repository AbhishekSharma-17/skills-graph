---
name: astro
description: "Astro — the web framework for content-driven websites with islands architecture, zero-JS by default, and multi-framework component support. MANDATORY TRIGGERS: astro, astro.build, .astro files, astro config, content collections, content layer, islands architecture, client:load, client:idle, client:visible, client:only, server islands, astro actions, astro middleware, astro endpoints, view transitions, ClientRouter, astro adapter, SSR adapter, static output, on-demand rendering, hybrid rendering, astro integrations, astro MDX, astrojs. Also trigger when the user asks about building a content-driven site, blog, documentation site, marketing site, SSG with partial hydration, mixing React/Vue/Svelte components in one app, or zero-JavaScript websites. When in doubt about whether to use this skill for content-driven web development with Astro, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["astro", "web-framework", "ssg", "ssr", "islands-architecture"]
---

# Astro

> **Skill Version:** 1.0.0 | **Tracks:** Astro v5.17 (stable), Astro v6 beta | **Source:** https://docs.astro.build

Astro is the web framework for content-driven websites — blogs, marketing pages, documentation, e-commerce. It pioneered the **islands architecture**: ship zero JavaScript by default, hydrate only the interactive components. Astro lets you mix React, Vue, Svelte, Solid, Preact, and Lit in a single project, and deploy as static (SSG), on-demand (SSR), or hybrid.

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview** | `references/00-overview.md` | "what is astro", "install astro", "getting started", "create astro app" |
| **Project Structure** | `references/01-project-structure.md` | "astro.config.mjs", "directory layout", "src/pages", "public folder", "TypeScript setup" |
| **Pages & Routing** | `references/02-pages-and-routing.md` | "file-based routing", "dynamic routes", "[slug].astro", "getStaticPaths", "params" |
| **Astro Components** | `references/03-astro-components.md` | ".astro syntax", "component frontmatter", "props", "slots", "Astro.props" |
| **Content Collections** | `references/04-content-collections.md` | "content collections", "content layer", "defineCollection", "getCollection", "loaders" |
| **Islands & Client Directives** | `references/05-islands-and-client-directives.md` | "islands architecture", "client:load", "client:visible", "client:only", "framework components" |
| **Rendering Modes** | `references/06-rendering-modes.md` | "output static", "output server", "prerender", "on-demand", "hybrid rendering" |
| **Actions** | `references/07-actions.md` | "astro actions", "server actions", "defineAction", "form handling", "type-safe RPC" |
| **Middleware** | `references/08-middleware.md` | "middleware.ts", "onRequest", "Astro.locals", "sequence", "request interception" |
| **Endpoints & API Routes** | `references/09-endpoints-and-api-routes.md` | "API routes", "endpoints", "GET POST handler", "Response object", "JSON API" |
| **View Transitions** | `references/10-view-transitions.md` | "view transitions", "ClientRouter", "transition:name", "transition:animate", "SPA navigation" |
| **Integrations & Adapters** | `references/11-integrations-and-adapters.md` | "astro add", "Tailwind integration", "MDX", "Node adapter", "Cloudflare adapter", "Vercel adapter" |
| **Deployment & Best Practices** | `references/12-deployment-and-best-practices.md` | "deploy astro", "env vars", "image optimization", "performance", "common pitfalls" |

## Installation

```bash
# Create new Astro project (recommended)
npm create astro@latest

# Or with alternative package managers
pnpm create astro@latest
yarn create astro
bun create astro@latest

# Add to existing project
npm install astro

# Copy skill to Claude Code
cp -r . ~/.claude/skills/astro/
```

## Quick Reference

- **Docs:** https://docs.astro.build
- **GitHub:** https://github.com/withastro/astro
- **Integrations Directory:** https://astro.build/integrations
- **Themes:** https://astro.build/themes
- **Blog (release notes):** https://astro.build/blog/
