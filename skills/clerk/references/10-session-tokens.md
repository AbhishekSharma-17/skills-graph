# Clerk — Session & Token Management

> Source: [clerk.com/docs/backend-requests/overview](https://clerk.com/docs/backend-requests/overview)

## Table of Contents

- [Overview](#overview)
- [Session Tokens](#session-tokens)
- [Token Delivery Methods](#token-delivery-methods)
- [getToken on the Client](#gettoken-on-the-client)
- [getToken on the Server](#gettoken-on-the-server)
- [Custom JWT Templates](#custom-jwt-templates)
- [Session Lifetime](#session-lifetime)
- [Multi-Session Applications](#multi-session-applications)
- [Machine Tokens](#machine-tokens)
- [API Keys](#api-keys)
- [Cross-Origin Requests](#cross-origin-requests)
- [Common Patterns](#common-patterns)

## Overview

Clerk uses short-lived JWTs (session tokens) for authentication. These tokens:
- Are valid for ~60 seconds
- Contain user identity claims (userId, orgId, etc.)
- Are automatically refreshed by the Clerk frontend SDK
- Are cryptographically signed and verifiable without calling Clerk's API

## Session Tokens

A session token is a JWT with these default claims:

```json
{
  "azp": "https://myapp.com",
  "exp": 1234567890,
  "iat": 1234567830,
  "iss": "https://clerk.myapp.com",
  "nbf": 1234567825,
  "sid": "sess_abc123",
  "sub": "user_abc123"
}
```

| Claim | Description |
|-------|-------------|
| `sub` | User ID (`user_...`) |
| `sid` | Session ID (`sess_...`) |
| `org_id` | Active organization ID (if set) |
| `org_role` | Role in active org |
| `org_permissions` | Permissions in active org |
| `azp` | Authorized party (your app URL) |
| `exp` | Expiration timestamp |
| `iat` | Issued at timestamp |
| `iss` | Issuer (Clerk instance URL) |

## Token Delivery Methods

### Same-Origin (Automatic)

For requests between your frontend and backend on the same domain, session tokens are delivered automatically via cookies. No manual setup needed:

```tsx
// Frontend — same domain as API
const res = await fetch('/api/data')
// Cookie is sent automatically
```

### Cross-Origin (Manual)

For requests to a different domain, you must manually attach the token as a Bearer token:

```tsx
const { getToken } = useAuth()

const token = await getToken()
const res = await fetch('https://api.example.com/data', {
  headers: {
    Authorization: `Bearer ${token}`,
  },
})
```

## getToken on the Client

Access session tokens using the `useAuth()` hook:

```tsx
import { useAuth } from '@clerk/nextjs'

function ApiClient() {
  const { getToken } = useAuth()

  const fetchData = async () => {
    // Default session token
    const token = await getToken()

    // Custom JWT template
    const supabaseToken = await getToken({ template: 'supabase' })

    // Token with specific options
    const token = await getToken({
      template: 'my-template',
      skipCache: false,  // Use cached token if valid
    })

    return fetch('https://api.example.com/data', {
      headers: { Authorization: `Bearer ${token}` },
    })
  }
}
```

**Using with Vanilla JS:**

```tsx
const token = await window.Clerk.session.getToken()
```

## getToken on the Server

Access tokens in Server Components, Route Handlers, and Server Actions:

```tsx
import { auth } from '@clerk/nextjs/server'

export async function GET() {
  const { getToken } = await auth()

  // Default session token
  const token = await getToken()

  // Custom JWT template for external service
  const supabaseToken = await getToken({ template: 'supabase' })

  // Call external API with the token
  const res = await fetch('https://api.example.com/data', {
    headers: { Authorization: `Bearer ${supabaseToken}` },
  })

  return NextResponse.json(await res.json())
}
```

## Custom JWT Templates

Create custom JWT templates in the Clerk Dashboard (**Sessions > JWT Templates**) to include additional claims for external services:

**Supabase template example:**
```json
{
  "iss": "https://clerk.myapp.com",
  "sub": "{{user.id}}",
  "aud": "authenticated",
  "role": "authenticated",
  "email": "{{user.primary_email_address}}",
  "user_metadata": {
    "full_name": "{{user.full_name}}"
  }
}
```

**Hasura template example:**
```json
{
  "https://hasura.io/jwt/claims": {
    "x-hasura-default-role": "user",
    "x-hasura-allowed-roles": ["user"],
    "x-hasura-user-id": "{{user.id}}"
  }
}
```

**Convex template example:**
```json
{
  "sub": "{{user.id}}",
  "name": "{{user.full_name}}",
  "email": "{{user.primary_email_address}}"
}
```

Usage:
```tsx
const { getToken } = useAuth()
const token = await getToken({ template: 'supabase' })
```

## Session Lifetime

Configure session duration in the Clerk Dashboard (**Sessions**):

### Inactivity Timeout
- Session expires after a period of user inactivity
- User is inactive when the app closes or token refreshing stops
- Requires paid plan in production (free in development)

### Maximum Lifetime
- Session expires after a fixed duration regardless of activity
- Default: 7 days
- Requires paid plan to customize in production

**Both settings cannot be disabled simultaneously** — at least one expiration mechanism must be active.

### Browser Limitations
Sessions may end earlier than configured due to:
- User clears cookies manually
- Incognito window closes
- Chrome's 400-day cookie maximum (per HTTP spec)

## Multi-Session Applications

Enable users to maintain multiple authenticated accounts simultaneously:

### Setup
1. Enable **Multi-session handling** in Clerk Dashboard (**Sessions**)
2. Wrap your app with `<MultisessionAppSupport />`

```tsx
import { ClerkProvider, MultisessionAppSupport } from '@clerk/nextjs'

<ClerkProvider>
  <MultisessionAppSupport>
    {children}
  </MultisessionAppSupport>
</ClerkProvider>
```

### Switching Sessions

```tsx
import { useSessionList } from '@clerk/nextjs'

function AccountSwitcher() {
  const { sessions, setActive } = useSessionList()

  return (
    <ul>
      {sessions.map((session) => (
        <li key={session.id}>
          {session.user?.primaryEmailAddress?.emailAddress}
          <button onClick={() => setActive({ session: session.id })}>
            Switch
          </button>
        </li>
      ))}
    </ul>
  )
}
```

The `<UserButton />` component includes built-in multi-session UI when enabled.

## Machine Tokens

For server-to-server (M2M) authentication without user sessions:

```tsx
// Protect M2M routes in middleware
export default clerkMiddleware(async (auth, req) => {
  if (isMachineRoute(req)) {
    await auth.protect({ token: 'm2m_token' })
  }
})
```

Machine tokens are validated differently from session tokens — unauthenticated machine requests return 401 (not redirect).

## API Keys

For external API access with long-lived keys:

```tsx
// Protect API key routes
const isApiRoute = createRouteMatcher(['/api/v1(.*)'])

export default clerkMiddleware(async (auth, req) => {
  if (isApiRoute(req)) {
    await auth.protect({ token: 'api_key' })
  }
})
```

Manage API keys via the `useAPIKeys()` hook or Backend API.

## Cross-Origin Requests

### Using fetch

```tsx
const { getToken } = useAuth()

async function callExternalApi(endpoint: string) {
  const token = await getToken()

  const res = await fetch(endpoint, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
```

### Using SWR

```tsx
import useSWR from 'swr'
import { useAuth } from '@clerk/nextjs'

function useExternalData(url: string) {
  const { getToken } = useAuth()

  return useSWR(url, async (url) => {
    const token = await getToken()
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
    return res.json()
  })
}
```

### Using TanStack Query

```tsx
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@clerk/nextjs'

function useExternalData(key: string, url: string) {
  const { getToken } = useAuth()

  return useQuery({
    queryKey: [key],
    queryFn: async () => {
      const token = await getToken()
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      })
      return res.json()
    },
  })
}
```

## Common Patterns

**Token refresh wrapper:**
```tsx
function useAuthFetch() {
  const { getToken } = useAuth()

  return async (url: string, init?: RequestInit) => {
    const token = await getToken()
    return fetch(url, {
      ...init,
      headers: {
        ...init?.headers,
        Authorization: `Bearer ${token}`,
      },
    })
  }
}
```

**Verify tokens in external backend (Node.js):**
```tsx
import { createClerkClient } from '@clerk/backend'

const clerk = createClerkClient({
  secretKey: process.env.CLERK_SECRET_KEY,
})

async function verifyToken(token: string) {
  const payload = await clerk.verifyToken(token)
  return payload.sub // userId
}
```
