# SvelteKit — Deployment & Adapters

> Source: [svelte.dev/docs/kit/adapters](https://svelte.dev/docs/kit/adapters)

## Table of Contents

- [Overview](#overview)
- [adapter-auto](#adapter-auto)
- [adapter-node](#adapter-node)
- [adapter-vercel](#adapter-vercel)
- [adapter-cloudflare](#adapter-cloudflare)
- [adapter-netlify](#adapter-netlify)
- [adapter-static](#adapter-static)
- [Docker Deployment](#docker-deployment)
- [Environment Variables in Production](#environment-variables-in-production)

## Overview

SvelteKit apps need an **adapter** to convert the build output into a format compatible with the target platform. Adapters handle the translation between SvelteKit's universal request/response model and platform-specific APIs.

## adapter-auto

**Default for new projects.** Automatically detects the deployment platform and uses the correct adapter:

```js
// svelte.config.js
import adapter from '@sveltejs/adapter-auto';

export default {
  kit: {
    adapter: adapter()
  }
};
```

Supported platforms: Vercel, Netlify, Cloudflare Pages. Falls back to `adapter-node` for others.

**Recommendation:** Replace `adapter-auto` with a specific adapter when you know your deployment target. This gives you platform-specific configuration options and eliminates detection overhead.

## adapter-node

Generates a standalone Node.js server. Works anywhere Node runs — bare metal, VMs, Docker, Railway, Render, Fly.io.

```bash
npm install -D @sveltejs/adapter-node
```

```js
// svelte.config.js
import adapter from '@sveltejs/adapter-node';

export default {
  kit: {
    adapter: adapter({
      out: 'build',           // Output directory
      precompress: true,      // Generate brotli/gzip files
      envPrefix: ''            // Env var prefix for HOST, PORT, etc.
    })
  }
};
```

### Running the Server

```bash
npm run build
node build/index.js
```

### Configuration via Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` | Port to listen on |
| `HOST` | `0.0.0.0` | Host to bind to |
| `ORIGIN` | - | URL origin (e.g., `https://myapp.com`) |
| `PROTOCOL_HEADER` | - | Header for protocol (`x-forwarded-proto`) |
| `HOST_HEADER` | - | Header for host (`x-forwarded-host`) |
| `ADDRESS_HEADER` | - | Header for client IP |
| `XFF_DEPTH` | `1` | Trusted proxy depth for `x-forwarded-for` |
| `BODY_SIZE_LIMIT` | `512K` | Max request body size |
| `SHUTDOWN_TIMEOUT` | `30` | Graceful shutdown timeout (seconds) |
| `IDLE_TIMEOUT` | `0` | Connection idle timeout (seconds) |

```bash
PORT=8080 ORIGIN=https://myapp.com node build/index.js
```

### Custom Server

```ts
// custom-server.ts
import { handler } from './build/handler.js';
import express from 'express';

const app = express();

// Custom middleware before SvelteKit
app.use('/health', (req, res) => res.json({ status: 'ok' }));

// SvelteKit handler
app.use(handler);

app.listen(3000, () => console.log('Server running on port 3000'));
```

## adapter-vercel

Optimized for Vercel with edge and serverless function support:

```bash
npm install -D @sveltejs/adapter-vercel
```

```js
import adapter from '@sveltejs/adapter-vercel';

export default {
  kit: {
    adapter: adapter({
      runtime: 'nodejs22.x',  // or 'edge'
      regions: ['iad1'],
      memory: 1024,
      maxDuration: 30,
      isr: {
        expiration: 60  // Incremental Static Regeneration
      },
      images: {
        sizes: [640, 828, 1200],
        formats: ['image/avif', 'image/webp'],
        minimumCacheTTL: 300
      }
    })
  }
};
```

### Per-Route Configuration

```ts
// src/routes/api/heavy/+server.ts
export const config = {
  runtime: 'nodejs22.x',
  regions: ['iad1'],
  maxDuration: 60,
  memory: 3008
};
```

```ts
// src/routes/api/fast/+server.ts
export const config = {
  runtime: 'edge'
};
```

## adapter-cloudflare

Deploy to Cloudflare Pages (with Workers for server routes):

```bash
npm install -D @sveltejs/adapter-cloudflare
```

```js
import adapter from '@sveltejs/adapter-cloudflare';

export default {
  kit: {
    adapter: adapter({
      routes: {
        include: ['/*'],
        exclude: ['<all>']
      },
      platformProxy: {
        configPath: 'wrangler.toml',
        persist: '.wrangler/state'
      }
    })
  }
};
```

### Accessing Cloudflare Bindings

```ts
// src/app.d.ts
declare global {
  namespace App {
    interface Platform {
      env: {
        MY_KV: KVNamespace;
        MY_DO: DurableObjectNamespace;
        DB: D1Database;
      };
    }
  }
}
```

```ts
// +page.server.ts
export const load = async ({ platform }) => {
  const value = await platform!.env.MY_KV.get('key');
  return { value };
};
```

## adapter-netlify

Deploy to Netlify with serverless functions:

```bash
npm install -D @sveltejs/adapter-netlify
```

```js
import adapter from '@sveltejs/adapter-netlify';

export default {
  kit: {
    adapter: adapter({
      edge: false,           // Use Netlify Edge Functions
      split: false           // Split into per-route functions
    })
  }
};
```

## adapter-static

Generate a fully static site (SSG). No server required at runtime:

```bash
npm install -D @sveltejs/adapter-static
```

```js
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      pages: 'build',        // Output directory for pages
      assets: 'build',       // Output directory for assets
      fallback: undefined,   // SPA fallback page (e.g., '200.html')
      precompress: true,     // Generate brotli/gzip files
      strict: true           // Fail if routes can't be prerendered
    })
  }
};
```

### Full SSG

```ts
// src/routes/+layout.ts
export const prerender = true; // Prerender all pages
```

### SPA Mode

```ts
// src/routes/+layout.ts
export const ssr = false;
```

```js
// svelte.config.js — set fallback for SPA
adapter({ fallback: '200.html' })
```

## Docker Deployment

```dockerfile
# Build stage
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
RUN npm prune --production

# Production stage
FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/build build/
COPY --from=builder /app/node_modules node_modules/
COPY package.json .

ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000
CMD ["node", "build/index.js"]
```

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - ORIGIN=https://myapp.com
      - DATABASE_URL=postgresql://db:5432/mydb
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mydb
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## Environment Variables in Production

### Node Adapter

Read from the process environment at runtime:

```bash
DATABASE_URL=postgres://... ORIGIN=https://myapp.com node build/index.js
```

Or use `.env` with a loader:

```bash
node --env-file=.env build/index.js  # Node 20.6+
```

### Vercel / Netlify

Set in the platform dashboard or CLI:

```bash
vercel env add DATABASE_URL production
netlify env:set DATABASE_URL "postgres://..."
```

### Cloudflare

Set in `wrangler.toml` or the dashboard:

```toml
# wrangler.toml
[vars]
PUBLIC_API_URL = "https://api.example.com"
```

Secrets via CLI:

```bash
wrangler secret put DATABASE_URL
```

## Common Pitfalls

1. **Forgetting ORIGIN** — `adapter-node` needs the `ORIGIN` environment variable set in production for CSRF protection and correct URL generation
2. **Static adapter with form actions** — Form actions don't work on statically generated pages. Use API routes or client-side fetching.
3. **Large node_modules in Docker** — Use multi-stage builds and `npm prune --production`
4. **Missing platform bindings** — Cloudflare bindings (KV, D1, DO) require proper type declarations in `app.d.ts`
5. **adapter-auto in production** — Replace with a specific adapter for explicit control and configuration

## Related

- Page Options → `07-page-options.md`
- Environment → `11-environment.md`
- Overview & Setup → `00-overview.md`
