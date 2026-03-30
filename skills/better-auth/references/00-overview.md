# Better Auth — Overview & Setup

> Source: [better-auth.com/docs](https://www.better-auth.com/docs) | Version: 1.5.6

## Table of Contents

- [What Is Better Auth](#what-is-better-auth)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Auth Instance Setup](#auth-instance-setup)
- [Database Configuration](#database-configuration)
- [Database Schema Creation](#database-schema-creation)
- [API Route Handler](#api-route-handler)
- [Client Instance Setup](#client-instance-setup)
- [Quickstart: Email & Password](#quickstart-email--password)
- [Quickstart: Social Login](#quickstart-social-login)
- [CLI Reference](#cli-reference)
- [Common Pitfalls](#common-pitfalls)

## What Is Better Auth

Better Auth is a framework-agnostic authentication and authorization library for TypeScript. It provides comprehensive built-in features (email/password, OAuth, sessions, rate limiting) plus a plugin ecosystem for advanced capabilities (2FA, passkeys, organizations, SSO).

Key differentiators:
- **Framework-agnostic** — works with Next.js, Nuxt, SvelteKit, Astro, Hono, Express, and 20+ frameworks
- **Database-flexible** — supports PostgreSQL, MySQL, SQLite, MongoDB via adapters for Prisma, Drizzle, and Kysely
- **Plugin-driven** — extend with 2FA, passkeys, organizations, admin, magic link, and more
- **TypeScript-first** — full type inference from server to client
- **Self-hosted** — no third-party auth service dependency

## Key Features

| Category | Features |
|----------|----------|
| **Authentication** | Email/password, 40+ OAuth providers, magic link, passkeys, email OTP |
| **Session Management** | Cookie-based, JWT caching, stateless mode, Redis secondary storage |
| **Authorization** | Role-based access control, custom permissions, admin plugin |
| **Multi-Tenancy** | Organizations, teams, members, invitations, dynamic roles |
| **Security** | 2FA/TOTP, rate limiting, CSRF protection, token encryption |
| **Developer Experience** | CLI for migrations, auto-generated schemas, TypeScript inference |

## Architecture

Better Auth follows a server-client architecture:

```
┌─────────────────────┐     ┌──────────────────────────────┐
│  Client (Browser)   │     │  Server (Node.js runtime)    │
│                     │     │                              │
│  createAuthClient() │────▶│  betterAuth() instance       │
│  - signIn/signUp    │     │  - API endpoints (/api/auth) │
│  - useSession()     │     │  - Database adapters         │
│  - Plugin clients   │     │  - Plugin server logic       │
└─────────────────────┘     └──────────────────────────────┘
```

- **Server**: The `betterAuth()` instance creates API endpoints, manages database operations, and handles authentication logic
- **Client**: The `createAuthClient()` provides type-safe methods to call server endpoints, with framework-specific hooks
- **Plugins**: Extend both server and client with additional endpoints, schemas, and UI logic

## Installation

```bash
# npm
npm install better-auth

# pnpm
pnpm add better-auth

# yarn
yarn add better-auth

# bun
bun add better-auth
```

If using separate client/server packages (e.g., monorepo), install in both.

## Environment Configuration

Create a `.env` file in your project root:

```env
# Required: 32+ character secret for encryption and signing
BETTER_AUTH_SECRET=your_generated_secret_here

# Required: Your application's base URL
BETTER_AUTH_URL=http://localhost:3000
```

Generate a secret:

```bash
openssl rand -base64 32
```

## Auth Instance Setup

Create `auth.ts` (or `lib/auth.ts`, `utils/auth.ts`):

```typescript
import { betterAuth } from "better-auth";

export const auth = betterAuth({
  // Database connection (required)
  database: {
    // See Database Configuration section
  },
  // Authentication methods
  emailAndPassword: {
    enabled: true,
  },
  // Social providers (optional)
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    },
  },
  // Plugins (optional)
  plugins: [],
});
```

## Database Configuration

Better Auth supports multiple database options:

```typescript
// SQLite (better-sqlite3)
import Database from "better-sqlite3";
export const auth = betterAuth({
  database: new Database("./sqlite.db"),
});

// PostgreSQL (pg)
import { Pool } from "pg";
export const auth = betterAuth({
  database: new Pool({
    connectionString: process.env.DATABASE_URL,
  }),
});

// MySQL (mysql2)
import { createPool } from "mysql2/promise";
export const auth = betterAuth({
  database: createPool({
    uri: process.env.DATABASE_URL,
  }),
});

// Prisma adapter
import { prismaAdapter } from "better-auth/adapters/prisma";
import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();
export const auth = betterAuth({
  database: prismaAdapter(prisma, { provider: "postgresql" }),
});

// Drizzle adapter
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "./db";
export const auth = betterAuth({
  database: drizzleAdapter(db, { provider: "pg" }),
});
```

## Database Schema Creation

Run the CLI to generate and apply tables:

```bash
# Interactive migration (creates tables, adds columns)
npx auth@latest migrate

# Generate schema files for your ORM (Prisma/Drizzle)
npx auth@latest generate
```

## API Route Handler

Mount the auth handler to your framework's catch-all route at `/api/auth/*`:

```typescript
// Next.js App Router — app/api/auth/[...all]/route.ts
import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";
export const { GET, POST } = toNextJsHandler(auth);

// Express
import { toNodeHandler } from "better-auth/node";
app.all("/api/auth/*", toNodeHandler(auth));

// Hono
import { toHonoHandler } from "better-auth/hono";
app.on(["POST", "GET"], "/api/auth/**", toHonoHandler(auth));
```

## Client Instance Setup

Create a client for frontend use:

```typescript
// lib/auth-client.ts
import { createAuthClient } from "better-auth/react"; // or /vue, /svelte, /solid, /client

export const authClient = createAuthClient({
  baseURL: "http://localhost:3000", // Your server URL
});
```

## Quickstart: Email & Password

```typescript
// Sign up
const { data, error } = await authClient.signUp.email({
  email: "user@example.com",
  password: "securepassword123",
  name: "Jane Doe",
  callbackURL: "/dashboard",
});

// Sign in
const { data, error } = await authClient.signIn.email({
  email: "user@example.com",
  password: "securepassword123",
  callbackURL: "/dashboard",
});

// Get session (reactive hook)
const { data: session, isPending } = authClient.useSession();

// Sign out
await authClient.signOut({
  fetchOptions: {
    onSuccess: () => router.push("/login"),
  },
});
```

## Quickstart: Social Login

```typescript
// Server config
export const auth = betterAuth({
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    },
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    },
  },
});

// Client sign-in
await authClient.signIn.social({
  provider: "github",
  callbackURL: "/dashboard",
});
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `npx auth@latest migrate` | Run database migrations interactively |
| `npx auth@latest generate` | Generate schema files for ORM |
| `npx auth@latest init` | Initialize a new Better Auth project |

## Common Pitfalls

1. **Missing `BETTER_AUTH_SECRET`** — Auth will fail silently or throw cryptographic errors. Always set a 32+ character secret.
2. **Forgetting to run migrations** — After adding plugins, always run `npx auth migrate` to create new tables/columns.
3. **Wrong base URL** — The `BETTER_AUTH_URL` must match your actual server URL, including port.
4. **Not mounting the catch-all route** — The handler must be at `/api/auth/[...all]` (or equivalent). Missing this causes 404s on all auth endpoints.
5. **Installing only on one side** — In monorepos, install `better-auth` in both client and server packages.
6. **Not placing `nextCookies()` plugin last** — In Next.js, the `nextCookies` plugin must be the last plugin in the array.
