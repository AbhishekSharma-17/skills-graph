# Better Auth — Framework Integrations

> Source: [better-auth.com/docs/integrations](https://www.better-auth.com/docs/integrations) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Next.js](#nextjs)
- [Nuxt](#nuxt)
- [SvelteKit](#sveltekit)
- [Astro](#astro)
- [Hono](#hono)
- [Express](#express)
- [Remix / React Router v7](#remix--react-router-v7)
- [Expo (React Native)](#expo-react-native)
- [Other Frameworks](#other-frameworks)
- [Common Pitfalls](#common-pitfalls)

## Overview

Better Auth provides framework-specific handlers and helpers. The pattern is always:
1. Create the auth instance (`betterAuth()`)
2. Mount the handler to a catch-all API route
3. Create the client (`createAuthClient()`) with framework-specific import

## Next.js

### App Router Setup

```typescript
// app/api/auth/[...all]/route.ts
import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

export const { GET, POST } = toNextJsHandler(auth);
```

### Pages Router Setup

```typescript
// pages/api/auth/[...all].ts
import { toNodeHandler } from "better-auth/node";
import { auth } from "@/lib/auth";

export const config = { api: { bodyParser: false } };
export default toNodeHandler(auth.handler);
```

### Client

```typescript
import { createAuthClient } from "better-auth/react";
export const authClient = createAuthClient();
```

### Server Components

```typescript
import { auth } from "@/lib/auth";
import { headers } from "next/headers";

export default async function DashboardPage() {
  const session = await auth.api.getSession({
    headers: await headers(),
  });
  if (!session) redirect("/sign-in");
  return <h1>Welcome {session.user.name}</h1>;
}
```

### nextCookies Plugin

For automatic cookie handling in Server Actions:

```typescript
import { nextCookies } from "better-auth/next-js";

export const auth = betterAuth({
  plugins: [
    // ... other plugins
    nextCookies(), // Must be LAST
  ],
});
```

### Route Protection (Middleware/Proxy)

```typescript
// Next.js 16+ (proxy.ts)
import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";

export async function proxy(request: NextRequest) {
  const session = await auth.api.getSession({
    headers: await headers(),
  });
  if (!session) {
    return NextResponse.redirect(new URL("/sign-in", request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/dashboard/:path*"] };
```

```typescript
// Pre-16 (middleware.ts) — Cookie-only check (fast but less secure)
import { getSessionCookie } from "better-auth/cookies";

export function middleware(request: NextRequest) {
  const sessionCookie = getSessionCookie(request);
  if (!sessionCookie) {
    return NextResponse.redirect(new URL("/sign-in", request.url));
  }
  return NextResponse.next();
}
```

## Nuxt

### Server Setup

```typescript
// server/api/auth/[...all].ts
import { auth } from "~/lib/auth";
import { toH3Handler } from "better-auth/h3";

export default toH3Handler(auth);
```

### Client

```typescript
import { createAuthClient } from "better-auth/vue";
export const authClient = createAuthClient();
```

### Usage in Composables

```typescript
// composables/useAuth.ts
const { data: session } = authClient.useSession();
```

## SvelteKit

### Server Setup

```typescript
// src/hooks.server.ts
import { auth } from "$lib/auth";
import { svelteKitHandler } from "better-auth/svelte-kit";

export async function handle({ event, resolve }) {
  return svelteKitHandler({ event, resolve, auth });
}
```

### Client

```typescript
import { createAuthClient } from "better-auth/svelte";
export const authClient = createAuthClient();
```

### Usage in Components

```svelte
<script>
  import { authClient } from "$lib/auth-client";
  const session = authClient.useSession();
</script>

{#if $session.data}
  <p>Welcome {$session.data.user.name}</p>
{:else}
  <a href="/sign-in">Sign in</a>
{/if}
```

## Astro

### Server Setup

```typescript
// src/pages/api/auth/[...all].ts
import { auth } from "@/lib/auth";
import { toAstroHandler } from "better-auth/astro";

export const ALL = toAstroHandler(auth);
```

### Client

```typescript
import { createAuthClient } from "better-auth/client";
export const authClient = createAuthClient();
```

For React islands, use `better-auth/react` instead.

## Hono

### Server Setup

```typescript
import { Hono } from "hono";
import { auth } from "./auth";
import { toHonoHandler } from "better-auth/hono";

const app = new Hono();
app.on(["POST", "GET"], "/api/auth/**", toHonoHandler(auth));
```

### With Cloudflare Workers

```typescript
import { betterAuth } from "better-auth";

export default {
  fetch(request, env) {
    const auth = betterAuth({
      database: {
        // D1 or other Cloudflare database
      },
    });
    return auth.handler(request);
  },
};
```

## Express

### Server Setup

```typescript
import express from "express";
import { toNodeHandler } from "better-auth/node";
import { auth } from "./auth";

const app = express();

// Must be before body-parser middleware
app.all("/api/auth/*", toNodeHandler(auth));

app.listen(3000);
```

### With CORS

```typescript
import cors from "cors";

app.use(cors({
  origin: "http://localhost:5173", // Your frontend URL
  credentials: true, // Required for cookies
}));
```

## Remix / React Router v7

### Loader/Action Handler

```typescript
// app/routes/api.auth.$.tsx
import { auth } from "~/lib/auth";

export async function loader({ request }: LoaderFunctionArgs) {
  return auth.handler(request);
}

export async function action({ request }: ActionFunctionArgs) {
  return auth.handler(request);
}
```

### Client

```typescript
import { createAuthClient } from "better-auth/react";
export const authClient = createAuthClient();
```

## Expo (React Native)

### Client Setup

```typescript
import { createAuthClient } from "better-auth/react";
import { expoClient } from "@better-auth/expo";

const authClient = createAuthClient({
  baseURL: "https://your-server.com",
  plugins: [expoClient()],
  disableDefaultFetchPlugins: true, // No browser redirects
});
```

### Install Expo Plugin

```bash
npm install @better-auth/expo expo-secure-store expo-web-browser expo-linking
```

The Expo plugin:
- Uses `expo-secure-store` for session persistence
- Uses `expo-web-browser` for OAuth flows
- Handles deep linking for callbacks

## Other Frameworks

| Framework | Handler | Import |
|-----------|---------|--------|
| Fastify | `toNodeHandler` | `better-auth/node` |
| NestJS | `toNodeHandler` | `better-auth/node` |
| Elysia | Custom | See docs |
| Solid Start | `toSolidStartHandler` | `better-auth/solid-start` |
| TanStack Start | Custom | See docs |
| Waku | Custom | See docs |
| Electron | `toNodeHandler` | `better-auth/node` |
| Convex | Custom adapter | See docs |

### Generic Node.js Handler

For any Node.js framework:

```typescript
import { toNodeHandler } from "better-auth/node";
app.all("/api/auth/*", toNodeHandler(auth));
```

### Generic Web API Handler

For platforms with Web API `Request`/`Response`:

```typescript
// auth.handler accepts a standard Request and returns a Response
const response = await auth.handler(request);
```

## Common Pitfalls

1. **Body parser before auth** — In Express, mount the auth handler BEFORE body-parser middleware. Better Auth handles its own body parsing.
2. **Missing CORS credentials** — When client and server are on different origins, set `credentials: true` in CORS config.
3. **nextCookies plugin order** — Must be the last plugin in the array.
4. **SvelteKit handle function** — Must export as `handle` from `hooks.server.ts`, not a custom name.
5. **Expo OAuth callbacks** — Configure deep links in `app.json` and matching redirect URIs in your OAuth provider.
6. **Cloudflare Workers** — Create the auth instance inside the fetch handler to access env variables.
