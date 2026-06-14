# Clerk — Middleware & Route Protection

> Source: [clerk.com/docs/references/nextjs/clerk-middleware](https://clerk.com/docs/references/nextjs/clerk-middleware)

## Table of Contents

- [Overview](#overview)
- [Basic Setup](#basic-setup)
- [createRouteMatcher](#createroutematcher)
- [Protecting Routes](#protecting-routes)
- [Public Routes Pattern](#public-routes-pattern)
- [Role-Based Protection](#role-based-protection)
- [Permission-Based Protection](#permission-based-protection)
- [Multiple Route Groups](#multiple-route-groups)
- [Token Type Protection](#token-type-protection)
- [Middleware Chaining](#middleware-chaining)
- [Frontend API Proxy](#frontend-api-proxy)
- [Configuration Options](#configuration-options)
- [Debugging](#debugging)
- [Common Patterns](#common-patterns)

## Overview

`clerkMiddleware()` integrates Clerk authentication into Next.js at the middleware layer. It runs on every matched request, attaching auth state that downstream code can read via `auth()`.

By default, **no routes are protected** — all routes are public. You must explicitly define which routes require authentication.

## Basic Setup

```tsx
// middleware.ts (Next.js ≤15) or proxy.ts (Next.js 16+)
import { clerkMiddleware } from '@clerk/nextjs/server'

export default clerkMiddleware()

export const config = {
  matcher: [
    // Skip static files and Next.js internals
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API and tRPC routes
    '/(api|trpc)(.*)',
    // Clerk internal routes
    '/__clerk/(.*)',
  ],
}
```

The middleware file name depends on your Next.js version:
- **Next.js 15 and below:** `middleware.ts`
- **Next.js 16+:** `proxy.ts`

## createRouteMatcher

`createRouteMatcher()` creates a function that tests if a request URL matches a set of patterns:

```tsx
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/forum(.*)',
  '/api/private(.*)',
])
```

Patterns use path-to-regexp syntax:
- `/dashboard(.*)` — matches `/dashboard` and all sub-paths
- `/api/users/:id` — matches with named parameter
- `/admin` — exact match only

## Protecting Routes

### Using auth.protect()

Automatically redirects unauthenticated users to sign-in:

```tsx
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/account(.*)',
])

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect()
  }
})
```

### Using auth() with Custom Logic

For more control over the redirect behavior:

```tsx
export default clerkMiddleware(async (auth, req) => {
  const { isAuthenticated, redirectToSignIn } = await auth()

  if (!isAuthenticated && isProtectedRoute(req)) {
    return redirectToSignIn()
  }
})
```

### Protect ALL Routes

```tsx
export default clerkMiddleware(async (auth) => {
  await auth.protect()
})
```

## Public Routes Pattern

Define which routes are public and protect everything else:

```tsx
const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks(.*)',
  '/pricing',
  '/about',
])

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect()
  }
})
```

## Role-Based Protection

Restrict routes to users with specific organization roles:

```tsx
const isAdminRoute = createRouteMatcher(['/admin(.*)'])

export default clerkMiddleware(async (auth, req) => {
  if (isAdminRoute(req)) {
    await auth.protect({ role: 'org:admin' })
  }
})
```

Unauthenticated users → redirected to sign-in.
Authenticated but wrong role → 404 response.

## Permission-Based Protection

Check granular permissions instead of roles:

```tsx
const isAdminRoute = createRouteMatcher(['/admin(.*)'])

export default clerkMiddleware(async (auth, req) => {
  if (isAdminRoute(req)) {
    await auth.protect((has) => {
      return (
        has({ permission: 'org:admin:example1' }) ||
        has({ permission: 'org:admin:example2' })
      )
    })
  }
})
```

## Multiple Route Groups

Apply different protection levels to different route groups:

```tsx
const isTenantRoute = createRouteMatcher([
  '/organization-selector(.*)',
  '/orgid/(.*)',
])
const isTenantAdminRoute = createRouteMatcher([
  '/orgId/(.*)/memberships',
  '/orgId/(.*)/settings',
])

export default clerkMiddleware(async (auth, req) => {
  // Most restrictive first
  if (isTenantAdminRoute(req)) {
    await auth.protect((has) => {
      return has({ permission: 'org:admin:example1' })
    })
  }

  if (isTenantRoute(req)) {
    await auth.protect()
  }
})
```

## Token Type Protection

Enforce specific authentication mechanisms for API routes:

```tsx
const isApiKeyRoute = createRouteMatcher(['/api/v1(.*)'])
const isMachineRoute = createRouteMatcher(['/api/m2m(.*)'])

export default clerkMiddleware(async (auth, req) => {
  if (isApiKeyRoute(req)) {
    await auth.protect({ token: 'api_key' })
  }
  if (isMachineRoute(req)) {
    await auth.protect({ token: 'm2m_token' })
  }
})
```

## Middleware Chaining

Combine Clerk with other middleware (e.g., next-intl):

```tsx
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import createMiddleware from 'next-intl/middleware'

const intlMiddleware = createMiddleware({
  locales: ['en', 'de', 'fr'],
  defaultLocale: 'en',
})

const isProtectedRoute = createRouteMatcher(['/dashboard(.*)'])

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect()
  }
  return intlMiddleware(req)
})
```

## Frontend API Proxy

Route Clerk API requests through your domain instead of Clerk's:

```tsx
// Basic proxy
export default clerkMiddleware({
  frontendApiProxy: {
    enabled: true,
  },
})

// Conditional proxy (multi-domain)
export default clerkMiddleware({
  frontendApiProxy: {
    enabled: (url) => url.hostname !== 'myapp.com',
  },
})
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `audience` | `string \| string[]` | — | Validates `aud` claim in session tokens |
| `authorizedParties` | `string[]` | — | Whitelist of approved request origins |
| `clockSkewInMs` | `number` | `5000` | Tolerance for clock differences |
| `domain` | `string` | — | Domain for satellite deployments |
| `isSatellite` | `boolean` | `false` | Enable satellite mode |
| `signInUrl` | `string` | — | Custom sign-in page path |
| `signUpUrl` | `string` | — | Custom sign-up page path |
| `publishableKey` | `string` | env var | Clerk publishable key |
| `secretKey` | `string` | env var | Clerk secret key |
| `frontendApiProxy` | `object` | — | Proxy configuration |
| `debug` | `boolean` | `false` | Enable debug logging |

## Debugging

Enable debug mode for detailed middleware logs:

```tsx
export default clerkMiddleware(
  async (auth, req) => {
    // your logic
  },
  { debug: true }
)
```

Debug output goes to the terminal and includes:
- Matched routes
- Auth state resolution
- Token validation results
- Redirect decisions

## Common Patterns

**SaaS app with public marketing pages:**
```tsx
const isPublicRoute = createRouteMatcher([
  '/',
  '/pricing',
  '/blog(.*)',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks(.*)',
])

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) await auth.protect()
})
```

**API with mixed auth (session + API keys):**
```tsx
const isApiRoute = createRouteMatcher(['/api/v1(.*)'])

export default clerkMiddleware(async (auth, req) => {
  if (isApiRoute(req)) {
    await auth.protect({
      token: ['session_token', 'api_key'],
    })
  }
})
```
