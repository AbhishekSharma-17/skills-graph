# Admin Panel

> Source: https://payloadcms.com/docs/admin/overview

## Overview

Payload auto-generates a React-based admin panel built on Next.js. It provides list views, edit views, document management, media browsing, version diffing, and live preview — all customizable through component swapping and configuration.

The admin panel lives at `/admin` by default and is fully white-label ready.

## Admin Configuration

```typescript
// payload.config.ts
import { buildConfig } from 'payload'

export default buildConfig({
  admin: {
    user: 'users',                // Auth collection for admin login
    meta: {
      titleSuffix: '— My CMS',
      favicon: '/favicon.ico',
      ogImage: '/og-image.png',
    },
    avatar: 'gravatar',           // 'gravatar' | 'default' | Component
    dateFormat: 'MMM d, yyyy',
    components: {
      beforeDashboard: ['/components/DashboardBanner'],
      afterDashboard: ['/components/DashboardStats'],
      beforeLogin: ['/components/LoginBranding'],
      afterLogin: ['/components/LoginFooter'],
      logout: { Button: '/components/CustomLogoutButton' },
      graphics: {
        Logo: '/components/Logo',
        Icon: '/components/Icon',
      },
      Nav: '/components/CustomNav',
      views: {
        dashboard: {
          Component: '/components/CustomDashboard',
        },
      },
    },
    routes: {
      admin: '/admin',          // Admin panel base route
    },
  },
  // ...
})
```

## Custom Components

Payload uses a path-based component system. Components are referenced as string paths and resolved at build time:

```typescript
// /components/DashboardBanner.tsx
'use client'

import React from 'react'

const DashboardBanner: React.FC = () => {
  return (
    <div style={{ padding: '20px', background: '#f0f0f0', marginBottom: '20px' }}>
      <h2>Welcome to the Content Hub</h2>
      <p>Manage your website content from here.</p>
    </div>
  )
}

export default DashboardBanner
```

### Component Injection Points

| Location | Config Path | Purpose |
|----------|-------------|---------|
| Before dashboard | `admin.components.beforeDashboard` | Banners, announcements |
| After dashboard | `admin.components.afterDashboard` | Stats, quick actions |
| Before login | `admin.components.beforeLogin` | Branding above login form |
| After login | `admin.components.afterLogin` | Footer below login |
| Logo/Icon | `admin.components.graphics` | Branding in nav/login |
| Navigation | `admin.components.Nav` | Custom sidebar |
| Custom views | `admin.components.views` | Full page replacements |

### Collection-Level Components

```typescript
export const Posts: CollectionConfig = {
  slug: 'posts',
  admin: {
    components: {
      beforeList: ['/components/PostFilters'],
      afterList: ['/components/BulkActions'],
      beforeListTable: ['/components/ListBanner'],
      afterListTable: ['/components/ListFooter'],
      edit: {
        beforeFields: ['/components/PostPreview'],
        afterFields: ['/components/PostMetadata'],
      },
    },
  },
  fields: [/* ... */],
}
```

### Custom Field Components

```typescript
{
  name: 'color',
  type: 'text',
  admin: {
    components: {
      Field: '/components/ColorPicker',
      Cell: '/components/ColorCell',       // List view cell renderer
      Filter: '/components/ColorFilter',   // Custom filter in list view
    },
  },
}
```

## Admin Sidebar Groups

Organize collections in the sidebar:

```typescript
export const Posts: CollectionConfig = {
  slug: 'posts',
  admin: { group: 'Content' },
  // ...
}

export const Pages: CollectionConfig = {
  slug: 'pages',
  admin: { group: 'Content' },
  // ...
}

export const Users: CollectionConfig = {
  slug: 'users',
  admin: { group: 'Admin' },
  // ...
}
// Results in: Content > Posts, Pages | Admin > Users
```

## Live Preview

Render your frontend within the admin panel:

```typescript
// payload.config.ts
admin: {
  livePreview: {
    url: ({ data, collectionConfig, locale }) => {
      return `${process.env.FRONTEND_URL}/${data.slug}?preview=true`
    },
    collections: ['posts', 'pages'],
    globals: ['header', 'footer'],
    breakpoints: [
      { label: 'Mobile', name: 'mobile', width: 375, height: 667 },
      { label: 'Tablet', name: 'tablet', width: 768, height: 1024 },
      { label: 'Desktop', name: 'desktop', width: 1440, height: 900 },
    ],
  },
}
```

### Frontend Integration (Server-Side)

```typescript
// app/(frontend)/[slug]/page.tsx
import { draftMode } from 'next/headers'
import { getPayload } from 'payload'
import config from '@payload-config'
import { RefreshRouteOnSave } from './RefreshRouteOnSave'

export default async function Page({ params }) {
  const { isEnabled: isDraft } = await draftMode()
  const payload = await getPayload({ config })

  const page = await payload.find({
    collection: 'pages',
    where: { slug: { equals: params.slug } },
    draft: isDraft,
    limit: 1,
  })

  return (
    <>
      {isDraft && <RefreshRouteOnSave />}
      <PageContent data={page.docs[0]} />
    </>
  )
}
```

### Frontend Integration (Client-Side)

```typescript
'use client'
import { RefreshRouteOnSave as PayloadRefresh } from '@payloadcms/live-preview-react'
import { useRouter } from 'next/navigation'

export const RefreshRouteOnSave: React.FC = () => {
  const router = useRouter()
  return <PayloadRefresh refresh={router.refresh} serverURL={process.env.NEXT_PUBLIC_SERVER_URL!} />
}
```

## Admin Panel Theming

Customize the admin panel appearance via CSS:

```typescript
admin: {
  css: '/styles/admin.css',  // Custom CSS file path
}
```

```css
/* /styles/admin.css */
:root {
  --theme-elevation-0: #ffffff;
  --theme-elevation-50: #f7f7f7;
  --theme-elevation-100: #eeeeee;
  --color-base-0: #000000;
  --color-base-500: #666666;
  --color-base-1000: #ffffff;
  --font-body: 'Inter', sans-serif;
}
```

## Preview Button

Add a preview link on collection edit pages:

```typescript
export const Posts: CollectionConfig = {
  slug: 'posts',
  admin: {
    preview: (doc) => {
      if (doc?.slug) {
        return `${process.env.FRONTEND_URL}/posts/${doc.slug}`
      }
      return null
    },
  },
  fields: [/* ... */],
}
```

## Common Pitfalls

1. **Component paths must be strings** — Don't import components directly; use string paths like `'/components/MyComponent'`.
2. **Client vs server components** — Admin custom components that use hooks or interactivity need `'use client'` directive.
3. **Missing `admin.user`** — Without specifying which auth collection controls admin access, nobody can log in.
4. **Live preview CORS** — Your frontend must allow the admin panel origin for postMessage communication.
5. **Custom views must handle auth** — Custom admin views should check authentication themselves if they contain sensitive data.
