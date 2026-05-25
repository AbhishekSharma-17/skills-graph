# Testing

> Source: https://www.pulumi.com/docs/iac/concepts/testing/ | Version: 3.242.0

## Table of Contents

- [Testing Strategies](#testing-strategies)
- [Unit Testing with Mocks](#unit-testing-with-mocks)
- [Python Unit Tests (pytest)](#python-unit-tests-pytest)
- [TypeScript Unit Tests (Jest/Vitest)](#typescript-unit-tests-jestvitest)
- [Property Testing](#property-testing)
- [Integration Testing](#integration-testing)
- [Testing Best Practices](#testing-best-practices)

## Testing Strategies

| Strategy | Runs Against | Speed | Confidence | Use Case |
|----------|-------------|-------|------------|----------|
| **Unit testing** | Mocks | Fast | Medium | Logic, conditionals, component structure |
| **Property testing** | Preview data | Medium | Medium-High | Invariants, policy-like assertions |
| **Integration testing** | Real cloud | Slow | High | End-to-end infrastructure validation |

## Unit Testing with Mocks

Pulumi's mock system intercepts resource creation and returns predictable values without making cloud API calls. Tests run entirely in memory.

### How Mocks Work

1. Set `PULUMI_TEST_MODE=true` (or use `pulumi.runtime.set_mocks()`)
2. Provide a mock that returns fake resource outputs
3. Run your program — all resources are created against the mock
4. Assert on resource properties, counts, and relationships

## Python Unit Tests (pytest)

### Setup

```python
# test_infra.py
import unittest
import pulumi


class MyMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        """Called for every resource creation."""
        outputs = args.inputs.copy()

        # Add computed outputs based on resource type
        if args.typ == "aws:s3/bucketV2:BucketV2":
            outputs["id"] = f"{args.name}-id"
            outputs["arn"] = f"arn:aws:s3:::{args.name}-id"
            outputs["bucket"] = outputs.get("bucket", f"{args.name}-auto")
            outputs["bucketRegionalDomainName"] = f"{args.name}-id.s3.us-east-1.amazonaws.com"

        if args.typ == "aws:ec2/instance:Instance":
            outputs["id"] = f"i-{args.name}"
            outputs["publicIp"] = "1.2.3.4"
            outputs["privateDnsName"] = f"ip-10-0-0-1.ec2.internal"

        return [f"{args.name}-id", outputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        """Called for provider function invocations (data sources)."""
        return {}


# Install mocks BEFORE importing infrastructure code
pulumi.runtime.set_mocks(
    MyMocks(),
    preview=False,  # Set True to test preview behavior
)

# NOW import infrastructure code
import __main__ as infra  # or: from myproject import infra
```

### Writing Tests

```python
class TestInfrastructure(unittest.TestCase):

    @pulumi.runtime.test
    def test_bucket_has_tags(self):
        """Verify S3 bucket has required tags."""
        def check_tags(tags):
            self.assertIn("Environment", tags)
            self.assertEqual(tags["ManagedBy"], "pulumi")

        infra.bucket.tags.apply(check_tags)

    @pulumi.runtime.test
    def test_bucket_not_public(self):
        """Verify bucket doesn't have public access."""
        def check_acl(acl):
            self.assertNotEqual(acl, "public-read")
            self.assertNotEqual(acl, "public-read-write")

        infra.bucket.acl.apply(check_acl)

    @pulumi.runtime.test
    def test_instance_type(self):
        """Verify instance type is from approved list."""
        def check_type(instance_type):
            approved = ["t3.micro", "t3.small", "t3.medium"]
            self.assertIn(instance_type, approved)

        infra.server.instance_type.apply(check_type)

    @pulumi.runtime.test
    def test_server_in_private_subnet(self):
        """Verify server is placed in a private subnet."""
        def check_subnet(subnet_id):
            self.assertIsNotNone(subnet_id)

        infra.server.subnet_id.apply(check_subnet)
```

### Testing Components

```python
# Test that a component creates expected child resources
class TestVpcComponent(unittest.TestCase):

    @pulumi.runtime.test
    def test_vpc_creates_subnets(self):
        vpc = Vpc("test", VpcArgs(
            availability_zones=["us-east-1a", "us-east-1b"],
        ))

        def check_subnets(ids):
            self.assertEqual(len(ids), 2)

        vpc.public_subnet_ids.apply(check_subnets)

    @pulumi.runtime.test
    def test_vpc_cidr(self):
        vpc = Vpc("test", VpcArgs(cidr_block="10.1.0.0/16"))

        def check_cidr(cidr):
            self.assertEqual(cidr, "10.1.0.0/16")

        vpc.vpc.cidr_block.apply(check_cidr)
```

### Running Tests

```bash
# Run with pytest
PULUMI_TEST_MODE=true \
PULUMI_CONFIG='{"project:region":"us-east-1"}' \
python -m pytest tests/ -v

# Or set environment in conftest.py
```

```python
# conftest.py
import os
os.environ["PULUMI_TEST_MODE"] = "true"
os.environ["PULUMI_CONFIG"] = '{"my-project:region": "us-east-1"}'
os.environ["PULUMI_NODEJS_STACK"] = "test"
os.environ["PULUMI_NODEJS_PROJECT"] = "my-project"
```

## TypeScript Unit Tests (Jest/Vitest)

```typescript
// __tests__/infra.test.ts
import * as pulumi from "@pulumi/pulumi";

pulumi.runtime.setMocks({
    newResource(args: pulumi.runtime.MockResourceArgs) {
        const outputs: Record<string, any> = { ...args.inputs };

        if (args.type === "aws:s3/bucketV2:BucketV2") {
            outputs.id = `${args.name}-id`;
            outputs.arn = `arn:aws:s3:::${args.name}-id`;
        }

        return { id: `${args.name}-id`, state: outputs };
    },
    call(args: pulumi.runtime.MockCallArgs) {
        return {};
    },
});

import * as infra from "../index";

describe("Infrastructure", () => {
    test("bucket has encryption tag", async () => {
        const tags = await new Promise<Record<string, string>>((resolve) =>
            infra.bucket.tags.apply(resolve)
        );
        expect(tags.ManagedBy).toBe("pulumi");
    });
});
```

## Property Testing

Property testing uses CrossGuard-style assertions that run during `pulumi preview`:

```python
# policy.py — run with: pulumi preview --policy-pack ./policy
from pulumi_policy import (
    PolicyPack,
    ResourceValidationPolicy,
    EnforcementLevel,
)

PolicyPack("tests", policies=[
    ResourceValidationPolicy(
        name="s3-no-public-read",
        description="S3 buckets must not allow public read access.",
        validate=lambda args, report_violation:
            report_violation("S3 bucket has public read ACL")
            if args.resource_type == "aws:s3/bucketV2:BucketV2"
            and args.props.get("acl") == "public-read"
            else None,
    ),
    ResourceValidationPolicy(
        name="ec2-approved-instance-types",
        description="EC2 instances must use approved instance types.",
        validate=lambda args, report_violation:
            report_violation(f"Instance type {args.props.get('instanceType')} not approved")
            if args.resource_type == "aws:ec2/instance:Instance"
            and args.props.get("instanceType") not in ["t3.micro", "t3.small", "t3.medium"]
            else None,
    ),
])
```

## Integration Testing

Integration tests deploy real infrastructure, run assertions, and tear it down:

```python
import subprocess
import json

def test_full_deployment():
    """Integration test: deploy, verify, destroy."""
    stack_name = "test-integration"

    try:
        # Deploy
        subprocess.run(
            ["pulumi", "up", "--yes", "--stack", stack_name],
            check=True,
        )

        # Get outputs
        result = subprocess.run(
            ["pulumi", "stack", "output", "--json", "--stack", stack_name],
            capture_output=True, text=True, check=True,
        )
        outputs = json.loads(result.stdout)

        # Assert on real infrastructure
        assert "bucket_name" in outputs
        assert outputs["bucket_name"].startswith("data-")

        # Verify the bucket exists via AWS CLI
        subprocess.run(
            ["aws", "s3", "ls", f"s3://{outputs['bucket_name']}"],
            check=True,
        )

    finally:
        # Always clean up
        subprocess.run(
            ["pulumi", "destroy", "--yes", "--stack", stack_name],
            check=True,
        )
        subprocess.run(
            ["pulumi", "stack", "rm", "--yes", stack_name],
            check=True,
        )
```

### Using Automation API for Integration Tests

```python
import pulumi.automation as auto

def test_with_automation_api():
    stack = auto.create_or_select_stack(
        stack_name="test",
        project_name="integration-test",
        program=my_pulumi_program,
    )

    stack.set_config("aws:region", auto.ConfigValue("us-east-1"))

    try:
        up_result = stack.up(on_output=print)
        assert up_result.outputs["bucket_name"].value is not None

        # Run additional assertions against real resources

    finally:
        stack.destroy(on_output=print)
        stack.workspace.remove_stack("test")
```

## Testing Best Practices

1. **Unit test logic, not infrastructure** — test conditionals, loops, and component wiring, not that AWS creates an S3 bucket
2. **Use property tests for policies** — enforce naming conventions, tagging, and security rules
3. **Integration tests are expensive** — run sparingly (nightly, pre-release), not on every commit
4. **Mock only at the provider boundary** — test your abstractions, not Pulumi internals
5. **Test component interfaces** — verify outputs, not internal resource details
6. **Use dedicated test stacks** — never run integration tests against production
7. **Clean up on failure** — always destroy test infrastructure in a finally block
