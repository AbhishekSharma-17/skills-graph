# Analytics & Dashboards

> Source: [langfuse.com/docs/analytics/overview](https://langfuse.com/docs/analytics/overview)

## Table of Contents

- [Overview](#overview)
- [Default Dashboard](#default-dashboard)
- [Custom Dashboards](#custom-dashboards)
- [Cost Tracking](#cost-tracking)
- [Latency Monitoring](#latency-monitoring)
- [Token Usage](#token-usage)
- [Quality Metrics](#quality-metrics)
- [Segmentation Dimensions](#segmentation-dimensions)
- [Metrics API](#metrics-api)
- [Third-Party Exports](#third-party-exports)
- [Common Patterns](#common-patterns)

---

## Overview

Langfuse analytics derives insights from observability traces and evaluation scores. Metrics include cost, latency, token usage, quality scores, and volume — all filterable by user, model, prompt version, feature, and custom tags.

## Default Dashboard

The built-in dashboard shows:

- **Trace volume** — requests over time
- **Cost** — total and per-model breakdown
- **Latency** — P50, P90, P95 response times
- **Token usage** — input/output tokens over time
- **Quality scores** — average scores over time
- **Model usage** — distribution across models
- **Error rate** — failed traces percentage

All widgets support time range selection (1h, 24h, 7d, 30d, custom).

## Custom Dashboards

Create custom dashboards with widgets tailored to your needs:

1. Go to **Analytics** > **Dashboards**
2. Click **New Dashboard**
3. Add widgets:
   - **Time series** — metrics over time
   - **Table** — grouped aggregations
   - **Number** — single metric KPIs
4. Configure filters per widget

### Widget Types

| Widget | Metrics | Use Case |
|--------|---------|----------|
| Time series | Cost, latency, tokens, scores, volume | Trend analysis |
| Table | Grouped by model, user, trace name | Top-N analysis |
| Number | Sum, average, count, P50/P90/P95 | KPI monitoring |

### Filters

Every widget supports:
- Time range
- Trace name (use case / feature)
- Model
- User ID
- Tags
- Metadata keys (top-level keys are filterable)
- Score names
- Release / version
- Environment

## Cost Tracking

### Automatic Cost Calculation

Langfuse maintains a model cost registry. When you log token usage, cost is calculated automatically for supported models:

```python
generation.update(
    model="gpt-4o",
    usage={"input": 500, "output": 200},
)
# Cost auto-calculated based on gpt-4o pricing
```

### Custom Model Costs

For custom or self-hosted models:

```python
generation.update(
    model="my-fine-tuned-model",
    usage={"input": 500, "output": 200},
    usage_details={
        "input_cost": 0.0015,   # Total cost in USD
        "output_cost": 0.002,
    },
)
```

### Cost Dashboard Views

- **Total cost** over time
- **Cost per model** — which models consume the most budget
- **Cost per user** — identify high-usage users
- **Cost per feature** — which features are most expensive
- **Cost per prompt version** — measure the cost impact of prompt changes

## Latency Monitoring

### Tracked Latencies

| Metric | Description |
|--------|-------------|
| End-to-end | Trace start to trace end |
| LLM latency | Generation start to end |
| Time-to-first-token | For streaming responses |
| Non-LLM overhead | Total - LLM = your code's overhead |

### Percentile Breakdown

Dashboard shows P50, P90, P95, P99 latency:
- P50: median user experience
- P90: tail latency
- P95/P99: worst-case scenarios

### Latency Filters

Filter latency by:
- Model (compare GPT-4o vs Claude 3.5 Sonnet)
- Trace name (compare API endpoints)
- Time period (detect regressions after deploys)

## Token Usage

Track input and output tokens across:
- Models
- Features / trace names
- Users
- Prompt versions
- Time periods

Dashboard widgets:
- Total tokens over time (input vs output)
- Average tokens per request
- Token usage by model
- Token usage by feature

## Quality Metrics

Aggregate evaluation scores across dimensions:

- **Average score** per trace name
- **Score distribution** — histogram of score values
- **Score trends** — quality over time
- **Score by model** — which model produces better results
- **Score by prompt version** — which prompt performs best

### Score Aggregation

```
Quality = AVG(score) WHERE score.name = "quality"
Relevance P90 = PERCENTILE(score, 0.9) WHERE score.name = "relevance"
Hallucination Rate = COUNT(score = 0) / COUNT(*) WHERE score.name = "factual"
```

## Segmentation Dimensions

All analytics can be sliced by:

| Dimension | Example Values |
|-----------|---------------|
| `trace.name` | "chat-api", "rag-pipeline", "agent-run" |
| `model` | "gpt-4o", "claude-3.5-sonnet" |
| `user_id` | Individual user metrics |
| `session_id` | Session-level aggregates |
| `tags` | "production", "experiment-a" |
| `metadata.*` | Top-level metadata keys |
| `release` | "v2.0.1", "v2.1.0" |
| `prompt.name` | "qa-prompt", "chat-system" |
| `prompt.version` | Version numbers |

## Metrics API

Access analytics programmatically:

```python
# Fetch daily metrics
metrics = langfuse.api.metrics.daily(
    trace_name="chat-api",
    from_timestamp="2026-03-01T00:00:00Z",
    to_timestamp="2026-03-29T00:00:00Z",
)

for day in metrics:
    print(f"{day.date}: cost=${day.total_cost:.4f}, traces={day.count}")
```

## Third-Party Exports

### PostHog

Export Langfuse metrics to PostHog for product analytics:

```python
# Configure in Langfuse settings
# Settings > Integrations > PostHog
# Provide PostHog API key and host
```

Exported data: trace volume, cost, latency, scores — correlated with PostHog user events.

### Mixpanel

Similar export capability for Mixpanel analytics.

### Custom Webhook

Set up webhooks to receive trace events for custom processing:
- Trigger on new traces, scores, or specific events
- Send to your data warehouse, alerting system, or custom pipeline

## Common Patterns

### Cost Budgeting

Monitor daily/weekly cost and set up alerts:

```python
# Daily cost check
metrics = langfuse.api.metrics.daily(
    from_timestamp=today_start,
    to_timestamp=now,
)
daily_cost = sum(m.total_cost for m in metrics)
if daily_cost > budget_threshold:
    alert(f"Cost budget exceeded: ${daily_cost:.2f}")
```

### Release Comparison

Compare metrics before and after a deployment:

```python
# Filter by release to compare
# Release "v2.0" vs "v2.1" in the dashboard
# Look at: latency, cost, quality scores
```

### Model Migration

Track the impact of switching models:

```python
# Tag traces with the model being tested
trace = langfuse.trace(
    name="chat",
    tags=["model-migration", "claude-3.5-sonnet"],
    metadata={"migration_phase": "canary"},
)
# Compare metrics across model tags in the dashboard
```
