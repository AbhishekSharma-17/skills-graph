# Clerk — Overview & Setup

> Source: [clerk.com/docs](https://clerk.com/docs) | Package: `@clerk/nextjs` v7.5 (Core 3)

## Table of Contents

- [What Is Clerk](#what-is-clerk)
- [When to Use Clerk](#when-to-use-clerk)
- [Clerk vs Alternatives](#clerk-vs-alternatives)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [ClerkProvider Setup](#clerkprovider-setup)
- [Middleware Configuration](#middleware-configuration)
- [Basic Auth Flow](#basic-auth-flow)
- [Project Structure](#project-structure)
- [Key Concepts](#key-concepts)
- [Framework Support](#framework-support)

## What Is Clerk

Clerk is a managed authentication and user management platform for modern web applications. It provides:

- Drop-in sign-in/sign-up UI components with full customization
- Server-side and client-side auth helpers
- Multi-tenant organization support with roles and permissions
- Enterprise SSO (SAML/OIDC) out of the box
- Webhooks for syncing user events to your database
- Session management with short-lived JWTs
- Built-in billing/subscription management via Stripe

Clerk handles the full auth lifecycle — signup, login, session management, user profiles, organizations, and machine-to-machine auth — so you focus on your application logic.

## When to Use Clerk

**Good fit:**
- Next.js or React applications needing auth quickly
- SaaS apps with organization/team features
- Apps needing social login, MFA, or enterprise SSO
- Projects where you want managed infrastructure (no self-hosting auth)
- Multi-tenant B2B applications with role-based access

**Not ideal for:**
- Self-hosted or air-gapped environments (Clerk is cloud-only)
- Applications requiring full control over auth infrastructure
- Budget-constrained projects (free tier has limits)
- Non-JavaScript backends without a Clerk SDK

## Clerk vs Alternatives

| Feature | Clerk | Auth.js | Better Auth | Auth0 |
|---------|-------|---------|-------------|-------|
| Managed service | Yes | No | No | Yes |
| Prebuilt UI | Full | Minimal | Minimal | Partial |
| Organizations | Built-in | DIY | DIY | Add-on |
| Enterprise SSO | Built-in | Plugin | Plugin | Built-in |
| Self-hostable | No | Yes | Yes | No |
| Free tier | Yes | OSS | OSS | Yes |
| Next.js integration | Deep | Good | Good | Good |

## Installation

### CLI Setup (Recommended)

```bash
# Install Clerk CLI globally
npm install -g clerk

# Authenticate with your Clerk account
clerk auth login

# Initialize in an existing or new Next.js project
clerk init

# For new projects — scaffolds with framework detection
clerk init --framework next --pm npm
```

### Manual Setup

```bash
# Next.js (App Router or Pages Router)
npm install @clerk/nextjs

# React (Vite, CRA, etc.)
npm install @clerk/clerk-react

# Express.js backend
npm install @clerk/express

# Backend-only (Node.js)
npm install @clerk/backend
```

## Environment Variables

Create a `.env.local` file in your project root:

```env
# Required — from Clerk Dashboard > API Keys
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Optional — customize redirect URLs
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/dashboard
```

The publishable key is safe for client-side code. The secret key must never be exposed to the browser.

## ClerkProvider Setup

Wrap your application in `ClerkProvider` in your root layout:

```tsx
// app/layout.tsx
import { ClerkProvider } from '@clerk/nextjs'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <ClerkProvider>
          {children}
        </ClerkProvider>
      </body>
    </html>
  )
}
```

`ClerkProvider` goes inside `<body>`, not wrapping `<html>`.

## Middleware Configuration

Create the middleware file at your project root:

```tsx
// middleware.ts (Next.js 15 and below)
// proxy.ts (Next.js 16+)
import { clerkMiddleware } from '@clerk/nextjs/server'

export default clerkMiddleware()

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
    '/__clerk/(.*)',
  ],
}
```

By default, `clerkMiddleware()` does NOT protect any routes — all routes are public unless you explicitly protect them.

## Basic Auth Flow

Add sign-in/sign-up controls to your layout:

```tsx
// app/layout.tsx
import {
  ClerkProvider,
  SignInButton,
  SignUpButton,
  UserButton,
  Show,
} from '@clerk/nextjs'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <ClerkProvider>
          <header>
            <Show when="signed-out">
              <SignInButton />
              <SignUpButton />
            </Show>
            <Show when="signed-in">
              <UserButton />
            </Show>
          </header>
          <main>{children}</main>
        </ClerkProvider>
      </body>
    </html>
  )
}
```

Access user data in a Server Component:

```tsx
// app/dashboard/page.tsx
import { auth, currentUser } from '@clerk/nextjs/server'

export default async function DashboardPage() {
  const { userId } = await auth()
  const user = await currentUser()

  return (
    <div>
      <h1>Welcome, {user?.firstName}</h1>
      <p>User ID: {userId}</p>
    </div>
  )
}
```

## Project Structure

A typical Next.js project with Clerk:

```
my-app/
├── app/
│   ├── layout.tsx              # ClerkProvider wrapper
│   ├── page.tsx                # Public home page
│   ├── sign-in/[[...sign-in]]/
│   │   └── page.tsx            # Dedicated sign-in page
│   ├── sign-up/[[...sign-up]]/
│   │   └── page.tsx            # Dedicated sign-up page
│   ├── dashboard/
│   │   └── page.tsx            # Protected page
│   └── api/
│       └── webhooks/
│           └── clerk/route.ts  # Webhook handler
├── middleware.ts               # clerkMiddleware
├── .env.local                  # API keys
└── package.json
```

## Key Concepts

**Core 3:** The current generation of Clerk's core functionality, shared across all SDKs. Core versions release roughly every 6 months.

**Publishable Key:** A public key (`pk_test_...` or `pk_live_...`) used by the frontend to identify your Clerk instance. Safe to expose.

**Secret Key:** A private key (`sk_test_...` or `sk_live_...`) used by the backend for authenticated API calls. Never expose to the client.

**Session Token:** A short-lived JWT (valid ~60 seconds) containing user identity claims. Automatically refreshed by Clerk.

**Auth Object:** Returned by `auth()` on the server, contains `userId`, `sessionId`, `orgId`, `orgRole`, and helper methods like `protect()` and `redirectToSignIn()`.

**User Object:** The full user profile returned by `currentUser()`, including name, email, metadata, and external accounts.

## Framework Support

**First-party SDKs:**
- Next.js (App Router + Pages Router)
- React, React Router, Vue, Nuxt, Astro
- Expo (React Native), Android, iOS
- Express, Fastify
- Go, Ruby on Rails, Python, Java, C#, PHP

**Community SDKs:**
- Angular, SolidJS, Svelte
- Hono, Koa, Elysia
- Rust, Tauri, Chrome Extensions
