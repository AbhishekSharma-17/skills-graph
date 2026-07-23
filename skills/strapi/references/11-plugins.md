# Strapi — Plugins

> Source: https://docs.strapi.io/cms/plugins/developing-plugins

## Table of Contents

- [Overview](#overview)
- [Plugin Types](#plugin-types)
- [Built-in Plugins](#built-in-plugins)
- [Creating a Local Plugin](#creating-a-local-plugin)
- [Server API](#server-api)
- [Admin Panel API](#admin-panel-api)
- [MCP Server Extension](#mcp-server-extension)
- [Publishing Plugins](#publishing-plugins)
- [Accessing Plugin APIs](#accessing-plugin-apis)
- [Common Pitfalls](#common-pitfalls)

## Overview

Plugins extend Strapi's functionality with new features, content types, API endpoints, and admin panel UI. They can be local (project-specific), published to npm, or distributed through the Strapi Marketplace.

## Plugin Types

| Type | Location | Use Case |
|------|----------|----------|
| **Built-in** | Installed by default | i18n, Users & Permissions, Upload |
| **Marketplace** | `npm install` | Community/official extensions |
| **Local** | `src/plugins/` | Project-specific features |

## Built-in Plugins

| Plugin | Description |
|--------|-------------|
| `@strapi/plugin-users-permissions` | JWT auth, roles, social providers |
| `@strapi/plugin-upload` | Media library, file storage providers |
| `@strapi/plugin-i18n` | Internationalization |
| `@strapi/plugin-graphql` | GraphQL API (install separately) |
| `@strapi/plugin-documentation` | Auto-generated OpenAPI docs |

## Creating a Local Plugin

### Using Plugin SDK

```bash
npx @strapi/sdk-plugin init my-plugin
```

This generates the plugin scaffolding with server and admin directories.

### Manual Creation

```
src/plugins/my-plugin/
├── admin/
│   └── src/
│       └── index.js          # Admin panel registration
├── server/
│   ├── bootstrap.js          # Runs on server start
│   ├── config/
│   │   └── index.js          # Default config
│   ├── content-types/        # Plugin content types
│   ├── controllers/          # Plugin controllers
│   ├── middlewares/           # Plugin middlewares
│   ├── policies/             # Plugin policies
│   ├── register.js           # Runs before bootstrap
│   ├── routes/               # Plugin routes
│   └── services/             # Plugin services
├── package.json
└── strapi-server.js          # Server entry point
```

### Register the Plugin

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  'my-plugin': {
    enabled: true,
    resolve: './src/plugins/my-plugin',
    config: {
      // Plugin-specific configuration
    },
  },
});
```

## Server API

### Plugin Entry Point

```javascript
// src/plugins/my-plugin/strapi-server.js
module.exports = {
  register({ strapi }) {
    // Register custom logic before bootstrap
  },

  bootstrap({ strapi }) {
    // Run after all plugins are registered
  },

  config: {
    default: {
      // Default configuration values
      apiKey: '',
      enabled: true,
    },
    validator(config) {
      if (!config.apiKey) {
        throw new Error('Plugin requires apiKey configuration');
      }
    },
  },

  contentTypes: require('./content-types'),
  controllers: require('./controllers'),
  routes: require('./routes'),
  services: require('./services'),
  middlewares: require('./middlewares'),
  policies: require('./policies'),
};
```

### Plugin Controller

```javascript
// src/plugins/my-plugin/server/controllers/my-controller.js
module.exports = ({ strapi }) => ({
  async index(ctx) {
    const data = await strapi
      .plugin('my-plugin')
      .service('myService')
      .getAll();

    ctx.body = { data };
  },

  async findOne(ctx) {
    const { id } = ctx.params;
    const data = await strapi
      .plugin('my-plugin')
      .service('myService')
      .findOne(id);

    ctx.body = { data };
  },
});
```

### Plugin Service

```javascript
// src/plugins/my-plugin/server/services/my-service.js
module.exports = ({ strapi }) => ({
  async getAll() {
    return strapi.documents('plugin::my-plugin.my-content-type').findMany();
  },

  async findOne(documentId) {
    return strapi.documents('plugin::my-plugin.my-content-type').findOne({
      documentId,
    });
  },

  getConfig() {
    return strapi.config.get('plugin::my-plugin');
  },
});
```

### Plugin Routes

```javascript
// src/plugins/my-plugin/server/routes/index.js
module.exports = [
  {
    method: 'GET',
    path: '/',
    handler: 'myController.index',
    config: {
      policies: [],
      auth: false,
    },
  },
  {
    method: 'GET',
    path: '/:id',
    handler: 'myController.findOne',
    config: {
      policies: [],
    },
  },
];
```

Plugin routes are prefixed with `/api/<plugin-name>/` automatically.

### Plugin Content Types

```json
// src/plugins/my-plugin/server/content-types/my-content-type/schema.json
{
  "kind": "collectionType",
  "collectionName": "my_plugin_items",
  "info": {
    "singularName": "item",
    "pluralName": "items",
    "displayName": "Plugin Item"
  },
  "options": {
    "draftAndPublish": false
  },
  "attributes": {
    "name": {
      "type": "string",
      "required": true
    },
    "data": {
      "type": "json"
    }
  }
}
```

## Admin Panel API

### Registration

```javascript
// src/plugins/my-plugin/admin/src/index.js
export default {
  register(app) {
    // Register plugin in the admin panel
    app.addMenuLink({
      to: `/plugins/my-plugin`,
      icon: PluginIcon,
      intlLabel: {
        id: `${pluginId}.plugin.name`,
        defaultMessage: 'My Plugin',
      },
      permissions: [],
    });
  },

  bootstrap(app) {
    // Runs after all plugins are registered
  },
};
```

### Custom Fields

Plugins can register custom field types:

```javascript
// In register()
app.customFields.register({
  name: 'color-picker',
  pluginId: 'my-plugin',
  type: 'string',
  intlLabel: {
    id: 'my-plugin.color-picker.label',
    defaultMessage: 'Color Picker',
  },
  components: {
    Input: async () => import('./components/ColorPickerInput'),
  },
});
```

## MCP Server Extension

Plugins can register tools for AI clients via Strapi's MCP service:

```javascript
// In register()
strapi.ai.mcp.registerTool({
  name: 'search-products',
  description: 'Search products by name or category',
  inputSchema: {
    type: 'object',
    properties: {
      query: { type: 'string' },
    },
  },
  handler: async ({ query }) => {
    return strapi.documents('api::product.product').findMany({
      filters: { name: { $containsi: query } },
    });
  },
});
```

## Publishing Plugins

### To npm

```bash
cd src/plugins/my-plugin
npm publish
```

### Version Compatibility

Release Strapi 5 plugins as a different major version to distinguish from v4-compatible versions.

### Marketplace Submission

Submit plugins to the Strapi Marketplace at `market.strapi.io` for community distribution.

## Accessing Plugin APIs

```javascript
// Access plugin service
strapi.plugin('my-plugin').service('myService').method();

// Access plugin controller
strapi.plugin('my-plugin').controller('myController');

// Access plugin config
strapi.config.get('plugin::my-plugin');
strapi.config.get('plugin::my-plugin.apiKey');
```

## Common Pitfalls

- **Plugin content type UIDs** use `plugin::` prefix — `plugin::my-plugin.item`, not `api::`
- **Plugin routes are auto-prefixed** with `/api/<plugin-name>/` — don't add the prefix manually
- **Strapi 5 plugins require a different major version** than v4 plugins — use major version bump
- **Local plugins must be registered** in `config/plugins.js` with `resolve` pointing to the directory
- **Plugin config validator runs at startup** — invalid config prevents server from starting
- **Admin panel changes require rebuild** — run `npm run build` after modifying admin UI code
- **Custom fields must be registered in `register()`** not `bootstrap()` — order matters
