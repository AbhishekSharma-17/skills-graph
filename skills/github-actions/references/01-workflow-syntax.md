# Workflow Syntax

> Source: [docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions) | Full YAML Reference

## Table of Contents

- [Top-Level Keys](#top-level-keys)
- [name and run-name](#name-and-run-name)
- [on (Event Triggers)](#on-event-triggers)
- [permissions](#permissions)
- [env (Environment Variables)](#env-environment-variables)
- [defaults](#defaults)
- [concurrency](#concurrency)
- [jobs](#jobs)
- [Job Dependencies with needs](#job-dependencies-with-needs)
- [Job Outputs](#job-outputs)
- [Job Conditionals](#job-conditionals)
- [Strategy and Matrix](#strategy-and-matrix)
- [Container Jobs and Service Containers](#container-jobs-and-service-containers)
- [Steps](#steps)
- [Complete Multi-Feature Example](#complete-multi-feature-example)

---

## Top-Level Keys

Every workflow file supports these top-level keys:

```yaml
name: CI Pipeline                    # Display name (optional)
run-name: Deploy ${{ github.ref }}   # Dynamic run name (optional)
on: push                             # Event trigger(s) (required)
permissions: read-all                # Token permissions (optional)
env:                                 # Workflow-level env vars (optional)
  NODE_ENV: production
defaults:                            # Default shell/working-directory (optional)
  run:
    shell: bash
concurrency:                         # Concurrency control (optional)
  group: deploy
  cancel-in-progress: true
jobs:                                # Job definitions (required)
  build:
    runs-on: ubuntu-latest
    steps: [...]
```

Only `on` and `jobs` are required. Everything else is optional but commonly used.

## name and run-name

`name` sets the workflow display name in the Actions tab. If omitted, GitHub uses the file path.

`run-name` sets the display name for each individual run with expression support:

```yaml
name: Deploy
run-name: Deploy to ${{ inputs.environment }} by @${{ github.actor }}

on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [staging, production]
```

## on (Event Triggers)

Single event, multiple events, or events with configuration:

```yaml
on:
  push:
    branches: [main, release/*]
    paths: ['src/**', 'package.json']
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
  schedule:
    - cron: '0 6 * * 1'
  workflow_dispatch:
    inputs:
      deploy_target:
        description: 'Deployment target'
        required: true
        type: choice
        options: [staging, production]
```

See the Event Triggers reference for full coverage of every event type.

## permissions

Control the scope of the `GITHUB_TOKEN`. Follows the principle of least privilege.

```yaml
permissions:
  contents: read
  pull-requests: write
  id-token: write        # For OIDC cloud auth
```

Scopes: `actions`, `contents`, `issues`, `pull-requests`, `packages`, `deployments`, `statuses`, `checks`, `id-token`, `security-events`, `pages`, `attestations`. Each accepts `read`, `write`, or `none`. Shorthand: `permissions: read-all` or `permissions: {}`.

Job-level permissions override workflow-level:

```yaml
permissions:
  contents: read

jobs:
  deploy:
    permissions:
      contents: read
      id-token: write    # OIDC needed only for deploy
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/deploy
```

## env (Environment Variables)

Environment variables cascade: workflow > job > step. More specific levels override broader ones.

```yaml
env:
  CI: true
  NODE_ENV: production

jobs:
  build:
    env:
      DATABASE_URL: postgresql://localhost:5432/testdb
    runs-on: ubuntu-latest
    steps:
      - name: Show environment
        env:
          STEP_VAR: only-this-step
        run: |
          echo "CI=$CI"                    # from workflow
          echo "DB=$DATABASE_URL"          # from job
          echo "STEP=$STEP_VAR"            # from step
```

Access secrets through the `secrets` context: `${{ secrets.API_KEY }}`.

## defaults

Set default shell and working directory for all `run` steps:

```yaml
defaults:
  run:
    shell: bash
    working-directory: ./app
```

| Shell | Platforms | Notes |
|:------|:----------|:------|
| `bash` | All | Default on Linux/macOS. Uses `bash --noprofile --norc -eo pipefail` |
| `sh` | Linux/macOS | Fallback POSIX shell |
| `pwsh` | All | PowerShell Core (cross-platform) |
| `powershell` | Windows | Windows PowerShell 5.1 |
| `python` | All | Executes the step as a Python script |
| `cmd` | Windows | Windows Command Prompt |

Job-level defaults override workflow-level. Custom shells: `shell: perl {0}`.

## concurrency

Ensure only one run executes at a time for a given group:

```yaml
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: true
```

Common groups: `ci-${{ github.event.pull_request.number || github.sha }}` (per-PR), `release` (global singleton).

## jobs

Each job runs on a fresh runner instance. Jobs execute in parallel by default.

```yaml
jobs:
  lint:
    name: Lint Code              # Display name in UI
    runs-on: ubuntu-latest
    timeout-minutes: 10          # Kill if exceeds (default: 360)
    continue-on-error: false     # Whether failure fails the workflow
    steps:
      - uses: actions/checkout@v4
      - run: npm run lint
```

Job identifiers must start with a letter or underscore, containing only alphanumeric characters, hyphens, or underscores.

## Job Dependencies with needs

Use `needs` to create a dependency DAG. Jobs wait for all listed dependencies to succeed:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run lint
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
  build:
    needs: [lint, test]          # Waits for both to pass
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
  deploy:
    needs: build                 # Single dependency
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying..."
```

## Job Outputs

Pass data between jobs through outputs:

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.value }}
      should_deploy: ${{ steps.check.outputs.deploy }}
    steps:
      - id: version
        run: echo "value=1.2.3" >> "$GITHUB_OUTPUT"
      - id: check
        run: echo "deploy=true" >> "$GITHUB_OUTPUT"

  deploy:
    needs: prepare
    if: needs.prepare.outputs.should_deploy == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying version ${{ needs.prepare.outputs.version }}"
```

Outputs are always strings. Use `fromJSON()` for complex data.

## Job Conditionals

```yaml
jobs:
  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying to staging"

  deploy-production:
    needs: test
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying to production"

  notify-failure:
    needs: [test, deploy-staging]
    if: failure()                # Runs only if a dependency failed
    runs-on: ubuntu-latest
    steps:
      - run: echo "Something failed"
```

Common `if` functions: `success()`, `failure()`, `cancelled()`, `always()`, `contains()`, `startsWith()`, `endsWith()`.

## Strategy and Matrix

Run a job multiple times with different configurations:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false           # Don't cancel others on failure
      max-parallel: 4            # Limit concurrent matrix jobs
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python: ['3.11', '3.12', '3.13']
        exclude:
          - os: windows-latest
            python: '3.11'
        include:
          - os: ubuntu-latest
            python: '3.13'
            experimental: true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: pip install -r requirements.txt
      - run: pytest
```

## Container Jobs and Service Containers

Run the job inside a Docker container with sidecar services:

```yaml
jobs:
  integration-test:
    runs-on: ubuntu-latest
    container:
      image: node:22-bookworm
      env:
        NODE_ENV: test
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:integration
        env:
          DATABASE_URL: postgresql://testuser:testpass@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
```

Service containers start before steps run. Health checks ensure readiness. When running in a container job, reference services by name (e.g., `postgres`) instead of `localhost`.

## Steps

Steps are the atomic units of a job, executing sequentially:

```yaml
steps:
  - name: Checkout
    uses: actions/checkout@v4          # Use a marketplace action
    with:
      fetch-depth: 0

  - name: Install and test
    run: |                             # Multi-line shell command
      npm ci
      npm test

  - name: Upload coverage
    if: success() && github.event_name == 'push'
    uses: actions/upload-artifact@v4   # Conditional step
    with:
      name: coverage-report
      path: coverage/

  - name: Get version
    id: pkg                            # Step ID for output reference
    run: echo "version=$(node -p 'require(\"./package.json\").version')" >> "$GITHUB_OUTPUT"

  - name: Use output
    run: echo "Version is ${{ steps.pkg.outputs.version }}"
```

## Complete Multi-Feature Example

```yaml
name: CI/CD Pipeline

run-name: "${{ github.event_name == 'push' && 'CI' || 'PR' }} #${{ github.run_number }}"

on:
  push:
    branches: [main]
    paths-ignore: ['**.md', 'docs/**']
  pull_request:
    branches: [main]

permissions:
  contents: read
  checks: write

env:
  NODE_VERSION: 22

defaults:
  run:
    shell: bash

concurrency:
  group: ci-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
      - run: npm ci
      - run: npm run lint && npx tsc --noEmit

  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
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
    needs: [lint, test]
    runs-on: ubuntu-latest
    outputs:
      artifact_name: ${{ steps.meta.outputs.artifact }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm
      - run: npm ci && npm run build
      - id: meta
        run: echo "artifact=build-${{ github.sha }}" >> "$GITHUB_OUTPUT"
      - uses: actions/upload-artifact@v4
        with:
          name: build-${{ github.sha }}
          path: dist/

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: staging
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: ${{ needs.build.outputs.artifact_name }}
          path: dist/
      - run: echo "Deploying ${{ needs.build.outputs.artifact_name }}"
```
