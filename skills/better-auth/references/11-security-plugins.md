# Better Auth — Security Plugins

> Source: [better-auth.com/docs/plugins](https://www.better-auth.com/docs/plugins) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Two-Factor Authentication (2FA)](#two-factor-authentication-2fa)
- [Passkeys (WebAuthn)](#passkeys-webauthn)
- [Magic Link](#magic-link)
- [Email OTP](#email-otp)
- [Rate Limiting](#rate-limiting)
- [Common Pitfalls](#common-pitfalls)

## Overview

Better Auth provides several security plugins to strengthen authentication: two-factor authentication (TOTP), passkeys (WebAuthn/FIDO2), magic link, email OTP, and built-in rate limiting.

## Two-Factor Authentication (2FA)

### Setup

```typescript
// Server
import { twoFactor } from "better-auth/plugins";

export const auth = betterAuth({
  plugins: [
    twoFactor({
      issuer: "My App", // TOTP issuer name
    }),
  ],
});

// Client
import { twoFactorClient } from "better-auth/client/plugins";

const authClient = createAuthClient({
  plugins: [twoFactorClient()],
});
```

Run migrations: `npx auth migrate`

### Enable 2FA for a User

```typescript
// Generate TOTP secret and QR code URI
const { data } = await authClient.twoFactor.enable({
  password: "current-password", // Verify identity first
});
// data = { totpURI, backupCodes }
// Display QR code from totpURI for authenticator app scanning
```

### Verify TOTP Code

After sign-in, if 2FA is enabled, the user must provide a TOTP code:

```typescript
const { data, error } = await authClient.twoFactor.verifyTotp({
  code: "123456", // 6-digit code from authenticator app
});
```

### Backup Codes

Generated when 2FA is enabled. Users can sign in with a backup code if they lose their authenticator:

```typescript
const { data } = await authClient.twoFactor.verifyBackupCode({
  code: "backup-code-here",
});
```

### Trusted Devices

Skip 2FA on trusted devices:

```typescript
// During TOTP verification
await authClient.twoFactor.verifyTotp({
  code: "123456",
  trustDevice: true, // Remember this device
});
```

### Disable 2FA

```typescript
await authClient.twoFactor.disable({
  password: "current-password",
});
```

## Passkeys (WebAuthn)

### Setup

```bash
npm install @better-auth/passkey
```

```typescript
// Server
import { passkey } from "@better-auth/passkey";

export const auth = betterAuth({
  plugins: [
    passkey({
      rpID: "example.com",     // Relying Party ID (your domain)
      rpName: "My App",        // Display name
      origin: "https://example.com",
    }),
  ],
});

// Client
import { passkeyClient } from "@better-auth/passkey/client";

const authClient = createAuthClient({
  plugins: [passkeyClient()],
});
```

Run migrations: `npx auth migrate`

### Register a Passkey

```typescript
const { data, error } = await authClient.passkey.addPasskey({
  name: "My MacBook",
  authenticatorAttachment: "platform", // or "cross-platform"
});
```

### Sign In with Passkey

```typescript
const { data, error } = await authClient.signIn.passkey({
  autoFill: true, // Enable browser autofill UI
});
```

For conditional UI, add `autocomplete="username webauthn"` to your login input field.

### Manage Passkeys

```typescript
// List all passkeys
const { data: passkeys } = await authClient.passkey.listUserPasskeys();

// Update passkey name
await authClient.passkey.updatePasskey({
  passkeyId: "pk-id",
  name: "Work Laptop",
});

// Delete passkey
await authClient.passkey.deletePasskey({
  passkeyId: "pk-id",
});
```

## Magic Link

### Setup

```typescript
// Server
import { magicLink } from "better-auth/plugins";

export const auth = betterAuth({
  plugins: [
    magicLink({
      sendMagicLink: async ({ email, url, token, metadata }, ctx) => {
        await sendEmail({
          to: email,
          subject: "Sign in to My App",
          body: `Click to sign in: ${url}`,
        });
      },
      expiresIn: 300,      // 5 minutes (default)
      allowedAttempts: 1,  // Verification attempts
    }),
  ],
});

// Client
import { magicLinkClient } from "better-auth/client/plugins";

const authClient = createAuthClient({
  plugins: [magicLinkClient()],
});
```

### Send Magic Link

```typescript
const { data, error } = await authClient.signIn.magicLink({
  email: "user@example.com",
  callbackURL: "/dashboard",
  newUserCallbackURL: "/welcome",      // Redirect for new users
  errorCallbackURL: "/login?error=true",
  metadata: { referralCode: "ABC" },   // Pass-through data
});
```

### Verify Magic Link

Typically handled automatically when the user clicks the link. Manual verification:

```typescript
const { data } = await authClient.magicLink.verify({
  query: { token: "token-from-url", callbackURL: "/dashboard" },
});
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `expiresIn` | 300 | Token expiration (seconds) |
| `allowedAttempts` | 1 | Max verification attempts |
| `disableSignUp` | false | Block new user registration |
| `storeToken` | "plain" | "plain", "hashed", or custom function |
| `generateToken` | random | Custom token generator |

## Email OTP

One-time password sent via email:

```typescript
// Server
import { emailOTP } from "better-auth/plugins";

export const auth = betterAuth({
  plugins: [
    emailOTP({
      sendVerificationOTP: async ({ email, otp, type }) => {
        await sendEmail({
          to: email,
          subject: "Your verification code",
          body: `Your code is: ${otp}`,
        });
      },
      otpLength: 6,            // Code length
      expiresIn: 300,          // 5 minutes
      sendEmailVerificationOnSignUp: true,
    }),
  ],
});

// Client
import { emailOTPClient } from "better-auth/client/plugins";

const authClient = createAuthClient({
  plugins: [emailOTPClient()],
});
```

### Sign In with OTP

```typescript
// 1. Request OTP
await authClient.signIn.emailOtp({
  email: "user@example.com",
});

// 2. Verify OTP
const { data } = await authClient.emailOtp.verifyEmail({
  email: "user@example.com",
  otp: "123456",
});
```

## Rate Limiting

Built-in rate limiting (no plugin needed):

```typescript
export const auth = betterAuth({
  rateLimit: {
    window: 60,  // seconds
    max: 100,    // requests per window
    enabled: true, // Disabled in dev by default
    storage: "memory", // or "database", "secondary-storage"
  },
});
```

### Custom Per-Endpoint Rules

```typescript
rateLimit: {
  window: 60,
  max: 100,
  customRules: {
    "/sign-in/email": { window: 10, max: 3 },
    "/sign-up/email": { window: 60, max: 5 },
    "/two-factor/*": { window: 10, max: 3 },
    "/forget-password": { window: 60, max: 3 },
  },
}
```

### Storage Options

```typescript
// Database storage
rateLimit: { storage: "database" }
// Then run: npx auth migrate

// Redis (secondary storage)
rateLimit: { storage: "secondary-storage" }

// Custom storage
rateLimit: {
  customStorage: {
    get: async (key) => { /* retrieve */ },
    set: async (key, value) => { /* store */ },
  },
}
```

### IPv6 Handling

```typescript
advanced: {
  ipAddress: {
    ipAddressHeaders: ["cf-connecting-ip"], // Cloudflare
    ipv6Subnet: 64, // Subnet-based limiting
  },
}
```

### Client Error Handling

```typescript
const authClient = createAuthClient({
  fetchOptions: {
    onError: async (ctx) => {
      if (ctx.response.status === 429) {
        const retryAfter = ctx.response.headers.get("X-Retry-After");
        toast.error(`Too many requests. Try again in ${retryAfter}s`);
      }
    },
  },
});
```

## Common Pitfalls

1. **2FA without backup codes** — Always display backup codes to users when enabling 2FA. They can't recover without them.
2. **Passkey rpID mismatch** — The `rpID` must match your domain. Localhost works for development.
3. **Magic link without email handler** — The `sendMagicLink` callback is required. Without it, no emails are sent.
4. **Rate limiting in dev** — Rate limiting is disabled by default in development. Set `enabled: true` to test.
5. **IPv6 bypass** — Without `ipv6Subnet` configuration, users can bypass rate limits by using different IPv6 addresses from the same network.
6. **Passkey origin without protocol** — The `origin` must include the protocol (e.g., `https://example.com`, not just `example.com`).
