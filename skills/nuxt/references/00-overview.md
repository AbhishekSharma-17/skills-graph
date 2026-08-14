# Nuxt — Overview & Setup

> Source: [nuxt.com/docs/getting-started](https://nuxt.com/docs/getting-started/introduction)

## What Is Nuxt?

Nuxt is a free, open-source full-stack framework for building type-safe, performant, production-grade web applications with Vue.js. It provides:

- **File-based routing** — pages defined by filesystem structure
- **Auto-imports** — components, composables, and utilities available without manual imports
- **Server-side rendering** — SSR enabled by default for SEO and performance
- **Nitro server engine** — universal server deployable to Node.js, serverless, edge, or static hosting
- **Zero-config TypeScript** — full type safety with auto-generated types
- **Vite-powered** — fast HMR and optimized builds (Rspack also supported in v4.5+)

## When to Use Nuxt

Choose Nuxt when you need:
- A Vue.js application with SSR or static site generation
- File-based routing without manual route configuration
- Full-stack capabilities (API routes, server middleware) in one project
- Auto-imports to reduce boilerplate
- Universal deployment across Node.js, serverless, and edge platforms

Nuxt is the Vue.js equivalent of Next.js (React) or SvelteKit (Svelte).

## Installation

```bash
# Create a new Nuxt project
npx nuxi@latest init my-app
cd my-app
npm install
npm run dev
```

The `nuxi` CLI scaffolds a project with `app.vue`, `nuxt.config.ts`, and `package.json`.

### Adding to an Existing Project

```bash
npm install nuxt vue vue-router
```

Create `nuxt.config.ts`:

```typescript
export default defineNuxtConfig({})
```

Create `app/app.vue`:

```vue
<template>
  <div>
    <h1>Hello Nuxt</h1>
  </div>
</template>
```

Add scripts to `package.json`:

```json
{
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt build",
    "generate": "nuxt generate",
    "preview": "nuxt preview",
    "postinstall": "nuxt prepare"
  }
}
```

## Nuxt 4 — Key Changes

Nuxt 4.0 released July 15, 2025. Current latest is v4.5.x (August 2026).

### New `app/` Directory

Application source code now lives in `app/` by default:

```
my-app/
├── app/
│   ├── assets/
│   ├── components/
│   ├── composables/
│   ├── layouts/
│   ├── middleware/
│   ├── pages/
│   ├── plugins/
│   ├── utils/
│   ├── app.vue
│   └── app.config.ts
├── server/
├── shared/
├── public/
├── nuxt.config.ts
└── package.json
```

### Improved TypeScript

Nuxt 4 creates separate TypeScript projects for app code, server code, `shared/` folder, and builder code. A single `tsconfig.json` replaces multiple config files.

### Enhanced Data Fetching

`useAsyncData` and `useFetch` now:
- Automatically share data across components using identical keys
- Include automatic cleanup on component unmount
- Support reactive keys for refetching

### Performance Improvements

- Faster cold starts with Node.js compile caching
- Native file watching via `fs.watch` APIs
- Socket-based CLI communication
- Vite 8 and Rspack 2 support (v4.5+)

### Migration from Nuxt 3

```bash
npx nuxt upgrade --dedupe
```

Automated migration available via Codemod. Nuxt 3 received maintenance until January 2026.

## Core Concepts

### Auto-Imports

Nuxt auto-imports Vue APIs, composables, and components:

```vue
<script setup>
// No imports needed — ref, computed, useFetch are auto-imported
const count = ref(0)
const doubled = computed(() => count.value * 2)
const { data } = await useFetch('/api/hello')
</script>
```

### Universal Rendering

By default, Nuxt renders pages on the server first (SSR), then hydrates on the client. This provides:
- Faster initial page loads
- Better SEO (search engines see full HTML)
- Works on low-powered devices

Disable SSR per-page or globally:

```typescript
// nuxt.config.ts — disable globally
export default defineNuxtConfig({
  ssr: false
})
```

### The Nitro Server Engine

Nitro powers Nuxt's server side. It builds your application into a portable `.output` directory that can be deployed anywhere:

```
.output/
├── server/
│   └── index.mjs    # Server entry point
├── public/          # Static assets
└── nitro.json       # Runtime config
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `nuxt dev` | Start development server with HMR |
| `nuxt build` | Build for production (SSR) |
| `nuxt generate` | Pre-render static site (SSG) |
| `nuxt preview` | Preview production build locally |
| `nuxt prepare` | Generate TypeScript types |
| `nuxt upgrade` | Upgrade Nuxt to latest version |
| `nuxt info` | Display project information |
| `nuxt module add <name>` | Add a Nuxt module |
| `nuxt cleanup` | Clean generated files |

## Minimum Requirements

- **Node.js:** v18.12.0 or newer (v20+ recommended)
- **Vue.js:** v3.5+ (bundled with Nuxt)
- **Package Managers:** npm, yarn, pnpm, or bun
