# Variables and Outputs

> **Source:** https://developer.hashicorp.com/terraform/language/values | **Written for:** Terraform v1.11.x

Input variables parameterize modules. Output values expose computed attributes. Local values are named private expressions inside a module. Together they form the module contract.

## Input Variables

Declare with `variable`:

```hcl
variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "instance_count" {
  description = "Number of EC2 instances"
  type        = number
  default     = 2
  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "instance_count must be between 1 and 10."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  # no default -> required
}

variable "vpc_config" {
  description = "VPC configuration"
  type = object({
    cidr_block      = string
    azs             = list(string)
    enable_flow_log = optional(bool, false)
    tags            = optional(map(string), {})
  })
}
```

### Variable Arguments

| Argument | Purpose |
|----------|---------|
| `description` | Human-readable help text — surface in Cloud UI, docs |
| `type` | Type constraint (see [`01-configuration-language.md`](01-configuration-language.md)) |
| `default` | Value when caller omits the variable |
| `sensitive` | Redact from plan/apply output |
| `nullable` | When `false`, disallow `null` assignments (default `true`) |
| `validation` | Custom validation rule (can appear multiple times) |
| `ephemeral` | Value is not persisted to state (1.10+, for secrets) |

### Validation Rules

```hcl
variable "env" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be one of dev, staging, prod."
  }
}

variable "cidr" {
  type = string
  validation {
    condition     = can(cidrhost(var.cidr, 0))
    error_message = "cidr must be a valid CIDR block."
  }
}
```

`can()` wraps expressions that might fail — useful to validate parseable inputs.

### Setting Variables

In order of precedence (highest wins):

1. CLI flag: `terraform apply -var="region=us-west-2"`
2. `-var-file` flag: `terraform apply -var-file=prod.tfvars`
3. `*.auto.tfvars` or `*.auto.tfvars.json` (auto-loaded, alphabetical)
4. `terraform.tfvars` or `terraform.tfvars.json` (auto-loaded)
5. Environment variables: `TF_VAR_region=us-west-2`
6. `default` in the variable declaration

### `.tfvars` Example

```hcl
# prod.tfvars
region         = "us-east-1"
instance_count = 5
tags = {
  Environment = "prod"
  Owner       = "platform-team"
}
```

```bash
terraform apply -var-file=prod.tfvars
```

### Ephemeral Variables (1.10+)

```hcl
variable "api_token" {
  type      = string
  ephemeral = true
}
```

Ephemeral values can be used during plan/apply but are never written to state, plan files, or outputs. Pair with ephemeral resources like `random_password` for zero-trust secret handling.

## Output Values

Outputs expose values from a module to its caller (or to the CLI, for root modules).

```hcl
output "instance_ids" {
  description = "IDs of the EC2 instances"
  value       = aws_instance.web[*].id
}

output "instance_ips" {
  description = "Private IPs"
  value       = { for k, v in aws_instance.web : k => v.private_ip }
}

output "db_endpoint" {
  description = "RDS connection endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "vpc_id" {
  value      = aws_vpc.main.id
  depends_on = [aws_internet_gateway.main]  # rarely needed
}
```

### Output Arguments

| Argument | Purpose |
|----------|---------|
| `description` | Doc string |
| `value` | Expression to expose (required) |
| `sensitive` | Redact in CLI output; requires `sensitive = true` to consume in non-sensitive context |
| `depends_on` | Force ordering (rare) |
| `precondition` / `postcondition` | Runtime assertions |
| `ephemeral` | Output is not persisted to state |

### Reading Outputs

```bash
terraform output                       # all outputs (human)
terraform output -json                 # machine-readable
terraform output instance_ids          # single named output
terraform output -raw db_endpoint      # raw string (scripting)
```

### Cross-module Outputs

A calling module accesses a child module's outputs via `module.<name>.<output>`:

```hcl
module "vpc" {
  source = "./modules/vpc"
  cidr   = "10.0.0.0/16"
}

resource "aws_instance" "web" {
  subnet_id = module.vpc.public_subnet_ids[0]
}
```

### Output Preconditions / Postconditions

```hcl
output "lb_url" {
  value = "https://${aws_lb.main.dns_name}"

  precondition {
    condition     = aws_lb.main.load_balancer_type == "application"
    error_message = "Expected an Application Load Balancer."
  }
}
```

## Local Values

Named expressions computed inside the module. Use to avoid repetition and express intent.

```hcl
locals {
  common_tags = {
    Project     = var.project
    Environment = var.env
    ManagedBy   = "terraform"
  }

  name_prefix = "${var.project}-${var.env}"

  az_count    = length(var.azs)
  subnets_per_az = {
    for i, az in var.azs : az => cidrsubnet(var.vpc_cidr, 8, i)
  }

  is_prod = var.env == "prod"

  backup_retention = local.is_prod ? 35 : 7
}
```

Reference with `local.<name>`. Locals are private — not exposed to callers.

## Variable vs Local — Which to Use?

| Need | Use |
|------|-----|
| Caller must supply the value | `variable` (no `default`) |
| Caller can override with a reasonable default | `variable` with `default` |
| Value is derived from other variables / resources | `local` |
| Expose a value to the caller | `output` |
| Store a secret | `variable { sensitive = true }` (or `ephemeral = true`) |

## Common Patterns

### Environment-per-directory

```
envs/
├── dev/
│   ├── main.tf        # module calls
│   └── terraform.tfvars
├── staging/
└── prod/
```

Each env directory has its own state, its own `.tfvars`, and calls shared modules.

### Conditional resources via count

```hcl
resource "aws_cloudwatch_log_group" "app" {
  count = var.enable_logging ? 1 : 0
  name  = "/app/${var.env}"
}
```

Access conditionally via splat: `aws_cloudwatch_log_group.app[*].arn`.

### Tag inheritance

```hcl
provider "aws" {
  region = var.region
  default_tags {
    tags = local.common_tags
  }
}
```

Every resource created by this provider instance inherits these tags.

### Computed defaults via locals

```hcl
locals {
  instance_type = coalesce(var.instance_type, local.is_prod ? "t3.large" : "t3.micro")
}
```

## Pitfalls

- **Secrets in `default`** — a `default` value ends up in plan output and the tfstate. Don't put real secrets there; prefer env vars or a secret manager data source.
- **Large defaults in shared modules** — force callers to override with `null` to accept your defaults. Document clearly.
- **`sensitive = true` isn't encryption** — it only redacts from CLI output. The value still lives in `terraform.tfstate`.
- **Output type changes break callers** — changing an output from `list` to `set` breaks splat usage downstream. Version modules semver-style.
- **Missing `description`** — autogenerated docs and Terraform Cloud UI show them; invest 10 seconds per variable.

## Related

- [`06-modules.md`](06-modules.md) — module input/output contracts and composition.
- [`10-testing-and-validation.md`](10-testing-and-validation.md) — preconditions, postconditions, and tests.
- [`12-best-practices.md`](12-best-practices.md) — secret handling conventions.
