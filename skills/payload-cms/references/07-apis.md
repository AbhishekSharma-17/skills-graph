# APIs — Local, REST, and GraphQL

> Source: https://payloadcms.com/docs/local-api/overview

## Table of Contents

- [Overview](#overview)
- [Local API](#local-api)
- [REST API](#rest-api)
- [GraphQL API](#graphql-api)
- [Query Operators](#query-operators)
- [Pagination and Sorting](#pagination-and-sorting)
- [Depth and Population](#depth-and-population)
- [Common Pitfalls](#common-pitfalls)

## Overview

Every collection and global in Payload automatically generates three API layers:

| API | Access Method | Best For |
|-----|-------------|----------|
| **Local API** | Direct function calls in Node.js | Server components, server actions, hooks, scripts |
| **REST API** | HTTP endpoints (`/api/<slug>`) | External clients, mobile apps, third-party integrations |
| **GraphQL API** | Single endpoint (`/api/graphql`) | Frontend apps that need precise field selection |

## Local API

The most powerful and performant API. Direct database access with no HTTP overhead, fully typed:

```typescript
import { getPayload } from 'payload'
import config from '@payload-config'

const payload = await getPayload({ config })

// Find documents
const posts = await payload.find({
  collection: 'posts',
  where: {
    status: { equals: 'published' },
    category: { in: ['tech', 'design'] },
  },
  sort: '-createdAt',
  limit: 10,
  page: 1,
  depth: 2,
})
// Returns: { docs: Post[], totalDocs, totalPages, page, ... }

// Find by ID
const post = await payload.findByID({
  collection: 'posts',
  id: '64a1b2c3d4e5f6g7h8i9j0k1',
  depth: 1,
})

// Create
const newPost = await payload.create({
  collection: 'posts',
  data: {
    title: 'My New Post',
    content: richTextContent,
    status: 'draft',
  },
})

// Update
const updated = await payload.update({
  collection: 'posts',
  id: '64a1b2c3d4e5f6g7h8i9j0k1',
  data: { status: 'published' },
})

// Update many
const bulkUpdated = await payload.update({
  collection: 'posts',
  where: { status: { equals: 'draft' }, createdAt: { less_than: '2024-01-01' } },
  data: { status: 'archived' },
})

// Delete
await payload.delete({
  collection: 'posts',
  id: '64a1b2c3d4e5f6g7h8i9j0k1',
})

// Delete many
await payload.delete({
  collection: 'posts',
  where: { status: { equals: 'archived' } },
})

// Count
const { totalDocs } = await payload.count({
  collection: 'posts',
  where: { status: { equals: 'published' } },
})
```

### Global Operations (Local API)

```typescript
// Read global
const settings = await payload.findGlobal({ slug: 'site-settings' })

// Update global
await payload.updateGlobal({
  slug: 'site-settings',
  data: { siteName: 'Updated Name' },
})
```

### Access Control in Local API

```typescript
// Default: overrideAccess is TRUE (bypasses access control)
const allPosts = await payload.find({ collection: 'posts' })

// To enforce access control (e.g., on behalf of a user):
const userPosts = await payload.find({
  collection: 'posts',
  overrideAccess: false,
  user: req.user,  // Pass the authenticated user
})
```

## REST API

Auto-generated HTTP endpoints:

### Collection Endpoints

| Method | Path | Operation |
|--------|------|-----------|
| `GET` | `/api/<slug>` | Find documents |
| `GET` | `/api/<slug>/:id` | Find by ID |
| `POST` | `/api/<slug>` | Create document |
| `PATCH` | `/api/<slug>/:id` | Update document |
| `DELETE` | `/api/<slug>/:id` | Delete document |

### Query Parameters

```
GET /api/posts?where[status][equals]=published
              &where[category][in]=tech,design
              &sort=-createdAt
              &limit=10
              &page=2
              &depth=1
              &locale=en
              &select=title,slug,excerpt
```

### Authentication Headers

```
Authorization: Bearer <jwt-token>
# or
Authorization: users API-Key <api-key>
```

### Global Endpoints

| Method | Path | Operation |
|--------|------|-----------|
| `GET` | `/api/globals/<slug>` | Read global |
| `POST` | `/api/globals/<slug>` | Update global |

## GraphQL API

Available at `/api/graphql`:

```graphql
# Find posts
query {
  Posts(
    where: { status: { equals: published } }
    sort: "-createdAt"
    limit: 10
    page: 1
  ) {
    docs {
      id
      title
      slug
      author {
        name
      }
    }
    totalDocs
    totalPages
  }
}

# Find by ID
query {
  Post(id: "64a1b2c3d4e5f6g7h8i9j0k1") {
    title
    content
  }
}

# Create
mutation {
  createPost(data: { title: "New Post", status: draft }) {
    id
    title
  }
}

# Update
mutation {
  updatePost(id: "64a1b2c3d4e5f6g7h8i9j0k1", data: { status: published }) {
    id
    status
  }
}

# Delete
mutation {
  deletePost(id: "64a1b2c3d4e5f6g7h8i9j0k1") {
    id
  }
}

# Read global
query {
  SiteSetting {
    siteName
    logo { url }
  }
}
```

## Query Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `equals` | Exact match | `{ status: { equals: 'published' } }` |
| `not_equals` | Not equal | `{ status: { not_equals: 'draft' } }` |
| `greater_than` | Greater than | `{ price: { greater_than: 100 } }` |
| `greater_than_equal` | >= | `{ price: { greater_than_equal: 100 } }` |
| `less_than` | Less than | `{ price: { less_than: 50 } }` |
| `less_than_equal` | <= | `{ price: { less_than_equal: 50 } }` |
| `like` | Case-insensitive partial match | `{ title: { like: 'payload' } }` |
| `contains` | Contains substring | `{ tags: { contains: 'cms' } }` |
| `in` | In array of values | `{ status: { in: ['published', 'featured'] } }` |
| `not_in` | Not in array | `{ status: { not_in: ['draft', 'archived'] } }` |
| `exists` | Field exists/has value | `{ featuredImage: { exists: true } }` |
| `near` | GeoJSON proximity | `{ location: { near: '-71.05,42.36,10000' } }` |

### Combining Operators

```typescript
where: {
  and: [
    { status: { equals: 'published' } },
    {
      or: [
        { category: { equals: 'tech' } },
        { category: { equals: 'design' } },
      ],
    },
  ],
}
```

## Pagination and Sorting

```typescript
const result = await payload.find({
  collection: 'posts',
  sort: '-createdAt',       // Prefix with - for descending
  limit: 25,                // Documents per page
  page: 2,                  // Page number (1-based)
})

// result shape:
{
  docs: Post[],             // Documents on this page
  totalDocs: 150,           // Total matching documents
  totalPages: 6,            // Total pages
  page: 2,                  // Current page
  pagingCounter: 26,        // Index of first doc on this page
  hasPrevPage: true,
  hasNextPage: true,
  prevPage: 1,
  nextPage: 3,
}
```

## Depth and Population

Control how deeply relationships are populated:

```typescript
// depth: 0 — relationships return IDs only
{ author: '64a1b2c3...' }

// depth: 1 — first-level relationships populated
{ author: { id: '64a1b2c3...', name: 'John', role: 'editor' } }

// depth: 2 — relationships within relationships also populated
{ author: { id: '...', name: 'John', organization: { id: '...', name: 'Acme' } } }
```

Use `select` to limit returned fields (reduces payload size):

```typescript
const posts = await payload.find({
  collection: 'posts',
  select: {
    title: true,
    slug: true,
    excerpt: true,
  },
  depth: 0,
})
```

## Common Pitfalls

1. **Excessive depth** — High depth values cause expensive joins. Default to 0-1, increase only when needed.
2. **Local API `overrideAccess` default** — It's `true` by default, bypassing access control. Always set `false` when acting on behalf of a user.
3. **GraphQL disabled** — Set `graphQL: false` on collections/globals you don't need exposed via GraphQL to reduce schema size.
4. **Missing auth header** — REST API returns 401 for authenticated routes without a valid token or cookie.
5. **Forgetting pagination** — `find()` returns paginated results. Don't assume `docs` contains all documents.
