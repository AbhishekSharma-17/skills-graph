# CI/CD Patterns

> **Source:** https://developer.hashicorp.com/terraform/tutorials/automation | **Written for:** Terraform v1.11.x

Running Terraform in CI/CD is how you scale from a solo practitioner to a team. The core insight: **every change goes through a pull request, the plan is posted to the PR for review, and apply happens on merge**. This section covers GitOps workflows for GitHub Actions, GitLab CI, Atlantis, and HCP Terraform.

## Table of Contents

- [The GitOps model](#the-gitops-model)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Atlantis](#atlantis)
- [HCP Terraform / Terraform Cloud](#hcp-terraform--terraform-cloud)
- [Authenticating to clouds](#authenticating-to-clouds)
- [Managing multiple environments](#managing-multiple-environments)
- [Cost estimation](#cost-estimation)
- [Drift detection](#drift-detection)

## The GitOps Model

```
PR opened ──▶ fmt, validate, tflint, test ──▶ plan ──▶ post plan to PR ──▶ review
                                                                            │
                                                                            ▼
                                                            merge to main ──▶ apply
                                                                            │
                                                                            ▼
                                                              state updated + notifications
```

Principles:

- **No manual `apply` on developer laptops.** Apply is the CI system's job.
- **Plan output is the review artifact.** Reviewers compare the plan to the diff.
- **State lives in a remote backend.** See [`05-state.md`](05-state.md).
- **Secrets come from the CI platform**, never from files.
- **Every apply is reproducible** via the merged PR and `.terraform.lock.hcl`.

## GitHub Actions

### Baseline workflow — plan on PR, apply on merge

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  pull_request:
    paths: ['infra/**']
  push:
    branches: [main]
    paths: ['infra/**']

permissions:
  id-token: write       # OIDC to AWS
  contents: read
  pull-requests: write  # comment plan on PR

jobs:
  plan:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: infra
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::111111111111:role/GithubActionsTerraform
          aws-region: us-east-1

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.11.4

      - run: terraform fmt -check -recursive
      - run: terraform init
      - run: terraform validate
      - run: terraform plan -out=tfplan -input=false -no-color | tee plan.txt

      - uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('infra/plan.txt', 'utf8');
            const truncated = plan.length > 60000 ? plan.slice(0, 60000) + '\n...[truncated]' : plan;
            await github.rest.issues.createComment({
              ...context.repo,
              issue_number: context.issue.number,
              body: '### Terraform Plan\n```hcl\n' + truncated + '\n```'
            });

      - uses: actions/upload-artifact@v4
        with:
          name: tfplan
          path: infra/tfplan

  apply:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production   # GitHub environment gate
    defaults:
      run:
        working-directory: infra
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::111111111111:role/GithubActionsTerraform
          aws-region: us-east-1

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.11.4

      - run: terraform init
      - run: terraform apply -auto-approve -input=false
```

### Hardening

- **Concurrency** to avoid concurrent applies:

  ```yaml
  concurrency:
    group: terraform-prod
    cancel-in-progress: false
  ```

- **Required reviewers** via GitHub environments (production branch protection).
- **Require plan artifact in apply** — pull the saved plan from the PR and apply it verbatim to guarantee review-vs-apply parity.
- **CODEOWNERS** for `infra/**` to enforce platform team review.

### Matrix over environments

```yaml
strategy:
  matrix:
    env: [dev, staging, prod]
    include:
      - env: dev
        role: arn:aws:iam::111111111111:role/TfDev
      - env: staging
        role: arn:aws:iam::222222222222:role/TfStaging
      - env: prod
        role: arn:aws:iam::333333333333:role/TfProd
```

## GitLab CI

```yaml
# .gitlab-ci.yml
variables:
  TF_ROOT: ${CI_PROJECT_DIR}/infra
  TF_STATE_NAME: default

image: hashicorp/terraform:1.11.4

before_script:
  - cd $TF_ROOT

stages:
  - validate
  - plan
  - apply

fmt:
  stage: validate
  script: terraform fmt -check -recursive

validate:
  stage: validate
  script:
    - terraform init
    - terraform validate

plan:
  stage: plan
  script:
    - terraform init
    - terraform plan -out=tfplan
  artifacts:
    paths: ["$TF_ROOT/tfplan"]
    reports:
      terraform: ${TF_ROOT}/tfplan.json   # GitLab MR plan viewer
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

apply:
  stage: apply
  script:
    - terraform init
    - terraform apply -input=false tfplan
  dependencies: [plan]
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  when: manual       # require click-through
```

GitLab's managed Terraform state backend provides native state + locking:

```hcl
terraform {
  backend "http" {}
}
```

```bash
terraform init \
  -backend-config="address=https://gitlab.com/api/v4/projects/$PROJECT_ID/terraform/state/default" \
  -backend-config="lock_address=https://gitlab.com/api/v4/projects/$PROJECT_ID/terraform/state/default/lock" \
  -backend-config="unlock_address=https://gitlab.com/api/v4/projects/$PROJECT_ID/terraform/state/default/lock" \
  -backend-config="username=$CI_JOB_TOKEN_USERNAME" \
  -backend-config="password=$CI_JOB_TOKEN" \
  -backend-config="lock_method=POST" \
  -backend-config="unlock_method=DELETE" \
  -backend-config="retry_wait_min=5"
```

## Atlantis

Self-hosted PR automation server. Atlantis watches your git repos and runs Terraform in response to PR comments.

Workflow:
1. Open PR → Atlantis auto-runs `plan` and comments the output.
2. Reviewers approve.
3. Commenter types `atlantis apply`.
4. Atlantis runs `apply`, posts result, merges.

`atlantis.yaml`:

```yaml
version: 3
projects:
  - name: networking
    dir: infra/networking
    workspace: default
    autoplan:
      when_modified: ["*.tf", "*.tfvars", "../modules/**/*.tf"]
      enabled: true
    apply_requirements: [approved, mergeable]

  - name: apps
    dir: infra/apps
    workspace: default
    autoplan:
      when_modified: ["*.tf"]
```

Key features:
- Per-project auto-planning with fine-grained file watchers.
- Workspace locking to serialize applies.
- Pluggable custom workflows (add checkov, sentinel, cost estimation).

## HCP Terraform / Terraform Cloud

The managed SaaS: handles state, runs, variables, cost estimation, Sentinel policies, teams.

VCS-driven workspace setup:
1. Connect org to GitHub/GitLab/Bitbucket.
2. Create a workspace pointing at a repo + working directory.
3. Workspace auto-plans on PR, queues apply on merge.
4. Review plan in the HCP UI with a human-friendly diff.

`cloud` block in your root config:

```hcl
terraform {
  cloud {
    organization = "my-org"
    workspaces {
      tags = ["platform", "prod"]
    }
  }
}
```

Authenticate locally:
```bash
terraform login
```

In CI, use an API token:
```bash
TF_TOKEN_app_terraform_io=<token> terraform init
```

## Authenticating to Clouds

### AWS — OIDC (recommended)

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ACCT:role/GithubActionsTerraform
    aws-region: us-east-1
```

The role's trust policy grants `sts:AssumeRoleWithWebIdentity` to the GitHub OIDC provider. No static keys.

### Azure — Federated credentials
```yaml
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### GCP — Workload Identity Federation
```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/123/locations/global/workloadIdentityPools/gh/providers/gha
    service_account: tf-deployer@proj.iam.gserviceaccount.com
```

## Managing Multiple Environments

### Pattern A: Directory per environment

```
infra/
├── modules/
│   ├── network/
│   ├── database/
│   └── app/
├── dev/
│   ├── main.tf         # module calls
│   └── backend.hcl     # dev state config
├── staging/
└── prod/
```

Each env has its own state, its own `.tfvars`, and its own CI trigger. Changes flow dev → staging → prod via PR.

### Pattern B: Workspaces (simpler, more coupled)

One config, one state backend, one workspace per env:

```bash
terraform workspace new dev
terraform workspace select prod
terraform apply
```

Inside config:
```hcl
locals {
  env_config = {
    dev     = { instance_type = "t3.micro", count = 1 }
    prod    = { instance_type = "t3.large", count = 5 }
  }
  cfg = local.env_config[terraform.workspace]
}
```

Trade-offs:
- **Dir-per-env** — true isolation, harder to mix up prod and dev. Recommended for production.
- **Workspaces** — less repetition, faster onboarding. Accept the risk of wrong workspace.

### Pattern C: Terragrunt

Terragrunt (external tool) is a DRY wrapper around Terraform that's popular for multi-env/multi-account setups:

```hcl
# prod/database/terragrunt.hcl
terraform {
  source = "../../../modules/database"
}

include "root" {
  path = find_in_parent_folders()
}

inputs = {
  env           = "prod"
  instance_type = "db.r6g.large"
}
```

Terragrunt handles backend generation, dependency wiring, and parallel applies.

## Cost Estimation

### Infracost (OSS)

```bash
brew install infracost
infracost auth login
infracost breakdown --path=.
```

GitHub Actions integration:
```yaml
- uses: infracost/actions/setup@v3
  with:
    api-key: ${{ secrets.INFRACOST_API_KEY }}

- run: |
    infracost breakdown --path . --format json --out-file /tmp/infracost-base.json
    # after plan
    infracost diff --path . --compare-to /tmp/infracost-base.json --format json --out-file /tmp/infracost.json
    infracost comment github --path /tmp/infracost.json \
      --repo $GITHUB_REPOSITORY --pull-request ${{github.event.pull_request.number}} \
      --github-token ${{secrets.GITHUB_TOKEN}} --behavior update
```

### HCP Terraform Cost Estimation
Built-in on paid plans — posts to the plan output automatically.

## Drift Detection

Schedule a nightly refresh-only plan:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'

jobs:
  drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform plan -refresh-only -detailed-exitcode
        id: plan
        continue-on-error: true

      - uses: actions/github-script@v7
        if: steps.plan.outputs.exitcode == '2'
        with:
          script: |
            await github.rest.issues.create({
              ...context.repo,
              title: 'Terraform drift detected',
              body: 'Nightly drift check found divergence. Investigate or apply -refresh-only.'
            });
```

`-detailed-exitcode` returns `0` (no diff), `1` (error), or `2` (diff) — perfect for CI logic.

## Common Pitfalls

- **Shared workspaces, different laptops** — two engineers running `apply` concurrently corrupt state. Use state locking and enforce CI-only applies.
- **Secrets in plan output** — sensitive variables can leak into plan comments if not marked `sensitive = true`. Redact before posting.
- **State lock orphans** — kill -9 during apply leaves a lock. Surface a `terraform force-unlock` runbook to your team.
- **Runner IAM too permissive** — scope the CI role to only what the repo needs. Don't grant `AdministratorAccess`.
- **Drift ignored** — silent drift accumulates. Scheduled `plan -refresh-only` + paging on non-zero exit saves future incidents.

## Related

- [`05-state.md`](05-state.md) — backend setup, locking, workspaces.
- [`10-testing-and-validation.md`](10-testing-and-validation.md) — lint/test/policy gates in CI.
- [`12-best-practices.md`](12-best-practices.md) — secret management, least privilege.
