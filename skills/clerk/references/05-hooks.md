# Clerk — Client Hooks

> Source: [clerk.com/docs/reference/nextjs/overview](https://clerk.com/docs/reference/nextjs/overview)

## Table of Contents

- [Overview](#overview)
- [useUser](#useuser)
- [useAuth](#useauth)
- [useClerk](#useclerk)
- [useSignIn](#usesignin)
- [useSignUp](#usesignup)
- [useSession](#usesession)
- [useSessionList](#usesessionlist)
- [useOrganization](#useorganization)
- [useOrganizationList](#useorganizationlist)
- [useReverification](#usereverification)
- [Billing Hooks](#billing-hooks)
- [Common Patterns](#common-patterns)

## Overview

Clerk provides React hooks for accessing auth state and user data on the client side. All hooks must be used within the `<ClerkProvider>` context.

These hooks are available in both `@clerk/nextjs` and `@clerk/clerk-react`.

## useUser

Access the current user object and loading state:

```tsx
import { useUser } from '@clerk/nextjs'

function ProfileCard() {
  const { isLoaded, isSignedIn, user } = useUser()

  if (!isLoaded) return <Skeleton />
  if (!isSignedIn) return <SignInPrompt />

  return (
    <div>
      <img src={user.imageUrl} alt={user.fullName ?? 'Avatar'} />
      <h2>{user.fullName}</h2>
      <p>{user.primaryEmailAddress?.emailAddress}</p>
      <p>Joined: {user.createdAt?.toLocaleDateString()}</p>
    </div>
  )
}
```

**Return values:**

| Property | Type | Description |
|----------|------|-------------|
| `isLoaded` | `boolean` | Whether Clerk has finished loading |
| `isSignedIn` | `boolean` | Whether the user is signed in |
| `user` | `User \| null` | The full User object |

**User object key properties:**
- `id` — Clerk user ID
- `firstName`, `lastName`, `fullName`
- `primaryEmailAddress` — Primary `EmailAddress` object
- `primaryPhoneNumber` — Primary `PhoneNumber` object
- `imageUrl` — Profile picture URL
- `username` — Username if configured
- `publicMetadata` — Public metadata (read-only on client)
- `unsafeMetadata` — User-writable metadata
- `externalAccounts` — Connected OAuth providers
- `createdAt`, `updatedAt`

**User object methods:**
- `user.update({ firstName, lastName, ... })` — Update profile
- `user.setProfileImage({ file })` — Upload avatar
- `user.createEmailAddress({ email })` — Add email
- `user.createPhoneNumber({ phoneNumber })` — Add phone

## useAuth

Access lightweight auth state without the full User object:

```tsx
import { useAuth } from '@clerk/nextjs'

function AuthStatus() {
  const {
    isLoaded,
    isSignedIn,
    userId,
    sessionId,
    orgId,
    orgRole,
    getToken,
    signOut,
    has,
  } = useAuth()

  if (!isLoaded) return null
  if (!isSignedIn) return <p>Not signed in</p>

  return <p>User: {userId}, Org: {orgId}</p>
}
```

**Return values:**

| Property | Type | Description |
|----------|------|-------------|
| `isLoaded` | `boolean` | Whether Clerk has finished loading |
| `isSignedIn` | `boolean` | Whether user is signed in |
| `userId` | `string \| null` | Current user ID |
| `sessionId` | `string \| null` | Current session ID |
| `orgId` | `string \| null` | Active organization ID |
| `orgRole` | `string \| null` | Role in active organization |
| `orgSlug` | `string \| null` | Active organization slug |
| `getToken` | `(opts?) => Promise<string \| null>` | Get session or custom JWT |
| `signOut` | `(opts?) => Promise<void>` | Sign the user out |
| `has` | `(params) => boolean` | Check role or permission |

**getToken usage:**

```tsx
const { getToken } = useAuth()

// Default session token
const token = await getToken()

// Custom JWT template (configured in Clerk Dashboard)
const supabaseToken = await getToken({ template: 'supabase' })

// Use with fetch
const res = await fetch('/api/data', {
  headers: { Authorization: `Bearer ${token}` },
})
```

## useClerk

Access the Clerk instance for imperative actions:

```tsx
import { useClerk } from '@clerk/nextjs'

function CustomSignOut() {
  const clerk = useClerk()

  const handleSignOut = async () => {
    await clerk.signOut()
    window.location.href = '/'
  }

  return <button onClick={handleSignOut}>Sign Out</button>
}
```

**Clerk instance methods:**
- `clerk.openSignIn(props?)` — Open sign-in modal
- `clerk.openSignUp(props?)` — Open sign-up modal
- `clerk.openUserProfile(props?)` — Open user profile modal
- `clerk.openOrganizationProfile(props?)` — Open org profile modal
- `clerk.openCreateOrganization(props?)` — Open create org modal
- `clerk.signOut(opts?)` — Sign out current or all sessions
- `clerk.setActive({ session?, organization? })` — Switch active session/org

## useSignIn

Build custom sign-in flows:

```tsx
import { useSignIn } from '@clerk/nextjs'

function CustomSignIn() {
  const { signIn, setActive, isLoaded } = useSignIn()

  const handleEmailPassword = async (email: string, password: string) => {
    if (!isLoaded) return

    const result = await signIn.create({
      identifier: email,
      password,
    })

    if (result.status === 'complete') {
      await setActive({ session: result.createdSessionId })
    } else if (result.status === 'needs_second_factor') {
      // Handle MFA
    } else if (result.status === 'needs_first_factor') {
      // Handle additional verification
    }
  }

  const handleOAuth = async (provider: string) => {
    await signIn.authenticateWithRedirect({
      strategy: `oauth_${provider}`,
      redirectUrl: '/sso-callback',
      redirectUrlComplete: '/dashboard',
    })
  }

  // render your custom form
}
```

**SignIn statuses:**
- `complete` — Sign-in successful, call `setActive()`
- `needs_first_factor` — First factor verification needed
- `needs_second_factor` — MFA required
- `needs_identifier` — Need to provide identifier

## useSignUp

Build custom sign-up flows:

```tsx
import { useSignUp } from '@clerk/nextjs'

function CustomSignUp() {
  const { signUp, setActive, isLoaded } = useSignUp()

  const handleSignUp = async (
    email: string,
    password: string,
    firstName: string,
  ) => {
    if (!isLoaded) return

    await signUp.create({
      emailAddress: email,
      password,
      firstName,
    })

    // Send email verification
    await signUp.prepareEmailAddressVerification({
      strategy: 'email_code',
    })

    // After user enters the code:
    const result = await signUp.attemptEmailAddressVerification({
      code: '123456',
    })

    if (result.status === 'complete') {
      await setActive({ session: result.createdSessionId })
    }
  }
}
```

## useSession

Access the current session:

```tsx
import { useSession } from '@clerk/nextjs'

function SessionInfo() {
  const { isLoaded, session } = useSession()

  if (!isLoaded || !session) return null

  return (
    <div>
      <p>Session ID: {session.id}</p>
      <p>Last active: {session.lastActiveAt?.toLocaleString()}</p>
      <p>Expires: {session.expireAt?.toLocaleString()}</p>
    </div>
  )
}
```

## useSessionList

Manage multiple sessions (multi-session apps):

```tsx
import { useSessionList } from '@clerk/nextjs'

function SessionManager() {
  const { sessions, setActive, isLoaded } = useSessionList()

  if (!isLoaded) return null

  return (
    <ul>
      {sessions.map((session) => (
        <li key={session.id}>
          <span>{session.user?.primaryEmailAddress?.emailAddress}</span>
          <button onClick={() => setActive({ session: session.id })}>
            Switch
          </button>
        </li>
      ))}
    </ul>
  )
}
```

## useOrganization

Access the active organization and manage its members:

```tsx
import { useOrganization } from '@clerk/nextjs'

function OrgInfo() {
  const { organization, membership, isLoaded } = useOrganization()

  if (!isLoaded || !organization) return null

  return (
    <div>
      <h2>{organization.name}</h2>
      <p>Slug: {organization.slug}</p>
      <p>Your role: {membership?.role}</p>
      <p>Members: {organization.membersCount}</p>
    </div>
  )
}
```

Invite members:

```tsx
const { organization } = useOrganization()

await organization.inviteMember({
  emailAddress: 'user@example.com',
  role: 'org:member',
})
```

## useOrganizationList

List all organizations the user belongs to:

```tsx
import { useOrganizationList } from '@clerk/nextjs'

function OrgList() {
  const { organizationList, isLoaded, setActive } = useOrganizationList({
    userMemberships: { infinite: true },
  })

  if (!isLoaded) return null

  return (
    <ul>
      {organizationList?.map(({ organization, membership }) => (
        <li key={organization.id}>
          <span>{organization.name} ({membership.role})</span>
          <button
            onClick={() => setActive({ organization: organization.id })}
          >
            Switch
          </button>
        </li>
      ))}
    </ul>
  )
}
```

## useReverification

Re-verify user identity for sensitive operations:

```tsx
import { useReverification } from '@clerk/nextjs'

function DeleteAccountButton() {
  const { verify } = useReverification()

  const handleDelete = async () => {
    const verified = await verify()
    if (verified) {
      await deleteAccount()
    }
  }

  return <button onClick={handleDelete}>Delete My Account</button>
}
```

## Billing Hooks

Clerk provides hooks for subscription/billing management (requires Clerk Billing):

| Hook | Purpose |
|------|---------|
| `useCheckout()` | Initiate checkout flow |
| `usePaymentElement()` | Render payment form element |
| `usePaymentMethods()` | List/manage payment methods |
| `usePlans()` | List available pricing plans |
| `useSubscription()` | Access current subscription |
| `usePaymentAttempts()` | View payment history |
| `useStatements()` | Access billing statements |
| `useAPIKeys()` | Manage API keys |

## Common Patterns

**Conditional rendering by auth state:**
```tsx
function App() {
  const { isLoaded, isSignedIn } = useUser()
  if (!isLoaded) return <Loading />
  return isSignedIn ? <Dashboard /> : <LandingPage />
}
```

**Permission-based UI:**
```tsx
function AdminFeature() {
  const { has } = useAuth()
  if (!has?.({ permission: 'org:admin:access' })) return null
  return <AdminPanel />
}
```

**Cross-origin API calls:**
```tsx
function useApi() {
  const { getToken } = useAuth()

  return async (path: string, opts?: RequestInit) => {
    const token = await getToken()
    return fetch(`https://api.example.com${path}`, {
      ...opts,
      headers: {
        ...opts?.headers,
        Authorization: `Bearer ${token}`,
      },
    })
  }
}
```
