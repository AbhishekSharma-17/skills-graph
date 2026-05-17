# Environments and Deployments

> Source: [docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments)

Environments represent deployment targets like development, staging, and production. They provide protection rules, scoped secrets and variables, deployment tracking, and approval gates. Environments are configured in repository settings and referenced in workflow jobs.

## Table of Contents

- [Creating Environments](#creating-environments)
- [Referencing Environments in Workflows](#referencing-environments-in-workflows)
- [Protection Rules](#protection-rules)
- [Environment Secrets and Variables](#environment-secrets-and-variables)
- [Deployment Workflow Patterns](#deployment-workflow-patterns)
- [GitHub Deployments API](#github-deployments-api)
- [Concurrency Control](#concurrency-control)
- [Common Patterns](#common-patterns)

---

## Creating Environments

Create environments through **Settings > Environments > New environment**. Type a name and configure protection rules, secrets, and variables. Environment names are case-insensitive and must be unique within a repository.

Typical environment setup for a web application:

| Environment | Purpose | Protection |
|:------------|:--------|:-----------|
| `development` | Feature branch deploys | None |
| `staging` | Pre-production testing | Branch restriction to `main` |
| `production` | Live deployment | Required reviewers + wait timer + branch restriction |

Environments are available on public repositories for all plans and on private repositories for GitHub Pro, Team, and Enterprise plans.

## Referencing Environments in Workflows

### Simple Reference

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

### With Deployment URL

Providing a URL displays a "View deployment" link in the pull request timeline and on the repository's deployments page:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.example.com
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

The `url` can be dynamic using step outputs: set `url: ${{ steps.deploy.outputs.url }}` and write the URL to `$GITHUB_OUTPUT` in a deploy step.

## Protection Rules

Configure protection rules on each environment to control when and how deployments happen.

| Rule | Description |
|:-----|:------------|
| **Required reviewers** | Up to 6 reviewers; only one needs to approve. Workflow pauses until approved. |
| **Self-review prevention** | Prevents the user who triggered the workflow from approving their own deploy. |
| **Wait timer** | 1 to 43,200 minutes (30 days) delay after approval before the job starts. |
| **Branch/tag restrictions** | Glob patterns (`main`, `release/*`, `v*`) limit which refs can deploy. Non-matching branches fail immediately. |
| **Custom protection rules** | Third-party gates (Datadog, Honeycomb, ServiceNow) that approve/reject via webhook. |

## Environment Secrets and Variables

Environment-scoped secrets and variables override repository-level values of the same name when the job references that environment.

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Migrate
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}    # resolves to staging DB
        run: npm run migrate

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Migrate
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}    # resolves to production DB
        run: npm run migrate
```

Both jobs reference `secrets.DATABASE_URL`, but each environment resolves to a different value. This keeps workflow files environment-agnostic.

## Deployment Workflow Patterns

### Sequential Pipeline with Approval Gates

The most common pattern: test, deploy to staging, get approval, deploy to production.

```yaml
name: Deploy Pipeline

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm test
      - run: npm run build

      - name: Upload build
        uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.myapp.com
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build
          path: dist/
      - name: Deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: |
          aws s3 sync dist/ s3://${{ vars.S3_BUCKET }} --delete
          aws cloudfront create-invalidation --distribution-id ${{ vars.CF_DISTRIBUTION_ID }} --paths "/*"

  deploy-production:  # same steps as staging, different environment secrets/variables
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production    # has required reviewers — pauses for approval
      url: https://myapp.com
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: build
          path: dist/
      - name: Deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: aws s3 sync dist/ s3://${{ vars.S3_BUCKET }} --delete
```

### Blue/Green Deployment

The pattern: deploy to an inactive slot, health-check it, then swap traffic.

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: ${{ steps.swap.outputs.url }}
    steps:
      - uses: actions/checkout@v4

      - name: Determine target slot
        id: slot
        run: |
          ACTIVE=$(curl -s https://api.myapp.com/active-slot)
          if [ "$ACTIVE" = "blue" ]; then
            echo "target=green" >> "$GITHUB_OUTPUT"
          else
            echo "target=blue" >> "$GITHUB_OUTPUT"
          fi

      - name: Deploy to inactive slot
        run: ./deploy.sh --slot "${{ steps.slot.outputs.target }}" --image "myapp:${{ github.sha }}"

      - name: Health check
        run: curl --fail --retry 10 --retry-delay 5 "https://${{ steps.slot.outputs.target }}.myapp.com/health"

      - name: Swap traffic
        id: swap
        run: |
          ./swap-slots.sh --to "${{ steps.slot.outputs.target }}"
          echo "url=https://myapp.com" >> "$GITHUB_OUTPUT"
```

### Canary with Manual Promotion

Deploy a canary to a small percentage of traffic, verify metrics in a separate environment, then promote to production with an approval gate:

```yaml
jobs:
  canary:
    runs-on: ubuntu-latest
    environment: canary
    steps:
      - uses: actions/checkout@v4
      - name: Deploy canary (10% traffic)
        run: |
          kubectl set image deployment/app-canary app=myapp:${{ github.sha }}
          kubectl scale deployment/app-canary --replicas=1

  promote:
    needs: canary
    runs-on: ubuntu-latest
    environment: production  # requires approval
    steps:
      - uses: actions/checkout@v4
      - name: Promote to full deployment
        run: |
          kubectl set image deployment/app app=myapp:${{ github.sha }}
          kubectl rollout status deployment/app --timeout=300s
      - name: Scale down canary
        run: kubectl scale deployment/app-canary --replicas=0
```

### Rollback Workflow

A manually triggered rollback using `workflow_dispatch`:

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        required: true
        type: choice
        options: [staging, production]

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - name: Rollback
        run: kubectl rollout undo deployment/app -n ${{ inputs.environment }}
      - name: Verify
        run: kubectl rollout status deployment/app -n ${{ inputs.environment }} --timeout=300s
```

## GitHub Deployments API

When a job references an environment, GitHub automatically creates deployment and deployment status records visible on the repository's deployments page and in pull request timelines.

### Deployment Status in Pull Requests

When a workflow deploys from a branch associated with a PR, GitHub shows:

- A deployment status indicator in the PR timeline
- A "View deployment" button linking to the environment URL
- A deployment history showing all deployments for that PR

This works automatically when your workflow job has an `environment` key with a `url`.

For complex multi-step deployments, use the `bobheadxi/deployments` action or the GitHub REST API to create and update deployment status records programmatically.

## Concurrency Control

Prevent multiple deployments to the same environment from running simultaneously:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    concurrency:
      group: deploy-production
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

| Setting | `cancel-in-progress: false` | `cancel-in-progress: true` |
|:--------|:---------------------------|:--------------------------|
| **Behavior** | Queue new runs, wait for current to finish | Cancel current run, start new one |
| **Best for** | Production deployments (never cancel mid-deploy) | Staging/preview deploys (latest wins) |

Use the environment name in the concurrency group to allow parallel deploys to different environments:

```yaml
concurrency:
  group: deploy-${{ inputs.environment }}
  cancel-in-progress: ${{ inputs.environment != 'production' }}
```

## Common Patterns

### Review Apps for Pull Requests

Deploy every PR to an ephemeral environment for testing:

```yaml
name: Review App

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  deploy-preview:
    runs-on: ubuntu-latest
    environment:
      name: pr-${{ github.event.pull_request.number }}
      url: ${{ steps.deploy.outputs.url }}
    concurrency:
      group: pr-${{ github.event.pull_request.number }}
      cancel-in-progress: true
    steps:
      - uses: actions/checkout@v4

      - name: Deploy preview
        id: deploy
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
        run: |
          URL=$(npx vercel deploy --token "$VERCEL_TOKEN" --yes)
          echo "url=$URL" >> "$GITHUB_OUTPUT"

      - name: Comment on PR
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          header: preview
          message: |
            **Preview deployed**
            ${{ steps.deploy.outputs.url }}
            Commit: ${{ github.sha }}
```

Add a separate workflow on `pull_request: types: [closed]` to clean up the ephemeral environment when the PR is merged or closed.

### Multi-Region Deployment

Use a matrix with per-region environments. Set `max-parallel: 1` to deploy one region at a time, reducing blast radius:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      max-parallel: 1
      matrix:
        region:
          - name: us-east-1
            environment: production-us-east
          - name: eu-west-1
            environment: production-eu-west
    environment:
      name: ${{ matrix.region.environment }}
      url: https://${{ matrix.region.name }}.myapp.com
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ matrix.region.name }}
      - name: Deploy
        run: |
          aws ecs update-service --cluster ${{ vars.ECS_CLUSTER }} --service ${{ vars.ECS_SERVICE }} --force-new-deployment
          aws ecs wait services-stable --cluster ${{ vars.ECS_CLUSTER }} --services ${{ vars.ECS_SERVICE }}
```

Each region uses its own environment with region-specific secrets and variables (`AWS_ROLE_ARN`, `ECS_CLUSTER`, `ECS_SERVICE` can differ per environment).

### Scheduled Production Deploys

Deploy accumulated changes on a schedule. Combine with `workflow_dispatch` for manual override:

```yaml
on:
  schedule:
    - cron: "0 14 * * 1-5"  # 2 PM UTC, weekdays
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - run: ./deploy.sh --env production
```
