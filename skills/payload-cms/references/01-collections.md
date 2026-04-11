# Collections

> Source: https://payloadcms.com/docs/configuration/collections

## Overview

A Collection is a group of documents (records) that share a common schema. Each collection you define automatically generates:
- A database table/collection
- REST API endpoints (`/api/<slug>`)
- GraphQL queries and mutations
- Admin panel list and edit views
- A Local API interface

## Collection Config

```typescript
import type { CollectionConfig } from 'payload'

export const Posts: CollectionConfig = {
  slug: 'posts',                    // URL-safe identifier (required)
  labels: {                         // Admin UI labels
    singular: 'Post',
    plural: 'Posts',
  },
  admin: {
    useAsTitle: 'title',            // Field used as document title in admin
    defaultColumns: ['title', 'status', 'createdAt'],
    group: 'Content',               // Group in sidebar navigation
    description: 'Blog posts and articles',
    listSearchableFields: ['title', 'slug'],
    pagination: {
      defaultLimit: 20,
      limits: [10, 20, 50],
    },
    preview: (doc) => `https://mysite.com/posts/${doc.slug}`,
  },
  fields: [
    // ... field definitions (see 02-fields.md)
  ],
  access: {
    // ... access control (see 04-access-control.md)
  },
  hooks: {
    // ... lifecycle hooks (see 05-hooks.md)
  },
  timestamps: true,                 // Adds createdAt and updatedAt (default: true)
}
```

## Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `slug` | `string` | URL-safe identifier, used in API routes and database |
| `fields` | `Field[]` | Array of field definitions for the document schema |

## Key Optional Properties

| Property | Type | Description |
|----------|------|-------------|
| `labels` | `{ singular, plural }` | Display names in admin UI |
| `admin` | `object` | Admin panel configuration |
| `access` | `object` | Access control functions |
| `hooks` | `object` | Lifecycle hook functions |
| `auth` | `boolean \| object` | Enable authentication on this collection |
| `upload` | `boolean \| object` | Enable file uploads on this collection |
| `versions` | `boolean \| object` | Enable version history |
| `timestamps` | `boolean` | Add `createdAt`/`updatedAt` fields (default: `true`) |
| `defaultSort` | `string` | Default sort field (prefix with `-` for descending) |
| `defaultPopulate` | `object` | Fields to populate by default on queries |
| `endpoints` | `Endpoint[]` | Custom REST endpoints |
| `graphQL` | `object \| false` | GraphQL configuration or disable |

## Auth-Enabled Collections

Adding `auth: true` transforms a collection into an authentication-enabled collection with login, logout, token refresh, and password management:

```typescript
export const Users: CollectionConfig = {
  slug: 'users',
  auth: {
    tokenExpiration: 7200,          // 2 hours in seconds
    maxLoginAttempts: 5,
    lockTime: 600000,               // Lock for 10 minutes after max attempts
    useAPIKey: true,                // Enable API key auth
    depth: 0,                       // Depth for populating user on requests
    cookies: {
      secure: true,
      sameSite: 'lax',
      domain: '.mysite.com',
    },
  },
  fields: [
    { name: 'name', type: 'text', required: true },
    {
      name: 'role',
      type: 'select',
      options: ['admin', 'editor', 'viewer'],
      defaultValue: 'viewer',
      required: true,
    },
  ],
}
```

## Upload-Enabled Collections

Adding `upload` transforms a collection into a file management system:

```typescript
export const Media: CollectionConfig = {
  slug: 'media',
  upload: {
    staticDir: 'media',
    mimeTypes: ['image/*', 'application/pdf'],
    imageSizes: [
      { name: 'thumbnail', width: 300, height: 300, position: 'centre' },
      { name: 'card', width: 768, height: 1024, position: 'centre' },
      { name: 'hero', width: 1920, height: undefined },  // Maintain ratio
    ],
    adminThumbnail: 'thumbnail',
    focalPoint: true,               // Enable focal point selection
    crop: true,                     // Enable image cropping in admin
  },
  fields: [
    { name: 'alt', type: 'text', required: true },
    { name: 'caption', type: 'textarea' },
  ],
}
```

## Custom Endpoints

Add custom REST endpoints to any collection:

```typescript
export const Posts: CollectionConfig = {
  slug: 'posts',
  endpoints: [
    {
      path: '/slug/:slug',
      method: 'get',
      handler: async (req) => {
        const { slug } = req.routeParams
        const result = await req.payload.find({
          collection: 'posts',
          where: { slug: { equals: slug } },
          limit: 1,
        })
        if (result.docs.length === 0) {
          return Response.json({ error: 'Not found' }, { status: 404 })
        }
        return Response.json(result.docs[0])
      },
    },
  ],
  fields: [/* ... */],
}
```

## Admin Configuration

```typescript
admin: {
  useAsTitle: 'title',               // Field displayed as document title
  defaultColumns: ['title', 'status', 'author', 'createdAt'],
  group: 'Content',                  // Sidebar group name
  description: 'Manage blog posts',
  hidden: false,                     // Hide from admin nav
  listSearchableFields: ['title', 'slug', 'excerpt'],
  pagination: {
    defaultLimit: 25,
    limits: [10, 25, 50, 100],
  },
  components: {
    beforeList: ['/components/PostStats'],  // Custom components
    afterList: ['/components/PostActions'],
    edit: {
      beforeFields: ['/components/PostPreview'],
    },
  },
  preview: (doc, { locale }) => {
    if (doc?.slug) {
      return `https://mysite.com/${locale}/posts/${doc.slug}`
    }
    return null
  },
}
```

## TypeScript Types

Payload auto-generates types for each collection:

```typescript
// Generated in payload-types.ts
export interface Post {
  id: string
  title: string
  slug: string
  content: any       // Rich text content
  status: 'draft' | 'published'
  author: string | User
  createdAt: string
  updatedAt: string
}
```

## Common Patterns

### Slug Generation with Hooks

```typescript
import { CollectionConfig } from 'payload'
import { formatSlug } from '../utilities/formatSlug'

export const Posts: CollectionConfig = {
  slug: 'posts',
  hooks: {
    beforeValidate: [
      ({ data, operation }) => {
        if (operation === 'create' || operation === 'update') {
          if (data?.title) {
            data.slug = formatSlug(data.title)
          }
        }
        return data
      },
    ],
  },
  fields: [
    { name: 'title', type: 'text', required: true },
    { name: 'slug', type: 'text', unique: true, admin: { position: 'sidebar' } },
  ],
}
```

### Published Content Filter

```typescript
export const Posts: CollectionConfig = {
  slug: 'posts',
  access: {
    read: ({ req }) => {
      if (req.user) return true  // Logged-in users see everything
      return { status: { equals: 'published' } }  // Public sees published only
    },
  },
  fields: [
    {
      name: 'status',
      type: 'select',
      options: [
        { label: 'Draft', value: 'draft' },
        { label: 'Published', value: 'published' },
      ],
      defaultValue: 'draft',
      required: true,
    },
  ],
}
```

## Common Pitfalls

1. **Slug conflicts** — Collection slugs must be unique across all collections and globals. Use descriptive, URL-safe slugs.
2. **Missing `useAsTitle`** — Without it, the admin panel shows document IDs instead of meaningful titles.
3. **Upload `staticDir` permissions** — Ensure the directory exists and is writable in production.
4. **Auth collection without admin access** — At least one auth-enabled collection should have admin panel access, or you'll be locked out.
5. **Too many `defaultColumns`** — Keep it to 4-6 columns for readability in the admin list view.
