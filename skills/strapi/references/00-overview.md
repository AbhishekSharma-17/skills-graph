# Strapi — Overview & Getting Started

> Source: https://docs.strapi.io/cms/getting-started

## What is Strapi?

Strapi is an open-source headless CMS that gives developers full control over their content API while providing editors a customizable admin panel. It generates REST and GraphQL APIs automatically from content type definitions, supports role-based access control, and runs on Node.js with SQL databases.

### When to Use Strapi

- Building content-driven applications (blogs, e-commerce, portfolios, documentation sites)
- Need a self-hosted CMS with full data ownership
- Want auto-generated REST and GraphQL APIs from content models
- Need a customizable admin panel for non-technical editors
- Building multi-language content with internationalization
- Need draft/publish workflows and editorial review processes
- Want to decouple content management from frontend presentation

### When NOT to Use Strapi

- Need a simple static site (use a flat-file CMS or Markdown instead)
- Need MongoDB or NoSQL support (Strapi only supports SQL databases)
- Need a full-stack framework with frontend rendering (use Next.js, Nuxt, etc. as frontends)
- Need cloud-native database support (Aurora, Cloud SQL not supported)

## Prerequisites

| Requirement | Supported Versions |
|---|---|
| Node.js | v22, v24, v26 (LTS only — odd versions unsupported) |
| Package Manager | npm v6+, pnpm, or Corepack |
| Python | Required for SQLite |
| Databases | PostgreSQL 14+, MySQL 8+, MariaDB 10.3+, SQLite 3 |

## Installation

### Create a New Project

```bash
npx create-strapi@latest my-project
```

The CLI prompts for Strapi Cloud authentication (optional, provides 30-day Growth trial), then scaffolds the project with SQLite by default.

### Start Development Server

```bash
cd my-project
npm run develop
```

The admin panel opens at `http://localhost:1337/admin`. Create the first admin user on first launch.

### Use a Specific Database

```bash
# PostgreSQL
DATABASE_CLIENT=postgres \
DATABASE_HOST=127.0.0.1 \
DATABASE_PORT=5432 \
DATABASE_NAME=strapi \
DATABASE_USERNAME=strapi \
DATABASE_PASSWORD=strapi \
npx create-strapi@latest my-project
```

## Project Structure

```
my-project/
├── config/              # Server, database, middleware, plugin configs
│   ├── admin.js         # Admin panel configuration
│   ├── api.js           # REST API settings
│   ├── database.js      # Database connection
│   ├── middlewares.js    # Global middleware stack
│   ├── plugins.js       # Plugin configuration
│   └── server.js        # Host, port, cron settings
├── database/            # SQLite file and migrations
├── public/              # Static assets served by Strapi
├── src/
│   ├── admin/           # Admin panel customizations
│   ├── api/             # Content-type APIs (models, controllers, services, routes)
│   │   └── restaurant/
│   │       ├── content-types/
│   │       │   └── restaurant/
│   │       │       └── schema.json
│   │       ├── controllers/
│   │       ├── routes/
│   │       └── services/
│   ├── components/      # Reusable component schemas
│   ├── middlewares/      # Custom global middlewares
│   ├── plugins/         # Local plugin code
│   └── index.js         # register(), bootstrap(), destroy() lifecycle hooks
├── .env                 # Environment variables
├── package.json
└── tsconfig.json        # TypeScript configuration (if TS project)
```

## Core Architecture

```
Client (React, Vue, Mobile)
    │
    ├── REST API  (/api/*)
    │       │
    │       ├── Routes → Policies → Middlewares → Controllers → Services
    │       │
    └── GraphQL API  (/graphql)
            │
            ├── Resolvers → Services
            │
            └── Document Service API (backend CRUD layer)
                    │
                    └── Database (PostgreSQL / MySQL / SQLite)
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Collection Type** | Content type with multiple entries (e.g., Articles, Products) |
| **Single Type** | Content type with one entry (e.g., Homepage, About Page) |
| **Component** | Reusable group of fields (e.g., SEO metadata, Address) |
| **Dynamic Zone** | Flexible area accepting different components per entry |
| **Document** | An entity spanning all locales and draft/published states under one `documentId` |

### CLI Commands

```bash
npm run develop          # Start dev server with auto-reload
npm run start            # Start production server
npm run build            # Build admin panel for production
npm run strapi generate  # Interactive generator (content-type, controller, service, etc.)
```

## TypeScript Support

Strapi v5 supports TypeScript natively. Enable auto-generation of types:

```typescript
// config/typescript.ts
export default ({ env }) => ({
  autogenerate: true,
});
```

Types are generated into `types/` on server restart, providing autocompletion for content types, services, and controllers.

## Quick Example: Creating a Blog API

1. Start the project: `npm run develop`
2. Open admin panel: `http://localhost:1337/admin`
3. Create a "Post" collection type with fields: Title (text), Content (rich text), Slug (UID), Cover (media)
4. Add entries via the Content Manager
5. Set public permissions: Settings → Users & Permissions → Public → Enable `find` and `findOne` for Post
6. Access the API: `GET http://localhost:1337/api/posts`

## Common Pitfalls

- **Odd Node.js versions** are not supported (v23, v25 will fail)
- **MongoDB is not supported** — Strapi requires SQL databases only
- **Admin user** must be created on first launch — there's no default admin account
- **Content types are private by default** — you must explicitly grant public permissions
- **Local and Cloud databases are separate** — data doesn't auto-sync between environments
- **`npm run develop`** is for development only — use `npm run build && npm start` for production
