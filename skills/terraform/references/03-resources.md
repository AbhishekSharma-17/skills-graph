# Resources

> **Source:** https://developer.hashicorp.com/terraform/language/resources | **Written for:** Terraform v1.11.x

Resources are the primary building block of Terraform. A resource block declares a single piece of infrastructure — a VM, a DNS record, an IAM policy — that Terraform should create, update, and destroy on your behalf.

## Anatomy of a Resource

```hcl
resource "TYPE" "NAME" {
  argument_a = value_a
  argument_b = value_b

  nested_block {
    arg = val
  }
}
```

- **TYPE** — namespaced by provider: `aws_instance`, `google_compute_instance`, `github_repository`. The first token (`aws`, `google`, `github`) is the provider's local name.
- **NAME** — local identifier, unique within a module. Not visible to the cloud API. Used in references: `aws_instance.web.id`.
- **Arguments** — as defined by the provider schema. Required arguments error at plan if missing.
- **Attributes** — read-only outputs computed after apply, also defined by the schema. Accessed via `TYPE.NAME.attribute`.

## Example: Full AWS Stack Snippet

```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "primary"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
}

resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Allow HTTP/HTTPS"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOT
    #!/bin/bash
    apt update && apt install -y nginx
    systemctl enable --now nginx
  EOT

  tags = {
    Name = "web-${var.env}"
  }
}
```

Terraform computes the dependency graph from references (`aws_vpc.main.id` ← `aws_subnet.public`) and executes in topological order.

## Resource Addresses

Every resource has a fully qualified address used for state, targeting, and imports:

```
module.MODULE_NAME.TYPE.NAME
module.MODULE_NAME.TYPE.NAME[INDEX]           # count
module.MODULE_NAME.TYPE.NAME["KEY"]           # for_each
```

Examples:

```
aws_instance.web
aws_instance.web[0]
module.vpc.aws_subnet.public["a"]
module.cluster.module.workers.aws_launch_template.this
```

Use these addresses with CLI commands:

```bash
terraform state show 'module.vpc.aws_subnet.public["a"]'
terraform apply -target='aws_instance.web[2]'          # caution — avoid in regular workflow
terraform state mv aws_instance.web aws_instance.api   # rename without destroy
```

## Meta-Arguments

Arguments that every resource supports (full detail in [`08-lifecycle-and-meta-arguments.md`](08-lifecycle-and-meta-arguments.md)):

| Meta-Argument | Purpose |
|---------------|---------|
| `count` | Create N copies of a resource |
| `for_each` | Create one copy per map/set entry |
| `provider` | Select a non-default provider alias |
| `depends_on` | Force ordering that isn't implied by references |
| `lifecycle` | Control create/update/delete behavior |
| `provisioner` | Imperatively run commands after create/before destroy (last resort) |

Short example:

```hcl
resource "aws_instance" "web" {
  for_each = toset(["a", "b", "c"])

  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public[each.key].id

  tags = {
    Name = "web-${each.key}"
  }

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [ami]
  }
}
```

## Creating vs Updating vs Replacing

Terraform classifies each planned change into one of five actions:

| Symbol | Action | Triggered when |
|--------|--------|----------------|
| `+` | Create | Resource is new in config |
| `-` | Destroy | Resource removed from config or moved out |
| `~` | Update in place | Only mutable attributes changed |
| `-/+` | Replace (destroy then create) | An immutable attribute changed |
| `+/-` | Replace (create then destroy) | Same, with `create_before_destroy = true` |

The provider schema marks each attribute as updatable in place or force-replace. Read the plan output carefully — a single typo can mean destroying prod.

## Importing Existing Resources

Two approaches:

### `import` block (Terraform 1.5+, preferred)

Declarative, version-controlled imports that run during plan/apply:

```hcl
import {
  to = aws_s3_bucket.legacy
  id = "my-legacy-bucket-name"
}

resource "aws_s3_bucket" "legacy" {
  bucket = "my-legacy-bucket-name"
}
```

