# Supabase — Authentication

> Source: https://supabase.com/docs/guides/auth

## Table of Contents

- [Overview](#overview)
- [Email & Password](#email--password)
- [Magic Link & OTP](#magic-link--otp)
- [Social Login (OAuth)](#social-login-oauth)
- [Phone Authentication](#phone-authentication)
- [Single Sign-On (SSO)](#single-sign-on-sso)
- [Session Management](#session-management)
- [Multi-Factor Authentication](#multi-factor-authentication)
- [User Management](#user-management)
- [Auth Hooks](#auth-hooks)
- [Common Pitfalls](#common-pitfalls)

## Overview

Supabase Auth (powered by GoTrue) handles user identity with JWT tokens that integrate directly with Row Level Security. When a user signs in, the JWT is automatically included in all database requests, and RLS policies use `auth.uid()` to filter data per-user.

**Authentication** = verifying identity (who are you?)
**Authorization** = checking access (what can you do?) — handled by RLS policies.

Pricing is based on Monthly Active Users (MAU), not total registered users.

## Email & Password

Email auth is enabled by default. Email verification is enabled on hosted projects.

### Sign Up

```typescript
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'securepassword123',
  options: {
    emailRedirectTo: 'https://myapp.com/welcome',
    data: {
      display_name: 'Jane Doe',
      avatar_url: 'https://example.com/avatar.jpg',
    },
  },
})
```

The `options.data` object is stored in `raw_user_meta_data` and accessible via `auth.jwt()`.

### Sign In

```typescript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'securepassword123',
})
// data.session contains the JWT tokens
// data.user contains user profile
```

### Password Reset

```typescript
// Step 1: Send reset email
await supabase.auth.resetPasswordForEmail('user@example.com', {
  redirectTo: 'https://myapp.com/update-password',
})

// Step 2: User clicks link, lands on your page, then:
await supabase.auth.updateUser({
  password: 'newSecurePassword456',
})
```

### PKCE Flow (Server-Side Rendering)

For SSR frameworks (Next.js, SvelteKit), use the PKCE flow:

```typescript
// Sign up (same API, but handle the callback server-side)
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'securepassword123',
  options: {
    emailRedirectTo: 'https://myapp.com/auth/callback',
  },
})
```

Callback route (Next.js example):

```typescript
// app/auth/callback/route.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get('code')

  if (code) {
    const supabase = createServerClient(/* ... */)
    await supabase.auth.exchangeCodeForSession(code)
  }

  return NextResponse.redirect(new URL('/', request.url))
}
```

## Magic Link & OTP

Passwordless authentication via email:

```typescript
// Magic Link — user clicks a link in their email
const { error } = await supabase.auth.signInWithOtp({
  email: 'user@example.com',
  options: {
    emailRedirectTo: 'https://myapp.com/dashboard',
  },
})

// OTP — user enters a 6-digit code
const { error } = await supabase.auth.signInWithOtp({
  email: 'user@example.com',
  options: {
    shouldCreateUser: true,  // Create account if doesn't exist
  },
})

// Verify OTP
const { data, error } = await supabase.auth.verifyOtp({
  email: 'user@example.com',
  token: '123456',
  type: 'email',
})
```

## Social Login (OAuth)

Supabase supports 20+ OAuth providers including Google, GitHub, Apple, Discord, Twitter, Microsoft, Facebook, Slack, and Spotify.

### Basic OAuth Flow

```typescript
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: 'https://myapp.com/auth/callback',
    scopes: 'email profile',
    queryParams: {
      access_type: 'offline',
      prompt: 'consent',
    },
  },
})
// data.url contains the OAuth redirect URL
```

### Google One Tap / ID Token

```typescript
const { data, error } = await supabase.auth.signInWithIdToken({
  provider: 'google',
  token: response.credential,  // From Google's GSI library
})
```

### Provider Setup

1. Create OAuth credentials in the provider's developer console
2. Set the redirect URI to `https://<project-ref>.supabase.co/auth/v1/callback`
3. Add Client ID and Secret in Dashboard → Authentication → Providers

### Available Providers

Apple, Azure, Bitbucket, Discord, Facebook, Figma, GitHub, GitLab, Google, Kakao, Keycloak, LinkedIn (OIDC), Notion, Slack (OIDC), Spotify, Twitch, Twitter, WorkOS, Zoom, and custom OIDC/OAuth2 providers.

## Phone Authentication

Requires an SMS provider (Twilio, MessageBird, Vonage, or TextLocal):

```typescript
// Sign up with phone
const { data, error } = await supabase.auth.signUp({
  phone: '+13334445555',
  password: 'securepassword123',
})

// Verify phone via OTP
const { data, error } = await supabase.auth.verifyOtp({
  phone: '+13334445555',
  token: '123456',
  type: 'sms',
})

// Sign in with phone
const { data, error } = await supabase.auth.signInWithPassword({
  phone: '+13334445555',
  password: 'securepassword123',
})
```

## Single Sign-On (SSO)

Enterprise SSO with SAML 2.0 providers:

```typescript
const { data, error } = await supabase.auth.signInWithSSO({
  domain: 'company.com',
  options: {
    redirectTo: 'https://myapp.com/dashboard',
  },
})
```

## Session Management

```typescript
// Get current session
const { data: { session } } = await supabase.auth.getSession()

// Get current user
const { data: { user } } = await supabase.auth.getUser()

// Listen for auth state changes
supabase.auth.onAuthStateChange((event, session) => {
  // event: 'SIGNED_IN' | 'SIGNED_OUT' | 'TOKEN_REFRESHED' |
  //        'USER_UPDATED' | 'PASSWORD_RECOVERY'
  console.log(event, session)
})

// Sign out
await supabase.auth.signOut()

// Sign out from all devices
await supabase.auth.signOut({ scope: 'global' })
```

## Multi-Factor Authentication

### Enroll a TOTP Factor

```typescript
const { data, error } = await supabase.auth.mfa.enroll({
  factorType: 'totp',
  friendlyName: 'My Authenticator App',
})
// data.totp.qr_code — display QR code to user
// data.totp.uri — manual entry URI
// data.id — factor ID for verification
```

### Verify MFA Challenge

```typescript
const { data: challenge } = await supabase.auth.mfa.challenge({
  factorId: factorId,
})

const { data, error } = await supabase.auth.mfa.verify({
  factorId: factorId,
  challengeId: challenge.id,
  code: '123456',  // From authenticator app
})
```

### Check MFA Status in RLS

```sql
create policy "Require MFA for sensitive data"
  on sensitive_table
  as restrictive
  for select
  to authenticated
  using ((select auth.jwt()->>'aal') = 'aal2');
```

## User Management

```typescript
// Update user profile
await supabase.auth.updateUser({
  data: { display_name: 'New Name' },
})

// Update email (sends confirmation to new email)
await supabase.auth.updateUser({
  email: 'newemail@example.com',
})

// Admin: list users (server-side only with service_role key)
const { data, error } = await supabase.auth.admin.listUsers()

// Admin: create user
const { data, error } = await supabase.auth.admin.createUser({
  email: 'user@example.com',
  password: 'password',
  email_confirm: true,
})
```

## Auth Hooks

Server-side hooks let you customize auth behavior:

- **Custom Access Token** — modify JWT claims before token issuance
- **MFA Verification** — add custom MFA verification logic
- **Send SMS** — use a custom SMS provider
- **Send Email** — use a custom email provider

## Common Pitfalls

1. **Using `getSession()` for security** — `getSession()` reads from local storage and can be tampered with. Use `getUser()` for server-side verification (it makes a network request to validate the JWT).
2. **Not handling `onAuthStateChange`** — The auth listener is essential for keeping UI in sync. Subscribe on app mount and unsubscribe on cleanup.
3. **Storing auth data in `user_metadata`** — `raw_user_meta_data` is editable by the user. Use `raw_app_meta_data` (server-only) for authorization decisions.
4. **Forgetting `emailRedirectTo`** — Without it, confirmation emails redirect to the Supabase default page instead of your app.
5. **Not configuring custom SMTP** — The built-in email service has rate limits (3/hour per recipient). Configure custom SMTP for production.
6. **JWT claim staleness** — JWT claims are static until the token refreshes. Immediate permission changes won't take effect until the session refreshes.
