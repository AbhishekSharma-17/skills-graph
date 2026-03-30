# Better Auth — Client SDK

> Source: [better-auth.com/docs/concepts/client](https://www.better-auth.com/docs/concepts/client) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Framework Imports](#framework-imports)
- [Client Initialization](#client-initialization)
- [Authentication Methods](#authentication-methods)
- [Session Management](#session-management)
- [Session Options](#session-options)
- [Error Handling](#error-handling)
- [Fetch Options](#fetch-options)
- [Client Plugins](#client-plugins)
- [Common Pitfalls](#common-pitfalls)

## Overview

The Better Auth client provides type-safe methods to interact with the auth server. It offers framework-specific hooks (React, Vue, Svelte, Solid) and a vanilla client for non-framework environments.

## Framework Imports

```typescript
// React (hooks with useState/useEffect)
import { createAuthClient } from "better-auth/react";

// Vue (composables with ref/computed)
import { createAuthClient } from "better-auth/vue";

// Svelte (stores)
import { createAuthClient } from "better-auth/svelte";

// Solid (signals)
import { createAuthClient } from "better-auth/solid";

// Vanilla (no framework, plain fetch)
import { createAuthClient } from "better-auth/client";
```

## Client Initialization

```typescript
const authClient = createAuthClient({
  // Server base URL (required if different from current origin)
  baseURL: "http://localhost:3000",

  // Custom base path (must match server config)
  basePath: "/api/auth", // default

  // Plugins (must mirror server plugins)
  plugins: [],
});
```

For same-origin setups (client and server on same domain), `baseURL` can be omitted.

## Authentication Methods

### Email/Password Sign Up

```typescript
const { data, error } = await authClient.signUp.email({
  email: "user@example.com",
  password: "securepassword123", // min 8 chars by default
  name: "Jane Doe",
  image: "https://example.com/avatar.jpg", // optional
  callbackURL: "/dashboard",
});
```

### Email/Password Sign In

```typescript
const { data, error } = await authClient.signIn.email({
  email: "user@example.com",
  password: "securepassword123",
  callbackURL: "/dashboard",
  rememberMe: true, // default: true
});
```

### Social Sign In

```typescript
await authClient.signIn.social({
  provider: "github", // or google, discord, etc.
  callbackURL: "/dashboard",
});
```

### Sign Out

```typescript
await authClient.signOut({
  fetchOptions: {
    onSuccess: () => {
      router.push("/login");
    },
  },
});
```

### Callback Hooks

All sign-in/sign-up methods support lifecycle callbacks:

```typescript
const { data, error } = await authClient.signIn.email({
  email: "user@example.com",
  password: "password",
  fetchOptions: {
    onRequest: (ctx) => {
      // Show loading spinner
    },
    onSuccess: (ctx) => {
      // Redirect or update UI
    },
    onError: (ctx) => {
      // Show error message
      alert(ctx.error.message);
    },
  },
});
```

## Session Management

### Reactive Session Hook

The `useSession()` hook provides reactive session data:

```typescript
// React
function Dashboard() {
  const { data: session, isPending, error, refetch } = authClient.useSession();

  if (isPending) return <div>Loading...</div>;
  if (!session) return <div>Not authenticated</div>;

  return <h1>Welcome {session.user.name}</h1>;
}
```

```typescript
// Vue
const { data: session, isPending } = authClient.useSession();
```

```typescript
// Svelte
const session = authClient.useSession();
// Access: $session.data, $session.isPending
```

### One-Time Fetch

For non-reactive contexts:

```typescript
const { data: session } = await authClient.getSession();
```

### List Active Sessions

```typescript
const { data: sessions } = await authClient.listSessions();
```

### Revoke Sessions

```typescript
// Revoke specific session
await authClient.revokeSession({ token: "session-token" });

// Revoke all other sessions
await authClient.revokeOtherSessions();

// Revoke all sessions (logs out everywhere)
await authClient.revokeSessions();
```

## Session Options

Configure automatic session refresh behavior:

```typescript
const { data: session } = authClient.useSession({
  // Refetch session every 5 minutes
  refetchInterval: 5 * 60 * 1000,

  // Refetch when window regains focus
  refetchOnWindowFocus: true,

  // Whether to refetch when offline
  refetchWhenOffline: false,
});
```

## Error Handling

### Response Structure

All client methods return `{ data, error }`:

```typescript
const { data, error } = await authClient.signIn.email({
  email: "user@example.com",
  password: "password",
});

if (error) {
  console.log(error.message);  // Human-readable message
  console.log(error.status);   // HTTP status code
  console.log(error.code);     // Error code string
}
```

### Error Code Mapping

Map error codes to custom messages (useful for i18n):

```typescript
const authClient = createAuthClient({
  // ...
});

// Access error codes
const errorMap = authClient.$ERROR_CODES;
```

### Per-Request Error Handling

```typescript
await authClient.signIn.email({
  email: "user@example.com",
  password: "password",
  fetchOptions: {
    onError: (ctx) => {
      if (ctx.response.status === 429) {
        const retryAfter = ctx.response.headers.get("X-Retry-After");
        toast.error(`Rate limited. Retry in ${retryAfter}s`);
      }
    },
  },
});
```

## Fetch Options

Customize HTTP behavior globally or per-request:

```typescript
// Global fetch options
const authClient = createAuthClient({
  fetchOptions: {
    // Custom headers
    headers: { "X-Custom-Header": "value" },

    // Global error handler
    onError: async (ctx) => {
      if (ctx.response.status === 429) {
        const retryAfter = ctx.response.headers.get("X-Retry-After");
        console.log(`Rate limited. Retry after ${retryAfter}s`);
      }
    },
  },
});

// Per-request fetch options
await authClient.signIn.email({
  email: "user@example.com",
  password: "password",
  fetchOptions: {
    onRequest: (ctx) => { /* before request */ },
    onSuccess: (ctx) => { /* on success */ },
    onError: (ctx) => { /* on error */ },
  },
});
```

### Disabling Default Plugins

For non-browser environments (React Native, Electron):

```typescript
const authClient = createAuthClient({
  disableDefaultFetchPlugins: true,
});
```

## Client Plugins

Add client-side plugins to match server plugins:

```typescript
import { createAuthClient } from "better-auth/react";
import { organizationClient } from "better-auth/client/plugins";
import { passkeyClient } from "@better-auth/passkey/client";
import { twoFactorClient } from "better-auth/client/plugins";

const authClient = createAuthClient({
  plugins: [
    organizationClient(),
    passkeyClient(),
    twoFactorClient(),
  ],
});
```

Client plugins provide:
- Type-safe methods that map to server endpoints
- Reactive state atoms (for hooks like `useSession`)
- Custom actions and helpers

## Common Pitfalls

1. **Mismatched plugins** — Server and client plugins must be paired. Adding `organization()` on server requires `organizationClient()` on client.
2. **Missing `baseURL`** — Required when client and server are on different origins.
3. **Using vanilla client in React** — Import from `better-auth/react`, not `better-auth/client`, to get hooks.
4. **Not handling the `error` return** — Always check `error` before using `data`.
5. **Session hook outside component** — `useSession()` must be called inside a React component (or equivalent framework context).
