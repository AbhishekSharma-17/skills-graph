# Data Sources

> **Source:** https://developer.hashicorp.com/terraform/language/data-sources | **Written for:** Terraform v1.11.x

Data sources let Terraform **read** information from providers without creating or managing it. They are the read-only twin of resources. Use them to reference existing infrastructure, look up AMIs, fetch secrets, compute ARNs, and decouple modules.

## Syntax

```hcl
data "TYPE" "NAME" {
  argument = value
}

# reference with data.TYPE.NAME.attribute
```

## Common Examples

### Looking up an AMI

```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]   # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
}
```

### Current account / region / identity

```hcl
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  azs        = slice(data.aws_availability_zones.available.names, 0, 3)
}
```

### IAM policy documents

```hcl
data "aws_iam_policy_document" "s3_readonly" {
  statement {
    actions = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.app.arn,
      "${aws_s3_bucket.app.arn}/*",
    ]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${local.account_id}:role/app-runtime"]
    }
  }
}

resource "aws_iam_policy" "s3_readonly" {
  name   = "s3-readonly"
  policy = data.aws_iam_policy_document.s3_readonly.json
}
```

`aws_iam_policy_document` is much safer than raw JSON — typos fail at plan time, references are validated.

### Secrets Manager / SSM

```hcl
data "aws_secretsmanager_secret" "db_password" {
  name = "prod/db/password"
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = data.aws_secretsmanager_secret.db_password.id
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

**Warning:** the secret value will land in `terraform.tfstate`. Mitigate with state encryption or use ephemeral resources (Terraform 1.10+, see below).

### Remote state

Share outputs across root modules without creating a provider coupling:

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "my-org-tfstate"
    key    = "networking/prod/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "app" {
  subnet_id              = data.terraform_remote_state.network.outputs.private_subnet_ids[0]
  vpc_security_group_ids = [data.terraform_remote_state.network.outputs.default_sg_id]
}
```

## Ephemeral Data Sources (1.10+)

Ephemeral data sources return values that never persist to state. Essential for secrets-in-flight:

```hcl
ephemeral "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "prod/db/password"
}

resource "aws_db_instance" "main" {
  password = ephemeral.aws_secretsmanager_secret_version.db_password.secret_string
}
```

Ephemeral values cannot be used in `output`, `local`, or any non-ephemeral attribute unless the receiving resource supports them. Check provider docs for which attributes accept ephemeral inputs.

Common ephemeral types (AWS provider 5.80+):
- `aws_secretsmanager_secret_version`
- `aws_ssm_parameter`
- `aws_kms_secrets`
- `aws_lambda_invocation`

## Data Source Lifecycle

Data sources evaluate at one of three points:

1. **Plan time** — if all arguments are known statically. Their result becomes part of the plan.
2. **Apply time** — if arguments depend on resources that haven't been created yet. You'll see `(known after apply)` in the plan output.
3. **Each refresh** — `terraform apply -refresh-only` re-reads every data source.

This is why a downstream resource referencing a data source might show unexpected diffs — the underlying data has changed.

## Conditional Data Sources

Use `count` or `for_each` to make a data source optional:

```hcl
data "aws_route53_zone" "existing" {
  count = var.create_dns ? 1 : 0
  name  = var.domain_name
}

resource "aws_route53_record" "web" {
  count = var.create_dns ? 1 : 0

  zone_id = data.aws_route53_zone.existing[0].zone_id
  name    = "www"
  type    = "A"
  ttl     = 300
  records = [aws_instance.web.public_ip]
}
```

## The `external` Provider

Call any executable that returns JSON:

```hcl
data "external" "git_commit" {
  program = ["bash", "-c", "echo '{\"sha\": \"'$(git rev-parse HEAD)'\"}'"]
}

resource "aws_s3_object" "deploy_meta" {
  bucket  = aws_s3_bucket.artifacts.id
  key     = "deploys/latest.json"
  content = jsonencode({
    git_sha = data.external.git_commit.result.sha
  })
}
```

Use sparingly — breaks reproducibility and is harder to debug than native providers.

## The `http` Provider

HTTP GET against an endpoint:

```hcl
data "http" "my_ip" {
  url = "https://checkip.amazonaws.com"
}

resource "aws_security_group_rule" "allow_me" {
  type        = "ingress"
  protocol    = "tcp"
  from_port   = 22
  to_port     = 22
  cidr_blocks = ["${chomp(data.http.my_ip.response_body)}/32"]
  security_group_id = aws_security_group.bastion.id
}
```

## Template Rendering

Terraform has no dedicated `template_file` data source anymore (deprecated). Use `templatefile()`:

```hcl
locals {
  user_data = templatefile("${path.module}/templates/user-data.sh.tftpl", {
    db_endpoint = aws_db_instance.main.endpoint
    env         = var.env
  })
}

resource "aws_launch_template" "web" {
  user_data = base64encode(local.user_data)
}
```

## File and Archive Data

```hcl
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "app" {
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  # ...
}
```

## Kubernetes Data Sources

Look up existing cluster objects:

```hcl
data "kubernetes_service" "app" {
  metadata {
    name      = "app"
    namespace = "production"
  }
}

output "app_ip" {
  value = data.kubernetes_service.app.status[0].load_balancer[0].ingress[0].ip
}
```

## Best Practices

- **Prefer data sources over hardcoded IDs** — decouples config from cloud resource IDs that change across environments.
- **Cache with locals** — if the same data source result is used many times, wrap it in a `local` for readability.
- **Filter precisely** — an `aws_ami` lookup with loose filters can pick up unexpected images, leading to surprise replacements.
- **Pin immutable attributes** — for Lambda deployments, use `filename_sha256` so Terraform detects code changes.
- **Mark secrets as sensitive** — but remember data sources can't have `sensitive = true` on their definition; downstream usages should.

## Common Pitfalls

- **Slow data sources** — some sources hit paginated APIs (e.g., listing all EBS snapshots). Expect plan-time delays.
- **Stale data** — data sources don't refresh between `plan` and `apply` unless refs change. For "current time" or frequently-changing data, use the `time` provider or external scripts.
- **Permission errors** — the executing identity needs **read** permissions for every data source type. `aws_caller_identity` requires `sts:GetCallerIdentity`.
- **`data` vs `resource` for same object** — only one should own a resource. Mixing both leads to drift.

## Related

- [`03-resources.md`](03-resources.md) — the companion concept for managed infrastructure.
- [`02-providers.md`](02-providers.md) — `terraform_remote_state` for cross-module sharing.
- [`12-best-practices.md`](12-best-practices.md) — secret handling and ephemeral usage.
