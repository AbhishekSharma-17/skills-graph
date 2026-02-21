# Observability — DevUI, Telemetry, Debugging, Tracing

## DevUI — Visual Agent Debugger

The built-in developer UI for inspecting agent execution in real-time.

### Setup

```bash
pip install agent-framework-devui
```

### Launch DevUI

```python
from agent_framework.devui import DevUI

# Start DevUI server
devui = DevUI(port=5173)
await devui.start()

# Create agent with DevUI attached
agent = client.as_agent(
    name="DebugAgent",
    instructions="You are a helpful assistant.",
    tools=[get_weather],
)

# DevUI automatically captures:
# - All agent runs
# - Tool calls and responses
# - Message history
# - Streaming tokens
# - Middleware execution
```

### Access
Open `http://localhost:5173` in your browser.

### What DevUI Shows

| Panel | Information |
|---|---|
| **Conversations** | Full message history per session |
| **Tool Calls** | Function name, arguments, results |
| **Streaming** | Token-by-token output display |
| **Middleware** | Execution order and timing |
| **Errors** | Exception details and stack traces |

## OpenTelemetry Integration

Built-in tracing for production observability:

```python
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# Configure OpenTelemetry
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# Agent automatically creates spans for:
# - agent.run() calls
# - Tool/function invocations
# - Chat client requests
# - Middleware execution
# - Workflow steps
```

### Azure Monitor Integration

```python
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(
    connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"],
)

# All agent traces now flow to Azure Monitor
# Query with Kusto: traces | where customDimensions.agent_name == "MyAgent"
```

## Logging

```python
import logging

# Set framework logging level
logging.getLogger("agent_framework").setLevel(logging.DEBUG)

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
```

### Log Levels

| Level | Shows |
|---|---|
| `DEBUG` | All internal framework operations |
| `INFO` | Agent runs, tool calls, major events |
| `WARNING` | Retries, deprecations |
| `ERROR` | Failures, exceptions |

## Custom Observability via Middleware

### Timing Middleware

```python
import time

async def timing_middleware(context, next):
    start = time.perf_counter()
    await next(context)
    elapsed = time.perf_counter() - start
    print(f"Agent run took {elapsed:.2f}s")
```

### Token Tracking Middleware

```python
async def token_tracking(context, next):
    await next(context)
    if hasattr(context, 'result') and context.result:
        # Track token usage
        for msg in getattr(context.result, 'messages', []):
            for content in msg.contents:
                if hasattr(content, 'usage'):
                    print(f"Tokens: {content.usage}")
```

### Error Tracking Middleware

```python
async def error_tracking(context, next):
    try:
        await next(context)
    except Exception as e:
        # Send to error tracking service
        await sentry.capture_exception(e)
        raise
```

## Production Observability Stack

```
Agent Framework
  → OpenTelemetry SDK (traces + metrics)
    → Azure Monitor / Application Insights
      → Dashboards & Alerts

Agent Framework
  → Structured Logging
    → Azure Log Analytics
      → Kusto Queries

Agent Framework
  → Custom Middleware (token counting)
    → Metrics Service
      → Cost Dashboards
```

## Debugging Tips

1. **Start with DevUI** for local development — visual inspection is fastest
2. **Enable DEBUG logging** to see all framework internals
3. **Add timing middleware** to find performance bottlenecks
4. **Track token usage** to control costs
5. **Use structured logging** for production — makes querying easy
6. **Set up alerts** on error rates and response latencies
