# Better Auth — Session Management

> Source: [better-auth.com/docs/concepts/session-management](https://www.better-auth.com/docs/concepts/session-management) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Session Configuration](#session-configuration)
- [Session Expiration & Refresh](#session-expiration--refresh)
- [Session Freshness](#session-freshness)
- [Cookie Caching](#cookie-caching)
- [Caching Strategies](#caching-strategies)
- [Stateless Sessions](#stateless-sessions)
- [Secondary Storage (Redis)](#secondary-storage-redis)
- [Custom Session Data](#custom-session-data)
- [Session API Methods](#session-api-methods)
- [Common Pitfalls](#common-pitfalls)

## Overview

Better Auth uses cookie-based session management. When a user signs in, a session record is created in the database and a session token is set as an HTTP cookie. On each request, the server validates the cookie against the database and returns user data if valid.

Core session fields: `id`, `token`, `userId`, `expiresAt`, `ipAddress`, `userAgent`, `createdAt`, `updatedAt`.

## Session Configuration

```typescript
export const auth = betterAuth({
  session: {
    expiresIn: 60 * 60 * 24 * 7,  // 7 days (default)
    updateAge: 60 * 60 * 24,       // Refresh every 1 day (default)
    disableSessionRefresh: false,   // Set true to disable auto-refresh
  },
});
```

- `expiresIn`: Total session lifetime in seconds
- `updateAge`: How often to refresh the expiration (on active use)
- When a session is used and `updateAge` has elapsed, `expiresAt` resets to `now + expiresIn`

## Session Expiration & Refresh

### Default Behavior

Sessions expire after 7 days. Active sessions refresh every 24 hours.

### Disable Refresh

```typescript
session: { disableSessionRefresh: true }
```

### Deferred Refresh

Makes GET requests read-only. Returns `needsRefresh: true` when refresh is needed, and the client auto-triggers a POST refresh:

```typescript
session: { deferSessionRefresh: true }
```

## Session Freshness

Freshness ensures a session was recently created — required for sensitive operations like changing passwords or enabling 2FA.

```typescript
session: {
  freshAge: 60 * 60 * 24,  // 1 day (default)
  // freshAge: 60 * 5,      // 5 minutes (stricter)
  // freshAge: 0,            // Disable freshness checks
}
```

If a session isn't fresh enough, the endpoint returns an error prompting re-authentication.

## Cookie Caching

Cookie caching stores session data in short-lived signed cookies, reducing database queries. The server validates sessions from cookies alone during the cache window.

```typescript
session: {
  cookieCache: {
    enabled: true,
    maxAge: 5 * 60, // 5 minutes cache duration
  },
}
```

**Important:** Revoked sessions remain active on cached clients until the cache expires. The server cannot remotely delete client cookies.

### Bypass Cache

Force a fresh database lookup:

```typescript
const session = await authClient.getSession({
  query: { disableCookieCache: true },
});
```

## Caching Strategies

| Strategy | Size | Security | Readable | Interoperable | Use Case |
|----------|------|----------|----------|---------------|----------|
| `compact` | Smallest | Signed | Yes | No | Performance-critical apps |
| `jwt` | Medium | Signed | Yes | Yes | Third-party integrations |
| `jwe` | Largest | Encrypted | No | Yes | Maximum security |

```typescript
session: {
  cookieCache: {
    enabled: true,
    maxAge: 5 * 60,
    strategy: "compact", // or "jwt" or "jwe"
  },
}
```

## Stateless Sessions

Operate without a database by using signed/encrypted cookies only. Useful for edge deployments and serverless.

### Automatic Stateless

If no database is configured, Better Auth defaults to stateless mode:

```typescript
const auth = betterAuth({
  // No database config
  socialProviders: { /* ... */ },
});
```

### Manual Stateless Config

```typescript
session: {
  cookieCache: {
    enabled: true,
    maxAge: 7 * 24 * 60 * 60, // 7 days
    strategy: "jwe",
    refreshCache: true, // Auto-refresh before expiry
  },
},
account: {
  storeStateStrategy: "cookie",
  storeAccountCookie: true,
},
```

### Refresh Options

```typescript
// No auto-refresh (default)
refreshCache: false

// Refresh at 80% of maxAge
refreshCache: true

// Custom: refresh when 60s remaining
refreshCache: { updateAge: 60 }
```

### Session Versioning

Invalidate all sessions by changing the version:

```typescript
session: {
  cookieCache: {
    version: "2", // Forces all users to re-authenticate
  },
}
```

## Secondary Storage (Redis)

Offload sessions to Redis for high-performance read/write:

```typescript
import { redisStorage } from "@better-auth/redis-storage";
import { Redis } from "ioredis";

const redis = new Redis({ host: "localhost", port: 6379 });

export const auth = betterAuth({
  secondaryStorage: redisStorage({
    client: redis,
    keyPrefix: "better-auth:",
  }),
});
```

By default, when secondary storage is configured, sessions are stored there instead of the database.

```typescript
// Force database storage alongside secondary storage
session: { storeSessionInDatabase: true }

// Keep revoked sessions in database for audit
session: { preserveSessionInDatabase: true }
```

### Custom Secondary Storage

Implement the `SecondaryStorage` interface:

```typescript
secondaryStorage: {
  get: async (key) => await redis.get(key),
  set: async (key, value, ttl) => await redis.set(key, value, "EX", ttl),
  delete: async (key) => await redis.del(key),
}
```

## Custom Session Data

Use the `customSession` plugin to extend session responses:

```typescript
import { customSession } from "better-auth/plugins";

export const auth = betterAuth({
  plugins: [
    customSession(async ({ user, session }) => ({
      roles: await findUserRoles(session.session.userId),
      user: { ...user, displayName: user.name.toUpperCase() },
      session,
    })),
  ],
});
```

Client-side type inference:

```typescript
import { customSessionClient } from "better-auth/client/plugins";
import type { auth } from "@/lib/auth";

const authClient = createAuthClient({
  plugins: [customSessionClient<typeof auth>()],
});

// data.roles and data.user.displayName are typed
const { data } = authClient.useSession();
```

**Caveat:** Custom fields are not included in cookie caching — the callback runs on each session fetch.

## Session API Methods

| Client Method | Description |
|---------------|-------------|
| `authClient.useSession()` | Reactive session hook |
| `authClient.getSession()` | One-time session fetch |
| `authClient.listSessions()` | List all active sessions |
| `authClient.revokeSession({ token })` | Revoke specific session |
| `authClient.revokeOtherSessions()` | Revoke all except current |
| `authClient.revokeSessions()` | Revoke all sessions |
| `authClient.updateSession({ key: value })` | Update custom session fields |

| Server Method | Description |
|---------------|-------------|
| `auth.api.getSession({ headers })` | Get session from headers |
| `auth.api.listSessions({ headers })` | List user sessions |
| `auth.api.revokeSession({ body: { token } })` | Revoke by token |
| `auth.api.revokeSessions({ headers })` | Revoke all user sessions |

## Common Pitfalls

1. **Cookie cache hiding revoked sessions** — Revoked sessions stay active until cache expires on other devices. Use short `maxAge` (5 min) for security-sensitive apps.
2. **Missing `storeSessionInDatabase`** — When using secondary storage, sessions are not in the database by default. Set this flag if you need database session records.
3. **Custom session + cookie cache** — Custom session fields don't survive cookie caching. The callback runs fresh each time.
4. **Stateless sessions can't be revoked** — Without a database, there's no central session store to invalidate. Use versioning as a workaround.
