# Turso Authentication & Security

> Source: [docs.turso.tech/sdk/authorization](https://docs.turso.tech/sdk/authorization)

## Table of Contents
- [Token Types](#token-types)
- [Creating Tokens](#creating-tokens)
- [Fine-Grained Permissions](#fine-grained-permissions)
- [JWKS Integration](#jwks-integration)
- [Encryption at Rest](#encryption-at-rest)
- [Network Security](#network-security)
- [Common Pitfalls](#common-pitfalls)

## Token Types

Turso uses JWT-based tokens at multiple scoping levels:

| Token Type | Scope | Created Via |
|-----------|-------|-------------|
| Platform API Token | Manage all infrastructure | `turso auth api-tokens mint` |
| Group Token | Access all databases in a group | `turso group tokens create <group>` |
| Database Token | Access a specific database | `turso db tokens create <db>` |
| Read-Only Token | Query-only access | `--read-only` flag |
| Fine-Grained Token | Table + action specific | `-p <table>:<actions>` syntax |
| Time-Limited Token | Auto-expiring | `--expiration` flag |

## Creating Tokens

### Database Tokens

```bash
# Full access token
turso db tokens create my-database

# Read-only token
turso db tokens create my-database --read-only

# Time-limited (expires in 7 days)
turso db tokens create my-database --expiration 7d

# Supported expiration formats: 1h, 7d, 30d, 1y, never
```

### Group Tokens

```bash
# Access all databases in the group
turso group tokens create my-group

# Read-only group token
turso group tokens create my-group --read-only
```

### Platform API Tokens

```bash
# Mint a new API token
turso auth api-tokens mint my-ci-token

# List existing tokens
turso auth api-tokens list

# Revoke a token
turso auth api-tokens revoke my-ci-token
```

### Invalidate All Tokens

```bash
# Invalidate all tokens for a database
turso db tokens invalidate my-database

# Invalidate all tokens for a group
turso group tokens invalidate my-group
```

## Fine-Grained Permissions

Control access at the table and action level:

```bash
# Read all tables, insert into comments only
turso db tokens create mydb \
  -p all:data_read \
  -p comments:data_add

# Read-only access to users table
turso db tokens create mydb \
  -p users:data_read

# Full CRUD on orders, read-only on products
turso db tokens create mydb \
  -p orders:data_read,data_add,data_update,data_delete \
  -p products:data_read
```

### Available Permissions

| Permission | Description |
|-----------|-------------|
| `data_read` | SELECT queries |
| `data_add` | INSERT statements |
| `data_update` | UPDATE statements |
| `data_delete` | DELETE statements |
| `schema_read` | Read schema information |
| `schema_update` | ALTER TABLE, CREATE TABLE, etc. |

### Using Tokens in SDKs

```typescript
import { createClient } from "@libsql/client";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!, // Any token type works here
});
```

## JWKS Integration

Use external auth providers (Clerk, Auth0, Firebase) to issue database tokens via JWKS:

### Configure JWKS Endpoint

```bash
turso group update my-group --jwks-url "https://your-auth-provider.com/.well-known/jwks.json"
```

### Mint Tokens from Your Auth Provider

```typescript
// Example with Clerk
import { auth } from "@clerk/nextjs/server";

export async function getTursoClient() {
  const { getToken } = await auth();

  // Clerk mints a JWT that Turso validates against the JWKS endpoint
  const token = await getToken({ template: "turso" });

  return createClient({
    url: process.env.TURSO_DATABASE_URL!,
    authToken: token!,
  });
}
```

### JWT Claims for Turso

The JWT must include these claims:

```json
{
  "sub": "user_123",
  "iat": 1234567890,
  "exp": 1234571490,
  "turso": {
    "permissions": {
      "data_read": { "tables": ["*"] },
      "data_add": { "tables": ["user_settings"] }
    }
  }
}
```

## Encryption at Rest

Turso supports page-level encryption where each 4KB page is encrypted individually with a unique nonce using AEAD algorithms.

### Supported Ciphers

| Cipher Family | Variants | Key Size |
|--------------|----------|----------|
| **AEGIS** (recommended) | `aegis128l`, `aegis128x2`, `aegis128x4` | 128-bit |
| **AEGIS** (recommended) | `aegis256`, `aegis256x2`, `aegis256x4` | 256-bit |
| **AES-GCM** (NIST-approved) | `aes128gcm` | 128-bit |
| **AES-GCM** (NIST-approved) | `aes256gcm` | 256-bit |

### Key Generation

```bash
# 256-bit key (for AEGIS-256, AES-256-GCM)
openssl rand -hex 32

# 128-bit key (for AEGIS-128L, AES-128-GCM)
openssl rand -hex 16
```

### Enabling Encryption

#### Via CLI

```bash
tursodb --experimental-encryption "file:encrypted.db?cipher=aegis256&hexkey=YOUR_HEX_KEY"
```

#### Via TypeScript SDK

```typescript
import { connect } from "@tursodatabase/database";

const db = await connect("encrypted.db", {
  encryption: {
    cipher: "aegis256",
    hexkey: "b1bbfda4f589dc9daaf004fe21111e00dc00c98237102f5c7002a5669fc76327",
  },
});
```

### Performance Impact

| Operation | Overhead |
|-----------|----------|
| Reads | ~6% |
| Writes | ~14% |
| Mixed workload | ~1-3% |

### Encryption Constraints

- Keys are never stored on disk — losing the key means permanent data loss
- The first 100 bytes of the database header remain unencrypted
- Currently experimental (`--experimental-encryption` flag)
- No key rotation yet (planned)
- No migration from unencrypted to encrypted databases yet (planned)

## Network Security

### IP Allow Rules

Restrict database access to specific IP addresses:

```bash
# Set allow rules
turso db config allow-rules set my-database --ip 203.0.113.0/24

# Show current rules
turso db config allow-rules show my-database

# Clear all rules (open access)
turso db config allow-rules clear my-database
```

### Private Endpoints

For enterprise plans, configure private endpoints to keep traffic off the public internet:

```bash
# Configure via Turso dashboard or Platform API
```

### BYOK Encryption (Cloud)

Turso Cloud supports Bring-Your-Own-Key encryption for data at rest in managed databases.

## Common Pitfalls

1. **Local development doesn't need tokens** — Tokens are only required for remote connections. `file:local.db` works without auth
2. **Token type confusion** — Platform tokens manage infrastructure; database/group tokens access data. A platform token cannot query a database
3. **JWKS setup** — The JWKS URL is set at the group level, not the database level. All databases in the group share the same JWKS configuration
4. **Key management** — Encryption keys are never recoverable. Store them in a secrets manager (Vault, AWS Secrets Manager), not in code or env files on disk
5. **Token expiration** — Default tokens don't expire. Always set `--expiration` for production tokens
6. **Fine-grained granularity** — Permissions are per-table, not per-row. For row-level security, implement it in your application logic
