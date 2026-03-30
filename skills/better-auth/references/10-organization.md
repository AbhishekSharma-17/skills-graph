# Better Auth — Organization (Multi-Tenant)

> Source: [better-auth.com/docs/plugins/organization](https://www.better-auth.com/docs/plugins/organization) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Organization CRUD](#organization-crud)
- [Members & Roles](#members--roles)
- [Invitations](#invitations)
- [Teams](#teams)
- [Access Control](#access-control)
- [Dynamic Access Control](#dynamic-access-control)
- [Lifecycle Hooks](#lifecycle-hooks)
- [Database Schema](#database-schema)
- [Common Pitfalls](#common-pitfalls)

## Overview

The organization plugin enables multi-tenant workspace management with members, teams, roles, and granular access control. Organizations contain members with roles, optional teams, and an invitation system.

## Setup

### Server

```typescript
import { betterAuth } from "better-auth";
import { organization } from "better-auth/plugins";

export const auth = betterAuth({
  plugins: [organization()],
});
```

### Client

```typescript
import { createAuthClient } from "better-auth/react";
import { organizationClient } from "better-auth/client/plugins";

const authClient = createAuthClient({
  plugins: [organizationClient()],
});
```

Run migrations: `npx auth migrate`

## Organization CRUD

### Create Organization

```typescript
const { data: org } = await authClient.organization.create({
  name: "Acme Corp",
  slug: "acme-corp",       // URL-friendly identifier
  logo: "https://...",     // Optional
  metadata: { plan: "pro" }, // Optional custom data
});
```

### List Organizations

```typescript
const { data: orgs } = await authClient.organization.list();
```

### Update Organization

```typescript
await authClient.organization.update({
  organizationId: "org-id",
  data: { name: "Acme Inc" },
});
```

### Delete Organization

```typescript
await authClient.organization.delete({
  organizationId: "org-id",
});
```

### Set Active Organization

Set which organization the current session is operating in:

```typescript
await authClient.organization.setActive({
  organizationId: "org-id",
});
```

### Get Full Organization

```typescript
const { data } = await authClient.organization.getFullOrganization({
  query: { organizationId: "org-id" },
});
// Returns: org details + members + pending invitations
```

### Restrict Creation

```typescript
organization({
  allowUserToCreateOrganization: async (user) => {
    // Only verified users can create orgs
    return user.emailVerified;
  },
})
```

## Members & Roles

### Default Roles

| Role | Permissions |
|------|-------------|
| **Owner** | Full control, created the organization |
| **Admin** | Full control except org deletion |
| **Member** | Read-only access |

Members can have multiple roles (comma-separated).

### Add Member

```typescript
await authClient.organization.addMember({
  organizationId: "org-id",
  userId: "user-id",
  role: "member",
});
```

### Remove Member

```typescript
await authClient.organization.removeMember({
  organizationId: "org-id",
  memberIdOrEmail: "user-id",
});
```

### Update Role

```typescript
await authClient.organization.updateMemberRole({
  organizationId: "org-id",
  memberId: "member-id",
  role: "admin",
});
```

### Leave Organization

```typescript
await authClient.organization.leave({
  organizationId: "org-id",
});
```

### Get Active Member

```typescript
const { data: member } = await authClient.organization.getActiveMember({
  query: { organizationId: "org-id" },
});
```

## Invitations

### Send Invitation

```typescript
await authClient.organization.inviteMember({
  organizationId: "org-id",
  email: "new-user@example.com",
  role: "member",
});
```

Configure the email sender:

```typescript
organization({
  sendInvitationEmail: async (data) => {
    await sendEmail({
      to: data.email,
      subject: `Invitation to ${data.organization.name}`,
      body: `Accept: ${data.invitationURL}`,
    });
  },
  invitationExpiresIn: 60 * 60 * 48, // 48 hours (default)
})
```

### Accept Invitation

```typescript
await authClient.organization.acceptInvitation({
  invitationId: "invitation-id",
});
```

### Reject Invitation

```typescript
await authClient.organization.rejectInvitation({
  invitationId: "invitation-id",
});
```

### Cancel Invitation

```typescript
await authClient.organization.cancelInvitation({
  invitationId: "invitation-id",
});
```

## Teams

Enable teams for hierarchical structure within organizations:

```typescript
organization({
  teams: {
    enabled: true,
    maximumTeams: 10, // Per organization
  },
})
```

### Create Team

```typescript
const { data: team } = await authClient.organization.createTeam({
  organizationId: "org-id",
  name: "Engineering",
});
```

### List Teams

```typescript
const { data: teams } = await authClient.organization.listTeams({
  query: { organizationId: "org-id" },
});
```

### Manage Team Members

```typescript
// Add member to team
await authClient.organization.addTeamMember({
  teamId: "team-id",
  memberId: "member-id",
});

// Remove from team
await authClient.organization.removeTeamMember({
  teamId: "team-id",
  memberId: "member-id",
});

// Set active team
await authClient.organization.setActiveTeam({
  teamId: "team-id",
});
```

## Access Control

Define custom permissions using `createAccessControl`:

```typescript
import { createAccessControl } from "better-auth/plugins/access";

const statement = {
  organization: ["update", "delete"],
  member: ["create", "update", "delete"],
  invitation: ["create", "cancel"],
  project: ["create", "read", "update", "delete", "share"],
} as const;

const ac = createAccessControl(statement);

const owner = ac.newRole({
  organization: ["update", "delete"],
  member: ["create", "update", "delete"],
  invitation: ["create", "cancel"],
  project: ["create", "read", "update", "delete", "share"],
});

const admin = ac.newRole({
  member: ["create", "update"],
  invitation: ["create", "cancel"],
  project: ["create", "read", "update", "delete"],
});

const member = ac.newRole({
  project: ["create", "read"],
});
```

Register with the plugin:

```typescript
// Server
organization({ ac, roles: { owner, admin, member } })

// Client
organizationClient({ ac, roles: { owner, admin, member } })
```

### Check Permissions

```typescript
const { data } = await authClient.organization.hasPermission({
  organizationId: "org-id",
  permissions: { project: ["delete"] },
});
```

## Dynamic Access Control

Enable runtime role creation per organization:

```typescript
organization({
  dynamicAccessControl: {
    enabled: true,
    maxRoles: 50, // Per organization
  },
})
```

### Create Custom Role

```typescript
await authClient.organization.createRole({
  organizationId: "org-id",
  role: {
    name: "reviewer",
    permissions: { project: ["read"] },
  },
});
```

### Update/Delete Roles

```typescript
await authClient.organization.updateRole({
  roleId: "role-id",
  permissions: { project: ["read", "update"] },
});

await authClient.organization.deleteRole({
  roleId: "role-id",
});
```

## Lifecycle Hooks

```typescript
organization({
  // Organization hooks
  beforeCreateOrganization: async (org) => { /* validate */ },
  afterCreateOrganization: async (org) => { /* side effects */ },
  beforeDeleteOrganization: async (org) => { /* check */ },
  afterDeleteOrganization: async (org) => { /* cleanup */ },

  // Member hooks
  beforeAddMember: async (member) => { /* validate */ },
  afterAddMember: async (member) => { /* notify */ },
  beforeRemoveMember: async (member) => { /* check */ },
  afterRemoveMember: async (member) => { /* cleanup */ },

  // Invitation hooks
  beforeCreateInvitation: async (inv) => { /* validate */ },
  afterCreateInvitation: async (inv) => { /* log */ },
  beforeAcceptInvitation: async (inv) => { /* check */ },
  afterAcceptInvitation: async (inv) => { /* welcome */ },

  // Team hooks
  beforeCreateTeam: async (team) => { /* validate */ },
  afterCreateTeam: async (team) => { /* notify */ },
})
```

Throwing errors in `before` hooks prevents the operation.

## Database Schema

| Table | Key Fields |
|-------|------------|
| `organization` | id, name, slug, logo, metadata, createdAt |
| `member` | id, organizationId, userId, role, createdAt |
| `invitation` | id, organizationId, email, role, status, expiresAt |
| `session` (extended) | activeOrganizationId, activeTeamId |
| `team` (optional) | id, name, organizationId, createdAt |
| `teamMember` (optional) | id, teamId, memberId |
| `organizationRole` (dynamic) | id, organizationId, name, permissions |

## Common Pitfalls

1. **Not setting active organization** — Many operations require an active org. Call `setActive` after selection.
2. **Missing invitation email handler** — Without `sendInvitationEmail`, invitations are created but no email is sent.
3. **Dynamic roles without enabling** — `createRole` fails unless `dynamicAccessControl.enabled` is true.
4. **Team member vs org member** — A team member must first be an org member. You can't add someone to a team who isn't in the organization.
5. **Owner role protection** — The last owner can't leave or be removed from an organization.
