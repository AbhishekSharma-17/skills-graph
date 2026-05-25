# Projects and Stacks

> Source: https://www.pulumi.com/docs/iac/concepts/projects/ | Version: 3.242.0

## Table of Contents

- [Projects](#projects)
- [Pulumi.yaml Reference](#pulumiyaml-reference)
- [Stacks](#stacks)
- [Stack Configuration](#stack-configuration)
- [Stack Organization Patterns](#stack-organization-patterns)
- [Stack References](#stack-references)

## Projects

A Pulumi project is a directory containing a `Pulumi.yaml` file and the source code for your infrastructure program. Each project can have multiple stacks (instances of the program with different configurations).

```
my-project/
├── Pulumi.yaml            # Project metadata (required)
├── Pulumi.dev.yaml        # Stack config for "dev"
├── Pulumi.staging.yaml    # Stack config for "staging"
├── Pulumi.prod.yaml       # Stack config for "prod"
├── __main__.py            # Infrastructure code (Python)
├── requirements.txt       # Dependencies
└── venv/                  # Virtual environment
```

## Pulumi.yaml Reference

```yaml
name: my-infrastructure           # Required: project name (unique within org)
runtime: python                    # Required: language runtime
description: AWS infrastructure    # Optional: human-readable description

# Runtime with options
runtime:
  name: python
  options:
    virtualenv: venv               # Python virtual environment path
    toolchain: pip                 # pip, poetry, or uv

# For TypeScript/JavaScript
runtime:
  name: nodejs
  options:
    packagemanager: npm            # npm, yarn, or pnpm
    typescript: true               # Enable TypeScript

# For Go
runtime:
  name: go
  options:
    binary: my-infra               # Pre-built binary name

# Backend configuration (optional, overrides CLI default)
backend:
  url: s3://my-state-bucket

# Template configuration (for pulumi new templates)
template:
  description: My starter template
  config:
    aws:region:
      description: AWS region
      default: us-east-1
```

## Stacks

A stack is an isolated, independently configurable instance of a Pulumi program. Common patterns:

- **Environment-based**: `dev`, `staging`, `prod`
- **Region-based**: `us-east-1`, `eu-west-1`
- **Feature-based**: `feature-auth`, `feature-payments`
- **Tenant-based**: `customer-acme`, `customer-globex`

### Stack Lifecycle

```bash
# Create a new stack
pulumi stack init dev

# List stacks
pulumi stack ls
# NAME   LAST UPDATE  RESOURCE COUNT  URL
# dev    2 hours ago  12              https://app.pulumi.com/...
# prod*  1 day ago    45              https://app.pulumi.com/...

# Switch active stack
pulumi stack select dev

# Show stack details
pulumi stack

# Show stack outputs
pulumi stack output
pulumi stack output bucket_name    # Single output

# Remove a stack (must destroy resources first)
pulumi destroy
pulumi stack rm dev

# Force remove (skip resource check)
pulumi stack rm dev --force
```

### Stack Tags

```bash
# Set tags for organization
pulumi stack tag set environment production
pulumi stack tag set team platform
pulumi stack tag set cost-center eng-42

# List tags
pulumi stack tag ls

# Remove tag
pulumi stack tag rm cost-center
```

## Stack Configuration

Each stack has its own configuration stored in `Pulumi.<stack>.yaml`:

```bash
# Set configuration values
pulumi config set aws:region us-east-1
pulumi config set instanceType t3.micro
pulumi config set --secret dbPassword s3cr3t!

# Read in code (Python)
```

```python
import pulumi

config = pulumi.Config()

# Required values (raises if missing)
region = config.require("aws:region")
instance_type = config.require("instanceType")

# Optional values with defaults
replicas = config.get_int("replicas") or 3
enable_monitoring = config.get_bool("enableMonitoring") or True

# Secrets (automatically decrypted)
db_password = config.require_secret("dbPassword")  # Returns Output[str]

# Structured config (objects/lists)
config.require_object("tags")  # Returns dict
```

```typescript
// TypeScript
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();
const region = config.require("region");
const dbPassword = config.requireSecret("dbPassword");
const replicas = config.getNumber("replicas") ?? 3;
```

### Configuration File Format

```yaml
# Pulumi.prod.yaml
config:
  aws:region: us-east-1
  my-project:instanceType: t3.large
  my-project:replicas: "5"
  my-project:dbPassword:
    secure: AAABADQXFlU0mxol...   # Encrypted secret
  my-project:tags:
    environment: production
    team: platform
```

## Stack Organization Patterns

### Monolithic Stack

Single stack manages all infrastructure. Simple but doesn't scale well.

```python
# Everything in one program
vpc = aws.ec2.Vpc(...)
db = aws.rds.Instance(...)
cluster = aws.ecs.Cluster(...)
cdn = aws.cloudfront.Distribution(...)
```

### Micro-Stacks

Separate stacks per concern. Better isolation and team ownership.

```
infra/
├── networking/          # VPC, subnets, security groups
│   ├── Pulumi.yaml
│   └── __main__.py
├── database/            # RDS, ElastiCache
│   ├── Pulumi.yaml
│   └── __main__.py
├── compute/             # ECS, Lambda
│   ├── Pulumi.yaml
│   └── __main__.py
└── monitoring/          # CloudWatch, alerts
    ├── Pulumi.yaml
    └── __main__.py
```

### Per-Service Stacks

Each microservice has its own infrastructure stack, deployed independently.

## Stack References

Stack references let you read outputs from another stack:

```python
import pulumi

# Reference another stack's outputs
network_stack = pulumi.StackReference("myorg/networking/prod")

# Get outputs (returns Output[T])
vpc_id = network_stack.get_output("vpc_id")
subnet_ids = network_stack.get_output("private_subnet_ids")

# Use in resource definitions
instance = aws.ec2.Instance("web",
    subnet_id=subnet_ids[0],
    vpc_security_group_ids=[network_stack.get_output("web_sg_id")],
)
```

```typescript
// TypeScript
const networkStack = new pulumi.StackReference("myorg/networking/prod");
const vpcId = networkStack.getOutput("vpc_id");
const subnetIds = networkStack.getOutput("private_subnet_ids");
```

Best practices for stack references:
- Export only what consumers need (minimal API surface)
- Use descriptive output names
- Document stack outputs as your stack's public API
- Version stack outputs carefully — consumers depend on them
