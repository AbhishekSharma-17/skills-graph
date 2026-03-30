# Better Auth — Admin & Authorization

> Source: [better-auth.com/docs/plugins/admin](https://www.better-auth.com/docs/plugins/admin) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [User Management](#user-management)
- [Role Management](#role-management)
- [Custom Roles & Permissions](#custom-roles--permissions)
- [Permission Checking](#permission-checking)
- [User Banning](#user-banning)
- [Session Management](#session-management)
- [User Impersonation](#user-impersonation)
- [User Removal](#user-removal)
- [Configuration Options](#configuration-options)
- [Common Pitfalls](#common-pitfalls)

## Overview

The Admin plugin provides administrative user management, role-based access control (RBAC), banning, and impersonation. It adds a `role` field to the user table and provides admin-only API endpoints.

## Setup

### Server

```typescript
import { betterAuth } from "better-auth";
import { admin } from "better-auth/plugins";

export const auth = betterAuth({
  plugins: [admin()],
});
```

### Client

```typescript
import { createAuthClient } from "better-auth/react";
import { adminClient } from "better-auth/client/plugins";

const authClient = createAuthClient({
  plugins: [adminClient()],
});
```

Run migrations: `npx auth migrate`

### Database Changes

Adds to user table: `role` (string), `banned` (boolean), `banReason` (string), `banExpires` (date).
Adds to session table: `impersonatedBy` (string).

## User Management

### Create User

```typescript
const { data, error } = await authClient.admin.createUser({
  email: "user@example.com",
  password: "secure-password",
  name: "James Smith",
  role: "user",
  data: { customField: "value" }, // Additional fields
});
```

### List Users

```typescript
const { data, error } = await authClient.admin.listUsers({
  query: {
    searchValue: "john",
    searchField: "name",         // "name", "email", etc.
    searchOperator: "contains",  // "contains", "starts_with", "ends_with"
    limit: 100,
    offset: 0,
    sortBy: "name",
    sortDirection: "asc",        // "asc" or "desc"
  },
});
// data = { users: [...], total: 150, limit: 100, offset: 0 }
```

### Get User

```typescript
const { data } = await authClient.admin.getUser({
  query: { id: "user-id" },
});
```

### Update User

```typescript
await authClient.admin.updateUser({
  userId: "user-id",
  data: { name: "John Doe", customField: "newValue" },
});
```

### Set Password

```typescript
await authClient.admin.setUserPassword({
  userId: "user-id",
  newPassword: "new-password",
});
```

## Role Management

### Default Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full control over users and settings |
| `user` | Standard user, no admin access |

Users can hold multiple roles (stored as comma-separated string).

### Set User Role

```typescript
await authClient.admin.setRole({
  userId: "user-id",
  role: "admin", // string or string[]
});
```

## Custom Roles & Permissions

Define fine-grained permissions with `createAccessControl`:

```typescript
import { createAccessControl } from "better-auth/plugins/access";

// Define resource-action matrix
const statement = {
  project: ["create", "read", "update", "delete", "share"],
  user: ["create", "list", "ban", "impersonate"],
  billing: ["read", "update"],
} as const;

const ac = createAccessControl(statement);

// Create roles with specific permissions
export const userRole = ac.newRole({
  project: ["create", "read"],
});

export const adminRole = ac.newRole({
  project: ["create", "read", "update", "delete"],
  user: ["create", "list", "ban"],
  billing: ["read", "update"],
});

export const superAdminRole = ac.newRole({
  project: ["create", "read", "update", "delete", "share"],
  user: ["create", "list", "ban", "impersonate"],
  billing: ["read", "update"],
});
```

### Register Custom Roles

```typescript
// Server
export const auth = betterAuth({
  plugins: [
    admin({
      ac,
      roles: {
        user: userRole,
        admin: adminRole,
        superAdmin: superAdminRole,
      },
    }),
  ],
});

// Client
const authClient = createAuthClient({
  plugins: [
    adminClient({
      ac,
      roles: {
        user: userRole,
        admin: adminRole,
        superAdmin: superAdminRole,
      },
    }),
  ],
});
```

## Permission Checking

### Runtime Permission Check

```typescript
const { data: hasPermission } = await authClient.admin.hasPermission({
  permissions: {
    project: ["create", "update"],
  },
});
// hasPermission = { success: true } or { success: false }
```

### Static Role Permission Check

```typescript
const canDelete = authClient.admin.checkRolePermission({
  permissions: { project: ["delete"] },
  role: "admin",
});
// Returns boolean
```

### Server-Side Check

```typescript
const session = await auth.api.getSession({ headers });
const hasPermission = await auth.api.userHasPermission({
  body: {
    userId: session.user.id,
    permissions: { project: ["delete"] },
  },
});
```

## User Banning

### Ban User

```typescript
await authClient.admin.banUser({
  userId: "user-id",
  banReason: "Violation of terms",
  banExpiresIn: 60 * 60 * 24 * 7, // 7 days (optional)
});
```

Without `banExpiresIn`, the ban is permanent.

### Unban User

```typescript
await authClient.admin.unbanUser({
  userId: "user-id",
});
```

Banning revokes all active sessions immediately.

## Session Management

### List User Sessions

```typescript
const { data } = await authClient.admin.listUserSessions({
  userId: "user-id",
});
```

### Revoke Sessions

```typescript
// Revoke specific session
await authClient.admin.revokeUserSession({
  sessionToken: "session_token",
});

// Revoke all user sessions
await authClient.admin.revokeUserSessions({
  userId: "user-id",
});
```

## User Impersonation

Admins can impersonate users to debug issues:

```typescript
// Start impersonation (creates a new session as the target user)
const { data } = await authClient.admin.impersonateUser({
  userId: "target-user-id",
});
// Default duration: 1 hour

// Stop impersonation (returns to admin session)
await authClient.admin.stopImpersonating();
```

By default, admins cannot impersonate other admins. Override with the `impersonate-admins` permission:

```typescript
const superAdmin = ac.newRole({
  ...adminRole.statements,
  user: ["impersonate-admins", ...adminRole.statements.user],
});
```

## User Removal

Permanently delete a user:

```typescript
const { data } = await authClient.admin.removeUser({
  userId: "user-id",
});
```

## Configuration Options

```typescript
admin({
  defaultRole: "user",                    // Role for new users
  adminRoles: ["admin"],                  // Roles with admin access
  adminUserIds: ["user-1", "user-2"],     // Users always treated as admin
  impersonationSessionDuration: 60 * 60,  // 1 hour (seconds)
  defaultBanReason: "No reason provided",
  defaultBanExpiresIn: undefined,         // Permanent by default
  bannedUserMessage: "Your account has been suspended",
})
```

## Common Pitfalls

1. **Not running migrations** — The admin plugin adds columns to the user and session tables. Always run `npx auth migrate`.
2. **Missing access control on client** — Pass the same `ac` and `roles` to both server and client plugins for type-safe permission checks.
3. **Impersonation leaks** — Impersonated sessions have `impersonatedBy` set. Always check this field in security-sensitive operations.
4. **adminRoles vs adminUserIds** — `adminRoles` checks the `role` field. `adminUserIds` bypasses role checks for specific users.
5. **Ban expiry** — Without `banExpiresIn`, bans are permanent. Always provide an expiry for temporary bans.
