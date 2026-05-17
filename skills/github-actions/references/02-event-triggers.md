# Event Triggers

> Source: [docs.github.com/en/actions/using-workflows/events-that-trigger-workflows](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows) | All Trigger Events

## Table of Contents

- [Push Events](#push-events)
- [Pull Request Events](#pull-request-events)
- [Schedule (Cron)](#schedule-cron)
- [Manual Triggers (workflow_dispatch)](#manual-triggers-workflow_dispatch)
- [Reusable Workflows (workflow_call)](#reusable-workflows-workflow_call)
- [External Triggers (repository_dispatch)](#external-triggers-repository_dispatch)
- [Release Events](#release-events)
- [Issue and Comment Events](#issue-and-comment-events)
- [Branch and Tag Events](#branch-and-tag-events)
- [Workflow Run Events](#workflow-run-events)
- [Other Useful Events](#other-useful-events)
- [Event Filtering Patterns](#event-filtering-patterns)
- [Activity Types](#activity-types)
- [Event Payload Access](#event-payload-access)
- [Multiple Event Configuration](#multiple-event-configuration)

---

## Push Events

Triggered when commits are pushed to matching branches or tags.

```yaml
on:
  push:
    branches:
      - main
      - release/*
      - '!release/*-beta'       # Exclude beta branches
    tags:
      - 'v*'
    paths:
      - 'src/**'
      - 'package.json'
      - '!src/**/*.test.ts'     # Exclude test files
```

Use `branches-ignore`, `tags-ignore`, and `paths-ignore` as alternatives to negation patterns. You cannot mix `branches` and `branches-ignore` in the same event (same for tags and paths).

Key push event context values: `github.event.before` (previous SHA), `github.event.after` (new SHA), `github.event.commits` (commit array), `github.event.head_commit`, `github.event.forced` (force push).

## Pull Request Events

### pull_request

Runs in the context of the merge commit. Has read-only access to secrets for PRs from forks.

```yaml
on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, ready_for_review, labeled]
    paths:
      - 'src/**'
      - 'tests/**'
```

Default types when none specified: `opened`, `synchronize`, `reopened`.

All activity types: `opened`, `synchronize`, `reopened`, `closed`, `ready_for_review`, `converted_to_draft`, `labeled`, `unlabeled`, `assigned`, `unassigned`, `review_requested`, `review_request_removed`, `edited`, `auto_merge_enabled`, `auto_merge_disabled`.

### pull_request_target

Runs in the context of the base branch with full secret access even for fork PRs. The workflow code comes from the base branch.

```yaml
on:
  pull_request_target:
    types: [opened, synchronize]

jobs:
  label:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/labeler@v5
```

Safe uses: labeling, commenting, approving. Never checkout and execute PR code with secrets.

## Schedule (Cron)

POSIX cron syntax. Runs against the default branch.

```yaml
on:
  schedule:
    - cron: '0 6 * * 1-5'      # 6:00 AM UTC, weekdays
    - cron: '0 0 * * 0'        # Midnight UTC, Sundays
```

Cron field reference:

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
* * * * *
```

| Schedule | Expression |
|:---------|:-----------|
| Every 15 minutes | `*/15 * * * *` |
| Daily at midnight UTC | `0 0 * * *` |
| Weekdays at 9 AM UTC | `0 9 * * 1-5` |
| Weekly on Monday | `0 0 * * 1` |
| Monthly on the 1st | `0 0 1 * *` |
| Every 6 hours | `0 */6 * * *` |

Timezone support (available since late 2025):

```yaml
on:
  schedule:
    - cron: '0 9 * * 1-5'
      timezone: America/New_York    # 9 AM Eastern, weekdays
```

Without `timezone`, cron uses UTC. The shortest guaranteed interval is 5 minutes. Scheduled workflows are automatically disabled after 60 days of no repository activity.

## Manual Triggers (workflow_dispatch)

Manual triggering from the GitHub UI, CLI, or REST API with typed inputs.

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options: [development, staging, production]
        default: staging
      dry_run:
        description: 'Dry run without deploying'
        type: boolean
        default: true
      version:
        description: 'Version to deploy'
        type: string
      log_level:
        description: 'Log verbosity'
        type: choice
        options: [debug, info, warn, error]
        default: info

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        if: inputs.dry_run == false
        run: echo "Deploying ${{ inputs.version }} to ${{ inputs.environment }}"
      - name: Dry run
        if: inputs.dry_run
        run: echo "DRY RUN -- would deploy ${{ inputs.version }} to ${{ inputs.environment }}"
```

Input types: `string`, `boolean`, `choice`, `environment`. Trigger via CLI:

```bash
gh workflow run deploy.yml -f environment=staging -f dry_run=false -f version=1.2.3
```

## Reusable Workflows (workflow_call)

Define a workflow callable from other workflows with inputs, outputs, and secrets.

Reusable workflow (`.github/workflows/reusable-test.yml`):

```yaml
on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '22'
    outputs:
      coverage:
        description: 'Test coverage percentage'
        value: ${{ jobs.test.outputs.coverage }}
    secrets:
      CODECOV_TOKEN:
        required: false

jobs:
  test:
    runs-on: ubuntu-latest
    outputs:
      coverage: ${{ steps.cov.outputs.percentage }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: npm
      - run: npm ci && npm test
      - id: cov
        run: echo "percentage=87" >> "$GITHUB_OUTPUT"
```

Caller:

```yaml
jobs:
  test:
    uses: ./.github/workflows/reusable-test.yml
    with:
      node-version: '22'
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

  report:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: echo "Coverage was ${{ needs.test.outputs.coverage }}%"
```

Reference from same repo (`./.github/workflows/file.yml`), another repo (`owner/repo/.github/workflows/file.yml@ref`), or across an organization.

## External Triggers (repository_dispatch)

Trigger from external systems via the GitHub API.

```yaml
on:
  repository_dispatch:
    types: [deploy, rollback]

jobs:
  handle:
    runs-on: ubuntu-latest
    steps:
      - name: Handle deploy
        if: github.event.action == 'deploy'
        run: echo "Deploying ${{ github.event.client_payload.version }}"
```

Trigger via API:

```bash
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/OWNER/REPO/dispatches" \
  -d '{"event_type":"deploy","client_payload":{"version":"2.1.0"}}'
```

## Release Events

```yaml
on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: https://registry.npmjs.org
      - run: npm ci && npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Activity types: `published`, `unpublished`, `created`, `edited`, `deleted`, `prereleased`, `released`. Use `released` for non-pre-release only. Access data: `github.event.release.tag_name`, `.name`, `.prerelease`, `.body`.

## Issue and Comment Events

```yaml
on:
  issues:
    types: [opened, labeled]
  issue_comment:
    types: [created]

jobs:
  triage:
    if: github.event_name == 'issues' && github.event.action == 'opened'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const body = context.payload.issue.body || '';
            const labels = [];
            if (body.includes('bug')) labels.push('bug');
            if (body.includes('feature')) labels.push('enhancement');
            if (labels.length > 0) {
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                labels
              });
            }

  slash-command:
    if: github.event_name == 'issue_comment' && startsWith(github.event.comment.body, '/deploy')
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploy requested by ${{ github.event.comment.user.login }}"
```

The `issue_comment` event fires on both issue and PR comments. Check `github.event.issue.pull_request` to distinguish.

## Branch and Tag Events

```yaml
on:
  create:    # Branch or tag created
  delete:    # Branch or tag deleted

jobs:
  on-branch-create:
    if: github.event.ref_type == 'branch'
    runs-on: ubuntu-latest
    steps:
      - run: echo "New branch: ${{ github.event.ref }}"
```

## Workflow Run Events

Trigger after another workflow completes:

```yaml
on:
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]

jobs:
  deploy:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    steps:
      - run: echo "CI passed on main, deploying..."
```

Always runs on the default branch. The `workflows` field accepts workflow names (the `name:` field, not filenames).

## Other Useful Events

| Event | Trigger | Use Case |
|:------|:--------|:---------|
| `deployment` | Deployment created via API | Custom deployment pipelines |
| `deployment_status` | Deployment status changes | Post-deployment notifications |
| `page_build` | GitHub Pages build | Verify Pages deployment |
| `registry_package` | Package published/updated | Cross-repo package workflows |
| `discussion` | Discussion created/edited | Community management |
| `merge_group` | Merge queue events | Merge queue workflows |

## Event Filtering Patterns

Glob patterns for branches/tags:

```yaml
on:
  push:
    branches:
      - main                    # Exact match
      - 'release/**'            # Matches release/1.0, release/2.0/rc1
      - 'feature/*'             # Matches feature/login, NOT feature/auth/oauth
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+' # Semver tags
```

Path filtering for monorepos:

```yaml
on:
  push:
    paths: ['packages/api/**', 'packages/shared/**', 'package.json']
```

## Activity Types

Every webhook event has default activity types. Specify `types` to narrow the trigger:

```yaml
on:
  pull_request_review:
    types: [submitted]           # Only on approval/review submission
  issues:
    types: [labeled]             # Only when labeled
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
```

If you omit `types`, the event uses its defaults.

## Event Payload Access

Access event data through `github.event`:

```yaml
steps:
  - name: PR info
    if: github.event_name == 'pull_request'
    run: |
      echo "PR #${{ github.event.pull_request.number }}"
      echo "Title: ${{ github.event.pull_request.title }}"
      echo "Author: ${{ github.event.pull_request.user.login }}"
      echo "Base: ${{ github.event.pull_request.base.ref }}"
      echo "Head: ${{ github.event.pull_request.head.ref }}"

  - name: Push info
    if: github.event_name == 'push'
    run: |
      echo "Ref: ${{ github.ref }}"
      echo "SHA: ${{ github.sha }}"
      echo "Commit: ${{ github.event.head_commit.message }}"
      echo "Forced: ${{ github.event.forced }}"
```

## Multiple Event Configuration

A single workflow responding to many events:

```yaml
name: CI/CD

on:
  push:
    branches: [main]
    paths-ignore: ['**.md']
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'
  workflow_dispatch:
    inputs:
      skip_tests:
        type: boolean
        default: false
  release:
    types: [published]

jobs:
  test:
    if: github.event_name != 'release' && (github.event_name != 'workflow_dispatch' || !inputs.skip_tests)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test

  deploy-staging:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying to staging"

  deploy-production:
    if: github.event_name == 'release'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: echo "Deploying ${{ github.event.release.tag_name }}"

  weekly-audit:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm audit --audit-level=high
```

Use `github.event_name` in `if` conditions to route jobs based on the triggering event.
