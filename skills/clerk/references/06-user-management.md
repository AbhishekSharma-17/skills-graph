# Clerk — User Management

> Source: [clerk.com/docs/users/overview](https://clerk.com/docs/users/overview)

## Table of Contents

- [Overview](#overview)
- [User Object](#user-object)
- [Metadata Types](#metadata-types)
- [Frontend User Management](#frontend-user-management)
- [Backend User Management](#backend-user-management)
- [Creating Users](#creating-users)
- [Updating Users](#updating-users)
- [Deleting Users](#deleting-users)
- [Listing and Searching Users](#listing-and-searching-users)
- [User Metadata Patterns](#user-metadata-patterns)
- [Syncing Users to Your Database](#syncing-users-to-your-database)
- [Common Patterns](#common-patterns)

## Overview

Clerk manages user accounts, profiles, and authentication state. The User object is the central data structure containing all user information. You can manage users through:

- **Prebuilt components** — `<UserButton />`, `<UserProfile />`
- **Client hooks** — `useUser()` for reading/updating on the client
- **Server helpers** — `currentUser()` for server-side access
- **Backend API** — `clerkClient` for full CRUD operations
- **Clerk Dashboard** — Manual user management UI

## User Object

Core properties of the User object:

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` | Unique Clerk user ID (`user_...`) |
| `firstName` | `string \| null` | First name |
| `lastName` | `string \| null` | Last name |
| `fullName` | `string \| null` | Computed full name |
| `username` | `string \| null` | Username (if enabled) |
| `imageUrl` | `string` | Profile picture URL |
| `primaryEmailAddress` | `EmailAddress \| null` | Primary email |
| `primaryPhoneNumber` | `PhoneNumber \| null` | Primary phone |
| `emailAddresses` | `EmailAddress[]` | All email addresses |
| `phoneNumbers` | `PhoneNumber[]` | All phone numbers |
| `externalAccounts` | `ExternalAccount[]` | Connected OAuth providers |
| `publicMetadata` | `Record<string, unknown>` | Public metadata |
| `privateMetadata` | `Record<string, unknown>` | Private metadata (server only) |
| `unsafeMetadata` | `Record<string, unknown>` | User-writable metadata |
| `createdAt` | `Date` | Account creation date |
| `updatedAt` | `Date` | Last update date |
| `lastSignInAt` | `Date \| null` | Last sign-in date |
| `banned` | `boolean` | Whether user is banned |
| `locked` | `boolean` | Whether user is locked |
| `twoFactorEnabled` | `boolean` | Whether MFA is enabled |
| `passwordEnabled` | `boolean` | Whether password is set |

## Metadata Types

Clerk supports three metadata categories:

### Public Metadata
- Readable on both client and server
- Writable only from the Backend API or Dashboard
- Use for: subscription plans, feature flags, roles

```tsx
// Read on client
const { user } = useUser()
const plan = user?.publicMetadata?.plan as string

// Write from server
const client = await clerkClient()
await client.users.updateUserMetadata('user_123', {
  publicMetadata: {
    plan: 'pro',
    features: ['advanced-analytics', 'custom-domains'],
  },
})
```

### Private Metadata
- Readable and writable only from the Backend API
- Never exposed to the client
- Use for: internal flags, Stripe customer IDs, admin notes

```tsx
const client = await clerkClient()
await client.users.updateUserMetadata('user_123', {
  privateMetadata: {
    stripeCustomerId: 'cus_...',
    internalNotes: 'VIP customer',
  },
})
```

### Unsafe Metadata
- Readable and writable from both client and server
- Use with caution — users can modify this
- Use for: user preferences, UI settings, onboarding state

```tsx
// Write from client
const { user } = useUser()
await user.update({
  unsafeMetadata: {
    theme: 'dark',
    onboardingComplete: true,
  },
})
```

## Frontend User Management

### Prebuilt Components

```tsx
// User avatar dropdown with menu
import { UserButton } from '@clerk/nextjs'
<UserButton afterSignOutUrl="/" />

// Full user profile page
import { UserProfile } from '@clerk/nextjs'
<UserProfile path="/settings" />
```

### Using useUser Hook

```tsx
import { useUser } from '@clerk/nextjs'

function UpdateProfile() {
  const { user } = useUser()

  const handleUpdate = async (formData: FormData) => {
    await user?.update({
      firstName: formData.get('firstName') as string,
      lastName: formData.get('lastName') as string,
    })
  }

  const handleAvatar = async (file: File) => {
    await user?.setProfileImage({ file })
  }

  const handleAddEmail = async (email: string) => {
    const emailAddress = await user?.createEmailAddress({ email })
    // Triggers verification flow
    await emailAddress?.prepareVerification({ strategy: 'email_code' })
  }
}
```

## Backend User Management

Use `clerkClient` for full CRUD operations from server-side code:

```tsx
import { clerkClient } from '@clerk/nextjs/server'

// Initialize the client
const client = await clerkClient()
```

## Creating Users

```tsx
const client = await clerkClient()

const user = await client.users.createUser({
  emailAddress: ['user@example.com'],
  password: 'secure-password-123',
  firstName: 'Jane',
  lastName: 'Doe',
  publicMetadata: {
    plan: 'free',
  },
})
```

Create user without password (will need to verify email):

```tsx
const user = await client.users.createUser({
  emailAddress: ['user@example.com'],
  firstName: 'Jane',
})
```

## Updating Users

```tsx
const client = await clerkClient()

// Update profile fields
await client.users.updateUser('user_123', {
  firstName: 'Jane',
  lastName: 'Smith',
  username: 'janesmith',
})

// Update metadata (merge, not replace)
await client.users.updateUserMetadata('user_123', {
  publicMetadata: {
    plan: 'pro',
  },
  privateMetadata: {
    stripeCustomerId: 'cus_abc123',
  },
})

// Ban a user
await client.users.banUser('user_123')

// Unban a user
await client.users.unbanUser('user_123')

// Lock a user (prevent sign-in)
await client.users.lockUser('user_123')

// Unlock a user
await client.users.unlockUser('user_123')
```

## Deleting Users

```tsx
const client = await clerkClient()
await client.users.deleteUser('user_123')
```

Bulk deletion is not available via the API — contact Clerk support for large-scale deletions.

## Listing and Searching Users

```tsx
const client = await clerkClient()

// List users with pagination
const users = await client.users.getUserList({
  limit: 20,
  offset: 0,
  orderBy: '-created_at',
})

// Search by email
const results = await client.users.getUserList({
  emailAddress: ['user@example.com'],
})

// Search by query (searches name, email, username)
const results = await client.users.getUserList({
  query: 'jane',
})

// Filter by user IDs
const results = await client.users.getUserList({
  userId: ['user_123', 'user_456'],
})

// Get a single user
const user = await client.users.getUser('user_123')

// Get user count
const count = await client.users.getCount()
```

## User Metadata Patterns

**Subscription management:**
```tsx
// After Stripe checkout success
await client.users.updateUserMetadata(userId, {
  publicMetadata: {
    plan: 'pro',
    planExpiresAt: '2027-01-01',
  },
  privateMetadata: {
    stripeCustomerId: 'cus_...',
    stripeSubscriptionId: 'sub_...',
  },
})
```

**Feature flags:**
```tsx
// Server: set feature flags
await client.users.updateUserMetadata(userId, {
  publicMetadata: {
    features: {
      betaDashboard: true,
      aiAssistant: true,
    },
  },
})

// Client: check feature flags
const { user } = useUser()
const features = user?.publicMetadata?.features as Record<string, boolean>
if (features?.betaDashboard) {
  // show beta dashboard
}
```

**Onboarding state:**
```tsx
// Client: track onboarding progress
const { user } = useUser()
await user.update({
  unsafeMetadata: {
    onboardingStep: 3,
    onboardingComplete: false,
  },
})
```

## Syncing Users to Your Database

Clerk is the source of truth for auth, but you often need user records in your own database. Two approaches:

### 1. Webhook Sync (Recommended)

Listen for `user.created`, `user.updated`, `user.deleted` webhooks:

```tsx
// See references/08-webhooks.md for full implementation
```

### 2. Just-in-Time Sync

Create/update database records on first access:

```tsx
import { auth } from '@clerk/nextjs/server'

export default async function Dashboard() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  // Upsert user in your database
  const dbUser = await db.user.upsert({
    where: { clerkId: userId },
    create: { clerkId: userId },
    update: { lastSeenAt: new Date() },
  })

  return <DashboardContent user={dbUser} />
}
```

## Common Patterns

**Check if user has completed onboarding:**
```tsx
const { user } = useUser()
const onboarded = user?.unsafeMetadata?.onboardingComplete
if (!onboarded) redirect('/onboarding')
```

**Get user's primary email:**
```tsx
const email = user.primaryEmailAddress?.emailAddress
// or from emailAddresses array
const emails = user.emailAddresses.map((e) => e.emailAddress)
```

**Check connected OAuth accounts:**
```tsx
const hasGoogle = user.externalAccounts.some(
  (a) => a.provider === 'google'
)
```
