# tRPC — Server Adapters

> Source: [trpc.io/docs/server/adapters](https://trpc.io/docs/server/adapters) | Version: 11.16.0

## Table of Contents

- [Adapter Overview](#adapter-overview)
- [Standalone (Node.js HTTP)](#standalone-nodejs-http)
- [Express](#express)
- [Fastify](#fastify)
- [Fetch / Edge Runtimes](#fetch--edge-runtimes)
- [Next.js](#nextjs)
- [AWS Lambda](#aws-lambda)
- [Cloudflare Workers](#cloudflare-workers)
- [HTTP/2 Server](#http2-server)
- [Choosing an Adapter](#choosing-an-adapter)

## Adapter Overview

Adapters connect tRPC routers to HTTP servers. Each adapter converts the server's request/response format into tRPC's internal format:

```
HTTP Request → Adapter → tRPC Router → Adapter → HTTP Response
```

All adapters need:
1. The `appRouter` instance
2. A `createContext` function (optional but recommended)

## Standalone (Node.js HTTP)

The simplest adapter — runs a plain Node.js HTTP server. Best for quick prototyping or serverful deployments:

```typescript
import { createHTTPServer } from '@trpc/server/adapters/standalone';
import { appRouter } from './router';
import { createContext } from './context';

const server = createHTTPServer({
  router: appRouter,
  createContext,

  // Optional CORS
  responseMeta() {
    return {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    };
  },
});

server.listen(3000);
console.log('tRPC server listening on port 3000');
```

### With Server-Sent Events

```typescript
import { createHTTPServer } from '@trpc/server/adapters/standalone';

const server = createHTTPServer({
  router: appRouter,
  createContext,
});

// SSE subscriptions work out of the box with standalone adapter
server.listen(3000);
```

## Express

Integrate tRPC as Express middleware alongside existing routes:

```typescript
import express from 'express';
import cors from 'cors';
import { createExpressMiddleware } from '@trpc/server/adapters/express';
import { appRouter } from './router';
import { createContext } from './context';

const app = express();

app.use(cors());

// Mount tRPC at /api/trpc
app.use(
  '/api/trpc',
  createExpressMiddleware({
    router: appRouter,
    createContext,
    onError({ error, path }) {
      console.error(`tRPC error on ${path}:`, error);
    },
  }),
);

// Regular Express routes still work
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(3000);
```

### Express Context with Request Access

```typescript
import { type CreateExpressContextOptions } from '@trpc/server/adapters/express';

export const createContext = async ({ req, res }: CreateExpressContextOptions) => {
  const token = req.headers.authorization?.split(' ')[1];
  const user = token ? await verifyToken(token) : null;

  return {
    db: prisma,
    user,
    req,
    res,
  };
};
```

## Fastify

Fastify v5+ adapter — registers tRPC as a Fastify plugin:

```typescript
import Fastify from 'fastify';
import {
  fastifyTRPCPlugin,
  type FastifyTRPCPluginOptions,
} from '@trpc/server/adapters/fastify';
import { appRouter, type AppRouter } from './router';
import { createContext } from './context';

const server = Fastify();

server.register(fastifyTRPCPlugin, {
  prefix: '/api/trpc',
  trpcOptions: {
    router: appRouter,
    createContext,
    onError({ error, path }) {
      console.error(`tRPC error on ${path}:`, error);
    },
  } satisfies FastifyTRPCPluginOptions<AppRouter>['trpcOptions'],
});

server.listen({ port: 3000 });
```

### Fastify Context

```typescript
import { type CreateFastifyContextOptions } from '@trpc/server/adapters/fastify';

export const createContext = async ({ req, res }: CreateFastifyContextOptions) => {
  return {
    db: prisma,
    user: await getUserFromRequest(req),
  };
};
```

## Fetch / Edge Runtimes

The fetch adapter works with any runtime that supports the Web Fetch API:

```typescript
import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { appRouter } from './router';

export default {
  async fetch(request: Request): Promise<Response> {
    return fetchRequestHandler({
      endpoint: '/api/trpc',
      req: request,
      router: appRouter,
      createContext: () => ({ db: prisma }),
    });
  },
};
```

Compatible runtimes:
- Cloudflare Workers
- Deno / Deno Deploy
- Bun
- Vercel Edge Runtime
- Remix loaders
- SvelteKit endpoints
- Astro API routes

## Next.js

### App Router (Fetch Adapter)

```typescript
// app/api/trpc/[trpc]/route.ts
import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { appRouter } from '@/server/router';
import { createTRPCContext } from '@/server/trpc';

const handler = (req: Request) =>
  fetchRequestHandler({
    endpoint: '/api/trpc',
    req,
    router: appRouter,
    createContext: () => createTRPCContext({ headers: req.headers }),
  });

export { handler as GET, handler as POST };
```

### Pages Router

```typescript
// pages/api/trpc/[trpc].ts
import { createNextApiHandler } from '@trpc/server/adapters/next';
import { appRouter } from '@/server/router';
import { createContext } from '@/server/context';

export default createNextApiHandler({
  router: appRouter,
  createContext,
});
```

## AWS Lambda

```typescript
import { awsLambdaRequestHandler } from '@trpc/server/adapters/aws-lambda';
import { appRouter } from './router';
import { createContext } from './context';

export const handler = awsLambdaRequestHandler({
  router: appRouter,
  createContext,
});
```

### With API Gateway Event

```typescript
import {
  awsLambdaRequestHandler,
  type CreateAWSLambdaContextOptions,
} from '@trpc/server/adapters/aws-lambda';
import type { APIGatewayProxyEventV2 } from 'aws-lambda';

export const createContext = async ({
  event,
}: CreateAWSLambdaContextOptions<APIGatewayProxyEventV2>) => {
  return {
    user: await getUserFromEvent(event),
  };
};

export const handler = awsLambdaRequestHandler({
  router: appRouter,
  createContext,
});
```

## Cloudflare Workers

Using the fetch adapter with Cloudflare bindings:

```typescript
// src/index.ts
import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { appRouter } from './router';

export interface Env {
  DB: D1Database;
  KV: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    return fetchRequestHandler({
      endpoint: '/api/trpc',
      req: request,
      router: appRouter,
      createContext: () => ({
        db: env.DB,
        kv: env.KV,
      }),
    });
  },
};
```

## HTTP/2 Server

v11 added HTTP/2 support:

```typescript
import { createHTTP2Handler } from '@trpc/server/adapters/standalone';
import { readFileSync } from 'fs';
import http2 from 'http2';

const handler = createHTTP2Handler({
  router: appRouter,
  createContext,
});

const server = http2.createSecureServer(
  {
    key: readFileSync('server.key'),
    cert: readFileSync('server.cert'),
  },
  handler,
);

server.listen(3000);
```

## Choosing an Adapter

| Scenario | Adapter |
|----------|---------|
| Quick prototype / standalone service | `standalone` |
| Adding tRPC to existing Express app | `express` |
| High-performance Node.js server | `fastify` |
| Next.js App Router | `fetch` |
| Next.js Pages Router | `next` |
| Cloudflare Workers / Deno / Bun | `fetch` |
| AWS Lambda + API Gateway | `aws-lambda` |
| SSE subscriptions needed | `standalone` or `express` |

## Common Pitfalls

1. **Match the `endpoint` to your route path** — `endpoint: '/api/trpc'` must match where the handler is mounted. Mismatches cause 404s.

2. **Fetch adapter doesn't expose `req`/`res`** — if you need raw Node.js request objects, use the Express or standalone adapter instead.

3. **Cloudflare Workers don't support WebSockets with tRPC** — use SSE subscriptions (httpSubscriptionLink) instead.

4. **Fastify requires v5+** — the tRPC Fastify adapter doesn't work with Fastify v4.
