# Observability in Workflows — Monitoring, Tracing, Debugging

## Overview

Workflow observability provides visibility into execution, performance, and errors. The framework provides built-in monitoring, event streaming, OpenTelemetry integration, and DevUI for debugging.

## executor_io_observation Pattern

Monitor executor inputs and outputs in real-time.

### Basic Monitoring

```python
from agent_framework.workflows import Workflow, Executor, handler, WorkflowContext
import logging
import json

logger = logging.getLogger(__name__)

async def monitor_executor_io(workflow: Workflow, input_data):
    """Log all executor inputs and outputs."""
    io_log = []

    async for event in workflow.run_stream(input_data):
        if event.type == "output":
            entry = {
                "executor": event.executor_id,
                "input_type": event.input_type,
                "output": event.data,
                "timestamp": event.timestamp,
            }
            io_log.append(entry)
            logger.info(f"[{event.executor_id}] Output: {event.data}")

    return io_log
```

### Structured IO Logging

```python
import json
from datetime import datetime
from pathlib import Path

class ExecutorIOMonitor:
    """Track all executor inputs/outputs to file."""

    def __init__(self, log_file: str = "executor_io.jsonl"):
        self.log_file = Path(log_file)

    async def monitor_workflow(self, workflow, input_data):
        """Run workflow with IO monitoring."""
        with open(self.log_file, "a") as f:
            async for event in workflow.run_stream(input_data):
                if event.type == "output":
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "executor_id": event.executor_id,
                        "event_type": event.type,
                        "data": json.dumps(event.data, default=str),
                    }
                    f.write(json.dumps(log_entry) + "\n")
```

### Executor Wrapper for IO Monitoring

```python
class ObservableExecutor(Executor):
    """Wrapper that monitors another executor's IO."""

    def __init__(self, wrapped: Executor, io_logger: ExecutorIOMonitor):
        super().__init__(id=f"observable_{wrapped.id}")
        self.wrapped = wrapped
        self.logger = io_logger

    @handler
    async def process(self, data, ctx: WorkflowContext) -> None:
        # Log input
        input_log = {
            "executor": self.wrapped.id,
            "direction": "input",
            "data": data,
            "type": type(data).__name__,
        }
        logger.info(f"Input to {self.wrapped.id}: {input_log}")

        # Execute
        await self.wrapped.run(data, ctx)

        # Output is logged by stream listener
```

## Event-Based Monitoring with run_stream

Stream all workflow events for real-time monitoring:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class WorkflowMetrics:
    executor_count: int = 0
    output_count: int = 0
    error_count: int = 0
    request_info_count: int = 0
    events: List = None

    def __post_init__(self):
        if self.events is None:
            self.events = []

async def collect_workflow_metrics(workflow, input_data) -> WorkflowMetrics:
    """Collect metrics from workflow execution."""
    metrics = WorkflowMetrics()

    async for event in workflow.run_stream(input_data):
        metrics.events.append({
            "type": event.type,
            "executor": getattr(event, "executor_id", None),
            "timestamp": datetime.utcnow().isoformat(),
        })

        if event.type == "output":
            metrics.output_count += 1
            metrics.executor_count = len(set(e["executor"] for e in metrics.events if e["executor"]))
        elif event.type == "error":
            metrics.error_count += 1
        elif event.type == "request_info":
            metrics.request_info_count += 1

    return metrics

# Usage
metrics = await collect_workflow_metrics(workflow, "input data")
print(f"Outputs: {metrics.output_count}, Errors: {metrics.error_count}")
```

### Processing Event Stream

```python
async def process_events_with_callbacks(workflow, input_data, callbacks: dict):
    """Process events with callback handlers."""
    async for event in workflow.run_stream(input_data):
        handler = callbacks.get(event.type)
        if handler:
            await handler(event)

# Define callbacks
callbacks = {
    "output": lambda e: print(f"Output from {e.executor_id}: {e.data}"),
    "error": lambda e: print(f"Error in {e.executor_id}: {e.data}"),
    "request_info": lambda e: print(f"Request from {e.executor_id}: {e.data}"),
}

await process_events_with_callbacks(workflow, data, callbacks)
```

## ObservableExecutor Wrapper with Timing

Add timing information to executor monitoring:

```python
import time
from typing import Optional

class TimedObservableExecutor(Executor):
    """Executor wrapper with timing and detailed logging."""

    def __init__(self, wrapped: Executor):
        super().__init__(id=f"timed_{wrapped.id}")
        self.wrapped = wrapped
        self.execution_times = []

    @handler
    async def process(self, data, ctx: WorkflowContext) -> None:
        start_time = time.perf_counter()
        input_size = len(str(data))

        logger.info(f"[{self.wrapped.id}] START | Input size: {input_size} bytes")

        try:
            await self.wrapped.run(data, ctx)
            elapsed = time.perf_counter() - start_time
            self.execution_times.append(elapsed)

            logger.info(f"[{self.wrapped.id}] COMPLETE | Duration: {elapsed:.3f}s")

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"[{self.wrapped.id}] ERROR | Duration: {elapsed:.3f}s | {e}")
            raise

    def get_average_execution_time(self) -> Optional[float]:
        """Get average execution time."""
        return sum(self.execution_times) / len(self.execution_times) if self.execution_times else None
