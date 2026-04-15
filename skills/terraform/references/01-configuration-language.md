# Configuration Language (HCL)

> **Source:** https://developer.hashicorp.com/terraform/language | **Written for:** Terraform v1.11.x

HCL — HashiCorp Configuration Language — is the declarative syntax Terraform uses to describe infrastructure. It is designed to be human-readable and machine-friendly, with a JSON-equivalent representation for programmatic generation.

## File Layout

- Files end in `.tf` (HCL) or `.tf.json` (JSON equivalent).
- Files in the same directory are merged into one configuration — order of files does not matter.
- Conventional splits, all optional:
  - `main.tf` — primary resources
  - `variables.tf` — input variable declarations
  - `outputs.tf` — output declarations
  - `providers.tf` — `terraform {}` and `provider {}` blocks
  - `versions.tf` — `required_version` and `required_providers`

## Block Structure

An HCL file is a sequence of **blocks**. Each block has a *type*, zero or more *labels*, and a body enclosed in `{}`:

```hcl
block_type "label_one" "label_two" {
  argument = value

  nested_block {
    nested_argument = value
  }
}
```

### Top-level block types

| Block | Labels | Purpose |
|-------|--------|---------|
| `terraform` | none | Backend, required providers, required version, experiments |
| `provider` | provider name | Configure a provider instance |
| `resource` | type, name | Declare a managed infrastructure object |
| `data` | type, name | Query an existing object without managing it |
| `variable` | name | Declare an input variable |
| `output` | name | Expose a value from the module |
| `locals` | none | Define local (private) named values |
| `module` | name | Call a child module |
| `moved` | none | Declare that a resource address has moved |
| `import` | none | Declarative import of an existing resource (1.5+) |
| `removed` | none | Drop a resource from state without destroying (1.7+) |
| `check` | name | Runtime assertions that run during plan/apply |

## Arguments, Identifiers, Comments

```hcl
# Line comment
// Also a line comment
/* Block
   comment */

identifier_snake_case = "value"     # argument
identifier.attribute                # attribute access
resource_type.name.attribute        # resource reference
```

Identifiers must start with a letter and contain letters, digits, hyphens (in labels), or underscores.

## Primitive Types

| Type | Example | Notes |
|------|---------|-------|
| `string` | `"hello"` | Double-quoted, supports interpolation and escapes |
| `number` | `42`, `3.14` | Arbitrary precision; no `int`/`float` distinction in config |
| `bool` | `true`, `false` | Lowercase only |
| `null` | `null` | Explicit absence; skips optional arguments |

### Strings

```hcl
plain    = "hello world"
interp   = "hello ${var.name}"
escaped  = "quote: \" backslash: \\\nnewline"
heredoc  = <<-EOT
  Multi-line string.
  Trimmed leading whitespace thanks to the dash.
  Interpolations work: ${var.name}
EOT
```

## Collection Types

```hcl
list_of_str    = ["a", "b", "c"]
tuple          = ["mixed", 42, true]          # heterogeneous, fixed length
map_of_num     = { a = 1, b = 2 }
object         = { name = "tf", version = 1 }  # heterogeneous values, fixed keys
set_of_str     = toset(["a", "b"])            # unordered, unique
```

- **List** vs **tuple**: list is homogeneous and variable length; tuple allows mixed types with fixed arity.
- **Map** vs **object**: map values share a type; object has a fixed schema with typed attributes.
- **Set**: no ordering, no duplicates — iteration order is undefined.

## Type Constraints

Variables and module inputs can declare type constraints. `any` permits any type.

```hcl
variable "instance_count" {
  type = number
}

variable "tags" {
  type = map(string)
}

variable "subnets" {
  type = list(object({
    cidr = string
    az   = string
  }))
}

variable "flags" {
  type = object({
    enabled  = bool
    priority = optional(number, 10)   # optional with default
  })
}
```

`optional(T)` marks an object attribute optional; the second argument sets a default. Callers can omit the attribute entirely.

## References and Expressions

References navigate the resource graph:

```hcl
aws_instance.web.id                 # resource attribute
aws_instance.web[0].private_ip      # count-addressed
aws_instance.web["blue"].tags       # for_each-addressed
module.vpc.public_subnet_ids        # module output
var.region                          # input variable
local.common_tags                   # local value
data.aws_ami.ubuntu.id              # data source attribute
each.key, each.value                # inside for_each
count.index                         # inside count
self.private_ip                     # inside provisioners & lifecycle
```

### Operators

| Category | Operators |
|----------|-----------|
| Arithmetic | `+ - * / %` (numeric); `+` also concatenates strings in some funcs |
| Comparison | `== != < <= > >=` |
| Logical | `&& || !` |
| Conditional | `condition ? a : b` |
| Null coalescing | via `coalesce(a, b, c)` |
| Splat | `aws_instance.web[*].id` (flattens over count/for_each) |

### Interpolation

Inside a string, `${...}` evaluates an expression:

```hcl
name = "cluster-${var.env}-${local.suffix}"
```

Template directives for conditionals and loops:

```hcl
rendered = <<-EOT
  %{ if var.enabled ~}
  export FOO=bar
  %{ endif ~}
  %{ for k, v in var.env_vars ~}
  export ${k}=${v}
  %{ endfor ~}
EOT
```

The `~` trims surrounding whitespace/newlines.

## For Expressions

Transform collections inline:

```hcl
# list -> list
upper_names = [for n in var.names : upper(n)]

# list -> map
by_name = { for inst in aws_instance.web : inst.tags.Name => inst.id }

# with filter
active = [for s in local.servers : s if s.enabled]

# list -> set
unique = toset([for s in local.servers : s.region])

# Object iteration
configs = { for k, v in var.servers : k => merge(local.defaults, v) }
```

## Dynamic Blocks

Generate repeating nested blocks from a collection:

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
    }
  }
}
```

See [`08-lifecycle-and-meta-arguments.md`](08-lifecycle-and-meta-arguments.md) for `count`, `for_each`, `dynamic`, and lifecycle rules in depth.

## JSON Syntax (`.tf.json`)

Every HCL block can be expressed as JSON. Useful for programmatic generation (CDKTF, scripts):

```json
{
  "resource": {
    "aws_s3_bucket": {
      "example": {
        "bucket": "my-bucket"
      }
    }
  }
}
```

## Formatting Rules

- Indent with 2 spaces.
- Align arguments within a block by the `=` sign.
- Use `terraform fmt -recursive` as a pre-commit hook.

## Reserved Names

Avoid these as resource or variable names: `count`, `depends_on`, `for_each`, `lifecycle`, `provider`, `provisioner`, `source`, `version`, `locals`, `source`, `module`, `path`, `self`, `terraform`.

## Common Pitfalls

- **String vs bool** — `"true"` is a string, not a boolean. Use `true` without quotes.
- **Implicit list flattening is gone** — `[1, [2, 3]]` is a tuple of tuples; use `flatten()` to collapse.
- **Null ≠ empty** — `null` means "argument not set" and triggers any default behavior; `""` is an empty string value.
- **Map ordering** — iteration over maps is alphabetical by key, not insertion order.
- **`"${expr}"` anti-pattern** — just write `expr` directly; the wrapping interpolation is redundant.

## Related

- [`04-variables-and-outputs.md`](04-variables-and-outputs.md) — declaring and validating inputs.
- [`09-functions-and-expressions.md`](09-functions-and-expressions.md) — built-in functions and full expression reference.
- [`08-lifecycle-and-meta-arguments.md`](08-lifecycle-and-meta-arguments.md) — `count`, `for_each`, `dynamic`, `lifecycle`.
