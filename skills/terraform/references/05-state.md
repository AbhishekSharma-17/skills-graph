# State

> **Source:** https://developer.hashicorp.com/terraform/language/state | **Written for:** Terraform v1.11.x

State is Terraform's memory. It maps resource addresses in your configuration (`aws_instance.web`) to real-world object IDs (`i-0123456789abcdef0`), caches attribute values, and tracks dependencies. Understanding state is the single biggest leap from Terraform novice to practitioner.

## What State Contains

By default, state lives in `terraform.tfstate` (JSON) in the working directory. It records:

- **Resource metadata** — type, name, provider, module path
- **Resource ID and attributes** — cached snapshot from the last refresh
- **Module hierarchy** — which resources belong to which module instance
- **Output values** — the last computed output values
- **Version metadata** — terraform version, serial number, lineage

Example fragment:

```json
{
  "version": 4,
  "terraform_version": "1.11.4",
  "serial": 42,
  "lineage": "abc-123",
  "resources": [
    {
      "mode": "managed",
      "type": "aws_instance",
      "name": "web",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "attributes": {
            "id": "i-0123456789abcdef0",
            "ami": "ami-abc",
            "instance_type": "t3.micro",
            "private_ip": "10.0.1.42"
          }
        }
      ]
    }
  ]
}
```

## Why Remote State?

Local state is fine for learning. For any real project, use a **remote backend**:

| Problem with local state | Remote backend fix |
|--------------------------|--------------------|
| Only one engineer can plan/apply safely | State locking prevents concurrent modification |
| State lost if laptop dies | Durable cloud storage with versioning |
| Secrets live in local `.tfstate` | Encrypt at rest; IAM-restrict access |
| Two engineers can't share outputs | `terraform_remote_state` data source |
| No audit trail | Backend versioning + access logs |

## Backend Configuration

Declare in the `terraform {}` block:

```hcl
terraform {
  backend "s3" {
    bucket         = "my-org-tfstate"
    key            = "networking/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
    kms_key_id     = "alias/tfstate"
  }
}
```

Note: you cannot interpolate variables inside a `backend` block. Use partial config + CLI args:

```hcl
terraform {
  backend "s3" {}
}
```

```bash
terraform init \
  -backend-config="bucket=my-org-tfstate-${ENV}" \
  -backend-config="key=networking/${ENV}/terraform.tfstate" \
  -backend-config="region=us-east-1"
```

## Supported Backends

| Backend | Lock Mechanism | Use Case |
|---------|----------------|----------|
| `s3` | DynamoDB table (or S3 native, 1.10+) | AWS shops, battle-tested |
| `azurerm` | Blob lease | Azure infra |
| `gcs` | Native object lock | GCP infra |
| `http` | Custom via PUT/POST/DELETE | GitLab, Atlantis, custom platforms |
| `remote` | Native | Terraform Cloud/Enterprise |
| `cloud` | Native | HCP Terraform (newer block) |
| `kubernetes` | Secret + lease | Cluster-local state |
| `pg` | Advisory lock | Self-hosted Postgres |
| `local` | File lock | Dev only |

### S3 Backend — 2025 recommended setup

Terraform 1.10 added native S3 locking (no DynamoDB needed). Enable with `use_lockfile = true`:

```hcl
terraform {
  backend "s3" {
    bucket       = "my-org-tfstate"
    key          = "platform/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
```

For older providers, keep the DynamoDB pattern:

```bash
# One-time setup
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### HCP Terraform / Terraform Cloud

```hcl
terraform {
  cloud {
    organization = "my-org"
    workspaces {
      name = "platform-prod"
    }
  }
}
```

`terraform login` authenticates locally; CI uses `TF_TOKEN_app_terraform_io`.

## Workspaces

Workspaces are named, isolated state instances within the same backend.

```bash
terraform workspace list
terraform workspace new dev
terraform workspace select staging
terraform workspace show
terraform workspace delete old-env
```

Inside config, reference `terraform.workspace`:

```hcl
resource "aws_s3_bucket" "example" {
  bucket = "app-${terraform.workspace}"
}
```

**When to use workspaces:**
- Short-lived environments (PR-preview stacks, ephemeral test infra).
- Thin variations of the same config (different region, different account).

**When *not* to use workspaces:**
- Hard-boundary environments (dev vs prod). Use separate **backends** or at least separate state `key` values — a mistake on the CLI workspace switcher shouldn't be able to destroy prod.

## State Locking

When a state operation starts, the backend acquires a lock. Other invocations block (or error out) until the lock is released.

```bash
# Forcibly release a stuck lock (careful!)
terraform force-unlock 12345-abcde-lock-id
```

Debug locks with `TF_LOG=debug`. Stuck locks usually mean a prior process was killed mid-apply — verify nothing is still running before forcing.

## State Inspection Commands

```bash
terraform state list                                  # all resources
terraform state list | grep aws_instance              # filter
terraform state show 'aws_instance.web[0]'            # attributes
terraform state show 'module.vpc.aws_subnet.public["a"]'
```

## State Manipulation Commands

**State manipulation is destructive — always back up first.**

```bash
# Rename resource without destroy/create
terraform state mv aws_instance.web aws_instance.api

