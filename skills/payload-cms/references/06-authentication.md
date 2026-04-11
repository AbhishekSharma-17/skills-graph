# Authentication

> Source: https://payloadcms.com/docs/authentication/overview

## Overview

Payload provides built-in authentication on any collection by setting `auth: true`. This adds email/password login, JWT tokens, HTTP-only cookies, password hashing, account locking, and password reset — all automatically.

Authentication strategies:
1. **Email/Password** — default strategy with bcrypt hashing
2. **HTTP-only Cookies** — automatic, secure, XSS-resistant
3. **JWT Tokens** — Bearer token authentication for APIs
4. **API Keys** — static keys for third-party integrations
5. **Custom Strategies** — implement your own (OAuth, SAML, etc.)

## Enabling Authentication

```typescript
import type { CollectionConfig } from 'payload'

export const Users: CollectionConfig = {
  slug: 'users',
  auth: true,  // Simple — uses all defaults
  fields: [
    { name: 'name', type: 'text', required: true },
    {
      name: 'role',
      type: 'select',
      options: ['admin', 'editor', 'viewer'],
      defaultValue: 'viewer',
    },
  ],
}
```

## Auth Configuration Options

```typescript
auth: {
  // Token settings
  tokenExpiration: 7200,          // Token lifetime in seconds (default: 2 hours)
  maxLoginAttempts: 5,            // Max failed attempts before lock
  lockTime: 600000,               // Lock duration in ms (default: 10 min)

  // Cookie settings
  cookies: {
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',              // 'strict' | 'lax' | 'none'
    domain: '.mysite.com',        // For cross-subdomain auth
  },

  // API Keys
  useAPIKey: true,                // Enable API key strategy

  // Verification
  verify: {                       // Email verification
    generateEmailHTML: ({ req, token, user }) => {
      return `<a href="${process.env.FRONTEND_URL}/verify?token=${token}">Verify</a>`
    },
    generateEmailSubject: () => 'Verify your email',
  },

  // Password reset
  forgotPassword: {
    generateEmailHTML: ({ req, token, user }) => {
      return `<a href="${process.env.FRONTEND_URL}/reset?token=${token}">Reset</a>`
    },
    generateEmailSubject: () => 'Reset your password',
  },

  // Depth for populated user on req.user
  depth: 0,

  // Disable email/password strategy (use API keys only)
  disableLocalStrategy: false,
}
```

## Authentication Operations

### Login

```typescript
// Local API
const { user, token } = await payload.login({
  collection: 'users',
  data: {
    email: 'user@example.com',
    password: 'securePassword123',
  },
})

// REST API
// POST /api/users/login
// Body: { "email": "...", "password": "..." }

// Response: { user: {...}, token: "jwt-token", exp: 1234567890 }
```

### Logout

```typescript
// Local API
await payload.logout({ collection: 'users' })

// REST API
// POST /api/users/logout
```

### Current User (Me)

```typescript
// Local API
const { user } = await payload.auth({ headers: req.headers })

// REST API
// GET /api/users/me
// Header: Authorization: Bearer <token>
```

### Refresh Token

```typescript
// REST API
// POST /api/users/refresh-token
// Uses HTTP-only cookie automatically
```

### Forgot / Reset Password

```typescript
// Request reset email
await payload.forgotPassword({
  collection: 'users',
  data: { email: 'user@example.com' },
})

// Reset with token
await payload.resetPassword({
  collection: 'users',
  data: {
    token: 'reset-token-from-email',
    password: 'newSecurePassword',
  },
})
```

## API Key Authentication

Enable API keys for machine-to-machine authentication:

```typescript
export const Users: CollectionConfig = {
  slug: 'users',
  auth: {
    useAPIKey: true,
  },
  fields: [/* ... */],
}
```

Usage:

```typescript
// REST API with API key
// GET /api/posts
// Header: Authorization: users API-Key <api-key-value>

// Local API
const posts = await payload.find({
  collection: 'posts',
  overrideAccess: false,
  user: apiKeyUser,  // Pass the user associated with the API key
})
```

API keys appear in the admin panel on each user's edit page. They can be generated and copied from there.

## JWT and Cookies

Payload uses both JWTs and HTTP-only cookies:

- **HTTP-only cookies** are set automatically on login/refresh. They cannot be read by JavaScript (XSS protection).
- **JWT tokens** are returned in login responses for use in API calls from external services.
- The same access control applies regardless of auth method.

### Adding Custom Data to JWT

```typescript
{
  name: 'role',
  type: 'select',
  options: ['admin', 'editor'],
  saveToJWT: true,  // Include in JWT payload
}

// Or a custom key
{
  name: 'organizationId',
  type: 'relationship',
  relationTo: 'organizations',
  saveToJWT: 'org',  // Custom key name in JWT
}
```

## Using Auth in Next.js

```typescript
// app/(frontend)/dashboard/page.tsx
import { getPayload } from 'payload'
import config from '@payload-config'
import { headers } from 'next/headers'
import { redirect } from 'next/navigation'

export default async function Dashboard() {
  const payload = await getPayload({ config })
  const headersList = await headers()

  const { user } = await payload.auth({ headers: headersList })

  if (!user) {
    redirect('/login')
  }

  return <div>Welcome, {user.name}</div>
}
```

## Multiple Auth Collections

You can have multiple auth-enabled collections (e.g., `users` for website users, `admins` for CMS editors):

```typescript
export const Admins: CollectionConfig = {
  slug: 'admins',
  auth: true,
  admin: {
    useAsTitle: 'email',
  },
  fields: [
    { name: 'name', type: 'text' },
  ],
}

// In payload.config.ts
admin: {
  user: 'admins',  // Which auth collection controls admin panel access
}
```

## Common Pitfalls

1. **No auth collection with admin access** — You need at least one auth-enabled collection to access the admin panel. Specified via `admin.user` in the Payload config.
2. **PAYLOAD_SECRET not set** — JWT signing requires this environment variable. Generate a secure random string.
3. **Cookie domain mismatch** — If your frontend and API are on different subdomains, set the `domain` option in cookie config.
4. **`overrideAccess` in Local API** — By default, the Local API bypasses access control. Set `overrideAccess: false` when acting on behalf of a user.
5. **Forgot to configure email transport** — Password reset and email verification require a configured email adapter in the Payload config.
