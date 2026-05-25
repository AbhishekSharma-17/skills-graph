# Inputs and Outputs

> Source: https://www.pulumi.com/docs/iac/concepts/inputs-outputs/ | Version: 3.242.0

## Table of Contents

- [Overview](#overview)
- [Output Type](#output-type)
- [apply Method](#apply-method)
- [all Function](#all-function)
- [concat and interpolate](#concat-and-interpolate)
- [Lifting](#lifting)
- [Stack Outputs](#stack-outputs)
- [Stack References](#stack-references)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

## Overview

Pulumi uses special types — `Input[T]` and `Output[T]` — to track dependencies between resources. Outputs represent values that are not known until a resource is provisioned (like a server's IP address or a bucket's ARN). They are similar to promises/futures.

- **Input[T]** — a value that can be a plain `T` or an `Output[T]`. Resource constructors accept inputs.
- **Output[T]** — a value that will be resolved asynchronously after provisioning. Resource properties return outputs.

```python
import pulumi
import pulumi_aws as aws

bucket = aws.s3.BucketV2("data")

# bucket.id is Output[str] — not a plain string
# bucket.arn is Output[str]
# You can pass outputs directly to other resources as inputs
```

## Output Type

`Output[T]` wraps a value of type `T` and carries dependency information. You cannot access the inner value directly — you must use `apply()` or other combinators.

```python
bucket = aws.s3.BucketV2("data")

# WRONG: can't use Output[str] as a plain string
# url = f"https://{bucket.bucket}.s3.amazonaws.com"  # TypeError

# RIGHT: use apply or interpolation
url = bucket.bucket.apply(lambda name: f"https://{name}.s3.amazonaws.com")
# url is Output[str]
```

### Output.all()

Combine multiple outputs into a single output:

```python
combined = pulumi.Output.all(bucket.id, bucket.arn).apply(
    lambda args: f"ID: {args[0]}, ARN: {args[1]}"
)
```

### Output.from_input()

Convert a plain value to an output:

```python
static_value = pulumi.Output.from_input("us-east-1")
```

## apply Method

`apply()` transforms an output value. The callback receives the resolved value and returns a new value (or another Output):

```python
bucket = aws.s3.BucketV2("data")

# Simple transformation
bucket_url = bucket.bucket_regional_domain_name.apply(
    lambda domain: f"https://{domain}"
)

# Chaining applies
endpoint = bucket.bucket.apply(
    lambda name: f"{name}.s3.amazonaws.com"
).apply(
    lambda domain: f"https://{domain}/index.html"
)

# Returning an Output from apply (flattened automatically)
def get_object_url(bucket_name):
    obj = aws.s3.BucketObject("index",
        bucket=bucket_name,
        key="index.html",
        content="<h1>Hello</h1>",
    )
    return obj.id

object_id = bucket.bucket.apply(get_object_url)  # Output[str]
```

### Multi-value apply

```python
# Using Output.all for multiple values
full_name = pulumi.Output.all(
    bucket.bucket,
    bucket.arn,
    server.public_ip,
).apply(lambda args: {
    "bucket": args[0],
    "arn": args[1],
    "server_ip": args[2],
})
```

## all Function

`pulumi.Output.all()` combines multiple outputs:

```python
# Positional arguments
combined = pulumi.Output.all(vpc.id, subnet.id, sg.id).apply(
    lambda args: f"VPC: {args[0]}, Subnet: {args[1]}, SG: {args[2]}"
)

# Keyword arguments
combined = pulumi.Output.all(
    vpc_id=vpc.id,
    subnet_id=subnet.id,
).apply(
    lambda args: f"VPC: {args['vpc_id']}, Subnet: {args['subnet_id']}"
)

# Collecting outputs from a list
instances = [aws.ec2.Instance(f"web-{i}", ...) for i in range(3)]
all_ips = pulumi.Output.all(*[inst.public_ip for inst in instances])
```

## concat and interpolate

### concat

Join strings and outputs together:

```python
url = pulumi.Output.concat(
    "https://", bucket.bucket_regional_domain_name, "/index.html"
)
```

### interpolate (TypeScript)

```typescript
// TypeScript has a tagged template literal
const url = pulumi.interpolate`https://${bucket.bucketRegionalDomainName}/index.html`;

// Equivalent to:
const url = pulumi.Output.concat("https://", bucket.bucketRegionalDomainName, "/index.html");
```

In Python, use `Output.concat()` or `Output.all(...).apply(lambda args: f"...")`.

## Lifting

Pulumi automatically "lifts" property access on outputs. Accessing a property on an `Output[T]` returns a new `Output` of that property's type:

```python
instance = aws.ec2.Instance("web", ...)

# Lifting: access nested properties directly
instance.public_ip           # Output[str]
instance.tags                # Output[dict]
instance.ebs_block_devices   # Output[list]

# Array indexing is lifted too (TypeScript only)
# const firstSubnet = vpcInfo.subnetIds[0];

# In Python, use apply for indexing
first_subnet = subnet_ids.apply(lambda ids: ids[0])
```

## Stack Outputs

Export values from your stack for consumption by other stacks, CLI, or external tools:

```python
import pulumi

# Export outputs
pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
pulumi.export("api_url", api.url)
pulumi.export("kubeconfig", cluster.kubeconfig)

# Export a secret (remains encrypted in state)
pulumi.export("db_connection", pulumi.Output.secret(db.endpoint))
```

```bash
# Read stack outputs from CLI
pulumi stack output
pulumi stack output bucket_name
pulumi stack output kubeconfig --show-secrets
```

## Stack References

Read outputs from another stack in a different project:

```python
# Reference format: <org>/<project>/<stack>
infra = pulumi.StackReference("myorg/infrastructure/prod")

# Get typed outputs
vpc_id = infra.get_output("vpc_id")           # Output[Any]
subnet_ids = infra.get_output("subnet_ids")   # Output[Any]

# Get output with details (distinguishes plain vs secret)
details = infra.get_output_details("db_password")
# details.value is set for plain values
# details.secret_value is set for secret values
```

```typescript
// TypeScript
const infra = new pulumi.StackReference("myorg/infrastructure/prod");
const vpcId = infra.getOutput("vpc_id");

// Typed output
const vpcId = infra.requireOutput("vpc_id") as pulumi.Output<string>;
```

## Common Patterns

### JSON Serialization

```python
# Serialize an output to JSON (for IAM policies, etc.)
policy_doc = pulumi.Output.all(bucket.arn).apply(
    lambda args: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["s3:GetObject"],
            "Resource": f"{args[0]}/*",
        }],
    })
)
```

### Conditional Output

```python
endpoint = pulumi.Output.all(
    use_custom=config.get_bool("useCustomDomain"),
    custom=custom_domain.url if custom_domain else None,
    default=api.default_url,
).apply(lambda args:
    args["custom"] if args["use_custom"] else args["default"]
)
```

### Output as Secret

```python
# Mark a plain output as secret
connection_string = pulumi.Output.secret(
    pulumi.Output.concat(
        "postgresql://", db.username, ":", db.password,
        "@", db.endpoint, "/", db.db_name
    )
)
```

## Pitfalls

**Never use `apply` for side effects** — apply callbacks may run multiple times during preview and update. Don't make API calls or write files inside apply.

**Don't log outputs directly** — `print(bucket.id)` prints the Output object, not the value. Use `pulumi.export()` or `apply()`.

**Avoid deeply nested applies** — use `Output.all()` to flatten multiple outputs into a single apply call.

**Preview values** — during `pulumi preview`, outputs have placeholder values. Code inside `apply` runs with real values only during `pulumi up`.
