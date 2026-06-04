# Artifacts

> Source: [docs.wandb.ai/models/artifacts](https://docs.wandb.ai/models/artifacts/) | wandb 0.27.1

## Table of Contents

- [Overview](#overview)
- [Creating Artifacts](#creating-artifacts)
- [Adding Content](#adding-content)
- [Logging Artifacts](#logging-artifacts)
- [Using and Downloading Artifacts](#using-and-downloading-artifacts)
- [Versioning](#versioning)
- [Aliases](#aliases)
- [Artifact Types](#artifact-types)
- [Artifact Graph and Lineage](#artifact-graph-and-lineage)
- [External Storage](#external-storage)
- [TTL and Cleanup](#ttl-and-cleanup)
- [Public API](#public-api)
- [Common Patterns](#common-patterns)

## Overview

W&B Artifacts provide version control for datasets, models, and any files used in ML workflows. Every artifact has a name, type, and version. Artifacts track lineage — which runs produced them and which runs consumed them.

```
Dataset v0 → Training Run → Model v0 → Eval Run → Results Table
   (input)      (output)      (input)      (output)
```

## Creating Artifacts

```python
import wandb

with wandb.init(project="artifacts-demo", job_type="create-dataset") as run:
    artifact = wandb.Artifact(
        name="my-dataset",
        type="dataset",
        description="Training dataset for image classification",
        metadata={"num_samples": 10000, "split": "train"},
    )
    artifact.add_file("data/train.csv")
    run.log_artifact(artifact)
```

### wandb.Artifact Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Artifact name (unique within project + type) |
| `type` | `str` | Category: `"dataset"`, `"model"`, or custom |
| `description` | `str` | Human-readable description |
| `metadata` | `dict` | Arbitrary key-value pairs |

## Adding Content

### Single File

```python
artifact.add_file("path/to/file.csv", name="training_data.csv")
```

### Directory

```python
artifact.add_dir("data/images/", name="images")
```

### In-Memory Object

```python
# Add a wandb.Table
table = wandb.Table(columns=["id", "label"], data=[[1, "cat"], [2, "dog"]])
artifact.add(table, name="labels")
```

### Reference (External File)

```python
artifact.add_reference("s3://my-bucket/large-dataset/", name="training_data")
```

## Logging Artifacts

### As Run Output

```python
with wandb.init(job_type="train") as run:
    # Log after training
    run.log_artifact(artifact)

    # Shorthand for file/directory
    run.log_artifact("./model.pt", name="trained-model", type="model")
```

### Waiting for Upload

```python
artifact = run.log_artifact(artifact)
artifact.wait()  # Block until fully uploaded
```

## Using and Downloading Artifacts

### Mark as Input and Download

```python
with wandb.init(job_type="evaluate") as run:
    # Mark as run input (creates lineage edge)
    artifact = run.use_artifact("my-dataset:latest")

    # Download to local directory
    data_dir = artifact.download()  # Returns path string
    # Default: ./artifacts/my-dataset:v3/

    # Download to specific location
    data_dir = artifact.download(root="./data/")
```

### Fetch Without Marking as Input

```python
with wandb.init() as run:
    artifact = run.use_artifact("my-dataset:v2")
    path = artifact.get_path("training_data.csv").download()
```

## Versioning

Artifacts are automatically versioned. Each `log_artifact()` call creates a new version if the content has changed.

```
my-dataset:v0  →  my-dataset:v1  →  my-dataset:v2
   (initial)       (added rows)       (cleaned data)
```

W&B uses content-addressable storage — if the content hasn't changed, no new version is created.

### Version Specifiers

| Specifier | Meaning |
|-----------|---------|
| `"my-dataset:v0"` | Exact version 0 |
| `"my-dataset:v3"` | Exact version 3 |
| `"my-dataset:latest"` | Most recent version |
| `"my-dataset:production"` | Version with `production` alias |

## Aliases

Aliases are mutable pointers to specific artifact versions.

```python
# Add alias when logging
artifact = run.log_artifact(artifact)
artifact.aliases.append("production")
artifact.save()

# Via Public API
api = wandb.Api()
artifact = api.artifact("entity/project/my-model:v5")
artifact.aliases.append("staging")
artifact.save()
```

Built-in alias: `latest` always points to the most recent version.

## Artifact Types

The `type` parameter categorizes artifacts for organization and filtering:

| Type | Convention |
|------|-----------|
| `"dataset"` | Training/test datasets |
| `"model"` | Model weights and checkpoints |
| `"code"` | Source code snapshots |
| `"result"` | Evaluation results, predictions |
| Custom string | Any categorization you need |

```python
# Filter by type in API
api = wandb.Api()
collections = api.artifact_type("model", project="entity/project").collections()
```

## Artifact Graph and Lineage

W&B automatically tracks which runs produced and consumed artifacts, creating a directed acyclic graph (DAG).

```python
# Traverse lineage
api = wandb.Api()
artifact = api.artifact("entity/project/my-model:latest")

# Which run created this artifact?
producer_run = artifact.logged_by()

# Which runs used this artifact?
consumer_runs = artifact.used_by()

# What artifacts did the producer run consume?
for input_art in producer_run.used_artifacts():
    print(f"Input: {input_art.name}:{input_art.version}")
```

## External Storage

Track files in external storage without uploading to W&B:

```python
artifact = wandb.Artifact("external-data", type="dataset")
artifact.add_reference("s3://my-bucket/train-data/")
artifact.add_reference("gs://my-gcs-bucket/images/")
run.log_artifact(artifact)
```

Supported schemes: `s3://`, `gs://`, `https://`, local file paths.

## TTL and Cleanup

Set time-to-live policies to auto-delete old artifact versions:

```python
from datetime import timedelta

artifact = wandb.Artifact("temp-data", type="dataset")
artifact.ttl = timedelta(days=30)
run.log_artifact(artifact)
```

### Via Public API

```python
api = wandb.Api()
artifact = api.artifact("entity/project/temp-data:v0")
artifact.ttl = timedelta(days=7)
artifact.save()
```

## Public API

```python
api = wandb.Api()

# List artifact versions
versions = api.artifact_versions("dataset", "entity/project/my-dataset")
for v in versions:
    print(f"{v.version}: {v.created_at}, size={v.size}")

# Delete artifact version
artifact = api.artifact("entity/project/old-model:v0")
artifact.delete()

# Download artifact without a run context
artifact = api.artifact("entity/project/my-dataset:latest")
artifact.download(root="./data/")
```

## Common Patterns

### Dataset Versioning Pipeline

```python
with wandb.init(project="data-pipeline", job_type="preprocess") as run:
    raw = run.use_artifact("raw-data:latest")
    raw_dir = raw.download()

    processed_data = preprocess(raw_dir)

    artifact = wandb.Artifact("processed-data", type="dataset")
    artifact.add_dir(processed_data)
    run.log_artifact(artifact)
```

### Model Checkpointing

```python
with wandb.init(project="training") as run:
    for epoch in range(100):
        train_epoch(model)
        val_acc = evaluate(model)
        run.log({"val/accuracy": val_acc})

        if epoch % 10 == 0:
            torch.save(model.state_dict(), f"checkpoint_{epoch}.pt")
            artifact = wandb.Artifact(f"model-checkpoint", type="model")
            artifact.add_file(f"checkpoint_{epoch}.pt")
            run.log_artifact(artifact)
```

## Related

- Registry → `references/06-registry.md`
- Tables → `references/07-tables.md`
- Experiment Tracking → `references/01-experiment-tracking.md`
