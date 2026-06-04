# Reports & Automations

> Source: [docs.wandb.ai/models/reports](https://docs.wandb.ai/models/reports/) | [docs.wandb.ai/models/automations](https://docs.wandb.ai/models/automations/) | wandb 0.27.1

## Table of Contents

- [Reports Overview](#reports-overview)
- [Creating Reports](#creating-reports)
- [Report Content](#report-content)
- [Sharing and Exporting](#sharing-and-exporting)
- [Programmatic Reports](#programmatic-reports)
- [Automations Overview](#automations-overview)
- [Events and Triggers](#events-and-triggers)
- [Actions](#actions)
- [Setting Up Webhooks](#setting-up-webhooks)
- [Setting Up Slack Notifications](#setting-up-slack-notifications)
- [Common Automation Patterns](#common-automation-patterns)

## Reports Overview

W&B Reports are collaborative documents for organizing experiment results, embedding live visualizations, and sharing findings with team members. They combine narrative text with auto-updating panels from your W&B workspace.

## Creating Reports

### Via UI

1. Navigate to your project workspace
2. Click **Create report** in the upper right
3. Select charts and panels to include
4. Click **Create report**
5. Add text, headings, and code blocks
6. Click **Publish to project**

### From a Workspace

Select specific panels, runs, or views in your workspace, then click "Add to report" to embed them.

## Report Content

Reports support:

- **Markdown text** — headings, lists, code blocks, links
- **Run panels** — line plots, scatter plots, bar charts, parallel coordinates
- **Media panels** — image galleries, audio players, 3D viewers
- **Tables** — interactive data tables from logged `wandb.Table` objects
- **Custom Vega charts** — custom visualizations using Vega-Lite specs
- **Code blocks** — syntax-highlighted code with language detection
- **LaTeX** — mathematical notation inline and block
- **Run selectors** — filter which runs appear in embedded panels

### Panel Types

| Panel | Description |
|-------|-------------|
| Line Plot | Metrics over time (loss curves, accuracy) |
| Scatter Plot | Two metrics against each other |
| Bar Chart | Compare final metric values across runs |
| Parallel Coordinates | Multi-dimensional hyperparameter visualization |
| Run Table | Sortable, filterable list of runs |
| Media Panel | Images, audio, video from runs |
| Custom Chart | Vega-Lite specification |
| Code | Query panel with W&B query language |

## Sharing and Exporting

| Action | How |
|--------|-----|
| Share with team | Click **Share** → add collaborators |
| Public link | Set visibility to public in share dialog |
| Export PDF | Report menu → Download as PDF |
| Export LaTeX | Report menu → Download as LaTeX zip |
| Embed | Use the report URL in iframes |
| Clone | Duplicate to create a variant |

## Programmatic Reports

```python
import wandb
from wandb_workspaces import reports as wr

report = wr.Report(
    project="my-project",
    title="Training Results Q2 2026",
    description="Comparison of model architectures",
)

# Add blocks
report.blocks = [
    wr.H1("Model Comparison"),
    wr.P("This report compares ResNet and EfficientNet architectures."),
    wr.PanelGrid(
        panels=[
            wr.LinePlot(x="epoch", y=["val/accuracy"]),
            wr.BarPlot(metrics=["val/accuracy"]),
        ],
        runsets=[wr.RunSet(project="my-project", filters={"tags": "final"})],
    ),
]

report.save()
url = report.url
```

Requires: `pip install wandb-workspaces`

## Automations Overview

W&B Automations trigger actions when events occur, following the pattern:

```
Event → (Optional) Condition → Action
```

Automations can be created at two scopes:
- **Project automations** — react to run events within a project
- **Registry automations** — react to artifact events in the registry

## Events and Triggers

### Project Events

| Event | Description |
|-------|-------------|
| Run finishes | A run completes (success or failure) |
| Run fails | A run exits with an error |
| Run metric change | A logged metric crosses a threshold |
| Run metric z-score | A metric deviates from the population mean |
| New artifact version | A new artifact version is logged |
| Alias added | An alias is assigned to an artifact |

### Registry Events

| Event | Description |
|-------|-------------|
| New version linked | An artifact version is linked to a collection |
| Alias added | An alias is added to a registry version |

### Conditions (Filters)

Narrow when automations fire:

```
Event: Run finishes
Condition: run.config.model == "resnet50" AND run.summary.val_accuracy > 0.95
Action: Send Slack notification
```

## Actions

### Slack Notification

Sends a formatted message to a Slack channel with event details and links back to W&B.

### Webhook

Sends a JSON POST request to an external URL with event payload.

Webhook payload example:

```json
{
  "event_type": "run_finished",
  "event_author": "user@example.com",
  "project": "entity/project",
  "run_id": "abc123",
  "run_name": "golden-sunset-42",
  "run_url": "https://wandb.ai/entity/project/runs/abc123",
  "run_summary": {
    "val/accuracy": 0.95,
    "val/loss": 0.12
  },
  "run_config": {
    "model": "resnet50",
    "lr": 0.001
  }
}
```

## Setting Up Webhooks

1. **Add secret** — Team Settings → Secrets → add your webhook auth token
2. **Create webhook** — Team Settings → Webhooks → add URL and select secret
3. **Create automation** — Project → Automations → New → select event and webhook

### Testing Webhooks

Use the Test button in Team Settings → Webhooks to send a sample payload.

## Setting Up Slack Notifications

1. **Install W&B Slack app** — Team Settings → Notifications → Connect to Slack
2. **Select channel** — choose which Slack channel receives notifications
3. **Create automation** — Project → Automations → New → select event and Slack action

## Common Automation Patterns

### Alert on Training Failure

```
Event:     Run fails
Condition: (none — all failures)
Action:    Slack notification to #ml-alerts
```

### Deploy on Model Promotion

```
Event:     Alias "production" added (Registry)
Condition: (none)
Action:    Webhook to deployment service
```

### Alert on Metric Regression

```
Event:     Run finishes
Condition: run.summary.val_accuracy < 0.90
Action:    Slack notification to #ml-team
```

### NaN Detection

```
Event:     Run metric change
Condition: loss == NaN
Action:    Slack notification + Webhook to auto-stop
```

### Quality Gate for Registry

```
Event:     New version linked to "production-models/text-classifier"
Condition: (none)
Action:    Webhook to CI/CD pipeline for automated testing
```

## Related

- Artifacts → `references/05-artifacts.md`
- Registry → `references/06-registry.md`
- Platform & Deployment → `references/12-platform-deployment.md`
