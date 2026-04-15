# Terraform — Overview

> **Source:** https://developer.hashicorp.com/terraform/intro | **Written for:** Terraform v1.11.x

## What is Terraform?

Terraform is an open-source Infrastructure as Code (IaC) tool from HashiCorp that lets you define, provision, and manage infrastructure resources across hundreds of cloud and on-premises providers using a declarative configuration language called HCL (HashiCorp Configuration Language).

Instead of clicking through cloud consoles or writing imperative scripts, you describe the **desired end state** of your infrastructure in `.tf` files. Terraform computes the delta between your configuration and the current state, then applies the minimum set of API calls needed to reach the target.

## Core Value Proposition

| Without Terraform | With Terraform |
|-------------------|----------------|
| Click-ops in cloud consoles | Declarative `.tf` files checked into git |
| Snowflake environments that drift | Reproducible, version-controlled infrastructure |
| Undocumented manual setup steps | Self-documenting code with modules |
| Risky blind changes in prod | `terraform plan` previews exact diff before apply |
| Vendor lock-in via proprietary tools | 4,000+ providers, cross-cloud orchestration |

## When to Use Terraform

**Use Terraform when you need to:**
- Provision cloud resources (AWS, Azure, GCP, Oracle Cloud, DigitalOcean, etc.)
- Manage Kubernetes clusters, namespaces, Helm releases
- Configure SaaS tools (GitHub repos, Datadog monitors, PagerDuty schedules, Cloudflare DNS)
- Enforce infrastructure consistency across environments (dev/staging/prod)
- Roll out changes through code review and CI/CD
- Onboard new engineers with a reproducible infrastructure baseline

**Don't use Terraform for:**
- Configuration management inside VMs (use Ansible, Chef, Puppet, or cloud-init)
- Application deployment orchestration (use ArgoCD, Flux, or pipeline tools)
- Ad-hoc one-time scripts that won't be maintained
- Mutable state that changes frequently outside of Terraform's control

## How Terraform Works

Terraform follows a three-step core loop:

1. **Write** — You author `.tf` files describing the desired state (resources, variables, outputs).
2. **Plan** — `terraform plan` reads your config, queries the current state, and shows a diff.
3. **Apply** — `terraform apply` makes API calls in dependency order to converge reality with config.

The execution plan is the central safety mechanism: you see *exactly* what will be created, modified, or destroyed **before** any change is made.

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  .tf files  │────▶│  terraform   │────▶│  Providers  │
│  (desired)  │      │     core     │      │  (API SDKs) │
└─────────────┘      └──────────────┘      └─────────────┘
       ▲                    │                     │
       │                    ▼                     ▼
       │             ┌──────────────┐      ┌─────────────┐
       └─────────────│ state file   │◀─────│   Cloud /   │
          refresh    │ (actual)     │      │    SaaS     │
                     └──────────────┘      └─────────────┘
```

## Installation

### macOS (Homebrew)
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
terraform version
```

### Linux (Debian/Ubuntu)
```bash
wget -O- https://apt.releases.hashicorp.com/gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list

sudo apt update && sudo apt install terraform
```

### Version Manager (tfenv — recommended for multi-project teams)
```bash
brew install tfenv
tfenv install 1.11.4
tfenv use 1.11.4

# Pin per project
echo "1.11.4" > .terraform-version
```

### Windows (Chocolatey)
```powershell
choco install terraform
```

### Docker
```bash
docker run --rm -v $(pwd):/workspace -w /workspace hashicorp/terraform:1.11 init
```

## Your First Configuration

Create `main.tf`:

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "example" {
  bucket = "my-terraform-demo-bucket-${random_id.suffix.hex}"
}

resource "random_id" "suffix" {
  byte_length = 4
}

output "bucket_name" {
  value = aws_s3_bucket.example.bucket
}
```

Run the core workflow:

```bash
terraform init      # Download providers + set up backend
terraform fmt       # Canonicalize formatting
terraform validate  # Syntactic + type checks
terraform plan      # Show diff (dry run)
terraform apply     # Apply changes (prompts for confirmation)
terraform destroy   # Tear everything down when finished
```

## Essential CLI Commands

| Command | Purpose |
|---------|---------|
| `terraform init` | Initialize working directory, download providers, configure backend |
| `terraform fmt [-recursive]` | Rewrite files to canonical format |
| `terraform validate` | Check syntax and argument types |
| `terraform plan [-out=plan.tfplan]` | Compute and preview execution plan |
| `terraform apply [plan.tfplan]` | Apply a saved plan (or compute + apply) |
| `terraform destroy` | Remove all resources in state |
| `terraform state list` | Enumerate resources in state |
| `terraform state show <addr>` | Inspect a single resource's attributes |
| `terraform import <addr> <id>` | Bring an existing cloud resource under management |
| `terraform output [-json]` | Print output values |
| `terraform refresh` | Reconcile state with real infrastructure (deprecated — use `apply -refresh-only`) |
| `terraform taint` / `terraform apply -replace=<addr>` | Force recreation |
| `terraform workspace {list,new,select}` | Manage named workspaces |
| `terraform login` / `terraform logout` | Authenticate to Terraform Cloud/Enterprise |
| `terraform test` | Run test files (`.tftest.hcl`) |
| `terraform console` | Interactive HCL expression REPL |
| `terraform providers [mirror DIR]` | Show or mirror provider deps |
| `terraform graph` | Output DOT graph of dependencies |

## Terraform vs. OpenTofu

In August 2023 HashiCorp moved Terraform from MPL to the Business Source License (BSL). The Linux Foundation forked the MPL-era codebase as **OpenTofu** (`tofu` CLI), which remains fully open source and largely drop-in compatible with Terraform 1.5.x features. Most of this skill applies to both, though:

- OpenTofu adds features like **state encryption** and **early variable evaluation** that Terraform lacks.
- Terraform adds enterprise features (Terraform Cloud, Sentinel, stacks) that OpenTofu does not yet have.
- Provider ecosystems are shared — both use the Terraform Registry protocol.

Choose OpenTofu if you need a permissive OSS license; choose Terraform if you need HashiCorp Cloud Platform, Sentinel policy-as-code, or the latest upstream features.

## Mental Model for Newcomers

Five ideas carry you through everything else:

1. **Everything is a resource** — VMs, DNS records, IAM policies, Datadog dashboards. A resource type has a fixed schema defined by a provider.
2. **State is the source of truth** — Terraform compares desired config against recorded state, not live infra (though it refreshes to reconcile).
3. **Providers are plugins** — The core binary is small; `terraform init` downloads providers that speak cloud APIs.
4. **Modules are reusable folders** — Any directory of `.tf` files can be consumed as a module from another configuration.
5. **The plan is the contract** — Review it like a code diff. Applying a plan that differs from what you reviewed is the most common source of surprises.

## Related Reading

- See [`01-configuration-language.md`](01-configuration-language.md) for HCL syntax, types, and expressions.
- See [`02-providers.md`](02-providers.md) for configuring providers, versions, and aliases.
- See [`05-state.md`](05-state.md) for remote backends and state management.
- See [`12-best-practices.md`](12-best-practices.md) for secrets handling, secure defaults, and team conventions.
