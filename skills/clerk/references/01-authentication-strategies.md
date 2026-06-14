# Clerk — Authentication Strategies

> Source: [clerk.com/docs/authentication](https://clerk.com/docs/authentication/configuration/sign-up-sign-in-options)

## Table of Contents

- [Overview](#overview)
- [Email and Password](#email-and-password)
- [Email Verification Code (OTP)](#email-verification-code-otp)
- [Email Verification Link (Magic Link)](#email-verification-link-magic-link)
- [Phone Number OTP](#phone-number-otp)
- [Username](#username)
- [Passkeys](#passkeys)
- [Social Connections (OAuth)](#social-connections-oauth)
- [Enterprise SSO](#enterprise-sso)
- [Multi-Factor Authentication](#multi-factor-authentication)
- [Web3 Authentication](#web3-authentication)
- [Configuration via Dashboard](#configuration-via-dashboard)
- [Configuration via CLI](#configuration-via-cli)
- [Common Patterns](#common-patterns)

## Overview

Clerk supports multiple authentication strategies that can be mixed and matched. Configure strategies in the Clerk Dashboard under **User & Authentication > Email, Phone, Username** or via the CLI.

Strategies fall into three categories:
- **Identifiers** — How users are identified (email, phone, username)
- **First factors** — How users prove identity (password, OTP, magic link, passkey, OAuth)
- **Second factors** — Optional MFA (SMS, TOTP, backup codes)

## Email and Password

The traditional email + password combination. When enabled:

```
User signs up → provides email + password → verifies email → account created
User signs in → provides email + password → authenticated
```

**Password requirements:**
- Minimum 8 characters (configurable)
- Clerk checks against breached password databases (haveibeenpwned)
- Zxcvbn-based strength scoring available

Disabling passwords only affects new users — existing password users retain access.

```tsx
// Custom sign-up with password (headless)
import { useSignUp } from '@clerk/nextjs'

function SignUpForm() {
  const { signUp, setActive } = useSignUp()

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = new FormData(e.currentTarget)

    const result = await signUp.create({
      emailAddress: form.get('email') as string,
      password: form.get('password') as string,
    })

    if (result.status === 'complete') {
      await setActive({ session: result.createdSessionId })
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="email" type="email" required />
      <input name="password" type="password" required />
      <button type="submit">Sign Up</button>
    </form>
  )
}
```

## Email Verification Code (OTP)

Users receive a one-time passcode via email. No password required.

```
Sign in → enter email → receive 6-digit code → enter code → authenticated
```

```tsx
import { useSignIn } from '@clerk/nextjs'

function EmailOTPSignIn() {
  const { signIn, setActive } = useSignIn()
  const [pendingVerification, setPendingVerification] = useState(false)

  const startSignIn = async (email: string) => {
    await signIn.create({
      identifier: email,
      strategy: 'email_code',
    })
    setPendingVerification(true)
  }

  const verifyCode = async (code: string) => {
    const result = await signIn.attemptFirstFactor({
      strategy: 'email_code',
      code,
    })
    if (result.status === 'complete') {
      await setActive({ session: result.createdSessionId })
    }
  }

  // render form based on pendingVerification state
}
```

## Email Verification Link (Magic Link)

Users receive a sign-in link via email. Links expire after 10 minutes.

```
Sign in → enter email → receive link → click link → authenticated
```

Optional: Require same-device verification (link must be opened on the same device/browser that initiated the flow).

## Phone Number OTP

Users authenticate with their phone number via SMS OTP. Requires a paid plan in production.

- Default: US and Canada numbers enabled
- Configure SMS allowlist in Dashboard to restrict or expand regions
- Rate limits apply to prevent abuse

## Username

Usernames as an authentication identifier:

- 4–64 characters
- Alphanumeric only (Latin-based characters)
- No special characters or Unicode (prevents spoofing)
- Typically paired with password or another first factor

## Passkeys

WebAuthn-based passwordless authentication using biometrics or device PIN:

- Users create passkeys after initial sign-up
- Maximum 10 passkeys per account
- Domain-specific — work on subdomains but not satellite domains
- Requires a paid plan in production

```tsx
import { useSignIn } from '@clerk/nextjs'

function PasskeySignIn() {
  const { signIn, setActive } = useSignIn()

  const handlePasskey = async () => {
    const result = await signIn.authenticateWithPasskey()
    if (result.status === 'complete') {
      await setActive({ session: result.createdSessionId })
    }
  }

  return <button onClick={handlePasskey}>Sign in with Passkey</button>
}
```

## Social Connections (OAuth)

Clerk supports 20+ OAuth providers out of the box:

**Popular providers:**
- Google, Apple, Microsoft, GitHub, GitLab
- Facebook, X (Twitter), LinkedIn, Discord
- Slack, Notion, Spotify, Twitch, Dropbox

**Web3 providers:**
- MetaMask, Coinbase Wallet, OKX Wallet

**Configuration:**
1. Enable providers in Dashboard > **User & Authentication > Social connections**
2. For production: provide your own OAuth app credentials (client ID + secret)
3. Development mode: uses Clerk's shared dev credentials

```tsx
// Redirect-based OAuth
import { useSignIn } from '@clerk/nextjs'

function SocialSignIn() {
  const { signIn } = useSignIn()

  const handleGoogle = () => {
    signIn.authenticateWithRedirect({
      strategy: 'oauth_google',
      redirectUrl: '/sso-callback',
      redirectUrlComplete: '/dashboard',
    })
  }

  return <button onClick={handleGoogle}>Sign in with Google</button>
}
```

Or use the prebuilt component:

```tsx
import { SignIn } from '@clerk/nextjs'

// Automatically renders configured social buttons
export default function SignInPage() {
  return <SignIn />
}
```

## Enterprise SSO

For B2B applications with SAML or OIDC identity providers:

- **SAML** — Azure AD, Okta, Google Workspace, custom providers
- **OIDC** — Custom OIDC-compatible providers
- **EASIE** — Multi-tenant OIDC for Google Workspace and Microsoft Entra ID

Enterprise connections are domain-scoped. See `references/11-enterprise-sso.md` for full details.

## Multi-Factor Authentication

Three MFA strategies available:

**SMS Verification Code:**
- User receives OTP via SMS after primary authentication
- Requires paid plan in production

**Authenticator App (TOTP):**
- Works with Google Authenticator, Authy, 1Password, etc.
- User scans QR code during setup
- Time-based rotating codes

**Backup Codes:**
- One-time-use recovery codes
- Generated when MFA is enabled
- Typically 10 codes provided

**Configuration options:**
- Optional MFA — users choose to enable
- Required MFA — all users must set up a second factor

```tsx
// Check if MFA is required during sign-in
import { useSignIn } from '@clerk/nextjs'

function SignInWithMFA() {
  const { signIn, setActive } = useSignIn()

  const handleSignIn = async (email: string, password: string) => {
    const result = await signIn.create({
      identifier: email,
      password,
    })

    if (result.status === 'needs_second_factor') {
      // Prompt for TOTP or SMS code
      const mfaResult = await signIn.attemptSecondFactor({
        strategy: 'totp',
        code: '123456', // from authenticator app
      })
      if (mfaResult.status === 'complete') {
        await setActive({ session: mfaResult.createdSessionId })
      }
    }
  }
}
```

## Web3 Authentication

Clerk supports Web3 wallet-based authentication:

- MetaMask, Coinbase Wallet, OKX Wallet
- Sign-in with Ethereum (SIWE) pattern
- Wallet address becomes a user identifier

## Configuration via Dashboard

Navigate to **User & Authentication** in the Clerk Dashboard:

- **Email, Phone, Username** — Enable/disable identifiers
- **Social connections** — Configure OAuth providers
- **Enterprise connections** — Set up SAML/OIDC
- **Multi-factor** — Enable MFA strategies
- **Restrictions** — Allowlist/blocklist domains or emails

## Configuration via CLI

```bash
# View current auth configuration schema
npx clerk@latest config schema

# Patch configuration
npx clerk@latest config patch

# Enable specific features
npx clerk@latest enable orgs
npx clerk@latest enable billing
```

## Common Patterns

**Email-first SaaS:** Email OTP + social login (Google, GitHub) + optional MFA
**Enterprise B2B:** Email/password + SAML SSO + required MFA
**Consumer app:** Social login (Google, Apple) + passkeys
**Developer tool:** GitHub OAuth + email OTP fallback
**Web3 app:** Wallet auth (MetaMask) + email OTP fallback
