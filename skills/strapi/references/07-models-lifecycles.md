# Strapi — Models & Lifecycle Hooks

> Source: https://docs.strapi.io/cms/backend-customization/models

## Model Schema Structure

Every content type is defined by a `schema.json` file:

```
src/api/<api-name>/content-types/<type-name>/
├── schema.json       # Field definitions, relations, options
└── lifecycles.js     # Lifecycle hook implementations
```

### Schema Format

```json
{
  "kind": "collectionType",
  "collectionName": "products",
  "info": {
    "singularName": "product",
    "pluralName": "products",
    "displayName": "Product",
    "description": "E-commerce products"
  },
  "options": {
    "draftAndPublish": true
  },
  "pluginOptions": {
    "i18n": {
      "localized": true
    }
  },
  "attributes": {}
}
```

### Schema Fields

| Field | Description |
|-------|-------------|
| `kind` | `collectionType` or `singleType` |
| `collectionName` | Database table name |
| `info.singularName` | Singular API ID (used in routes) |
| `info.pluralName` | Plural API ID (used in REST endpoints) |
| `info.displayName` | Human-readable name in admin |
| `options.draftAndPublish` | Enable draft/publish workflow |
| `pluginOptions.i18n.localized` | Enable internationalization |

## Lifecycle Hooks

Lifecycle hooks execute custom logic at specific points in the content lifecycle. Define them in `lifecycles.js` alongside `schema.json`.

### Available Hooks

| Hook | Triggered When |
|------|----------------|
| `beforeCreate` | Before a new entry is created |
| `afterCreate` | After a new entry is created |
| `beforeUpdate` | Before an entry is updated |
| `afterUpdate` | After an entry is updated |
| `beforeDelete` | Before an entry is deleted |
| `afterDelete` | After an entry is deleted |
| `beforeDeleteMany` | Before batch deletion |
| `afterDeleteMany` | After batch deletion |
| `beforeFindOne` | Before a single entry query |
| `afterFindOne` | After a single entry query |
| `beforeFindMany` | Before a list query |
| `afterFindMany` | After a list query |
| `beforeCount` | Before a count query |
| `afterCount` | After a count query |

### Event Object

Every hook receives an `event` object:

```javascript
{
  action: 'beforeCreate',     // hook name
  model: {                    // content type metadata
    singularName: 'article',
    uid: 'api::article.article',
    // ...
  },
  params: {                   // operation parameters
    data: { /* entry data */ },
    where: { /* filter conditions */ },
    populate: [ /* relations to load */ ],
  },
  result: { /* entry data (after hooks only) */ },
  state: {},                  // shared state between before/after pairs
}
```

### Implementation Examples

```javascript
// src/api/article/content-types/article/lifecycles.js

module.exports = {
  // Auto-generate slug before creation
  beforeCreate(event) {
    const { data } = event.params;
    if (data.title && !data.slug) {
      data.slug = data.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '');
    }
  },

  // Log after creation
  afterCreate(event) {
    const { result } = event;
    strapi.log.info(`Article created: ${result.title} (${result.documentId})`);
  },

  // Prevent deletion of published articles
  beforeDelete(event) {
    const { where } = event.params;
    // Custom validation logic
  },

  // Update related data after update
  async afterUpdate(event) {
    const { result, params } = event;
    if (params.data.status === 'published') {
      // Notify subscribers, update cache, etc.
      await strapi.service('api::notification.notification').notifySubscribers(result);
    }
  },

  // Modify query before find
  beforeFindMany(event) {
    // Add default filter to always exclude archived entries
    event.params.where = {
      ...event.params.where,
      archived: false,
    };
  },

  // Post-process find results
  afterFindMany(event) {
    const { result } = event;
    // Modify results (e.g., add computed fields)
    if (Array.isArray(result)) {
      result.forEach(entry => {
        entry.readTime = Math.ceil((entry.content?.length || 0) / 1000);
      });
    }
  },
};
```

### Sharing State Between Before/After Hooks

Use `event.state` to pass data between a before and its corresponding after hook:

```javascript
module.exports = {
  beforeUpdate(event) {
    event.state.previousTitle = event.params.data.title;
  },

  afterUpdate(event) {
    const { result, state } = event;
    if (state.previousTitle !== result.title) {
      strapi.log.info(`Title changed from "${state.previousTitle}" to "${result.title}"`);
    }
  },
};
```

## Document Service Middlewares

For more granular control, register middlewares on the Document Service layer:

```javascript
// src/index.js
module.exports = {
  register({ strapi }) {
    strapi.documents.use(async (context, next) => {
      // Runs for ALL document operations
      if (context.action === 'create' && context.uid === 'api::article.article') {
        // Pre-process before creation
        context.params.data.slug = generateSlug(context.params.data.title);
      }

      const result = await next();

      // Post-process after operation
      return result;
    });
  },
};
```

## Validation Patterns

### Field-Level Validation (Schema)

```json
{
  "email": {
    "type": "email",
    "required": true,
    "unique": true
  },
  "age": {
    "type": "integer",
    "required": true,
    "min": 0,
    "max": 150
  },
  "bio": {
    "type": "text",
    "minLength": 10,
    "maxLength": 500
  }
}
```

### Custom Validation in Lifecycle Hooks

```javascript
module.exports = {
  beforeCreate(event) {
    const { data } = event.params;

    if (data.startDate && data.endDate) {
      if (new Date(data.startDate) >= new Date(data.endDate)) {
        throw new Error('Start date must be before end date');
      }
    }
  },
};
```

## Common Pitfalls

- **Lifecycle hooks run on ALL operations** including admin panel actions — guard with conditions if needed
- **`beforeFind` hooks modify the query** — be careful not to accidentally exclude entries the admin needs
- **`afterFind` hooks receive raw data** — mutations to `event.result` directly modify what's returned
- **`state` is only shared within a single before/after pair** — not across different hook types
- **Document Service middlewares vs lifecycle hooks**: middlewares run at the Document Service layer (API calls), lifecycle hooks run at the query engine layer (all database operations)
- **Async lifecycle hooks must be awaited** — if your hook is async, make sure the function is declared `async`
- **Throwing in `beforeCreate`/`beforeUpdate`** aborts the operation and returns a 400 error
