# Advanced Patterns

> **Source:** https://docs.github.com/en/actions/using-workflows | **Written for:** GitHub Actions 2026

Workflow patterns beyond basic CI: concurrency control, monorepo filtering, conditional execution, self-hosted runners, release automation, and optimization.

## Table of Contents

- [Concurrency Groups](#concurrency-groups)
- [Path and Branch Filtering](#path-and-branch-filtering)
- [Monorepo CI Patterns](#monorepo-ci-patterns)
- [Conditional Execution](#conditional-execution)
- [Self-Hosted Runner Patterns](#self-hosted-runner-patterns)
- [Workflow Optimization](#workflow-optimization)
- [Release Automation](#release-automation)
- [Useful Patterns](#useful-patterns)

---

## Concurrency Groups

Concurrency groups prevent duplicate workflow runs. When a new run enters a group with an active run, it either queues or cancels the in-progress run.

### PR Workflows: Cancel Previous Runs

```yaml
name: CI
on:
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: npm ci && npm test
```

Two PRs run in parallel (different refs). Pushes to the same PR cancel previous runs (same ref).

### Production Deploys: Never Cancel

```yaml
concurrency:
  group: deploy-production
  cancel-in-progress: false
```

### Job-Level and Named Groups

Apply concurrency per-job instead of per-workflow. Use environment-based group names for deployment isolation:

```yaml
deploy:
  needs: test
  runs-on: ubuntu-latest
  concurrency:
    group: deploy-${{ inputs.environment || 'staging' }}
    cancel-in-progress: false
  steps:
    - run: ./deploy.sh
```

---

## Path and Branch Filtering

### Selective Triggering with Paths

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'package.json'
      - 'package-lock.json'
      - '.github/workflows/ci.yml'
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

`paths` and `paths-ignore` are mutually exclusive. For tags: `tags: ['v*']` matches version tags, `'!v*-alpha'` excludes alpha.

### Per-Job Path Decisions with dorny/paths-filter

Workflow-level `paths` is all-or-nothing. For per-job decisions, use `dorny/paths-filter`:

```yaml
jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - uses: dorny/paths-filter@de90cc6fb38fc0963ad72b210f1f284cd68cea36 # v3.0.2
        id: filter
        with:
          filters: |
            frontend:
              - 'apps/web/**'
            backend:
              - 'apps/api/**'

  test-frontend:
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: cd apps/web && npm ci && npm test
```

The same pattern applies to any number of filtered jobs. Each job checks its output flag and skips when its paths are unchanged.

---

## Monorepo CI Patterns

### Dynamic Matrix from Changed Services

Generate a matrix at runtime based on which directories changed:

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      services: ${{ steps.find.outputs.services }}
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
        with:
          fetch-depth: 0
      - id: find
        run: |
          CHANGED=$(git diff --name-only origin/main...HEAD \
            | grep '^services/' | cut -d'/' -f2 | sort -u \
            | jq -R -s -c 'split("\n") | map(select(. != ""))')
          echo "services=$CHANGED" >> "$GITHUB_OUTPUT"

  test:
    needs: detect
    if: needs.detect.outputs.services != '[]'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: ${{ fromJson(needs.detect.outputs.services) }}
      fail-fast: false
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: cd services/${{ matrix.service }} && npm ci && npm test
```

### Shared Reusable Workflow for Services

Define a common CI template, called per service:

```yaml
# .github/workflows/service-ci.yml (reusable)
on:
  workflow_call:
    inputs:
      service-path:
        required: true
        type: string
jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ inputs.service-path }}
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - uses: actions/setup-node@1a4442cacd436585916f15e7e73da3bfd52cb060 # v4.2.0
        with:
          node-version: 22
          cache: npm
          cache-dependency-path: ${{ inputs.service-path }}/package-lock.json
      - run: npm ci && npm run lint && npm test
```

Call it: `uses: ./.github/workflows/service-ci.yml` with `service-path: services/api`.

---

## Conditional Execution

### Branch and Event Gating

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

### Label-Gated Deployment

```yaml
on:
  pull_request:
    types: [labeled]

jobs:
  deploy-preview:
    if: github.event.label.name == 'deploy-preview'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: ./deploy-preview.sh
```

### Skip CI

GitHub natively supports `[skip ci]` or `[ci skip]` in commit messages. No configuration needed.

### Conditional on Previous Job Output

```yaml
jobs:
  check:
    runs-on: ubuntu-latest
    outputs:
      should-deploy: ${{ steps.decide.outputs.deploy }}
    steps:
      - id: decide
        run: |
          if [[ "${{ github.event.head_commit.message }}" == *"[deploy]"* ]]; then
            echo "deploy=true" >> "$GITHUB_OUTPUT"
          fi
  deploy:
    needs: check
    if: needs.check.outputs.should-deploy == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

---

## Self-Hosted Runner Patterns

### Runner Scale Set (2026)

The runner scale set replaces the Kubernetes-based ARC with a Go-based client supporting custom autoscaling without Kubernetes:

```yaml
jobs:
  build:
    runs-on: my-scale-set    # matches scale set name
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: make build
```

### Runner Groups and Label Routing

Organize runners by team or environment, restrict access via `gh api orgs/{org}/actions/runner-groups`. Target runners by labels:

```yaml
jobs:
  gpu-training:
    runs-on: [self-hosted, gpu, linux]
    steps:
      - run: python train.py
```

### Ephemeral Runners and Security

Use `--ephemeral` so each runner processes one job then terminates, preventing cross-job contamination. Run runners in isolated VMs or containers. Restrict runner groups to specific repositories. Never use self-hosted runners on public repositories.

---

## Workflow Optimization

### Fail Fast: Cheap Checks First

Lint takes seconds. Tests take minutes. Gate tests behind lint:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: npm ci && npm run lint && npx tsc --noEmit

  test:
    needs: lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
      fail-fast: false
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: npm ci && npm test -- --shard=${{ matrix.shard }}/4
```

### Cache Aggressively

Most `actions/setup-*` actions have built-in caching (e.g., `cache: npm`). For custom caches, use `actions/cache` with a key based on `hashFiles()` of lock files and `restore-keys` for partial matches.

---

## Release Automation

### Changelog and GitHub Release on Tag

```yaml
name: Release
on:
  push:
    tags: ['v*']
permissions:
  contents: write
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
        with:
          fetch-depth: 0
      - name: Generate changelog
        id: changelog
        run: |
          PREV_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")
          RANGE="${PREV_TAG:+$PREV_TAG..HEAD}"
          CHANGES=$(git log --pretty=format:"- %s (%h)" ${RANGE:-HEAD})
          echo "changes<<EOF" >> "$GITHUB_OUTPUT"
          echo "$CHANGES" >> "$GITHUB_OUTPUT"
          echo "EOF" >> "$GITHUB_OUTPUT"
      - uses: actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea # v7.0.1
        with:
          script: |
            const tag = context.ref.replace('refs/tags/', '');
            await github.rest.repos.createRelease({
              owner: context.repo.owner, repo: context.repo.repo,
              tag_name: tag, name: tag,
              body: `${{ steps.changelog.outputs.changes }}`,
              prerelease: tag.includes('-')
            });
```

### Publish to npm on Release

```yaml
on:
  release:
    types: [published]
permissions:
  contents: read
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - uses: actions/setup-node@1a4442cacd436585916f15e7e73da3bfd52cb060 # v4.2.0
        with:
          node-version: 22
          registry-url: https://registry.npmjs.org
      - run: npm ci && npm publish --provenance --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Publish to PyPI with Trusted Publishing

```yaml
on:
  release:
    types: [published]
permissions:
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - uses: astral-sh/setup-uv@6b9c6063abd6010835c3c7f4a7a2299c7d1ced39 # v4.1.0
      - run: uv build
      - uses: pypa/gh-action-pypi-publish@76f52bc884231f62b54a4f29d3f36c1bf688ee43 # v1.10.3
```

### Docker Build and Push to GHCR

Use `docker/setup-buildx-action`, `docker/login-action`, and `docker/build-push-action` (all SHA-pinned). Authenticate with `${{ secrets.GITHUB_TOKEN }}` and the `packages: write` permission. Use `cache-from: type=gha` and `cache-to: type=gha,mode=max` for layer caching via GitHub Actions cache backend. Tag images with `${{ github.ref_name }}` for version tags or `${{ github.sha }}` for commit-based tags.

---

## Useful Patterns

### Auto-Merge Dependabot PRs

```yaml
name: Auto-merge Dependabot
on: pull_request
permissions:
  contents: write
  pull-requests: write
jobs:
  auto-merge:
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - uses: dependabot/fetch-metadata@d7267f607e9d3fb96fc2fbe83e0af444713e90b7 # v2.2.0
        id: metadata
      - if: steps.metadata.outputs.update-type != 'version-update:semver-major'
        run: gh pr merge "${{ github.event.pull_request.number }}" --auto --squash
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Notify Slack on Failure

Add a job that runs only when a previous job fails:

```yaml
notify:
  needs: test
  if: failure()
  runs-on: ubuntu-latest
  steps:
    - env:
        SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK_URL }}
      run: |
        curl -X POST "$SLACK_WEBHOOK" -H 'Content-Type: application/json' \
          -d "{\"text\":\"CI failed on ${{ github.repository }} — <${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Run>\"}"
```

### Stale Issue Cleanup

```yaml
on:
  schedule:
    - cron: '0 6 * * 1'
permissions:
  issues: write
  pull-requests: write
jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@28ca1036281a5e5922ead5184a1bbf96e5fc984e # v9.0.0
        with:
          days-before-stale: 60
          days-before-close: 14
          stale-issue-label: stale
          exempt-issue-labels: pinned,security,bug
```

### Parallel Steps (Mid-2026)

Steps in the same `parallel-group` run simultaneously:

```yaml
- name: Lint
  run: npm run lint
  parallel-group: quality-checks
- name: Type check
  run: npx tsc --noEmit
  parallel-group: quality-checks
- name: Unit tests
  run: npm test
  parallel-group: quality-checks
```

Before this feature, use backgrounding with `wait`:

```yaml
- run: |
    npm run lint &
    npx tsc --noEmit &
    npm test &
    wait
```
