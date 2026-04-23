# Cloudflare Workers — Configuration

> Source: [developers.cloudflare.com/workers/wrangler/configuration](https://developers.cloudflare.com/workers/wrangler/configuration/)

## Table of Contents

- [Configuration File Formats](#configuration-file-formats)
- [Top-Level Fields](#top-level-fields)
- [Compatibility Dates and Flags](#compatibility-dates-and-flags)
- [Bindings Configuration](#bindings-configuration)
- [Environments](#environments)
- [Build Configuration](#build-configuration)
- [Triggers](#triggers)
- [Static Assets](#static-assets)

## Configuration File Formats

Wrangler supports two configuration formats:

```toml
# wrangler.toml (TOML — most common)
name = "my-worker"
main = "src/index.ts"
compatibility_date = "2026-04-23"
```

```jsonc
// wrangler.jsonc (JSON with comments)
{
  "name": "my-worker",
  "main": "src/index.ts",
  "compatibility_date": "2026-04-23"
}
```

## Top-Level Fields

```toml
name = "my-worker"                    # Worker name (used in URL)
main = "src/index.ts"                 # Entry point file
compatibility_date = "2026-04-23"     # Runtime behavior version
compatibility_flags = ["nodejs_compat_v2"]  # Feature flags
account_id = "abc123"                 # Cloudflare account (optional, auto-detected)

# Worker limits
limits.cpu_ms = 30000                 # CPU time limit in ms (paid plan)

# Observability
observability.enabled = true          # Enable detailed logging

# Node.js compatibility
node_compat = true                    # Enable Node.js API polyfills (deprecated)
# Use compatibility_flags = ["nodejs_compat_v2"] instead
```

## Compatibility Dates and Flags

The `compatibility_date` controls which runtime features and breaking changes are active. Always set it to today's date for new projects.

```toml
compatibility_date = "2026-04-23"

# Common compatibility flags
compatibility_flags = [
  "nodejs_compat_v2",            # Node.js APIs (Buffer, crypto, async_hooks, etc.)
  "transformstream_enable_standard_constructor",
  "web_socket_auto_reply_to_close",  # Auto-reply WebSocket close (2026-04-07+)
]
```

Key compatibility dates:
- `2024-09-23` — `global_navigator` enabled by default
- `2024-10-01` — `nodejs_compat_v2` behavior change
- `2026-04-07` — `web_socket_auto_reply_to_close` enabled by default

## Bindings Configuration

### Variables (Environment Variables)

```toml
[vars]
API_URL = "https://api.example.com"
MAX_RETRIES = "3"
DEBUG = "false"
```

### KV Namespaces

```toml
[[kv_namespaces]]
binding = "MY_KV"
id = "abc123def456"

# Preview namespace (used in wrangler dev)
[[kv_namespaces]]
binding = "MY_KV"
id = "abc123def456"
preview_id = "preview789"
```

### D1 Databases

```toml
[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "xxxx-xxxx-xxxx"

# Auto-provisioned (no ID needed, created on first deploy)
[[d1_databases]]
binding = "DB"
database_name = "my-database"
```

### R2 Buckets

```toml
[[r2_buckets]]
binding = "MY_BUCKET"
bucket_name = "my-bucket"

# With jurisdiction (EU data residency)
[[r2_buckets]]
binding = "EU_BUCKET"
bucket_name = "eu-bucket"
jurisdiction = "eu"
```

### Durable Objects

```toml
[durable_objects]
bindings = [
  { name = "COUNTER", class_name = "Counter" },
  { name = "ROOM", class_name = "ChatRoom" },
]

# Durable Object migrations (required on first deploy or class changes)
[[migrations]]
tag = "v1"
new_classes = ["Counter", "ChatRoom"]

# Use new_sqlite_classes for SQLite-backed DOs
[[migrations]]
tag = "v2"
new_sqlite_classes = ["Counter"]
```

### Queues

```toml
# Producer binding
[[queues.producers]]
binding = "MY_QUEUE"
queue = "my-queue"

# Consumer configuration
[[queues.consumers]]
queue = "my-queue"
max_batch_size = 10        # 1-100, default 10
max_batch_timeout = 5      # seconds, default 5
max_retries = 3            # default 3
dead_letter_queue = "my-dlq"
max_concurrency = 10       # parallel consumers
```

### Workers AI

```toml
[ai]
binding = "AI"
```

### Service Bindings

```toml
[[services]]
binding = "AUTH_SERVICE"
service = "auth-worker"

# Bind to a named entrypoint
[[services]]
binding = "ADMIN_API"
service = "api-worker"
entrypoint = "AdminEntrypoint"
```

### Hyperdrive (External DB Connection Pooling)

```toml
[[hyperdrive]]
binding = "HYPERDRIVE"
id = "xxxx-xxxx-xxxx"
```

### Vectorize

```toml
[[vectorize]]
binding = "MY_INDEX"
index_name = "my-vector-index"
```

### Analytics Engine

```toml
[[analytics_engine_datasets]]
binding = "ANALYTICS"
dataset = "my-dataset"
```

## Environments

Define environment-specific overrides:

```toml
name = "my-worker"
main = "src/index.ts"
compatibility_date = "2026-04-23"

[vars]
ENVIRONMENT = "production"

# Staging environment
[env.staging]
name = "my-worker-staging"
vars = { ENVIRONMENT = "staging" }

[[env.staging.kv_namespaces]]
binding = "MY_KV"
id = "staging-kv-id"

# Preview environment
[env.preview]
name = "my-worker-preview"
vars = { ENVIRONMENT = "preview" }
```

Deploy to specific environment:

```bash
wrangler deploy --env staging
wrangler dev --env staging
```

Bindings are NOT inherited between environments — you must redeclare them in each environment.

## Build Configuration

```toml
# Custom build step (runs before Wrangler bundles)
[build]
command = "npm run build"
cwd = "."
watch_dir = "src"

# Bundle rules (non-JS assets)
[[rules]]
type = "Text"
globs = ["**/*.html", "**/*.txt"]
fallthrough = true

[[rules]]
type = "Data"
globs = ["**/*.bin"]
```

## Triggers

### Cron Triggers (Scheduled Workers)

```toml
[triggers]
crons = [
  "0 * * * *",       # Every hour
  "*/5 * * * *",     # Every 5 minutes
  "0 0 * * *",       # Daily at midnight
  "0 9 * * MON",     # Monday at 9am
]
```

### Custom Domains and Routes

```toml
# Route patterns
routes = [
  { pattern = "example.com/api/*", zone_name = "example.com" },
  { pattern = "api.example.com/*", zone_name = "example.com" },
]

# Custom domains (simpler, auto-configures DNS)
[[custom_domains]]
hostname = "api.example.com"
```

## Static Assets

```toml
# Serve static files alongside Worker logic
[assets]
directory = "./public"
binding = "ASSETS"

# Routing behavior
[assets.serve_directly]
enabled = true    # Serve assets directly without Worker (if route matches)
```

## Common Pitfalls

- **Bindings not inherited** — Each `[env.X]` needs its own bindings declared explicitly.
- **Compatibility date** — Omitting this field causes unpredictable behavior. Always set it.
- **Auto-provisioning** — KV, R2, and D1 bindings without IDs are auto-created on deploy. Great for starting out, but pin IDs for production.
- **Secrets vs vars** — Use `wrangler secret put` for sensitive values. They don't go in `wrangler.toml`.
- **Migration tags** — Durable Object migrations must have unique, sequential tags. Never reuse a tag.
