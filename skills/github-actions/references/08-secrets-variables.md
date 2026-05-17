# Secrets and Variables

> Source: [docs.github.com/en/actions/security-for-github-actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

Secrets and variables let you store configuration data at the repository, organization, and environment levels. Secrets are encrypted and masked in logs. Variables are plaintext and intended for non-sensitive configuration. Both are injected into workflows via expressions.

## Table of Contents

- [Repository Secrets](#repository-secrets)
- [Organization Secrets](#organization-secrets)
- [Environment Secrets](#environment-secrets)
- [Accessing Secrets in Workflows](#accessing-secrets-in-workflows)
- [GITHUB_TOKEN](#github_token)
- [Personal Access Tokens](#personal-access-tokens)
- [Secret Masking and Security](#secret-masking-and-security)
- [Configuration Variables](#configuration-variables)
- [Default Environment Variables](#default-environment-variables)
- [Best Practices](#best-practices)

---

## Repository Secrets

Create repository secrets through **Settings > Secrets and variables > Actions > New repository secret**. Each secret is scoped to a single repository and available to all workflows in that repository.

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        run: |
          curl -X POST "${{ secrets.DEPLOY_URL }}/api/deploy" \
            -H "Authorization: Bearer ${{ secrets.DEPLOY_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"ref": "${{ github.sha }}"}'
```

Secret names are case-insensitive and can only contain alphanumeric characters and underscores. They must not start with `GITHUB_` (reserved prefix). Maximum size per secret value is 48 KB.

## Organization Secrets

Organization secrets are created through the organization settings page and shared across multiple repositories. When creating an organization secret, you set a visibility policy:

| Visibility | Description |
|:-----------|:------------|
| **All repositories** | Every repository in the organization can access the secret |
| **Private repositories** | Only private repositories can access the secret |
| **Selected repositories** | Only explicitly chosen repositories have access |

Organization secrets are useful for shared credentials like cloud provider keys, Docker registry tokens, or API keys used across multiple services.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
```

When a repository secret has the same name as an organization secret, the repository secret takes precedence.

## Environment Secrets

Environment secrets are scoped to a specific deployment environment. They override repository-level secrets of the same name when the job references that environment.

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy
        run: |
          echo "Deploying to ${{ vars.API_URL }}"
          ./deploy.sh --token "${{ secrets.DEPLOY_KEY }}"

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production
    steps:
      - name: Deploy
        run: |
          echo "Deploying to ${{ vars.API_URL }}"
          ./deploy.sh --token "${{ secrets.DEPLOY_KEY }}"
```

In this example, `DEPLOY_KEY` and `API_URL` can have different values in the `staging` and `production` environments. The `environment:` key on the job determines which set of secrets and variables are injected.

## Accessing Secrets in Workflows

### Direct Interpolation

Use the `${{ secrets.NAME }}` expression anywhere in your workflow YAML:

```yaml
steps:
  - name: Call API
    run: curl -H "Authorization: token ${{ secrets.API_TOKEN }}" https://api.example.com
```

### Mapping to Environment Variables

Map secrets to environment variables for cleaner shell scripts and better compatibility with tools that read from `env`:

```yaml
steps:
  - name: Run database migration
    env:
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
      REDIS_URL: ${{ secrets.REDIS_URL }}
    run: |
      npx prisma migrate deploy
      node scripts/seed.js
```

Mapping to environment variables is the preferred approach. It avoids accidental secret exposure through shell history, keeps your `run` blocks readable, and works naturally with tools that expect `process.env` or `os.environ`.

### Secrets as Action Inputs

```yaml
steps:
  - name: Deploy to Vercel
    uses: amondnet/vercel-action@v25
    with:
      vercel-token: ${{ secrets.VERCEL_TOKEN }}
      vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
      vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
      working-directory: ./frontend
```

## GITHUB_TOKEN

Every workflow run automatically receives a `GITHUB_TOKEN` — a short-lived token scoped to the repository where the workflow runs. You do not need to create or manage this token.

### Default Permissions

Since 2023, new repositories default to **read-only** permissions for `GITHUB_TOKEN`. You can change the default in **Settings > Actions > General > Workflow permissions**, or override per workflow with the `permissions` key.

### Customizing Permissions

Set permissions at the workflow or job level:

```yaml
name: Release

permissions:
  contents: write
  packages: write
  pull-requests: read

on:
  push:
    tags: ["v*"]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
```

Job-level permissions override workflow-level permissions entirely (they do not merge):

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - run: npm run lint

  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      deployments: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: Deploy with OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/deploy
          aws-region: us-east-1
```

### Available Permission Scopes

| Scope | Controls |
|:------|:---------|
| `actions` | Workflow runs, artifacts, caches |
| `checks` | Check runs and check suites |
| `contents` | Repository contents, commits, branches, tags, releases |
| `deployments` | Deployment statuses and environments |
| `id-token` | OIDC token for cloud provider authentication |
| `issues` | Issues and issue comments |
| `packages` | GitHub Packages (read/write) |
| `pages` | GitHub Pages builds and deployments |
| `pull-requests` | Pull requests and PR comments |
| `repository-projects` | Project boards |
| `security-events` | Code scanning and Dependabot alerts |
| `statuses` | Commit statuses |

Each scope accepts `read`, `write`, or `none`. Setting `permissions: {}` (empty object) revokes all permissions — useful as a top-level default when you want explicit opt-in per job.

### Token Lifetime and Scope

The `GITHUB_TOKEN` expires when the job completes. It cannot be passed between jobs in the same workflow run. Each job gets its own token instance. The token is scoped to the current repository and cannot access other repositories.

## Personal Access Tokens

Use a Personal Access Token (PAT) when you need cross-repository access or operations that `GITHUB_TOKEN` cannot perform:

```yaml
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger deploy in another repo
        run: |
          gh workflow run deploy.yml \
            --repo org/infrastructure \
            --ref main \
            --field version="${{ github.sha }}"
        env:
          GH_TOKEN: ${{ secrets.CROSS_REPO_PAT }}
```

Fine-grained PATs (recommended over classic tokens) let you scope access to specific repositories and permissions. Store the PAT as a repository or organization secret.

## Secret Masking and Security

GitHub automatically masks secret values in workflow logs. If `secrets.API_KEY` contains `abc123`, any occurrence of `abc123` in log output is replaced with `***`.

### Masking Limitations

- Structured values may partially leak. If a secret is a JSON object, individual fields within it may not be masked.
- Short secret values (under 4 characters) are not masked.
- Multiline secrets: only the first line is registered for masking by default.

### Registering Additional Masks

```yaml
steps:
  - name: Decode and mask a derived value
    run: |
      DECODED=$(echo "${{ secrets.ENCODED_KEY }}" | base64 --decode)
      echo "::add-mask::$DECODED"
      echo "Using decoded key in subsequent commands"
      ./tool --key "$DECODED"
```

### Security Rules

**Forked pull requests**: Secrets are not available to workflows triggered by pull requests from forks. This prevents malicious forks from exfiltrating secrets. The `pull_request` event from a fork runs with read-only permissions and no secret access.

**pull_request_target**: This event runs in the context of the base repository, granting access to secrets even for fork PRs. This is a significant security risk if the workflow checks out and executes code from the fork:

```yaml
# DANGEROUS — do not do this
on: pull_request_target
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # Checks out fork code
      - run: npm ci && npm test  # Executes untrusted code with access to secrets
```

If you must use `pull_request_target`, never check out the fork's code, or run it in a separate job without secret access.

**Never echo secrets**: Even though masking exists, avoid `echo ${{ secrets.KEY }}` or logging secrets intentionally. Masking is a safety net, not a feature to rely on.

## Configuration Variables

Variables store non-sensitive configuration values in plaintext. Access them with `${{ vars.NAME }}`.

### Scoping Levels

Variables can be defined at three levels with the same precedence rules as secrets:

| Level | Override Behavior |
|:------|:-----------------|
| Organization | Base defaults across repos |
| Repository | Overrides organization variables of the same name |
| Environment | Overrides repository variables when the job uses that environment |

### Limits

- 100 variables per organization
- 100 variables per repository
- 100 variables per environment
- 48 KB maximum value size per variable

### Usage Examples

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Build with configuration
        env:
          API_BASE_URL: ${{ vars.API_BASE_URL }}
          LOG_LEVEL: ${{ vars.LOG_LEVEL }}
          FEATURE_FLAGS: ${{ vars.FEATURE_FLAGS }}
        run: |
          echo "Building for ${{ vars.ENVIRONMENT_NAME }}"
          npm run build

  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to region
        run: |
          ./deploy.sh \
            --region "${{ vars.AWS_REGION }}" \
            --cluster "${{ vars.ECS_CLUSTER }}" \
            --service "${{ vars.ECS_SERVICE }}"
```

Use variables for deployment URLs, feature flags, region settings, cluster names, log levels, and any configuration that changes between environments but is not sensitive.

## Default Environment Variables

GitHub sets environment variables automatically for every workflow run. These are available in `run` steps without any configuration:

| Variable | Description | Example Value |
|:---------|:------------|:-------------|
| `GITHUB_SHA` | Full commit SHA that triggered the run | `a1b2c3d4e5f6...` |
| `GITHUB_REF` | Branch or tag ref | `refs/heads/main` |
| `GITHUB_REF_NAME` | Short branch or tag name | `main` |
| `GITHUB_REPOSITORY` | Owner and repository name | `octocat/hello-world` |
| `GITHUB_REPOSITORY_OWNER` | Repository owner | `octocat` |
| `GITHUB_ACTOR` | User or app that triggered the workflow | `octocat` |
| `GITHUB_WORKFLOW` | Workflow name | `CI` |
| `GITHUB_RUN_ID` | Unique ID for the workflow run | `1234567890` |
| `GITHUB_RUN_NUMBER` | Sequential number for runs of this workflow | `42` |
| `GITHUB_EVENT_NAME` | Event that triggered the workflow | `push` |
| `RUNNER_OS` | OS of the runner | `Linux` |
| `RUNNER_ARCH` | Architecture of the runner | `X64` |

Access these in shell commands directly:

```yaml
steps:
  - name: Tag Docker image
    run: |
      docker build -t myapp:$GITHUB_SHA .
      docker tag myapp:$GITHUB_SHA registry.example.com/myapp:$GITHUB_REF_NAME
      docker push registry.example.com/myapp:$GITHUB_REF_NAME
```

Access them in expressions using the `github` context:

```yaml
steps:
  - name: Print run info
    run: echo "Run ${{ github.run_number }} on ${{ github.ref_name }} by ${{ github.actor }}"
```

## Best Practices

**Prefer OIDC over long-lived credentials.** Instead of storing AWS/GCP/Azure access keys as secrets, use OpenID Connect to get short-lived tokens:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions
          aws-region: us-east-1

      - run: aws s3 sync ./dist s3://my-bucket
```

**Rotate secrets regularly.** Set calendar reminders to rotate API keys, tokens, and credentials. When rotating, update the secret value in GitHub settings — all subsequent workflow runs pick up the new value immediately.

**Use environment scoping for sensitive secrets.** Put production database credentials in the `production` environment with required reviewers. This ensures no workflow can access production secrets without approval.

**Set minimum permissions for GITHUB_TOKEN.** Always declare `permissions` explicitly rather than relying on defaults:

```yaml
permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

**Separate secrets from variables.** Use secrets for API keys, tokens, passwords, and connection strings. Use variables for URLs, feature flags, region names, and configuration that you would not mind seeing in a log.

**Use `secrets: inherit` sparingly.** When calling reusable workflows, prefer passing specific secrets by name rather than inheriting all secrets. This makes the dependency explicit and limits exposure.
