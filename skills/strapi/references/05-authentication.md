# Strapi — Authentication & Permissions

> Source: https://docs.strapi.io/cms/features/users-permissions

## Table of Contents

- [Overview](#overview)
- [JWT Authentication](#jwt-authentication)
- [Registration](#registration)
- [Login](#login)
- [Password Reset](#password-reset)
- [API Tokens](#api-tokens)
- [Roles & Permissions](#roles--permissions)
- [OAuth Providers](#oauth-providers)
- [Rate Limiting](#rate-limiting)
- [Common Pitfalls](#common-pitfalls)

## Overview

Strapi has two distinct user systems:

| System | Purpose | Auth Method |
|--------|---------|-------------|
| **Admin Users** | Manage content via admin panel | Session-based |
| **End Users** | Consume content via APIs | JWT-based |

The Users & Permissions plugin manages end users — those consuming content through frontend applications. It provides JWT authentication, role-based access control, and OAuth provider support.

## JWT Authentication

### Configuration

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  'users-permissions': {
    config: {
      jwt: {
        expiresIn: '7d',
      },
      jwtManagement: 'legacy-support', // or 'refresh'
    },
  },
});
```

### JWT Modes

| Mode | Description |
|------|-------------|
| `legacy-support` | Long-lived JWTs (default). Simple but less secure for sensitive apps. |
| `refresh` | Short-lived access tokens with refresh tokens. Better security. |

### Using JWT in Requests

Include the JWT in the `Authorization` header:

```javascript
const response = await fetch('http://localhost:1337/api/articles', {
  headers: {
    Authorization: `Bearer ${jwt}`,
  },
});
```

The JWT secret is configured via the `JWT_SECRET` environment variable.

## Registration

### Endpoint

```bash
POST /api/auth/local/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

### Response

```json
{
  "jwt": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "documentId": "abc123...",
    "username": "johndoe",
    "email": "john@example.com",
    "confirmed": true,
    "blocked": false
  }
}
```

### Allowing Additional Fields

By default, only `username`, `email`, and `password` are accepted. To allow custom fields:

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  'users-permissions': {
    config: {
      register: {
        allowedFields: ['firstName', 'lastName', 'company'],
      },
    },
  },
});
```

### Email Confirmation

Enable in Settings → Users & Permissions → Advanced Settings:
- Toggle "Enable email confirmation"
- Set the redirect URL for after confirmation

## Login

### Endpoint

```bash
POST /api/auth/local
Content-Type: application/json

{
  "identifier": "john@example.com",
  "password": "SecurePass123!"
}
```

The `identifier` field accepts either username or email.

### Response

```json
{
  "jwt": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "documentId": "abc123...",
    "username": "johndoe",
    "email": "john@example.com",
    "confirmed": true,
    "blocked": false
  }
}
```

### Get Current User

```bash
GET /api/users/me
Authorization: Bearer <jwt>
```

## Password Reset

### Step 1: Request Reset Email

```bash
POST /api/auth/forgot-password
Content-Type: application/json

{
  "email": "john@example.com"
}
```

Sends an email with a reset code/token.

### Step 2: Reset Password

```bash
POST /api/auth/reset-password
Content-Type: application/json

{
  "code": "reset-code-from-email",
  "password": "NewSecurePass456!",
  "passwordConfirmation": "NewSecurePass456!"
}
```

### Email Templates

Templates use Lodash syntax and support these variables:
- `USER` — user object
- `TOKEN` or `CODE` — reset token/code
- `URL` — configured redirect URL
- `SERVER_URL` — Strapi server URL

Configure templates in Settings → Users & Permissions → Email templates.

## API Tokens

API tokens provide stateless authentication without user accounts. Manage in Settings → API Tokens.

### Token Types

| Type | Description |
|------|-------------|
| **Read-only** | Only `find` and `findOne` access |
| **Full access** | All CRUD operations |
| **Custom** | Granular per-content-type permissions |

### Usage

```bash
GET /api/articles
Authorization: Bearer <api-token>
```

### Configuration

```javascript
// config/admin.js
module.exports = ({ env }) => ({
  apiToken: {
    salt: env('API_TOKEN_SALT', 'a-random-salt-string'),
  },
});
```

## Roles & Permissions

### Default Roles

| Role | Description |
|------|-------------|
| **Public** | Unauthenticated users. No permissions by default. |
| **Authenticated** | Logged-in users. No permissions by default. |

Both roles start with zero permissions — you must explicitly enable access.

### Configuring Permissions (Admin Panel)

1. Navigate to Settings → Users & Permissions → Roles
2. Select a role (Public, Authenticated, or custom)
3. Expand a content type
4. Check the actions to allow: `find`, `findOne`, `create`, `update`, `delete`
5. Save

### Making Content Publicly Accessible

To allow unauthenticated API access:
1. Go to Settings → Users & Permissions → Roles → Public
2. Enable `find` and `findOne` for the desired content types
3. Save

## OAuth Providers

Strapi supports OAuth authentication with external providers. Enable in Settings → Users & Permissions → Providers.

Supported providers include: Google, GitHub, Facebook, Twitter, Discord, Microsoft, and many others.

### Provider Flow

1. Frontend redirects user to: `GET /api/connect/<provider>`
2. User authenticates with the provider
3. Provider redirects back with code
4. Strapi exchanges code for tokens
5. Strapi creates/finds user and returns JWT

### Callback URL

```
http://localhost:1337/api/connect/<provider>/callback
```

### Custom Callback Validation

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  'users-permissions': {
    config: {
      callback: {
        validate: (cbUrl) => {
          if (new URL(cbUrl).hostname !== 'myapp.com') {
            throw new Error('Invalid callback URL');
          }
        },
      },
    },
  },
});
```

## Rate Limiting

Protect authentication endpoints from abuse:

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  'users-permissions': {
    config: {
      ratelimit: {
        enabled: true,
        interval: 60000,  // 1 minute window
        max: 10,           // max requests per window
      },
    },
  },
});
```

## Common Pitfalls

- **Admin users and end users are separate** — admin credentials don't work with the API auth endpoints
- **Roles have zero permissions by default** — even the Authenticated role can't access anything until configured
- **JWT expiry > 30 days is not recommended** — use refresh tokens for long-lived sessions
- **`identifier` in login accepts both username and email** — don't create separate endpoints
- **API tokens and JWTs are different** — API tokens are for machine-to-machine access, JWTs for user sessions
- **Password field type** is never returned in API responses regardless of permissions
- **OAuth providers** must be individually enabled and configured with client ID/secret from each provider
- **Email confirmation** requires a working email provider (default uses Sendmail, configure SMTP for production)
