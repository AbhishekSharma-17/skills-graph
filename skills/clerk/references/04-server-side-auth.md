# Clerk — Server-Side Auth

> Source: [clerk.com/docs/references/nextjs/auth](https://clerk.com/docs/references/nextjs/auth)

## Table of Contents

- [Overview](#overview)
- [auth() Helper](#auth-helper)
- [Auth Object Properties](#auth-object-properties)
- [protect() Method](#protect-method)
- [currentUser() Helper](#currentuser-helper)
- [Server Components](#server-components)
- [Route Handlers](#route-handlers)
- [Server Actions](#server-actions)
- [Pages Router Helpers](#pages-router-helpers)
- [clerkClient](#clerkclient)
- [Common Patterns](#common-patterns)

## Overview

Clerk provides server-side helpers for the Next.js App Router that let you access auth state without client-side JavaScript. These run in Server Components, Route Handlers, and Server Actions.

Key helpers:
- `auth()` — Lightweight, returns auth state (userId, orgId, etc.)
- `currentUser()` — Returns the full User object (makes a Backend API call)
- `clerkClient` — Full Backend API access for CRUD operations

All are imported from `@clerk/nextjs/server`.

## auth() Helper

Returns the Auth object with the current user's authentication state:

```tsx
import { auth } from '@clerk/nextjs/server'

export default async function Page() {
  const { userId, sessionId, orgId } = await auth()

  if (!userId) {
    return <p>Not authenticated</p>
  }

  return <p>User: {userId}</p>
}
```

`auth()` is **async** in `@clerk/nextjs` v6+ — always use `await`.

Requirements:
- Only works in the App Router (Server Components, Route Handlers, Server Actions)
- Requires `clerkMiddleware()` to be configured
- Does NOT make network requests — reads from the middleware-attached auth state

## Auth Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `userId` | `string \| null` | Current user's ID |
| `sessionId` | `string \| null` | Current session ID |
| `orgId` | `string \| null` | Active organization ID |
| `orgRole` | `string \| null` | Role in active org (e.g., `"org:admin"`) |
| `orgSlug` | `string \| null` | Active organization's slug |
| `orgPermissions` | `string[]` | Permissions in active org |
| `sessionClaims` | `JWTPayload` | Full JWT claims |
| `isAuthenticated` | `boolean` | Whether user is signed in |
| `actor` | `object \| null` | Impersonation actor info |
| `has` | `(params) => boolean` | Check role/permission |

Methods:
| Method | Description |
|--------|-------------|
| `protect(params?)` | Enforce auth/authz, redirect or throw on failure |
| `redirectToSignIn(opts?)` | Redirect to sign-in page |
| `getToken(opts?)` | Get session token or custom JWT template |

## protect() Method

`auth.protect()` enforces authentication and authorization:

```tsx
export default async function AdminPage() {
  const { protect } = await auth()

  // Require authentication
  protect()

  // Or require a specific role
  protect({ role: 'org:admin' })

  // Or require a specific permission
  protect({ permission: 'org:billing:manage' })

  // Or use custom logic
  protect((has) => {
    return has({ role: 'org:admin' }) || has({ permission: 'org:super:access' })
  })

  return <AdminDashboard />
}
```

Behavior table:

| State | Page Request | API Request |
|-------|-------------|-------------|
| Authenticated + Authorized | Returns Auth object | Returns Auth object |
| Authenticated + Unauthorized | Returns 404 | Returns 404 |
| Unauthenticated (session) | Redirects to sign-in | Returns 404 |
| Unauthenticated (machine) | — | Returns 401 |

Custom redirect on unauthorized:

```tsx
protect({
  role: 'org:admin',
  unauthorizedUrl: '/not-authorized',
  unauthenticatedUrl: '/sign-in',
})
```

## currentUser() Helper

Returns the full `User` object by making a Backend API call:

```tsx
import { currentUser } from '@clerk/nextjs/server'

export default async function ProfilePage() {
  const user = await currentUser()

  if (!user) {
    return <p>Not signed in</p>
  }

  return (
    <div>
      <h1>{user.firstName} {user.lastName}</h1>
      <p>{user.emailAddresses[0]?.emailAddress}</p>
      <img src={user.imageUrl} alt="Avatar" />
    </div>
  )
}
```

`currentUser()` is heavier than `auth()` — use `auth()` when you only need userId/orgId.

## Server Components

```tsx
// app/dashboard/page.tsx
import { auth, currentUser } from '@clerk/nextjs/server'

export default async function Dashboard() {
  // Lightweight — no API call
  const { userId, orgId } = await auth()

  // Full user data — makes API call
  const user = await currentUser()

  // Protect the page
  if (!userId) {
    return <RedirectToSignIn />
  }

  return <DashboardContent user={user} orgId={orgId} />
}
```

## Route Handlers

```tsx
// app/api/user/route.ts
import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

export async function GET() {
  const { userId } = await auth()

  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // Fetch user-specific data
  const data = await getUserData(userId)
  return NextResponse.json(data)
}

export async function POST(req: Request) {
  const { userId, orgId } = await auth()

  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const body = await req.json()
  const result = await createResource({ ...body, userId, orgId })
  return NextResponse.json(result, { status: 201 })
}
```

## Server Actions

```tsx
// app/actions.ts
'use server'

import { auth } from '@clerk/nextjs/server'

export async function updateProfile(formData: FormData) {
  const { userId } = await auth()

  if (!userId) {
    throw new Error('Unauthorized')
  }

  const name = formData.get('name') as string
  await db.user.update({
    where: { clerkId: userId },
    data: { name },
  })
}

export async function deleteProject(projectId: string) {
  const { protect } = await auth()

  // Only org admins can delete projects
  protect({ permission: 'org:project:delete' })

  await db.project.delete({ where: { id: projectId } })
}
```

## Pages Router Helpers

For the Pages Router, use `getAuth()` and `buildClerkProps()`:

```tsx
// pages/dashboard.tsx
import { getAuth, buildClerkProps } from '@clerk/nextjs/server'
import { GetServerSideProps } from 'next'

export const getServerSideProps: GetServerSideProps = async (ctx) => {
  const { userId } = getAuth(ctx.req)

  if (!userId) {
    return { redirect: { destination: '/sign-in', permanent: false } }
  }

  const data = await getUserData(userId)

  return {
    props: {
      ...buildClerkProps(ctx.req),
      data,
    },
  }
}

export default function Dashboard({ data }) {
  return <DashboardContent data={data} />
}
```

## clerkClient

Access the full Clerk Backend API from server-side code:

```tsx
import { clerkClient } from '@clerk/nextjs/server'

// Get a user
const client = await clerkClient()
const user = await client.users.getUser('user_123')

// List organization members
const members = await client.organizations.getOrganizationMembershipList({
  organizationId: 'org_123',
})

// Update user metadata
await client.users.updateUserMetadata('user_123', {
  publicMetadata: { plan: 'pro' },
})
```

See `references/06-user-management.md` for full Backend API usage.

## Common Patterns

**Fetch user's own data:**
```tsx
export default async function MyDataPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const data = await db.items.findMany({ where: { ownerId: userId } })
  return <ItemList items={data} />
}
```

**Organization-scoped data:**
```tsx
export default async function OrgDashboard() {
  const { userId, orgId } = await auth()
  if (!userId) redirect('/sign-in')
  if (!orgId) redirect('/select-org')

  const projects = await db.project.findMany({
    where: { organizationId: orgId },
  })
  return <ProjectList projects={projects} />
}
```

**Get a custom JWT for external API:**
```tsx
export async function GET() {
  const { getToken } = await auth()
  const token = await getToken({ template: 'supabase' })

  const res = await fetch('https://api.example.com/data', {
    headers: { Authorization: `Bearer ${token}` },
  })
  return NextResponse.json(await res.json())
}
```
