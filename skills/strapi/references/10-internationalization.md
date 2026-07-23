# Strapi — Internationalization (i18n)

> Source: https://docs.strapi.io/cms/features/internationalization

## Overview

Strapi's i18n feature enables managing content in multiple languages. It provides locale management, per-field translation control, and locale-aware API filtering. The feature is free and available by default but must be enabled per content type.

## Setup

### Enable i18n on a Content Type

1. Open Content-Type Builder
2. Edit or create a content type
3. Go to Advanced Settings
4. Toggle "Enable internationalization for this Content-Type"
5. Save

### Per-Field Localization

Not all fields need translation. Configure each field individually:

- **Localized fields**: Have different values per locale (e.g., title, description)
- **Non-localized fields**: Share the same value across all locales (e.g., price, SKU, media)

Set this in each field's Advanced Settings → "Enable localization for this field".

### Configure Locales

Navigate to Settings → Global Settings → Internationalization:

- Add locales from 500+ pre-configured ISO codes
- Set one locale as default
- Assign custom display names to locales

### Environment Variable

Set the default locale at project initialization:

```bash
STRAPI_PLUGIN_I18N_INIT_LOCALE_CODE=fr
```

## Content Translation Workflow

### Admin Panel

1. Open an entry in Content Manager
2. Use the locale dropdown to switch between languages
3. Translate content for each locale independently
4. Use "Fill in from another locale" to copy content from an existing translation
5. Publish each locale separately

Content can only be managed one locale at a time.

### AI-Powered Translation (Growth Plan)

On Growth plans, saving the default locale triggers automatic translation to all project locales. Translations consume Strapi AI credits (1,000/month on Growth plan).

Edits to non-default locales do not trigger re-translation — the default locale is the single source of truth for AI translations.

## REST API

### Query by Locale

```bash
# Get articles in French
GET /api/articles?locale=fr

# Get articles in default locale (omit param)
GET /api/articles

# Get a specific article in Spanish
GET /api/articles/abc123?locale=es
```

### Create with Locale

```bash
POST /api/articles
Content-Type: application/json

{
  "data": {
    "title": "Mon Article",
    "content": "Contenu en français..."
  },
  "locale": "fr"
}
```

### Update a Locale

```bash
PUT /api/articles/abc123?locale=fr
Content-Type: application/json

{
  "data": {
    "title": "Titre Mis à Jour"
  }
}
```

### Delete a Specific Locale

```bash
DELETE /api/articles/abc123?locale=fr
```

This deletes only the French version; other locales remain intact.

## GraphQL API

### Query by Locale

```graphql
query {
  article(documentId: "abc123", locale: "fr") {
    documentId
    title
    content
    locale
  }
}

# List articles in a specific locale
query {
  articles(locale: "es") {
    documentId
    title
    locale
  }
}
```

### Create with Locale

```graphql
mutation {
  createArticle(
    data: { title: "Mon Article", content: "..." }
    locale: "fr"
  ) {
    documentId
    title
    locale
  }
}
```

### Update Localized Entry

```graphql
mutation {
  updateArticle(
    documentId: "abc123"
    data: { title: "Nouveau Titre" }
    locale: "fr"
  ) {
    documentId
    title
    locale
  }
}
```

### Delete Specific Locale

```graphql
mutation {
  deleteArticle(documentId: "abc123", locale: "fr") {
    documentId
  }
}
```

## Document Service API

### Query by Locale

```javascript
// Get entries in French
const articles = await strapi.documents('api::article.article').findMany({
  locale: 'fr',
});

// Get a specific entry in Spanish
const article = await strapi.documents('api::article.article').findOne({
  documentId: 'abc123',
  locale: 'es',
});
```

### Create with Locale

```javascript
const article = await strapi.documents('api::article.article').create({
  data: { title: 'Mon Article', content: '...' },
  locale: 'fr',
});
```

### Publish Specific Locale

```javascript
await strapi.documents('api::article.article').publish({
  documentId: 'abc123',
  locale: 'fr',
});
```

### Publish All Locales

```javascript
await strapi.documents('api::article.article').publish({
  documentId: 'abc123',
  locale: '*',
});
```

### Delete Operations

```javascript
// Delete only French version
await strapi.documents('api::article.article').delete({
  documentId: 'abc123',
  locale: 'fr',
});

// Delete all locales
await strapi.documents('api::article.article').delete({
  documentId: 'abc123',
  locale: '*',
});
```

## Relational Fields and i18n

Relational field entries can differ between locales. For example, an Article in English can relate to different Categories than the same Article in French.

Configure this behavior in the Content-Type Builder under the relation field's i18n settings.

## Common Pitfalls

- **i18n must be enabled per content type** — it's not a global switch
- **Per-field localization control** is important — not every field needs translation (prices, dates, media often shouldn't be localized)
- **Content managed one locale at a time** — there's no bulk translation interface in the admin
- **Omitting `locale` defaults to the default locale** — it does not return all locales
- **Relations can vary per locale** — this is a feature, but can be confusing if unexpected
- **Deleting a locale** only removes that translation — other locales and the documentId remain
- **AI translations only trigger from default locale changes** — editing a non-default locale is manual only
- **Each locale must be published separately** — publishing English doesn't auto-publish French