# Move resource between modules
terraform state mv aws_instance.web module.compute.aws_instance.web

# Remove from state (doesn't touch real infra)
terraform state rm aws_instance.obsolete

# Pull state JSON to stdout
terraform state pull > backup.tfstate

# Push local state to remote (use with extreme caution)
terraform state push backup.tfstate

# Replace provider in state
terraform state replace-provider \
  registry.terraform.io/-/aws \
  registry.terraform.io/hashicorp/aws
```

## Migrating Between Backends

1. Edit `backend "..."` block to new configuration.
2. Run `terraform init -migrate-state`. Terraform copies state to the new backend and prompts for confirmation.
3. Verify `terraform plan` shows no changes.
4. Commit the backend change.

For cross-account S3 migration:

```bash
# 1. Pull current state locally
terraform state pull > current.tfstate

# 2. Edit backend config to new bucket
# 3. Re-init, copy state
terraform init -migrate-state

# 4. Verify
terraform plan
```

## Drift Detection

Drift = reality has diverged from state (someone clicked in the console, autoscaling group changed instances, etc.).

```bash
# Refresh state from reality, show diff without applying
terraform plan -refresh-only

# Apply refreshed state (updates state file, no infra changes)
terraform apply -refresh-only
```

Enterprise tools (Terraform Cloud, env0, Spacelift) run drift checks nightly and alert. For OSS, schedule a cron in CI.

## Partial Refreshes

```bash
# Skip refresh (speeds up plan, but may miss drift)
terraform plan -refresh=false

# Target a specific resource
terraform plan -target=aws_instance.web
```

Prefer `-refresh-only` over `-refresh=false` — drift blindness causes incidents.

## Sensitive Data in State

Sensitive outputs and resource attributes **land in plaintext** inside state. Mitigations:

- **Encrypt at rest** — enable S3 SSE-KMS, GCS CMEK, Azure Blob SSE.
- **Restrict IAM access** — least privilege on the state bucket, audit reads.
- **Use ephemeral resources** — `random_password` with `ephemeral = true`, `data "aws_secretsmanager_secret_version"` (values not stored).
- **OpenTofu state encryption** — if you can use OpenTofu, its AES-GCM state encryption seals the file at rest.

## Backup & Disaster Recovery

- Enable **S3 versioning + Object Lock** (or equivalent on GCS/Azure) — every state write keeps a previous version.
- **Export nightly** to a separate bucket for cold backup.
- **MFA-protect state bucket deletion.**

Restore procedure:

```bash
aws s3api list-object-versions --bucket my-org-tfstate --prefix platform/
aws s3api copy-object \
  --bucket my-org-tfstate \
  --copy-source "my-org-tfstate/platform/terraform.tfstate?versionId=OLD_VERSION" \
  --key platform/terraform.tfstate
```

## Common State Issues

- **"Objects have changed outside of Terraform"** — drift. Run `terraform apply -refresh-only` to sync.
- **"Error acquiring the state lock"** — check who's running `apply`. Use `force-unlock` only if sure.
- **"Resource already exists"** on apply — the resource was created but not recorded. Use `import`.
- **"Missing resource instance"** — state references a resource that was removed from config without a `removed` block. Add the block or `terraform state rm`.
- **Corrupted state** — restore from backend version history; never hand-edit JSON.

## Related

- [`02-providers.md`](02-providers.md) — backends configured inside the `terraform` block.
- [`11-cicd-patterns.md`](11-cicd-patterns.md) — how CI/CD interacts with remote state and locking.
- [`12-best-practices.md`](12-best-practices.md) — protecting state, workspaces vs separate state, naming.
