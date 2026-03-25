# Deployment & CLI

> Source: https://trigger.dev/docs — v4.4.3

## Contents

- [Development (dev command)](#development-dev-command)
- [Deployment (deploy command)](#deployment-deploy-command)
- [Environments](#environments)
- [CI/CD Integration](#cicd-integration)
- [Self-Hosting](#self-hosting)
- [Common Patterns](#common-patterns)

## Development (dev command)

The `dev` command runs your tasks locally, connecting to Trigger.dev Cloud (or your self-hosted instance):

```bash
npx trigger.dev@latest dev
```

### What it Does

1. Bundles your task code from configured `dirs`
2. Connects to your Trigger.dev project
3. Registers tasks in the DEV environment
4. Runs tasks locally when triggered
5. Shows logs in your terminal

### Dev Options

```bash
# Specify config file
npx trigger.dev@latest dev --config custom.config.ts

# Specify project reference
npx trigger.dev@latest dev --project-ref proj_xxxx

# Custom log level
npx trigger.dev@latest dev --log-level debug

# Use a specific profile
npx trigger.dev@latest dev --profile staging

# Point to self-hosted instance
npx trigger.dev@latest dev --api-url https://trigger.mycompany.com
```

### Development Behavior

- **Retries:** Disabled by default in DEV (configurable via `enabledInDev`)
- **Scheduled tasks:** Only trigger when `dev` is running
- **Machine size:** Runs on your local machine (not cloud workers)
- **Hot reload:** Automatically rebuilds when task files change

## Deployment (deploy command)

Deploy your tasks to Trigger.dev Cloud or self-hosted infrastructure:

```bash
npx trigger.dev@latest deploy
```

### What it Does

1. Optionally checks for package updates
2. Compiles and bundles your task code
3. Uploads the bundle to Trigger.dev
4. Registers tasks as a new version
5. Promotes the new version to "current" (unless `--skip-promotion`)

### Deploy Options

```bash
# Deploy to production (default)
npx trigger.dev@latest deploy

# Deploy to staging
npx trigger.dev@latest deploy --env staging

# Deploy to preview (auto-detects branch from git)
npx trigger.dev@latest deploy --env preview

# Specify branch for preview
npx trigger.dev@latest deploy --env preview --branch feature/my-branch

# Dry run — build without deploying
npx trigger.dev@latest deploy --dry-run

# Skip promoting to current version
npx trigger.dev@latest deploy --skip-promotion

# Skip environment variable syncing
npx trigger.dev@latest deploy --skip-sync-env-vars

# Force local Docker build (automatic for self-hosted)
npx trigger.dev@latest deploy --local-build

# Load env vars into CLI process
npx trigger.dev@latest deploy --env-file .env.production

# Skip package update checks
npx trigger.dev@latest deploy --skip-update-check
```

### All Deploy Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--config` | `-c` | Config file name |
| `--project-ref` | `-p` | Project reference |
| `--env` | `-e` | Target environment (prod/staging/preview) |
| `--branch` | `-b` | Preview branch name |
| `--dry-run` | | Build without deploying |
| `--skip-promotion` | | Don't promote to current |
| `--skip-sync-env-vars` | | Skip env var sync |
| `--local-build` | | Force local Docker build |
| `--env-file` | | Load env vars file |
| `--skip-update-check` | | Skip package update check |
| `--profile` | | Login profile |
| `--api-url` | `-a` | Override API endpoint |
| `--log-level` | `-l` | Verbosity (debug/info/log/warn/error) |
| `--skip-telemetry` | | Opt out of telemetry |

## Environments

Trigger.dev supports four environment types:

| Environment | Purpose | Deploy Command |
|-------------|---------|----------------|
| **DEV** | Local development | `npx trigger.dev dev` |
| **STAGING** | Pre-production testing | `--env staging` |
| **PREVIEW** | Per-branch testing | `--env preview` |
| **PRODUCTION** | Live traffic | `--env prod` (default) |

### Environment Keys

Each environment has its own secret key:

```bash
# Dashboard → Project → API Keys
TRIGGER_SECRET_KEY=tr_dev_xxxx    # DEV
TRIGGER_SECRET_KEY=tr_stg_xxxx   # STAGING
TRIGGER_SECRET_KEY=tr_prev_xxxx  # PREVIEW
TRIGGER_SECRET_KEY=tr_prod_xxxx  # PRODUCTION
```

### Preview Branches

Preview environments auto-detect the git branch:

```bash
# Auto-detects branch from git
npx trigger.dev@latest deploy --env preview

# Manually specify branch
npx trigger.dev@latest deploy --env preview --branch feature/payments
```

In your app, set `TRIGGER_PREVIEW_BRANCH` to route triggers to the correct preview deployment.

## CI/CD Integration

### Authentication

For CI/CD, use `TRIGGER_ACCESS_TOKEN` instead of interactive login:

```bash
# Generate from dashboard → Account → Access Tokens
export TRIGGER_ACCESS_TOKEN=tr_at_xxxx
```

### GitHub Actions

```yaml
name: Deploy Trigger.dev
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npx trigger.dev@latest deploy
        env:
          TRIGGER_ACCESS_TOKEN: ${{ secrets.TRIGGER_ACCESS_TOKEN }}
```

### GitHub Actions with Preview Deploys

```yaml
name: Deploy Trigger.dev Preview
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  deploy-preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npx trigger.dev@latest deploy --env preview
        env:
          TRIGGER_ACCESS_TOKEN: ${{ secrets.TRIGGER_ACCESS_TOKEN }}
```

### GitLab CI

```yaml
deploy-triggers:
  stage: deploy
  image: node:20
  script:
    - npm ci
    - npx trigger.dev@latest deploy
  variables:
    TRIGGER_ACCESS_TOKEN: $TRIGGER_ACCESS_TOKEN
  only:
    - main
```

## Self-Hosting

Trigger.dev can be self-hosted using Docker or Kubernetes.

### Docker Setup

```bash
# Clone the Docker templates repo
git clone https://github.com/triggerdotdev/docker.git
cd docker

# Start with Docker Compose
docker compose up -d
```

### Kubernetes

Trigger.dev v4 supports Kubernetes deployments for production self-hosting.

### Connecting CLI to Self-Hosted

```bash
# Login to your self-hosted instance
npx trigger.dev@latest login --api-url https://trigger.mycompany.com

# Dev against self-hosted
npx trigger.dev@latest dev --api-url https://trigger.mycompany.com

# Deploy to self-hosted
npx trigger.dev@latest deploy --api-url https://trigger.mycompany.com
```

### Self-Hosted Deploy Behavior

- Builds are performed **locally by default** (uses Docker)
- Set `TRIGGER_ACCESS_TOKEN` for CI/CD authentication
- Same deploy command, just pointed at your instance

## Common Patterns

### Monorepo Setup

```typescript
// trigger.config.ts
export default defineConfig({
  project: "proj_xxxx",
  dirs: [
    "./packages/background-jobs/trigger",
    "./apps/web/trigger",
  ],
});
```

### Environment-Specific Configuration

```typescript
export default defineConfig({
  project: "proj_xxxx",
  machine: process.env.NODE_ENV === "production" ? "medium-1x" : "small-1x",
  retries: {
    enabledInDev: false,
    default: {
      maxAttempts: process.env.NODE_ENV === "production" ? 5 : 1,
    },
  },
});
```

### Login Profiles

```bash
# Login to different instances/accounts
npx trigger.dev@latest login --profile work
npx trigger.dev@latest login --profile personal

# Use a specific profile
npx trigger.dev@latest dev --profile work
npx trigger.dev@latest deploy --profile personal
```

## Related Topics

- Configuration → `09-configuration.md`
- Scheduled tasks & environments → `04-scheduled-tasks.md`
- Overview & setup → `00-overview.md`