```

## OpenTelemetry Integration for Workflows

Export workflow traces to OpenTelemetry:

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Configure OpenTelemetry tracer
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

tracer_provider = TracerProvider(
    active_span_processor=SimpleSpanProcessor(jaeger_exporter)
)
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

# Trace workflow execution
class TracedExecutor(Executor):
    """Executor wrapper that emits OpenTelemetry spans."""

    def __init__(self, wrapped: Executor):
        super().__init__(id=f"traced_{wrapped.id}")
        self.wrapped = wrapped

    @handler
    async def process(self, data, ctx: WorkflowContext) -> None:
        with tracer.start_as_current_span(f"executor_{self.wrapped.id}") as span:
            span.set_attribute("executor.id", self.wrapped.id)
            span.set_attribute("input.type", type(data).__name__)

            await self.wrapped.run(data, ctx)

            span.set_attribute("status", "success")
```

## Azure Monitor Integration

Export workflow metrics to Azure Monitor:

```python
from azure.monitor.opentelemetry import configure_azure_monitor
import os

# Configure Azure Monitor
configure_azure_monitor(
    connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"],
)

# Queries in Application Insights:
# traces | where customDimensions.executor_id == "my_executor"
# traces | where severityLevel == 2  // Errors only
# traces | summarize count() by tostring(customDimensions.executor_id)

class AzureMonitoredExecutor(Executor):
    """Executor that logs to Azure Monitor."""

    def __init__(self, wrapped: Executor):
        super().__init__(id=f"monitored_{wrapped.id}")
        self.wrapped = wrapped

    @handler
    async def process(self, data, ctx: WorkflowContext) -> None:
        start = time.perf_counter()

        try:
            await self.wrapped.run(data, ctx)
            duration = time.perf_counter() - start

            logger.info(
                f"Executor success",
                extra={
                    "executor_id": self.wrapped.id,
                    "duration_ms": duration * 1000,
                    "input_type": type(data).__name__,
                }
            )

        except Exception as e:
            duration = time.perf_counter() - start
            logger.error(
                f"Executor failed",
                extra={
                    "executor_id": self.wrapped.id,
                    "duration_ms": duration * 1000,
                    "error": str(e),
                }
            )
            raise
```

## Logging Executor Wrapper

Simple logging wrapper for any executor:

```python
import logging

logger = logging.getLogger("workflow.executors")

class LoggingExecutor(Executor):
    """Executor wrapper that adds detailed logging."""

    def __init__(self, wrapped: Executor, level=logging.INFO):
        super().__init__(id=f"log_{wrapped.id}")
        self.wrapped = wrapped
        self.level = level

    @handler
    async def process(self, data, ctx: WorkflowContext) -> None:
        logger.log(self.level, f"Starting {self.wrapped.id}")
        logger.log(self.level, f"  Input type: {type(data).__name__}")
        logger.log(self.level, f"  Input length: {len(str(data))}")

        try:
            await self.wrapped.run(data, ctx)
            logger.log(self.level, f"Completed {self.wrapped.id}")
        except Exception as e:
            logger.exception(f"Failed {self.wrapped.id}: {e}")
            raise
```

## Custom Event Emission via ctx.add_event

Emit custom events from executors:

```python
from agent_framework.workflows import WorkflowContext

class CustomEventExecutor(Executor):
    """Executor that emits custom events."""

    def __init__(self):
        super().__init__(id="event_emitter")

    @handler
    async def process(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        # Emit custom event
        await ctx.add_event({
            "type": "custom_event",
            "message": f"Processing item: {data.get('id')}",
            "metadata": {"source": self.id},
        })

        result = {"processed": True, **data}
        await ctx.send_message(result)

# Listen for custom events
async for event in workflow.run_stream(data):
    if getattr(event, "type", None) == "custom_event":
        print(f"Custom event: {event.message}")
```

## DevUI for Workflow Debugging

Visual debugger for inspecting workflow execution:

```python
from agent_framework.devui import DevUI

# Start DevUI
devui = DevUI(port=5173)
await devui.start()

# Access at http://localhost:5173
# DevUI shows:
# - Workflow graph visualization
# - Real-time executor execution
# - Input/output for each executor
# - Error details
# - Performance metrics

# Run workflow (DevUI captures automatically)
result = await workflow.run(input_data)

# View in DevUI browser interface
```

