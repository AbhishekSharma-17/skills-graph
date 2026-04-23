# Cloudflare Workers — Deployment & CI/CD

> Source: [developers.cloudflare.com/workers/ci-cd](https://developers.cloudflare.com/workers/ci-cd/)

## Table of Contents

- [Deploying with Wrangler](#deploying-with-wrangler)
- [Environments](#environments)
- [Secrets Management](#secrets-management)
- [GitHub Actions](#github-actions)
- [Rollbacks](#rollbacks)
- [Custom Domains](#custom-domains)
- [Gradual Rollouts](#gradual-rollouts)
- [Observability](#observability)
- [Common Patterns](#common-patterns)

## Deploying with Wrangler

### Basic Deployment

```bash
# Deploy to production
npx wrangler deploy

# Deploy with dry-run (preview only)
npx wrangler deploy --dry-run

# Deploy with verbose output
npx wrangler deploy --log-level debug
```

Output:
```
Uploaded my-worker (1.23 sec)
Deployed my-worker triggers (0.45 sec)
  https://my-worker.username.workers.dev
```

### Deploy to Specific Environment

```bash
npx wrangler deploy --env staging
npx wrangler deploy --env production
```

### First Deploy

On first deploy, Wrangler:
1. Creates the Worker script
2. Sets up routes/custom domains
3. Provisions auto-provisioned resources (KV, R2, D1)
4. Applies Durable Object migrations

## Environments

Define environment-specific configuration:

```toml
# wrangler.toml
name = "my-api"
main = "src/index.ts"
compatibility_date = "2026-04-23"

[vars]
ENVIRONMENT = "production"
LOG_LEVEL = "info"

[[d1_databases]]
binding = "DB"
database_name = "my-db-prod"
database_id = "prod-id-123"

# --- Staging ---
[env.staging]
name = "my-api-staging"
vars = { ENVIRONMENT = "staging", LOG_LEVEL = "debug" }

[[env.staging.d1_databases]]
binding = "DB"
database_name = "my-db-staging"
database_id = "staging-id-456"

# --- Preview ---
[env.preview]
name = "my-api-preview"
vars = { ENVIRONMENT = "preview", LOG_LEVEL = "debug" }
```

```bash
# Deploy staging
npx wrangler deploy --env staging

# Run dev against staging
npx wrangler dev --env staging
```

## Secrets Management

Secrets are encrypted environment variables that don't appear in `wrangler.toml`:

```bash
# Set a secret (prompts for value)
npx wrangler secret put API_KEY
# Enter the value interactively

# Set from pipe
echo "my-secret-value" | npx wrangler secret put API_KEY

# Set for specific environment
npx wrangler secret put API_KEY --env staging

# List secrets (shows names only, not values)
npx wrangler secret list

# Delete a secret
npx wrangler secret delete API_KEY
```

### In CI/CD

```bash
# Set from environment variable
echo "$API_KEY" | npx wrangler secret put API_KEY
```

### Accessing Secrets

Secrets are accessed the same way as variables — via `env`:

```typescript
interface Env {
  API_KEY: string;      // Secret
  DB_URL: string;       // Secret
  ENVIRONMENT: string;  // Variable (from wrangler.toml)
}

export default {
  async fetch(request: Request, env: Env) {
    // Secrets and vars accessed identically
    const response = await fetch("https://api.external.com", {
      headers: { Authorization: `Bearer ${env.API_KEY}` },
    });
    return response;
  },
};
```

### .dev.vars (Local Development)

```bash
# .dev.vars (gitignored — local secrets for wrangler dev)
API_KEY=dev-api-key-123
DB_URL=postgres://localhost:5432/devdb
JWT_SECRET=local-jwt-secret
```

Add `.dev.vars` to `.gitignore` — never commit it.

## GitHub Actions

### Basic Deployment Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy Worker

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Deploy to Cloudflare
        run: npx wrangler deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

### Multi-Environment Workflow

```yaml
name: Deploy

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm test

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/staging'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npx wrangler deploy --env staging
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npx wrangler deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

### Setting Up API Token

1. Go to Cloudflare Dashboard → My Profile → API Tokens
2. Create Token → Custom Token
3. Permissions: `Account: Workers Scripts: Edit`, `Zone: Workers Routes: Edit`
4. Add token as GitHub repository secret: `CLOUDFLARE_API_TOKEN`

## Rollbacks

### Version History

```bash
# List recent deployments
npx wrangler deployments list

# View details of a deployment
npx wrangler deployments view <deployment-id>
```

### Rollback to Previous Version

```bash
# Rollback to previous deployment
npx wrangler rollback

# Rollback to specific version
npx wrangler rollback --version <version-id>
```

### Deployment Safety

```bash
# Deploy with a message (for tracking)
npx wrangler deploy --message "Fix: rate limiter bug"

# Verify after deploy
npx wrangler tail  # Stream live logs
```

## Custom Domains

```toml
# wrangler.toml

# Option 1: Route patterns (requires zone in your account)
routes = [
  { pattern = "api.example.com/*", zone_name = "example.com" },
]

# Option 2: Custom domains (auto-configures DNS)
[[custom_domains]]
hostname = "api.example.com"
```

```bash
# Add via CLI
npx wrangler domains add api.example.com
```

### workers.dev Subdomain

Every Worker gets a free `<name>.<subdomain>.workers.dev` URL. Disable if only using custom domains:

```toml
workers_dev = false
```

## Gradual Rollouts

Deploy changes to a percentage of traffic:

```bash
# Deploy to 10% of traffic
npx wrangler deploy --percentage 10

# Increase to 50%
npx wrangler deploy --percentage 50

# Full rollout
npx wrangler deploy --percentage 100
```

Monitor error rates between versions before increasing percentage.

## Observability

### Live Logs (Tail)

```bash
# Stream all logs
npx wrangler tail

# Filter by status
npx wrangler tail --status error

# Filter by IP
npx wrangler tail --ip-address 1.2.3.4

# Filter by search string
npx wrangler tail --search "error"

# JSON output
npx wrangler tail --format json
```

### Structured Logging

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const start = Date.now();
    const url = new URL(request.url);

    try {
      const response = await handleRequest(request, env);

      console.log(JSON.stringify({
        level: "info",
        path: url.pathname,
        method: request.method,
        status: response.status,
        duration_ms: Date.now() - start,
        cf_colo: request.cf?.colo,
      }));

      return response;
    } catch (err) {
      console.error(JSON.stringify({
        level: "error",
        path: url.pathname,
        error: err instanceof Error ? err.message : "Unknown",
        stack: err instanceof Error ? err.stack : undefined,
      }));
      throw err;
    }
  },
};
```

### Observability Config

```toml
# wrangler.toml
[observability]
enabled = true   # Enhanced logging in dashboard
```

### Analytics Engine

```typescript
// Track custom metrics
env.ANALYTICS.writeDataPoint({
  indexes: [request.cf?.country ?? "unknown"],
  blobs: [url.pathname, request.method],
  doubles: [Date.now() - start],
});
```

## Common Patterns

### Pre-Deploy Checklist Script

```bash
#!/bin/bash
set -e

echo "Running pre-deploy checks..."
npm run lint
npm run typecheck
npm run test
npx wrangler deploy --dry-run
echo "All checks passed. Ready to deploy."
```

### Blue-Green with Environments

```bash
# Deploy to staging first
npx wrangler deploy --env staging

# Test staging
curl https://my-api-staging.workers.dev/health

# If healthy, deploy to production
npx wrangler deploy
```

## Common Pitfalls

- **API token scope** — The token needs `Workers Scripts: Edit` permission. Read-only tokens can't deploy.
- **Secrets in CI** — Never hardcode secrets in workflow files. Use GitHub repository secrets.
- **`.dev.vars` not deployed** — This file is for local dev only. Use `wrangler secret put` for deployed secrets.
- **Migration ordering** — Durable Object migrations must be applied in order. Don't skip tags.
- **Rollback limitations** — Rollback reverts code but not bindings/config. If you changed wrangler.toml, rollback may not work as expected.
- **Tail sampling** — `wrangler tail` samples logs, it doesn't capture 100% of requests on high-traffic Workers.
