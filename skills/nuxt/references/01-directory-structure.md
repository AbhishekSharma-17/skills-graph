# Nuxt — Directory Structure

> Source: [nuxt.com/docs/guide/directory-structure](https://nuxt.com/docs/guide/directory-structure/app)

## Nuxt 4 Project Layout

```
my-app/
├── app/                    # Application source code
│   ├── assets/             # Build-processed assets (CSS, images, fonts)
│   ├── components/         # Vue components (auto-imported)
│   ├── composables/        # Composition API functions (auto-imported)
│   ├── layouts/            # Layout templates
│   ├── middleware/          # Route middleware
│   ├── pages/              # File-based routing (optional)
│   ├── plugins/            # Vue/Nuxt plugins
│   ├── utils/              # Utility functions (auto-imported)
│   ├── app.vue             # Root component
│   ├── app.config.ts       # Build-time app configuration
│   ├── error.vue           # Global error page
│   └── router.options.ts   # Vue Router overrides
├── server/                 # Backend code (Nitro)
│   ├── api/                # API routes (prefixed with /api)
│   ├── routes/             # Server routes (no /api prefix)
│   ├── middleware/          # Server middleware (every request)
│   ├── plugins/            # Nitro lifecycle plugins
│   └── utils/              # Server utilities (auto-imported)
├── shared/                 # Code shared between app and server
│   ├── types/              # Shared TypeScript types
│   └── utils/              # Shared utility functions
├── public/                 # Static files served at root URL
├── content/                # Content files (with @nuxt/content)
├── layers/                 # Nuxt layers for code sharing
├── .nuxt/                  # Generated build artifacts (gitignored)
├── .output/                # Production build output (gitignored)
├── nuxt.config.ts          # Main configuration file
├── tsconfig.json           # TypeScript configuration
├── .env                    # Environment variables
├── .nuxtrc                 # Nuxt runtime config overrides
└── .nuxtignore             # Files to exclude from scanning
```

## Key Directories

### `app/` — Application Code

The main directory for client-side and universal code. All subdirectories within `app/` are convention-based and auto-scanned.

**Why `app/`?** Nuxt 4 moved application code into `app/` for:
- Faster file watching (scans only app code, not node_modules)
- Better IDE context and type inference
- Clear separation between app, server, and shared code

### `app/components/` — Vue Components

Components are auto-imported and available in templates without `import` statements.

```
app/components/
├── AppHeader.vue           → <AppHeader />
├── base/
│   └── Button.vue          → <BaseButton />
└── ui/
    ├── Card.vue            → <UiCard />
    └── Modal.vue           → <UiModal />
```

Naming follows path-based conventions — the directory path becomes part of the component name.

### `app/composables/` — Composition Functions

Only top-level files are auto-imported by default:

```
app/composables/
├── useAuth.ts              → useAuth() available everywhere
├── useCart.ts              → useCart() available everywhere
└── nested/
    └── useHelper.ts        → NOT auto-imported (nested)
```

Enable nested scanning in `nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  imports: {
    dirs: ['~/composables/**']
  }
})
```

### `app/pages/` — File-Based Routing

Each `.vue` file becomes a route. This directory is **optional** — without it, `vue-router` is excluded entirely.

```
app/pages/
├── index.vue               → /
├── about.vue               → /about
├── blog/
│   ├── index.vue           → /blog
│   └── [slug].vue          → /blog/:slug
└── [...slug].vue           → Catch-all route
```

### `app/layouts/` — Layout Wrappers

Layouts wrap page content with shared UI (headers, footers, sidebars):

```
app/layouts/
├── default.vue             → Default layout for all pages
├── admin.vue               → Named layout for admin pages
└── auth.vue                → Named layout for auth pages
```

### `app/middleware/` — Route Middleware

Functions that run before navigation completes:

```
app/middleware/
├── auth.ts                 → Named middleware (opt-in per page)
└── 01.tracking.global.ts   → Global middleware (runs on every route)
```

### `app/plugins/` — Initialization Logic

Plugins run during Vue app creation. Only top-level files are auto-loaded:

```
app/plugins/
├── 01.auth.ts              → Runs first (numeric ordering)
├── 02.analytics.ts         → Runs second
└── vue-directives.ts       → Registers custom directives
```

### `app/utils/` — Utility Functions

Auto-imported helper functions. Unlike composables, these are typically stateless:

```
app/utils/
├── formatDate.ts           → formatDate() available everywhere
└── validators.ts           → Named exports auto-imported
```

### `server/` — Backend Code

Server-side code powered by Nitro. Completely separate from the Vue app:

```
server/
├── api/
│   ├── users.get.ts        → GET /api/users
│   ├── users.post.ts       → POST /api/users
│   └── users/[id].ts       → /api/users/:id (all methods)
├── routes/
│   └── health.ts           → GET /health (no /api prefix)
├── middleware/
│   └── log.ts              → Runs on every request
├── plugins/
│   └── database.ts         → Nitro lifecycle hooks
└── utils/
    └── db.ts               → Auto-imported in server code
```

### `shared/` — Cross-Environment Code

Code accessible in both `app/` and `server/` contexts. Must be environment-agnostic (no browser or Node.js-specific APIs):

```typescript
// shared/types/user.ts
export interface User {
  id: string
  name: string
  email: string
}

// shared/utils/validate.ts
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}
```

### `public/` — Static Files

Files served directly at the root URL without processing:

```
public/
├── favicon.ico             → /favicon.ico
├── robots.txt              → /robots.txt
└── images/
    └── logo.png            → /images/logo.png
```

### `.nuxt/` — Generated Directory

Auto-generated by `nuxt dev` and `nuxt prepare`. Contains:
- TypeScript type declarations
- Vue Router configuration
- Auto-import declarations
- Nitro configuration

Always gitignore this directory.

### `.output/` — Production Build

Generated by `nuxt build`. Contains the deployable application:

```
.output/
├── server/
│   └── index.mjs           # Server entry point
├── public/                  # Static assets + client bundles
└── nitro.json               # Runtime metadata
```

## Configuration Files

| File | Purpose |
|------|---------|
| `nuxt.config.ts` | Main Nuxt configuration (modules, build, runtime) |
| `tsconfig.json` | TypeScript settings (auto-managed by Nuxt) |
| `app.config.ts` | Build-time reactive app configuration |
| `.env` | Environment variables (loaded by Nuxt) |
| `.nuxtrc` | Runtime config overrides (dotenv-style) |
| `.nuxtignore` | Exclude files from Nuxt scanning (gitignore syntax) |

## Common Pitfalls

- **Missing `app/` directory** — Nuxt 4 defaults to `app/`. Nuxt 3 projects without `app/` still work but show a deprecation warning.
- **Nested composables not imported** — Only top-level files in `composables/` are auto-imported. Use `imports.dirs` for nested scanning.
- **`shared/` environment safety** — Code in `shared/` runs in both browser and server. Don't use `fs`, `process`, or browser-only APIs here.
- **Plugin execution order** — Plugins load alphabetically unless prefixed with numbers. Use `01.plugin.ts` naming for explicit ordering.
