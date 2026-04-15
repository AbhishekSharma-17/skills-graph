# Testing and Validation

> **Source:** https://developer.hashicorp.com/terraform/language/tests | **Written for:** Terraform v1.11.x

Terraform offers three complementary validation layers: **input validation** (catch bad variables early), **preconditions/postconditions** (runtime assertions on resources), and **`terraform test`** (the native test framework introduced in 1.6). Combined with policy-as-code (Sentinel, OPA, Checkov, tflint), they prevent misconfigurations from ever reaching prod.

## Table of Contents

- [Input validation blocks](#input-validation)
- [Preconditions and postconditions](#preconditions-and-postconditions)
- [The `check` block](#the-check-block)
- [`terraform test`](#terraform-test)
- [Testing patterns](#testing-patterns)
- [Policy-as-code](#policy-as-code)
- [Linting](#linting)

## Input Validation

The first line of defense — validate inputs at plan time:

```hcl
variable "env" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be dev, staging, or prod."
  }
  validation {
    condition     = length(var.env) <= 10
    error_message = "env name must be 10 characters or fewer."
  }
}

variable "cidr" {
  type = string
  validation {
    condition     = can(cidrhost(var.cidr, 0))
    error_message = "cidr must be a valid CIDR block."
  }
}

variable "instance_count" {
  type = number
  validation {
    condition     = var.instance_count > 0 && var.instance_count <= 100
    error_message = "instance_count must be between 1 and 100."
  }
}
```

### `can()` and `try()` for Safe Validation

```hcl
validation {
  condition     = can(regex("^[a-z][a-z0-9-]{0,31}$", var.name))
  error_message = "name must be lowercase alphanumeric with hyphens, 1-32 chars."
}
```

### Cross-variable Validation (1.9+)

A validation can reference other variables:

```hcl
variable "min_nodes" { type = number }
variable "max_nodes" { type = number }

variable "max_nodes" {
  type = number
  validation {
    condition     = var.max_nodes >= var.min_nodes
    error_message = "max_nodes must be >= min_nodes."
  }
}
```

## Preconditions and Postconditions

Runtime assertions that fire during plan/apply. Defined inside a `lifecycle` block or on outputs.

### Resource Preconditions

Check assumptions before a resource is read/created:

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  lifecycle {
    precondition {
      condition     = data.aws_ami.ubuntu.architecture == "x86_64"
      error_message = "AMI must be x86_64 for the current instance_type."
    }
  }
}
```

### Resource Postconditions

Check the resulting resource meets requirements after creation:

```hcl
resource "aws_instance" "web" {
  # ...
  lifecycle {
    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance did not receive a public IP. Subnet must auto-assign."
    }
    postcondition {
      condition     = self.root_block_device[0].encrypted == true
      error_message = "Root volume must be encrypted."
    }
  }
}
```

### Data Source Preconditions

Fail if a lookup returns the wrong shape:

```hcl
data "aws_vpc" "main" {
  tags = { Name = "main" }

  lifecycle {
    postcondition {
      condition     = self.cidr_block == "10.0.0.0/16"
      error_message = "Expected VPC cidr to be 10.0.0.0/16, got ${self.cidr_block}."
    }
  }
}
```

### Output Postconditions

```hcl
output "api_url" {
  value = "https://${aws_lb.api.dns_name}"

  precondition {
    condition     = aws_lb.api.load_balancer_type == "application"
    error_message = "api must be an Application Load Balancer."
  }
}
```

## The `check` Block

Soft assertions — they warn but don't fail the apply. Introduced in 1.5 for infrastructure health/SLO checks:

```hcl
check "https_health" {
  data "http" "home" {
    url = "https://${aws_lb.web.dns_name}"
  }

  assert {
    condition     = data.http.home.status_code == 200
    error_message = "Homepage returned ${data.http.home.status_code}, expected 200."
  }
}

check "certificate_expiry" {
  data "tls_certificate" "cert" {
    url = "https://${aws_lb.web.dns_name}"
  }

  assert {
    condition     = timecmp(data.tls_certificate.cert.certificates[0].not_after, timeadd(timestamp(), "720h")) == 1
    error_message = "Certificate expires within 30 days."
  }
}
```

Run as part of `terraform plan -refresh-only` in cron-scheduled CI.

## `terraform test`

Native integration testing, introduced in Terraform 1.6. Test files end in `.tftest.hcl` and live in a `tests/` directory.

### Structure

```hcl
# tests/defaults.tftest.hcl

variables {
  env = "test"
}

# test run: plan only
run "valid_defaults" {
  command = plan

  assert {
    condition     = aws_s3_bucket.example.bucket == "app-test"
    error_message = "Bucket name not templated correctly."
  }
}

# test run: full apply
run "creates_bucket" {
  command = apply

  assert {
    condition     = aws_s3_bucket.example.bucket_regional_domain_name != ""
    error_message = "Bucket domain not assigned."
  }
}

# override inputs per run
run "prod_has_versioning" {
  command = plan
  variables {
    env                = "prod"
    enable_versioning  = true
  }

  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].status == "Enabled"
    error_message = "Versioning not enabled for prod."
  }
}
```

### Running Tests

```bash
# All tests
terraform test

# Specific file
terraform test -filter=tests/defaults.tftest.hcl

# Verbose — show full plan for each run
terraform test -verbose
```

### Mocking Providers (1.7+)

For fast unit tests that don't hit real APIs:

```hcl
mock_provider "aws" {
  mock_resource "aws_s3_bucket" {
    defaults = {
      arn                          = "arn:aws:s3:::mock-bucket"
      bucket_regional_domain_name  = "mock-bucket.s3.amazonaws.com"
    }
  }
}

run "unit_test" {
  command = plan

  assert {
    condition     = aws_s3_bucket.example.arn == "arn:aws:s3:::mock-bucket"
    error_message = "Expected mocked ARN."
  }
}
```

### Using Modules in Tests

Test alternative configurations by swapping modules:

```hcl
run "minimal_config" {
  module {
    source = "./examples/minimal"
  }

  command = plan

  assert {
    condition     = length(module.network.public_subnets) == 1
    error_message = "Minimal config should have 1 public subnet."
  }
}
```

### Test File Layout

```
my-module/
├── main.tf
├── variables.tf
├── outputs.tf
└── tests/
    ├── defaults.tftest.hcl       # default input validation
    ├── prod.tftest.hcl           # prod-tier config
    ├── validation.tftest.hcl     # expected failures
    └── mocks.tftest.hcl          # unit tests with mocks
```

### Expected Failures

```hcl
run "rejects_invalid_env" {
  command = plan

  variables {
    env = "invalid"
  }

  expect_failures = [
    var.env,
  ]
}
```

## Testing Patterns

### Unit tests (fast, mocked)
- Validate variable validation rules.
- Validate conditional logic.
- Validate output expressions.
- **No real providers** — use `mock_provider`.

### Integration tests (slow, real resources)
- Provision to a sandbox account.
- Verify resource attributes with data sources.
- Tear down on test completion (Terraform test does this automatically).

### Contract tests (module-level)
- Stand up the module in isolation with example inputs.
- Assert outputs match the documented contract.
- Run against multiple input variations.

## Policy-as-Code

For organizational policies that exceed what Terraform alone can enforce:

### Sentinel (HCP Terraform/Enterprise)

```sentinel
import "tfplan/v2" as tfplan

ec2_instances = filter tfplan.resource_changes as _, rc {
  rc.type is "aws_instance" and
  rc.mode is "managed" and
  (rc.change.actions contains "create" or rc.change.actions contains "update")
}

main = rule {
  all ec2_instances as _, inst {
    inst.change.after.instance_type in ["t3.micro", "t3.small", "t3.medium"]
  }
}
```

### Open Policy Agent (OPA) — Conftest

```rego
# policy/instance_type.rego
package main

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_instance"
  action := resource.change.actions[_]
  action == "create"
  not resource.change.after.instance_type in ["t3.micro", "t3.small"]
  msg := sprintf("Instance %s has unapproved type %s", [resource.address, resource.change.after.instance_type])
}
```

Run in CI:

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json
conftest test plan.json -p policy/
```

### Checkov — Out-of-the-box Security

```bash
pip install checkov
checkov -d . --framework terraform
checkov -d . --check CKV_AWS_20,CKV_AWS_57
```

Checkov ships with 1000+ pre-built checks (encryption at rest, public access blocks, IAM least privilege).

### Trivy (formerly tfsec)

```bash
brew install trivy
trivy config .
```

## Linting

`tflint` catches provider-specific issues, dead code, and style problems:

```bash
brew install tflint
tflint --init
tflint
```

`.tflint.hcl` config:

```hcl
plugin "aws" {
  enabled = true
  version = "0.32.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

config {
  module = true
  force  = false
}

rule "terraform_required_version" {
  enabled = true
}

rule "terraform_required_providers" {
  enabled = true
}

rule "terraform_unused_declarations" {
  enabled = true
}
```

Combine with `terraform fmt`, `terraform validate`, and pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.90.0
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
      - id: terraform_docs
      - id: terraform_checkov
```

## Recommended Validation Stack

1. **`terraform fmt`** — every commit (pre-commit hook).
2. **`terraform validate`** — every commit.
3. **`tflint`** — every PR.
4. **Checkov / Trivy / tfsec** — every PR for security.
5. **`terraform test`** — every PR; run mocked tests fast, integration tests nightly.
6. **Sentinel / OPA** — before `apply` in prod, via CI policy gate.

## Pitfalls

- **Validation condition errors** — `can()` wraps errors; without it, a failing expression inside a validation condition blocks the whole plan.
- **Postcondition failures rollback state** — a postcondition that fails after resource creation marks the apply as failed but the resource *is* created. Next apply will see drift.
- **`terraform test` cleanup** — tests tear down created resources on exit. Interruptions can leak infra. Always run against sandbox accounts.
- **Policy coverage ≠ compliance** — Checkov catches common issues but not custom org rules. Layer tools.

## Related

- [`04-variables-and-outputs.md`](04-variables-and-outputs.md) — validation blocks on variables.
- [`08-lifecycle-and-meta-arguments.md`](08-lifecycle-and-meta-arguments.md) — pre/postconditions inside lifecycle.
- [`11-cicd-patterns.md`](11-cicd-patterns.md) — running validation gates in CI.
