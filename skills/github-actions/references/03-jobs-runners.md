# Jobs and Runners

> Source: [docs.github.com/en/actions/using-jobs](https://docs.github.com/en/actions/using-jobs) | Job Configuration & Runner Types

## Table of Contents

- [Job Configuration](#job-configuration)
- [Job Dependency Graph](#job-dependency-graph)
- [Job Outputs](#job-outputs)
- [GitHub-Hosted Runners](#github-hosted-runners)
- [Larger Runners](#larger-runners)
- [Runner Labels and runs-on Syntax](#runner-labels-and-runs-on-syntax)
- [Self-Hosted Runners](#self-hosted-runners)
- [Runner Scale Sets](#runner-scale-sets)
- [Container Jobs](#container-jobs)
- [Service Containers](#service-containers)
- [Matrix with Runner Variation](#matrix-with-runner-variation)
- [Timeout and Error Handling](#timeout-and-error-handling)
- [Conditional Jobs](#conditional-jobs)
- [Job Concurrency Groups](#job-concurrency-groups)
- [Complete Multi-Job Pipeline](#complete-multi-job-pipeline)

---

## Job Configuration

Every job needs an identifier, a runner, and at least one step.

```yaml
jobs:
  build:                         # Job identifier (used in needs, outputs)
    name: Build Application      # Display name in the GitHub UI
    runs-on: ubuntu-latest       # Runner selection
    timeout-minutes: 15          # Maximum execution time (default: 360)
    continue-on-error: false     # Whether job failure fails the workflow
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
```

Identifiers must start with a letter or underscore, containing only alphanumeric characters, hyphens, or underscores.

## Job Dependency Graph

Jobs run in parallel by default. Use `needs` to create execution order.

Sequential: chain jobs with `needs: previous-job`. Parallel: omit `needs` (default).

### Fan-Out / Fan-In

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.ver.outputs.value }}
    steps:
      - uses: actions/checkout@v4
      - id: ver
        run: echo "value=$(node -p 'require(\"./package.json\").version')" >> "$GITHUB_OUTPUT"

  test-unit:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run test:unit

  test-integration:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run test:integration

  test-e2e:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npx playwright test

  deploy:
    needs: [test-unit, test-integration, test-e2e]
    runs-on: ubuntu-latest
    steps:
      - run: echo "All tests passed, deploying v${{ needs.setup.outputs.version }}"
```

### Conditional Continuation After Failure

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
  notify:
    needs: test
    if: always()                 # Run regardless of test outcome
    runs-on: ubuntu-latest
    steps:
      - run: echo "Test result: ${{ needs.test.result }}"
```

The `needs.<job>.result` is one of: `success`, `failure`, `cancelled`, `skipped`.

## Job Outputs

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      changed: ${{ steps.changes.outputs.services }}
      sha: ${{ steps.meta.outputs.sha }}
    steps:
      - uses: actions/checkout@v4
      - id: changes
        run: |
          services=$(git diff --name-only HEAD~1 | grep '^services/' | cut -d/ -f2 | sort -u | jq -R -s -c 'split("\n") | map(select(. != ""))')
          echo "services=$services" >> "$GITHUB_OUTPUT"
      - id: meta
        run: echo "sha=$(git rev-parse --short HEAD)" >> "$GITHUB_OUTPUT"

  build:
    needs: detect
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building SHA ${{ needs.detect.outputs.sha }}, changed: ${{ needs.detect.outputs.changed }}"
```

Outputs are always strings. For complex data, serialize to JSON and parse with `fromJSON()`.

## GitHub-Hosted Runners

| Label | OS | Architecture | vCPU | RAM |
|:------|:---|:-------------|:-----|:----|
| `ubuntu-latest` | Ubuntu 24.04 | x86_64 | 4 | 16 GB |
| `ubuntu-24.04` | Ubuntu 24.04 | x86_64 | 4 | 16 GB |
| `ubuntu-22.04` | Ubuntu 22.04 | x86_64 | 4 | 16 GB |
| `windows-latest` | Windows Server 2022 | x86_64 | 4 | 16 GB |
| `windows-2022` | Windows Server 2022 | x86_64 | 4 | 16 GB |
| `macos-latest` | macOS 15 (Sequoia) | arm64 | 4 | 14 GB |
| `macos-15` | macOS 15 (Sequoia) | arm64 | 4 | 14 GB |
| `macos-14` | macOS 14 (Sonoma) | arm64 | 3 | 7 GB |
| `macos-13` | macOS 13 (Ventura) | x86_64 | 4 | 14 GB |

Standard runners come pre-installed with Git, Node.js, Python, Docker (Linux/Windows), and common build tools. The `latest` labels may change; pin a specific version for reproducible builds.

## Larger Runners

Available on GitHub Team and Enterprise plans.

| Type | Specs | Use Case |
|:-----|:------|:---------|
| Linux 8-core | 8 vCPU, 32 GB | Large test suites |
| Linux 16-core | 16 vCPU, 64 GB | Build-heavy projects |
| Linux 32-core | 32 vCPU, 128 GB | Monorepo builds |
| Linux 64-core | 64 vCPU, 256 GB | ML, large compilations |
| GPU (NVIDIA T4/L4) | 4 vCPU + GPU | ML inference/training |
| Linux ARM64 | 4 vCPU, 16 GB | ARM-native builds |
| macOS XL (M1) | 6 vCPU, 14 GB | iOS/macOS builds |

Configured in organization settings, referenced by assigned label:

```yaml
jobs:
  build:
    runs-on: my-org-linux-16core
    steps:
      - uses: actions/checkout@v4
      - run: make build
```

## Runner Labels and runs-on Syntax

```yaml
# Single label
runs-on: ubuntu-latest

# Label array (runner must match ALL labels)
runs-on: [self-hosted, linux, x64, gpu]

# Group with labels (larger runners)
runs-on:
  group: my-runner-group
  labels: [linux, x64]
```

## Self-Hosted Runners

Install the runner agent on your own machines for custom hardware, network access, or cost control.

Setup: Repository or Organization Settings > Actions > Runners > "New self-hosted runner". Apply custom labels during setup or via the UI:

```yaml
jobs:
  train:
    runs-on: [self-hosted, gpu]
    steps:
      - uses: actions/checkout@v4
      - run: python train.py
```

Security considerations:
- Never use self-hosted runners on public repositories (arbitrary fork code execution)
- Use `--ephemeral` for single-use runners that clean up after each job
- Run the agent as a non-root user with minimal permissions
- Runners persist between jobs; sensitive data from one job may leak to the next

## Runner Scale Sets

Auto-scaling self-hosted runners (public preview since 2025) without requiring Kubernetes. GitHub manages scaling based on job queue depth.

```yaml
jobs:
  build:
    runs-on: my-scale-set
    steps:
      - uses: actions/checkout@v4
      - run: make build
```

Configured through the GitHub UI/API with min/max runner counts and idle timeout. For Kubernetes-based scaling, use the Actions Runner Controller (ARC).

## Container Jobs

Run the entire job inside a Docker container:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: python:3.13-slim
      env:
        PYTHONDONTWRITEBYTECODE: '1'
      volumes:
        - /tmp/cache:/cache
      options: --cpus 2 --memory 4g
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt && pytest -x -v
```

For private registries, add `credentials` with `username` and `password` (e.g., `${{ secrets.GITHUB_TOKEN }}`). Container jobs only work on Linux runners.

## Service Containers

Sidecar containers for databases, caches, and other services.

### PostgreSQL + Redis

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: secret
          POSTGRES_DB: testdb
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
        options: --health-cmd "redis-cli ping" --health-interval 10s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:integration
        env:
          DATABASE_URL: postgresql://app:secret@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
```

For MySQL, use `image: mysql:8.4` with `MYSQL_ROOT_PASSWORD` and health check `mysqladmin ping -h localhost`.

Services start before steps run. Health checks ensure readiness. In a container job, reference services by name (e.g., `postgres`) instead of `localhost`.

## Matrix with Runner Variation

Test across multiple operating systems and configurations:

```yaml
jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node: [20, 22]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: npm
      - run: npm ci
      - run: npm test
```

Creates 6 parallel jobs (3 OS x 2 Node versions).

## Timeout and Error Handling

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - run: npm run build

  experimental:
    runs-on: ubuntu-latest
    continue-on-error: true      # Failure does not fail the workflow
    steps:
      - run: npm run test:experimental

  deploy:
    needs: [build, experimental]  # Runs even if experimental failed
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying..."
```

Step-level timeout: add `timeout-minutes: 10` to any step.

## Conditional Jobs

Use `if` expressions with path-based change detection for monorepos:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.filter.outputs.backend }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            backend:
              - 'api/**'

  test-backend:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd api && npm ci && npm test

  deploy:
    needs: test-backend
    if: always() && (needs.test-backend.result == 'success' || needs.test-backend.result == 'skipped')
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying"
```

## Job Concurrency Groups

```yaml
jobs:
  deploy-api:
    runs-on: ubuntu-latest
    concurrency:
      group: deploy-api-${{ github.ref }}
      cancel-in-progress: false    # Queue, don't cancel
    steps:
      - run: echo "Deploying API"

  deploy-web:
    runs-on: ubuntu-latest
    concurrency:
      group: deploy-web-${{ github.ref }}
      cancel-in-progress: true     # Cancel stale deploys
    steps:
      - run: echo "Deploying web"
```

## Complete Multi-Job Pipeline

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  checks: write

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run lint && npx tsc --noEmit

  security:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm audit --audit-level=high

  test:
    needs: lint
    runs-on: ubuntu-latest
    timeout-minutes: 20
    strategy:
      fail-fast: false
      matrix:
        node: [20, 22]
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_PASSWORD: testpass
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 5s --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: npm
      - run: npm ci
      - run: npm test
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/postgres

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci && npm run build
      - id: meta
        run: echo "version=$(node -p 'require(\"./package.json\").version')" >> "$GITHUB_OUTPUT"
      - uses: actions/upload-artifact@v4
        with:
          name: dist-${{ github.sha }}
          path: dist/

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: staging
    concurrency:
      group: deploy-staging
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist-${{ github.sha }}
          path: dist/
      - run: echo "Deploying v${{ needs.build.outputs.version }}"

  notify:
    needs: [lint, test, build]
    if: failure() && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Failed -- ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
```
