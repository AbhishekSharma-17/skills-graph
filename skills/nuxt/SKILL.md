---
name: nuxt
description: "Nuxt full-stack Vue.js framework with file-based routing, SSR/SSG, auto-imports, Nitro server engine, and universal deployment. MANDATORY TRIGGERS: nuxt, nuxt4, nuxt.js, nuxtjs, useFetch, useAsyncData, defineNuxtConfig, nitro, nuxt server, vue full-stack. Also trigger when user wants to build a full-stack Vue app, set up file-based routing with Vue, use server-side rendering with Vue, create API routes with Nitro, configure auto-imports, or deploy a Vue app to serverless/edge. When in doubt about whether to use this skill for Vue.js full-stack tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["nuxt", "vue", "ssr", "full-stack", "nitro", "web-framework", "vite"]
---

# Nuxt — Skill Router

> Full-stack Vue.js framework — file-based routing, auto-imports, SSR/SSG, and the Nitro server engine.

**Source:** [nuxt.com/docs](https://nuxt.com/docs) | **Package:** `nuxt` v4.5.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, project structure, Nuxt 4 changes |
| **Directory Structure** | `references/01-directory-structure.md` | app/ directory, server/, shared/, public/, file conventions |
| **Routing** | `references/02-routing.md` | Pages, dynamic routes, nested routes, NuxtLink, route middleware |
| **Components** | `references/03-components.md` | Auto-imports, naming, lazy loading, client/server components |
| **Data Fetching** | `references/04-data-fetching.md` | useFetch, useAsyncData, $fetch, caching, SSR-safe requests |
| **State Management** | `references/05-state-management.md` | useState, Pinia, composables, SSR-safe state patterns |
| **Server Engine** | `references/06-server-engine.md` | Nitro, API routes, server middleware, H3, event handlers |
| **Configuration** | `references/07-configuration.md` | nuxt.config.ts, runtime config, app config, env variables |
| **SEO & Meta** | `references/08-seo-meta.md` | useHead, useSeoMeta, title templates, Open Graph, components |
| **Plugins & Middleware** | `references/09-plugins-middleware.md` | Plugin system, route middleware, provide/inject, Vue directives |
| **Layouts & Views** | `references/10-layouts-views.md` | Layouts, app.vue, error handling, transitions, NuxtPage |
| **Deployment** | `references/11-deployment.md` | SSR, SSG, prerendering, Nitro presets, hosting providers |
| **Testing & Modules** | `references/12-testing-modules.md` | @nuxt/test-utils, modules, layers, Nuxt ecosystem |

## Installation

```bash
# Create new project
npx nuxi@latest init my-app
cd my-app
npm install
npm run dev

# Upgrade existing Nuxt 3 project to Nuxt 4
npx nuxt upgrade --dedupe
```

## Quick Reference

- **Docs:** https://nuxt.com/docs
- **GitHub:** https://github.com/nuxt/nuxt
- **npm:** https://www.npmjs.com/package/nuxt
- **Modules:** https://nuxt.com/modules
- **Blog:** https://nuxt.com/blog
