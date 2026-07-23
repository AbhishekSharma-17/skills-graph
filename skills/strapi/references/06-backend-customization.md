# Strapi — Backend Customization

> Source: https://docs.strapi.io/cms/backend-customization

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Routes](#routes)
- [Controllers](#controllers)
- [Services](#services)
- [Policies](#policies)
- [Middlewares](#middlewares)
- [Request Flow](#request-flow)
- [Common Pitfalls](#common-pitfalls)

## Architecture Overview

Strapi follows an MVC-like pattern where HTTP requests flow through:

```
Request → Routes → Policies → Middlewares → Controllers → Services → Database
```

Each layer can be customized per content type:

```
src/api/<api-name>/
├── content-types/   # Schema definitions
├── controllers/     # Request handlers
├── middlewares/      # Request/response interceptors
├── policies/        # Access control gates
├── routes/          # URL-to-handler mappings
└── services/        # Business logic
```

## Routes

### Core Routes

Strapi auto-generates five routes per collection type (`find`, `findOne`, `create`, `update`, `delete`). Customize with `createCoreRouter`:

```javascript
// src/api/restaurant/routes/restaurant.js
const { createCoreRouter } = require('@strapi/strapi').factories;

module.exports = createCoreRouter('api::restaurant.restaurant', {
  only: ['find', 'findOne'],  // only expose these routes
  config: {
    find: {
      auth: false,              // public access
      policies: [],
      middlewares: [],
    },
    findOne: {
      auth: false,
    },
  },
});
```

### Options

| Option | Description |
|--------|-------------|
| `only` | Array of route names to expose (whitelist) |
| `except` | Array of route names to exclude (blacklist) |
| `config` | Per-route configuration (auth, policies, middlewares) |
| `prefix` | Custom URL prefix (default: `/<pluralApiId>`) |

### Custom Routes

Create additional routes alongside core routes:

```javascript
// src/api/restaurant/routes/01-custom-routes.js
module.exports = {
  routes: [
    {
      method: 'GET',
      path: '/restaurants/featured',
      handler: 'api::restaurant.restaurant.findFeatured',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/restaurants/:documentId/reserve',
      handler: 'api::restaurant.restaurant.reserve',
      config: {
        policies: ['global::is-authenticated'],
      },
    },
  ],
};
```

Prefix custom route files with numbers (e.g., `01-`) to control loading order — custom routes should load before core routes to take priority.

### Public Routes

Routes require authentication by default. Disable with:

```javascript
config: { auth: false }
```

## Controllers

### Extending Core Controllers

Use `createCoreController` to override or add actions:

```javascript
// src/api/restaurant/controllers/restaurant.js
const { createCoreController } = require('@strapi/strapi').factories;

module.exports = createCoreController('api::restaurant.restaurant', ({ strapi }) => ({
  // Override the default find action
  async find(ctx) {
    // Add custom logic before calling the core action
    ctx.query = { ...ctx.query, filters: { ...ctx.query.filters, active: true } };
    const response = await super.find(ctx);
    // Modify response after
    response.meta.timestamp = new Date().toISOString();
    return response;
  },

  // Add a completely new action
  async findFeatured(ctx) {
    await this.validateQuery(ctx);
    const sanitizedQuery = await this.sanitizeQuery(ctx);

    const results = await strapi.service('api::restaurant.restaurant').findFeatured(sanitizedQuery);
    const sanitized = await this.sanitizeOutput(results, ctx);

    return this.transformResponse(sanitized);
  },
}));
```

### Security Methods

Always use these in custom controllers:

| Method | Purpose |
|--------|---------|
| `this.validateQuery(ctx)` | Throws error on invalid query params |
| `this.sanitizeQuery(ctx)` | Removes unauthorized query params |
| `this.sanitizeOutput(data, ctx)` | Removes private/unauthorized fields |
| `this.transformResponse(data, meta)` | Wraps data in standard response format |

### Context Object

```javascript
ctx.request.body   // POST/PUT request body
ctx.query          // Query string parameters
ctx.params         // URL path parameters (e.g., :documentId)
ctx.state.user     // Authenticated user (if any)
ctx.request.files  // Uploaded files
```

## Services

### Extending Core Services

```javascript
// src/api/restaurant/services/restaurant.js
const { createCoreService } = require('@strapi/strapi').factories;

module.exports = createCoreService('api::restaurant.restaurant', ({ strapi }) => ({
  // Override core find with custom logic
  async find(params) {
    const { results, pagination } = await super.find(params);
    // Post-process results
    return { results, pagination };
  },

  // Add custom service method
  async findFeatured(params) {
    return strapi.documents('api::restaurant.restaurant').findMany({
      ...params,
      filters: { ...params.filters, featured: true },
      sort: [{ rating: 'desc' }],
      populate: ['cover', 'category'],
    });
  },
}));
```

### Using Services in Controllers

```javascript
// Access API service
const result = await strapi.service('api::restaurant.restaurant').findFeatured(params);

// Access plugin service
const user = await strapi.service('plugin::users-permissions.user').fetch(userId);
```

### Helper Methods

- `getFetchParams(params)` — converts controller query objects to Document Service format

## Policies

Policies are boolean gates that run before controllers. Return `true` to proceed, `false` to block.

### Global Policy

```javascript
// src/policies/is-admin.js
module.exports = (policyContext, config, { strapi }) => {
  const user = policyContext.state.user;
  if (user && user.role.name === 'Admin') {
    return true;
  }
  return false;
};
```

### Configurable Policy

```javascript
// src/policies/rate-limit.js
module.exports = (policyContext, config, { strapi }) => {
  const { maxRequests = 100 } = config;
  // Rate limiting logic...
  return true;
};
```

### Applying Policies to Routes

```javascript
config: {
  policies: [
    'global::is-admin',
    'api::restaurant.is-owner',
    'plugin::users-permissions.isAuthenticated',
    { name: 'global::rate-limit', config: { maxRequests: 50 } },
    // Inline policy
    (policyContext, config, { strapi }) => {
      return policyContext.state.user !== null;
    },
  ],
}
```

### Naming Convention

| Scope | Prefix | Example |
|-------|--------|---------|
| Global | `global::` | `global::is-admin` |
| API | `api::<api-name>.` | `api::restaurant.is-owner` |
| Plugin | `plugin::<plugin>.` | `plugin::users-permissions.isAuthenticated` |

## Middlewares

Middlewares intercept request/response cycles. They differ from policies: middlewares can modify requests/responses, policies only allow/deny.

### Custom Middleware

```javascript
// src/middlewares/response-time.js
module.exports = (config, { strapi }) => {
  return async (ctx, next) => {
    const start = Date.now();
    await next();
    const delta = Math.ceil(Date.now() - start);
    ctx.set('X-Response-Time', `${delta}ms`);
  };
};
```

### Route-Level Middleware

```javascript
// src/api/restaurant/middlewares/is-owner.js
module.exports = (config, { strapi }) => {
  return async (ctx, next) => {
    const { documentId } = ctx.params;
    const userId = ctx.state.user?.id;

    const entry = await strapi.documents('api::restaurant.restaurant').findOne({
      documentId,
      populate: ['createdBy'],
    });

    if (entry?.createdBy?.id !== userId) {
      return ctx.forbidden('You are not the owner');
    }

    await next();
  };
};
```

### Applying to Routes

```javascript
config: {
  middlewares: [
    'global::response-time',
    'api::restaurant.is-owner',
    // Inline middleware
    (ctx, next) => {
      console.log('Request to:', ctx.url);
      return next();
    },
  ],
}
```

## Request Flow

The complete request lifecycle:

```
1. HTTP Request
2. Global Middlewares (config/middlewares.js)
3. Route Matching
4. Route Policies (evaluated in order, first false = 403)
5. Route Middlewares (evaluated in order)
6. Controller Action
7. Service Methods
8. Document Service / Query Engine
9. Database Query
10. Response (back through middleware chain)
```

## Common Pitfalls

- **When extending core controllers, sanitization is handled automatically** — don't double-sanitize when calling `super.find(ctx)`
- **Custom controller actions need explicit sanitization** via `validateQuery`, `sanitizeQuery`, and `sanitizeOutput`
- **Policy return value matters** — return `true` (not truthy values like `1` or `'yes'`) to proceed
- **Route file loading is alphabetical** — prefix custom routes with numbers to control order
- **Middleware `next()` must be awaited** — forgetting `await` causes response to return before downstream logic completes
- **Services accessed via `strapi.service()` use the full UID** — `'api::restaurant.restaurant'`, not just `'restaurant'`
