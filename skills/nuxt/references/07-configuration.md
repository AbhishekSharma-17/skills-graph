# Nuxt — Configuration

> Source: [nuxt.com/docs/getting-started/configuration](https://nuxt.com/docs/getting-started/configuration)

## Table of Contents

- [nuxt.config.ts](#nuxtconfigts)
- [Runtime Configuration](#runtime-configuration)
- [App Configuration](#app-configuration)
- [runtimeConfig vs app.config](#runtimeconfig-vs-appconfig)
- [Environment Variables](#environment-variables)
- [Environment Overrides](#environment-overrides)
- [External Tool Configuration](#external-tool-configuration)
- [Common Pitfalls](#common-pitfalls)

## nuxt.config.ts

The primary configuration file. Uses `defineNuxtConfig()` which is globally available without imports:

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: ['@pinia/nuxt', '@nuxt/ui'],
  css: ['~/assets/css/main.css'],
  ssr: true,
  typescript: {
    strict: true
  }
})
```

### Common Configuration Options

```typescript
export default defineNuxtConfig({
  // Application metadata
  app: {
    head: {
      title: 'My App',
      htmlAttrs: { lang: 'en' },
      meta: [
        { name: 'description', content: 'My Nuxt app' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ]
    },
    baseURL: '/',          // Base URL for deployment
    buildAssetsDir: '/_nuxt/' // Assets directory prefix
  },

  // Modules
  modules: [
    '@pinia/nuxt',
    '@nuxt/ui',
    '@nuxt/image'
  ],

  // Global CSS
  css: ['~/assets/css/main.css'],

  // SSR toggle
  ssr: true,

  // Route rules for hybrid rendering
  routeRules: {
    '/': { prerender: true },
    '/api/**': { cors: true },
    '/admin/**': { ssr: false },
    '/blog/**': { isr: 3600 }  // Revalidate every hour
  },

  // TypeScript
  typescript: {
    strict: true,
    typeCheck: true
  },

  // Dev server
  devServer: {
    port: 3000,
    host: 'localhost'
  },

  // Source map generation
  sourcemap: {
    server: true,
    client: false
  },

  // Auto-import configuration
  imports: {
    dirs: ['~/composables/**']
  },

  // Component configuration
  components: [
    { path: '~/components', pathPrefix: false }
  ]
})
```

## Runtime Configuration

Expose values to the application at runtime. Supports environment variable overrides:

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    // Server-only keys (NOT exposed to client)
    apiSecret: 'default-secret',
    dbUrl: 'postgresql://localhost:5432/mydb',

    // Client-accessible keys
    public: {
      apiBase: 'https://api.example.com',
      appName: 'My App'
    }
  }
})
```

### Accessing Runtime Config

```typescript
// In components, composables, pages (app code)
const config = useRuntimeConfig()
console.log(config.public.apiBase) // Available on client and server

// In server code
const config = useRuntimeConfig()
console.log(config.apiSecret)      // Server-only
console.log(config.public.apiBase) // Also available on server
```

```vue
<script setup>
const config = useRuntimeConfig()
</script>

<template>
  <p>API Base: {{ config.public.apiBase }}</p>
</template>
```

### Event-Specific Runtime Config

In server routes, access runtime config via the event:

```typescript
// server/api/data.ts
export default defineEventHandler((event) => {
  const config = useRuntimeConfig(event)
  // Best practice: pass event for request-scoped config
})
```

## App Configuration

Build-time configuration for non-sensitive, reactive values:

```typescript
// app/app.config.ts
export default defineAppConfig({
  title: 'My App',
  theme: {
    dark: false,
    colors: {
      primary: '#3b82f6'
    }
  },
  ui: {
    button: {
      defaultVariant: 'solid'
    }
  }
})
```

### Accessing App Config

```vue
<script setup>
const appConfig = useAppConfig()
</script>

<template>
  <h1>{{ appConfig.title }}</h1>
</template>
```

### Updating App Config at Runtime

```typescript
const appConfig = useAppConfig()
appConfig.theme.dark = true // Reactive update, triggers HMR in dev
```

### Type-Safe App Config

```typescript
// app/app.config.ts
declare module 'nuxt/schema' {
  interface AppConfigInput {
    title?: string
    theme?: {
      dark?: boolean
      colors?: {
        primary?: string
      }
    }
  }
}

export default defineAppConfig({
  title: 'My App',
  theme: { dark: false, colors: { primary: '#3b82f6' } }
})
```

## runtimeConfig vs app.config

| Feature | runtimeConfig | app.config |
|---------|--------------|------------|
| Environment variable override | Yes | No |
| Server-only secrets | Yes | No |
| Determined at | Runtime | Build time |
| Reactive in dev | No | Yes (HMR) |
| Serializable values only | Yes | Yes |
| Best for | API keys, secrets, URLs | Theme, UI config, feature flags |

**Decision rule:**
- Needs to change per environment without rebuild? → `runtimeConfig`
- Sensitive/secret value? → `runtimeConfig` (not in `public`)
- UI theme, feature flags, branding? → `app.config`

## Environment Variables

### Overriding runtimeConfig

Environment variables override `runtimeConfig` values using the `NUXT_` prefix:

```bash
# .env
NUXT_API_SECRET=production-secret
NUXT_PUBLIC_API_BASE=https://api.production.com
```

Naming convention: `NUXT_` + uppercase + underscores for nested keys:

| runtimeConfig key | Environment variable |
|-------------------|---------------------|
| `apiSecret` | `NUXT_API_SECRET` |
| `public.apiBase` | `NUXT_PUBLIC_API_BASE` |
| `db.host` | `NUXT_DB_HOST` |

### .env File

Nuxt automatically loads `.env` files in development:

```bash
# .env
NUXT_API_SECRET=dev-secret
NUXT_PUBLIC_API_BASE=http://localhost:3001
DATABASE_URL=postgresql://localhost:5432/dev
```

For production, set environment variables in your hosting platform — `.env` files are for development only.

### Custom Environment Variables

Access non-NUXT_ variables in server code via `process.env`:

```typescript
// server/utils/db.ts
const dbUrl = process.env.DATABASE_URL
```

For client-side access, expose through `runtimeConfig.public`:

```typescript
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      analyticsId: process.env.ANALYTICS_ID || ''
    }
  }
})
```

## Environment Overrides

Apply different configuration per environment:

```typescript
export default defineNuxtConfig({
  // Base config (always applied)
  devtools: { enabled: true },

  // Production overrides
  $production: {
    devtools: { enabled: false },
    routeRules: {
      '/**': { isr: true }
    }
  },

  // Development overrides
  $development: {
    devtools: { enabled: true }
  },

  // Custom named environments
  $env: {
    staging: {
      runtimeConfig: {
        public: { apiBase: 'https://staging-api.example.com' }
      }
    }
  }
})
```

Activate custom environments via CLI:

```bash
nuxt build --envName staging
```

## External Tool Configuration

Consolidate tool configs in `nuxt.config.ts`:

```typescript
export default defineNuxtConfig({
  // Vite configuration
  vite: {
    css: {
      preprocessorOptions: {
        scss: { additionalData: '@use "~/assets/scss/variables" as *;' }
      }
    },
    vue: {
      customElement: true
    }
  },

  // Nitro (server engine)
  nitro: {
    preset: 'node-server',
    storage: {
      cache: { driver: 'redis', url: process.env.REDIS_URL }
    },
    compressPublicAssets: true
  },

  // PostCSS
  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {}
    }
  },

  // Webpack (if using webpack builder)
  webpack: {
    extractCSS: true
  }
})
```

Tools that keep separate config files:
- TypeScript → `tsconfig.json`
- ESLint → `eslint.config.mjs`
- Prettier → `.prettierrc`

## Common Pitfalls

- **Exposing secrets in `public`** — Values in `runtimeConfig.public` are sent to the browser. Never put API keys, database URLs, or secrets there.
- **Using `process.env` in app code** — `process.env` is not available in client-side code. Use `runtimeConfig.public` instead.
- **Assuming `.env` works in production** — `.env` files are loaded by Nuxt in development only. Set environment variables in your hosting platform for production.
- **Confusing `runtimeConfig` and `app.config`** — `runtimeConfig` supports env var overrides, `app.config` does not. Choose based on whether the value needs to change per deployment.
- **Hardcoding values** — Avoid hardcoding URLs, API keys, or environment-specific values. Always use `runtimeConfig` so deployment environments can override them.
