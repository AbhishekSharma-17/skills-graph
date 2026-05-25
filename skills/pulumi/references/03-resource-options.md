# Resource Options

> Source: https://www.pulumi.com/docs/iac/concepts/resources/options/ | Version: 3.242.0

## Table of Contents

- [Overview](#overview)
- [depends_on](#depends_on)
- [protect](#protect)
- [ignore_changes](#ignore_changes)
- [aliases](#aliases)
- [parent](#parent)
- [provider](#provider)
- [transforms](#transforms)
- [delete_before_replace](#delete_before_replace)
- [retain_on_delete](#retain_on_delete)
- [replace_on_changes](#replace_on_changes)
- [custom_timeouts](#custom_timeouts)
- [Combining Options](#combining-options)

## Overview

Resource options modify how Pulumi manages a resource — controlling dependencies, protection, replacement behavior, and provider selection. Options are passed via `opts=pulumi.ResourceOptions(...)` in Python or as the third constructor argument in TypeScript.

```python
resource = aws.s3.BucketV2("bucket",
    tags={"env": "prod"},
    opts=pulumi.ResourceOptions(
        protect=True,
        ignore_changes=["tags"],
        depends_on=[other_resource],
    ),
)
```

## depends_on

Declares explicit ordering dependencies when there is no natural output-to-input relationship:

```python
# The endpoint needs the role to exist, but doesn't reference its outputs
role = aws.iam.Role("lambda-role", assume_role_policy=policy_json)
role_attachment = aws.iam.RolePolicyAttachment("attach",
    role=role.name,
    policy_arn="arn:aws:iam::aws:policy/AWSLambdaBasicExecutionRole",
)

fn = aws.lambda_.Function("handler",
    role=role.arn,
    handler="index.handler",
    runtime="python3.12",
    code=pulumi.FileArchive("./src"),
    opts=pulumi.ResourceOptions(
        depends_on=[role_attachment],  # Wait for attachment
    ),
)
```

**When to use**: only when Pulumi can't infer the dependency from output references. If you pass `role.arn` to a resource, Pulumi automatically knows to create the role first.

## protect

Prevents a resource from being deleted:

```python
db = aws.rds.Instance("production-db",
    engine="postgres",
    instance_class="db.r6g.xlarge",
    opts=pulumi.ResourceOptions(protect=True),
)
```

To delete a protected resource:
```bash
# Option 1: Remove protection via state
pulumi state unprotect <urn>
pulumi destroy

# Option 2: Set protect=False in code, run up, then remove resource
```

## ignore_changes

Tells Pulumi to ignore changes to specific properties — useful when external processes modify resources:

```python
# Ignore tag changes made by AWS auto-tagging
cluster = aws.ecs.Cluster("app",
    tags={"ManagedBy": "pulumi"},
    opts=pulumi.ResourceOptions(
        ignore_changes=["tags"],
    ),
)

# Ignore ASG desired count (managed by autoscaling policies)
asg = aws.autoscaling.Group("web",
    min_size=2,
    max_size=10,
    desired_capacity=4,
    opts=pulumi.ResourceOptions(
        ignore_changes=["desired_capacity"],
    ),
)
```

## aliases

Rename or retype a resource without destroying and recreating it:

```python
# Old name was "web-bucket", renaming to "static-assets"
bucket = aws.s3.BucketV2("static-assets",
    opts=pulumi.ResourceOptions(
        aliases=[pulumi.Alias(name="web-bucket")],
    ),
)

# Move a resource under a new parent component
bucket = aws.s3.BucketV2("assets",
    opts=pulumi.ResourceOptions(
        aliases=[pulumi.Alias(parent=pulumi.ROOT_STACK_RESOURCE)],
        parent=my_component,
    ),
)

# Change resource type (provider migration)
bucket = aws.s3.BucketV2("data",
    opts=pulumi.ResourceOptions(
        aliases=[pulumi.Alias(type_="aws:s3/bucket:Bucket")],
    ),
)
```

## parent

Sets the parent for resource hierarchy and option inheritance:

```python
class MyVpc(pulumi.ComponentResource):
    def __init__(self, name, opts=None):
        super().__init__("custom:network:MyVpc", name, {}, opts)

        # Child resources inherit parent's provider, protect, etc.
        self.vpc = aws.ec2.Vpc(f"{name}-vpc",
            cidr_block="10.0.0.0/16",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.subnet = aws.ec2.Subnet(f"{name}-subnet",
            vpc_id=self.vpc.id,
            cidr_block="10.0.1.0/24",
            opts=pulumi.ResourceOptions(parent=self),
        )
```

Parent inheritance chain: `provider`, `protect`, `transforms`, and `aliases` propagate from parent to children.

## provider

Specifies which provider instance to use for a resource:

```python
# Create an explicit provider for a different region
us_west = aws.Provider("us-west-2", region="us-west-2")
eu = aws.Provider("eu-west-1", region="eu-west-1")

# Use specific providers
bucket_us = aws.s3.BucketV2("us-bucket",
    opts=pulumi.ResourceOptions(provider=us_west),
)

bucket_eu = aws.s3.BucketV2("eu-bucket",
    opts=pulumi.ResourceOptions(provider=eu),
)
```

For component resources, use `providers` (plural) to pass multiple providers:

```python
class MultiRegionApp(pulumi.ComponentResource):
    def __init__(self, name, opts=None):
        super().__init__("custom:app:MultiRegion", name, {}, opts)
        # Children automatically use the correct provider based on type

app = MultiRegionApp("app",
    opts=pulumi.ResourceOptions(
        providers=[us_west, eu],
    ),
)
```

## transforms

Modify resource inputs before they are sent to the provider. Powerful for enforcing org-wide defaults:

```python
# Ensure all S3 buckets have encryption enabled
def enforce_encryption(args: pulumi.ResourceTransformArgs):
    if args.type_ == "aws:s3/bucketV2:BucketV2":
        args.props["tags"] = {**(args.props.get("tags") or {}), "Encrypted": "true"}
    return pulumi.ResourceTransformResult(args.props, args.opts)

pulumi.runtime.register_stack_transform(enforce_encryption)
```

```python
# Apply transforms to a component and all its children
def add_tags(args: pulumi.ResourceTransformArgs):
    if "tags" in args.props:
        args.props["tags"]["Team"] = "platform"
    return pulumi.ResourceTransformResult(args.props, args.opts)

component = MyComponent("app",
    opts=pulumi.ResourceOptions(
        transforms=[add_tags],
    ),
)
```

## delete_before_replace

Forces delete-then-create ordering during replacement (default is create-then-delete):

```python
# Use when the cloud provider doesn't allow two resources with the same config
elb = aws.elb.LoadBalancer("main",
    opts=pulumi.ResourceOptions(
        delete_before_replace=True,
    ),
)
```

**Warning**: causes downtime during replacement since the old resource is deleted before the new one exists.

## retain_on_delete

Keeps the cloud resource when removed from Pulumi state:

```python
# Remove from Pulumi management without deleting the actual resource
bucket = aws.s3.BucketV2("legacy-data",
    opts=pulumi.ResourceOptions(retain_on_delete=True),
)
```

## replace_on_changes

Forces a replacement when specified properties change, even if the provider would normally do an in-place update:

```python
server = aws.ec2.Instance("web",
    user_data=startup_script,
    opts=pulumi.ResourceOptions(
        replace_on_changes=["user_data"],  # Replace instead of update
    ),
)
```

## custom_timeouts

Override default timeouts for long-running operations:

```python
db = aws.rds.Instance("prod",
    engine="postgres",
    instance_class="db.r6g.2xlarge",
    opts=pulumi.ResourceOptions(
        custom_timeouts=pulumi.CustomTimeouts(
            create="30m",
            update="40m",
            delete="20m",
        ),
    ),
)
```

## Combining Options

```python
bucket = aws.s3.BucketV2("critical-data",
    tags={"Environment": "production"},
    opts=pulumi.ResourceOptions(
        protect=True,
        retain_on_delete=True,
        ignore_changes=["tags.LastModified"],
        depends_on=[kms_key],
        custom_timeouts=pulumi.CustomTimeouts(create="10m"),
    ),
)
```
