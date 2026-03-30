# Better Auth — OAuth & Social Providers

> Source: [better-auth.com/docs/concepts/oauth](https://www.better-auth.com/docs/concepts/oauth) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Provider Configuration](#provider-configuration)
- [Built-In Providers](#built-in-providers)
- [Sign-In Flow](#sign-in-flow)
- [Provider Options](#provider-options)
- [Account Linking](#account-linking)
- [Token Access & Refresh](#token-access--refresh)
- [Additional Data Through OAuth](#additional-data-through-oauth)
- [Advanced Features](#advanced-features)
- [Common Pitfalls](#common-pitfalls)

## Overview

Better Auth supports OAuth 2.0 and OpenID Connect with 40+ built-in social providers. Each provider requires a `clientId` and `clientSecret` from the provider's developer console.

The default callback URL is: `{BETTER_AUTH_URL}/api/auth/callback/{providerName}`

## Provider Configuration

```typescript
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
    discord: {
      clientId: process.env.DISCORD_CLIENT_ID!,
      clientSecret: process.env.DISCORD_CLIENT_SECRET!,
    },
  },
});
```

## Built-In Providers

| Provider | Key | Notes |
|----------|-----|-------|
| Apple | `apple` | Requires Sign in with Apple setup |
| Discord | `discord` | |
| Facebook | `facebook` | |
| GitHub | `github` | Most common for dev tools |
| Google | `google` | Supports `prompt: "select_account"` |
| LinkedIn | `linkedin` | |
| Microsoft | `microsoft` | Azure AD / Entra ID |
| Slack | `slack` | |
| Spotify | `spotify` | |
| Twitch | `twitch` | |
| X (Twitter) | `twitter` | OAuth 2.0 |

Plus 28+ additional providers. See full list in the docs.

## Sign-In Flow

### Client-Side

```typescript
// Basic social sign-in
await authClient.signIn.social({
  provider: "github",
  callbackURL: "/dashboard",
});

// With error handling
await authClient.signIn.social({
  provider: "google",
  callbackURL: "/dashboard",
  errorCallbackURL: "/login?error=true",
  newUserCallbackURL: "/onboarding",
});
```

### Server-Side

```typescript
const response = await auth.api.signInSocial({
  body: { provider: "github" },
  asResponse: true,
});
```

## Provider Options

| Option | Type | Description |
|--------|------|-------------|
| `clientId` | `string` | OAuth client ID (required) |
| `clientSecret` | `string` | OAuth client secret (required) |
| `scope` | `string[]` | Requested permissions |
| `redirectURI` | `string` | Custom callback URL |
| `disableSignUp` | `boolean` | Block new user registration |
| `disableImplicitSignUp` | `boolean` | Require explicit `requestSignUp: true` |
| `mapProfileToUser` | `function` | Transform provider data to user fields |
| `overrideUserInfoOnSignIn` | `boolean` | Update stored user info on each sign-in |
| `prompt` | `string` | OAuth prompt parameter |
| `disableDefaultScope` | `boolean` | Use only explicitly set scopes |

### Custom Profile Mapping

```typescript
google: {
  clientId: process.env.GOOGLE_CLIENT_ID!,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
  mapProfileToUser: (profile) => ({
    name: profile.name,
    image: profile.picture,
    // Map custom fields
    locale: profile.locale,
  }),
}
```

### Disable Sign-Up

```typescript
github: {
  clientId: "...",
  clientSecret: "...",
  disableSignUp: true, // Only existing users can sign in
}
```

## Account Linking

Account linking connects multiple OAuth providers to one user account. Enabled by default when the provider confirms email verification.

### Configure Linking

```typescript
export const auth = betterAuth({
  account: {
    accountLinking: {
      enabled: true, // default
      trustedProviders: ["google", "github"], // Auto-link without email verification
    },
  },
});
```

### Manual Social Linking

```typescript
// Link a new provider to existing account
await authClient.linkSocial({
  provider: "google",
  callbackURL: "/settings",
});

// Link with ID token directly
await authClient.linkSocial({
  provider: "google",
  idToken: {
    token: "id_token_from_provider",
    nonce: "nonce_used",
    accessToken: "optional_access_token",
    refreshToken: "optional_refresh_token",
  },
});
```

### Unlink Account

```typescript
await authClient.unlinkAccount({
  providerId: "google",
});
```

Unlinking is blocked if the user has only one account (unless `allowUnlinkingAll` is enabled).

### Disable Linking

```typescript
account: {
  accountLinking: { enabled: false },
}
```

## Token Access & Refresh

Access stored OAuth tokens for API calls to the provider:

```typescript
// Client-side: get access token
const { data } = await authClient.getAccessToken({
  providerId: "github",
});
// data.accessToken — automatically refreshed if expired
```

### Custom Token Refresh

```typescript
github: {
  clientId: "...",
  clientSecret: "...",
  refreshAccessToken: async (refreshToken) => {
    // Custom refresh logic
    return {
      accessToken: "new_access_token",
      refreshToken: "new_refresh_token",
      expiresIn: 3600,
    };
  },
}
```

## Additional Data Through OAuth

Pass temporary data through the OAuth flow without database persistence:

```typescript
// Client: pass data during sign-in
await authClient.signIn.social({
  provider: "google",
  additionalData: {
    referralCode: "ABC123",
    source: "landing-page",
  },
});

// Server: access in hooks
hooks: {
  after: createAuthMiddleware(async (ctx) => {
    if (ctx.path === "/callback/:id") {
      const data = await getOAuthState<{
        referralCode?: string;
        source?: string;
      }>();
      // Use data.referralCode, data.source
    }
  }),
}
```

**Security note:** Always validate and sanitize `additionalData` — it originates from client requests.

## Advanced Features

### Request Additional Scopes

Re-invoke `linkSocial()` with new scopes to trigger re-authorization:

```typescript
await authClient.linkSocial({
  provider: "google",
  scopes: ["https://www.googleapis.com/auth/calendar.readonly"],
});
```

### Custom User Info Retrieval

Override the default provider profile API:

```typescript
google: {
  clientId: "...",
  clientSecret: "...",
  getUserInfo: async (token) => {
    const response = await fetch("https://custom-api.example.com/userinfo", {
      headers: { Authorization: `Bearer ${token.accessToken}` },
    });
    return await response.json();
  },
}
```

### OAuth Prompt Parameter

```typescript
google: {
  clientId: "...",
  clientSecret: "...",
  prompt: "select_account", // or "consent", "login"
}
```

## Common Pitfalls

1. **Wrong callback URL** — Set the callback URL in your provider's developer console to `{BETTER_AUTH_URL}/api/auth/callback/{providerName}`.
2. **Missing env vars** — Provider credentials in `.env` must be loaded before auth initialization.
3. **Account linking with unverified emails** — Only `trustedProviders` skip email verification for auto-linking.
4. **Custom OAuth providers** — Use the Generic OAuth Plugin for non-built-in providers. Note: custom providers don't support `refreshAccessToken`.
5. **Forgetting `allowDifferentEmails`** — By default, linking requires matching email addresses.
