# Payload CMS — Overview

> Source: https://payloadcms.com/docs/getting-started/what-is-payload

## What Is Payload

Payload is an open-source, TypeScript-first headless CMS and application framework that installs directly into Next.js applications. Unlike traditional CMS platforms that run as separate services, Payload 3.0 is Next.js-native — the admin panel and HTTP layer are built on top of Next.js itself.

Key characteristics:
- **Code-first configuration** — define your schema in TypeScript, not a GUI
- **Self-hosted** — no vendor lock-in, no subscriptions, runs on your infrastructure
- **Next.js native** — lives in your `/app` folder alongside your frontend
- **Three APIs automatically generated** — Local API, REST API, and GraphQL
- **Full TypeScript support** — auto-generated types from your config
- **40K+ GitHub stars**, 100K+ weekly npm downloads

## When to Use Payload

| Use Case | Fit |
|----------|-----|
| Content-heavy websites with custom frontends | Excellent |
| Multi-tenant SaaS applications | Excellent |
| E-commerce product catalogs | Great |
| Internal tools and admin dashboards | Great |
| Headless API backends | Great |
| Blog/portfolio with minimal content | Overkill — consider Markdown/MDX |
| Static sites with no dynamic content | Not needed |

## Core Concepts

### Collections
Groups of documents sharing a common schema. Each collection gets automatic CRUD APIs and an admin UI panel. Examples: `posts`, `users`, `products`, `media`.

### Globals
Singleton documents for site-wide data. Examples: site settings, navigation menus, footer content. One document per global, no list views.

### Fields
The building blocks of your schema. Payload provides 20+ field types (text, number, relationship, blocks, array, tabs, etc.) with built-in validation, conditional logic, and access control.

### Hooks
Lifecycle functions that execute during document operations. Before/after validate, change, read, and delete — on collections, globals, and individual fields.

### Access Control
Function-based permission system. Returns `true`/`false` for allow/deny, or a query constraint for filtering. Applied at collection, global, and field levels.

### Admin Panel
Auto-generated React admin UI built on Next.js. Fully customizable through component swapping — from individual field labels to entire views.

## Installation

### New Project

```bash
npx create-payload-app@latest my-project
cd my-project
npm run dev
```

The CLI prompts you to select a template and database (MongoDB, Postgres, or SQLite).

### Add to Existing Next.js App

```bash
npm install payload @payloadcms/next @payloadcms/richtext-lexical sharp
# Choose a database adapter
npm install @payloadcms/db-mongodb    # or
npm install @payloadcms/db-postgres   # or
npm install @payloadcms/db-sqlite
```

### Requirements
- Node.js 20.9.0+
- Any JavaScript package manager (pnpm preferred)
- MongoDB, Postgres, or SQLite

## Project Structure

```
my-project/
├── payload.config.ts          # Central configuration
├── app/
│   ├── (frontend)/            # Your frontend routes
│   │   ├── page.tsx
│   │   └── layout.tsx
│   └── (payload)/             # Admin panel routes (auto-generated)
│       └── admin/
│           └── [[...segments]]/
│               └── page.tsx
├── collections/               # Collection configs
│   ├── Users.ts
│   ├── Posts.ts
│   └── Media.ts
├── globals/                   # Global configs
│   └── Settings.ts
├── access/                    # Reusable access control functions
│   └── isAdmin.ts
└── hooks/                     # Reusable hooks
    └── populateCreatedBy.ts
```

## The Payload Config

The central configuration file — typically `payload.config.ts` in the project root:

```typescript
import { buildConfig } from 'payload'
import { mongooseAdapter } from '@payloadcms/db-mongodb'
import { lexicalEditor } from '@payloadcms/richtext-lexical'
import { Posts } from './collections/Posts'
import { Users } from './collections/Users'
import { Media } from './collections/Media'
import { Settings } from './globals/Settings'

export default buildConfig({
  // Database adapter (required)
  db: mongooseAdapter({
    url: process.env.DATABASE_URI!,
  }),

  // Rich text editor
  editor: lexicalEditor(),

  // Collections
  collections: [Users, Posts, Media],

  // Globals
  globals: [Settings],

  // Secret for JWT tokens (required)
  secret: process.env.PAYLOAD_SECRET!,

  // TypeScript output path
  typescript: {
    outputFile: './payload-types.ts',
  },
})
```

## Auto-Generated Types

Payload generates TypeScript types from your config:

```bash
npx payload generate:types
```

This creates a `payload-types.ts` file with interfaces for all collections and globals, used throughout your application for type safety.

## Three APIs

Every collection and global automatically gets:

1. **Local API** — Direct database access in Node.js, no HTTP overhead. The fastest way to query data.
2. **REST API** — Standard HTTP endpoints at `/api/<collection-slug>`. Supports filtering, sorting, pagination.
3. **GraphQL API** — Full GraphQL schema at `/api/graphql`. Auto-generated queries and mutations.

```typescript
// Local API — direct, fast, strongly typed
const posts = await payload.find({
  collection: 'posts',
  where: { status: { equals: 'published' } },
})

// REST API equivalent
// GET /api/posts?where[status][equals]=published

// GraphQL equivalent
// query { Posts(where: { status: { equals: published } }) { docs { title } } }
```

## Common Pitfalls

1. **Forgetting `PAYLOAD_SECRET`** — Required environment variable for JWT signing. Generate a random 32+ char string.
2. **Not installing `sharp`** — Required for image processing. Payload warns but doesn't fail without it.
3. **Circular relationships** — Two collections referencing each other can cause issues. Use `relationTo` carefully and consider using hooks instead.
4. **Large payload configs** — Split collections, globals, hooks, and access functions into separate files. Don't put everything in one config file.
5. **Running migrations on deploy** — Always run `npx payload migrate` before deploying schema changes with Postgres/SQLite.
