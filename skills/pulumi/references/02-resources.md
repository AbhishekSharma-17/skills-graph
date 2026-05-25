# Resources

> Source: https://www.pulumi.com/docs/iac/concepts/resources/ | Version: 3.242.0

## Table of Contents

- [Resource Basics](#resource-basics)
- [Custom Resources](#custom-resources)
- [Component Resources](#component-resources)
- [Resource Names and URNs](#resource-names-and-urns)
- [Resource Lifecycle](#resource-lifecycle)
- [Importing Existing Resources](#importing-existing-resources)
- [Common Patterns](#common-patterns)

## Resource Basics

Resources are the fundamental unit of Pulumi programs. Each resource represents a single cloud infrastructure object — an S3 bucket, a VPC, a Kubernetes deployment, a DNS record.

There are two types:
- **Custom resources** — managed by a provider (e.g., `aws.s3.BucketV2`). Correspond to real cloud objects.
- **Component resources** — logical groupings of other resources. No cloud provider calls — purely organizational.

## Custom Resources

Every custom resource takes a **logical name** (first argument) and **args** (resource-specific configuration):

```python
import pulumi_aws as aws

# Minimal resource
bucket = aws.s3.BucketV2("my-bucket")

# With configuration
bucket = aws.s3.BucketV2("my-bucket",
    tags={
        "Environment": "production",
        "ManagedBy": "pulumi",
    },
)

# With resource options (third argument)
bucket = aws.s3.BucketV2("my-bucket",
    tags={"Environment": "production"},
    opts=pulumi.ResourceOptions(
        protect=True,
        retain_on_delete=True,
    ),
)
```

```typescript
// TypeScript
import * as aws from "@pulumi/aws";

const bucket = new aws.s3.BucketV2("my-bucket", {
    tags: {
        Environment: "production",
    },
}, {
    protect: true,
});
```

### Resource Properties

Resources expose input properties (what you set) and output properties (what the cloud returns):

```python
bucket = aws.s3.BucketV2("my-bucket")

# Output properties (resolved after creation)
bucket.id          # The AWS resource ID
bucket.arn         # The ARN
bucket.bucket      # The bucket name (auto-generated if not specified)

# Outputs are wrapped in Output[T] — use apply() to transform
bucket.arn.apply(lambda arn: f"Bucket ARN: {arn}")
```

## Component Resources

Component resources group related resources into a reusable abstraction:

```python
import pulumi

class StaticWebsite(pulumi.ComponentResource):
    def __init__(self, name: str, domain: str, opts=None):
        super().__init__("custom:web:StaticWebsite", name, {}, opts)

        self.bucket = aws.s3.BucketV2(f"{name}-bucket",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.cdn = aws.cloudfront.Distribution(f"{name}-cdn",
            origins=[aws.cloudfront.DistributionOriginArgs(
                domain_name=self.bucket.bucket_regional_domain_name,
                origin_id="s3",
            )],
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs({
            "bucket_name": self.bucket.id,
            "cdn_url": self.cdn.domain_name,
        })

# Usage
site = StaticWebsite("marketing", domain="example.com")
pulumi.export("cdn_url", site.cdn.domain_name)
```

## Resource Names and URNs

### Logical Name

The first argument to every resource constructor. Used to track the resource across updates:

```python
# "web-server" is the logical name
server = aws.ec2.Instance("web-server", ...)
```

**Critical rule**: changing the logical name creates a new resource and deletes the old one. Use `aliases` to rename without replacement.

### Physical Name

The actual name in the cloud provider. Pulumi auto-generates unique names by appending a random suffix:

```python
# Logical name: "my-bucket"
# Physical name: "my-bucket-a1b2c3d" (auto-generated)
bucket = aws.s3.BucketV2("my-bucket")

# Override with explicit physical name
bucket = aws.s3.BucketV2("my-bucket",
    bucket="my-exact-bucket-name",
)
```

Auto-naming avoids conflicts during stack updates (old resource exists while new one is being created).

### URN (Uniform Resource Name)

Pulumi's internal unique identifier for every resource:

```
urn:pulumi:prod::my-project::aws:s3/bucketV2:BucketV2::my-bucket
         ^stack  ^project    ^type                       ^logical-name
```

```bash
# List URNs for all resources in a stack
pulumi stack --show-urns
```

## Resource Lifecycle

Pulumi determines the correct operation for each resource during `pulumi up`:

| Operation | When |
|-----------|------|
| **Create** | Resource is in code but not in state |
| **Update** | Resource exists in state; inputs changed |
| **Replace** | An input change requires destroy + create |
| **Delete** | Resource is in state but removed from code |
| **Same** | No changes detected |

### Replace Behavior

Some property changes force a replacement (destroy old, create new):

```python
# Changing the AMI forces replacement of an EC2 instance
server = aws.ec2.Instance("web",
    ami="ami-newversion",  # Changed from previous value
    instance_type="t3.micro",
)
```

Pulumi creates the new resource first, then deletes the old one (create-before-delete). Override with `delete_before_replace=True` in resource options.

## Importing Existing Resources

Bring unmanaged cloud resources under Pulumi control:

```bash
# CLI import (generates code)
pulumi import aws:s3/bucketV2:BucketV2 my-bucket my-actual-bucket-name

# Bulk import from file
pulumi import --file resources.json
```

```json
// resources.json
{
  "resources": [
    {
      "type": "aws:s3/bucketV2:BucketV2",
      "name": "my-bucket",
      "id": "my-actual-bucket-name"
    },
    {
      "type": "aws:ec2/instance:Instance",
      "name": "web-server",
      "id": "i-0123456789abcdef0"
    }
  ]
}
```

Import via code (resource option):

```python
# Import during first pulumi up, then remove the import option
bucket = aws.s3.BucketV2("my-bucket",
    bucket="my-actual-bucket-name",
    opts=pulumi.ResourceOptions(
        import_="my-actual-bucket-name",
    ),
)
```

## Common Patterns

### Conditional Resources

```python
config = pulumi.Config()
enable_cdn = config.get_bool("enableCdn") or False

cdn = None
if enable_cdn:
    cdn = aws.cloudfront.Distribution("cdn", ...)

pulumi.export("cdn_url", cdn.domain_name if cdn else None)
```

### Dynamic Resource Count

```python
config = pulumi.Config()
replicas = config.get_int("replicas") or 3

instances = []
for i in range(replicas):
    instance = aws.ec2.Instance(f"web-{i}",
        instance_type="t3.micro",
        ami="ami-12345678",
        tags={"Name": f"web-{i}"},
    )
    instances.append(instance)

pulumi.export("instance_ids", [inst.id for inst in instances])
```

### Resource Dependencies

```python
# Implicit dependency (via output reference)
vpc = aws.ec2.Vpc("vpc", cidr_block="10.0.0.0/16")
subnet = aws.ec2.Subnet("subnet",
    vpc_id=vpc.id,  # Automatic dependency on vpc
    cidr_block="10.0.1.0/24",
)

# Explicit dependency (when no output reference exists)
role = aws.iam.Role("role", ...)
policy = aws.iam.RolePolicy("policy",
    role=role.name,
    policy=json.dumps({...}),
    opts=pulumi.ResourceOptions(depends_on=[role]),
)
```
