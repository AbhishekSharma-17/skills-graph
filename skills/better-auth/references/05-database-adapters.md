# Better Auth — Database & Adapters

> Source: [better-auth.com/docs/concepts/database](https://www.better-auth.com/docs/concepts/database) | Version: 1.5.6

## Table of Contents

- [Overview](#overview)
- [Core Schema](#core-schema)
- [Database Adapters](#database-adapters)
- [CLI Tools](#cli-tools)
- [Custom Schema Configuration](#custom-schema-configuration)
- [Extending Schemas](#extending-schemas)
- [ID Generation](#id-generation)
- [Database Hooks](#database-hooks)
- [Secondary Storage (Redis)](#secondary-storage-redis)
- [Experimental Joins](#experimental-joins)
- [Common Pitfalls](#common-pitfalls)

## Overview

Better Auth stores users, sessions, accounts, and verification data in a database. It supports multiple databases through adapters: built-in Kysely (SQLite, PostgreSQL, MySQL), Prisma, Drizzle ORM, and MongoDB.

## Core Schema

Four required tables:

### User Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (PK) | Unique identifier |
| `name` | string | Display name |
| `email` | string | Email address |
| `emailVerified` | boolean | Verification status |
| `image` | string? | Avatar URL |
| `createdAt` | datetime | Creation timestamp |
| `updatedAt` | datetime | Last update timestamp |

### Session Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (PK) | Unique identifier |
| `userId` | string (FK) | References user.id |
| `token` | string | Session token (cookie value) |
| `expiresAt` | datetime | Expiration timestamp |
| `ipAddress` | string? | Client IP |
| `userAgent` | string? | Browser info |
| `createdAt` | datetime | Creation timestamp |
| `updatedAt` | datetime | Last update timestamp |

### Account Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (PK) | Unique identifier |
| `userId` | string (FK) | References user.id |
| `accountId` | string | Provider-specific user ID |
| `providerId` | string | Provider name (e.g., "github") |
| `accessToken` | string? | OAuth access token |
| `refreshToken` | string? | OAuth refresh token |
| `accessTokenExpiresAt` | datetime? | Token expiration |
| `refreshTokenExpiresAt` | datetime? | Refresh token expiration |
| `scope` | string? | OAuth scopes |
| `idToken` | string? | OIDC ID token |
| `password` | string? | Hashed password (email/password auth) |
| `createdAt` | datetime | Creation timestamp |
| `updatedAt` | datetime | Last update timestamp |

### Verification Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (PK) | Unique identifier |
| `identifier` | string | What's being verified |
| `value` | string | Verification token/code |
| `expiresAt` | datetime | Expiration timestamp |
| `createdAt` | datetime | Creation timestamp |
| `updatedAt` | datetime | Last update timestamp |

## Database Adapters

### Built-in Kysely (Direct Connection)

```typescript
// SQLite
import Database from "better-sqlite3";
export const auth = betterAuth({
  database: new Database("./sqlite.db"),
});

// PostgreSQL
import { Pool } from "pg";
export const auth = betterAuth({
  database: new Pool({ connectionString: process.env.DATABASE_URL }),
});

// MySQL
import { createPool } from "mysql2/promise";
export const auth = betterAuth({
  database: createPool({ uri: process.env.DATABASE_URL }),
});
```

### Prisma Adapter

```typescript
import { prismaAdapter } from "better-auth/adapters/prisma";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();
export const auth = betterAuth({
  database: prismaAdapter(prisma, {
    provider: "postgresql", // or "mysql", "sqlite"
  }),
});
```

### Drizzle Adapter

```typescript
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "./db";

export const auth = betterAuth({
  database: drizzleAdapter(db, {
    provider: "pg", // or "mysql", "sqlite"
  }),
});
```

### MongoDB Adapter

```typescript
import { mongodbAdapter } from "better-auth/adapters/mongodb";
import { MongoClient } from "mongodb";

const client = new MongoClient(process.env.MONGODB_URI!);
const db = client.db("myapp");
export const auth = betterAuth({
  database: mongodbAdapter(db),
});
```

## CLI Tools

```bash
# Interactive migration — creates tables, adds missing columns
npx auth@latest migrate

# Generate schema files for ORM
npx auth@latest generate
# Outputs: Prisma schema additions, Drizzle schema, or raw SQL

# Initialize a new project
npx auth@latest init
```

### Programmatic Migrations (Serverless)

```typescript
import { getMigrations } from "better-auth/db/migration";

const { runMigrations } = await getMigrations(auth);
await runMigrations();
```

## Custom Schema Configuration

Rename tables and columns:

```typescript
export const auth = betterAuth({
  user: {
    modelName: "users",       // Table name
    fields: {
      name: "full_name",      // Column mapping
      email: "email_address",
    },
  },
  session: {
    modelName: "sessions",
  },
});
```

## Extending Schemas

Add custom fields to user or session tables:

```typescript
export const auth = betterAuth({
  user: {
    additionalFields: {
      role: {
        type: "string",
        defaultValue: "user",
        input: true, // Allowed in sign-up body
      },
      plan: {
        type: "string",
        defaultValue: "free",
        input: false, // Server-only, not settable via API
      },
    },
  },
  session: {
    additionalFields: {
      theme: {
        type: "string",
        defaultValue: "light",
      },
    },
  },
});
```

After adding fields, run `npx auth migrate` to update the database.

## ID Generation

```typescript
export const auth = betterAuth({
  advanced: {
    // Let database handle IDs (auto-increment)
    generateId: false,

    // Use UUIDs
    generateId: "uuid",

    // Use serial/auto-increment
    generateId: "serial",

    // Custom generator
    generateId: (options) => {
      if (options.model === "user") return generateCustomId();
      return undefined; // Fall back to default
    },
  },
});
```

## Database Hooks

Execute logic during entity lifecycle events:

```typescript
export const auth = betterAuth({
  databaseHooks: {
    user: {
      create: {
        before: async (user, ctx) => {
          // Validate, modify, or block
          if (user.email.endsWith("@blocked.com")) {
            throw new APIError("BAD_REQUEST", {
              message: "Domain not allowed",
            });
          }
          return { data: { ...user, role: "user" } };
        },
        after: async (user) => {
          // Side effects (send welcome email, etc.)
          await sendWelcomeEmail(user.email);
        },
      },
      update: {
        before: async (user) => {
          return { data: user };
        },
      },
    },
    account: {
      create: {
        before: async (account) => {
          // Encrypt tokens before storage
          const encrypted = { ...account };
          if (account.accessToken) {
            encrypted.accessToken = encrypt(account.accessToken);
          }
          if (account.refreshToken) {
            encrypted.refreshToken = encrypt(account.refreshToken);
          }
          return { data: encrypted };
        },
      },
    },
    session: {
      create: {
        after: async (session) => {
          await logSessionCreated(session);
        },
      },
    },
  },
});
```

- **Before hooks**: Return `{ data: modified }` to change data, throw `APIError` to block
- **After hooks**: For side effects only (logging, notifications)

## Secondary Storage (Redis)

```typescript
// Official Redis package
import { redisStorage } from "@better-auth/redis-storage";
import { Redis } from "ioredis";

const redis = new Redis({ host: "localhost", port: 6379 });

export const auth = betterAuth({
  secondaryStorage: redisStorage({
    client: redis,
    keyPrefix: "better-auth:",
  }),
});

// Upstash Redis (serverless)
import { Redis } from "@upstash/redis";
const redis = new Redis({ url: "...", token: "..." });

export const auth = betterAuth({
  secondaryStorage: {
    get: async (key) => await redis.get(key),
    set: async (key, value, ttl) => {
      if (ttl) await redis.set(key, value, { ex: ttl });
      else await redis.set(key, value);
    },
    delete: async (key) => await redis.del(key),
  },
});
```

## Experimental Joins

Reduce database round-trips (v1.4+):

```typescript
export const auth = betterAuth({
  experimental: { joins: true },
});
```

After enabling, regenerate ORM schemas:

```bash
npx auth@latest generate
```

## Common Pitfalls

1. **Forgetting migrations** — Always run `npx auth migrate` after adding plugins or custom fields.
2. **Token encryption** — Better Auth does NOT encrypt OAuth tokens by default. Use database hooks for encryption.
3. **Prisma adapter provider** — Must match your actual database (e.g., `"postgresql"`, not `"postgres"`).
4. **MongoDB limitations** — Some features (joins, certain queries) have limited MongoDB support.
5. **Serial IDs with UUIDs** — If your ORM expects UUIDs but you set `generateId: "serial"`, you'll get type mismatches.
