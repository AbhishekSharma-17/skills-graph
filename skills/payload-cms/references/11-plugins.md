# Plugins

> Source: https://payloadcms.com/docs/plugins/overview

## Overview

Payload plugins extend core functionality by modifying the Payload config. A plugin is a function that receives the config and returns a modified config. Official plugins are published under the `@payloadcms` npm namespace.

```typescript
import { buildConfig } from 'payload'
import { seoPlugin } from '@payloadcms/plugin-seo'
import { formBuilderPlugin } from '@payloadcms/plugin-form-builder'

export default buildConfig({
  plugins: [
    seoPlugin({ collections: ['posts', 'pages'] }),
    formBuilderPlugin({ fields: { text: true, email: true, select: true } }),
  ],
  // ...
})
```

## Official Plugins

### SEO Plugin

Injects SEO metadata fields (title, description, image) into collections and globals:

```bash
npm install @payloadcms/plugin-seo
```

```typescript
import { seoPlugin } from '@payloadcms/plugin-seo'

seoPlugin({
  collections: ['posts', 'pages'],
  globals: ['site-settings'],
  uploadsCollection: 'media',
  tabbedUI: true,                  // Show SEO fields in a separate tab
  generateTitle: ({ doc }) => `${doc.title} — My Site`,
  generateDescription: ({ doc }) => doc.excerpt || '',
  generateURL: ({ doc, collectionConfig }) => {
    return `https://mysite.com/${collectionConfig.slug}/${doc.slug}`
  },
})
```

Injected fields:
- `meta.title` — SEO title with character count
- `meta.description` — Meta description with character count
- `meta.image` — Open Graph image (relationship to upload collection)

### Form Builder Plugin

Creates a forms collection with dynamic field configuration:

```bash
npm install @payloadcms/plugin-form-builder
```

```typescript
import { formBuilderPlugin } from '@payloadcms/plugin-form-builder'

formBuilderPlugin({
  fields: {
    text: true,
    email: true,
    textarea: true,
    select: true,
    checkbox: true,
    number: true,
    message: true,
    country: true,
    state: true,
    payment: false,
  },
  formOverrides: {
    admin: { group: 'Forms' },
  },
  formSubmissionOverrides: {
    admin: { group: 'Forms' },
  },
  redirectRelationships: ['pages', 'posts'],
})
```

Creates two collections:
- `forms` — Form definitions with fields, confirmation settings, emails
- `form-submissions` — Submitted form data

### Search Plugin

Creates a unified search index across collections:

```bash
npm install @payloadcms/plugin-search
```

```typescript
import { searchPlugin } from '@payloadcms/plugin-search'

searchPlugin({
  collections: ['posts', 'pages', 'products'],
  defaultPriorities: {
    posts: 20,
    pages: 10,
    products: 30,
  },
  beforeSync: ({ originalDoc, searchDoc }) => {
    return {
      ...searchDoc,
      excerpt: originalDoc.excerpt || '',
    }
  },
  searchOverrides: {
    admin: { group: 'Search' },
  },
})
```

### Cloud Storage Plugin

Store uploads in cloud providers instead of local filesystem:

```bash
npm install @payloadcms/plugin-cloud-storage
```

```typescript
import { cloudStoragePlugin } from '@payloadcms/plugin-cloud-storage'
import { s3Adapter } from '@payloadcms/plugin-cloud-storage/s3'

cloudStoragePlugin({
  collections: {
    media: {
      adapter: s3Adapter({
        bucket: process.env.S3_BUCKET!,
        config: {
          credentials: {
            accessKeyId: process.env.S3_ACCESS_KEY!,
            secretAccessKey: process.env.S3_SECRET_KEY!,
          },
          region: process.env.S3_REGION!,
        },
      }),
      disableLocalStorage: true,
      generateFileURL: ({ filename }) => {
        return `https://${process.env.S3_BUCKET}.s3.amazonaws.com/${filename}`
      },
    },
  },
})
```

Available adapters:
- `s3Adapter` — Amazon S3 and S3-compatible (MinIO, DigitalOcean Spaces, Cloudflare R2)
- `gcsAdapter` — Google Cloud Storage
- `azureBlobStorageAdapter` — Azure Blob Storage

### Nested Docs Plugin

Enables hierarchical parent-child relationships with breadcrumb generation:

```bash
npm install @payloadcms/plugin-nested-docs
```

```typescript
import { nestedDocsPlugin } from '@payloadcms/plugin-nested-docs'

nestedDocsPlugin({
  collections: ['pages', 'categories'],
  generateLabel: (_, doc) => doc.title,
  generateURL: (docs) => docs.reduce((url, doc) => `${url}/${doc.slug}`, ''),
  breadcrumbsFieldSlug: 'breadcrumbs',
  parentFieldSlug: 'parent',
})
```

Adds to each document:
- `parent` — Relationship to parent document
- `breadcrumbs` — Array of `{ label, url, doc }` for the full hierarchy

### Redirects Plugin

Manage URL redirects:

```bash
npm install @payloadcms/plugin-redirects
```

```typescript
import { redirectsPlugin } from '@payloadcms/plugin-redirects'

redirectsPlugin({
  collections: ['pages', 'posts'],
  overrides: {
    admin: { group: 'SEO' },
  },
})
```

## Building Custom Plugins

A plugin is a function that takes the existing config and returns a modified one:

```typescript
import type { Plugin } from 'payload'

export const myPlugin: Plugin = (incomingConfig) => {
  // Add a new collection
  const config = {
    ...incomingConfig,
    collections: [
      ...(incomingConfig.collections || []),
      {
        slug: 'audit-logs',
        fields: [
          { name: 'action', type: 'text' },
          { name: 'user', type: 'relationship', relationTo: 'users' },
          { name: 'timestamp', type: 'date' },
          { name: 'details', type: 'json' },
        ],
        admin: { group: 'System' },
      },
    ],
  }

  // Add hooks to existing collections
  config.collections = config.collections.map((collection) => ({
    ...collection,
    hooks: {
      ...collection.hooks,
      afterChange: [
        ...(collection.hooks?.afterChange || []),
        async ({ doc, req, operation, collection: col }) => {
          await req.payload.create({
            collection: 'audit-logs',
            data: {
              action: `${col.slug}.${operation}`,
              user: req.user?.id,
              timestamp: new Date().toISOString(),
              details: { docId: doc.id },
            },
          })
        },
      ],
    },
  }))

  return config
}
```

## Common Pitfalls

1. **Plugin order matters** — Plugins execute in order. If one plugin depends on collections created by another, order them accordingly.
2. **SEO plugin without upload collection** — The `uploadsCollection` must reference an existing upload-enabled collection.
3. **Cloud storage in development** — Use `disableLocalStorage: false` in dev to keep local file serving working.
4. **Nested docs depth** — Deep hierarchies (>5 levels) can cause slow breadcrumb generation. Limit nesting depth.
5. **Form builder field types** — Only explicitly enabled field types are available in the form builder admin.
