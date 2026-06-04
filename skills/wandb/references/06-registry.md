# Model Registry

> Source: [docs.wandb.ai/models/registry](https://docs.wandb.ai/models/registry/) | wandb 0.27.1

## Table of Contents

- [Overview](#overview)
- [Registry Structure](#registry-structure)
- [Default Registries](#default-registries)
- [Creating Registries](#creating-registries)
- [Collections](#collections)
- [Linking Artifacts to Registry](#linking-artifacts-to-registry)
- [Aliases in Registry](#aliases-in-registry)
- [Tags and Metadata](#tags-and-metadata)
- [Lifecycle Workflow](#lifecycle-workflow)
- [Access Control](#access-control)
- [Automations with Registry](#automations-with-registry)
- [Public API](#public-api)
- [Common Patterns](#common-patterns)

## Overview

The W&B Registry is a curated central repository of artifact versions within an organization. It provides a single source of truth for production-ready models, validated datasets, and other artifacts that need lifecycle management, access control, and audit trails.

Key distinction: **Artifacts** live within projects and are created by runs. The **Registry** is organization-wide and contains linked references to artifact versions — no duplication of data.

## Registry Structure

```
Organization
└── Registry (e.g., "Models")
    ├── Collection (e.g., "text-classifier")
    │   ├── v0 → linked from project-a/text-model:v12
    │   ├── v1 → linked from project-a/text-model:v15
    │   └── v2 → linked from project-b/text-model:v3
    └── Collection (e.g., "image-classifier")
        ├── v0 → linked from project-c/resnet:v8
        └── v1 → linked from project-c/resnet:v10
```

## Default Registries

Every organization gets two registries automatically:

| Registry | Purpose |
|----------|---------|
| **Models** | Model artifacts for production deployment |
| **Datasets** | Dataset artifacts for reproducibility |

Custom registries can be created for other artifact types.

## Creating Registries

### Via UI

Navigate to Registry → Create Registry → specify name, type, and visibility.

### Via Python SDK

```python
import wandb

api = wandb.Api()
# Registries are created via the UI or W&B API
# Collections within registries can be created programmatically
```

## Collections

Collections group related artifact versions within a registry (e.g., one collection per model architecture or task).

### Creating Collections

Collections are auto-created when you first link an artifact to a target path that doesn't exist:

```python
with wandb.init(project="training") as run:
    model_artifact = run.log_artifact("model.pt", name="my-model", type="model")
    
    # "text-classifier" collection is auto-created if it doesn't exist
    run.link_artifact(
        artifact=model_artifact,
        target_path="wandb-registry-model/text-classifier",
    )
```

## Linking Artifacts to Registry

```python
with wandb.init(project="training", job_type="train") as run:
    # Step 1: Log artifact to project
    artifact = wandb.Artifact("my-model", type="model")
    artifact.add_file("model.pt")
    logged = run.log_artifact(artifact)
    logged.wait()

    # Step 2: Link to registry collection
    run.link_artifact(
        artifact=logged,
        target_path="wandb-registry-model/text-classifier",
    )
```

The registry assigns sequential version numbers (v0, v1, v2...) independent of the source artifact versions.

### Link via Public API

```python
api = wandb.Api()
artifact = api.artifact("entity/project/my-model:v5")
artifact.link("wandb-registry-model/text-classifier")
```

## Aliases in Registry

Aliases in the registry are independent of project-level aliases.

```python
api = wandb.Api()
artifact = api.artifact("wandb-registry-model/text-classifier:v3")
artifact.aliases.append("production")
artifact.aliases.append("approved-2026-06")
artifact.save()
```

Common alias patterns:

| Alias | Meaning |
|-------|---------|
| `latest` | Most recently linked version (auto-managed) |
| `staging` | Being tested for production |
| `production` | Currently deployed |
| `candidate` | Meets quality bar, awaiting review |

## Tags and Metadata

```python
api = wandb.Api()
collection = api.artifact_collection("model", "wandb-registry-model/text-classifier")

# Tag a collection
collection.tags = ["nlp", "production", "english"]
collection.save()

# Add metadata to a specific version
artifact = api.artifact("wandb-registry-model/text-classifier:v3")
artifact.metadata["approved_by"] = "ml-team"
artifact.metadata["evaluation_score"] = 0.95
artifact.save()
```

## Lifecycle Workflow

```
Training → Log Artifact → Link to Registry → Add Alias → Automate Deployment
                               │                   │
                               ├─ v0 (candidate)   ├─ staging
                               ├─ v1 (candidate)   ├─ production
                               └─ v2 (latest)      └─ latest
```

### Promotion Pattern

```python
api = wandb.Api()

# Promote staging to production
staging = api.artifact("wandb-registry-model/text-classifier:staging")
staging.aliases.append("production")

# Remove production from old version
old_prod = api.artifact("wandb-registry-model/text-classifier:v1")
old_prod.aliases.remove("production")

staging.save()
old_prod.save()
```

## Access Control

Registry visibility levels:

| Level | Who Can View | Who Can Link |
|-------|-------------|--------------|
| **Organization** | All org members | Members with registry write access |
| **Restricted** | Specified teams only | Specified teams with write access |

Permissions are managed at the registry level, not per-collection.

## Automations with Registry

Trigger actions when registry events occur:

```
Event: Alias "production" added to collection
  → Action: POST webhook to deployment service
  → Action: Slack notification to #ml-deploys
```

### Webhook Example

When a new version gets the `production` alias, fire a webhook to trigger model deployment:

```json
{
  "event_type": "add_alias",
  "alias": "production",
  "artifact_version": "wandb-registry-model/text-classifier:v3",
  "artifact_digest": "abc123...",
  "collection": "text-classifier"
}
```

See `references/08-reports-automations.md` for full automation setup.

## Public API

```python
api = wandb.Api()

# List all collections in a registry
collections = api.artifact_type("model").collections()
for c in collections:
    print(f"{c.name}: {len(list(c.versions()))} versions")

# Get specific version
artifact = api.artifact("wandb-registry-model/text-classifier:production")
print(f"Version: {artifact.version}")
print(f"Created: {artifact.created_at}")
print(f"Metadata: {artifact.metadata}")

# Download from registry
path = artifact.download()
```

## Common Patterns

### CI/CD Model Deployment

```python
def deploy_model(registry_path: str, alias: str = "production"):
    api = wandb.Api()
    artifact = api.artifact(f"{registry_path}:{alias}")
    model_dir = artifact.download()
    
    # Deploy to your serving infrastructure
    deploy_to_serving(model_dir, version=artifact.version)
    
    return artifact.version
```

### Model Comparison Before Promotion

```python
api = wandb.Api()

candidate = api.artifact("wandb-registry-model/text-classifier:latest")
production = api.artifact("wandb-registry-model/text-classifier:production")

candidate_run = candidate.logged_by()
production_run = production.logged_by()

if candidate_run.summary["val/accuracy"] > production_run.summary["val/accuracy"]:
    candidate.aliases.append("production")
    production.aliases.remove("production")
    candidate.save()
    production.save()
```

## Related

- Artifacts → `references/05-artifacts.md`
- Reports & Automations → `references/08-reports-automations.md`
