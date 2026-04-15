# Providers

> **Source:** https://developer.hashicorp.com/terraform/language/providers | **Written for:** Terraform v1.11.x

Providers are plugins that Terraform downloads at `init` time to translate HCL into API calls. Every managed resource and data source belongs to exactly one provider. The registry at `registry.terraform.io` hosts 4,000+ official, partner, and community providers.

## The `terraform` Block

Declare required providers and version constraints here. This should live in every repository.

```hcl
terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.4"
    }
  }

  # Optional: remote state backend (see 05-state.md)
  backend "s3" {
    bucket         = "my-org-tfstate"
    key            = "networking/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf-locks"
    encrypt        = true
  }
}
```

### Source Addresses

`source = "<namespace>/<name>"` resolves to `registry.terraform.io/<namespace>/<name>`. For other registries or mirrors:

```hcl
source = "app.terraform.io/my-org/my-provider"           # Terraform Cloud
source = "registry.example.com/my-org/my-provider"       # Private registry
source = "localhost:8080/my-org/my-provider"             # Local dev
```

### Version Constraints

| Operator | Meaning | Example matches |
|----------|---------|-----------------|
| `= 5.80.0` or `5.80.0` | Exact version | `5.80.0` only |
| `>= 5.80` | At least | `5.80.0`, `5.81.2`, `6.0.0` |
| `< 6.0` | Less than | `5.99.9`, not `6.0.0` |
| `~> 5.80` | Pessimistic, same minor | `5.80.x`, `5.81.x`, not `6.0` |
| `~> 5.80.0` | Pessimistic, same patch | `5.80.x` only |
| `>= 5.80, < 6.0` | Range | Combined with comma |

**Recommended:** use `~> MAJOR.MINOR` to receive patch updates automatically while pinning the major version.

## Provider Configuration

`provider` blocks configure provider instances. Most providers read credentials from environment variables or cloud CLI default chains.

```hcl
provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Environment = var.env
      ManagedBy   = "terraform"
      Repo        = "platform-infra"
    }
  }
}
```

### Credential Sources (AWS example)

In order of precedence:
1. `provider` block arguments (`access_key`, `secret_key`, `profile`) — **avoid static keys in code.**
2. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_PROFILE`, `AWS_REGION`).
3. Shared credentials / config file (`~/.aws/credentials`, `~/.aws/config`).
4. IAM role on the execution environment (EC2, ECS, Lambda, GitHub Actions OIDC).

**Best practice:** use OIDC federation or instance roles, never long-lived keys.

## Multiple Instances — `alias`

Configure the same provider multiple times (e.g., multiple AWS regions or accounts):

```hcl
provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "west"
  region = "us-west-2"
}

provider "aws" {
  alias   = "audit"
  region  = "us-east-1"
  profile = "audit-account"
}

resource "aws_s3_bucket" "primary" {
  bucket = "primary-bucket"
}

resource "aws_s3_bucket" "replica" {
  provider = aws.west
  bucket   = "replica-bucket"
}
```

Modules that need a specific alias must declare it via `configuration_aliases`:

```hcl
# inside a module
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.80"
      configuration_aliases = [aws.primary, aws.replica]
    }
  }
}

# when calling the module
module "cross_region" {
  source = "./modules/cross-region"
  providers = {
    aws.primary = aws
    aws.replica = aws.west
  }
}
```

## The `.terraform.lock.hcl` File

Created by `terraform init`, this **dependency lock file** pins every provider to a specific version + hash. Commit it. Without it, CI and teammates may silently upgrade.

```bash
# Update all providers to latest allowed versions
terraform init -upgrade

# Add hashes for additional platforms (common for CI/CD)
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_arm64 \
  -platform=darwin_amd64
```

## Common Official Providers

| Provider | Source | Use For |
|----------|--------|---------|
| AWS | `hashicorp/aws` | 1,500+ AWS services |
| AzureRM | `hashicorp/azurerm` | Azure Resource Manager |
| Google | `hashicorp/google` | GCP via GA APIs |
| Google Beta | `hashicorp/google-beta` | GCP beta features |
| Kubernetes | `hashicorp/kubernetes` | K8s objects via API |
| Helm | `hashicorp/helm` | Helm releases |
| Random | `hashicorp/random` | Generate IDs, passwords |
| Null | `hashicorp/null` | Placeholder for provisioners |
| External | `hashicorp/external` | Call arbitrary scripts |
| TLS | `hashicorp/tls` | Generate keys/certificates |
| Archive | `hashicorp/archive` | Create zip files (Lambda) |
| Time | `hashicorp/time` | Time-based resources, delays |

## Popular Partner / Community Providers

| Provider | Source | Use For |
|----------|--------|---------|
| GitHub | `integrations/github` | Repos, teams, branch protection |
| Datadog | `datadog/datadog` | Monitors, dashboards, SLOs |
| Cloudflare | `cloudflare/cloudflare` | DNS, Pages, Workers, WAF |
| MongoDB Atlas | `mongodb/mongodbatlas` | Atlas clusters, users |
| Snowflake | `snowflakedb/snowflake` | Warehouses, databases, grants |
| PagerDuty | `PagerDuty/pagerduty` | Services, schedules, policies |
| Vercel | `vercel/vercel` | Projects, deployments, domains |
| Auth0 | `auth0/auth0` | Tenants, clients, rules |
| OpenAI | `community-terraform-providers/openai` | Fine-tunes, assistants |
| Okta | `okta/okta` | Users, groups, apps |

Browse the full registry at https://registry.terraform.io/browse/providers.

## Provider Meta-Arguments

Providers accept a few meta-arguments across all types:

```hcl
provider "aws" {
  region = "us-east-1"
  assume_role {
    role_arn     = "arn:aws:iam::111111111111:role/TerraformDeployer"
    session_name = "terraform-${local.env}"
    external_id  = var.external_id
  }
  assume_role_with_web_identity {
    role_arn                = "arn:aws:iam::111111111111:role/GithubActions"
    web_identity_token_file = "/tmp/web_identity_token"
  }
}
```

## `terraform_remote_state` Data Source

Not a provider per se, but vital for sharing outputs across root modules:

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "my-org-tfstate"
    key    = "networking/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.network.outputs.private_subnets[0]
}
```

For modern codebases, prefer passing outputs explicitly via module inputs or storing shared configuration in SSM/Secrets Manager instead.

## Upgrading Providers Safely

1. Read the upstream CHANGELOG for breaking changes before upgrading.
2. Run `terraform init -upgrade` in a branch.
3. Run `terraform plan` and inspect for unexpected resource replacements.
4. For major version bumps, use the provider's migration guide (most include automated upgrade scripts).
5. Commit both the updated `.terraform.lock.hcl` and any configuration changes.

## Troubleshooting

- **"provider configuration not present"** — You removed a `provider` block but the module still references its alias. Add back a minimal `provider` block or remove the alias.
- **"Failed to query available provider packages"** — Network issue or registry auth required. Check `TF_LOG=debug` and registry credentials.
- **"Inconsistent dependency lock file"** — A teammate generated the lock on a different OS/arch. Run `terraform providers lock -platform=...` to add additional hashes, then commit.
- **"Error: Incompatible provider version"** — `required_version` or `required_providers` constraints exclude your installed version. Update the constraint or install a matching version.

## Related

- [`05-state.md`](05-state.md) — backends and remote state sharing.
- [`06-modules.md`](06-modules.md) — passing providers into modules.
- [`12-best-practices.md`](12-best-practices.md) — credential management and least privilege.
