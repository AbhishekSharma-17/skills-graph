# Hono — Authentication

> Source: [hono.dev/docs/middleware/builtin](https://hono.dev/docs/middleware/builtin)

## Overview

Hono provides built-in authentication middleware for common patterns: JWT, Bearer token, and Basic auth. Each middleware validates credentials and either allows the request to proceed or returns an appropriate HTTP error.

## JWT Authentication

The JWT middleware verifies JSON Web Tokens from the `Authorization` header or cookies.

### Setup

```typescript
import { Hono } from 'hono'
import { jwt } from 'hono/jwt'
import type { JwtVariables } from 'hono/jwt'

type Variables = JwtVariables

const app = new Hono<{ Variables: Variables }>()

app.use('/auth/*', jwt({
  secret: 'your-secret-key',
  alg: 'HS256',
}))

app.get('/auth/profile', (c) => {
  const payload = c.get('jwtPayload')
  return c.json(payload)
})
```

### JWT Options

| Option | Type | Description |
|--------|------|-------------|
| `secret` | `string` | Required. Secret key for verification |
| `alg` | `string` | Required. Algorithm: HS256, HS384, HS512, RS256, RS384, RS512, ES256, etc. |
| `cookie` | `string` | Cookie name to read JWT from (instead of Authorization header) |
| `headerName` | `string` | Custom header name (default: `Authorization`) |

### Using Environment Variables for Secret

```typescript
app.use('/auth/*', (c, next) => {
  const jwtMiddleware = jwt({
    secret: c.env.JWT_SECRET,
    alg: 'HS256',
  })
  return jwtMiddleware(c, next)
})
```

### JWT from Cookies

```typescript
app.use('/auth/*', jwt({
  secret: 'your-secret',
  alg: 'HS256',
  cookie: 'auth_token', // Read JWT from this cookie
}))
```

### Creating JWTs

Hono includes JWT helper functions:

```typescript
import { sign, verify, decode } from 'hono/jwt'

// Create a token
app.post('/login', async (c) => {
  const { email, password } = await c.req.json()
  const user = await authenticateUser(email, password)

  const token = await sign(
    {
      sub: user.id,
      exp: Math.floor(Date.now() / 1000) + 60 * 60, // 1 hour
    },
    c.env.JWT_SECRET,
    'HS256'
  )

  return c.json({ token })
})
```

### Issuer Validation

```typescript
app.use('/auth/*', jwt({
  secret: 'your-secret',
  alg: 'HS256',
  verifyOptions: {
    iss: 'my-trusted-issuer', // Validate issuer claim
  },
}))
```

## Bearer Token Authentication

For API key or opaque token validation:

```typescript
import { bearerAuth } from 'hono/bearer-auth'

// Single token
app.use('/api/*', bearerAuth({
  token: 'my-api-token',
}))

// Multiple tokens
app.use('/api/*', bearerAuth({
  token: ['token1', 'token2', 'token3'],
}))
```

### Custom Token Verification

```typescript
app.use('/api/*', bearerAuth({
  verifyToken: async (token, c) => {
    const isValid = await validateTokenInDB(token)
    return isValid
  },
}))
```

### Bearer Auth Options

| Option | Type | Description |
|--------|------|-------------|
| `token` | `string \| string[]` | Valid token(s) for comparison |
| `verifyToken` | `(token, c) => boolean \| Promise<boolean>` | Custom verification function |
| `realm` | `string` | WWW-Authenticate realm (default: `''`) |
| `prefix` | `string` | Header prefix (default: `'Bearer'`) |
| `headerName` | `string` | Custom header (default: `'Authorization'`) |
| `hashFunction` | `Function` | Custom hash function for token comparison |

## Basic Authentication

For HTTP Basic authentication:

```typescript
import { basicAuth } from 'hono/basic-auth'

app.use('/admin/*', basicAuth({
  username: 'admin',
  password: 'secret',
}))

// Multiple users
app.use('/admin/*', basicAuth({
  username: 'admin',
  password: 'secret',
}, {
  username: 'editor',
  password: 'editor-pass',
}))
```

### Custom Basic Auth Verification

```typescript
app.use('/admin/*', basicAuth({
  verifyUser: async (username, password, c) => {
    const user = await db.findUser(username)
    if (!user) return false
    return await bcrypt.compare(password, user.passwordHash)
  },
}))
```

## API Key Middleware Pattern

For custom API key validation (not built-in, but a common pattern):

```typescript
import { createMiddleware } from 'hono/factory'
import { HTTPException } from 'hono/http-exception'

type Env = {
  Bindings: { API_KEYS: KVNamespace }
  Variables: { apiKeyOwner: string }
}

const apiKeyAuth = createMiddleware<Env>(async (c, next) => {
  const key = c.req.header('X-API-Key')
  if (!key) {
    throw new HTTPException(401, { message: 'Missing API key' })
  }

  const owner = await c.env.API_KEYS.get(key)
  if (!owner) {
    throw new HTTPException(403, { message: 'Invalid API key' })
  }

  c.set('apiKeyOwner', owner)
  await next()
})

app.use('/api/*', apiKeyAuth)
```

## Combining Auth Methods

```typescript
import { jwt } from 'hono/jwt'
import { bearerAuth } from 'hono/bearer-auth'

// JWT for user-facing routes
app.use('/api/user/*', jwt({
  secret: 'jwt-secret',
  alg: 'HS256',
}))

// Bearer token for service-to-service
app.use('/api/internal/*', bearerAuth({
  verifyToken: async (token) => {
    return await verifyServiceToken(token)
  },
}))

// Basic auth for admin panel
app.use('/admin/*', basicAuth({
  username: 'admin',
  password: 'secure-password',
}))
```

## Common Pitfalls

1. **Hardcoding secrets** — Use `c.env` for environment-based secrets, not string literals
2. **Not typing JwtVariables** — Pass `JwtVariables` to `Hono<{ Variables }>` for typed `c.get('jwtPayload')`
3. **Missing alg parameter** — JWT middleware requires both `secret` and `alg`
4. **Bearer vs JWT** — Use `bearerAuth` for opaque tokens, `jwt` for tokens that need payload extraction
5. **Auth middleware order** — Register auth middleware before route handlers, not after
