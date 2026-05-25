# Providers

> Source: https://www.pulumi.com/docs/iac/concepts/providers/ | Version: 3.242.0

## Table of Contents

- [Provider Model](#provider-model)
- [Default Providers](#default-providers)
- [Explicit Providers](#explicit-providers)
- [Multi-Region Deployments](#multi-region-deployments)
- [Multi-Cloud Deployments](#multi-cloud-deployments)
- [AWS Provider](#aws-provider)
- [Azure Native Provider](#azure-native-provider)
- [GCP Provider](#gcp-provider)
- [Kubernetes Provider](#kubernetes-provider)
- [Dynamic Providers](#dynamic-providers)
- [Terraform Bridge Providers](#terraform-bridge-providers)

## Provider Model

Providers are plugins that implement CRUD operations for specific cloud platforms. Each provider:
- Manages authentication with the cloud API
- Translates Pulumi resource definitions into API calls
- Handles resource diffs and update logic
- Communicates with the Pulumi engine via gRPC

```bash
# Providers are installed automatically when you install the SDK
pip install pulumi-aws        # AWS provider
pip install pulumi-azure-native  # Azure provider
pip install pulumi-gcp        # GCP provider
pip install pulumi-kubernetes # Kubernetes provider
```

## Default Providers

When you create a resource without specifying a provider, Pulumi uses the default provider configured via stack config or environment variables:

```python
import pulumi_aws as aws

# Uses the default AWS provider (region from pulumi config or AWS_REGION)
bucket = aws.s3.BucketV2("my-bucket")
```

```bash
# Configure default provider via stack config
pulumi config set aws:region us-east-1
pulumi config set aws:profile production
```

## Explicit Providers

Create provider instances for fine-grained control:

```python
import pulumi
import pulumi_aws as aws

# Create explicit provider instances
us_east = aws.Provider("us-east-1",
    region="us-east-1",
    profile="production",
)

us_west = aws.Provider("us-west-2",
    region="us-west-2",
    profile="production",
)

# Use explicit providers
east_bucket = aws.s3.BucketV2("east-data",
    opts=pulumi.ResourceOptions(provider=us_east),
)

west_bucket = aws.s3.BucketV2("west-data",
    opts=pulumi.ResourceOptions(provider=us_west),
)
```

### Provider Inheritance

Child resources inherit providers from their parent component:

```python
class RegionalInfra(pulumi.ComponentResource):
    def __init__(self, name, region, opts=None):
        provider = aws.Provider(f"{name}-provider", region=region)
        super().__init__("custom:infra:Regional", name, {},
            opts=pulumi.ResourceOptions.merge(opts, pulumi.ResourceOptions(
                providers=[provider],
            )),
        )
        # All children automatically use the regional provider
        self.bucket = aws.s3.BucketV2(f"{name}-bucket",
            opts=pulumi.ResourceOptions(parent=self),
        )
```

## Multi-Region Deployments

```python
import pulumi
import pulumi_aws as aws

regions = ["us-east-1", "us-west-2", "eu-west-1"]

for region in regions:
    provider = aws.Provider(f"aws-{region}", region=region)

    bucket = aws.s3.BucketV2(f"data-{region}",
        tags={"Region": region},
        opts=pulumi.ResourceOptions(provider=provider),
    )

    table = aws.dynamodb.Table(f"cache-{region}",
        attributes=[aws.dynamodb.TableAttributeArgs(
            name="id", type="S",
        )],
        hash_key="id",
        billing_mode="PAY_PER_REQUEST",
        opts=pulumi.ResourceOptions(provider=provider),
    )
```

## Multi-Cloud Deployments

```python
import pulumi
import pulumi_aws as aws
import pulumi_gcp as gcp

# AWS resources
aws_bucket = aws.s3.BucketV2("aws-data")

# GCP resources (uses default GCP provider)
gcp_bucket = gcp.storage.Bucket("gcp-data",
    location="US",
)

pulumi.export("aws_bucket", aws_bucket.id)
pulumi.export("gcp_bucket", gcp_bucket.url)
```

## AWS Provider

```python
import pulumi_aws as aws

# Provider configuration
provider = aws.Provider("aws",
    region="us-east-1",
    profile="prod",                    # AWS CLI profile
    assume_role=aws.ProviderAssumeRoleArgs(
        role_arn="arn:aws:iam::123456789:role/deploy",
        session_name="pulumi",
    ),
    default_tags=aws.ProviderDefaultTagsArgs(
        tags={
            "ManagedBy": "pulumi",
            "Environment": "production",
        },
    ),
)
```

Common AWS resources:

```python
# VPC
vpc = aws.ec2.Vpc("main", cidr_block="10.0.0.0/16")

# S3 Bucket
bucket = aws.s3.BucketV2("data")

# Lambda Function
fn = aws.lambda_.Function("handler",
    runtime="python3.12",
    handler="index.handler",
    role=role.arn,
    code=pulumi.FileArchive("./src"),
)

# RDS Instance
db = aws.rds.Instance("postgres",
    engine="postgres",
    engine_version="16.4",
    instance_class="db.t4g.micro",
    allocated_storage=20,
    db_name="mydb",
    username="admin",
    password=config.require_secret("dbPassword"),
    skip_final_snapshot=True,
)

# ECS Fargate Service
service = awsx.ecs.FargateService("api",
    cluster=cluster.arn,
    task_definition_args=awsx.ecs.FargateServiceTaskDefinitionArgs(
        container=awsx.ecs.TaskDefinitionContainerDefinitionArgs(
            name="api",
            image="my-api:latest",
            cpu=256,
            memory=512,
            essential=True,
            port_mappings=[awsx.ecs.TaskDefinitionPortMappingArgs(
                container_port=8080,
            )],
        ),
    ),
)
```

## Azure Native Provider

```python
import pulumi_azure_native as azure

# Resource Group
rg = azure.resources.ResourceGroup("rg",
    location="eastus",
)

# Storage Account
storage = azure.storage.StorageAccount("storage",
    resource_group_name=rg.name,
    location=rg.location,
    sku=azure.storage.SkuArgs(name="Standard_LRS"),
    kind="StorageV2",
)

# App Service
app = azure.web.WebApp("webapp",
    resource_group_name=rg.name,
    server_farm_id=plan.id,
    site_config=azure.web.SiteConfigArgs(
        app_settings=[
            azure.web.NameValuePairArgs(name="ENV", value="production"),
        ],
    ),
)
```

## GCP Provider

```python
import pulumi_gcp as gcp

# GCS Bucket
bucket = gcp.storage.Bucket("data",
    location="US",
    uniform_bucket_level_access=True,
)

# Cloud Run Service
service = gcp.cloudrunv2.Service("api",
    location="us-central1",
    template=gcp.cloudrunv2.ServiceTemplateArgs(
        containers=[gcp.cloudrunv2.ServiceTemplateContainerArgs(
            image="gcr.io/my-project/api:latest",
            ports=[gcp.cloudrunv2.ServiceTemplateContainerPortArgs(
                container_port=8080,
            )],
        )],
    ),
)
```

## Kubernetes Provider

```python
import pulumi_kubernetes as k8s

# Use default kubeconfig
provider = k8s.Provider("k8s",
    kubeconfig=cluster.kubeconfig,  # Or from file
)

# Deployment
deployment = k8s.apps.v1.Deployment("nginx",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        labels={"app": "nginx"},
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=3,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels={"app": "nginx"},
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels={"app": "nginx"},
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[k8s.core.v1.ContainerArgs(
                    name="nginx",
                    image="nginx:1.27",
                    ports=[k8s.core.v1.ContainerPortArgs(
                        container_port=80,
                    )],
                )],
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(provider=provider),
)

# Helm Chart (v4)
chart = k8s.helm.v4.Chart("ingress",
    chart="ingress-nginx",
    repository_opts=k8s.helm.v4.RepositoryOptsArgs(
        repo="https://kubernetes.github.io/ingress-nginx",
    ),
    values={"controller": {"replicaCount": 2}},
    opts=pulumi.ResourceOptions(provider=provider),
)
```

## Dynamic Providers

Create custom providers for resources not covered by existing providers:

```python
from pulumi.dynamic import Resource, ResourceProvider, CreateResult

class MyApiProvider(ResourceProvider):
    def create(self, inputs):
        # Make API call to create resource
        result = requests.post("https://api.example.com/resources",
            json={"name": inputs["name"]},
        )
        return CreateResult(
            id_=result.json()["id"],
            outs={**inputs, "endpoint": result.json()["endpoint"]},
        )

    def delete(self, id, props):
        requests.delete(f"https://api.example.com/resources/{id}")

    def diff(self, id, old_inputs, new_inputs):
        # Return changes
        changes = old_inputs.get("name") != new_inputs.get("name")
        return DiffResult(changes=changes)

class MyApiResource(Resource):
    endpoint: pulumi.Output[str]

    def __init__(self, name, args, opts=None):
        super().__init__(MyApiProvider(), name, {"endpoint": None, **args}, opts)

# Usage
resource = MyApiResource("my-thing", {"name": "example"})
pulumi.export("endpoint", resource.endpoint)
```

## Terraform Bridge Providers

Most Pulumi providers are built using the Terraform Bridge, which wraps existing Terraform providers. This gives Pulumi access to the 4,000+ Terraform provider ecosystem while maintaining the Pulumi programming model.

```bash
# Terraform-bridged providers work identically to native ones
pip install pulumi-datadog
pip install pulumi-cloudflare
pip install pulumi-github
```

The bridge automatically translates between Pulumi's Output model and Terraform's plan/apply cycle.
