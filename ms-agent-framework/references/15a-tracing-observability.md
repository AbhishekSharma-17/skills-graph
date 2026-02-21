# Tracing & Observability — OpenTelemetry, Monitoring, Debugging

## Overview

The Microsoft Agent Framework provides built-in observability through OpenTelemetry (OTel) integration, following the GenAI Semantic Conventions standard. Three observability pillars enable comprehensive monitoring:

- **Traces**: Distributed tracing across agent execution, tool calls, and workflows
- **Metrics**: Quantitative measurements of agent behavior and performance
- **Logs**: Structured logging for debugging and audit trails

---

## OpenTelemetry Setup

### Minimal Configuration

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Configure trace exporter (OTLP over gRPC)
trace_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(trace_provider)

# Configure metrics exporter
metrics_reader = PeriodicExportingMetricReader(trace_exporter)
metrics_provider = MeterProvider(metric_readers=[metrics_reader])
metrics.set_meter_provider(metrics_provider)
```

### Production Configuration with Environment Variables

```python
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def configure_otel():
    """Configure OpenTelemetry from environment variables."""
    endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4317"
    )
    service_name = os.getenv("OTEL_SERVICE_NAME", "agent-framework-app")

    trace_exporter = OTLPSpanExporter(endpoint=endpoint)
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)

    return trace_provider

# Call in your application startup
tracer_provider = configure_otel()
```

---

## Automatic Spans

The Agent Framework automatically generates spans for key operations. These spans include semantic attributes following GenAI conventions.

### Span Types and Attributes

| Span Name | Parent | Attributes | Use Case |
|-----------|--------|-----------|----------|
| `invoke_agent` | None (root) | `agent.name`, `session.id`, `user.id` | Agent invocation entry point |
| `agent.chat` | `invoke_agent` | `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` | LLM chat completion |
| `agent.execute_tool` | `invoke_agent` | `tool.name`, `tool.parameters`, `tool.error` | Tool execution |
| `workflow.execute` | `invoke_agent` | `workflow.name`, `executor.name`, `workflow.status` | Workflow execution |
| `middleware.execute` | Parent operation | `middleware.name`, `middleware.duration_ms` | Middleware processing |

### Example: Inspecting Auto-Generated Spans

```python
from agent_framework import ChatAgent
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

agent = ChatAgent(name="DataAnalyzer", chat_client=client)

with tracer.start_as_current_span("my_application") as span:
    result = agent.invoke(
        "Analyze this data for trends",
        context={"data": sales_data}
    )
    # Child spans auto-generated:
    # - invoke_agent (agent.name="DataAnalyzer")
    #   - agent.chat (gen_ai.request.model="gpt-4")
    #   - agent.execute_tool (tool.name="sql_query")
```

---

## GenAI Semantic Conventions

The Agent Framework uses the OpenTelemetry GenAI Semantic Conventions to standardize attributes across AI operations.

### Core Attributes

```python
# These attributes are automatically added to relevant spans
{
    # LLM Request/Response
    "gen_ai.operation.name": "chat",
    "gen_ai.request.model": "gpt-4-turbo",
    "gen_ai.request.max_tokens": 2048,
    "gen_ai.request.temperature": 0.7,
    "gen_ai.request.top_p": 0.9,

    # LLM Response
    "gen_ai.response.finish_reason": "stop",  # or "length", "tool_calls", "error"
    "gen_ai.response.model": "gpt-4-turbo",

    # Token Usage
    "gen_ai.usage.input_tokens": 150,
    "gen_ai.usage.output_tokens": 42,
    "gen_ai.usage.completion_tokens": 42,

    # Server/Endpoint
    "server.address": "api.openai.com",
    "server.port": 443,
    "server.socket.domain": "api.openai.com",
}
```

### Accessing Span Attributes Programmatically

```python
from opentelemetry import trace

def inspect_span_attributes():
    """Access current span attributes for debugging."""
    span = trace.get_current_span()

    if span and hasattr(span, 'attributes'):
        print(f"Model: {span.attributes.get('gen_ai.request.model')}")
        print(f"Input tokens: {span.attributes.get('gen_ai.usage.input_tokens')}")
        print(f"Output tokens: {span.attributes.get('gen_ai.usage.output_tokens')}")
```

---

## Environment Variables for Instrumentation

Configure OpenTelemetry behavior without code changes using these environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP backend endpoint | `http://localhost:4317` |
| `OTEL_SERVICE_NAME` | Service identifier in traces | `my-agent-app` |
| `OTEL_TRACES_EXPORTER` | Trace exporter type | `otlp` |
| `OTEL_METRICS_EXPORTER` | Metrics exporter type | `otlp` |
| `OTEL_LOGS_EXPORTER` | Logs exporter type | `otlp` |
| `OTEL_PROPAGATORS` | Trace context propagation | `tracecontext,baggage` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Azure Monitor connection | (see Azure section) |
| `OTEL_SDK_DISABLED` | Disable OTel entirely | `false` |

