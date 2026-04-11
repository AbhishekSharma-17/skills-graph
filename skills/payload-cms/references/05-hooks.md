# Hooks

> Source: https://payloadcms.com/docs/hooks/collections

## Table of Contents

- [Overview](#overview)
- [Collection Hooks](#collection-hooks)
- [Global Hooks](#global-hooks)
- [Field Hooks](#field-hooks)
- [Hook Arguments](#hook-arguments)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Hooks are functions that execute during the lifecycle of document operations. They allow you to add custom logic before or after database operations without modifying Payload's internals.

Hook types:
- **Collection hooks** — trigger on collection CRUD operations
- **Global hooks** — trigger on global read/update operations
- **Field hooks** — trigger on individual field processing

All hooks accept arrays of synchronous or async functions.

## Collection Hooks

```typescript
import type { CollectionConfig } from 'payload'

export const Posts: CollectionConfig = {
  slug: 'posts',
  hooks: {
    beforeValidate: [/* runs before field validation */],
    beforeChange: [/* runs before database write */],
    afterChange: [/* runs after database write */],
    beforeRead: [/* runs before returning data */],
    afterRead: [/* runs after data is read from DB */],
    beforeDelete: [/* runs before deletion */],
    afterDelete: [/* runs after deletion */],
    afterOperation: [/* runs after any operation completes */],
    beforeOperation: [/* runs before any operation starts */],
  },
  fields: [/* ... */],
}
```

### Hook Execution Order

For a `create` operation:
1. `beforeOperation`
2. `beforeValidate`
3. `beforeChange`
4. Database write
5. `afterChange`
6. `afterOperation`

For a `read` operation:
1. `beforeOperation`
2. Database read
3. `beforeRead`
4. `afterRead`
5. `afterOperation`

## Collection Hook Signatures

### beforeValidate

```typescript
beforeValidate: [
  ({ data, req, operation, originalDoc }) => {
    // Modify data before validation
    // operation: 'create' | 'update'
    if (operation === 'create' && !data.slug) {
      data.slug = data.title?.toLowerCase().replace(/\s+/g, '-')
    }
    return data  // Must return data
  },
],
```

### beforeChange

```typescript
beforeChange: [
  ({ data, req, operation, originalDoc }) => {
    // Last chance to modify data before save
    // Good for computed fields, sanitization
    if (operation === 'create') {
      data.createdBy = req.user?.id
    }
    return data
  },
],
```

### afterChange

```typescript
afterChange: [
  ({ doc, req, operation, previousDoc }) => {
    // doc = the saved document
    // Good for side effects: sending emails, webhooks, cache invalidation
    if (operation === 'create') {
      await sendNotification(doc)
    }
    return doc
  },
],
```

### beforeRead / afterRead

```typescript
beforeRead: [
  ({ doc, req, query }) => {
    // Modify the query or document before it's returned
    return doc
  },
],
afterRead: [
  ({ doc, req, query, findMany }) => {
    // Transform data after reading
    // findMany: boolean indicating if this is a find() or findByID()
    doc.computedField = calculateSomething(doc)
    return doc
  },
],
```

### beforeDelete / afterDelete

```typescript
beforeDelete: [
  ({ req, id }) => {
    // Validate if deletion should proceed
    // Throw an error to prevent deletion
  },
],
afterDelete: [
  ({ req, id, doc }) => {
    // Cleanup: delete related files, update references
    await cleanupRelatedData(id)
  },
],
```

## Global Hooks

Globals support a subset of hooks (no create/delete):

```typescript
export const SiteSettings: GlobalConfig = {
  slug: 'site-settings',
  hooks: {
    beforeValidate: [/* ... */],
    beforeChange: [/* ... */],
    afterChange: [/* ... */],
    beforeRead: [/* ... */],
    afterRead: [/* ... */],
  },
  fields: [/* ... */],
}
```

## Field Hooks

Field hooks run for individual fields during processing:

```typescript
{
  name: 'slug',
  type: 'text',
  hooks: {
    beforeValidate: [
      ({ value, data, req, operation, siblingData }) => {
        // Auto-generate slug from title
        if (!value && data?.title) {
          return data.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')
        }
        return value
      },
    ],
    afterRead: [
      ({ value }) => {
        // Transform value after read
        return value?.toLowerCase()
      },
    ],
  },
}
```

### Field Hook Types

| Hook | When | Returns |
|------|------|---------|
| `beforeValidate` | Before field validation | Field value |
| `beforeChange` | Before database write | Field value |
| `afterChange` | After database write | Nothing (side effects only) |
| `afterRead` | After data is read | Field value |

## Hook Arguments

### Common Arguments

| Argument | Available In | Description |
|----------|-------------|-------------|
| `req` | All hooks | Request object with `payload`, `user`, `locale` |
| `data` | beforeValidate, beforeChange | Incoming document data |
| `doc` | afterChange, afterRead, afterDelete | The document |
| `originalDoc` | beforeValidate, beforeChange (update) | Document before changes |
| `previousDoc` | afterChange | Document before this change |
| `operation` | beforeValidate, beforeChange, afterChange | `'create'` or `'update'` |
| `id` | beforeDelete, afterDelete | Document ID being deleted |
| `context` | All hooks | Shared context object for passing data between hooks |

### Using Context Between Hooks

```typescript
hooks: {
  beforeChange: [
    ({ data, context }) => {
      context.wasPublished = data.status === 'published'
      return data
    },
  ],
  afterChange: [
    ({ doc, context }) => {
      if (context.wasPublished) {
        // Send notification only when status changed to published
        notifySubscribers(doc)
      }
    },
  ],
}
```

## Common Patterns

### Populate createdBy/updatedBy

```typescript
hooks: {
  beforeChange: [
    ({ data, req, operation }) => {
      if (operation === 'create') {
        data.createdBy = req.user?.id
      }
      data.updatedBy = req.user?.id
      return data
    },
  ],
}
```

### Sync to External Service

```typescript
afterChange: [
  async ({ doc, operation, req }) => {
    try {
      await fetch('https://api.external.com/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event: operation, data: doc }),
      })
    } catch (error) {
      req.payload.logger.error('Webhook failed:', error)
      // Don't throw — let the operation succeed even if webhook fails
    }
  },
],
```

### Cache Invalidation

```typescript
afterChange: [
  async ({ doc, req }) => {
    await fetch(`${process.env.FRONTEND_URL}/api/revalidate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        collection: 'posts',
        slug: doc.slug,
      }),
    })
  },
],
```

## Common Pitfalls

1. **Forgetting to return data** — `beforeValidate` and `beforeChange` hooks MUST return the data object. Returning nothing results in empty documents.
2. **Infinite loops** — Calling `payload.update()` inside an `afterChange` hook on the same collection triggers the hook again. Use `context` to break the cycle.
3. **Throwing in afterChange** — Errors in `afterChange` don't roll back the database write. The document is already saved.
4. **Heavy operations in beforeRead** — These run on every read, including admin panel listing. Keep them fast.
5. **Not handling both create and update** — Check the `operation` argument when behavior should differ between create and update.
6. **Async side effects blocking response** — If a webhook or email doesn't need to complete before responding, consider using a background job instead.
