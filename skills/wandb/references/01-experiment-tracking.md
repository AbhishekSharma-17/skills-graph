# Experiment Tracking

> Source: [docs.wandb.ai/models/track](https://docs.wandb.ai/models/track/) | wandb 0.27.1

## Table of Contents

- [Overview](#overview)
- [Creating Runs](#creating-runs)
- [Run Configuration](#run-configuration)
- [wandb.init Parameters](#wandbinit-parameters)
- [Run Lifecycle](#run-lifecycle)
- [Run Groups and Jobs](#run-groups-and-jobs)
- [Resuming Runs](#resuming-runs)
- [Run Tags and Notes](#run-tags-and-notes)
- [Workspaces and Dashboards](#workspaces-and-dashboards)
- [Public API Access](#public-api-access)
- [Common Patterns](#common-patterns)

## Overview

W&B experiment tracking captures everything about a training run: hyperparameters via `config`, time-series metrics via `log()`, output files via artifacts, system metrics automatically, and git state if code saving is enabled.

Every call to `wandb.init()` creates a **Run** — the fundamental unit of tracking. Runs belong to projects, projects belong to entities (users or teams).

## Creating Runs

```python
import wandb

# Minimal — auto-generates project name
run = wandb.init()

# Recommended — context manager ensures cleanup
with wandb.init(project="image-classifier", entity="my-team") as run:
    run.log({"loss": 0.5})

# With config
config = {"lr": 0.001, "batch_size": 32, "model": "resnet50"}
with wandb.init(project="image-classifier", config=config) as run:
    # Training loop...
    pass
```

## Run Configuration

Config stores independent variables — things you set before training.

```python
# At init time
with wandb.init(config={"lr": 0.001, "epochs": 10}) as run:
    # Read config
    lr = run.config["lr"]

    # Update config mid-run
    run.config["dropout"] = 0.2
    run.config.update({"optimizer": "adam", "weight_decay": 1e-5})
```

### Config from argparse

```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--lr", type=float, default=0.001)
parser.add_argument("--epochs", type=int, default=10)
args = parser.parse_args()

with wandb.init(config=args) as run:
    lr = run.config["lr"]
```

### Config from YAML

Place `config-defaults.yaml` in the script directory:

```yaml
lr:
  value: 0.001
epochs:
  value: 10
model:
  value: resnet50
```

The file is auto-loaded by `wandb.init()`. Override with explicit config:

```python
with wandb.init(config={"lr": 0.01}) as run:
    # lr is 0.01, epochs and model come from YAML defaults
    pass
```

### Config after completion (Public API)

```python
api = wandb.Api()
run = api.run("entity/project/run_id")
run.config["notes"] = "best run so far"
run.update()
```

## wandb.init Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `project` | `str` | Project name (created if not exists) |
| `entity` | `str` | Team or user namespace |
| `config` | `dict \| argparse.Namespace` | Hyperparameters |
| `name` | `str` | Display name for this run |
| `tags` | `list[str]` | Searchable labels |
| `notes` | `str` | Markdown description |
| `group` | `str` | Group related runs (e.g., cross-validation folds) |
| `job_type` | `str` | Type label (e.g., `"train"`, `"eval"`, `"preprocess"`) |
| `resume` | `str` | `"allow"`, `"must"`, `"never"`, `"auto"`, or run ID |
| `id` | `str` | Unique run ID (for resuming) |
| `dir` | `str` | Local directory for run files |
| `mode` | `str` | `"online"`, `"offline"`, `"disabled"` |
| `save_code` | `bool` | Save the main script and git diff |
| `reinit` | `bool` | Allow multiple `wandb.init()` calls in one process |

## Run Lifecycle

```
wandb.init()  →  run.log()  →  run.finish()
   │                │               │
   ├─ Creates run   ├─ Logs metrics ├─ Uploads remaining data
   ├─ Syncs config  ├─ Auto-syncs   ├─ Marks run complete
   └─ Starts system └─ Streams to   └─ Releases resources
      metrics          cloud
```

### Automatic system metrics

W&B tracks without explicit code:
- CPU utilization and memory
- GPU utilization, memory, temperature, power
- Network I/O
- Disk I/O
- Process memory (RSS)

### Code saving

When `save_code=True` or `WANDB_SAVE_CODE=true`:
- Git commit hash and diff
- Main script source code
- `requirements.txt` / `pip freeze` output

## Run Groups and Jobs

```python
# Group cross-validation folds
for fold in range(5):
    with wandb.init(
        project="cv-experiment",
        group="experiment-1",
        job_type="train",
        name=f"fold-{fold}",
    ) as run:
        run.log({"fold_accuracy": 0.9 + fold * 0.01})
```

Groups appear collapsed in the UI — expand to see individual runs.

## Resuming Runs

```python
# Resume a specific run by ID
with wandb.init(project="my-project", id="abc123", resume="must") as run:
    # Continues logging from where it left off
    run.log({"loss": 0.1})
```

| Resume Mode | Behavior |
|-------------|----------|
| `"allow"` | Resume if run exists, create new otherwise |
| `"must"` | Resume existing run, error if not found |
| `"never"` | Always create new run, error if ID exists |
| `"auto"` | Resume if crash detected, create new otherwise |

## Run Tags and Notes

```python
with wandb.init(
    project="my-project",
    tags=["baseline", "resnet50", "augmented"],
    notes="Testing aggressive data augmentation with ResNet50",
) as run:
    # Add tags mid-run
    run.tags = run.tags + ("production-candidate",)
```

Tags are searchable in the UI and via the Public API.

## Workspaces and Dashboards

The W&B workspace provides:
- **Line plots** — metrics over time (loss curves, accuracy)
- **Scatter plots** — hyperparameter vs. metric correlations
- **Parallel coordinates** — multi-dimensional hyperparameter visualization
- **Bar charts** — comparing final metrics across runs
- **Custom panels** — Vega-Lite specifications for custom visualizations
- **Run tables** — sortable, filterable tables of all runs with config and summary

Pin important config keys for quick comparison:

```python
run.pin_config_keys(["lr", "batch_size", "model"])
```

## Public API Access

```python
api = wandb.Api()

# Access runs programmatically
runs = api.runs("entity/project", filters={"config.lr": 0.001})
for run in runs:
    print(run.name, run.summary["accuracy"])

# Download run data
run = api.run("entity/project/run_id")
history = run.history()  # pandas DataFrame
config = run.config
summary = run.summary
```

## Common Patterns

### Training Loop

```python
with wandb.init(project="classifier", config=config) as run:
    model = build_model(run.config)
    optimizer = torch.optim.Adam(model.parameters(), lr=run.config["lr"])

    for epoch in range(run.config["epochs"]):
        train_loss = train_one_epoch(model, train_loader, optimizer)
        val_loss, val_acc = evaluate(model, val_loader)

        run.log({
            "train/loss": train_loss,
            "val/loss": val_loss,
            "val/accuracy": val_acc,
            "epoch": epoch,
        })

    run.log_artifact(save_model(model), name="trained-model", type="model")
```

### Multiple Runs in One Script

```python
for lr in [0.001, 0.01, 0.1]:
    with wandb.init(project="lr-sweep", config={"lr": lr}, reinit=True) as run:
        run.log({"final_loss": train_with_lr(lr)})
```

## Related

- Logging Metrics → `references/02-logging-metrics.md`
- Logging Media → `references/03-logging-media.md`
- Sweeps → `references/04-sweeps.md`
