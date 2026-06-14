# Clerk — Organizations

> Source: [clerk.com/docs/organizations/overview](https://clerk.com/docs/organizations/overview)

## Table of Contents

- [Overview](#overview)
- [Key Concepts](#key-concepts)
- [Enabling Organizations](#enabling-organizations)
- [Creating Organizations](#creating-organizations)
- [Roles and Permissions](#roles-and-permissions)
- [Member Management](#member-management)
- [Invitations](#invitations)
- [Verified Domains](#verified-domains)
- [Organization Components](#organization-components)
- [Server-Side Organization Access](#server-side-organization-access)
- [Client-Side Organization Access](#client-side-organization-access)
- [Multi-Tenant Data Patterns](#multi-tenant-data-patterns)
- [Common Patterns](#common-patterns)

## Overview

Clerk Organizations enable multi-tenant B2B applications where users can belong to multiple teams, companies, or workspaces — similar to Slack workspaces, Linear teams, or Vercel projects.

Each user can belong to multiple organizations simultaneously, with different roles and permissions in each. One organization is "active" at a time, determining the user's current context.

## Key Concepts

**Organization:** A group entity (team, company, workspace) that users can join.

**Active Organization:** The currently selected org — determines data access and permissions. Each browser tab maintains its own active org independently.

**Membership:** A user's association with an organization, including their role.

**Role:** A set of permissions assigned to a member. Defined once at the application level, applied across all organizations.

**Permission:** A granular capability like `org:billing:manage` or `org:project:delete`.

**Invitation:** An email-based invite to join an organization with a specific role.

**Verified Domain:** A domain claimed by an organization (e.g., `@acme.com`) for automatic membership.

**Monthly Retained Organizations (MROs):** Billing metric — an org with ≥2 members where ≥1 member is a Monthly Retained User. Free: 50 MROs (dev), 100 MROs (prod).

## Enabling Organizations

```bash
# Via CLI
npx clerk@latest enable orgs

# Verify in Dashboard > Organizations
```

## Creating Organizations

**Via component:**
```tsx
import { CreateOrganization } from '@clerk/nextjs'

<CreateOrganization afterCreateOrganizationUrl="/org/:slug" />
```

**Via hook:**
```tsx
import { useOrganizationList } from '@clerk/nextjs'

function CreateOrgForm() {
  const { createOrganization } = useOrganizationList()

  const handleCreate = async (name: string) => {
    const org = await createOrganization({ name })
    // org.id, org.slug available
  }
}
```

**Via Backend API:**
```tsx
import { clerkClient } from '@clerk/nextjs/server'

const client = await clerkClient()
const org = await client.organizations.createOrganization({
  name: 'Acme Corp',
  slug: 'acme-corp',
  createdBy: 'user_123',
})
```

## Roles and Permissions

Roles are defined at the application level in the Clerk Dashboard under **Organizations > Roles & Permissions**.

**Default roles:**
- `org:admin` — Full organization management
- `org:member` — Basic membership access

**Custom roles example:**
```
org:billing_manager — Can manage billing
org:developer — Can access development resources
org:viewer — Read-only access
```

**Custom permissions example:**
```
org:project:create
org:project:read
org:project:update
org:project:delete
org:billing:manage
org:member:invite
org:settings:manage
```

**Checking permissions in components:**
```tsx
import { Protect } from '@clerk/nextjs'

<Protect permission="org:billing:manage">
  <BillingSettings />
</Protect>

<Protect role="org:admin" fallback={<p>Admin only</p>}>
  <OrgSettings />
</Protect>
```

**Checking permissions in hooks:**
```tsx
const { has } = useAuth()

const canManageBilling = has?.({ permission: 'org:billing:manage' })
const isAdmin = has?.({ role: 'org:admin' })
```

**Checking permissions on server:**
```tsx
import { auth } from '@clerk/nextjs/server'

export default async function BillingPage() {
  const { protect } = await auth()
  protect({ permission: 'org:billing:manage' })

  return <BillingDashboard />
}
```

## Member Management

**List members (server-side):**
```tsx
const client = await clerkClient()

const members = await client.organizations.getOrganizationMembershipList({
  organizationId: 'org_123',
  limit: 50,
})
```

**Update member role:**
```tsx
await client.organizations.updateOrganizationMembership({
  organizationId: 'org_123',
  userId: 'user_456',
  role: 'org:admin',
})
```

**Remove member:**
```tsx
await client.organizations.deleteOrganizationMembership({
  organizationId: 'org_123',
  userId: 'user_456',
})
```

**Client-side member management:**
```tsx
const { organization } = useOrganization()

// Get members
const { data: members } = useOrganization({
  membershipList: { limit: 20 },
})

// Invite a member
await organization.inviteMember({
  emailAddress: 'user@example.com',
  role: 'org:member',
})

// Remove a member
await organization.removeMember('user_456')

// Update a member's role
await organization.updateMember({
  userId: 'user_456',
  role: 'org:admin',
})
```

## Invitations

Users can be invited to organizations via email:

```tsx
// Server-side
const client = await clerkClient()

await client.organizations.createOrganizationInvitation({
  organizationId: 'org_123',
  emailAddress: 'new@example.com',
  role: 'org:member',
  inviterUserId: 'user_456',
})

// List pending invitations
const invitations = await client.organizations.getOrganizationInvitationList({
  organizationId: 'org_123',
  status: ['pending'],
})

// Revoke an invitation
await client.organizations.revokeOrganizationInvitation({
  organizationId: 'org_123',
  invitationId: 'inv_789',
  requestingUserId: 'user_456',
})
```

**Bulk invitations:**
```tsx
const emails = ['a@example.com', 'b@example.com', 'c@example.com']

await Promise.all(
  emails.map((email) =>
    client.organizations.createOrganizationInvitation({
      organizationId: 'org_123',
      emailAddress: email,
      role: 'org:member',
      inviterUserId: adminUserId,
    })
  )
)
```

## Verified Domains

Verified domains automatically invite users with matching email domains:

1. Admin adds a domain (e.g., `acme.com`) in the org settings
2. Clerk verifies domain ownership (DNS TXT record or email verification)
3. Users signing up with `@acme.com` are automatically invited or added

**Enrollment modes:**
- **Automatic invitation** — Users get an invitation email
- **Automatic suggestion** — Users see a suggestion to join
- **Manual invitation** — Domain verified but no auto-enrollment

## Organization Components

```tsx
// Switch between organizations
<OrganizationSwitcher
  afterCreateOrganizationUrl="/org/:slug"
  afterSelectOrganizationUrl="/org/:slug"
  hidePersonal={false}
/>

// Organization settings and member management
<OrganizationProfile path="/org/settings" />

// Create new organization
<CreateOrganization afterCreateOrganizationUrl="/org/:slug" />

// List organizations
<OrganizationList
  afterSelectOrganizationUrl="/org/:slug"
  afterCreateOrganizationUrl="/org/:slug"
/>
```

## Server-Side Organization Access

```tsx
import { auth } from '@clerk/nextjs/server'

export default async function OrgPage() {
  const { userId, orgId, orgRole, orgSlug } = await auth()

  if (!orgId) {
    redirect('/select-organization')
  }

  // orgId is the active organization
  // orgRole is the user's role in that org
  const data = await db.project.findMany({
    where: { organizationId: orgId },
  })

  return <ProjectList projects={data} isAdmin={orgRole === 'org:admin'} />
}
```

## Client-Side Organization Access

```tsx
import { useOrganization, useOrganizationList } from '@clerk/nextjs'

function OrgDashboard() {
  const { organization, membership } = useOrganization()
  const { organizationList, setActive } = useOrganizationList()

  if (!organization) {
    return <p>Select an organization</p>
  }

  return (
    <div>
      <h1>{organization.name}</h1>
      <p>Your role: {membership?.role}</p>
      <p>Members: {organization.membersCount}</p>
    </div>
  )
}
```

## Multi-Tenant Data Patterns

**Database schema with org scoping:**
```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  organization_id TEXT NOT NULL,  -- Clerk org ID
  created_by TEXT NOT NULL,       -- Clerk user ID
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_projects_org ON projects(organization_id);
```

**Always scope queries by orgId:**
```tsx
import { auth } from '@clerk/nextjs/server'

export async function GET() {
  const { userId, orgId } = await auth()

  if (!userId || !orgId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const projects = await db.project.findMany({
    where: { organizationId: orgId },
  })

  return NextResponse.json(projects)
}
```

## Common Patterns

**Require org selection before accessing app:**
```tsx
export default clerkMiddleware(async (auth, req) => {
  const { userId, orgId } = await auth()

  if (userId && !orgId && req.nextUrl.pathname.startsWith('/app')) {
    return NextResponse.redirect(new URL('/select-org', req.url))
  }
})
```

**Personal workspace + organizations:**
```tsx
const { orgId, userId } = await auth()

const ownerId = orgId ?? userId
const projects = await db.project.findMany({
  where: { ownerId },
})
```
