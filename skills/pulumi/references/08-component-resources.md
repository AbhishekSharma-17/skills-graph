# Component Resources

> Source: https://www.pulumi.com/docs/iac/concepts/components/ | Version: 3.242.0

## Table of Contents

- [Overview](#overview)
- [Building Components in Python](#building-components-in-python)
- [Building Components in TypeScript](#building-components-in-typescript)
- [Component Design Patterns](#component-design-patterns)
- [Pulumi Crosswalk Libraries](#pulumi-crosswalk-libraries)
- [Multi-Language Components](#multi-language-components)
- [Publishing Components](#publishing-components)
- [Best Practices](#best-practices)

## Overview

Component resources are logical groupings of related infrastructure. They don't correspond to a single cloud resource — instead, they contain child resources and present a simplified interface. Components are Pulumi's primary abstraction mechanism, analogous to Terraform modules but with full programming language capabilities.

Key properties:
- Extend `pulumi.ComponentResource`
- Contain child resources (set `parent=self`)
- Register outputs for consumers
- Can be shared as packages (npm, PyPI, NuGet)

## Building Components in Python

### Basic Component

```python
import pulumi
import pulumi_aws as aws


class StaticWebsite(pulumi.ComponentResource):
    """A static website hosted on S3 with CloudFront CDN."""

    bucket_name: pulumi.Output[str]
    cdn_url: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        index_document: str = "index.html",
        error_document: str = "error.html",
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("custom:web:StaticWebsite", name, {}, opts)

        self.bucket = aws.s3.BucketV2(
            f"{name}-bucket",
            opts=pulumi.ResourceOptions(parent=self),
        )

        aws.s3.BucketWebsiteConfigurationV2(
            f"{name}-website-config",
            bucket=self.bucket.id,
            index_document=aws.s3.BucketWebsiteConfigurationV2IndexDocumentArgs(
                suffix=index_document,
            ),
            error_document=aws.s3.BucketWebsiteConfigurationV2ErrorDocumentArgs(
                key=error_document,
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.bucket_name = self.bucket.id
        self.cdn_url = self.bucket.bucket_regional_domain_name

        self.register_outputs({
            "bucket_name": self.bucket_name,
            "cdn_url": self.cdn_url,
        })


# Usage
site = StaticWebsite("marketing-site")
pulumi.export("url", site.cdn_url)
```

### Component with Args Class

```python
from dataclasses import dataclass


@dataclass
class VpcArgs:
    cidr_block: str = "10.0.0.0/16"
    availability_zones: list[str] | None = None
    enable_nat_gateway: bool = True
    single_nat_gateway: bool = False
    tags: dict[str, str] | None = None


class Vpc(pulumi.ComponentResource):
    vpc_id: pulumi.Output[str]
    public_subnet_ids: pulumi.Output[list[str]]
    private_subnet_ids: pulumi.Output[list[str]]

    def __init__(
        self,
        name: str,
        args: VpcArgs,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("custom:network:Vpc", name, {}, opts)

        azs = args.availability_zones or ["us-east-1a", "us-east-1b"]
        base_tags = args.tags or {}

        self.vpc = aws.ec2.Vpc(
            f"{name}-vpc",
            cidr_block=args.cidr_block,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={**base_tags, "Name": f"{name}-vpc"},
            opts=pulumi.ResourceOptions(parent=self),
        )

        igw = aws.ec2.InternetGateway(
            f"{name}-igw",
            vpc_id=self.vpc.id,
            tags={**base_tags, "Name": f"{name}-igw"},
            opts=pulumi.ResourceOptions(parent=self),
        )

        public_subnets = []
        private_subnets = []

        for i, az in enumerate(azs):
            public = aws.ec2.Subnet(
                f"{name}-public-{i}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i * 2}.0/24",
                availability_zone=az,
                map_public_ip_on_launch=True,
                tags={**base_tags, "Name": f"{name}-public-{az}"},
                opts=pulumi.ResourceOptions(parent=self),
            )
            public_subnets.append(public)

            private = aws.ec2.Subnet(
                f"{name}-private-{i}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i * 2 + 1}.0/24",
                availability_zone=az,
                tags={**base_tags, "Name": f"{name}-private-{az}"},
                opts=pulumi.ResourceOptions(parent=self),
            )
            private_subnets.append(private)

        self.vpc_id = self.vpc.id
        self.public_subnet_ids = pulumi.Output.all(
            *[s.id for s in public_subnets]
        )
        self.private_subnet_ids = pulumi.Output.all(
            *[s.id for s in private_subnets]
        )

        self.register_outputs({
            "vpc_id": self.vpc_id,
            "public_subnet_ids": self.public_subnet_ids,
            "private_subnet_ids": self.private_subnet_ids,
        })


# Usage
network = Vpc("prod", VpcArgs(
    cidr_block="10.0.0.0/16",
    availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
    tags={"Environment": "production"},
))
```

## Building Components in TypeScript

```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

interface StaticWebsiteArgs {
    indexDocument?: string;
    errorDocument?: string;
}

class StaticWebsite extends pulumi.ComponentResource {
    public readonly bucketName: pulumi.Output<string>;
    public readonly cdnUrl: pulumi.Output<string>;

    constructor(name: string, args: StaticWebsiteArgs, opts?: pulumi.ComponentResourceOptions) {
        super("custom:web:StaticWebsite", name, {}, opts);

        const bucket = new aws.s3.BucketV2(`${name}-bucket`, {}, {
            parent: this,
        });

        this.bucketName = bucket.id;
        this.cdnUrl = bucket.bucketRegionalDomainName;

        this.registerOutputs({
            bucketName: this.bucketName,
            cdnUrl: this.cdnUrl,
        });
    }
}
```

## Component Design Patterns

### Facade Pattern

Hide complexity behind a simple interface:

```python
class Database(pulumi.ComponentResource):
    """Provisions RDS with security group, subnet group, and parameter group."""

    endpoint: pulumi.Output[str]
    port: pulumi.Output[int]

    def __init__(self, name, vpc_id, subnet_ids, engine="postgres", opts=None):
        super().__init__("custom:data:Database", name, {}, opts)

        sg = aws.ec2.SecurityGroup(f"{name}-sg",
            vpc_id=vpc_id,
            ingress=[aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp", from_port=5432, to_port=5432,
                cidr_blocks=["10.0.0.0/8"],
            )],
            opts=pulumi.ResourceOptions(parent=self),
        )

        subnet_group = aws.rds.SubnetGroup(f"{name}-subnets",
            subnet_ids=subnet_ids,
            opts=pulumi.ResourceOptions(parent=self),
        )

        db = aws.rds.Instance(f"{name}-instance",
            engine=engine,
            instance_class="db.t4g.micro",
            allocated_storage=20,
            vpc_security_group_ids=[sg.id],
            db_subnet_group_name=subnet_group.name,
            skip_final_snapshot=True,
            opts=pulumi.ResourceOptions(parent=self, protect=True),
        )

        self.endpoint = db.endpoint
        self.port = db.port
        self.register_outputs({"endpoint": self.endpoint, "port": self.port})
```

### Composition Pattern

Components that compose other components:

```python
class AppStack(pulumi.ComponentResource):
    def __init__(self, name, opts=None):
        super().__init__("custom:app:Stack", name, {}, opts)

        self.network = Vpc(f"{name}-network", VpcArgs(),
            opts=pulumi.ResourceOptions(parent=self))

        self.database = Database(f"{name}-db",
            vpc_id=self.network.vpc_id,
            subnet_ids=self.network.private_subnet_ids,
            opts=pulumi.ResourceOptions(parent=self))

        self.register_outputs({
            "vpc_id": self.network.vpc_id,
            "db_endpoint": self.database.endpoint,
        })
```

## Pulumi Crosswalk Libraries

Pulumi provides higher-level component libraries (crosswalk) for common patterns:

```python
import pulumi_awsx as awsx

# VPC with sensible defaults (replaces 50+ lines of raw AWS resources)
vpc = awsx.ec2.Vpc("main",
    nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
        strategy=awsx.ec2.NatGatewayStrategy.SINGLE,
    ),
)

# ECS Fargate service with ALB
service = awsx.ecs.FargateService("api",
    cluster=cluster.arn,
    assign_public_ip=True,
    task_definition_args=awsx.ecs.FargateServiceTaskDefinitionArgs(
        container=awsx.ecs.TaskDefinitionContainerDefinitionArgs(
            name="api",
            image="my-api:latest",
            cpu=256,
            memory=512,
            port_mappings=[awsx.ecs.TaskDefinitionPortMappingArgs(
                container_port=8080,
                target_group=lb_target_group,
            )],
        ),
    ),
)
```

```bash
pip install pulumi-awsx   # AWS Crosswalk
pip install pulumi-eks    # EKS components
```

## Multi-Language Components

Build a component in one language and consume it from any Pulumi-supported language using Pulumi Packages:

1. Write the component in your language of choice
2. Define a schema (Pulumi schema JSON)
3. Generate SDK bindings for other languages
4. Publish as a package

This is an advanced topic — see the Pulumi docs for the full component provider workflow.

## Best Practices

1. **Use descriptive type tokens** — `"custom:network:Vpc"` not `"myVpc"`
2. **Always set `parent=self`** on child resources for proper hierarchy
3. **Always call `register_outputs()`** — even if no outputs, call with `{}`
4. **Use args dataclasses** — structured inputs are clearer than many constructor params
5. **Expose only what consumers need** — keep internal resources private
6. **Inherit resource options** — pass `opts` to `super().__init__()` for transform/provider inheritance
7. **Name children with component prefix** — `f"{name}-bucket"` prevents collisions
8. **Protect stateful resources** — databases and storage inside components should use `protect=True`
