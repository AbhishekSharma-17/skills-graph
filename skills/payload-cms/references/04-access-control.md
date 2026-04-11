# Access Control

> Source: https://payloadcms.com/docs/access-control/overview

## Table of Contents

- [Overview](#overview)
- [Collection Access Control](#collection-access-control)
- [Global Access Control](#global-access-control)
- [Field-Level Access Control](#field-level-access-control)
- [Return Types](#return-types)
- [RBAC Patterns](#rbac-patterns)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Payload uses function-based access control. Access functions receive the request context and return either:
- `true` — allow full access
- `false` — deny access completely
- A **query constraint** (Where clause) — allow access to documents matching the filter

This model is powerful because the same function handles both admin panel visibility and API access.

## Collection Access Control

```typescript
import type { CollectionConfig, Access } from 'payload'

const isAdmin: Access = ({ req }) => {
  return req.user?.role === 'admin'
}

const isAdminOrSelf: Access = ({ req }) => {
  if (req.user?.role === 'admin') return true
  return { id: { equals: req.user?.id } }  // Query constraint
}

export const Users: CollectionConfig = {
  slug: 'users',
  access: {
    create: isAdmin,             // Who can create documents
    read: isAdminOrSelf,         // Who can read documents
    update: isAdminOrSelf,       // Who can update documents
    delete: isAdmin,             // Who can delete documents
    admin: ({ req }) => {        // Who can access admin panel for this collection
      return ['admin', 'editor'].includes(req.user?.role)
    },
  },
  auth: true,
  fields: [/* ... */],
}
```

### Access Function Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `req` | `PayloadRequest` | The request object with `user`, `payload`, `locale` |
| `id` | `string` | Document ID (for `read`, `update`, `delete`) |
| `data` | `object` | Incoming data (for `create`, `update`) |

## Global Access Control

Globals only have `read` and `update` operations (no create/delete since they are singletons):

```typescript
export const SiteSettings: GlobalConfig = {
  slug: 'site-settings',
  access: {
    read: () => true,                                    // Public readable
    update: ({ req }) => req.user?.role === 'admin',     // Only admins can modify
  },
  fields: [/* ... */],
}
```

## Field-Level Access Control

Control access to individual fields:

```typescript
{
  name: 'internalNotes',
  type: 'textarea',
  access: {
    read: ({ req }) => {
      return Boolean(req.user)  // Only logged-in users
    },
    create: ({ req }) => {
      return req.user?.role === 'admin'
    },
    update: ({ req }) => {
      return req.user?.role === 'admin'
    },
  },
}
```

When field access returns `false`:
- **Read**: Field is stripped from API responses
- **Create/Update**: Incoming values are silently discarded

## Return Types

### Boolean Return

```typescript
// Simple allow/deny
const isLoggedIn: Access = ({ req }) => Boolean(req.user)
const isAdmin: Access = ({ req }) => req.user?.role === 'admin'
```

### Query Constraint Return

Returns a `Where` clause that filters documents. This is the most powerful pattern — it allows partial access based on document properties:

```typescript
// Users can only read their own orders
const ownOrders: Access = ({ req }) => {
  if (!req.user) return false
  return {
    customer: { equals: req.user.id },
  }
}

// Editors can read published posts, admins can read all
const readAccess: Access = ({ req }) => {
  if (req.user?.role === 'admin') return true
  if (req.user?.role === 'editor') {
    return {
      or: [
        { status: { equals: 'published' } },
        { author: { equals: req.user.id } },
      ],
    }
  }
  return { status: { equals: 'published' } }
}
```

## RBAC Patterns

### Simple Role Check

```typescript
// access/isRole.ts
import type { Access } from 'payload'

export const isRole = (role: string): Access => ({ req }) => {
  return req.user?.role === role
}

export const hasRole = (...roles: string[]): Access => ({ req }) => {
  return roles.includes(req.user?.role)
}

// Usage
access: {
  create: hasRole('admin', 'editor'),
  read: () => true,
  update: hasRole('admin', 'editor'),
  delete: isRole('admin'),
}
```

### Multi-Tenant Access

```typescript
const tenantAccess: Access = ({ req }) => {
  if (req.user?.role === 'super-admin') return true
  if (!req.user?.tenant) return false
  return {
    tenant: { equals: req.user.tenant },
  }
}
```

### Owner-Based Access

```typescript
const isOwnerOrAdmin: Access = ({ req }) => {
  if (!req.user) return false
  if (req.user.role === 'admin') return true
  return {
    createdBy: { equals: req.user.id },
  }
}
```

## Common Patterns

### Public Read, Auth Write

```typescript
access: {
  create: ({ req }) => Boolean(req.user),
  read: () => true,
  update: ({ req }) => Boolean(req.user),
  delete: ({ req }) => req.user?.role === 'admin',
}
```

### Combining Multiple Conditions

```typescript
const complexAccess: Access = ({ req }) => {
  if (!req.user) return false
  if (req.user.role === 'admin') return true

  return {
    and: [
      { status: { equals: 'published' } },
      {
        or: [
          { author: { equals: req.user.id } },
          { editors: { contains: req.user.id } },
        ],
      },
    ],
  }
}
```

## Common Pitfalls

1. **Forgetting `req.user` can be `undefined`** — Always null-check before accessing user properties.
2. **Access functions must be synchronous or async** — Both work, but async functions should be fast to avoid slowing down every request.
3. **Query constraints must use valid operators** — `equals`, `not_equals`, `contains`, `in`, `not_in`, `greater_than`, `less_than`, etc.
4. **Field access doesn't affect admin panel visibility by default** — Use `admin.condition` for UI visibility, `access` for data-level security.
5. **No access defined = no access** — Collections without explicit access functions default to requiring authentication.
6. **`overrideAccess` in Local API** — By default, the Local API bypasses access control. Set `overrideAccess: false` when querying on behalf of a user.
