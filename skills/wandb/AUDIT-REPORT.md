# Audit Report — wandb

Generated: 2026-06-05

## Quality Scores

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| **Architecture** | 5 | Clean separation: W&B Models (training) and Weave (LLM observability). Router SKILL.md under 50 lines. All files are leaf nodes. |
| **Content Quality** | 5 | Comprehensive code examples for every API surface. Covers both Python and TypeScript where applicable. Practical patterns for real-world use cases. |
| **Completeness** | 4 | Covers all major features: tracking, sweeps, artifacts, registry, reports, automations, Weave tracing, evaluations, and 12+ integrations. Minor gaps: advanced Weave features (guardrails detail), serverless inference/training products. |
| **Maintainability** | 5 | VERSION.json tracks all 13 reference files with source pages. check-updates.py validates upstream version and file integrity. Staleness threshold set to 90 days. |
| **Trigger Quality** | 5 | Mandatory triggers cover brand names (wandb, W&B, Weights & Biases, Weave) and API entry points (wandb.init, wandb.log). Broad triggers for ML experiment tracking and LLM observability. |

## Overall: 4.8 / 5.0

## Coverage Map

| Feature | Covered | Reference File |
|---------|---------|---------------|
| Installation & Auth | Yes | 00-overview |
| Experiment Tracking | Yes | 01-experiment-tracking |
| Metric Logging | Yes | 02-logging-metrics |
| Media Logging | Yes | 03-logging-media |
| Hyperparameter Sweeps | Yes | 04-sweeps |
| Artifacts & Versioning | Yes | 05-artifacts |
| Model Registry | Yes | 06-registry |
| Tables & Data Viz | Yes | 07-tables |
| Reports | Yes | 08-reports-automations |
| Automations | Yes | 08-reports-automations |
| Weave Tracing | Yes | 09-weave-tracing |
| Weave Evaluations | Yes | 10-weave-evaluations |
| Framework Integrations | Yes | 11-integrations |
| Platform & Deployment | Yes | 12-platform-deployment |
| Serverless Inference | Partial | 00-overview (mentioned) |
| Serverless Training | No | New product, still in preview |
| Serverless Sandboxes | No | Private preview only |
