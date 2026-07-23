# Strapi — Configuration

> Source: https://docs.strapi.io/cms/configurations

## Table of Contents

- [Configuration Directory](#configuration-directory)
- [Server Configuration](#server-configuration)
- [Database Configuration](#database-configuration)
- [Admin Panel Configuration](#admin-panel-configuration)
- [Middleware Configuration](#middleware-configuration)
- [Plugin Configuration](#plugin-configuration)
- [API Configuration](#api-configuration)
- [Environment Variables](#environment-variables)
- [Environment-Specific Config](#environment-specific-config)
- [Cron Jobs](#cron-jobs)
- [Lifecycle Functions](#lifecycle-functions)
- [Common Pitfalls](#common-pitfalls)

## Configuration Directory

All configuration files live in `/config`:

```
config/
├── admin.js          # Admin panel, auth, API tokens
├── api.js            # REST API settings
├── database.js       # Database connection
├── middlewares.js     # Global middleware stack
├── plugins.js        # Plugin configuration
├── server.js         # Host, port, cron, proxy
├── typescript.js     # TypeScript auto-generation
└── env/
    ├── production/
    │   ├── database.js
    │   └── server.js
    └── staging/
        └── database.js
```

## Server Configuration

```javascript
// config/server.js
module.exports = ({ env }) => ({
  host: env('HOST', '0.0.0.0'),
  port: env.int('PORT', 1337),
  url: env('PUBLIC_URL', 'http://localhost:1337'),
  proxy: {
    enabled: env.bool('IS_PROXIED', false),
    // Trust the X-Forwarded-* headers
  },
  app: {
    keys: env.array('APP_KEYS', ['key1', 'key2']),
  },
  cron: {
    enabled: env.bool('CRON_ENABLED', false),
  },
  dirs: {
    public: './public',
  },
});
```

## Database Configuration

### Supported Databases

| Database | Recommended | Minimum |
|----------|------------|---------|
| PostgreSQL | 17.0 | 14.0 |
| MySQL | 8.4 | 8.0 |
| MariaDB | 11.4 | 10.3 |
| SQLite | 3 | 3 |

### PostgreSQL

```javascript
// config/database.js
module.exports = ({ env }) => ({
  connection: {
    client: 'postgres',
    connection: {
      host: env('DATABASE_HOST', '127.0.0.1'),
      port: env.int('DATABASE_PORT', 5432),
      database: env('DATABASE_NAME', 'strapi'),
      user: env('DATABASE_USERNAME', 'strapi'),
      password: env('DATABASE_PASSWORD', ''),
      ssl: env.bool('DATABASE_SSL', false) && {
        rejectUnauthorized: env.bool('DATABASE_SSL_SELF', false),
      },
      schema: env('DATABASE_SCHEMA', 'public'),
    },
    pool: {
      min: env.int('DATABASE_POOL_MIN', 2),
      max: env.int('DATABASE_POOL_MAX', 10),
      acquireTimeoutMillis: 60000,
      idleTimeoutMillis: 30000,
    },
    debug: false,
  },
  settings: {
    forceMigration: true,
    runMigrations: true,
  },
});
```

### MySQL

```javascript
module.exports = ({ env }) => ({
  connection: {
    client: 'mysql',
    connection: {
      host: env('DATABASE_HOST', '127.0.0.1'),
      port: env.int('DATABASE_PORT', 3306),
      database: env('DATABASE_NAME', 'strapi'),
      user: env('DATABASE_USERNAME', 'strapi'),
      password: env('DATABASE_PASSWORD', ''),
    },
  },
});
```

### SQLite (Default)

```javascript
module.exports = ({ env }) => ({
  connection: {
    client: 'sqlite',
    connection: {
      filename: env('DATABASE_FILENAME', '.tmp/data.db'),
    },
    useNullAsDefault: true,
  },
});
```

### Connection String

```javascript
module.exports = ({ env }) => ({
  connection: {
    client: 'postgres',
    connection: {
      connectionString: env('DATABASE_URL'),
    },
  },
});
```

### Docker Pool Settings

Set `min: 0` to prevent idle connection issues in containers:

```javascript
pool: { min: 0, max: 10 }
```

## Admin Panel Configuration

```javascript
// config/admin.js
module.exports = ({ env }) => ({
  auth: {
    secret: env('ADMIN_JWT_SECRET'),
  },
  apiToken: {
    salt: env('API_TOKEN_SALT'),
  },
  transfer: {
    token: {
      salt: env('TRANSFER_TOKEN_SALT'),
    },
  },
  // Customize admin panel URL path
  url: '/admin',
  // Auto-open browser on dev start
  autoOpen: false,
});
```

## Middleware Configuration

The middleware stack defines the order of global processing:

```javascript
// config/middlewares.js
module.exports = [
  'strapi::logger',
  'strapi::errors',
  'strapi::security',
  'strapi::cors',
  'strapi::poweredBy',
  'strapi::query',
  'strapi::body',
  'strapi::session',
  'strapi::favicon',
  'strapi::public',
];
```

### Customizing Built-in Middleware

```javascript
module.exports = [
  'strapi::logger',
  'strapi::errors',
  {
    name: 'strapi::security',
    config: {
      contentSecurityPolicy: {
        useDefaults: true,
        directives: {
          'connect-src': ["'self'", 'https:'],
          'img-src': ["'self'", 'data:', 'blob:', 'cdn.example.com'],
          'media-src': ["'self'", 'data:', 'blob:', 'cdn.example.com'],
          upgradeInsecureRequests: null,
        },
      },
    },
  },
  {
    name: 'strapi::cors',
    config: {
      origin: ['http://localhost:3000', 'https://myapp.com'],
      methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
      headers: ['Content-Type', 'Authorization', 'Origin', 'Accept'],
      keepHeadersOnError: true,
    },
  },
  {
    name: 'strapi::body',
    config: {
      formLimit: '256mb',
      jsonLimit: '256mb',
      textLimit: '256mb',
    },
  },
  'strapi::poweredBy',
  'strapi::query',
  'strapi::session',
  'strapi::favicon',
  'strapi::public',
];
```

## Plugin Configuration

```javascript
// config/plugins.js
module.exports = ({ env }) => ({
  // GraphQL plugin
  graphql: {
    config: {
      endpoint: '/graphql',
      shadowCRUD: true,
      playgroundAlways: false,
      defaultLimit: 25,
      maxLimit: 100,
      apolloServer: {
        tracing: false,
      },
    },
  },

  // Users & Permissions
  'users-permissions': {
    config: {
      jwt: { expiresIn: '7d' },
      ratelimit: {
        enabled: true,
        interval: 60000,
        max: 10,
      },
    },
  },

  // Upload / Media Library
  upload: {
    config: {
      sizeLimit: 250 * 1024 * 1024,
      breakpoints: {
        xlarge: 1920,
        large: 1000,
        medium: 750,
        small: 500,
      },
    },
  },

  // Email
  email: {
    config: {
      provider: 'sendgrid',
      providerOptions: {
        apiKey: env('SENDGRID_API_KEY'),
      },
      settings: {
        defaultFrom: 'noreply@example.com',
        defaultReplyTo: 'support@example.com',
      },
    },
  },

  // Disable a plugin
  'some-plugin': {
    enabled: false,
  },
});
```

## API Configuration

```javascript
// config/api.js
module.exports = ({ env }) => ({
  rest: {
    defaultLimit: 25,
    maxLimit: 100,
    withCount: true,       // include total count in pagination
    strictParams: false,    // reject unknown query params when true
  },
  documents: {
    strictParams: false,    // strict validation for Document Service
  },
});
```

## Environment Variables

### The `env` Helper

Strapi provides typed environment variable helpers:

```javascript
env('VAR_NAME')              // string
env('VAR_NAME', 'default')   // string with default
env.int('PORT', 1337)        // integer
env.float('RATE', 0.5)       // float
env.bool('DEBUG', false)     // boolean
env.json('CONFIG')           // parsed JSON
env.array('KEYS')            // comma-separated to array
```

### Essential Environment Variables

```bash
# .env
HOST=0.0.0.0
PORT=1337

# Security (auto-generated on project creation)
APP_KEYS=key1,key2,key3,key4
API_TOKEN_SALT=random-salt
ADMIN_JWT_SECRET=random-secret
JWT_SECRET=random-secret
TRANSFER_TOKEN_SALT=random-salt

# Database
DATABASE_CLIENT=sqlite
DATABASE_FILENAME=.tmp/data.db
# Or for PostgreSQL:
# DATABASE_CLIENT=postgres
# DATABASE_HOST=127.0.0.1
# DATABASE_PORT=5432
# DATABASE_NAME=strapi
# DATABASE_USERNAME=strapi
# DATABASE_PASSWORD=password
```

## Environment-Specific Config

Place environment-specific overrides in `config/env/<environment>/`:

```javascript
// config/env/production/server.js
module.exports = ({ env }) => ({
  url: env('PUBLIC_URL', 'https://api.myapp.com'),
  proxy: { enabled: true },
});

// config/env/production/database.js
module.exports = ({ env }) => ({
  connection: {
    client: 'postgres',
    connection: {
      connectionString: env('DATABASE_URL'),
    },
    pool: { min: 2, max: 20 },
  },
});
```

The `NODE_ENV` environment variable determines which directory is loaded.

## Cron Jobs

```javascript
// config/server.js
module.exports = ({ env }) => ({
  cron: { enabled: true },
});
```

```javascript
// config/cron-tasks.js
module.exports = {
  // Run every day at midnight
  '0 0 * * *': async ({ strapi }) => {
    const outdated = await strapi.documents('api::article.article').findMany({
      filters: { publishedAt: { $lt: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000) } },
    });
    strapi.log.info(`Found ${outdated.results.length} articles older than 1 year`);
  },

  // Run every hour
  '0 * * * *': {
    task: async ({ strapi }) => {
      await strapi.service('api::cache.cache').invalidate();
    },
    options: {
      tz: 'America/New_York',
    },
  },
};
```

## Lifecycle Functions

Application-level hooks in `src/index.js`:

```javascript
// src/index.js
module.exports = {
  // Runs before all other lifecycle methods
  register({ strapi }) {
    // Register custom fields, Document Service middlewares
  },

  // Runs after register, before server starts
  async bootstrap({ strapi }) {
    // Seed data, start background services
    const count = await strapi.documents('api::category.category').count();
    if (count === 0) {
      await strapi.documents('api::category.category').create({
        data: { name: 'Uncategorized' },
      });
    }
  },

  // Runs when the server shuts down
  async destroy({ strapi }) {
    // Cleanup resources
  },
};
```

## Common Pitfalls

- **MongoDB is not supported** — Strapi only works with SQL databases
- **Cloud-native databases** (Aurora, Cloud SQL) are not supported
- **Environment variables in `.env`** are loaded automatically — no need for `dotenv`
- **Pool `min` should be `0` in Docker** to prevent idle connection failures
- **`APP_KEYS` must contain at least one value** — used for session encryption
- **`PUBLIC_URL` must be set in production** — used for generating asset URLs
- **Cron jobs require `cron.enabled: true`** in server config — disabled by default
- **Environment-specific configs merge with base** — they override matching keys, not replace entirely