### Example: Set via Python

```python
import os

os.environ["OTEL_SERVICE_NAME"] = "advanced-agent-system"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://otel-collector:4317"
os.environ["OTEL_PROPAGATORS"] = "tracecontext,baggage"
```

---

## Azure Monitor Integration

Integrate with Azure Monitor for enterprise observability and compliance.

### Setup

```python
import os
from azure.monitor.opentelemetry import configure_azure_monitor

# Configure Azure Monitor (reads APPLICATIONINSIGHTS_CONNECTION_STRING)
configure_azure_monitor(
    connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
)

# After this, all traces/metrics/logs flow to Application Insights
```

### Alternative: Explicit Configuration

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

exporter = AzureMonitorTraceExporter(
    connection_string="InstrumentationKey=...;IngestionEndpoint=..."
)

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
```

### Querying Traces in Azure Monitor

**Kusto Query Language (KQL) for Application Insights:**

```kusto
// Find all agent invocations in the last hour
traces
| where customDimensions.["agent.name"] == "DataAnalyzer"
| where timestamp > ago(1h)
| summarize
    Count=count(),
    AvgDuration=avg(customDimensions.["duration_ms"]),
    ErrorRate=100.0*sum(iif(customDimensions.["error"] != "", 1, 0))/count()
    by customDimensions.["session.id"]
```

```kusto
// Monitor token usage by model
customMetrics
| where name == "gen_ai.usage.input_tokens" or name == "gen_ai.usage.output_tokens"
| extend model=tostring(customDimensions.["gen_ai.request.model"])
| summarize
    TotalInputTokens=sum(value[iif(name == "gen_ai.usage.input_tokens", 1, 0)]),
    TotalOutputTokens=sum(value[iif(name == "gen_ai.usage.output_tokens", 1, 0)])
    by model, bin(timestamp, 5m)
```

### Creating Dashboards

```python
# Example: Dashboard as code using Azure Monitor workbooks
# Typically done via Azure Portal or ARM templates, but can be automated

from azure.identity import DefaultAzureCredential
from azure.mgmt.applicationinsights import ApplicationInsightsManagementClient

credential = DefaultAzureCredential()
client = ApplicationInsightsManagementClient(credential, subscription_id)

# Create workbook with traces and metrics visualization
workbook_template = {
    "version": "Notebook/1.0",
    "isLocked": False,
    "items": [
        {
            "type": "query",
            "title": "Agent Invocations Over Time",
            "queries": [
                {
                    "query": "traces | where customDimensions.[\"span.name\"] == \"invoke_agent\" | summarize count() by bin(timestamp, 5m)"
                }
            ]
        }
    ]
}
```

---

## Aspire Dashboard (Local Development)

Use Aspire Dashboard for convenient local development observability without external backends.

### Docker Setup

```bash
# Start Aspire Dashboard container
docker run --rm -d \
  --name aspire-dashboard \
  -p 18888:18888 \
  -p 4317:4317 \
  mcr.microsoft.com/dotnet/nightly/aspire-dashboard:latest

# Access at http://localhost:18888
```

### Configure Agent to Send to Aspire

```python
import os

os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4317"
os.environ["OTEL_SERVICE_NAME"] = "my-agent-app"

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
```

### What Aspire Dashboard Shows

- **Traces**: Full distributed traces with timeline visualization
- **Metrics**: Real-time graphs of span duration, throughput, error rates
- **Logs**: Structured logs with filtering and search
- **Structure Map**: Service topology and dependencies
- **Resources**: Memory, CPU, and other runtime metrics

---

## DevUI — Visual Agent Debugger

The DevUI provides a web-based interface for debugging agent execution in real-time.

### Basic Usage

```python
from agent_framework.devui import serve
from agent_framework import ChatAgent

agent = ChatAgent(name="MyAgent", chat_client=client)

# Start DevUI server (default port 8000)
serve(entities=[agent], tracing_enabled=True)

# Access at http://localhost:8000
```

### Advanced Configuration

```python
from agent_framework.devui import serve, DevUIConfig

config = DevUIConfig(
    host="0.0.0.0",
    port=8080,
    enable_tracing=True,
    max_history=1000,  # Keep last 1000 conversations
    export_format="otlp",
)

