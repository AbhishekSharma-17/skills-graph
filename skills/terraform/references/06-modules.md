# Modules

> **Source:** https://developer.hashicorp.com/terraform/language/modules | **Written for:** Terraform v1.11.x

A module is any directory containing `.tf` files. Every Terraform configuration is already a module — the **root module**. You consume other modules with `module` blocks to compose reusable, versioned infrastructure patterns.

## When to Create a Module

Create a module when you'll reuse the same pattern 3+ times, or to encode organizational conventions. A good module:

- Has a **clear, narrow purpose** ("network with private/public subnets" not "everything for our app").
- Hides internal wiring behind a small **variable surface**.
- Exposes the **minimum necessary outputs**.
- Pins provider and Terraform version constraints.
- Ships a README, examples, and tests.

## Module Structure

```
modules/network/
├── README.md
├── main.tf             # primary resources
├── variables.tf        # inputs
├── outputs.tf          # exposed values
├── versions.tf         # required_providers, required_version
├── examples/
│   └── complete/
│       ├── main.tf     # example consumer
│       └── README.md
└── tests/
    └── defaults.tftest.hcl
```

Terraform doesn't enforce this layout — but the community expects it.

## Calling a Module

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.14"

  name = "prod-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false

  tags = local.common_tags
}

resource "aws_instance" "web" {
  subnet_id = module.vpc.private_subnets[0]
}
```

### Module Meta-Arguments

| Argument | Purpose |
|----------|---------|
| `source` | Where to find the module (required) |
| `version` | Version constraint — only for registry sources |
| `count` / `for_each` | Instantiate the module multiple times |
| `providers` | Pass non-default provider instances into the module |
| `depends_on` | Explicit ordering (rare) |

## Source Addresses

| Source Type | Example |
|-------------|---------|
| Local path | `source = "./modules/network"` |
| Terraform Registry | `source = "terraform-aws-modules/vpc/aws"` |
| Private Registry | `source = "app.terraform.io/my-org/vpc/aws"` |
| GitHub | `source = "github.com/my-org/terraform-aws-vpc?ref=v2.0.0"` |
| Generic Git | `source = "git::https://gitlab.com/my-org/tf-vpc.git?ref=v2.0.0"` |
| HTTPS archive | `source = "https://example.com/vpc.zip"` |
| S3 bucket | `source = "s3::https://s3.amazonaws.com/bucket/vpc.zip"` |
| GCS bucket | `source = "gcs::https://storage.googleapis.com/bucket/vpc.zip"` |

Use `//path` to reference a subdirectory:

```hcl
source = "github.com/my-org/tf-modules//networking/vpc?ref=v1.0.0"
```

## Version Pinning

For registry sources, always pin:

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.14"   # 5.14.x, 5.15.x, ... but not 6.0
}
```

For Git sources, pin with `?ref=`:

```hcl
source = "github.com/my-org/tf-vpc?ref=v2.0.0"     # tag
source = "github.com/my-org/tf-vpc?ref=abc1234"    # commit SHA
```

Never use `?ref=main` in production — every apply may pick up unreviewed changes.

## Passing Providers

If a child module uses a non-default provider alias, declare and wire it:

```hcl
# modules/dr-replication/versions.tf
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 5.80"
      configuration_aliases = [aws.primary, aws.replica]
    }
  }
}

# consuming module
provider "aws" {
  alias  = "us_east"
  region = "us-east-1"
}

provider "aws" {
  alias  = "us_west"
  region = "us-west-2"
}

module "dr" {
  source = "./modules/dr-replication"

  providers = {
    aws.primary = aws.us_east
    aws.replica = aws.us_west
  }
}
```

## Module `count` and `for_each`

Instantiate a module multiple times:

```hcl
module "region" {
  source   = "./modules/region-stack"
  for_each = toset(["us-east-1", "us-west-2", "eu-west-1"])

  region = each.value
  name   = "platform-${each.value}"
}

