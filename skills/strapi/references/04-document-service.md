# Strapi — Document Service API

> Source: https://docs.strapi.io/cms/api/document-service

## Overview

The Document Service API is Strapi v5's recommended backend interface for programmatic content operations. It sits above the Query Engine and handles CRUD operations on "documents" — entities that span all locales and draft/published states under a single `documentId`.

Use the Document Service when:
- Writing custom controllers or services
- Building plugin backend logic
- Running data migrations or seed scripts
- Implementing business logic that interacts with content

### Key Distinction: documentId vs id

- **`documentId`**: A persistent 24-character alphanumeric identifier. Stable across duplications, import/export, and locale changes. Use this for all Document Service operations.
- **`id`**: Internal database integer. Do not use for content identification in application logic.

## Accessing the Service

```javascript
// In a controller, service, or lifecycle hook:
const documents = strapi.documents('api::article.article');

// Alternative syntax:
strapi.documents('api::article.article').findMany({ /* params */ });
```

## Core Methods

### findMany

Retrieve multiple documents with filtering, sorting, and pagination:

```javascript
const { results, pagination } = await strapi.documents('api::article.article').findMany({
  filters: {
    title: { $contains: 'strapi' },
    publishedAt: { $notNull: true },
  },
  sort: [{ createdAt: 'desc' }],
  populate: ['category', 'tags'],
  fields: ['title', 'slug', 'publishedAt'],
  pagination: { page: 1, pageSize: 25 },
  locale: 'en',
  status: 'published',
});
```

### findOne

Retrieve a single document by `documentId`:

```javascript
const article = await strapi.documents('api::article.article').findOne({
  documentId: 'a1b2c3d4e5f6g7h8i9j0',
  populate: ['category', 'cover'],
  fields: ['title', 'content'],
  locale: 'en',
  status: 'published',
});
```

### findFirst

Return the first document matching parameters:

```javascript
const latest = await strapi.documents('api::article.article').findFirst({
  sort: [{ createdAt: 'desc' }],
  filters: { status: { $eq: 'published' } },
  populate: ['category'],
});
```

### create

Create a new document:

```javascript
const article = await strapi.documents('api::article.article').create({
  data: {
    title: 'New Article',
    content: 'Article body...',
    category: 'category-document-id',
    tags: ['tag-doc-id-1', 'tag-doc-id-2'],
  },
  locale: 'en',
  status: 'draft',
  populate: ['category'],
});
```

### update

Update an existing document:

```javascript
const updated = await strapi.documents('api::article.article').update({
  documentId: 'a1b2c3d4e5f6g7h8i9j0',
  data: {
    title: 'Updated Title',
    category: null, // clears the relation
  },
  locale: 'en',
});
```

### delete

Remove a document:

```javascript
// Delete all locales
await strapi.documents('api::article.article').delete({
  documentId: 'a1b2c3d4e5f6g7h8i9j0',
});

// Delete specific locale only
await strapi.documents('api::article.article').delete({
  documentId: 'a1b2c3d4e5f6g7h8i9j0',
  locale: 'fr',
});
```

### deleteMany

Batch delete documents matching filters:

```javascript
const { count } = await strapi.documents('api::article.article').deleteMany({
  filters: {
    createdAt: { $lt: '2025-01-01' },
  },
});
```

### count

Count documents matching parameters:

```javascript
const total = await strapi.documents('api::article.article').count({
  filters: {
    publishedAt: { $notNull: true },
  },
  locale: 'en',
});
```

## Draft & Publish Methods

### publish

Move a draft document to published state:

```javascript
await strapi.documents('api::article.article').publish({
  documentId: 'a1b2c3d4e5f6g7h8i9j0',
  locale: 'en',
});

// Publish all locales
await strapi.documents('api::article.article').publish({
  documentId: 'a1b2c3d4e5f6g7h8i9j0',
  locale: '*',
});
```

### unpublish

Revert a published document to draft:

```javascript
await strapi.documents('api::article.article').unpublish({
  documentId: 'a1b2c3d4e5f6g7h8i9j0',
  locale: 'en',
});
```

### discardDraft

Discard draft changes, keeping only the published version:

```javascript
await strapi.documents('api::article.article').discardDraft({
  documentId: 'a1b2c3d4e5f6g7h8i9j0',
  locale: 'en',
});
```

## Common Parameters

| Parameter | Description |
|-----------|-------------|
| `filters` | Query conditions using operators (`$eq`, `$contains`, `$gt`, etc.) |
| `fields` | Array of attribute names to return |
| `populate` | Relations/components to include |
| `sort` | Ordering (e.g., `[{ createdAt: 'desc' }]`) |
| `pagination` | `{ page, pageSize }` or `{ start, limit }` |
| `locale` | Target locale (default locale if omitted, `'*'` for all) |
| `status` | `'draft'` or `'published'` (when Draft & Publish enabled) |
| `publicationFilter` | Filter by publication state |

## Security: Sanitization

Document Service returns unsanitized data. Always sanitize before exposing to clients:

```javascript
// In a custom controller:
const { createCoreController } = require('@strapi/strapi').factories;

module.exports = createCoreController('api::article.article', ({ strapi }) => ({
  async customFind(ctx) {
    const results = await strapi.documents('api::article.article').findMany({
      filters: { featured: true },
      populate: ['category'],
    });

    // Sanitize before returning to client
    const sanitized = await this.sanitizeOutput(results, ctx);
    return this.transformResponse(sanitized);
  },
}));
```

## Common Pitfalls

- **Always sanitize output** when using Document Service in custom controllers — unlike core controllers, it returns raw unsanitized data
- **Relations use `documentId`** strings, not numeric `id` — pass `documentId` when setting relations
- **`locale` defaults to the default locale** — omitting it doesn't return all locales
- **Use `locale: '*'`** for operations that should affect all locales
- **`status` parameter** only works when Draft & Publish is enabled on the content type
- **`populate` must be explicit** — relations, components, and dynamic zones are never auto-populated