DevUI features:
- **Graph View**: Visual workflow diagram with execution status
- **Execution Timeline**: Event stream with timing
- **Executor Inspector**: Input/output inspection per executor
- **Error Viewer**: Stack traces and error context
- **Performance Dashboard**: Timing metrics by executor

## Token Tracking in Workflows

Track token usage across workflow execution:

```python
from agent_framework.workflows import Executor, handler, WorkflowContext

class TokenTrackingExecutor(Executor):
    """Track tokens used by executors."""

    def __init__(self, wrapped: Executor):
        super().__init__(id=f"token_{wrapped.id}")
        self.wrapped = wrapped
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @handler
    async def process(self, data, ctx: WorkflowContext) -> None:
        # Before execution
        before_tokens = self.get_total_tokens()

        await self.wrapped.run(data, ctx)

        # After execution
        after_tokens = self.get_total_tokens()
        tokens_used = after_tokens - before_tokens

        logger.info(f"[{self.wrapped.id}] Tokens used: {tokens_used}")

    def get_total_tokens(self) -> int:
        """Get total tokens from last completion."""
        # Implementation depends on client library
        return 0

# Usage with cost tracking
class CostTrackingMiddleware:
    """Track cost of workflow execution."""

    COST_PER_1K_TOKENS_INPUT = 0.0001
    COST_PER_1K_TOKENS_OUTPUT = 0.0003

    def __init__(self):
        self.total_cost = 0.0
        self.executions = []

    async def track_execution(self, executor_id: str, input_tokens: int, output_tokens: int):
        """Track execution cost."""
        input_cost = (input_tokens / 1000) * self.COST_PER_1K_TOKENS_INPUT
        output_cost = (output_tokens / 1000) * self.COST_PER_1K_TOKENS_OUTPUT
        total = input_cost + output_cost

        self.total_cost += total
        self.executions.append({
            "executor": executor_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total,
        })

        return total
```

## Production Observability Stack

Recommended setup for production environments:

```
Agent Framework Workflow
  ↓
  ├─ OpenTelemetry SDK (spans + metrics)
  │   ↓
  │   └─ Azure Monitor / Jaeger / Datadog
  │       ↓
  │       └─ Dashboards & Alerts
  │
  ├─ Structured Logging (JSON)
  │   ↓
  │   └─ Azure Log Analytics / Splunk / Elastic
  │       ↓
  │       └─ Kusto Queries / Search
  │
  └─ Custom Middleware (token counting, cost)
      ↓
      └─ Metrics Backend
          ↓
          └─ Cost Dashboards
```

### Complete Setup Example

```python
import logging
import json
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format=json.dumps({
        "timestamp": "%(asctime)s",
        "level": "%(levelname)s",
        "logger": "%(name)s",
        "message": "%(message)s"
    })
)

# Configure OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

azure_exporter = AzureMonitorTraceExporter(
    connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
)
trace.set_tracer_provider(
    TracerProvider(active_span_processor=SimpleSpanProcessor(azure_exporter))
)

# Run workflow with full observability
async def run_with_observability(workflow, input_data):
    """Run workflow with complete observability stack."""
    logger = logging.getLogger("workflow")
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("workflow_execution"):
        logger.info("Workflow started")

        try:
            result = await workflow.run(input_data)
            logger.info("Workflow completed", extra={"status": "success"})
            return result

        except Exception as e:
            logger.error("Workflow failed", extra={"error": str(e)})
            raise
```

## Workflow Execution Logging to JSON

Export complete workflow execution trace to JSON:

```python
import json
from pathlib import Path
from datetime import datetime

class WorkflowExecutionLogger:
    """Log complete workflow execution to JSON file."""

    def __init__(self, output_file: str = "workflow_execution.json"):
        self.output_file = Path(output_file)
        self.events = []
        self.start_time = None

    async def log_execution(self, workflow, input_data):
        """Execute workflow and log all events."""
        self.start_time = datetime.utcnow()

        async for event in workflow.run_stream(input_data):
            event_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": event.type,
                "executor_id": getattr(event, "executor_id", None),
                "data": json.dumps(event.data, default=str),
            }
            self.events.append(event_record)

        # Write execution log
        execution_log = {
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "total_events": len(self.events),
            "events": self.events,
        }

        with open(self.output_file, "w") as f:
            json.dump(execution_log, f, indent=2)

        return execution_log

# Usage
logger = WorkflowExecutionLogger("logs/workflow_exec_20240116.json")
await logger.log_execution(workflow, input_data)
```

## Debugging Tips

1. **Enable DEBUG logging**
   ```python
   logging.getLogger("agent_framework").setLevel(logging.DEBUG)
   ```

2. **Use DevUI for visual inspection** — Fastest way to debug
3. **Stream events for real-time monitoring** — Catch errors early
4. **Add timing middleware** — Find performance bottlenecks
5. **Wrap critical executors** — Log inputs/outputs
6. **Export to JSON** — Post-mortem analysis
7. **Set up alerts** — Monitor error rates and latencies
