# Pulumi Overview

> Source: https://www.pulumi.com/docs/ | Version: 3.242.0

## Table of Contents

- [What Is Pulumi](#what-is-pulumi)
- [Key Differentiators](#key-differentiators)
- [Installation](#installation)
- [Project Setup](#project-setup)
- [CLI Commands](#cli-commands)
- [Core Workflow](#core-workflow)
- [Language Support](#language-support)
- [Pulumi vs Terraform](#pulumi-vs-terraform)
- [Architecture Overview](#architecture-overview)

## What Is Pulumi

Pulumi is an infrastructure as code (IaC) platform that provisions and manages cloud resources using general-purpose programming languages. Instead of domain-specific languages like HCL, you write infrastructure definitions in Python, TypeScript, Go, C#, Java, or YAML and get full access to loops, conditionals, classes, type checking, testing frameworks, and package managers.

Pulumi supports 300+ cloud providers including AWS, Azure, GCP, Kubernetes, Cloudflare, Datadog, and more through its provider model.

## Key Differentiators

**Real programming languages** — use the same language for infrastructure and application code. No new syntax to learn.

**Rich type system** — full IDE support with autocompletion, type checking, and refactoring tools.

**Reusable abstractions** — build component resources using classes and share them as packages via npm, PyPI, or NuGet.

**Testing** — unit test infrastructure with standard testing frameworks (pytest, Jest, Go test).

**Automation API** — embed Pulumi as a library inside applications, web servers, or CI/CD pipelines.

**Policy as Code** — CrossGuard enforces security, compliance, and cost policies at deployment time.

**State management** — Pulumi Cloud provides managed state, or self-host with S3, Azure Blob, GCS, or local filesystem.

## Installation

```bash
# macOS
brew install pulumi/tap/pulumi

# Linux
curl -fsSL https://get.pulumi.com | sh

# Windows
choco install pulumi

# Verify
pulumi version
```

### Python SDK Setup

```bash
# Create a new project
mkdir my-infra && cd my-infra
pulumi new python

# This creates:
# Pulumi.yaml        — project metadata
# __main__.py        — infrastructure code
# requirements.txt   — Python dependencies
# venv/              — virtual environment

# Install provider SDKs
pip install pulumi-aws pulumi-azure-native pulumi-gcp
```

### TypeScript SDK Setup

```bash
pulumi new typescript

# Install provider SDKs
npm install @pulumi/aws @pulumi/azure-native @pulumi/gcp
```

## Project Setup

Every Pulumi project needs a `Pulumi.yaml` file:

```yaml
name: my-infrastructure
runtime: python         # or nodejs, go, dotnet, java, yaml
description: Production AWS infrastructure
```

For Python projects with options:

```yaml
name: my-infrastructure
runtime:
  name: python
  options:
    virtualenv: venv
    toolchain: pip      # or poetry, uv
description: Production AWS infrastructure
```

## CLI Commands

### Essential Commands

```bash
# Project lifecycle
pulumi new <template>       # Create new project from template
pulumi up                   # Preview and deploy changes
pulumi preview              # Preview changes without deploying
pulumi destroy              # Tear down all resources
pulumi refresh              # Sync state with actual cloud state

# Stack management
pulumi stack init <name>    # Create a new stack
pulumi stack select <name>  # Switch active stack
pulumi stack ls             # List all stacks
pulumi stack rm <name>      # Remove a stack
pulumi stack output         # Show stack outputs
pulumi stack export         # Export state as JSON
pulumi stack import         # Import state from JSON

# Configuration
pulumi config set <key> <value>           # Set plain config
pulumi config set --secret <key> <value>  # Set encrypted secret
pulumi config get <key>                   # Read config value
pulumi config rm <key>                    # Remove config value

# Resource management
pulumi import <type> <name> <id>   # Import existing resource
pulumi state delete <urn>          # Remove resource from state
pulumi state unprotect <urn>       # Remove protect flag

# Information
pulumi whoami                # Show current user/org
pulumi about                 # Show environment info
pulumi logs                  # Show resource logs (if supported)
```

### Flags

```bash
pulumi up --yes              # Skip confirmation prompt
pulumi up --skip-preview     # Deploy without preview
pulumi up -t <urn>           # Target specific resources
pulumi up --diff             # Show detailed diff
pulumi up -r                 # Replace resources (force recreate)
pulumi preview --json        # Machine-readable preview output
pulumi destroy --target <urn> # Destroy specific resource
```

## Core Workflow

```
Write Code → pulumi preview → Review Changes → pulumi up → Verify
```

1. **Write** infrastructure in your language of choice
2. **Preview** changes with `pulumi preview`
3. **Review** the diff showing creates, updates, deletes
4. **Deploy** with `pulumi up`
5. **Verify** outputs and resource state

```python
import pulumi
import pulumi_aws as aws

bucket = aws.s3.BucketV2("my-bucket",
    tags={"Environment": "production"},
)

pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
```

## Language Support

| Language | Runtime | Package Manager | Provider Install |
|----------|---------|----------------|-----------------|
| Python | `python` | pip / poetry / uv | `pip install pulumi-aws` |
| TypeScript | `nodejs` | npm / yarn / pnpm | `npm install @pulumi/aws` |
| Go | `go` | go modules | `go get github.com/pulumi/pulumi-aws/sdk/v7` |
| C# | `dotnet` | NuGet | `dotnet add package Pulumi.Aws` |
| Java | `java` | Maven / Gradle | Maven dependency |
| YAML | `yaml` | N/A | Declared in Pulumi.yaml |

## Pulumi vs Terraform

| Aspect | Pulumi | Terraform |
|--------|--------|-----------|
| Language | Python, TS, Go, C#, Java, YAML | HCL (domain-specific) |
| State | Pulumi Cloud (managed) or self-hosted | Terraform Cloud or self-hosted |
| Testing | Standard testing frameworks | `terraform test` (limited) |
| IDE Support | Full (type checking, autocomplete) | HCL extensions only |
| Reusability | Classes, packages, inheritance | Modules |
| Providers | 300+ (bridges Terraform providers) | 4,000+ native |
| Policy | CrossGuard (Python/TS) | Sentinel / OPA |
| Automation | Automation API (embedded SDK) | CLI wrapper / CDK for Terraform |
| Learning curve | Know your language | Learn HCL |

Pulumi can consume Terraform providers via its bridge layer, giving access to the Terraform ecosystem while using real programming languages.

## Architecture Overview

```
Your Code (Python/TS/Go)
    ↓
Pulumi Language Host
    ↓
Pulumi Engine (diffing, dependency graph)
    ↓
Resource Providers (AWS, Azure, GCP, K8s...)
    ↓
Cloud APIs
```

**Language Host** — runs your program, intercepts resource registrations, and communicates with the engine via gRPC.

**Engine** — builds a dependency graph, computes the diff against stored state, and orchestrates create/update/delete operations.

**Providers** — gRPC plugins that translate Pulumi resource definitions into cloud API calls. Each provider manages its own authentication and API versioning.

**State** — a JSON checkpoint of all managed resources, stored in Pulumi Cloud or a self-managed backend. Used by the engine to compute diffs.
