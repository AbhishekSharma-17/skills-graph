# Reusable Workflows

> Source: [docs.github.com/en/actions/sharing-automations/reusing-workflows](https://docs.github.com/en/actions/sharing-automations/reusing-workflows)

Reusable workflows let you define a workflow once and call it from other workflows across your organization. They apply the DRY principle to CI/CD pipelines — standardize testing, building, and deployment logic in a single place and call it with different parameters from each repository.

## Table of Contents

- [Creating a Reusable Workflow](#creating-a-reusable-workflow)
- [Defining Inputs](#defining-inputs)
- [Defining Outputs](#defining-outputs)
- [Declaring Secrets](#declaring-secrets)
- [Calling a Reusable Workflow](#calling-a-reusable-workflow)
- [Passing Secrets](#passing-secrets)
- [Nesting and Limits](#nesting-and-limits)
- [Access Control](#access-control)
- [Versioning](#versioning)
- [Composite Actions vs Reusable Workflows](#composite-actions-vs-reusable-workflows)
- [Creating Composite Actions](#creating-composite-actions)
- [Patterns](#patterns)

---

## Creating a Reusable Workflow

A reusable workflow is a standard workflow file that uses the `workflow_call` event trigger. Place it in `.github/workflows/` like any other workflow.

```yaml
# .github/workflows/build-and-test.yml
name: Build and Test

on:
  workflow_call:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run build
      - run: npm test
```

This is the simplest form — no inputs, no outputs, no secrets. Any workflow in a repository with access can call it.

## Defining Inputs

Inputs let callers parameterize the reusable workflow. Define them under `on.workflow_call.inputs`:

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  workflow_call:
    inputs:
      environment:
        description: "Target deployment environment"
        required: true
        type: string
      node-version:
        description: "Node.js version to use"
        required: false
        type: number
        default: 22
      dry-run:
        description: "Run without making changes"
        required: false
        type: boolean
        default: false
      log-level:
        description: "Logging verbosity"
        required: false
        type: string
        default: "info"

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}

      - run: npm ci

      - name: Deploy
        if: ${{ !inputs.dry-run }}
        run: |
          npm run deploy -- \
            --env "${{ inputs.environment }}" \
            --log-level "${{ inputs.log-level }}"

      - name: Dry run
        if: ${{ inputs.dry-run }}
        run: |
          echo "Would deploy to ${{ inputs.environment }}"
          npm run deploy -- --dry-run --env "${{ inputs.environment }}"
```

### Input Types

| Type | Description | Example Values |
|:-----|:------------|:---------------|
| `string` | Free-form text | `"production"`, `"v1.2.3"` |
| `number` | Numeric value | `22`, `3` |
| `boolean` | True or false | `true`, `false` |

The `choice` type is available for `workflow_dispatch` inputs (manual triggers) but not for `workflow_call` inputs. For reusable workflows, validate string inputs in your job steps if you need to constrain values.

## Defining Outputs

Outputs pass data from a reusable workflow back to the caller. Define them under `on.workflow_call.outputs` and map them to job outputs:

```yaml
on:
  workflow_call:
    outputs:
      version:
        description: "Resolved package version"
        value: ${{ jobs.build.outputs.version }}

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - name: Get version
        id: version
        run: echo "version=$(node -p 'require(\"./package.json\").version')" >> "$GITHUB_OUTPUT"
```

The caller accesses outputs through the job that called the reusable workflow:

```yaml
jobs:
  build:
    uses: ./.github/workflows/build.yml

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying ${{ needs.build.outputs.version }}"
```

## Declaring Secrets

Reusable workflows declare which secrets they expect. Mark secrets as `required: true` or `required: false`:

```yaml
on:
  workflow_call:
    secrets:
      DEPLOY_TOKEN:
        required: true
      SLACK_WEBHOOK:
        required: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: ./scripts/deploy.sh
      - name: Notify Slack
        if: ${{ secrets.SLACK_WEBHOOK != '' }}
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H "Content-Type: application/json" \
            -d '{"text": "Deployed successfully"}'
```

## Calling a Reusable Workflow

Use the `uses` key at the job level (not step level) to call a reusable workflow:

### Same Repository

```yaml
name: CI/CD

on:
  push:
    branches: [main]

jobs:
  test:
    uses: ./.github/workflows/build-and-test.yml

  deploy-staging:
    needs: test
    uses: ./.github/workflows/deploy.yml
    with:
      environment: staging
      dry-run: false
    secrets:
      DEPLOY_TOKEN: ${{ secrets.STAGING_DEPLOY_TOKEN }}

  deploy-production:
    needs: deploy-staging
    uses: ./.github/workflows/deploy.yml
    with:
      environment: production
    secrets:
      DEPLOY_TOKEN: ${{ secrets.PRODUCTION_DEPLOY_TOKEN }}
```

### Cross-Repository

Reference the full path including owner, repository, workflow file, and ref:

```yaml
jobs:
  lint:
    uses: my-org/shared-workflows/.github/workflows/lint.yml@v2

  test:
    uses: my-org/shared-workflows/.github/workflows/test-node.yml@main
    with:
      node-version: 22

  deploy:
    needs: [lint, test]
    uses: my-org/shared-workflows/.github/workflows/deploy.yml@v2
    with:
      environment: production
    secrets: inherit
```

A job that calls a reusable workflow cannot define `steps` alongside `uses`. The `uses` replaces the entire job definition — if you need additional steps, put them in a separate job.

## Passing Secrets

### Explicit Secret Passing

Pass each secret by name:

```yaml
jobs:
  deploy:
    uses: ./.github/workflows/deploy.yml
    secrets:
      DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
      SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
```

### Inherit All Secrets

Pass all caller secrets to the reusable workflow automatically:

```yaml
jobs:
  deploy:
    uses: ./.github/workflows/deploy.yml
    with:
      environment: production
    secrets: inherit
```

`secrets: inherit` passes every secret the caller has access to, including organization and environment secrets. Use this when the reusable workflow is trusted and you want to avoid maintaining an explicit list. Prefer explicit passing for third-party or less-trusted workflows.

## Nesting and Limits

Reusable workflows can call other reusable workflows, with these constraints:

| Limit | Value |
|:------|:------|
| Maximum nesting depth | 10 levels |
| Maximum total reusable workflow calls per run | 50 |
| Maximum workflow file size | 512 KB |

A reusable workflow cannot call another reusable workflow defined in the same file. Each reusable workflow must be a separate file.

```yaml
# This is valid: A calls B, B calls C (in separate files)
# caller.yml → build.yml → notify.yml

# This is NOT valid: calling a workflow defined in the same file
```

## Access Control

For a caller to use a reusable workflow in another repository:

- **Public repositories**: Any workflow can call reusable workflows in public repos.
- **Internal repositories** (Enterprise): Repositories in the same organization or enterprise can call them if the repository settings allow it. Go to **Settings > Actions > General > Access** and select "Accessible from repositories in the organization."
- **Private repositories**: Only other repositories in the same organization can call them, and only if explicitly allowed in repository settings.

## Versioning

Reference reusable workflows using tags, branches, or commit SHAs:

```yaml
# By tag — recommended for stability
uses: my-org/shared-workflows/.github/workflows/ci.yml@v2

# By branch — gets latest changes, may break
uses: my-org/shared-workflows/.github/workflows/ci.yml@main

# By SHA — most secure, immutable
uses: my-org/shared-workflows/.github/workflows/ci.yml@a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
```

### Semantic Versioning Strategy

Tag releases of your shared workflow repository and use major version tags that float to the latest minor/patch:

```bash
# Create a release
git tag v2.1.0
git push origin v2.1.0

# Move the major version tag to the latest release
git tag -f v2 v2.1.0
git push -f origin v2
```

Callers using `@v2` automatically get bug fixes and minor improvements without changing their workflow files. Breaking changes get a new major version (`@v3`).

## Composite Actions vs Reusable Workflows

Both provide reuse, but at different levels:

| Aspect | Composite Action | Reusable Workflow |
|:-------|:----------------|:------------------|
| **Scope** | Step-level reuse | Job/workflow-level reuse |
| **Execution** | Runs within a job step | Runs as a called workflow with its own jobs |
| **Defined in** | `action.yml` in any repo or directory | `.github/workflows/*.yml` |
| **Can define jobs** | No — only steps | Yes — full job definitions with runners |
| **Can use services/containers** | No | Yes |
| **Can set environment** | No | Yes |
| **Distribution** | Marketplace, repo, or local path | Repository reference only |
| **Caller syntax** | `uses:` at step level | `uses:` at job level |

### When to Use Each

**Use composite actions when** you want to bundle a sequence of steps that run within an existing job. Examples: lint and format, setup a specific toolchain, run a standard test sequence.

**Use reusable workflows when** you need full job definitions with their own runner selection, environment scoping, services, containers, or matrix strategies. Examples: complete CI pipeline, deployment workflow, release process.

## Creating Composite Actions

A composite action is defined in an `action.yml` file. Every `run` step in a composite action must specify a `shell`.

### Basic Composite Action

```yaml
# .github/actions/setup-project/action.yml
name: "Setup Project"
description: "Install dependencies and prepare the project for building"

inputs:
  node-version:
    description: "Node.js version"
    required: false
    default: "22"

outputs:
  cache-hit:
    description: "Whether the npm cache was hit"
    value: ${{ steps.cache.outputs.cache-hit }}

runs:
  using: composite
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}

    - name: Cache node_modules
      id: cache
      uses: actions/cache@v4
      with:
        path: node_modules
        key: ${{ runner.os }}-node-${{ inputs.node-version }}-${{ hashFiles('package-lock.json') }}

    - name: Install dependencies
      if: steps.cache.outputs.cache-hit != 'true'
      shell: bash
      run: npm ci

    - name: Verify installation
      shell: bash
      run: node --version && npm --version
```

Use it in a workflow:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup project
        uses: ./.github/actions/setup-project
        with:
          node-version: 22

      - run: npm test
```

### Sharing Composite Actions

- **Within a repository**: Place in `.github/actions/<name>/action.yml` and reference with `uses: ./.github/actions/<name>`.
- **Across an organization**: Create a dedicated repository (e.g., `my-org/actions`) and reference with `uses: my-org/actions/<name>@v1`.
- **Publicly via Marketplace**: Publish the repository containing `action.yml` at the root.

## Patterns

### Shared CI Template

A single reusable workflow replaces duplicated CI configs across every team repo:

```yaml
# In each consumer repo — two lines replace an entire CI file
jobs:
  ci:
    uses: org/shared-workflows/.github/workflows/node-ci.yml@v2
    with:
      node-version: 22
```

### Parameterized Deploy with Outputs

Combine inputs, secrets, and outputs to create a deploy workflow that callers can chain:

```yaml
# .github/workflows/deploy-reusable.yml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      image-tag:
        required: true
        type: string
    secrets:
      KUBE_CONFIG:
        required: true
    outputs:
      deployment-url:
        value: ${{ jobs.deploy.outputs.url }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.environment }}
      url: ${{ steps.deploy.outputs.url }}
    outputs:
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        id: deploy
        run: |
          kubectl set image deployment/app app=${{ inputs.image-tag }} -n ${{ inputs.environment }}
          kubectl rollout status deployment/app -n ${{ inputs.environment }} --timeout=300s
          URL=$(kubectl get ingress app -n ${{ inputs.environment }} -o jsonpath='{.spec.rules[0].host}')
          echo "url=https://$URL" >> "$GITHUB_OUTPUT"
        env:
          KUBECONFIG_DATA: ${{ secrets.KUBE_CONFIG }}
```

### Organization Workflow Templates

Place templates in your org's `.github` repository so they appear in the Actions tab of every repo:

```
.github/
  workflow-templates/
    node-ci.yml              # The workflow template
    node-ci.properties.json  # Metadata (name, description, filePatterns)
```
