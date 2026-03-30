# Better Auth — Server API

> Source: [better-auth.com/docs/concepts/api](https://www.better-auth.com/docs/concepts/api) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Auth Instance Creation](#auth-instance-creation)
- [Calling API Endpoints](#calling-api-endpoints)
- [Request Parameters](#request-parameters)
- [Response Handling](#response-handling)
- [Error Handling](#error-handling)
- [Core API Methods](#core-api-methods)
- [Framework Handlers](#framework-handlers)
- [Advanced Configuration](#advanced-configuration)
- [Common Pitfalls](#common-pitfalls)

## Overview

The `betterAuth()` function creates an auth instance that exposes:
- `auth.handler` — HTTP request handler for mounting as API routes
- `auth.api` — Server-side API object for direct function calls (no HTTP needed)

Server-side API calls bypass rate limiting and don't require HTTP round-trips.

## Auth Instance Creation

```typescript
import { betterAuth } from "better-auth";

export const auth = betterAuth({
  database: { /* ... */ },
  emailAndPassword: { enabled: true },
  socialProviders: { /* ... */ },
  session: { /* ... */ },
  plugins: [ /* ... */ ],
  advanced: { /* ... */ },
});
```

All plugins added to the auth instance automatically register their endpoints on the `auth.api` object.

## Calling API Endpoints

Import the auth instance and call methods on `auth.api`:

```typescript
import { auth } from "@/lib/auth";
import { headers } from "next/headers";

// Get current session
const session = await auth.api.getSession({
  headers: await headers(),
});

// Sign in programmatically
const result = await auth.api.signInEmail({
  body: {
    email: "user@example.com",
    password: "password123",
  },
});

// Verify email
await auth.api.verifyEmail({
  query: { token: "verification_token" },
});
```

## Request Parameters

API methods accept an object with three keys:

| Key | Type | Used For |
|-----|------|----------|
| `body` | `object` | POST request payload data |
| `headers` | `Headers` | HTTP headers (session cookies, tokens) |
| `query` | `object` | URL query parameters |

```typescript
// Body example (sign up)
await auth.api.signUpEmail({
  body: {
    email: "user@example.com",
    password: "password123",
    name: "John Doe",
  },
});

// Headers example (session access)
await auth.api.getSession({
  headers: await headers(),
});

// Query example (verification)
await auth.api.verifyEmail({
  query: { token: "abc123" },
});
```

## Response Handling

### Standard Response

API calls return JavaScript objects directly:

```typescript
const session = await auth.api.getSession({
  headers: await headers(),
});
// session = { user: { id, name, email, ... }, session: { id, token, ... } }
```

### Getting Response Headers

Use `returnHeaders: true` to access set-cookie headers:

```typescript
const { headers: responseHeaders, response } = await auth.api.signUpEmail({
  returnHeaders: true,
  body: {
    email: "user@example.com",
    password: "password123",
    name: "John Doe",
  },
});

const cookies = responseHeaders.getSetCookie();
```

### Getting Full Response Object

Use `asResponse: true` for the standard `Response` object:

```typescript
const response = await auth.api.signInEmail({
  body: { email: "user@example.com", password: "password123" },
  asResponse: true,
});
// response is a standard Response object
```

## Error Handling

Endpoints throw errors on failure. Use `APIError` and `isAPIError()`:

```typescript
import { APIError, isAPIError } from "better-auth/api";

try {
  await auth.api.signInEmail({
    body: { email: "user@example.com", password: "wrong" },
  });
} catch (error) {
  if (isAPIError(error)) {
    console.log(error.message); // "Invalid credentials"
    console.log(error.status);  // "UNAUTHORIZED"
  }
}
```

Common error statuses:
- `BAD_REQUEST` (400) — Invalid input
- `UNAUTHORIZED` (401) — Not authenticated
- `FORBIDDEN` (403) — Insufficient permissions
- `NOT_FOUND` (404) — Resource not found
- `TOO_MANY_REQUESTS` (429) — Rate limited

## Core API Methods

### Authentication

| Method | Description |
|--------|-------------|
| `auth.api.signUpEmail({ body })` | Register with email/password |
| `auth.api.signInEmail({ body })` | Sign in with email/password |
| `auth.api.signInSocial({ body })` | Initiate OAuth flow |
| `auth.api.signOut({ headers })` | End current session |

### Session

| Method | Description |
|--------|-------------|
| `auth.api.getSession({ headers })` | Get current user session |
| `auth.api.listSessions({ headers })` | List all active sessions |
| `auth.api.revokeSession({ body })` | Revoke a specific session |
| `auth.api.revokeSessions({ headers })` | Revoke all sessions |

### User Management

| Method | Description |
|--------|-------------|
| `auth.api.updateUser({ body, headers })` | Update profile |
| `auth.api.changePassword({ body, headers })` | Change password |
| `auth.api.changeEmail({ body, headers })` | Change email |
| `auth.api.deleteUser({ headers })` | Delete account |

### Email Verification

| Method | Description |
|--------|-------------|
| `auth.api.sendVerificationEmail({ body })` | Send verification email |
| `auth.api.verifyEmail({ query })` | Verify email token |

### Password Reset

| Method | Description |
|--------|-------------|
| `auth.api.forgetPassword({ body })` | Send reset email |
| `auth.api.resetPassword({ body })` | Reset with token |

## Framework Handlers

Mount the auth handler based on your framework:

```typescript
// Next.js App Router
import { toNextJsHandler } from "better-auth/next-js";
export const { GET, POST } = toNextJsHandler(auth);

// Next.js Pages Router
import { toNodeHandler } from "better-auth/node";
export default toNodeHandler(auth.handler);

// Express / Node.js
import { toNodeHandler } from "better-auth/node";
app.all("/api/auth/*", toNodeHandler(auth));

// Hono
import { toHonoHandler } from "better-auth/hono";
app.on(["POST", "GET"], "/api/auth/**", toHonoHandler(auth));

// SvelteKit
import { svelteKitHandler } from "better-auth/svelte-kit";
export async function handle({ event, resolve }) {
  return svelteKitHandler({ event, resolve, auth });
}

// Astro
import { toAstroHandler } from "better-auth/astro";
export const ALL = toAstroHandler(auth);
```

## Advanced Configuration

```typescript
export const auth = betterAuth({
  // Custom base path (default: /api/auth)
  basePath: "/auth",

  // App name for emails and OAuth
  appName: "My App",

  // Trusted origins for CORS
  trustedOrigins: ["https://app.example.com"],

  // Advanced options
  advanced: {
    // Custom IP detection headers
    ipAddress: {
      ipAddressHeaders: ["cf-connecting-ip", "x-forwarded-for"],
    },
    // Cross-subdomain cookies
    crossSubDomainCookies: {
      enabled: true,
      domain: ".example.com",
    },
    // Disable CSRF for specific routes
    disableCSRFCheck: false,
  },
});
```

## Common Pitfalls

1. **Not passing headers for session methods** — Methods like `getSession` need request headers to read the session cookie.
2. **Using `asResponse` when you want JSON** — By default, API calls return plain objects. Only use `asResponse` when you need the full `Response`.
3. **Forgetting `await`** — All API methods are async. Missing `await` gives you a Promise, not the result.
4. **Rate limiting on server-side calls** — Server-side `auth.api.*` calls bypass rate limiting. Only HTTP requests are rate-limited.
