# Inngest — Serve API & Frameworks

> Source: [inngest.com/docs/reference/serve](https://www.inngest.com/docs/reference/serve)

## Table of Contents

- [serve() API](#serve-api)
- [Configuration Options](#configuration-options)
- [Framework Adapters](#framework-adapters)
- [Next.js](#nextjs)
- [Express](#express)
- [Hono](#hono)
- [Fastify](#fastify)
- [AWS Lambda](#aws-lambda)
- [Cloudflare Workers](#cloudflare-workers)
- [Deno / Fresh](#deno--fresh)
- [Deployment](#deployment)
- [Production Configuration](#production-configuration)

---

## serve() API

The `serve()` function creates an HTTP handler that exposes your Inngest functions to the platform:

```typescript
import { serve } from "inngest/<framework>";
import { inngest } from "./client";
import { myFunction1, myFunction2 } from "./functions";

serve({
  client: inngest,
  functions: [myFunction1, myFunction2],
});
```

### HTTP endpoints exposed

| Method | Purpose |
|--------|---------|
| `GET` | Returns function metadata; shows landing page in dev |
| `POST` | Invokes functions (called by Inngest platform) |
| `PUT` | Registers/syncs functions with Inngest |

## Configuration Options

```typescript
serve({
  // Required
  client: Inngest;                     // Your Inngest client instance
  functions: InngestFunction[];        // Array of functions to serve

  // Optional
  id?: string;                         // Custom app ID (for multiple serve endpoints)
  serveOrigin?: string;                // Domain with protocol (e.g., "https://myapp.com")
  servePath?: string;                  // Path override (e.g., "/api/inngest")
  streaming?: "allow" | "force";       // Enable response streaming
  logLevel?: "debug" | "info" | "warn" | "error";
});
```

| Option | Default | Description |
|--------|---------|-------------|
| `client` | required | Inngest client with app ID and optional signing key |
| `functions` | required | Functions to expose |
| `id` | client's ID | Override app identifier |
| `serveOrigin` | auto-detected | Your app's public URL |
| `servePath` | auto-detected | Path where serve handler runs |
| `streaming` | `undefined` | Enable streaming for longer timeouts |
| `logLevel` | `"info"` | SDK log verbosity |

## Framework Adapters

Import `serve` from the framework-specific package:

```typescript
import { serve } from "inngest/next";       // Next.js
import { serve } from "inngest/express";     // Express
import { serve } from "inngest/hono";        // Hono
import { serve } from "inngest/fastify";     // Fastify
import { serve } from "inngest/lambda";      // AWS Lambda
import { serve } from "inngest/cloudflare";  // Cloudflare Workers
import { serve } from "inngest/remix";       // Remix
import { serve } from "inngest/fresh";       // Deno Fresh
import { serve } from "inngest/nuxt";        // Nuxt
import { serve } from "inngest/sveltekit";   // SvelteKit
import { serve } from "inngest/redwood";     // RedwoodJS
import { serve } from "inngest/koa";         // Koa
import { serve } from "inngest/h3";          // H3 / Nitro
```

## Next.js

### App Router

```typescript
// src/app/api/inngest/route.ts
import { serve } from "inngest/next";
import { inngest } from "@/inngest/client";
import { allFunctions } from "@/inngest/functions";

export const { GET, POST, PUT } = serve({
  client: inngest,
  functions: allFunctions,
});
```

### Pages Router

```typescript
// pages/api/inngest.ts
import { serve } from "inngest/next";
import { inngest } from "@/inngest/client";
import { allFunctions } from "@/inngest/functions";

export default serve({
  client: inngest,
  functions: allFunctions,
});
```

### With streaming (for Vercel)

```typescript
export const { GET, POST, PUT } = serve({
  client: inngest,
  functions: allFunctions,
  streaming: "allow", // Extends serverless function timeout
});
```

## Express

```typescript
import express from "express";
import { serve } from "inngest/express";
import { inngest } from "./inngest/client";
import { allFunctions } from "./inngest/functions";

const app = express();

app.use(
  "/api/inngest",
  serve({
    client: inngest,
    functions: allFunctions,
  })
);

app.listen(3000);
```

## Hono

```typescript
import { Hono } from "hono";
import { serve } from "inngest/hono";
import { inngest } from "./inngest/client";
import { allFunctions } from "./inngest/functions";

const app = new Hono();

app.on(
  ["GET", "POST", "PUT"],
  "/api/inngest",
  serve({
    client: inngest,
    functions: allFunctions,
  })
);

export default app;
```

## Fastify

```typescript
import Fastify from "fastify";
import { serve } from "inngest/fastify";
import { inngest } from "./inngest/client";
import { allFunctions } from "./inngest/functions";

const fastify = Fastify();

fastify.register(serve, {
  client: inngest,
  functions: allFunctions,
  prefix: "/api/inngest",
});

fastify.listen({ port: 3000 });
```

## AWS Lambda

```typescript
// handler.ts
import { serve } from "inngest/lambda";
import { inngest } from "./inngest/client";
import { allFunctions } from "./inngest/functions";

export const handler = serve({
  client: inngest,
  functions: allFunctions,
});
```

## Cloudflare Workers

```typescript
import { serve } from "inngest/cloudflare";
import { inngest } from "./inngest/client";
import { allFunctions } from "./inngest/functions";

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const handler = serve({
      client: inngest,
      functions: allFunctions,
    });
    return handler(request, env, ctx);
  },
};
```

## Deno / Fresh

```typescript
// routes/api/inngest.ts
import { serve } from "inngest/fresh";
import { inngest } from "../../inngest/client.ts";
import { allFunctions } from "../../inngest/functions.ts";

const handler = serve({
  client: inngest,
  functions: allFunctions,
});

export const GET = handler;
export const POST = handler;
export const PUT = handler;
```

## Deployment

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `INNGEST_EVENT_KEY` | Production | API key for sending events |
| `INNGEST_SIGNING_KEY` | Production | Key for verifying Inngest requests |
| `INNGEST_DEV` | Development | Set to `1` for local dev mode |

### Syncing functions

After deployment, Inngest needs to discover your functions. This happens via:

1. **Automatic sync** — Inngest polls your serve endpoint on deploy
2. **Manual sync** — Use the dashboard to trigger a sync
3. **PUT request** — The serve endpoint's PUT handler registers functions

```bash
# Manual sync via curl
curl -X PUT https://your-app.com/api/inngest
```

## Production Configuration

### Client setup for production

```typescript
const inngest = new Inngest({
  id: "my-app",
  // Signing key is read from INNGEST_SIGNING_KEY env var by default
  // Event key is read from INNGEST_EVENT_KEY env var by default
});
```

### Signing key security

- **Never hardcode** signing keys in source code
- Set `INNGEST_SIGNING_KEY` as an environment variable
- The signing key verifies that requests come from Inngest
- Use `signingKeyFallback` for key rotation:

```typescript
const inngest = new Inngest({
  id: "my-app",
  signingKeyFallback: process.env.INNGEST_SIGNING_KEY_FALLBACK,
});
```

### Streaming for serverless platforms

Enable streaming to bypass serverless timeout limits:

```typescript
serve({
  client: inngest,
  functions: allFunctions,
  streaming: "allow", // Use platform streaming if available
});
```

| Platform | Streaming Support | Benefit |
|----------|------------------|---------|
| Vercel | Yes | Extends beyond 10s/60s limit |
| Netlify | Yes | Extends beyond 10s limit |
| AWS Lambda | Via response streaming | Extends timeout |
| Cloudflare | Yes | Extends timeout |
