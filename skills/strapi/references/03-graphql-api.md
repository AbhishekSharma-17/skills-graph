# Strapi — GraphQL API

> Source: https://docs.strapi.io/cms/api/graphql

## Table of Contents

- [Setup](#setup)
- [Query Patterns](#query-patterns)
- [Mutations](#mutations)
- [Filtering](#filtering)
- [Sorting](#sorting)
- [Pagination](#pagination)
- [Relations & Media](#relations--media)
- [Dynamic Zones](#dynamic-zones)
- [Draft & Publish](#draft--publish)
- [Internationalization](#internationalization)
- [Common Pitfalls](#common-pitfalls)

## Setup

Install the GraphQL plugin:

```bash
npm install @strapi/plugin-graphql
```

The GraphQL playground is available at `http://localhost:1337/graphql` in development mode.

No additional configuration required — the plugin auto-generates the schema from content types.

## Query Patterns

### Single Document

Query by `documentId` using the singular API ID:

```graphql
query {
  restaurant(documentId: "a1b2c3d4e5f6g7h8i9j0") {
    documentId
    name
    description
    createdAt
  }
}
```

### Multiple Documents (Flat)

Use the plural API ID for flat result arrays:

```graphql
query {
  restaurants {
    documentId
    name
    description
  }
}
```

### Multiple Documents (Relay-Style)

Use the `_connection` suffix for pagination metadata:

```graphql
query {
  restaurants_connection {
    nodes {
      documentId
      name
    }
    pageInfo {
      page
      pageSize
      pageCount
      total
    }
  }
}
```

## Mutations

### Create

```graphql
mutation {
  createRestaurant(data: {
    name: "Pizzeria Amore"
    description: "Authentic Italian cuisine"
  }) {
    documentId
    name
  }
}
```

With variables:

```graphql
mutation CreateRestaurant($data: RestaurantInput!) {
  createRestaurant(data: $data) {
    documentId
    name
  }
}
```

```json
{
  "data": {
    "name": "Pizzeria Amore",
    "description": "Authentic Italian cuisine"
  }
}
```

### Update

```graphql
mutation {
  updateRestaurant(
    documentId: "a1b2c3d4e5f6g7h8i9j0"
    data: { name: "Pizzeria Bella" }
  ) {
    documentId
    name
  }
}
```

### Delete

```graphql
mutation {
  deleteRestaurant(documentId: "a1b2c3d4e5f6g7h8i9j0") {
    documentId
  }
}
```

## Filtering

Use the `filters` argument with operators:

```graphql
query {
  restaurants(filters: {
    name: { containsi: "pizza" }
  }) {
    documentId
    name
  }
}
```

### Available Operators

`eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `notIn`, `contains`, `containsi`, `startsWith`, `endsWith`, `null`, `notNull`, `between`

### Logical Operators

```graphql
query {
  restaurants(filters: {
    and: [
      { not: { averagePrice: { gte: 50 } } }
      {
        or: [
          { name: { eq: "Pizzeria" } }
          { name: { startsWith: "Ristorante" } }
        ]
      }
    ]
  }) {
    documentId
    name
    averagePrice
  }
}
```

### Filtering on Relations

```graphql
query {
  articles(filters: {
    category: { name: { eq: "Technology" } }
  }) {
    documentId
    title
  }
}
```

## Sorting

```graphql
# Single field
query {
  restaurants(sort: "name") {
    documentId
    name
  }
}

# Multiple fields with direction
query {
  restaurants(sort: ["name:asc", "averagePrice:desc"]) {
    documentId
    name
    averagePrice
  }
}
```

## Pagination

### Page-Based

```graphql
query {
  restaurants_connection(pagination: { page: 1, pageSize: 10 }) {
    nodes {
      documentId
      name
    }
    pageInfo {
      page
      pageSize
      pageCount
      total
    }
  }
}
```

### Offset-Based

```graphql
query {
  restaurants_connection(pagination: { start: 10, limit: 20 }) {
    nodes {
      documentId
      name
    }
    pageInfo {
      page
      pageSize
      pageCount
      total
    }
  }
}
```

## Relations & Media

### Fetching Relations

```graphql
query {
  articles {
    documentId
    title
    category {
      documentId
      name
    }
    tags {
      documentId
      name
    }
  }
}
```

### Media Fields

Use `_connection` for media field pagination:

```graphql
query {
  restaurants {
    documentId
    name
    images_connection {
      nodes {
        documentId
        url
        alternativeText
        width
        height
      }
    }
  }
}
```

Single media fields can be queried directly:

```graphql
query {
  article(documentId: "abc123") {
    cover {
      url
      alternativeText
    }
  }
}
```

### Components

```graphql
query {
  articles {
    documentId
    title
    seo {
      metaTitle
      metaDescription
    }
  }
}
```

## Dynamic Zones

Dynamic zones require fragment syntax with `__typename`:

```graphql
query {
  articles {
    documentId
    title
    blocks {
      __typename
      ... on ComponentBlocksHero {
        heading
        subheading
        backgroundImage {
          url
        }
      }
      ... on ComponentBlocksRichText {
        body
      }
      ... on ComponentBlocksQuote {
        text
        author
      }
    }
  }
}
```

## Draft & Publish

```graphql
# Published entries (default)
query {
  articles(status: PUBLISHED) {
    documentId
    title
  }
}

# Draft entries
query {
  articles(status: DRAFT) {
    documentId
    title
  }
}

# Publication filter
query {
  articles(status: DRAFT, publicationFilter: NEVER_PUBLISHED) {
    documentId
    title
  }
}
```

Available `publicationFilter` values: `NEVER_PUBLISHED`, `HAS_PUBLISHED_VERSION`, `MODIFIED`, `UNMODIFIED`.

## Internationalization

### Query by Locale

```graphql
query {
  restaurant(documentId: "abc123", locale: "fr") {
    documentId
    name
    locale
  }
}
```

### Create with Locale

```graphql
mutation {
  createRestaurant(
    data: { name: "Brasserie Parisienne" }
    locale: "fr"
  ) {
    documentId
    locale
    name
  }
}
```

### Delete Specific Locale

```graphql
mutation {
  deleteRestaurant(
    documentId: "abc123"
    locale: "fr"
  ) {
    documentId
  }
}
```

## Common Pitfalls

- **No file upload via GraphQL** — use the REST API `POST /api/upload` for media uploads
- **Aggregations (count, sum, avg)** are not yet implemented in Strapi v5 GraphQL
- **`pageInfo` only works at root level** — nested relation pagination is not supported
- **Media mutations use v4 `id`** (numeric), not `documentId` — and that `id` is not available in GraphQL query responses
- **Dynamic zones require `__typename`** and fragment syntax — plain field queries won't work
- **The GraphQL playground** is only available in development mode, not production
