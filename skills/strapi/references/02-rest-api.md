# Strapi — REST API

> Source: https://docs.strapi.io/cms/api/rest

## Table of Contents

- [Endpoint Patterns](#endpoint-patterns)
- [Response Format](#response-format)
- [CRUD Operations](#crud-operations)
- [Filtering](#filtering)
- [Sorting](#sorting)
- [Pagination](#pagination)
- [Population](#population)
- [Field Selection](#field-selection)
- [Draft & Publish](#draft--publish)
- [Locale Filtering](#locale-filtering)
- [Common Pitfalls](#common-pitfalls)

## Endpoint Patterns

Strapi auto-generates REST endpoints for every content type.

### Collection Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/:pluralApiId` | List entries (paginated) |
| `POST` | `/api/:pluralApiId` | Create entry |
| `GET` | `/api/:pluralApiId/:documentId` | Get single entry |
| `PUT` | `/api/:pluralApiId/:documentId` | Update entry |
| `DELETE` | `/api/:pluralApiId/:documentId` | Delete entry |

### Single Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/:singularApiId` | Get the entry |
| `PUT` | `/api/:singularApiId` | Update or create the entry |
| `DELETE` | `/api/:singularApiId` | Delete the entry |

## Response Format

All responses follow a consistent structure:

```json
{
  "data": {
    "id": 1,
    "documentId": "a1b2c3d4e5f6g7h8i9j0",
    "title": "My Article",
    "content": "Article body...",
    "createdAt": "2026-07-23T10:00:00.000Z",
    "updatedAt": "2026-07-23T10:00:00.000Z",
    "publishedAt": "2026-07-23T10:00:00.000Z",
    "locale": "en"
  },
  "meta": {}
}
```

List endpoints return an array with pagination metadata:

```json
{
  "data": [ /* array of entries */ ],
  "meta": {
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "pageCount": 4,
      "total": 100
    }
  }
}
```

## CRUD Operations

### Create

```bash
POST /api/articles
Content-Type: application/json

{
  "data": {
    "title": "New Article",
    "content": "Article body here",
    "category": "a1b2c3d4..."
  }
}
```

Relations are set by passing the related entry's `documentId`.

### Read (Single)

```bash
GET /api/articles/a1b2c3d4e5f6g7h8i9j0
```

### Read (List)

```bash
GET /api/articles
```

### Update

```bash
PUT /api/articles/a1b2c3d4e5f6g7h8i9j0
Content-Type: application/json

{
  "data": {
    "title": "Updated Title"
  }
}
```

Send `null` to clear a field value. Only include fields you want to change.

### Delete

```bash
DELETE /api/articles/a1b2c3d4e5f6g7h8i9j0
```

Deletion is permanent and irreversible.

## Filtering

Use the `filters` query parameter with operators:

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$eq` | Equal | `filters[title][$eq]=Hello` |
| `$ne` | Not equal | `filters[title][$ne]=Hello` |
| `$lt` | Less than | `filters[price][$lt]=100` |
| `$lte` | Less than or equal | `filters[price][$lte]=100` |
| `$gt` | Greater than | `filters[price][$gt]=50` |
| `$gte` | Greater than or equal | `filters[price][$gte]=50` |
| `$in` | In array | `filters[status][$in][0]=draft&filters[status][$in][1]=published` |
| `$notIn` | Not in array | `filters[status][$notIn][0]=archived` |
| `$contains` | Contains (case-sensitive) | `filters[title][$contains]=strapi` |
| `$containsi` | Contains (case-insensitive) | `filters[title][$containsi]=strapi` |
| `$notContains` | Does not contain | `filters[title][$notContains]=test` |
| `$startsWith` | Starts with | `filters[title][$startsWith]=How` |
| `$endsWith` | Ends with | `filters[slug][$endsWith]=-guide` |
| `$null` | Is null | `filters[publishedAt][$null]=true` |
| `$notNull` | Is not null | `filters[publishedAt][$notNull]=true` |
| `$between` | Between two values | `filters[price][$between][0]=10&filters[price][$between][1]=50` |

### Logical Operators

```bash
# AND (default when combining filters)
GET /api/articles?filters[title][$contains]=strapi&filters[status][$eq]=published

# OR
GET /api/articles?filters[$or][0][title][$contains]=strapi&filters[$or][1][title][$contains]=cms

# NOT
GET /api/articles?filters[$not][0][status][$eq]=archived

# Nested AND + OR
GET /api/articles?filters[$and][0][$or][0][title][$eq]=Hello&filters[$and][0][$or][1][title][$eq]=World&filters[$and][1][status][$eq]=published
```

### Filtering on Relations

```bash
GET /api/articles?filters[category][name][$eq]=Technology
GET /api/articles?filters[tags][name][$in][0]=javascript&filters[tags][name][$in][1]=react
```

## Sorting

```bash
# Single field ascending (default)
GET /api/articles?sort=title

# Single field descending
GET /api/articles?sort=title:desc

# Multiple fields
GET /api/articles?sort[0]=publishedAt:desc&sort[1]=title:asc

# Sort on relation field
GET /api/articles?sort=category.name:asc
```

## Pagination

### Page-Based (Default)

```bash
GET /api/articles?pagination[page]=2&pagination[pageSize]=10
```

- `page`: Page number (default: 1)
- `pageSize`: Items per page (default: 25, max: 100)

### Offset-Based

```bash
GET /api/articles?pagination[start]=20&pagination[limit]=10
```

- `start`: Index of first item (default: 0)
- `limit`: Number of items (default: 25, max: 100)

### Disable Pagination

```bash
GET /api/articles?pagination[limit]=-1
```

## Population

By default, relations, components, and dynamic zones are NOT included in responses. Use `populate` to include them.

```bash
# Populate one relation
GET /api/articles?populate=category

# Populate multiple
GET /api/articles?populate[0]=category&populate[1]=tags&populate[2]=cover

# Populate all top-level relations
GET /api/articles?populate=*

# Deep population (nested relations)
GET /api/articles?populate[category][populate]=icon
GET /api/articles?populate[category][populate][0]=icon&populate[category][populate][1]=parent

# Populate with field selection
GET /api/articles?populate[category][fields][0]=name&populate[category][fields][1]=slug

# Populate with filtering
GET /api/articles?populate[comments][filters][approved][$eq]=true&populate[comments][sort]=createdAt:desc
```

### Dynamic Zone Population

```bash
GET /api/articles?populate[blocks][on][blocks.hero][populate]=*&populate[blocks][on][blocks.gallery][populate][images][fields][0]=url
```

## Field Selection

```bash
# Select specific fields only
GET /api/articles?fields[0]=title&fields[1]=slug&fields[2]=publishedAt
```

## Draft & Publish

```bash
# Get published entries only (default for public role)
GET /api/articles?status=published

# Get draft entries
GET /api/articles?status=draft

# Filter by publication state
GET /api/articles?publicationFilter=NEVER_PUBLISHED
GET /api/articles?publicationFilter=HAS_PUBLISHED_VERSION
GET /api/articles?publicationFilter=MODIFIED
```

## Locale Filtering

```bash
# Get entries in a specific locale
GET /api/articles?locale=fr

# Get entries in the default locale (omit param)
GET /api/articles
```

## Common Pitfalls

- **Content types are private by default** — enable public permissions in Settings → Users & Permissions → Roles → Public
- **Relations are not populated by default** — always use `populate` to include related data
- **`documentId` is the query identifier**, not the numeric `id` — use `documentId` in GET/PUT/DELETE paths
- **Maximum `pageSize` is 100** — for bulk data, use pagination loops
- **Deeply nested population** can cause performance issues — populate only what you need
- **Dynamic zones require `on` syntax** for selective population
- **Filters use bracket notation** in URLs, which can be hard to read — consider using a query builder library
