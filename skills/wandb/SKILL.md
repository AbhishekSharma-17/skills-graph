---
name: wandb
description: "AI developer platform for experiment tracking, LLM observability, hyperparameter sweeps, artifact versioning, and model registry. MANDATORY TRIGGERS: wandb, weights and biases, weights & biases, W&B, weave, wandb.init, wandb.log. Also trigger when the user wants to track ML experiments, log training metrics, tune hyperparameters with sweeps, version datasets or models, trace LLM calls, evaluate LLM applications, or monitor AI agents. When in doubt about whether to use this skill for ML experiment tracking or LLM observability tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["ml", "experiment-tracking", "llm", "observability", "sweeps", "artifacts", "model-registry", "weave", "evaluation"]
---

# Weights & Biases (wandb)

> Source: [docs.wandb.ai](https://docs.wandb.ai) | Version tracked: 0.27.1 | `pip install wandb`

## Reference Files

| File | Read When |
|------|-----------|
| `references/00-overview.md` | Starting with W&B, understanding the platform, installation, auth |
| `references/01-experiment-tracking.md` | Creating runs, setting config, basic experiment workflow |
| `references/02-logging-metrics.md` | Logging scalars, system metrics, custom x-axes, summaries |
| `references/03-logging-media.md` | Logging images, audio, video, 3D objects, HTML, overlays |
| `references/04-sweeps.md` | Hyperparameter tuning with grid, random, Bayesian search |
| `references/05-artifacts.md` | Versioning datasets and models, artifact lineage graphs |
| `references/06-registry.md` | Model registry, collections, linking, lifecycle management |
| `references/07-tables.md` | Logging and querying tabular data, media in tables |
| `references/08-reports-automations.md` | Creating reports, webhooks, Slack alerts, event triggers |
| `references/09-weave-tracing.md` | LLM observability with Weave — ops, calls, traces, cost tracking |
| `references/10-weave-evaluations.md` | Evaluating LLM apps with scorers, datasets, leaderboards |
| `references/11-integrations.md` | PyTorch, Hugging Face, OpenAI, Anthropic, LangChain, Keras |
| `references/12-platform-deployment.md` | Self-hosted server, teams, security, CLI reference |

## Installation

```bash
pip install wandb
```

## Quick Reference

- [Docs](https://docs.wandb.ai) | [GitHub](https://github.com/wandb/wandb) | [PyPI](https://pypi.org/project/wandb/) | [Courses](https://www.wandb.courses)
