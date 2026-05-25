# CI/CD and Migration

> Source: https://www.pulumi.com/docs/iac/guides/continuous-delivery/ | Version: 3.242.0

## Table of Contents

- [CI/CD Overview](#cicd-overview)
- [GitHub Actions](#github-actions)
- [Pulumi Deployments](#pulumi-deployments)
- [GitOps Workflow](#gitops-workflow)
- [Other CI/CD Systems](#other-cicd-systems)
- [Migrating from Terraform](#migrating-from-terraform)
- [Importing Existing Resources](#importing-existing-resources)
- [Coexistence Strategies](#coexistence-strategies)

## CI/CD Overview

The standard Pulumi CI/CD pattern:

1. **Pull Request** → `pulumi preview` (show what would change)
2. **Merge to main** → `pulumi up` (deploy to staging)
3. **Release tag** → `pulumi up` (deploy to production)

Requirements:
- `PULUMI_ACCESS_TOKEN` — authenticate with Pulumi Cloud
- Cloud credentials — AWS, Azure, GCP credentials as secrets
- Pulumi CLI — installed in the CI environment

## GitHub Actions

### Preview on Pull Request

```yaml
# .github/workflows/preview.yml
name: Pulumi Preview

on:
  pull_request:
    branches: [main]

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - uses: pulumi/actions@v6
        with:
          command: preview
          stack-name: myorg/staging
          comment-on-pr: true        # Post preview as PR comment
          comment-on-summary: true
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
```

### Deploy on Merge

```yaml
# .github/workflows/deploy.yml
name: Pulumi Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements.txt

      - uses: pulumi/actions@v6
        with:
          command: up
          stack-name: myorg/staging
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production    # Requires approval
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements.txt

      - uses: pulumi/actions@v6
        with:
          command: up
          stack-name: myorg/production
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### GitHub Actions Options

```yaml
- uses: pulumi/actions@v6
  with:
    command: up                     # up, preview, destroy, refresh
    stack-name: myorg/prod          # Full stack reference
    work-dir: ./infrastructure      # Subdirectory with Pulumi.yaml
    cloud-url: s3://my-state        # Self-managed backend
    comment-on-pr: true             # Post preview as PR comment
    comment-on-summary: true        # Post to job summary
    diff: true                      # Show detailed diff
    expect-no-changes: true         # Fail if changes detected (drift check)
    refresh: true                   # Refresh before operation
    target: "**bucket**"            # Target specific resources
    parallel: 10                    # Parallel operations
    policyPacks: ./policies         # Run policy checks
    config-map: |                   # Set config values
      aws:region: us-east-1
```

### OIDC Authentication (No Long-Lived Keys)

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: pulumi/actions@v6
    with:
      command: up
      stack-name: myorg/prod
    env:
      PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
      AWS_ROLE_TO_ASSUME: arn:aws:iam::123456789:role/pulumi-deploy
```

## Pulumi Deployments

Managed deployment infrastructure by Pulumi Cloud — no self-hosted runners needed:

```bash
# Trigger deployment from CLI
pulumi deploy --stack myorg/prod

# Configure deployment settings (done in Pulumi Cloud UI or API)
```

Features:
- **Click-to-deploy** from Pulumi Cloud UI
- **Git integration** — auto-deploy on push
- **Drift detection** — scheduled refresh to detect changes
- **TTL stacks** — auto-destroy after a time period
- **Review stacks** — ephemeral stacks per PR

## GitOps Workflow

### With Pulumi Kubernetes Operator

Deploy Pulumi stacks from within Kubernetes:

```yaml
# Deploy the Pulumi operator
# Then create a Stack custom resource:
apiVersion: pulumi.com/v1
kind: Stack
metadata:
  name: my-app-prod
spec:
  stack: myorg/my-app/prod
  projectRepo: https://github.com/myorg/my-infra
  branch: main
  envRefs:
    PULUMI_ACCESS_TOKEN:
      type: Secret
      secret:
        name: pulumi-token
        key: token
  config:
    aws:region: us-east-1
  destroyOnFinalize: true
```

## Other CI/CD Systems

### GitLab CI

```yaml
# .gitlab-ci.yml
pulumi-preview:
  stage: test
  image: pulumi/pulumi-python:latest
  script:
    - pip install -r requirements.txt
    - pulumi preview --stack myorg/staging
  only:
    - merge_requests

pulumi-deploy:
  stage: deploy
  image: pulumi/pulumi-python:latest
  script:
    - pip install -r requirements.txt
    - pulumi up --yes --stack myorg/staging
  only:
    - main
```

### Jenkins

```groovy
pipeline {
    agent { docker { image 'pulumi/pulumi-python:latest' } }
    environment {
        PULUMI_ACCESS_TOKEN = credentials('pulumi-token')
    }
    stages {
        stage('Deploy') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pulumi up --yes --stack myorg/prod'
            }
        }
    }
}
```

## Migrating from Terraform

### Option 1: Pulumi Convert (Code Conversion)

```bash
# Convert HCL to Pulumi code
cd terraform-project/
pulumi convert --from terraform --language python --out ../pulumi-project

# Converts:
# - .tf files → __main__.py
# - Terraform modules → Pulumi components
# - Variables → Pulumi config
# - Outputs → pulumi.export()
```

Supported conversions:
- Terraform 1.x HCL syntax
- Most built-in functions
- Module references
- Provider configurations
- Data sources

### Option 2: State Import

```bash
# Import Terraform state into Pulumi
cd pulumi-project/
pulumi import --from terraform ../terraform-project/terraform.tfstate

# This:
# 1. Reads Terraform state file
# 2. Maps TF resource types to Pulumi types
# 3. Imports resources into Pulumi state
# 4. Generates skeleton Pulumi code
```

### Option 3: Pulumi Neo (AI-Assisted)

Pulumi Neo can automate the full migration — converting code, importing state, and validating the result. Available through Pulumi Cloud.

### Option 4: Coexistence

Use both tools simultaneously during gradual migration:

```python
# Read Terraform state outputs from Pulumi
import pulumi_terraform as terraform

tf_state = terraform.state.RemoteStateReference("network",
    backend_type="s3",
    config={
        "bucket": "my-tf-state",
        "key": "network/terraform.tfstate",
        "region": "us-east-1",
    },
)

vpc_id = tf_state.get_output("vpc_id")
```

## Importing Existing Resources

Bring unmanaged cloud resources under Pulumi control without recreating them:

### CLI Import

```bash
# Single resource
pulumi import aws:s3/bucketV2:BucketV2 my-bucket actual-bucket-name

# The CLI outputs the code you need to add to your program
```

### Bulk Import

```bash
# Create an import file
pulumi import --file imports.json
```

```json
{
  "resources": [
    {
      "type": "aws:ec2/vpc:Vpc",
      "name": "main-vpc",
      "id": "vpc-0123456789abcdef0"
    },
    {
      "type": "aws:ec2/subnet:Subnet",
      "name": "public-a",
      "id": "subnet-0123456789abcdef0"
    }
  ]
}
```

### Code-Based Import

```python
# Add import option to resource — run once, then remove
vpc = aws.ec2.Vpc("existing-vpc",
    cidr_block="10.0.0.0/16",
    opts=pulumi.ResourceOptions(
        import_="vpc-0123456789abcdef0",
    ),
)
# After successful import, remove the import_ option
```

## Coexistence Strategies

### Gradual Migration

1. Start by reading Terraform outputs from Pulumi via `RemoteStateReference`
2. Create new resources in Pulumi
3. Migrate existing resources one at a time using `pulumi import`
4. Remove corresponding Terraform resources with `terraform state rm`
5. Eventually decommission Terraform entirely

### Boundary Pattern

- Terraform manages legacy/stable infrastructure (VPCs, core networking)
- Pulumi manages application infrastructure (services, functions, containers)
- Share data via Terraform outputs → Pulumi stack references

### Tips

- Never let both tools manage the same resource
- Import before removing from Terraform state
- Test the migration in a dev environment first
- Use `pulumi refresh` after import to verify state accuracy
