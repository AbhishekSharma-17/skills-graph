# tRPC — Overview & Setup

> Source: [trpc.io/docs](https://trpc.io/docs) | Version: 11.16.0

## Table of Contents

- [What is tRPC](#what-is-trpc)
- [Core Philosophy](#core-philosophy)
- [Package Ecosystem](#package-ecosystem)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [When to Use tRPC](#when-to-use-trpc)
- [When NOT to Use tRPC](#when-not-to-use-trpc)

## What is tRPC

tRPC (TypeScript Remote Procedure Call) enables end-to-end typesafe APIs between a TypeScript client and server. You define procedures on the server, and the client gets full autocompletion and type checking — no code generation, no schemas to sync, no build step.

Key characteristics:
- **Zero code generation** — types are inferred directly from your server code
- **Full-stack TypeScript** — requires TypeScript on both client and server
- **Framework agnostic** — works with React, Next.js, Express, Fastify, Cloudflare Workers, etc.
- **Built on standards** — uses HTTP (GET for queries, POST for mutations) with JSON by default
- **39k+ GitHub stars** — battle-tested in production by thousands of projects

## Core Philosophy

tRPC leverages TypeScript's type inference to create a contract between client and server at compile time. When you change a procedure's input or output on the server, the client immediately sees type errors — no API documentation or OpenAPI specs needed.

```
Server defines procedure → TypeScript infers types → Client gets autocompletion
```

The trade-off: tRPC is designed for TypeScript monorepos or projects where both client and server share types. If you need a public API consumed by third parties or non-TypeScript clients, use REST/GraphQL with OpenAPI specs instead.

## Package Ecosystem

| Package | Purpose |
|---------|---------|
| `@trpc/server` | Core server — routers, procedures, context, middleware |
| `@trpc/client` | Vanilla TypeScript client — works anywhere |
| `@trpc/tanstack-react-query` | React Query v5 integration (recommended for React) |
| `@trpc/react-query` | Legacy React Query integration (v10 compatibility) |
| `@trpc/next` | Next.js-specific adapter and utilities |
| `zod` | Input/output validation (recommended, not required) |

## Installation

### Minimal Setup (Server + Client)

```bash
npm install @trpc/server @trpc/client zod
```

### Full React/Next.js Stack

```bash
npm install @trpc/server @trpc/client @trpc/tanstack-react-query @tanstack/react-query zod
```

### With Next.js Adapter

```bash
npm install @trpc/server @trpc/client @trpc/tanstack-react-query @trpc/next @tanstack/react-query zod
```

## Quickstart

### Step 1: Initialize tRPC on the Server

```typescript
// server/trpc.ts
import { initTRPC } from '@trpc/server';

const t = initTRPC.create();

export const router = t.router;
export const publicProcedure = t.procedure;
```

### Step 2: Define Your Router

```typescript
// server/router.ts
import { z } from 'zod';
import { router, publicProcedure } from './trpc';

export const appRouter = router({
  hello: publicProcedure
    .input(z.object({ name: z.string() }))
    .query(({ input }) => {
      return { greeting: `Hello, ${input.name}!` };
    }),

  createUser: publicProcedure
    .input(z.object({
      name: z.string().min(1),
      email: z.string().email(),
    }))
    .mutation(({ input }) => {
      // Insert into database
      return { id: '1', ...input };
    }),
});

// Export the router type for client usage
export type AppRouter = typeof appRouter;
```

### Step 3: Serve the API

```typescript
// server/index.ts
import { createHTTPServer } from '@trpc/server/adapters/standalone';
import { appRouter } from './router';

const server = createHTTPServer({
  router: appRouter,
});

server.listen(3000);
```

### Step 4: Create a Client

```typescript
// client/index.ts
import { createTRPCClient, httpBatchLink } from '@trpc/client';
import type { AppRouter } from '../server/router';

const trpc = createTRPCClient<AppRouter>({
  links: [
    httpBatchLink({
      url: 'http://localhost:3000',
    }),
  ],
});

// Fully typed — autocompletion works here
const result = await trpc.hello.query({ name: 'World' });
console.log(result.greeting); // "Hello, World!"

const user = await trpc.createUser.mutate({
  name: 'Alice',
  email: 'alice@example.com',
});
```

## Project Structure

### Typical Monorepo Layout

```
my-app/
├── packages/
│   ├── api/                    # @trpc/server
│   │   ├── src/
│   │   │   ├── trpc.ts         # initTRPC + base procedures
│   │   │   ├── router.ts       # Root router (merges sub-routers)
│   │   │   ├── routers/
│   │   │   │   ├── user.ts     # User procedures
│   │   │   │   ├── post.ts     # Post procedures
│   │   │   │   └── auth.ts     # Auth procedures
│   │   │   ├── middleware/
│   │   │   │   └── auth.ts     # Auth middleware
│   │   │   └── context.ts      # Context creation
│   │   └── package.json
│   └── web/                    # Next.js / React frontend
│       ├── src/
│       │   ├── trpc/
│       │   │   ├── client.ts   # tRPC React client setup
│       │   │   └── server.ts   # Server-side caller
│       │   └── app/
│       │       └── api/trpc/[trpc]/route.ts
│       └── package.json
└── package.json
```

### Next.js App Router Layout

```
my-nextjs-app/
├── src/
│   ├── server/
│   │   ├── trpc.ts             # initTRPC
│   │   ├── routers/
│   │   │   ├── _app.ts         # Root router
│   │   │   ├── user.ts
│   │   │   └── post.ts
│   │   └── context.ts
│   ├── trpc/
│   │   ├── client.tsx          # React Query client wrapper
│   │   ├── server.ts           # Server-side utilities
│   │   └── query-client.ts     # TanStack Query client
│   └── app/
│       └── api/trpc/[trpc]/route.ts
└── package.json
```

## How It Works

1. **Server defines procedures** with optional input validation (e.g., Zod schemas)
2. **TypeScript infers** the full type of each procedure (input + output)
3. **`AppRouter` type is exported** from the server package
4. **Client imports the type** (type-only import — no runtime code crosses the boundary)
5. **Client proxy** uses the type to provide autocompletion and type checking
6. **At runtime**, HTTP requests are made with JSON payloads

The type sharing happens at compile time only. No server code is bundled into the client.

## When to Use tRPC

- **Internal APIs** in TypeScript monorepos
- **Full-stack Next.js / React apps** where you control both ends
- **Rapid prototyping** — skip API documentation overhead
- **Teams using TypeScript everywhere** — maximum type safety payoff
- **T3 Stack** projects (Next.js + tRPC + Prisma + Tailwind)

## When NOT to Use tRPC

- **Public APIs** consumed by third parties (use REST + OpenAPI or GraphQL)
- **Non-TypeScript clients** (Python, Go, mobile) — types can't be shared
- **Microservices with different languages** — tRPC is TypeScript-to-TypeScript
- **When you need REST conventions** — tRPC uses its own URL scheme

For public + internal hybrid APIs, consider using tRPC internally and `trpc-openapi` to expose REST endpoints for external consumers.
