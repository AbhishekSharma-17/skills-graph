# Logging Metrics

> Source: [docs.wandb.ai/models/track/log](https://docs.wandb.ai/models/track/log/) | wandb 0.27.1

## Table of Contents

- [Overview](#overview)
- [Basic Logging](#basic-logging)
- [Step Control](#step-control)
- [Custom X-Axes](#custom-x-axes)
- [Summary Metrics](#summary-metrics)
- [Metric Naming Rules](#metric-naming-rules)
- [Grouped Metrics](#grouped-metrics)
- [System Metrics](#system-metrics)
- [Automatic Tracking](#automatic-tracking)
- [Logging Frequency](#logging-frequency)
- [Common Patterns](#common-patterns)

## Overview

`wandb.Run.log()` records time-series data — metrics that change over the course of training. Data is saved locally in a `wandb/` directory and synced to the W&B cloud. Each `log()` call creates a new step by default.

## Basic Logging

```python
with wandb.init(project="my-project") as run:
    # Single metric
    run.log({"loss": 0.5})

    # Multiple metrics in one call
    run.log({"train/loss": 0.5, "train/accuracy": 0.85})

    # Nested keys create grouped panels
    run.log({
        "train/loss": 0.5,
        "train/accuracy": 0.85,
        "val/loss": 0.6,
        "val/accuracy": 0.82,
    })
```

## Step Control

By default, each `log()` call increments the internal step counter.

```python
# Automatic steps: 0, 1, 2, ...
for i in range(100):
    run.log({"loss": 1.0 / (i + 1)})

# Explicit step (must be monotonically increasing)
for step in range(0, 1000, 10):
    run.log({"loss": compute_loss()}, step=step)

# Multiple log calls at the same step (committed on next step change)
run.log({"train/loss": 0.5}, step=100)
run.log({"val/loss": 0.6}, step=100)

# Force commit current step
run.log({"loss": 0.5}, commit=True)

# Log without incrementing step
run.log({"loss": 0.5}, commit=False)
```

## Custom X-Axes

By default, all metrics are plotted against the global step. Use `define_metric()` for custom axes.

```python
with wandb.init() as run:
    # Plot validation metrics against epoch, not step
    run.define_metric("epoch")
    run.define_metric("val/*", step_metric="epoch")

    for epoch in range(10):
        for batch in range(100):
            run.log({"train/loss": compute_loss(), "epoch": epoch})
        run.log({"val/loss": val_loss, "val/acc": val_acc, "epoch": epoch})
```

### define_metric Parameters

```python
run.define_metric(
    name="val/loss",            # Metric name or glob pattern ("val/*")
    step_metric="epoch",        # X-axis metric name
    step_sync=True,             # Auto-sync step_metric from previous log calls
    summary="min",              # Summary aggregation: "min", "max", "mean", "last", "best", "copy", "none"
    goal="minimize",            # For "best" summary: "minimize" or "maximize"
    hidden=False,               # Hide from default workspace panels
)
```

## Summary Metrics

The run summary stores a single value per metric — by default, the last logged value. Override this with `define_metric()` or set directly:

```python
with wandb.init() as run:
    # Auto-track best validation accuracy
    run.define_metric("val/accuracy", summary="max")
    run.define_metric("val/loss", summary="min")

    for epoch in range(100):
        run.log({"val/accuracy": acc, "val/loss": loss})

    # Manual summary override
    run.summary["best_epoch"] = 42
    run.summary["final_model"] = "resnet50-v2"
```

### Summary via Public API

```python
api = wandb.Api()
run = api.run("entity/project/run_id")
print(run.summary["val/accuracy"])  # Best or last value
```

## Metric Naming Rules

Names must match: `/^[_a-zA-Z][_a-zA-Z0-9]*$/`

| Valid | Invalid | Reason |
|-------|---------|--------|
| `accuracy` | `loss-train` | Hyphens not allowed |
| `val_loss` | `5_fold_cv` | Cannot start with digit |
| `modelAccuracy` | `loss.train` | Periods not allowed in name |
| `train/loss` | `train loss` | Spaces not allowed |

Use `/` to create panel groups: `train/loss` and `train/accuracy` appear together.

## Grouped Metrics

Prefix metrics with a common namespace for automatic UI grouping:

```python
run.log({
    "train/loss": 0.5,
    "train/accuracy": 0.85,
    "train/lr": 0.001,
    "val/loss": 0.6,
    "val/accuracy": 0.82,
    "system/gpu_temp": 72,
})
# Creates three panel groups: train, val, system
```

## System Metrics

W&B automatically captures hardware metrics every 10 seconds:

| Metric | Description |
|--------|-------------|
| `system/cpu` | CPU utilization (%) |
| `system/memory` | System memory usage (%) |
| `system/gpu.*.gpu` | GPU utilization per device (%) |
| `system/gpu.*.memory` | GPU memory usage per device (%) |
| `system/gpu.*.temp` | GPU temperature per device (°C) |
| `system/gpu.*.power` | GPU power draw per device (W) |
| `system/network.sent` | Network bytes sent |
| `system/network.recv` | Network bytes received |
| `system/disk.*.in` | Disk read bytes |
| `system/disk.*.out` | Disk write bytes |
| `system/proc.memory.rssMB` | Process RSS memory (MB) |

### Disable system metrics

```python
with wandb.init(settings=wandb.Settings(_disable_stats=True)) as run:
    pass
```

## Automatic Tracking

Beyond system metrics, W&B auto-captures:
- **stdout/stderr** — console output
- **Git state** — commit hash and diff (when `save_code=True`)
- **Dependencies** — `requirements.txt` or pip freeze
- **Command** — the exact command used to start the script
- **Environment** — Python version, OS, hostname

## Logging Frequency

```python
# Log every N steps to reduce overhead
log_interval = 10
for step in range(10000):
    loss = train_step()
    if step % log_interval == 0:
        run.log({"loss": loss})

# Log at the end of each epoch
for epoch in range(100):
    for batch in train_loader:
        train_step(batch)
    run.log({"epoch": epoch, "val/accuracy": evaluate()})
```

## Common Patterns

### Learning Rate Scheduling

```python
for step in range(total_steps):
    loss = train_step()
    lr = scheduler.get_last_lr()[0]
    run.log({"loss": loss, "lr": lr})
    scheduler.step()
```

### Multi-GPU Training

```python
import torch.distributed as dist

if dist.get_rank() == 0:
    with wandb.init(project="distributed") as run:
        for step in range(steps):
            run.log({"loss": gathered_loss})
```

### Gradient Monitoring (PyTorch)

```python
with wandb.init() as run:
    run.watch(model, log="all", log_freq=100)
    # Logs gradient histograms and parameter distributions every 100 steps
```

## Related

- Logging Media → `references/03-logging-media.md`
- Tables → `references/07-tables.md`
- Experiment Tracking → `references/01-experiment-tracking.md`
