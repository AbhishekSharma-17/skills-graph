# Functions and Expressions

> **Source:** https://developer.hashicorp.com/terraform/language/functions | **Written for:** Terraform v1.11.x

Terraform ships with 100+ built-in functions for strings, numbers, collections, encoding, hashing, filesystem, IP math, and date/time. You cannot define your own functions in HCL — everything is built-in. This reference covers the ones you'll actually use.

## Table of Contents

- [Function call syntax](#syntax)
- [String functions](#string-functions)
- [Numeric functions](#numeric-functions)
- [Collection functions](#collection-functions)
- [Encoding functions](#encoding-functions)
- [Filesystem functions](#filesystem-functions)
- [Date/time functions](#datetime-functions)
- [Hash and crypto functions](#hash-and-crypto-functions)
- [IP network functions](#ip-network-functions)
- [Type conversion](#type-conversion)
- [Conditional and logical patterns](#conditional-and-logical-patterns)
- [`for` expressions](#for-expressions)
- [Splat expressions](#splat-expressions)
- [The `console`](#the-terraform-console)

## Syntax

```hcl
function_name(arg1, arg2, ...)
```

Functions are pure — given the same inputs they return the same output and never produce side effects.

## String Functions

```hcl
format("Hello, %s!", "world")              # "Hello, world!"
format("%05d", 42)                          # "00042"
format("%.2f", 3.14159)                     # "3.14"

formatlist("instance-%s", ["a", "b"])       # ["instance-a", "instance-b"]

join(",", ["a", "b", "c"])                  # "a,b,c"
split(",", "a,b,c")                         # ["a", "b", "c"]

lower("HELLO")                              # "hello"
upper("hello")                              # "HELLO"
title("hello world")                        # "Hello World"

trim("  hello  ", " ")                      # "hello"
trimprefix("app-prod", "app-")              # "prod"
trimsuffix("service.test", ".test")         # "service"
trimspace("   hi   ")                       # "hi"

replace("foo-bar", "-", "_")                # "foo_bar"
regex("[a-z]+", "Hello 123 World")          # "ello"
regexall("[A-Z]+", "Hello World")           # ["H", "W"]
regexreplace("a1b2c3", "[0-9]", "")         # "abc"

startswith("prod-db", "prod")               # true
endswith("app.log", ".log")                 # true
contains(["a", "b", "c"], "b")              # true

substr("hello world", 6, 5)                 # "world"
strrev("hello")                             # "olleh"
strcontains("foo.bar", ".")                 # true (1.5+)

indent(2, "line1\nline2")                   # prepend 2 spaces to each line after first
chomp("hello\n")                            # "hello"
```

## Numeric Functions

```hcl
min(1, 2, 3)                    # 1
max(1, 2, 3)                    # 3
abs(-5)                         # 5
ceil(3.1)                       # 4
floor(3.9)                      # 3
log(8, 2)                       # 3
pow(2, 10)                      # 1024
signum(-3)                      # -1
parseint("ff", 16)              # 255
```

## Collection Functions

```hcl
length([1, 2, 3])                          # 3
length("hello")                            # 5
length({a=1, b=2})                         # 2

concat([1, 2], [3, 4])                     # [1, 2, 3, 4]
flatten([[1, 2], [3, [4, 5]]])             # [1, 2, 3, 4, 5]
distinct([1, 2, 2, 3, 1])                  # [1, 2, 3]
reverse([1, 2, 3])                         # [3, 2, 1]
sort(["b", "a", "c"])                      # ["a", "b", "c"]

element(["a", "b", "c"], 1)                # "b"
slice(["a", "b", "c", "d"], 1, 3)          # ["b", "c"]
chunklist([1, 2, 3, 4, 5], 2)              # [[1, 2], [3, 4], [5]]
zipmap(["a", "b"], [1, 2])                 # {a = 1, b = 2}

keys({a = 1, b = 2})                       # ["a", "b"]
values({a = 1, b = 2})                     # [1, 2]
lookup({a = 1}, "b", 99)                   # 99  (default)
merge({a = 1}, {b = 2}, {a = 3})           # {a = 3, b = 2}

contains(["a", "b"], "a")                  # true
index(["a", "b", "c"], "b")                # 1

setsubtract(["a", "b", "c"], ["b"])        # ["a", "c"]
setunion(["a"], ["b"])                     # ["a", "b"]
setintersection(["a", "b"], ["b", "c"])    # ["b"]
setproduct(["a", "b"], [1, 2])             # [["a",1], ["a",2], ["b",1], ["b",2]]

compact(["", "a", null, "b", ""])          # ["a", "b"]
coalesce(null, "", "actual")               # "actual"  (first non-null, non-empty)
coalescelist([], [1, 2], [3])              # [1, 2]

alltrue([true, true, true])                # true
anytrue([false, true])                     # true

range(5)                                   # [0, 1, 2, 3, 4]
range(1, 10, 2)                            # [1, 3, 5, 7, 9]
```

## Encoding Functions

```hcl
jsonencode({ name = "app", count = 3 })    # {"count":3,"name":"app"}
jsondecode("{\"a\": 1}")                   # {a = 1}

yamlencode({ name = "app" })               # "name: app\n"
yamldecode("name: app")                    # {name = "app"}

base64encode("hello")                      # "aGVsbG8="
base64decode("aGVsbG8=")                   # "hello"
base64gzip("hello world")                  # base64(gzip(..))
base64sha256("hello")                      # base64 of sha256

urlencode("a b&c=d")                       # "a+b%26c%3Dd"

textencodebase64("hello", "UTF-8")         # "aGVsbG8="
textdecodebase64("aGVsbG8=", "UTF-8")      # "hello"

csvdecode("a,b\n1,2\n3,4")                 # [{a="1", b="2"}, {a="3", b="4"}]
```

## Filesystem Functions

```hcl
file("${path.module}/schema.sql")          # file contents as string
filebase64("${path.module}/cert.p12")      # base64 of binary file
fileexists("${path.module}/config.json")   # true/false

templatefile("${path.module}/user-data.sh.tftpl", {
  env = var.env
  db  = aws_db_instance.main.endpoint
})

fileset(path.module, "policies/*.json")    # list of matching files
```

**Template files** use HCL interpolation syntax:

```bash
# user-data.sh.tftpl
#!/bin/bash
export APP_ENV=${env}
%{ for k, v in envs ~}
export ${k}=${v}
%{ endfor ~}
```

Path helpers:

| Variable | Points to |
|----------|-----------|
| `path.module` | Directory of the current module |
| `path.root` | Directory of the root module |
| `path.cwd` | Directory where Terraform was invoked |
| `terraform.workspace` | Current workspace name |

## Date/Time Functions

```hcl
timestamp()                                # "2026-04-16T10:30:00Z"  (RFC3339 UTC)
formatdate("YYYY-MM-DD", timestamp())      # "2026-04-16"
timeadd("2026-04-16T10:00:00Z", "24h")     # "2026-04-17T10:00:00Z"
timecmp("2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z")  # -1
```

`timestamp()` is **not** deterministic — it re-evaluates every plan. Usually wrap with `ignore_changes`:

```hcl
resource "aws_ssm_parameter" "deploy_time" {
  name  = "/app/last-deploy"
  type  = "String"
  value = timestamp()

  lifecycle {
    ignore_changes = [value]
  }
}
```

## Hash and Crypto Functions

```hcl
md5("hello")                               # hex
sha1("hello")
sha256("hello")
sha512("hello")
filesha256("${path.module}/file.zip")      # hash of file contents
filebase64sha256("${path.module}/app.zip") # for Lambda source_code_hash
uuid()                                     # random UUID — non-deterministic
uuidv5("dns", "example.com")               # deterministic UUIDv5
```

## IP Network Functions

Essential for VPC/subnet math:

```hcl
cidrhost("10.0.0.0/16", 10)                # "10.0.0.10"
cidrnetmask("10.0.0.0/16")                 # "255.255.0.0"
cidrsubnet("10.0.0.0/16", 8, 2)            # "10.0.2.0/24" (newbits=8, index=2)
cidrsubnets("10.0.0.0/16", 4, 4, 8, 8)     # 4 subnets of varying sizes

# Multiple subnets, one per AZ
[for i, az in var.azs : cidrsubnet(var.vpc_cidr, 8, i)]
```

## Type Conversion

```hcl
tostring(5)                               # "5"
tonumber("42")                            # 42
tobool("true")                            # true
tolist(["a", "b"])                        # list
toset(["a", "b", "a"])                    # set -> ["a", "b"]
tomap({a = 1})                            # map

# Type check / can()
can(tonumber(var.x))                      # true if convertible
can(var.missing)                          # false
try(var.maybe_undefined, "default")       # try each in order
```

`try(...)` is powerful for optional chained access:

```hcl
key = try(var.config.advanced.cache_key, "default-key")
```

## Conditional and Logical Patterns

```hcl
# Ternary
size = var.env == "prod" ? "large" : "small"

# Nested ternary
tier = var.env == "prod" ? "gold" : var.env == "staging" ? "silver" : "bronze"

# Null coalesce via coalesce()
name = coalesce(var.override_name, local.default_name)

# Short-circuit defaults
tags = merge(var.tags, {
  Env = coalesce(var.env_override, "dev")
})
```

## `for` Expressions

### List comprehension
```hcl
[for n in var.names : upper(n)]                     # transform
[for n in var.names : n if length(n) > 3]           # filter
[for i, n in var.names : "${i}-${n}"]               # with index
```

### Map comprehension
```hcl
{ for s in var.servers : s.name => s.ip }
{ for k, v in var.config : k => upper(v) if v != "" }
```

### Grouping
```hcl
# Group servers by region
{ for s in var.servers : s.region => s.name... }   # note the ... (grouping mode)
# -> { us-east-1 = ["web", "api"], us-west-2 = ["cache"] }
```

### Nested for
```hcl
flatten([
  for az, subnets in var.subnets : [
    for cidr in subnets : {
      az   = az
      cidr = cidr
    }
  ]
])
```

## Splat Expressions

Shortcuts for extracting one attribute from each element of a list:

```hcl
aws_instance.web[*].id
# equivalent to:
[for i in aws_instance.web : i.id]

# Also works on single object (treats as single-element list)
var.single_thing[*].field
```

Works on `count`-addressed resources; for `for_each`, use `values()`:

```hcl
values(aws_instance.web)[*].id
```

## The Terraform Console

Interactive expression REPL — invaluable for exploring data:

```bash
terraform console
> var.region
"us-east-1"

> [for s in aws_subnet.private : s.cidr_block]
["10.0.1.0/24", "10.0.2.0/24"]

> jsondecode(file("./config.json"))
{...}

> cidrsubnet("10.0.0.0/16", 8, 5)
"10.0.5.0/24"
```

Quit with `exit` or Ctrl-D.

## Practical Recipes

### Consistent naming prefix
```hcl
locals {
  name_prefix = lower("${var.project}-${var.env}")
  name        = length(local.name_prefix) > 32 ? substr(local.name_prefix, 0, 32) : local.name_prefix
}
```

### Optional nested structures
```hcl
locals {
  logging_config = var.logging_enabled ? {
    destination = var.log_bucket
    prefix      = "${var.app}/"
  } : null
}
```

### Hash-stable IDs
```hcl
resource "random_id" "suffix" {
  keepers = {
    env = var.env
  }
  byte_length = 4
}
```

## Pitfalls

- **`timestamp()` in resource args** causes perpetual drift unless ignored.
- **`uuid()` is non-deterministic** — every plan produces a new value, breaking the plan-then-apply workflow. Use `random_uuid` resource for stable IDs.
- **`file()` reads at plan time** — if the file isn't present, plan fails even if the resource that consumes it is conditional. Use `fileset()` + `for_each` for presence-conditional logic.
- **`jsondecode` whitespace-sensitive** — embed JSON with care; prefer HCL objects and let `jsonencode` handle serialization.
- **Large template files** — `templatefile()` fails with "unknown value" if any substitution depends on a not-yet-created resource. Split into two applies or move logic into a user_data script.

## Related

- [`01-configuration-language.md`](01-configuration-language.md) — expression fundamentals, operators, types.
- [`04-variables-and-outputs.md`](04-variables-and-outputs.md) — using functions in validations.
- [`07-data-sources.md`](07-data-sources.md) — `external` / `http` data sources for values not in functions.
