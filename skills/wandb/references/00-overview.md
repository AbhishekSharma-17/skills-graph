# Weights & Biases (wandb) — Overview

> Source: [docs.wandb.ai](https://docs.wandb.ai) | Version: 0.27.1 | Python >=3.10

## Table of Contents

- [What Is W&B](#what-is-wb)
- [Platform Architecture](#platform-architecture)
- [Installation](#installation)
- [Authentication](#authentication)
- [Core Concepts](#core-concepts)
- [Quickstart](#quickstart)
- [Project Organization](#project-organization)
- [Environment Variables](#environment-variables)
- [Common Pitfalls](#common-pitfalls)

## What Is W&B

Weights & Biases is an AI developer platform for tracking machine learning experiments, versioning datasets and models, tuning hyperparameters, and monitoring LLM applications. It consists of two major product lines:

**W&B Models** — experiment tracking, sweeps, artifacts, model registry, reports, and automations for traditional ML and deep learning workflows.

**W&B Weave** — LLM observability and evaluation platform for tracing, scoring, and monitoring large language model applications (RAG, agents, chatbots).

## Platform Architecture

```
┌────────────────────────────────────────────────┐
│                  W&B Platform                   │
├───────────────────────┬────────────────────────┤
│      W&B Models       │       W&B Weave        │
├───────────────────────┼────────────────────────┤
│ Experiment Tracking   │ Tracing (Ops, Calls)   │
│ Hyperparameter Sweeps │ Evaluations (Scorers)  │
│ Artifacts (Datasets)  │ LLM Cost Tracking      │
│ Model Registry        │ Guardrails             │
│ Reports & Dashboards  │ Leaderboards           │
│ Automations           │ Provider Integrations  │
└───────────────────────┴────────────────────────┘
```

**W&B Models** is for training-loop workflows — you call `wandb.init()` and `wandb.log()` in your training script.

**W&B Weave** is for inference/application workflows — you call `weave.init()` and decorate functions with `@weave.op()`.

## Installation

```bash
# Core SDK
pip install wandb

# With media logging support (images, audio, video, 3D)
pip install wandb[media]

# Weave (LLM observability)
pip install weave

# Both together
pip install wandb weave
```

Verify installation:

```bash
wandb --version
python -c "import wandb; print(wandb.__version__)"
```

## Authentication

### API Key Setup

Get your API key from [wandb.ai/authorize](https://wandb.ai/authorize). The key is shown only once at creation time.

```bash
# Option 1: CLI login (interactive, stores key in ~/.netrc)
wandb login

# Option 2: Environment variable (preferred for CI/CD)
export WANDB_API_KEY=your_api_key_here

# Option 3: Python
import wandb
wandb.login(key="your_api_key_here")
```

### Service Accounts

For automated systems (CI/CD, cron jobs), create a service account in team settings instead of using personal API keys.

### Offline Mode

```bash
# Disable syncing (log locally only)
export WANDB_MODE=offline

# Sync offline runs later
wandb sync ./wandb/offline-run-*
```

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Run** | A single execution of a training script or experiment. Created with `wandb.init()` |
| **Project** | A collection of runs grouped by task (e.g., "image-classifier") |
| **Entity** | Your username or team name. Runs live under `entity/project` |
| **Config** | Hyperparameters and settings for a run (independent variables) |
| **Log** | Metrics recorded during training (dependent variables like loss, accuracy) |
| **Artifact** | A versioned file or directory (datasets, models, checkpoints) |
| **Sweep** | Automated hyperparameter search across multiple runs |
| **Registry** | Central repository for curated artifact versions |
| **Report** | Collaborative document with embedded visualizations |
| **Op** | (Weave) A decorated function that automatically logs inputs/outputs |
| **Call** | (Weave) A single execution of an Op, capturing all metadata |
| **Trace** | (Weave) A tree of related Calls sharing an execution context |

## Quickstart

### Minimal Experiment Tracking

```python
import wandb

config = {"learning_rate": 0.001, "epochs": 10, "batch_size": 32}

with wandb.init(project="my-project", config=config) as run:
    for epoch in range(config["epochs"]):
        loss = 1.0 / (epoch + 1)  # simulated
        accuracy = 1.0 - loss
        run.log({"loss": loss, "accuracy": accuracy, "epoch": epoch})

# Results visible at wandb.ai/<entity>/my-project
```

### Minimal LLM Tracing with Weave

```python
import weave
from openai import OpenAI

weave.init("my-llm-app")
client = OpenAI()

@weave.op()
def ask(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content

ask("What is the capital of France?")
# Traces visible at wandb.ai/<entity>/my-llm-app/weave
```

## Project Organization

```
entity/
├── project-a/
│   ├── runs/           # Experiment runs
│   ├── artifacts/      # Versioned datasets and models
│   ├── sweeps/         # Hyperparameter searches
│   ├── reports/        # Collaborative documents
│   └── automations/    # Event-driven workflows
├── project-b/
│   └── weave/          # LLM traces, evaluations, leaderboards
└── registry/           # Organization-wide artifact registry
    ├── Models/
    └── Datasets/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WANDB_API_KEY` | Authentication key | — |
| `WANDB_PROJECT` | Default project name | `"uncategorized"` |
| `WANDB_ENTITY` | Default team or username | User's default entity |
| `WANDB_MODE` | `"online"`, `"offline"`, `"disabled"` | `"online"` |
| `WANDB_DIR` | Local storage directory | `./wandb` |
| `WANDB_SILENT` | Suppress console output (`"true"`) | `"false"` |
| `WANDB_TAGS` | Comma-separated run tags | — |
| `WANDB_NOTES` | Run description | — |
| `WANDB_NAME` | Run display name | Auto-generated |
| `WANDB_LOG_MODEL` | Auto-log model checkpoints | `"false"` |
| `WANDB_WATCH` | Gradient logging: `"gradients"`, `"parameters"`, `"all"` | — |
| `WANDB_CONSOLE` | Console logging: `"wrap"`, `"redirect"`, `"off"` | `"wrap"` |
| `WANDB_DISABLE_CODE` | Disable code saving | `"false"` |

## Common Pitfalls

1. **Forgetting `wandb.finish()`** — use `with wandb.init() as run:` context manager to auto-finish runs.
2. **Logging too frequently** — log every N steps, not every sample. Media is expensive (keep <50 images/step).
3. **Metric naming** — names must match `/^[_a-zA-Z][_a-zA-Z0-9]*$/`. No hyphens, no leading digits.
4. **Config vs log confusion** — `config` is for inputs (hyperparameters), `log` is for outputs (metrics).
5. **API key exposure** — never commit API keys. Use `WANDB_API_KEY` env var or `.netrc`.
6. **Mixing Models and Weave** — use `wandb.init()` for training loops, `weave.init()` for LLM applications. They serve different workflows.
7. **Not using context manager** — `wandb.init()` without `with` statement can leave zombie runs if the script crashes.

## Related

- Experiment Tracking → `references/01-experiment-tracking.md`
- Weave Tracing → `references/09-weave-tracing.md`
- Integrations → `references/11-integrations.md`