serve(entities=[agent_list], config=config)
```

### DevUI Features

| Feature | Purpose | Example |
|---------|---------|---------|
| **Conversation Viewer** | View full conversation history with messages and responses | See agent decisions in real-time |
| **Tool Call Inspector** | Inspect parameters and results of each tool execution | Debug tool integration issues |
| **Streaming Visualization** | Watch token streaming in real-time | Verify streaming behavior |
| **Middleware Timeline** | See execution order and duration of middleware | Optimize middleware performance |
| **Error Inspector** | Detailed error information with stack traces | Rapid debugging |
| **Token Accounting** | View input/output tokens per request | Monitor token usage |

### Command Line Usage

```bash
# Start DevUI for agents in ./agents directory
devui ./agents --tracing

# Specify port
devui ./agents --port 9000

# Export all conversations to JSONL on shutdown
devui ./agents --export conversations.jsonl
```

---

## Metrics

The Agent Framework exports standardized metrics following the GenAI Semantic Conventions.

### Available Metrics

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# These are automatically recorded by the Agent Framework:

# 1. LLM Operation Duration
# Metric: gen_ai.client.operation.duration
# Unit: milliseconds
# Attributes: gen_ai.request.model, gen_ai.response.finish_reason

# 2. Token Usage
# Metric: gen_ai.client.token.usage
# Unit: tokens
# Attributes: gen_ai.usage.input_tokens, gen_ai.usage.output_tokens, gen_ai.request.model

# 3. Agent Function Invocation Duration
# Metric: agent_framework.function.invocation.duration
# Unit: milliseconds
# Attributes: function.name, function.status

# 4. Tool Execution Duration
# Metric: agent_framework.tool.execution.duration
# Unit: milliseconds
# Attributes: tool.name, tool.status
```

### Recording Custom Metrics

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Create a histogram for custom operation timing
operation_timer = meter.create_histogram(
    name="custom.operation.duration",
    unit="ms",
    description="Duration of custom operations"
)

# Record metric
import time
start = time.time()
# ... do work ...
duration_ms = (time.time() - start) * 1000
operation_timer.record(duration_ms, attributes={"operation.type": "data_processing"})
```

### Querying Metrics in Azure Monitor

```kusto
// Average LLM response time by model
customMetrics
| where name == "gen_ai.client.operation.duration"
| extend model=tostring(customDimensions.["gen_ai.request.model"])
| summarize AvgResponseTime=avg(value) by model, bin(timestamp, 5m)
| render timechart
```

---

## Custom Instrumentation

Add custom spans, metrics, and logging for domain-specific operations.

### Custom Spans

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_large_dataset(data):
    """Process data with custom instrumentation."""
    with tracer.start_as_current_span("process_dataset") as span:
        span.set_attribute("dataset.size", len(data))

        # Processing steps
        with tracer.start_as_current_span("data_validation") as validation_span:
            # Validate data
            validation_span.set_attribute("validation.passed", True)

        with tracer.start_as_current_span("data_aggregation") as agg_span:
            # Aggregate results
            result = aggregate(data)
            agg_span.set_attribute("result.size", len(result))

        return result
```

### Custom Middleware for Instrumentation

```python
from agent_framework import Middleware
from opentelemetry import trace, metrics

class InstrumentationMiddleware(Middleware):
    """Custom middleware for detailed instrumentation."""

    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        self.request_counter = self.meter.create_counter(
            "custom.request.count",
            description="Number of agent requests"
        )

    async def on_invoke(self, agent_state):
        """Track before agent invocation."""
        self.request_counter.add(1, attributes={"agent.name": agent_state.agent.name})

        with self.tracer.start_as_current_span("custom_preprocessing") as span:
            span.set_attribute("input.message_length", len(agent_state.message))
            # Preprocessing logic

    async def on_chat(self, agent_state):
        """Track chat operation."""
        with self.tracer.start_as_current_span("custom_chat_processing") as span:
            span.set_attribute("token_budget", agent_state.token_limit)

    async def on_error(self, agent_state, error):
        """Track errors."""
        span = trace.get_current_span()
        span.set_attribute("error.type", type(error).__name__)
        span.set_attribute("error.message", str(error))
```

### Structured Logging

```python
import logging
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Enable automatic logging instrumentation
LoggingInstrumentor().instrument()

# Configure structured logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "trace_id": "%(trace_id)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Log with context
logger.info("Agent processing started", extra={
    "agent.name": "MyAgent",
    "session.id": session_id
})
```

---

## Workflow-Level Tracing

Trace complex workflows that involve multiple agents and executors.

### Span Hierarchy

```
invoke_agent (root span)
├── agent.chat (invoke OpenAI)
├── agent.execute_tool (run tool)
│   ├── tool.execution (tool-specific span)
│   └── tool.post_processing
├── workflow.execute (if part of workflow)
│   ├── executor.execute (first executor)
│   │   ├── agent.chat
│   │   └── agent.execute_tool
│   └── executor.execute (second executor)
│       ├── agent.chat
│       └── agent.execute_tool
└── middleware.execute (post-processing)
```

