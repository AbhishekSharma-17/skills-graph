# Policy as Code — CrossGuard

> Source: https://www.pulumi.com/docs/iac/crossguard/ | Version: 3.242.0

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Policy Types](#policy-types)
- [Writing Policies in Python](#writing-policies-in-python)
- [Writing Policies in TypeScript](#writing-policies-in-typescript)
- [Enforcement Levels](#enforcement-levels)
- [Remediation](#remediation)
- [Policy Packs](#policy-packs)
- [Server-Side Enforcement](#server-side-enforcement)
- [Common Policy Patterns](#common-policy-patterns)

## Overview

Pulumi CrossGuard is the policy as code framework that enforces security, compliance, cost, and architectural rules during `pulumi preview` and `pulumi up`. Policies run before resources are created or updated, preventing violations from reaching production.

Key features:
- Policies written in Python or TypeScript
- Run automatically during preview and update
- Three enforcement levels: advisory, mandatory, disabled
- Optional remediation (auto-fix violations)
- Server-side enforcement via Pulumi Cloud

## Getting Started

```bash
# Create a new policy pack
mkdir my-policies && cd my-policies
pulumi policy new aws-python   # Python policy template
# or
pulumi policy new aws-typescript  # TypeScript template

# Run policies locally
pulumi preview --policy-pack ./my-policies
pulumi up --policy-pack ./my-policies

# Run multiple policy packs
pulumi up --policy-pack ./security-policies --policy-pack ./cost-policies
```

### Python Policy Pack Structure

```
my-policies/
├── PulumiPolicy.yaml    # Policy pack metadata
├── __main__.py          # Policy definitions
└── requirements.txt     # pulumi-policy dependency
```

```yaml
# PulumiPolicy.yaml
name: my-security-policies
runtime: python
description: Security policies for AWS infrastructure
```

## Policy Types

### Resource Validation Policy

Validates individual resources — runs once per resource:

```python
from pulumi_policy import (
    PolicyPack,
    ResourceValidationPolicy,
    EnforcementLevel,
)

def s3_no_public_read(args, report_violation):
    if args.resource_type == "aws:s3/bucketV2:BucketV2":
        acl = args.props.get("acl", "")
        if acl in ["public-read", "public-read-write"]:
            report_violation("S3 buckets must not have public read access.")

PolicyPack("security", policies=[
    ResourceValidationPolicy(
        name="s3-no-public-read",
        description="Prohibits public ACLs on S3 buckets.",
        validate=s3_no_public_read,
        enforcement_level=EnforcementLevel.MANDATORY,
    ),
])
```

### Stack Validation Policy

Validates the entire stack — runs once after all resources are registered:

```python
from pulumi_policy import StackValidationPolicy

def require_at_least_one_tag_policy(args, report_violation):
    for resource in args.resources:
        tags = resource.props.get("tags", {})
        if resource.resource_type.startswith("aws:") and not tags:
            report_violation(
                f"Resource {resource.name} ({resource.resource_type}) "
                f"must have at least one tag."
            )

PolicyPack("tagging", policies=[
    StackValidationPolicy(
        name="require-tags",
        description="All AWS resources must have tags.",
        validate=require_at_least_one_tag_policy,
    ),
])
```

## Writing Policies in Python

### Multiple Policies in One Pack

```python
from pulumi_policy import (
    PolicyPack,
    ResourceValidationPolicy,
    StackValidationPolicy,
    EnforcementLevel,
)

APPROVED_INSTANCE_TYPES = [
    "t3.micro", "t3.small", "t3.medium", "t3.large",
    "t4g.micro", "t4g.small", "t4g.medium",
]

MAX_RDS_STORAGE_GB = 100


def ec2_approved_types(args, report_violation):
    if args.resource_type == "aws:ec2/instance:Instance":
        itype = args.props.get("instanceType", "")
        if itype not in APPROVED_INSTANCE_TYPES:
            report_violation(
                f"Instance type '{itype}' is not approved. "
                f"Approved types: {APPROVED_INSTANCE_TYPES}"
            )


def rds_storage_limit(args, report_violation):
    if args.resource_type == "aws:rds/instance:Instance":
        storage = args.props.get("allocatedStorage", 0)
        if storage > MAX_RDS_STORAGE_GB:
            report_violation(
                f"RDS storage {storage}GB exceeds limit of {MAX_RDS_STORAGE_GB}GB."
            )


def require_encryption(args, report_violation):
    if args.resource_type == "aws:s3/bucketV2:BucketV2":
        pass  # Check via separate BucketServerSideEncryptionConfiguration resource

    if args.resource_type == "aws:rds/instance:Instance":
        if not args.props.get("storageEncrypted", False):
            report_violation("RDS instances must have storage encryption enabled.")

    if args.resource_type == "aws:ebs/volume:Volume":
        if not args.props.get("encrypted", False):
            report_violation("EBS volumes must be encrypted.")


def no_untagged_resources(args, report_violation):
    for resource in args.resources:
        if resource.resource_type.startswith("aws:"):
            tags = resource.props.get("tags")
            if isinstance(tags, dict) and "Environment" not in tags:
                report_violation(
                    f"{resource.name} missing required 'Environment' tag."
                )


PolicyPack("aws-security", policies=[
    ResourceValidationPolicy(
        name="ec2-approved-instance-types",
        description="EC2 instances must use approved instance types.",
        validate=ec2_approved_types,
    ),
    ResourceValidationPolicy(
        name="rds-storage-limit",
        description=f"RDS storage must not exceed {MAX_RDS_STORAGE_GB}GB.",
        validate=rds_storage_limit,
    ),
    ResourceValidationPolicy(
        name="require-encryption",
        description="Storage resources must be encrypted.",
        validate=require_encryption,
        enforcement_level=EnforcementLevel.MANDATORY,
    ),
    StackValidationPolicy(
        name="require-environment-tag",
        description="All AWS resources must have an Environment tag.",
        validate=no_untagged_resources,
        enforcement_level=EnforcementLevel.ADVISORY,
    ),
])
```

## Writing Policies in TypeScript

```typescript
import { PolicyPack, validateResourceOfType } from "@pulumi/policy";
import * as aws from "@pulumi/aws";

new PolicyPack("aws-security", {
    policies: [
        {
            name: "s3-no-public-read",
            description: "S3 buckets must not have public ACLs.",
            enforcementLevel: "mandatory",
            validateResource: validateResourceOfType(aws.s3.BucketV2, (bucket, args, report) => {
                if (bucket.acl === "public-read") {
                    report("S3 bucket must not have public-read ACL.");
                }
            }),
        },
    ],
});
```

## Enforcement Levels

| Level | Behavior | Use Case |
|-------|----------|----------|
| `ADVISORY` | Warns but allows deployment | New policies in rollout, soft guidelines |
| `MANDATORY` | Blocks deployment on violation | Security requirements, compliance |
| `DISABLED` | Policy is skipped | Temporarily disable a policy |

```python
ResourceValidationPolicy(
    name="my-policy",
    validate=my_check,
    enforcement_level=EnforcementLevel.MANDATORY,  # Blocks on violation
)
```

Override enforcement at runtime:

```bash
# Override a specific policy to advisory
pulumi up --policy-pack ./policies \
  --policy-pack-config policy-config.json
```

```json
{
    "require-encryption": {
        "enforcementLevel": "advisory"
    }
}
```

## Remediation

Policies can automatically fix violations instead of just reporting them:

```python
from pulumi_policy import ResourceValidationPolicy, Remediation

def ensure_tags(args, report_violation):
    if args.resource_type.startswith("aws:"):
        tags = args.props.get("tags", {})
        if "ManagedBy" not in tags:
            report_violation("Missing 'ManagedBy' tag.")

def fix_tags(args):
    tags = args.props.get("tags", {})
    tags["ManagedBy"] = "pulumi"
    args.props["tags"] = tags

ResourceValidationPolicy(
    name="auto-tag",
    description="Auto-add ManagedBy tag to all resources.",
    validate=ensure_tags,
    remediation=Remediation(remediate=fix_tags),
)
```

## Policy Packs

### Publishing to Pulumi Cloud

```bash
# Publish policy pack to your organization
pulumi policy publish myorg

# Enable on all stacks in the org (done via Pulumi Cloud UI or API)
```

### Configurable Policies

```python
from pulumi_policy import PolicyConfigSchema

ResourceValidationPolicy(
    name="max-instance-count",
    description="Limit the number of EC2 instances.",
    validate=lambda args, report_violation: ...,
    config_schema=PolicyConfigSchema(
        properties={
            "maxCount": {"type": "integer", "default": 10},
        },
    ),
)
```

## Server-Side Enforcement

With Pulumi Cloud, policies run server-side on every deployment:

1. Publish policy packs to your Pulumi Cloud organization
2. Enable them as default policies for all stacks
3. Every `pulumi up` in the org is validated automatically
4. No developer can bypass — enforcement happens server-side

## Common Policy Patterns

- **Naming conventions**: enforce prefix/suffix patterns on resource names
- **Cost control**: restrict instance types, storage sizes, region usage
- **Security**: require encryption, block public access, enforce IAM boundaries
- **Compliance**: required tags, specific regions only, approved AMIs
- **Architecture**: maximum resource counts, required monitoring resources
