# Best Practices

> **Source:** https://developer.hashicorp.com/terraform/language/style | **Written for:** Terraform v1.11.x

Accumulated wisdom from running Terraform at scale. Follow these conventions and you'll avoid the most common sources of outages, drift, and team frustration.

## Table of Contents

- [Project structure](#project-structure)
- [Naming conventions](#naming-conventions)
- [State hygiene](#state-hygiene)
- [Secrets management](#secrets-management)
- [Security defaults](#security-defaults)
- [Immutable vs mutable infrastructure](#immutable-vs-mutable-infrastructure)
- [Versioning strategy](#versioning-strategy)
- [Code review checklist](#code-review-checklist)
- [Runbook essentials](#runbook-essentials)
- [Common mistakes](#common-mistakes)

## Project Structure

### Recommended layout for a mid-sized team

```
infra/
├── .pre-commit-config.yaml
├── .tflint.hcl
├── .terraform-version
├── modules/                    # reusable, versioned modules
│   ├── network/
│   ├── app-runtime/
│   └── rds-postgres/
├── envs/                       # one dir per environment, separate state
│   ├── dev/
│   │   ├── backend.hcl
│   │   ├── main.tf             # module calls
│   │   ├── terraform.tfvars
│   │   └── versions.tf
│   ├── staging/
│   └── prod/
└── bootstrap/                  # state bucket, IAM roles for CI
    └── main.tf
```

### Split large configurations

A single `apply` touching 500+ resources is slow, risky, and hard to review. Split by **bounded context**:

- `platform/` — VPC, Transit Gateway, DNS zones, shared IAM.
- `data/` — databases, caches, storage.
- `apps/<service-name>/` — one per service.

Each has its own state and its own CI pipeline. Share values via `terraform_remote_state`, SSM Parameter Store, or module outputs.

### Root modules stay thin

Root `.tf` files should be mostly module calls and variable wiring. Move resource definitions into modules. This makes the root readable and dramatically simpler to review.

## Naming Conventions

### Resources

- Local name `this` or `main` for the primary resource in a module (clean references: `aws_vpc.this.id`).
- `snake_case` for variable, local, and resource local names.
- `PascalCase` or `kebab-case` for cloud-side names (match org convention).
- Interpolate environment into names: `${var.project}-${var.env}`.

### Files

- `main.tf` — primary resources (< 300 lines; split further if longer).
- `variables.tf` — all `variable` declarations.
- `outputs.tf` — all `output` declarations.
- `providers.tf` — `terraform {}` block, provider configs.
- `data.tf` — data sources.
- `locals.tf` — locals if they're extensive.

### Tags

Apply a consistent tag set via `default_tags` on the provider:

```hcl
provider "aws" {
  default_tags {
    tags = {
      Environment = var.env
      Project     = var.project
      ManagedBy   = "terraform"
      Repo        = "github.com/org/infra"
      Owner       = var.team
      CostCenter  = var.cost_center
    }
  }
}
```

This covers 95% of your resources without per-resource duplication.

## State Hygiene

- **Remote backend always.** See [`05-state.md`](05-state.md).
- **One state per environment**, not per resource type.
- **Versioning + encryption** on the state bucket, mandatory.
- **MFA delete** on the state bucket for prod.
- **Least-privileged IAM** — CI role can read/write state; developers have read-only for debugging.
- **Never commit `terraform.tfstate`.**
- **Never manually edit state JSON.** Use `terraform state` commands.
- **Back up state regularly** to a separate bucket.

### `terraform state` commands you'll actually use

```bash
terraform state list                  # explore
terraform state show <addr>           # inspect
terraform state mv <old> <new>        # rename without destroy
terraform state rm <addr>             # remove from mgmt (without destroy)
terraform state pull > snapshot.json  # backup
```

## Secrets Management

**Rule 1:** Secrets never live in `.tf`, `.tfvars`, or VCS.

**Rule 2:** Secrets minimize their dwell time in state.

### Ranked by safety (most to least safe)

1. **Ephemeral resources and data sources** (Terraform 1.10+) — never stored in state. Use for runtime-only secrets.
2. **Secret manager reference** — store the ARN/ID in state, resolve at runtime on the target system (EC2 user_data fetches from SSM on boot).
3. **Variable marked `sensitive = true`** + `TF_VAR_*` env var. Value redacted in logs; still in state.
4. **Provider env var** (`AWS_SECRET_ACCESS_KEY`) — never reaches state.

### Patterns

```hcl
# Pattern: resolve secret at runtime, don't pass through Terraform
resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.env}/db/password"
  type  = "SecureString"
  value = random_password.db.result
  lifecycle {
    ignore_changes = [value]
  }
}

# EC2 user_data fetches at boot
resource "aws_instance" "app" {
  user_data = <<-EOT
    #!/bin/bash
    PASS=$(aws ssm get-parameter --name "/${var.env}/db/password" --with-decryption --query Parameter.Value --output text)
    # use $PASS
  EOT
}
```

```hcl
# Pattern: ephemeral fetch (1.10+)
ephemeral "aws_secretsmanager_secret_version" "db" {
  secret_id = "prod/db/password"
}

resource "aws_db_instance" "main" {
  password = ephemeral.aws_secretsmanager_secret_version.db.secret_string
}
```

### Never do

- `password = "hunter2"` hardcoded in `.tf`.
- Committing `.tfvars` files containing secrets.
- Storing secrets as outputs (even sensitive) without business need.
- Using `TF_LOG=trace` in CI with secret-bearing variables — logs can leak.

## Security Defaults

### Provider-level defaults

```hcl
provider "aws" {
  default_tags { tags = local.common_tags }
  # Enforce IMDSv2 via launch templates / userdata patterns.
}
```

### Encrypt everything at rest

```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.this.arn
    }
  }
}

resource "aws_db_instance" "main" {
  storage_encrypted = true
  kms_key_id        = aws_kms_key.db.arn
}
```

### Block public access by default

```hcl
resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### IAM least privilege

- Prefer `aws_iam_policy_document` (validated HCL) over raw JSON.
- Scope resource ARNs tightly — `arn:aws:s3:::my-bucket/app/*` not `*`.
- Separate roles per environment per service; don't share across accounts.

### Network segmentation

- Private subnets for workloads; public subnets only for ingress.
- Security groups over NACLs for most rules.
- VPC flow logs enabled.

### Audit with automated tooling

- `checkov -d .` — 1000+ built-in security checks.
- `trivy config .` (formerly tfsec).
- `tflint` with provider rulesets.

## Immutable vs Mutable Infrastructure

Prefer immutable:
- **AMIs baked by Packer** beat boot-time provisioning.
- **Container images** beat in-place package upgrades.
- **Blue/green** beats in-place upgrades for stateful services.

When immutable isn't possible (stateful DBs, shared caches), rely on `ignore_changes` and operational runbooks to manage drift gracefully.

## Versioning Strategy

### Pin Terraform version

```hcl
terraform {
  required_version = ">= 1.9.0, < 2.0.0"
}
```

Use `tfenv` or `.terraform-version` files for per-project pinning.

### Pin provider versions with `~>`

```hcl
required_providers {
  aws = {
    source  = "hashicorp/aws"
    version = "~> 5.80"    # patch updates only
  }
}
```

Commit `.terraform.lock.hcl` — this pins exact hashes.

### Pin module versions explicitly

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.14"
}

module "internal" {
  source = "github.com/my-org/tf-modules//network?ref=v2.0.0"
}
```

Never reference `main`/`master` branches in production configs.

### Upgrade cadence

- **Terraform core:** every 3-6 months. Read release notes for breaking changes.
- **Provider majors:** follow upstream migration guide; run in a branch first.
- **Internal modules:** semver, with `moved` blocks for refactors.

## Code Review Checklist

When reviewing an infrastructure PR:

### Plan output
- [ ] Plan matches PR intent.
- [ ] No unexpected `-/+` replacements of stateful resources.
- [ ] No resources destroyed accidentally.
- [ ] No `(known after apply)` values that should be known.

### Config quality
- [ ] `terraform fmt` clean.
- [ ] New variables have `description` and `type`.
- [ ] New outputs have `description`.
- [ ] New modules pin provider versions.
- [ ] No secrets in code.
- [ ] No wide-open security groups (`0.0.0.0/0` on non-HTTPS ports).
- [ ] Resources have required tags.
- [ ] No `-target` or `-replace` workarounds encoded into the workflow.

### Testing
- [ ] `terraform validate` passes.
- [ ] `tflint` passes.
- [ ] `checkov` passes (or findings waived with explanation).
- [ ] If a module, `terraform test` passes.

### Operational impact
- [ ] Rollback path identified.
- [ ] Stateful changes (DB migration, bucket rename) noted in description.
- [ ] Dependent services informed.

## Runbook Essentials

Write these runbooks before you need them:

1. **Force-unlock.** How to identify an orphaned lock and `terraform force-unlock <id>` safely.
2. **Import existing resource.** Steps with `import` block.
3. **Rollback a bad apply.** `terraform apply -refresh-only` then revert PR.
4. **State corruption.** Restore from S3 version history.
5. **Provider upgrade.** Migration guide link + local test branch steps.
6. **Drift detected.** Evaluate drift, either reconcile via apply or update config to match reality.
7. **Break-glass access.** How to assume the admin role when CI is broken.

## Common Mistakes

### 1. Hand-editing state
**Don't.** Use `terraform state` subcommands.

### 2. Using `count` on resources with stable identity
Switching elements causes destruction. Use `for_each`.

### 3. `terraform apply -target=X` as regular workflow
Targeting hides side effects. Reserve for incident response.

### 4. Storing provider versions in `.tfvars`
They belong in `required_providers`, not in runtime vars.

### 5. One giant root module
Blast radius is the entire stack. Split by bounded context.

### 6. Relying on `terraform refresh` auto-reconciling
Refresh mutates state silently. Prefer `terraform apply -refresh-only` with explicit review.

### 7. Skipping `.terraform.lock.hcl`
Without it, `init` may silently upgrade providers. Commit the lock.

### 8. Mixing `provisioner` with declarative resources
Provisioners break the model. Prefer cloud-init or config management.

### 9. Running `terraform destroy` in CI
Too easy to destroy prod by merging the wrong branch. Make destroy manual-only.

### 10. Trusting the registry
Public modules can have vulnerabilities or unwanted behavior. Fork and audit anything in critical paths.

## Quality Signals for Mature Teams

You know your Terraform setup is healthy when:

- A new engineer can `git clone`, `terraform init`, and see a no-op plan on day one.
- Every PR posts a plan diff automatically.
- Nightly drift detection reports zero drift most mornings.
- Upgrading providers is a 30-minute task, not a month-long project.
- State recovery has been practiced at least once (game day).
- You have module tests that run in under 2 minutes.
- `terraform destroy` is as scary as `rm -rf` — so you don't do it without a reason.

## Related

- [`05-state.md`](05-state.md) — state storage and protection.
- [`06-modules.md`](06-modules.md) — module authoring and versioning.
- [`10-testing-and-validation.md`](10-testing-and-validation.md) — the validation toolchain.
- [`11-cicd-patterns.md`](11-cicd-patterns.md) — GitOps workflows and review gates.
