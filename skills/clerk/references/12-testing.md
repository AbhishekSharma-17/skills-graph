# Clerk — Testing & Development

> Source: [clerk.com/docs/testing/overview](https://clerk.com/docs/testing/overview)

## Table of Contents

- [Overview](#overview)
- [Development vs Production](#development-vs-production)
- [Testing Tokens](#testing-tokens)
- [Fake Users with OTP](#fake-users-with-otp)
- [Session Tokens for API Testing](#session-tokens-for-api-testing)
- [Playwright Integration](#playwright-integration)
- [Cypress Integration](#cypress-integration)
- [Agent Tasks](#agent-tasks)
- [Unit Testing Components](#unit-testing-components)
- [Testing Webhooks](#testing-webhooks)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Overview

Testing authenticated flows requires special handling because Clerk includes bot detection that can block automated test suites. Clerk provides several mechanisms to work around this:

- **Testing Tokens** — Bypass bot detection in test suites
- **Fake Users with OTP** — Use fixed codes with fake email/phone
- **Session Tokens** — Programmatically create sessions for API testing
- **@clerk/testing** — Official testing utilities for Playwright and Cypress
- **Agent Tasks** — Create sessions without sign-in flows

## Development vs Production

**Development instances:**
- Use `pk_test_...` and `sk_test_...` keys
- Shared OAuth credentials (no need for your own Google/GitHub apps)
- Free access to all features (MFA, session config, etc.)
- Bot detection is relaxed

**Production instances:**
- Use `pk_live_...` and `sk_live_...` keys
- Require your own OAuth app credentials
- Some features require paid plans
- Full bot detection enabled

Always test against a development instance first. Use separate Clerk instances for development, staging, and production.

## Testing Tokens

Testing Tokens are short-lived tokens that bypass Clerk's bot detection. This prevents test suites from being blocked.

### Getting a Testing Token

```tsx
// Via Backend API
const client = await clerkClient()
const testingToken = await client.testingTokens.createTestingToken()
// Returns { token: "...", expiresAt: ... }
```

### Using Testing Tokens

Append as a query parameter to Frontend API requests:

```
?__clerk_testing_token=<token_value>
```

The `@clerk/testing` package handles this automatically for Playwright and Cypress.

### Limitations in Production
- Testing Tokens don't support code-based auth (OTP, magic links)
- Only email/password or direct email sign-in work
- Full Testing Token support is available in development instances

## Fake Users with OTP

Use fake email addresses or phone numbers with fixed OTP codes:

### Fake Email Addresses

```
Pattern: any+clerk_test@example.com
Fixed OTP: 424242
```

```tsx
// In your test
await signIn.create({
  identifier: 'testuser+clerk_test@example.com',
  strategy: 'email_code',
})

await signIn.attemptFirstFactor({
  strategy: 'email_code',
  code: '424242',
})
```

### Fake Phone Numbers

```
Pattern: +1155500001XX (where XX varies)
Fixed OTP: 424242
```

No actual SMS or email is sent for these test identifiers.

## Session Tokens for API Testing

Create sessions programmatically for API testing:

```tsx
import { clerkClient } from '@clerk/nextjs/server'

async function getTestSessionToken(userId: string) {
  const client = await clerkClient()

  // Create a session for the user
  const session = await client.sessions.createSession({
    userId,
  })

  // Get a session token
  const tokenResponse = await client.sessions.getToken(
    session.id,
    'default'
  )

  return tokenResponse.jwt
}

// Use in tests
const token = await getTestSessionToken('user_test_123')

const res = await fetch('http://localhost:3000/api/data', {
  headers: {
    Authorization: `Bearer ${token}`,
  },
})
```

**Important:** Session tokens expire after ~60 seconds. Refresh before each test or use a timer.

## Playwright Integration

Install the testing package:

```bash
npm install -D @clerk/testing
```

### Setup

```tsx
// playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  use: {
    baseURL: 'http://localhost:3000',
  },
  // Clerk testing setup runs in globalSetup
  globalSetup: './tests/global-setup.ts',
})
```

```tsx
// tests/global-setup.ts
import { clerkSetup } from '@clerk/testing/playwright'

export default async function globalSetup() {
  await clerkSetup()
}
```

### Writing Tests

```tsx
// tests/auth.spec.ts
import { test, expect } from '@playwright/test'
import { clerk } from '@clerk/testing/playwright'

test('authenticated user can access dashboard', async ({ page }) => {
  // Sign in as a test user
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'email_code',
      identifier: 'test+clerk_test@example.com',
    },
  })

  await page.goto('/dashboard')
  await expect(page.getByText('Welcome')).toBeVisible()
})

test('unauthenticated user is redirected', async ({ page }) => {
  await page.goto('/dashboard')
  await expect(page).toHaveURL(/sign-in/)
})

test('sign out works', async ({ page }) => {
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'email_code',
      identifier: 'test+clerk_test@example.com',
    },
  })

  await clerk.signOut({ page })
  await expect(page).toHaveURL('/')
})
```

## Cypress Integration

```bash
npm install -D @clerk/testing
```

### Setup

```tsx
// cypress/support/e2e.ts
import { addClerkCommands } from '@clerk/testing/cypress'

addClerkCommands()
```

```tsx
// cypress/e2e/auth.cy.ts
describe('Authentication', () => {
  it('allows authenticated users to access dashboard', () => {
    cy.clerkSignIn({
      strategy: 'email_code',
      identifier: 'test+clerk_test@example.com',
    })

    cy.visit('/dashboard')
    cy.contains('Welcome').should('be.visible')
  })

  it('redirects unauthenticated users', () => {
    cy.visit('/dashboard')
    cy.url().should('include', 'sign-in')
  })
})
```

## Agent Tasks

Agent Tasks create authenticated sessions without going through the standard sign-in flow — useful for automated testing and AI agent workflows:

```tsx
const client = await clerkClient()

// Create an agent task session
const agentSession = await client.sessions.createSession({
  userId: 'user_123',
})

// Use the session token
const token = await client.sessions.getToken(agentSession.id, 'default')
```

## Unit Testing Components

Mock Clerk's context for unit tests with Vitest or Jest:

```tsx
// __mocks__/@clerk/nextjs.tsx
import { vi } from 'vitest'

export const useUser = vi.fn(() => ({
  isLoaded: true,
  isSignedIn: true,
  user: {
    id: 'user_test',
    firstName: 'Test',
    lastName: 'User',
    fullName: 'Test User',
    primaryEmailAddress: {
      emailAddress: 'test@example.com',
    },
    imageUrl: 'https://example.com/avatar.png',
    publicMetadata: {},
    unsafeMetadata: {},
  },
}))

export const useAuth = vi.fn(() => ({
  isLoaded: true,
  isSignedIn: true,
  userId: 'user_test',
  sessionId: 'sess_test',
  orgId: null,
  orgRole: null,
  getToken: vi.fn(async () => 'mock-token'),
  has: vi.fn(() => false),
  signOut: vi.fn(),
}))

export const useClerk = vi.fn(() => ({
  openSignIn: vi.fn(),
  openSignUp: vi.fn(),
  signOut: vi.fn(),
}))

export const ClerkProvider = ({ children }: { children: React.ReactNode }) =>
  children

export const SignInButton = ({ children }: { children: React.ReactNode }) =>
  children

export const UserButton = () => <div data-testid="user-button" />

export const auth = vi.fn(async () => ({
  userId: 'user_test',
  sessionId: 'sess_test',
  orgId: null,
}))

export const currentUser = vi.fn(async () => ({
  id: 'user_test',
  firstName: 'Test',
  lastName: 'User',
  emailAddresses: [{ emailAddress: 'test@example.com' }],
}))
```

Usage in tests:

```tsx
import { render, screen } from '@testing-library/react'
import { useUser } from '@clerk/nextjs'
import ProfileCard from './ProfileCard'

vi.mock('@clerk/nextjs')

test('renders user profile', () => {
  render(<ProfileCard />)
  expect(screen.getByText('Test User')).toBeInTheDocument()
})

test('handles signed out state', () => {
  vi.mocked(useUser).mockReturnValue({
    isLoaded: true,
    isSignedIn: false,
    user: null,
  })

  render(<ProfileCard />)
  expect(screen.getByText('Sign in')).toBeInTheDocument()
})
```

## Testing Webhooks

Test webhooks locally using the Clerk CLI:

```bash
# Forward webhooks to local server
clerk webhooks proxy --url http://localhost:3000/api/webhooks/clerk
```

Or use ngrok:

```bash
ngrok http 3000
# Set ngrok URL as webhook endpoint in Dashboard
```

For unit testing webhook handlers:

```tsx
import { describe, it, expect } from 'vitest'

describe('Webhook handler', () => {
  it('creates user on user.created event', async () => {
    const payload = {
      data: {
        id: 'user_test',
        first_name: 'Jane',
        last_name: 'Doe',
        email_addresses: [{ email_address: 'jane@example.com' }],
      },
      type: 'user.created',
      object: 'event',
      timestamp: Date.now(),
    }

    // Call your handler directly (skip signature verification in tests)
    await handleUserCreated(payload.data)

    const user = await db.user.findUnique({ where: { clerkId: 'user_test' } })
    expect(user).toBeTruthy()
    expect(user?.email).toBe('jane@example.com')
  })
})
```

## Common Patterns

**Test user factory:**
```tsx
async function createTestUser(overrides = {}) {
  const client = await clerkClient()
  return client.users.createUser({
    emailAddress: [`test-${Date.now()}@example.com`],
    password: 'test-password-123',
    firstName: 'Test',
    lastName: 'User',
    ...overrides,
  })
}
```

**Clean up test users:**
```tsx
afterAll(async () => {
  const client = await clerkClient()
  const users = await client.users.getUserList({
    emailAddress: ['test-*@example.com'],
  })
  await Promise.all(
    users.data.map((u) => client.users.deleteUser(u.id))
  )
})
```

## Troubleshooting

**Bot detection blocking tests:**
- Use `@clerk/testing` package for automatic Testing Token handling
- Or manually include `__clerk_testing_token` query parameter

**Session tokens expiring mid-test:**
- Tokens are valid for ~60 seconds
- Refresh before each API call in integration tests
- Use `getToken()` just before each request, not once at setup

**CORS errors in test API calls:**
- Ensure `authorizedParties` in middleware includes your test origin
- Or disable CORS checking in test environment
