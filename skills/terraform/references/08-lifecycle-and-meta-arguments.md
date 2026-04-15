# Meta-Arguments and Lifecycle

> **Source:** https://developer.hashicorp.com/terraform/language/meta-arguments | **Written for:** Terraform v1.11.x

Meta-arguments modify how Terraform manages a resource, data source, or module — without being part of the provider schema. They are the primary tool for loops, dependencies, and replacement control.

## Table of Contents

- [`count` — numeric multiplicity](#count)
- [`for_each` — keyed multiplicity](#for_each)
- [`count` vs `for_each`](#when-to-use-which)
- [`depends_on`](#depends_on)
- [`lifecycle`](#lifecycle)
- [`dynamic` blocks](#dynamic-blocks)
- [`provider` selection](#provider-selection)
- [`provisioner`](#provisioners)

## `count`

Create N copies of a resource with a numeric index:

```hcl
resource "aws_instance" "web" {
  count = var.instance_count

  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"

  tags = {
    Name = "web-${count.index}"
  }
}
```

Access individual instances:

```hcl
aws_instance.web[0].id
aws_instance.web[*].private_ip    # splat -> list
length(aws_instance.web)
```

Use the conditional idiom to include/exclude a resource:

```hcl
resource "aws_cloudwatch_log_group" "app" {
  count = var.enable_logs ? 1 : 0
  name  = "/app/${var.env}"
}

# reference: aws_cloudwatch_log_group.app[*].arn  (list of zero or one)
```

## `for_each`

Create one copy per key in a map or set. Keys are stable identities — reorder the map and state addresses stay correct, unlike `count`.

```hcl
# Map form -> each.key, each.value
resource "aws_iam_user" "team" {
  for_each = {
    alice = { level = "admin" }
    bob   = { level = "viewer" }
  }

  name = each.key
  tags = {
    Access = each.value.level
  }
}

# Set form -> each.key == each.value
resource "aws_s3_bucket" "regional" {
  for_each = toset(["us-east-1", "us-west-2"])
  bucket   = "app-${each.key}"
}
```

Addressing:

```hcl
aws_iam_user.team["alice"].arn
values(aws_iam_user.team)[*].arn
```

`for_each` keys must be **known at plan time** and must all be strings. If the map comes from another resource's output (computed at apply), use `toset()` with known literal values or split into two applies.

### `for_each` with computed values

If your keys depend on resources that don't exist yet, Terraform errors out at plan. Mitigations:

- Build the key list from literals or variables, not from resource outputs.
- Use a `for` expression over known inputs:

```hcl
locals {
  subnet_map = { for i, az in var.azs : az => cidrsubnet(var.vpc_cidr, 8, i) }
}

resource "aws_subnet" "private" {
  for_each          = local.subnet_map
  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value
  availability_zone = each.key
}
```

## When to Use Which

| Need | Pick |
|------|------|
| 0/1 toggle for a single resource | `count = var.enabled ? 1 : 0` |
| N identical copies where identity doesn't matter | `count` |
| Copies with stable identity (named entities) | `for_each` |
| Iterating structured config from a map | `for_each` |

**Rule of thumb:** default to `for_each`. Reserve `count` for purely numeric replication or on/off toggles. `count`'s positional indexing means that removing the middle element of a list triggers destruction/recreation of every subsequent element.

## `depends_on`

Force ordering that Terraform can't infer from references:

```hcl
resource "aws_iam_role_policy" "s3_access" { /* ... */ }

resource "aws_instance" "web" {
  # ...
  depends_on = [aws_iam_role_policy.s3_access]
}
```

Use sparingly — most dependencies should be expressed by *referencing* the upstream resource's attributes. `depends_on` is a last resort for hidden dependencies (eventual consistency, side effects, API race conditions).

Valid on: `resource`, `data`, `module`, `output`.

## `lifecycle`

Fine-grained control over how Terraform replaces, updates, or destroys a resource.

```hcl
resource "aws_instance" "web" {
  # ...
  lifecycle {
    create_before_destroy = true
    prevent_destroy       = false
    ignore_changes        = [ami, tags["LastScan"]]
    replace_triggered_by  = [aws_launch_template.web.latest_version]
  }
}
```

### `create_before_destroy`

Create the replacement first, then destroy the old one. Essential for zero-downtime replacements of stateful resources (ALB target groups, Auto Scaling groups) where the API doesn't allow two resources with the same name:

```hcl
resource "aws_launch_template" "web" {
  lifecycle {
    create_before_destroy = true
  }

  name_prefix   = "web-"      # must be prefix, not fixed name
  image_id      = var.ami_id
  instance_type = var.instance_type
}
```

### `prevent_destroy`

Fail any plan that would destroy this resource. Useful for protecting stateful resources:

```hcl
resource "aws_s3_bucket" "critical_logs" {
  bucket = "org-audit-logs"
  lifecycle {
    prevent_destroy = true
  }
}
```

Remove the flag (or comment it out) to actually delete. Does not protect against `terraform state rm`.

### `ignore_changes`

Tell Terraform not to recreate or update on changes to specific attributes. Ideal when another system mutates the resource after creation (autoscaling desired_count, Helm-managed labels):

```hcl
resource "aws_autoscaling_group" "web" {
  # ...
  lifecycle {
    ignore_changes = [
      desired_capacity,            # managed by autoscaling policies
      target_group_arns,           # managed by another module
      tag,                         # AWS adds tags externally
    ]
  }
}
```

Use `ignore_changes = all` as a break-glass to freeze a resource's config entirely.

### `replace_triggered_by`

Replace this resource when the referenced value changes. Classic use: force recreation when a launch template version bumps:

```hcl
resource "aws_autoscaling_group" "web" {
  # ...
  lifecycle {
    replace_triggered_by = [aws_launch_template.web]
  }
}
```

### `precondition` / `postcondition` (1.2+)

Runtime assertions — see [`10-testing-and-validation.md`](10-testing-and-validation.md).

```hcl
resource "aws_instance" "web" {
  instance_type = var.instance_type

  lifecycle {
    precondition {
      condition     = contains(["t3.micro", "t3.small", "t3.medium"], var.instance_type)
      error_message = "instance_type must be t3 small-family."
    }

    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance did not receive a public IP."
    }
  }
}
```

## `dynamic` Blocks

Generate repeating nested blocks from a collection. Essential for loops inside resources:

```hcl
resource "aws_security_group" "web" {
  name = "web"

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from
      to_port     = ingress.value.to
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidrs
      description = ingress.value.description
    }
  }
}
```

Structure: `dynamic "BLOCK_NAME" { for_each = ...; content { ... } }`.

Inside `content`, `BLOCK_NAME.key` and `BLOCK_NAME.value` expose the iteration variables. Rename with `iterator = rule` if desired:

```hcl
dynamic "ingress" {
  for_each = var.ingress_rules
  iterator = rule
  content {
    from_port = rule.value.from
  }
}
```

Wrap in a conditional with `for_each = var.enabled ? [1] : []`:

```hcl
resource "aws_s3_bucket" "example" {
  bucket = var.name

  dynamic "versioning" {
    for_each = var.enable_versioning ? [1] : []
    content {
      enabled = true
    }
  }
}
```

## Provider Selection

Pick a non-default provider alias:

```hcl
resource "aws_s3_bucket" "replica" {
  provider = aws.west
  bucket   = "replica-bucket"
}
```

Required when:
- Multiple regions/accounts in the same root module.
- Calling modules that declare `configuration_aliases`.

See [`02-providers.md`](02-providers.md).

## Provisioners

Run commands on create or destroy. **Use sparingly** — they violate the declarative model and are fragile.

```hcl
resource "aws_instance" "web" {
  # ...

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file("~/.ssh/id_rsa")
    host        = self.public_ip
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt update",
      "sudo apt install -y nginx",
    ]
  }

  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Destroying ${self.id}' >> audit.log"
  }
}
```

Better alternatives:
- **User data / cloud-init** — bake startup into VM config.
- **Ansible / Chef / Salt** — mature config management.
- **Container images** — ship app pre-configured.
- **`null_resource` with triggers** — decouples commands from resource lifecycle.

## Scope — What Supports What

| Meta-Argument | Works on |
|---------------|----------|
| `count` | `resource`, `data`, `module` |
| `for_each` | `resource`, `data`, `module` |
| `depends_on` | `resource`, `data`, `module`, `output` |
| `provider` | `resource`, `data` |
| `lifecycle` | `resource` (and on modules via `moved`/`removed` blocks) |
| `dynamic` | nested blocks inside any resource/data |
| `provisioner` / `connection` | `resource` only |

## Pitfalls

- **`count` reordering** — removing an element from a list shifts indices and destroys/creates everything after it. Switch to `for_each` with stable keys.
- **`for_each` with unknown keys** — Terraform 1.7+ can handle some unknown-key cases; older versions error out. Derive keys from literal inputs when possible.
- **Mixing `count` and `for_each`** on the same resource is not allowed.
- **`ignore_changes` forever** — an innocuous ignore can mask drift that matters later. Review annually.
- **`prevent_destroy` blocks** — apply will fail with a confusing error if you remove the resource from config while this flag is set. Disable the flag first, then remove.
- **`dynamic` blocks for single blocks** — if you need 0 or 1 instance of a block, a `dynamic` with `for_each = var.enabled ? [1] : []` is idiomatic; nested conditionals aren't.

## Related

- [`03-resources.md`](03-resources.md) — resource basics.
- [`06-modules.md`](06-modules.md) — `count`/`for_each` on modules.
- [`10-testing-and-validation.md`](10-testing-and-validation.md) — preconditions, postconditions, check blocks.
