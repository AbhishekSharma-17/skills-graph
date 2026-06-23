# Getting Started with Turso

> Source: [docs.turso.tech/quickstart](https://docs.turso.tech/quickstart)

## Table of Contents
- [CLI Setup](#cli-setup)
- [Authentication](#authentication)
- [Creating Databases](#creating-databases)
- [Database Shell](#database-shell)
- [Basic SQL Operations](#basic-sql-operations)
- [Local Development](#local-development)
- [Database Management](#database-management)
- [Groups and Regions](#groups-and-regions)
- [Common Pitfalls](#common-pitfalls)

## CLI Setup

### Installation

```bash
# macOS / Linux
curl -sSfL https://get.tur.so/install.sh | bash

# Windows (PowerShell)
iwr https://get.tur.so/install.ps1 -useb | iex

# Update to latest
turso update

# Verify installation
turso --version
```

### Headless Mode

For CI/CD environments without a browser, set the API token directly:

```bash
export TURSO_API_TOKEN="your-token-here"
```

## Authentication

```bash
# Sign up for a new account
turso auth signup

# Log in (opens browser)
turso auth login

# Check current user
turso auth whoami

# Generate API token for programmatic access
turso auth api-tokens mint my-token

# List API tokens
turso auth api-tokens list

# Revoke a token
turso auth api-tokens revoke my-token

# Log out
turso auth logout
```

## Creating Databases

### Create a Database

```bash
# Create in the default group/region
turso db create my-app

# Create in a specific group
turso db create my-app --group us-east

# Create from an existing SQLite file
turso db create my-app --from-file ./local.db

# Create a branch from an existing database
turso db create my-app-staging --from-db my-app
```

### Get Connection Info

```bash
# Show database URL
turso db show my-app --url
# Output: libsql://my-app-username.turso.io

# Create an auth token for this database
turso db tokens create my-app

# Create a read-only token
turso db tokens create my-app --read-only

# Create a token with expiration
turso db tokens create my-app --expiration 7d

# Create a token with fine-grained permissions
turso db tokens create my-app -p users:data_read -p orders:data_read,data_add
```

## Database Shell

```bash
# Open interactive SQL shell
turso db shell my-app

# Execute a single statement
turso db shell my-app "SELECT * FROM users"

# Open shell for a local database file
turso db shell file:local.db
```

### Shell Commands

```
.tables          — List all tables
.schema <table>  — Show CREATE TABLE statement
.dump            — Export database as SQL
.quit            — Exit the shell
.help            — Show all commands
```

## Basic SQL Operations

### Creating Tables

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### STRICT Tables

```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    balance REAL NOT NULL,
    currency TEXT NOT NULL
) STRICT;
```

STRICT tables enforce column types — attempting to insert a string into an INTEGER column raises an error instead of silently coercing.

### Inserting Data

```sql
INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com');

INSERT INTO posts (user_id, title, content, published)
VALUES (1, 'Hello World', 'My first post', 1);
```

### Querying Data

```sql
-- Basic select
SELECT * FROM users;

-- Filtered query
SELECT * FROM posts WHERE published = 1 ORDER BY created_at DESC;

-- Join
SELECT u.name, p.title, p.created_at
FROM posts p
JOIN users u ON u.id = p.user_id
WHERE p.published = 1;

-- Aggregation
SELECT user_id, COUNT(*) as post_count
FROM posts
GROUP BY user_id
HAVING post_count > 5;
```

### Upsert (INSERT OR REPLACE)

```sql
INSERT INTO users (id, name, email)
VALUES (1, 'Alice Updated', 'alice@example.com')
ON CONFLICT (email) DO UPDATE SET name = excluded.name;
```

### JSON Functions

```sql
-- Store JSON
INSERT INTO settings (key, value) VALUES ('config', '{"theme": "dark", "lang": "en"}');

-- Extract JSON field
SELECT json_extract(value, '$.theme') AS theme FROM settings WHERE key = 'config';

-- JSON array operations
SELECT json_array_length('[1, 2, 3]');  -- Returns 3
```

## Local Development

### Using SQLite Directly

```bash
# Point your SDK at a local file — no Turso Cloud needed
# TypeScript: url: "file:local.db"
# Python: turso.connect("local.db")
# Go: sql.Open("turso", "local.db")
```

### Local Dev Server

```bash
# Start a local libSQL server
turso dev

# Starts on http://127.0.0.1:8080
# Connect with: url: "http://127.0.0.1:8080"
```

### In-Memory Databases

```bash
# CLI
tursodb :memory:

# SDKs
# TypeScript: await connect(":memory:")
# Python: turso.connect(":memory:")
```

## Database Management

```bash
# List all databases
turso db list

# Show database details
turso db show my-app

# Inspect database structure and size
turso db inspect my-app

# Export database to a local SQLite file
turso db export my-app ./backup.db

# Import a SQLite file into an existing database
turso db import my-app ./data.db

# Delete a database (irreversible)
turso db destroy my-app
```

## Groups and Regions

### Managing Groups

```bash
# Create a group in a specific primary region
turso group create us-prod --location iad

# List all groups
turso group list

# Add a replica region to a group
turso group update us-prod --add-location lax

# Remove a replica region
turso group update us-prod --remove-location lax

# Delete a group (and all its databases)
turso group destroy us-prod
```

### Available Regions

```bash
# List all available locations
turso db locations

# Common locations:
# iad — US East (Virginia)
# lax — US West (Los Angeles)
# lhr — Europe (London)
# nrt — Asia Pacific (Tokyo)
# sin — Asia Pacific (Singapore)
# syd — Australia (Sydney)
# gru — South America (São Paulo)
```

## Common Pitfalls

1. **Forgetting auth tokens in production** — Local development works without tokens, but remote connections always require `authToken`
2. **Using `@libsql/client` for new projects** — Consider `@tursodatabase/database` or `@tursodatabase/sync` for the latest engine features (MVCC, CDC)
3. **Not setting up groups** — Databases created without specifying a group go into `default`. Plan your group topology early for multi-region deployments
4. **SQLite file locking** — Local database files can only be opened by one process at a time unless using MVCC mode
5. **Branching without cleanup** — Branches consume quota. Delete them after testing with `turso db destroy`