Generate config automatically:

```bash
terraform plan -generate-config-out=generated.tf
```

After apply, delete the `import` block.

### `terraform import` command (legacy, still supported)

```bash
terraform import aws_s3_bucket.legacy my-legacy-bucket-name
terraform import 'aws_instance.web[0]' i-0123456789abcdef0
```

Then manually hand-author the matching resource block. The CLI import does *not* write any configuration.

## The `moved` Block

Refactor addresses without destroying resources:

```hcl
moved {
  from = aws_instance.web
  to   = module.app.aws_instance.this
}
```

Running `terraform plan` then shows a no-op move rather than destroy/create.

## The `removed` Block (1.7+)

Drop a resource from state without destroying the real infrastructure:

```hcl
removed {
  from = aws_instance.legacy
  lifecycle {
    destroy = false
  }
}
```

Useful when a resource has been imported into a different module or is now managed outside Terraform.

## Provisioners — Use Sparingly

Provisioners run local/remote commands on create or destroy. They are a **last resort** because they don't fit the declarative model and can leave state inconsistent on failure.

```hcl
resource "aws_instance" "web" {
  # ...
  provisioner "remote-exec" {
    inline = ["sudo systemctl restart nginx"]
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("~/.ssh/id_rsa")
      host        = self.public_ip
    }
  }

  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Destroying ${self.id}'"
  }
}
```

Prefer these alternatives:
- **Cloud-init / user_data** — bake configuration into VM boot.
- **Ansible / Chef** — mature configuration management.
- **Container images** — build once, deploy immutably.
- **`null_resource` + `triggers`** — trigger external commands declaratively.

## `null_resource` Pattern

Bridge Terraform to external actions:

```hcl
resource "null_resource" "seed_db" {
  triggers = {
    schema_hash = filesha256("${path.module}/schema.sql")
  }

  provisioner "local-exec" {
    command = "psql ${var.db_url} < ${path.module}/schema.sql"
  }

  depends_on = [aws_db_instance.main]
}
```

The `triggers` map hashes the schema file — any change re-runs the provisioner.

## Sensitive Attributes

Mark outputs or expressions as sensitive so Terraform redacts them in plan/apply/output:

```hcl
variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_db_instance" "main" {
  password = var.db_password
}

output "connection_string" {
  value     = "postgres://user:${var.db_password}@${aws_db_instance.main.endpoint}/app"
  sensitive = true
}
```

Sensitive values still land in the state file — protect state at rest. See [`05-state.md`](05-state.md) and [`12-best-practices.md`](12-best-practices.md).

## Replace a Single Resource

Force recreation without changing config (useful when a VM drifts into a broken state):

```bash
terraform apply -replace=aws_instance.web
```

Replaces `terraform taint`, which still works but is deprecated.

## Targeting (Use Rarely)

`-target` limits a plan/apply to specific addresses. Useful for break-glass fixes, **not** regular workflow — targeting hides dependency changes and tends to create drift.

```bash
terraform plan -target=aws_instance.web
```

## Common Pitfalls

- **Hardcoded strings** that should reference other resources (`subnet_id = "subnet-abc"`) create drift and break reproducibility.
- **Dependency on attributes that don't exist yet** — Terraform can't know an EC2 instance's public IP at plan time; use `output` values consumed by downstream steps or provisioners.
- **Large resources like IAM policies** — hit provider size limits. Split into multiple documents or use `aws_iam_policy_document` data source.
- **Provisioner failures** — partial failures mark the resource tainted; the next apply destroys and recreates. Read error messages carefully.

## Related

- [`07-data-sources.md`](07-data-sources.md) — querying existing infrastructure without managing it.
- [`08-lifecycle-and-meta-arguments.md`](08-lifecycle-and-meta-arguments.md) — `count`, `for_each`, `lifecycle`, `dynamic`.
- [`05-state.md`](05-state.md) — how resources are recorded and how to manipulate state.
