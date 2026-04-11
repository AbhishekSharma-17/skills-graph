# Globals

> Source: https://payloadcms.com/docs/configuration/globals

## Overview

Globals are singleton documents — each global has exactly one document. They are used for site-wide content that doesn't belong in a collection, such as navigation menus, site settings, footer content, or localized strings.

Like collections, globals automatically generate Local API, REST API, and GraphQL interfaces.

## Global Config

```typescript
import type { GlobalConfig } from 'payload'

export const SiteSettings: GlobalConfig = {
  slug: 'site-settings',
  label: 'Site Settings',
  access: {
    read: () => true,
    update: ({ req }) => req.user?.role === 'admin',
  },
  fields: [
    { name: 'siteName', type: 'text', required: true },
    { name: 'siteDescription', type: 'textarea' },
    {
      name: 'logo',
      type: 'upload',
      relationTo: 'media',
    },
    {
      name: 'socialLinks',
      type: 'array',
      fields: [
        { name: 'platform', type: 'select', options: ['twitter', 'github', 'linkedin'] },
        { name: 'url', type: 'text', required: true },
      ],
    },
  ],
}
```

## Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `slug` | `string` | Unique identifier for the global |
| `fields` | `Field[]` | Array of field definitions |

## Key Optional Properties

| Property | Type | Description |
|----------|------|-------------|
| `label` | `string` | Display name in admin panel |
| `access` | `object` | Access control functions (`read`, `update`) |
| `hooks` | `object` | Lifecycle hooks (`beforeValidate`, `beforeChange`, `afterChange`, `beforeRead`, `afterRead`) |
| `admin` | `object` | Admin panel configuration |
| `versions` | `boolean \| object` | Enable version history |
| `graphQL` | `object \| false` | GraphQL config or disable |
| `endpoints` | `Endpoint[]` | Custom REST endpoints |
| `typescript` | `object` | Type generation config |

## Querying Globals

```typescript
// Local API
const settings = await payload.findGlobal({ slug: 'site-settings' })

// Update
await payload.updateGlobal({
  slug: 'site-settings',
  data: { siteName: 'My New Site Name' },
})

// REST API
// GET  /api/globals/site-settings
// POST /api/globals/site-settings

// GraphQL
// query { SiteSetting { siteName siteDescription } }
```

## Common Global Examples

### Header Navigation

```typescript
export const Header: GlobalConfig = {
  slug: 'header',
  fields: [
    {
      name: 'navItems',
      type: 'array',
      maxRows: 8,
      fields: [
        { name: 'label', type: 'text', required: true },
        {
          name: 'link',
          type: 'group',
          fields: [
            {
              name: 'type',
              type: 'radio',
              options: [
                { label: 'Page', value: 'page' },
                { label: 'URL', value: 'url' },
              ],
              defaultValue: 'page',
            },
            {
              name: 'page',
              type: 'relationship',
              relationTo: 'pages',
              admin: { condition: (_, siblingData) => siblingData?.type === 'page' },
            },
            {
              name: 'url',
              type: 'text',
              admin: { condition: (_, siblingData) => siblingData?.type === 'url' },
            },
          ],
        },
      ],
    },
  ],
}
```

### Footer

```typescript
export const Footer: GlobalConfig = {
  slug: 'footer',
  fields: [
    {
      name: 'columns',
      type: 'array',
      maxRows: 4,
      fields: [
        { name: 'heading', type: 'text', required: true },
        {
          name: 'links',
          type: 'array',
          fields: [
            { name: 'label', type: 'text', required: true },
            { name: 'url', type: 'text', required: true },
            { name: 'newTab', type: 'checkbox' },
          ],
        },
      ],
    },
    { name: 'copyright', type: 'text' },
  ],
}
```

## Globals vs Collections

| Aspect | Globals | Collections |
|--------|---------|-------------|
| Documents | Exactly 1 | Many |
| List view | No | Yes |
| Create/Delete | No (always exists) | Yes |
| API operations | Read, Update | Create, Read, Update, Delete |
| Use case | Site settings, nav, banners | Posts, users, products |

## Using in Next.js Pages

```typescript
// app/(frontend)/layout.tsx
import { getPayload } from 'payload'
import config from '@payload-config'

export default async function RootLayout({ children }) {
  const payload = await getPayload({ config })

  const header = await payload.findGlobal({ slug: 'header' })
  const footer = await payload.findGlobal({ slug: 'footer' })

  return (
    <html>
      <body>
        <Header data={header} />
        {children}
        <Footer data={footer} />
      </body>
    </html>
  )
}
```

## Common Pitfalls

1. **Slug collisions** — Global slugs must not conflict with collection slugs.
2. **No `read` access defined** — Globals are inaccessible via API without explicit `read` access.
3. **Using globals for lists** — If you need multiple instances, use a collection instead.
4. **Heavy globals** — Don't put large amounts of data in globals. Use collections with relationships instead.
