# Hyperparameter Sweeps

> Source: [docs.wandb.ai/models/sweeps](https://docs.wandb.ai/models/sweeps/) | wandb 0.27.1

## Table of Contents

- [Overview](#overview)
- [Sweep Configuration](#sweep-configuration)
- [Search Strategies](#search-strategies)
- [Parameter Types](#parameter-types)
- [Creating and Running Sweeps](#creating-and-running-sweeps)
- [Sweep Agents](#sweep-agents)
- [Early Termination](#early-termination)
- [Multi-Machine Sweeps](#multi-machine-sweeps)
- [Programmatic API](#programmatic-api)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

W&B Sweeps automate hyperparameter search by orchestrating multiple training runs with different configurations. A central sweep controller selects the next set of hyperparameters, and agents on one or more machines execute training runs.

```
┌──────────────────┐
│  Sweep Controller │ ← Selects next hyperparameter set
│  (W&B Cloud)      │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Agent 1│ │Agent 2│ ← Execute training runs
│(GPU 0)│ │(GPU 1)│
└───────┘ └───────┘
```

## Sweep Configuration

Define sweeps in YAML or Python dict:

### YAML (sweep.yaml)

```yaml
program: train.py
method: bayes
metric:
  name: val/accuracy
  goal: maximize
parameters:
  learning_rate:
    min: 0.0001
    max: 0.1
    distribution: log_uniform_values
  batch_size:
    values: [16, 32, 64, 128]
  optimizer:
    values: ["adam", "sgd", "adamw"]
  dropout:
    min: 0.0
    max: 0.5
  epochs:
    value: 50
```

### Python Dict

```python
sweep_config = {
    "method": "bayes",
    "metric": {"name": "val/accuracy", "goal": "maximize"},
    "parameters": {
        "learning_rate": {"min": 0.0001, "max": 0.1, "distribution": "log_uniform_values"},
        "batch_size": {"values": [16, 32, 64, 128]},
        "optimizer": {"values": ["adam", "sgd", "adamw"]},
        "dropout": {"min": 0.0, "max": 0.5},
        "epochs": {"value": 50},
    },
}
```

## Search Strategies

| Method | Description | Best For |
|--------|-------------|----------|
| `grid` | Exhaustive search over all parameter combinations | Small, discrete search spaces |
| `random` | Random sampling from parameter distributions | Large search spaces, initial exploration |
| `bayes` | Bayesian optimization using Gaussian processes | Expensive training, continuous parameters |

### Grid Search

Tests every combination. Total runs = product of all parameter value counts.

```yaml
method: grid
parameters:
  lr: { values: [0.001, 0.01, 0.1] }
  batch_size: { values: [32, 64] }
# Creates 3 × 2 = 6 runs
```

### Random Search

Samples independently from each parameter distribution.

```yaml
method: random
parameters:
  lr: { distribution: log_uniform_values, min: 0.0001, max: 0.1 }
  dropout: { distribution: uniform, min: 0.0, max: 0.5 }
```

### Bayesian Optimization

Uses a Gaussian process to model the objective function and select promising parameter sets.

```yaml
method: bayes
metric:
  name: val/loss
  goal: minimize
parameters:
  lr: { min: 0.0001, max: 0.1 }
  layers: { values: [2, 3, 4, 5] }
```

## Parameter Types

| Type | Config | Example |
|------|--------|---------|
| **Constant** | `value: X` | `epochs: {value: 50}` |
| **Categorical** | `values: [...]` | `optimizer: {values: ["adam", "sgd"]}` |
| **Integer range** | `min/max + distribution` | `layers: {min: 1, max: 5, distribution: int_uniform}` |
| **Uniform** | `min/max` | `dropout: {min: 0.0, max: 0.5}` |
| **Log-uniform** | `min/max + distribution` | `lr: {min: 1e-5, max: 1e-1, distribution: log_uniform_values}` |
| **Normal** | `mu/sigma` | `weight_decay: {distribution: normal, mu: 0, sigma: 0.1}` |
| **Nested** | `parameters: {...}` | Conditional parameters |

### Distributions

| Distribution | Description |
|-------------|-------------|
| `uniform` | Uniform between min and max |
| `log_uniform_values` | Log-uniform between min and max (useful for learning rates) |
| `int_uniform` | Uniform integer between min and max |
| `normal` | Normal distribution with mu and sigma |
| `log_normal` | Log-normal distribution with mu and sigma |
| `q_uniform` | Quantized uniform (round to nearest q) |
| `q_log_uniform_values` | Quantized log-uniform |
| `q_normal` | Quantized normal |
| `categorical` | Uniform over values list |

## Creating and Running Sweeps

### CLI Workflow

```bash
# 1. Create sweep from YAML config
wandb sweep sweep.yaml
# Output: Created sweep with ID: abc123

# 2. Start agent(s)
wandb agent entity/project/abc123
```

### Python Workflow

```python
import wandb

sweep_id = wandb.sweep(sweep_config, project="my-project")

def train():
    with wandb.init() as run:
        lr = run.config.learning_rate
        batch_size = run.config.batch_size

        for epoch in range(run.config.epochs):
            loss = train_epoch(lr, batch_size)
            run.log({"val/loss": loss})

wandb.agent(sweep_id, function=train, count=50)
```

## Sweep Agents

```bash
# Run up to 50 trials
wandb agent --count 50 entity/project/sweep_id

# Run on specific GPU
CUDA_VISIBLE_DEVICES=0 wandb agent entity/project/sweep_id
```

### Multiple Agents

Start agents on multiple machines pointing to the same sweep ID. The controller distributes work automatically.

```bash
# Machine 1
CUDA_VISIBLE_DEVICES=0 wandb agent entity/project/sweep_id

# Machine 2
CUDA_VISIBLE_DEVICES=0 wandb agent entity/project/sweep_id
```

## Early Termination

Stop underperforming runs early to save compute.

### Hyperband

```yaml
early_terminate:
  type: hyperband
  min_iter: 3      # Minimum epochs before termination
  eta: 3           # Elimination rate (keep top 1/eta)
  s: 2             # Number of brackets
```

### Custom via Code

```python
def train():
    with wandb.init() as run:
        for epoch in range(100):
            val_loss = train_epoch()
            run.log({"val/loss": val_loss})

            if val_loss > 10.0 and epoch > 5:
                break  # Manual early stop
```

## Multi-Machine Sweeps

```bash
# Same sweep ID on different machines
# Machine A (2 GPUs)
CUDA_VISIBLE_DEVICES=0 wandb agent entity/project/sweep_id &
CUDA_VISIBLE_DEVICES=1 wandb agent entity/project/sweep_id &

# Machine B (2 GPUs)
CUDA_VISIBLE_DEVICES=0 wandb agent entity/project/sweep_id &
CUDA_VISIBLE_DEVICES=1 wandb agent entity/project/sweep_id &
```

## Programmatic API

```python
api = wandb.Api()

# Get sweep results
sweep = api.sweep("entity/project/sweep_id")
print(f"Best run: {sweep.best_run().name}")
print(f"Best config: {sweep.best_run().config}")
print(f"Best metric: {sweep.best_run().summary['val/accuracy']}")

# Get all runs in a sweep
runs = sorted(sweep.runs, key=lambda r: r.summary.get("val/accuracy", 0), reverse=True)
for run in runs[:5]:
    print(f"{run.name}: {run.summary.get('val/accuracy', 'N/A')}")
```

## Common Patterns

### Training Function Template

```python
def train():
    with wandb.init() as run:
        config = run.config
        model = build_model(config)
        optimizer = get_optimizer(config)
        
        for epoch in range(config.epochs):
            train_loss = train_one_epoch(model, optimizer, config)
            val_loss, val_acc = evaluate(model)
            
            run.log({
                "train/loss": train_loss,
                "val/loss": val_loss,
                "val/accuracy": val_acc,
                "epoch": epoch,
            })
```

### Sweep with Conditional Parameters

```yaml
parameters:
  optimizer:
    values: ["adam", "sgd"]
  adam_params:
    parameters:
      beta1: { min: 0.8, max: 0.99 }
      beta2: { min: 0.9, max: 0.999 }
  sgd_params:
    parameters:
      momentum: { min: 0.0, max: 0.99 }
```

## Common Pitfalls

1. **Forgetting metric config** — Bayesian sweeps require `metric.name` and `metric.goal`.
2. **Using `grid` for continuous parameters** — grid only works with `values` lists.
3. **Not logging the optimization metric** — the metric name in sweep config must exactly match the logged key.
4. **Running too few Bayesian trials** — Bayesian optimization needs 20+ runs to build a useful surrogate model.
5. **Ignoring log_uniform_values** — for learning rates, always use log-uniform, not uniform.

## Related

- Experiment Tracking → `references/01-experiment-tracking.md`
- Artifacts → `references/05-artifacts.md`
