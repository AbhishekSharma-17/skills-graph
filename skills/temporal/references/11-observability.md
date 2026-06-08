# Temporal — Observability

> Source: [docs.temporal.io/develop/python/observability](https://docs.temporal.io/develop/python/observability)

## Table of Contents

- [Overview](#overview)
- [Logging](#logging)
- [Metrics](#metrics)
- [Distributed Tracing](#distributed-tracing)
- [Search Attributes & Visibility](#search-attributes--visibility)
- [Workflow History Inspection](#workflow-history-inspection)
- [Web UI](#web-ui)
- [Production Monitoring](#production-monitoring)

## Overview

Temporal provides four observability pillars:

| Pillar | Purpose | Setup Effort |
|--------|---------|-------------|
| **Logging** | Debug workflow/activity execution | Built-in |
| **Metrics** | Monitor performance and throughput | Prometheus config |
| **Tracing** | Visualize call graphs across workflows | OpenTelemetry |
| **Visibility** | Query and filter workflow executions | Search attributes |

## Logging

### Workflow Logging (Replay-Aware)

Use `workflow.logger` — it automatically suppresses duplicate logs during replay:

```python
from temporalio import workflow

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        workflow.logger.info("Processing order %s", input.order_id)

        result = await workflow.execute_activity(
            process_payment, input,
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info("Order %s completed: %s", input.order_id, result)
        return result
```

Never use `print()` or standard `logging` in workflows — they fire on every replay.

### Activity Logging

Activities can use standard Python logging:

```python
import logging

logger = logging.getLogger(__name__)

@activity.defn
async def process_payment(input: PaymentInput) -> str:
    info = activity.info()
    logger.info(
        "Processing payment",
        extra={
            "order_id": input.order_id,
            "workflow_id": info.workflow_id,
            "attempt": info.attempt,
            "activity_id": info.activity_id,
        },
    )
    ...
```

### Log Level Configuration

```python
import logging

# SDK core defaults to WARN
logging.basicConfig(level=logging.INFO)

# For verbose debugging
logging.getLogger("temporalio").setLevel(logging.DEBUG)
```

## Metrics

### Prometheus Setup

```python
from temporalio.runtime import Runtime, TelemetryConfig, PrometheusConfig

runtime = Runtime(
    telemetry=TelemetryConfig(
        metrics=PrometheusConfig(bind_address="0.0.0.0:9000")
    )
)

client = await Client.connect("localhost:7233", runtime=runtime)
```

Prometheus endpoint is now available at `http://localhost:9000/metrics`.

### Key Metrics to Monitor

| Metric | What It Tells You |
|--------|------------------|
| `temporal_workflow_task_execution_latency` | Workflow task processing time |
| `temporal_activity_execution_latency` | Activity execution time |
| `temporal_workflow_task_schedule_to_start_latency` | Queue wait time (worker capacity) |
| `temporal_activity_schedule_to_start_latency` | Activity queue wait time |
| `temporal_sticky_cache_hit` | Workflow cache efficiency |
| `temporal_workflow_completed` | Workflow completion count |
| `temporal_workflow_failed` | Workflow failure count |
| `temporal_workflow_canceled` | Workflow cancellation count |
| `temporal_workflow_task_replay_latency` | Replay performance |
| `temporal_long_request_failure` | gRPC connection issues |

### Grafana Dashboard

Use the official Temporal Grafana dashboards or build custom ones from the Prometheus metrics. Key panels to create:

- Workflow throughput (started, completed, failed per minute)
- Activity latency distributions (p50, p95, p99)
- Schedule-to-start latency (indicates worker scaling needs)
- Worker task slot utilization

## Distributed Tracing

### OpenTelemetry Setup

```bash
pip install temporalio[opentelemetry]
```

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from temporalio.contrib.opentelemetry import TracingInterceptor

# Configure OpenTelemetry
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
)
trace.set_tracer_provider(provider)

# Connect with tracing interceptor
client = await Client.connect(
    "localhost:7233",
    interceptors=[TracingInterceptor()],
)
```

The `TracingInterceptor` creates spans for:
- Client calls (start_workflow, signal, query)
- Workflow executions
- Activity executions
- Child workflow invocations

Traces are serialized through the Temporal Service, creating unified distributed traces across workflows, activities, and child workflows.

### Worker with Tracing

```python
worker = Worker(
    client,
    task_queue="traced-queue",
    workflows=[OrderWorkflow],
    activities=[process_payment],
    interceptors=[TracingInterceptor()],
)
```

## Search Attributes & Visibility

Search attributes allow querying and filtering workflow executions by custom fields.

### Defining Search Attribute Keys

```python
from temporalio.client import SearchAttributeKey

customer_id_key = SearchAttributeKey.for_keyword("CustomerId")
order_total_key = SearchAttributeKey.for_float("OrderTotal")
is_priority_key = SearchAttributeKey.for_bool("IsPriority")
region_key = SearchAttributeKey.for_keyword("Region")
created_at_key = SearchAttributeKey.for_datetime("CreatedAt")
tags_key = SearchAttributeKey.for_keyword_list("Tags")
```

### Setting Attributes at Workflow Start

```python
from temporalio.client import SearchAttributePair, TypedSearchAttributes

handle = await client.start_workflow(
    OrderWorkflow.run,
    order_input,
    id="order-123",
    task_queue="orders",
    search_attributes=TypedSearchAttributes([
        SearchAttributePair(customer_id_key, "cust-456"),
        SearchAttributePair(order_total_key, 99.99),
        SearchAttributePair(is_priority_key, True),
        SearchAttributePair(region_key, "us-east"),
    ]),
)
```

### Upserting Attributes Inside Workflows

```python
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, input: OrderInput) -> str:
        # Update search attributes as workflow progresses
        workflow.upsert_search_attributes([
            customer_id_key.value_set(input.customer_id),
            region_key.value_set(input.region),
        ])

        result = await workflow.execute_activity(...)

        # Update after processing
        workflow.upsert_search_attributes([
            order_total_key.value_set(result.total),
        ])

        return result
```

### Removing Attributes

```python
workflow.upsert_search_attributes([
    is_priority_key.value_unset(),
])
```

### Querying by Search Attributes

```python
# Find all priority orders in us-east
async for wf in client.list_workflows(
    'IsPriority=true AND Region="us-east"'
):
    print(f"Priority order: {wf.id}")

# Complex queries with time ranges
async for wf in client.list_workflows(
    'WorkflowType="OrderWorkflow" '
    'AND OrderTotal > 100 '
    'AND ExecutionStatus="Running" '
    'AND StartTime > "2026-01-01T00:00:00Z"'
):
    print(f"High-value running order: {wf.id}")
```

### Search Attribute Types

| Type | Python Constructor | Query Operators |
|------|-------------------|----------------|
| Keyword | `for_keyword()` | `=`, `!=`, `IN` |
| Text | `for_text()` | Full-text search |
| Int | `for_int()` | `=`, `>`, `<`, `>=`, `<=` |
| Float | `for_float()` | `=`, `>`, `<`, `>=`, `<=` |
| Bool | `for_bool()` | `=` |
| Datetime | `for_datetime()` | `=`, `>`, `<`, `>=`, `<=` |
| KeywordList | `for_keyword_list()` | `=`, `IN` |

## Workflow History Inspection

### Via CLI

```bash
# Show workflow history
temporal workflow show --workflow-id order-123

# JSON output for replay testing
temporal workflow show --workflow-id order-123 --output json

# Show running workflows
temporal workflow list --query 'ExecutionStatus="Running"'
```

### Via SDK

```python
desc = await handle.describe()
print(f"Status: {desc.status}")
print(f"History length: {desc.history_length}")
print(f"Start time: {desc.start_time}")
print(f"Search attributes: {desc.search_attributes}")
```

## Web UI

The Temporal Web UI (available at `http://localhost:8233` in development) provides:
- Workflow execution list with filtering
- Detailed event history timeline
- Real-time workflow state inspection
- Signal/query/update interaction
- Schedule management
- Worker status

## Production Monitoring

### Essential Alerts

```yaml
# High schedule-to-start latency (workers can't keep up)
- alert: TemporalHighQueueLatency
  expr: temporal_activity_schedule_to_start_latency_seconds{quantile="0.95"} > 30

# Elevated workflow failure rate
- alert: TemporalHighFailureRate
  expr: rate(temporal_workflow_failed_total[5m]) / rate(temporal_workflow_completed_total[5m]) > 0.05

# Worker not polling (process crash or network issue)
- alert: TemporalWorkerDown
  expr: rate(temporal_long_request[5m]) == 0
```

### Health Check Endpoint

```python
from aiohttp import web

async def health(request):
    try:
        await client.service_client.check_health()
        return web.Response(text="ok")
    except Exception as e:
        return web.Response(status=503, text=str(e))
```
