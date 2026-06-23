# Turso Platform API

> Source: [docs.turso.tech/api-reference](https://docs.turso.tech/api-reference/introduction)

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Database Management](#database-management)
- [Group Management](#group-management)
- [Token Management](#token-management)
- [Multi-Tenancy Pattern](#multi-tenancy-pattern)
- [TypeScript SDK](#typescript-sdk)
- [Common Pitfalls](#common-pitfalls)

## Overview

The Turso Platform API provides programmatic control over databases, groups, tokens, and organizations. Use it for:

- Multi-tenant architectures (database-per-user)
- CI/CD automation (database branching per PR)
- Platform/reseller integrations
- Programmatic database provisioning

**Base URL**: `https://api.turso.tech`

## Authentication

All API requests require a Platform API token (different from database auth tokens).

### Create a Platform Token

```bash
# Via CLI
turso auth api-tokens mint my-platform-token

# Via API
curl -X POST https://api.turso.tech/v1/auth/api-tokens/my-token \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

### Using the Token

```bash
curl https://api.turso.tech/v1/organizations \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

## Database Management

### List Databases

```bash
curl https://api.turso.tech/v1/organizations/{org}/databases \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

### Create Database

```bash
curl -X POST https://api.turso.tech/v1/organizations/{org}/databases \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "user-db-12345",
    "group": "default"
  }'
```

### Create from Seed (Branching)

```bash
curl -X POST https://api.turso.tech/v1/organizations/{org}/databases \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "staging-branch",
    "group": "default",
    "seed": {
      "type": "database",
      "name": "production-db"
    }
  }'
```

### Retrieve Database

```bash
curl https://api.turso.tech/v1/organizations/{org}/databases/{db-name} \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

Response includes: `name`, `hostname`, `group`, `regions`, `primaryRegion`, `dbId`.

### Delete Database

```bash
curl -X DELETE https://api.turso.tech/v1/organizations/{org}/databases/{db-name} \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

### Database Stats

```bash
curl https://api.turso.tech/v1/organizations/{org}/databases/{db-name}/stats \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

Returns top queries, row counts, and performance metrics.

### Upload a SQLite File as Database

```bash
curl -X POST https://api.turso.tech/v1/organizations/{org}/databases/{db-name}/upload \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN" \
  -F "file=@local.db"
```

## Group Management

### Create Group

```bash
curl -X POST https://api.turso.tech/v1/organizations/{org}/groups \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "us-prod",
    "location": "iad",
    "extensions": "all"
  }'
```

### List Groups

```bash
curl https://api.turso.tech/v1/organizations/{org}/groups \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

### Add Replica Location

```bash
curl -X POST https://api.turso.tech/v1/organizations/{org}/groups/{group}/locations/{location} \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

### Delete Group

```bash
curl -X DELETE https://api.turso.tech/v1/organizations/{org}/groups/{group} \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

## Token Management

### Create Database Token

```bash
curl -X POST https://api.turso.tech/v1/organizations/{org}/databases/{db}/auth/tokens \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "permissions": {
      "read_attach": { "databases": ["*"] }
    },
    "authorization": "read-only"
  }'
```

### Create Group Token

```bash
curl -X POST https://api.turso.tech/v1/organizations/{org}/groups/{group}/auth/tokens \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

### Invalidate All Tokens

```bash
curl -X POST https://api.turso.tech/v1/organizations/{org}/databases/{db}/auth/rotate \
  -H "Authorization: Bearer $TURSO_PLATFORM_TOKEN"
```

## Multi-Tenancy Pattern

Database-per-user architecture using the Platform API:

```typescript
import { createClient } from "@tursodatabase/api";

const turso = createClient({
  org: process.env.TURSO_ORG!,
  token: process.env.TURSO_PLATFORM_TOKEN!,
});

// On user signup: create a dedicated database
async function onUserSignup(userId: string) {
  const db = await turso.databases.create(`user-${userId}`, {
    group: "default",
  });

  // Apply schema
  const token = await turso.databases.createToken(`user-${userId}`);

  const client = createClient({
    url: `libsql://user-${userId}-${process.env.TURSO_ORG}.turso.io`,
    authToken: token.jwt,
  });

  await client.batch([
    "CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)",
    "CREATE TABLE documents (id INTEGER PRIMARY KEY, title TEXT, content TEXT)",
  ], "write");

  return { dbUrl: db.hostname, token: token.jwt };
}

// On user request: connect to their database
async function getUserClient(userId: string) {
  const token = await turso.databases.createToken(`user-${userId}`, {
    expiration: "1h",
  });

  return createClient({
    url: `libsql://user-${userId}-${process.env.TURSO_ORG}.turso.io`,
    authToken: token.jwt,
  });
}

// On user delete: destroy their database
async function onUserDelete(userId: string) {
  await turso.databases.delete(`user-${userId}`);
}
```

### CI/CD Branch-per-PR Pattern

```yaml
# .github/workflows/preview.yml
name: Preview Database
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  create-preview:
    runs-on: ubuntu-latest
    steps:
      - name: Create branch database
        run: |
          DB_NAME="pr-${{ github.event.number }}"
          curl -X POST "https://api.turso.tech/v1/organizations/$ORG/databases" \
            -H "Authorization: Bearer ${{ secrets.TURSO_PLATFORM_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d "{\"name\": \"$DB_NAME\", \"group\": \"default\", \"seed\": {\"type\": \"database\", \"name\": \"production\"}}"
```

## TypeScript SDK

```bash
npm install @tursodatabase/api
```

```typescript
import { createClient } from "@tursodatabase/api";

const turso = createClient({
  org: "my-org",
  token: process.env.TURSO_PLATFORM_TOKEN!,
});

// List databases
const dbs = await turso.databases.list();

// Create database
const db = await turso.databases.create("my-new-db", { group: "default" });

// Generate scoped token
const token = await turso.databases.createToken("my-new-db", {
  expiration: "24h",
  authorization: "read-only",
});

// Delete database
await turso.databases.delete("my-new-db");

// Get closest region
const region = await turso.locations.closest();
```

## Common Pitfalls

1. **Platform token vs database token** — Platform tokens manage infrastructure (create/delete databases); database tokens access data (SELECT/INSERT). Don't mix them
2. **Database naming** — Names must be globally unique within your organization. Use prefixes like `user-`, `pr-`, `staging-` for namespacing
3. **Group required** — Every database must belong to a group. Create groups before databases
4. **Quota limits** — Each plan has database count limits. Monitor with the usage endpoint
5. **Token expiration** — Short-lived tokens (1h) are safer for user-facing apps. Platform tokens should be long-lived but stored securely
6. **Branch cleanup** — Preview databases from CI/CD should be destroyed when the PR closes. Add a cleanup job
