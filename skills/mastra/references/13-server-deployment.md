# Mastra — Server & Deployment

> Source: [mastra.ai/docs/server](https://mastra.ai/docs/server/mastra-server) · [mastra.ai/docs/deployment](https://mastra.ai/docs/deployment/overview) · `@mastra/core` v1.37.x

## Table of Contents

- [Server Overview](#server-overview)
- [Server Configuration](#server-configuration)
- [API Endpoints](#api-endpoints)
- [Custom Routes](#custom-routes)
- [Middleware](#middleware)
- [Authentication](#authentication)
- [Request Context](#request-context)
- [Stream Data Redaction](#stream-data-redaction)
- [Server Adapters](#server-adapters)
- [Deployment Options](#deployment-options)
- [Build and Deploy](#build-and-deploy)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

## Server Overview

Mastra runs an HTTP server built on Hono. It automatically generates API endpoints for all registered agents and workflows, plus supports custom routes and middleware.

## Server Configuration

```typescript
import { Mastra } from '@mastra/core'

export const mastra = new Mastra({
  agents: { myAgent },
  workflows: { myWorkflow },
  server: {
    port: 4111,        // Default: 4111
    host: 'localhost', // Default: localhost
  },
})
```

### Development Server

```bash
npx mastra dev
# Starts server + Studio UI at http://localhost:4111
```

### Production Build

```bash
npx mastra build
# Generates optimized server in .mastra/ directory
```

## API Endpoints

Mastra auto-generates endpoints:

### Agent Endpoints

```
POST /api/agents/:agentId/generate
POST /api/agents/:agentId/stream
GET  /api/agents/:agentId
GET  /api/agents
```

### Workflow Endpoints

```
POST /api/workflows/:workflowId/start
POST /api/workflows/:workflowId/stream
POST /api/workflows/:workflowId/:runId/resume
GET  /api/workflows/:workflowId
GET  /api/workflows
```

### API Documentation

```
GET /api/openapi.json    # OpenAPI spec (dev only)
GET /swagger-ui          # Swagger UI (dev only)
```

Both are disabled in production by default.

## Custom Routes

Add your own HTTP endpoints with access to the Mastra instance:

```typescript
import { Mastra } from '@mastra/core'

export const mastra = new Mastra({
  agents: { myAgent },
  server: {
    routes: (app, mastra) => {
      app.get('/health', (c) => c.json({ status: 'ok' }))

      app.post('/custom/analyze', async (c) => {
        const { text } = await c.req.json()
        const agent = mastra.getAgentById('my-agent')
        const result = await agent.generate(`Analyze: ${text}`)
        return c.json({ analysis: result.text })
      })
    },
  },
})
```

## Middleware

Intercept requests for authentication, logging, CORS, or context injection:

```typescript
import { Mastra } from '@mastra/core'

export const mastra = new Mastra({
  server: {
    middleware: [
      // CORS
      async (c, next) => {
        c.res.headers.set('Access-Control-Allow-Origin', '*')
        await next()
      },
      // Request logging
      async (c, next) => {
        const start = Date.now()
        await next()
        console.log(`${c.req.method} ${c.req.url} - ${Date.now() - start}ms`)
      },
    ],
  },
})
```

## Authentication

Secure endpoints using common auth providers:

### JWT Authentication

```typescript
middleware: [
  async (c, next) => {
    const token = c.req.header('Authorization')?.replace('Bearer ', '')
    if (!token) return c.json({ error: 'Unauthorized' }, 401)

    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET)
      c.set('user', decoded)
      await next()
    } catch {
      return c.json({ error: 'Invalid token' }, 401)
    }
  },
]
```

### Supported Auth Providers

Mastra can integrate with:
- **Clerk** — session-based auth
- **Supabase** — JWT + RLS
- **Firebase** — ID tokens
- **Auth0** — OIDC
- **WorkOS** — enterprise SSO
- **Better Auth** — session middleware

## Request Context

Pass runtime-specific values to agents, tools, and workflows via middleware:

```typescript
middleware: [
  async (c, next) => {
    const user = c.get('user')
    c.set('requestContext', new Map([
      ['user-id', user.id],
      ['user-tier', user.tier],
      ['locale', c.req.header('Accept-Language') || 'en'],
    ]))
    await next()
  },
]
```

Agents and workflow steps access this via `requestContext.get('user-id')`.

## Stream Data Redaction

Mastra automatically redacts sensitive data from response streams:

- System prompts
- Tool definitions
- API keys
- Internal configuration

This prevents leaking implementation details to clients consuming streamed responses.

## Server Adapters

Run Mastra with different HTTP frameworks:

### Express Adapter

```typescript
import express from 'express'
import { createExpressAdapter } from '@mastra/core/server/express'

const app = express()
const mastraRouter = createExpressAdapter(mastra)
app.use('/api', mastraRouter)
app.listen(3000)
```

### Hono (Built-in)

Mastra uses Hono natively. The built-in server is a Hono app.

### Custom Adapter

```typescript
import { createServerAdapter } from '@mastra/core/server'

const handler = createServerAdapter(mastra)
// Use with any HTTP framework that supports Request/Response
```

## Deployment Options

### Standalone Server

```bash
npx mastra build
node .mastra/output/index.mjs
```

Deploy to VMs, containers, or PaaS platforms.

### Docker

```dockerfile
FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY .mastra/ .mastra/
EXPOSE 4111
CMD ["node", ".mastra/output/index.mjs"]
```

### Cloud Providers

| Provider | Method |
|----------|--------|
| **Vercel** | Built-in deployer or serverless functions |
| **Netlify** | Built-in deployer |
| **Cloudflare** | Workers or built-in deployer |
| **AWS** | EC2, Lambda, ECS |
| **Azure** | App Services, Container Apps |
| **Digital Ocean** | App Platform, Droplets |
| **Railway** | Docker deployment |

### Built-in Deployers

```typescript
import { VercelDeployer } from '@mastra/deployer-vercel'

export const mastra = new Mastra({
  deployer: new VercelDeployer({
    teamId: process.env.VERCEL_TEAM_ID,
  }),
})
```

### Web Framework Integration

When integrated with Next.js, Astro, or other frameworks, Mastra deploys alongside your application:

```typescript
// Next.js API route
import { mastra } from '@/mastra'

export async function POST(req: Request) {
  const { message } = await req.json()
  const agent = mastra.getAgentById('my-agent')
  const result = await agent.generate(message)
  return Response.json({ text: result.text })
}
```

### Mastra Platform

Hosted platform offering:
- **Observability** — traces, logs, metrics dashboard
- **Studio** — agent testing and workflow debugging
- **Server** — managed production API deployment

### Workflow Deployment to Inngest

For production workflow orchestration with retries and monitoring:

```typescript
import { InngestDeployer } from '@mastra/deployer-inngest'

export const mastra = new Mastra({
  workflows: { myWorkflow },
  deployer: new InngestDeployer({
    inngestApiKey: process.env.INNGEST_API_KEY,
  }),
})
```

## Build and Deploy

```bash
# Development
npx mastra dev          # Dev server + Studio

# Production build
npx mastra build        # Build for deployment

# Deploy (with deployer configured)
npx mastra deploy       # Deploy to configured platform
```

### Supported Runtimes

- Node.js v22.13.0+
- Bun
- Deno
- Cloudflare Workers

## Common Patterns

### API Gateway with Auth

```typescript
const mastra = new Mastra({
  agents: { publicAgent, internalAgent },
  server: {
    middleware: [authMiddleware, rateLimitMiddleware],
    routes: (app, mastra) => {
      app.post('/v1/chat', async (c) => {
        const user = c.get('user')
        const agentId = user.tier === 'enterprise' ? 'internalAgent' : 'publicAgent'
        const agent = mastra.getAgentById(agentId)
        const stream = await agent.stream(c.req.json().message, {
          requestContext: new Map([['user-id', user.id]]),
        })
        return c.stream(stream.textStream)
      })
    },
  },
})
```

## Pitfalls

1. **Port 4111 is the default** — change it if it conflicts with other services
2. **Swagger UI is dev-only** — it's disabled in production by default for security
3. **Middleware order matters** — auth should run before custom routes
4. **Node.js v22.13.0+** required — older versions are not supported
5. **Build before deploying** — `mastra build` generates the production server; don't deploy the source directly
6. **Stream redaction is automatic** — don't send raw LLM streams to clients without the Mastra server layer
