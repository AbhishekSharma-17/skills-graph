---
name: sveltekit
description: "SvelteKit full-stack web framework with Svelte 5 runes, file-based routing, SSR/SSG/SPA, form actions, and deploy-anywhere adapters. MANDATORY TRIGGERS: sveltekit, svelte, svelte 5, runes, $state, $derived, $effect, +page.svelte, +layout.svelte, +server.js. Also trigger when user wants to build a full-stack web app with Svelte, set up file-based routing, use form actions, configure SSR or prerendering, deploy to Vercel/Cloudflare/Node, or use Svelte 5 reactivity. When in doubt about whether to use this skill for Svelte tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["sveltekit", "svelte", "svelte5", "runes", "ssr", "full-stack", "web-framework", "vite"]
---

# SvelteKit — Skill Router

> Full-stack web framework powered by Svelte 5 — file-based routing, server-side rendering, and deploy-anywhere adapters.

**Source:** [svelte.dev/docs/kit](https://svelte.dev/docs/kit) | **Package:** `@sveltejs/kit` v2.57.x / `svelte` v5.55.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, project structure, when to use SvelteKit |
| **Routing** | `references/01-routing.md` | Pages, layouts, route groups, dynamic params, rest params, matchers |
| **Runes & Reactivity** | `references/02-runes-reactivity.md` | $state, $derived, $effect, $props, $bindable, reactive proxies |
| **Loading Data** | `references/03-loading-data.md` | load functions, server vs universal, +page.server.js, +layout.js |
| **Form Actions** | `references/04-form-actions.md` | Form submissions, progressive enhancement, use:enhance, validation |
| **API Routes** | `references/05-api-routes.md` | +server.js endpoints, GET/POST/PUT/DELETE, streaming, JSON responses |
| **Hooks** | `references/06-hooks.md` | handle, handleFetch, handleError, reroute, sequence, locals |
| **Page Options** | `references/07-page-options.md` | SSR, CSR, prerendering, trailingSlash, rendering modes |
| **Navigation** | `references/08-navigation.md` | goto, invalidate, prefetch, $app/stores, remote functions, query |
| **Components** | `references/09-components.md` | Snippets, children, callback props, template syntax, {#each}, {#if} |
| **Styling** | `references/10-styling.md` | Scoped CSS, :global, transitions, animations, Tailwind integration |
| **Environment** | `references/11-environment.md` | $env/static, $env/dynamic, public vs private, $app modules |
| **Deployment** | `references/12-deployment.md` | Adapters, Node, Vercel, Cloudflare, static, adapter-auto |

## Installation

```bash
# Create new project
npx sv create my-app
cd my-app
npm install
npm run dev

# Add to existing project
npm install @sveltejs/kit svelte vite
```

## Quick Reference

- **Docs:** https://svelte.dev/docs/kit
- **GitHub:** https://github.com/sveltejs/kit
- **npm:** https://www.npmjs.com/package/@sveltejs/kit
- **Tutorial:** https://svelte.dev/tutorial/kit
- **Playground:** https://svelte.dev/playground
