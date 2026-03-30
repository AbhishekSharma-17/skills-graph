# Better Auth — Plugin System

> Source: [better-auth.com/docs/concepts/plugins](https://www.better-auth.com/docs/concepts/plugins) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Using Plugins](#using-plugins)
- [Plugin Architecture](#plugin-architecture)
- [Server Plugin Structure](#server-plugin-structure)
- [Creating Custom Endpoints](#creating-custom-endpoints)
- [Adding Database Schemas](#adding-database-schemas)
- [Plugin Hooks](#plugin-hooks)
- [Plugin Middleware](#plugin-middleware)
- [Client Plugin Structure](#client-plugin-structure)
- [Plugin Context](#plugin-context)
- [Available Official Plugins](#available-official-plugins)
- [Common Pitfalls](#common-pitfalls)

## Overview

Plugins are the primary extensibility mechanism in Better Auth. They can add custom API endpoints, database schemas, middleware, hooks, and rate limiting rules. Plugins have both server-side and client-side components.

## Using Plugins

### Server-Side

```typescript
import { betterAuth } from "better-auth";
import { twoFactor, admin, organization } from "better-auth/plugins";
import { passkey } from "@better-auth/passkey";

export const auth = betterAuth({
  plugins: [
    twoFactor(),
    admin(),
    organization(),
    passkey(),
  ],
});
```

### Client-Side

```typescript
import { createAuthClient } from "better-auth/react";
import { twoFactorClient, adminClient, organizationClient } from "better-auth/client/plugins";
import { passkeyClient } from "@better-auth/passkey/client";

const authClient = createAuthClient({
  plugins: [
    twoFactorClient(),
    adminClient(),
    organizationClient(),
    passkeyClient(),
  ],
});
```

**Important:** Always run `npx auth migrate` after adding plugins that modify the schema.

## Plugin Architecture

A plugin consists of:

| Component | Server | Client | Description |
|-----------|--------|--------|-------------|
| **Endpoints** | Yes | Inferred | Custom API routes |
| **Schema** | Yes | No | Database table definitions |
| **Hooks** | Yes | No | Before/after request handlers |
| **Middleware** | Yes | No | Route-specific logic |
| **Actions** | No | Yes | Custom client methods |
| **Atoms** | No | Yes | Reactive state (nanostores) |
| **Rate Limiting** | Yes | No | Per-endpoint throttling |

## Server Plugin Structure

```typescript
import type { BetterAuthPlugin } from "better-auth";

const myPlugin = (): BetterAuthPlugin => {
  return {
    id: "my-plugin",

    // Custom API endpoints
    endpoints: { /* ... */ },

    // Database schema additions
    schema: { /* ... */ },

    // Request lifecycle hooks
    hooks: { /* ... */ },

    // Route middleware
    middleware: { /* ... */ },

    // Rate limiting rules
    rateLimit: { /* ... */ },

    // Global request/response interceptors
    onRequest: async (request, ctx) => { /* ... */ },
    onResponse: async (response, ctx) => { /* ... */ },
  };
};
```

## Creating Custom Endpoints

```typescript
import { createAuthEndpoint } from "better-auth/api";
import { z } from "zod";

const myPlugin = (): BetterAuthPlugin => ({
  id: "my-plugin",
  endpoints: {
    // POST endpoint (data-modifying)
    createItem: createAuthEndpoint(
      "/my-plugin/create-item",
      {
        method: "POST",
        body: z.object({
          name: z.string(),
          description: z.string().optional(),
        }),
      },
      async (ctx) => {
        // Access session
        const session = await getSessionFromCtx(ctx);
        if (!session) throw new APIError("UNAUTHORIZED");

        // Access database
        const item = await ctx.context.adapter.create({
          model: "myItem",
          data: { name: ctx.body.name, userId: session.user.id },
        });

        return ctx.json(item);
      }
    ),

    // GET endpoint (read-only)
    listItems: createAuthEndpoint(
      "/my-plugin/list-items",
      {
        method: "GET",
        query: z.object({
          limit: z.number().optional(),
        }),
        use: [sessionMiddleware], // Require authentication
      },
      async (ctx) => {
        const items = await ctx.context.adapter.findMany({
          model: "myItem",
          where: [{ field: "userId", value: ctx.context.session.user.id }],
        });
        return ctx.json(items);
      }
    ),
  },
});
```

### Endpoint Naming Rules

- Use kebab-case paths: `/my-plugin/hello-world`
- Prefix with plugin name to avoid conflicts
- POST for data-modifying operations
- GET for read-only operations

## Adding Database Schemas

```typescript
const myPlugin = (): BetterAuthPlugin => ({
  id: "my-plugin",
  schema: {
    myItem: {
      fields: {
        name: { type: "string", required: true },
        description: { type: "string", required: false },
        status: { type: "string", defaultValue: "active" },
        userId: {
          type: "string",
          required: true,
          references: { model: "user", field: "id" },
        },
        createdAt: { type: "date", defaultValue: { type: "now" } },
      },
    },
  },
});
```

Field types: `string`, `number`, `boolean`, `date`.

## Plugin Hooks

```typescript
const myPlugin = (): BetterAuthPlugin => ({
  id: "my-plugin",
  hooks: {
    before: [
      {
        matcher: (ctx) => ctx.path === "/sign-up/email",
        handler: createAuthMiddleware(async (ctx) => {
          // Validate before sign-up
        }),
      },
    ],
    after: [
      {
        matcher: (ctx) => ctx.path.startsWith("/sign-in"),
        handler: createAuthMiddleware(async (ctx) => {
          // Post-sign-in logic
        }),
      },
    ],
  },
});
```

## Plugin Middleware

Middleware runs only on client-facing API calls (not server-side `auth.api.*`):

```typescript
const myPlugin = (): BetterAuthPlugin => ({
  id: "my-plugin",
  middleware: [
    {
      path: "/my-plugin/*",
      middleware: createAuthMiddleware(async (ctx) => {
        // Runs on all /my-plugin/* routes
        const session = await getSessionFromCtx(ctx);
        if (!session) {
          throw new APIError("UNAUTHORIZED");
        }
      }),
    },
  ],
});
```

## Client Plugin Structure

```typescript
import type { BetterAuthClientPlugin } from "better-auth/client";

const myPluginClient = () => {
  return {
    id: "my-plugin",

    // Infer endpoints from server plugin
    $InferServerPlugin: {} as ReturnType<typeof myPlugin>,

    // Custom client actions
    getActions: ($fetch, $store) => ({
      customMethod: async () => {
        return await $fetch("/my-plugin/custom", { method: "GET" });
      },
    }),

    // Reactive state atoms
    atomListeners: [
      {
        matcher: (path) => path === "/my-plugin/create-item",
        signal: "my-plugin-updated",
      },
    ],
  } satisfies BetterAuthClientPlugin;
};
```

Client plugins automatically convert server endpoint paths from kebab-case to camelCase:
- `/my-plugin/hello-world` → `authClient.myPlugin.helloWorld()`

## Plugin Context

Server plugins access rich context:

| Property | Description |
|----------|-------------|
| `ctx.context.appName` | Application name |
| `ctx.context.options` | Auth configuration |
| `ctx.context.tables` | Database table definitions |
| `ctx.context.baseURL` | Server base URL |
| `ctx.context.secret` | Encryption secret |
| `ctx.context.db` | Database client |
| `ctx.context.adapter` | Database adapter (CRUD operations) |
| `ctx.context.internalAdapter` | Internal adapter (user/session/account operations) |
| `ctx.context.logger` | Logger instance |

### Helper Functions

```typescript
import { getSessionFromCtx, sessionMiddleware } from "better-auth/api";

// Get session in plugin endpoint
const session = await getSessionFromCtx(ctx);

// Enforce authentication via middleware
use: [sessionMiddleware]
```

## Available Official Plugins

| Plugin | Package | Description |
|--------|---------|-------------|
| Two Factor | `better-auth/plugins` | TOTP, backup codes, trusted devices |
| Admin | `better-auth/plugins` | User management, roles, banning |
| Organization | `better-auth/plugins` | Multi-tenant workspaces |
| Magic Link | `better-auth/plugins` | Passwordless email links |
| Passkey | `@better-auth/passkey` | WebAuthn/FIDO2 authentication |
| Email OTP | `better-auth/plugins` | One-time password via email |
| Phone Number | `better-auth/plugins` | SMS-based authentication |
| API Key | `better-auth/plugins` | API key management |
| JWT | `better-auth/plugins` | JWT token support |
| Username | `better-auth/plugins` | Username-based auth |
| Anonymous | `better-auth/plugins` | Anonymous/guest sessions |
| Custom Session | `better-auth/plugins` | Extend session data |

## Common Pitfalls

1. **Missing client plugin** — Every server plugin with endpoints needs a matching client plugin.
2. **Not running migrations** — Plugins with schemas require `npx auth migrate`.
3. **Endpoint path conflicts** — Always prefix paths with your plugin name.
4. **Server-side middleware** — Plugin middleware only runs on HTTP requests, not `auth.api.*` calls.
5. **Plugin order** — Some plugins depend on others. Place framework-specific plugins (like `nextCookies`) last.