# access outputs
output "regional_endpoints" {
  value = { for r, m in module.region : r => m.api_endpoint }
}
```

## Module Outputs — What to Expose

Expose only what callers need. Don't leak implementation details.

**Good:**
```hcl
output "private_subnet_ids" {
  value = [for s in aws_subnet.private : s.id]
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "nat_gateway_public_ips" {
  value = aws_eip.nat[*].public_ip
}
```

**Bad:**
```hcl
output "aws_subnet_private" {  # exposes entire resource object
  value = aws_subnet.private
}
```

## Composing Modules

Compose smaller modules into larger stacks:

```hcl
# environments/prod/main.tf
module "network" {
  source = "../../modules/network"
  cidr   = "10.0.0.0/16"
}

module "database" {
  source            = "../../modules/rds-postgres"
  vpc_id            = module.network.vpc_id
  private_subnet_ids = module.network.private_subnet_ids
}

module "api" {
  source          = "../../modules/ecs-service"
  vpc_id          = module.network.vpc_id
  subnet_ids      = module.network.private_subnet_ids
  database_url    = module.database.connection_url
  container_image = "my-app:${var.image_tag}"
}
```

Each layer exposes inputs for the next. Keep the root module thin — it's mostly wiring.

## Terraform Registry

The public registry at https://registry.terraform.io hosts community and partner modules. High-quality providers to start with:

| Module | Purpose |
|--------|---------|
| `terraform-aws-modules/vpc/aws` | AWS VPC + subnets + NAT |
| `terraform-aws-modules/eks/aws` | EKS cluster with managed node groups |
| `terraform-aws-modules/rds/aws` | RDS instances/clusters |
| `terraform-aws-modules/lambda/aws` | Lambda functions + packaging |
| `Azure/naming/azurerm` | Consistent Azure naming |
| `GoogleCloudPlatform/lb-http/google` | GCP HTTP LB |
| `cloudposse/*` | Many modules with consistent conventions |

Treat registry modules like external dependencies — read their code, pin versions, audit upgrades.

## Private Registries

Host internal modules via:

- **Terraform Cloud / HCP Terraform private registry** (recommended).
- **GitHub releases** + `git::` source.
- **Self-hosted** registry conforming to the [Module Registry Protocol](https://developer.hashicorp.com/terraform/internals/module-registry-protocol).

```hcl
module "platform" {
  source  = "app.terraform.io/my-org/platform-baseline/aws"
  version = "~> 3.2"
}
```

## Module Authoring Conventions

- **Name the primary resource `this`**: `resource "aws_vpc" "this" {}`. Allows clean output references (`aws_vpc.this.id`).
- **Group related arguments**: place required args first, then optional, then tags.
- **Accept `tags` map** and merge with module defaults:

  ```hcl
  locals {
    tags = merge(
      { Module = "vpc", ManagedBy = "terraform" },
      var.tags,
    )
  }
  ```

- **Fail fast with validation** — catch bad inputs before resource creation.
- **Document all variables and outputs** — description fields flow to `terraform-docs`.

## Generating Docs

`terraform-docs` auto-generates README sections:

```bash
brew install terraform-docs
terraform-docs markdown table --output-file README.md --output-mode inject .
```

With a config file:

```yaml
# .terraform-docs.yml
formatter: markdown table
output:
  file: README.md
  mode: inject
  template: |-
    <!-- BEGIN_TF_DOCS -->
    {{ .Content }}
    <!-- END_TF_DOCS -->
sort:
  enabled: true
  by: required
```

Add as a pre-commit hook with the [`terraform-docs` hook](https://github.com/terraform-docs/terraform-docs/blob/master/docs/USERS_GUIDE.md).

## Refactoring — The `moved` Block

When renaming resources inside a module, add `moved` blocks so upgrades don't destroy/recreate:

```hcl
moved {
  from = aws_instance.web
  to   = aws_instance.app
}
```

Callers upgrading your module will see a no-op move instead of a destroy/create. Keep `moved` blocks for a few releases, then prune.

## Module Versioning

Use semver with tags:

- **Major** — breaking input/output changes, Terraform version bumps, provider bumps that break consumers.
- **Minor** — new features, new optional inputs, new outputs.
- **Patch** — bug fixes, doc updates, no interface change.

Tag releases (`git tag v2.0.0 && git push --tags`) so consumers can pin precisely.

## Testing Modules

Use native `terraform test`:

```hcl
# tests/defaults.tftest.hcl
run "plan_defaults" {
  command = plan

  variables {
    name = "test"
    cidr = "10.0.0.0/16"
  }

  assert {
    condition     = length(aws_subnet.private) == 3
    error_message = "Expected 3 private subnets by default."
  }
}
```

See [`10-testing-and-validation.md`](10-testing-and-validation.md).

## Pitfalls

- **Module sprawl** — dozens of one-off modules increase cognitive load. Prefer a few well-designed modules.
- **Over-parameterization** — 50+ inputs means the module does too much. Split it.
- **Tight coupling** — modules that reach into each other's internals via `terraform_remote_state` create brittle dependencies. Pass data explicitly.
- **Pinning to `main`/`master`** — breaks reproducibility. Pin to tags or commits.
- **Forgetting `configuration_aliases`** — modules using `provider = aws.replica` without declaring the alias fail with "provider configuration not present."

## Related

- [`02-providers.md`](02-providers.md) — provider aliasing and `configuration_aliases`.
- [`04-variables-and-outputs.md`](04-variables-and-outputs.md) — the module interface contract.
- [`10-testing-and-validation.md`](10-testing-and-validation.md) — testing module behavior.
