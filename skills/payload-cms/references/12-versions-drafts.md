# Versions and Drafts

> Source: https://payloadcms.com/docs/versions/overview

## Overview

Payload's versioning system stores the history of document changes over time. Built on top of versioning, the drafts system allows you to edit documents without publishing changes until you're ready.

When enabled, Payload:
- Creates a separate database table/collection for version history
- Adds version browsing, diffing, and restoring in the admin UI
- Replaces the Save button with Save Draft and Publish actions (when drafts are enabled)

## Enabling Versions

### On Collections

```typescript
export const Posts: CollectionConfig = {
  slug: 'posts',
  versions: {
    drafts: true,                    // Enable draft/publish workflow
    maxPerDoc: 25,                   // Max versions stored per document
  },
  fields: [/* ... */],
}
```

### On Globals

```typescript
export const SiteSettings: GlobalConfig = {
  slug: 'site-settings',
  versions: {
    drafts: true,
    max: 10,                         // Max versions for this global
  },
  fields: [/* ... */],
}
```

## Version Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `drafts` | `boolean \| object` | `false` | Enable draft/publish workflow |
| `drafts.autosave` | `boolean \| object` | `false` | Auto-save drafts as you type |
| `drafts.validate` | `boolean` | `false` | Validate fields on draft save |
| `maxPerDoc` | `number` | `100` | Max versions per document (collections) |
| `max` | `number` | `100` | Max versions (globals) |

## Drafts

When drafts are enabled:
- Documents have a `_status` field: `'draft'` or `'published'`
- The admin UI shows Save Draft and Publish buttons
- The API supports `draft: true` to fetch draft content
- Access control can differentiate between drafts and published content

### Draft Configuration

```typescript
versions: {
  drafts: {
    autosave: {
      interval: 2000,              // Auto-save every 2 seconds (ms)
    },
    validate: false,               // Don't require all fields for drafts
  },
}
```

## Querying Versions

### Fetch Published (Default)

```typescript
// Local API — returns published version by default
const posts = await payload.find({
  collection: 'posts',
})
```

### Fetch Drafts

```typescript
// Local API — include draft content
const drafts = await payload.find({
  collection: 'posts',
  draft: true,                    // Fetch latest draft version
})

// REST API
// GET /api/posts?draft=true

// GraphQL
// query { Posts(draft: true) { docs { title _status } } }
```

### Fetch Version History

```typescript
// Get all versions of a document
const versions = await payload.findVersions({
  collection: 'posts',
  where: {
    parent: { equals: documentId },
  },
  sort: '-updatedAt',
  limit: 10,
})

// Get a specific version
const version = await payload.findVersionByID({
  collection: 'posts',
  id: versionId,
})
```

### Restore a Version

```typescript
// Restore a previous version
const restored = await payload.restoreVersion({
  collection: 'posts',
  id: versionId,
})
```

## Version Data Structure

Each version document contains:

```typescript
{
  id: 'version-id',
  parent: 'original-document-id',
  version: {
    // Full snapshot of the document at that point
    title: 'My Post',
    content: { /* rich text */ },
    status: 'published',
    // ... all other fields
  },
  createdAt: '2024-01-15T10:30:00.000Z',
  updatedAt: '2024-01-15T10:30:00.000Z',
}
```

## Admin UI Features

When versions are enabled, the admin panel adds:

1. **Version History** — Browse all versions with timestamps and users
2. **Diff View** — Compare any two versions side by side, showing field-level changes
3. **Restore** — One-click restore to any previous version
4. **Autosave Indicator** — Shows when auto-save is active and last save time
5. **Publish/Unpublish** — Toggle between draft and published states

## Access Control with Drafts

Control who can read drafts vs published content:

```typescript
access: {
  read: ({ req }) => {
    // Admins and editors see everything including drafts
    if (req.user?.role === 'admin' || req.user?.role === 'editor') {
      return true
    }
    // Public only sees published content
    return {
      _status: { equals: 'published' },
    }
  },
}
```

## Publishing Workflow Pattern

```typescript
export const Posts: CollectionConfig = {
  slug: 'posts',
  versions: { drafts: true },
  hooks: {
    afterChange: [
      async ({ doc, previousDoc, operation, req }) => {
        // Detect publish event
        const wasJustPublished =
          doc._status === 'published' &&
          previousDoc?._status === 'draft'

        if (wasJustPublished) {
          // Trigger revalidation, send notifications, etc.
          await fetch(`${process.env.FRONTEND_URL}/api/revalidate`, {
            method: 'POST',
            body: JSON.stringify({ slug: doc.slug }),
          })
        }
      },
    ],
  },
  fields: [
    {
      name: 'publishedDate',
      type: 'date',
      admin: { position: 'sidebar' },
      hooks: {
        beforeChange: [
          ({ data, siblingData }) => {
            if (siblingData._status === 'published' && !data) {
              return new Date().toISOString()
            }
            return data
          },
        ],
      },
    },
  ],
}
```

## Preview with Drafts

Combine drafts with Next.js draft mode for preview:

```typescript
// app/api/preview/route.ts
import { draftMode } from 'next/headers'
import { redirect } from 'next/navigation'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const slug = searchParams.get('slug')
  const secret = searchParams.get('secret')

  if (secret !== process.env.PREVIEW_SECRET) {
    return new Response('Invalid token', { status: 401 })
  }

  const draft = await draftMode()
  draft.enable()
  redirect(`/posts/${slug}`)
}
```

```typescript
// app/(frontend)/posts/[slug]/page.tsx
import { draftMode } from 'next/headers'

export default async function PostPage({ params }) {
  const { isEnabled: isDraft } = await draftMode()

  const post = await payload.find({
    collection: 'posts',
    where: { slug: { equals: params.slug } },
    draft: isDraft,      // Fetch draft version in preview mode
    limit: 1,
  })

  return <PostContent data={post.docs[0]} />
}
```

## Common Pitfalls

1. **Database size** — Versions accumulate quickly. Set `maxPerDoc` to a reasonable number (10-50) to prevent unbounded growth.
2. **Draft validation** — By default, drafts don't validate required fields. Set `drafts.validate: true` if you want strict validation on drafts.
3. **Autosave frequency** — Too-frequent autosave creates many version records. Use 2000-5000ms intervals.
4. **`_status` in queries** — Don't forget to filter by `_status: 'published'` in public-facing queries, or use access control to enforce it.
5. **Version restoration and hooks** — Restoring a version triggers `beforeChange` and `afterChange` hooks. Ensure your hooks handle restoration gracefully.
6. **Postgres migrations for versions** — Enabling versions on an existing collection requires a migration to create the versions table.