### Tracing Workflow Execution

```python
from agent_framework import Workflow, Executor
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class AnalysisWorkflow(Workflow):
    def __init__(self):
        self.data_agent = ChatAgent(name="DataAgent", chat_client=client)
        self.summary_agent = ChatAgent(name="SummaryAgent", chat_client=client)

    async def execute(self, input_data):
        with tracer.start_as_current_span("analysis_workflow") as span:
            span.set_attribute("workflow.type", "analysis")

            # First executor: data analysis
            with tracer.start_as_current_span("data_analysis_executor") as exec_span:
                exec_span.set_attribute("executor.index", 0)
                analysis_result = await self.data_agent.invoke(
                    f"Analyze: {input_data}"
                )

            # Second executor: summarization
            with tracer.start_as_current_span("summary_executor") as exec_span:
                exec_span.set_attribute("executor.index", 1)
                summary = await self.summary_agent.invoke(
                    f"Summarize: {analysis_result}"
                )

            return summary
```

### Querying Workflow Traces

```kusto
// Find slow workflow executions
traces
| where customDimensions.["span.name"] == "workflow.execute"
| where customDimensions.["duration_ms"] > 5000
| project
    timestamp,
    workflow=customDimensions.["workflow.name"],
    duration=customDimensions.["duration_ms"],
    status=customDimensions.["workflow.status"]
| order by duration desc
```

---

## Production Observability Stack

Recommended architecture for production deployments:

```
┌─────────────────────────────────────────┐
│    Agent Framework Application          │
│  (with OTel SDK configured)             │
└─────────────┬───────────────────────────┘
              │ traces, metrics, logs
              │
┌─────────────▼───────────────────────────┐
│    OpenTelemetry Collector              │
│  (processes, batches, transforms)       │
└─────────────┬───────────────────────────┘
              │
     ┌────────┴────────┬──────────────┐
     │                 │              │
┌────▼──────┐  ┌──────▼────┐  ┌─────▼──────┐
│   Azure    │  │  Azure    │  │   Custom   │
│  Monitor   │  │   Logs    │  │  Metrics   │
│ (Traces)   │  │ (Logs)    │  │  Service   │
└────┬──────┘  └──────┬────┘  └─────┬──────┘
     │                │              │
     │          ┌──────▼────────┐    │
     │          │   Log         │    │
     │          │  Analytics    │    │
     │          │  (Kusto)      │    │
     │          └───────────────┘    │
     │                                │
     └────────┬───────────────────────┘
              │
         ┌────▼─────────┐
         │  Dashboards  │
         │  & Alerts    │
         └──────────────┘
```

### Docker Compose for Local Stack

```yaml
version: '3.8'
services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    ports:
      - "4317:4317"
      - "4318:4318"
      - "8888:8888"
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    command: --config=/etc/otel-collector-config.yaml

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yaml:/etc/prometheus/prometheus.yaml
    command:
      - --config.file=/etc/prometheus/prometheus.yaml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
```

---

## Debugging Tips Checklist

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| No traces appearing | Check OTLP endpoint connectivity | Verify `OTEL_EXPORTER_OTLP_ENDPOINT` points to running collector |
| Missing span attributes | Spans not enriched with metadata | Add `span.set_attribute()` calls in custom code |
| High latency in traces | Trace export is blocking | Use `BatchSpanProcessor` instead of `SimpleSpanProcessor` |
| Token counts incorrect | Wrong attributes set | Verify `gen_ai.usage.input_tokens` attribute is set |
| DevUI not showing conversations | DevUI not receiving data | Ensure agent is invoked with DevUI enabled |
| Memory usage growing | Span processors not flushing | Call `tracer_provider.force_flush()` before shutdown |
| Traces lost on exit | Processor not flushed | Implement graceful shutdown: `tracer_provider.force_flush(timeout_millis=5000)` |

### Debugging Commands

```bash
# Check OTLP collector is reachable
grpcurl -plaintext localhost:4317 list

# Monitor metrics in Prometheus
curl http://localhost:9090/api/v1/targets

# Force flush traces (in Python)
python -c "from opentelemetry import trace; trace.get_tracer_provider().force_flush()"

# View logs in real-time (if using file exporter)
tail -f agent-framework-traces.jsonl | jq .
```

---

## Summary

The Agent Framework's observability stack provides:

1. **Automatic instrumentation** of all core operations
2. **Standards-based** OpenTelemetry integration
3. **Enterprise support** via Azure Monitor integration
4. **Developer experience** through DevUI and Aspire Dashboard
5. **Production-ready** distributed tracing and metrics
6. **Customization** through middleware and custom spans

Use these tools to build transparent, debuggable, and compliant AI agents.
