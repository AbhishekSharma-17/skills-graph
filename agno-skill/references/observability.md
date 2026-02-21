# Observability

Agno supports observability through OpenTelemetry, integrating with popular tracing and monitoring platforms. Auto-instrumentation and flexible export to any OTel-compatible backend.

## Overview

- **Trace**: Visualize agent execution flows, calls, and latency
- **Monitor**: Track performance metrics, errors, and usage patterns
- **Debug**: Identify and resolve issues in agent behavior
- **Integration**: Works with 12+ providers via standardized protocols

## Supported Platforms

| Platform | Package | Init Method | Integration Type |
|----------|---------|-------------|-----------------|
| AgentOps | `agentops` | `agentops.init()` | Auto-instrumentation |
| Arize Phoenix | `arize-phoenix`, `openinference-instrumentation-agno` | `register(auto_instrument=True)` | OpenInference |
| Atla | `atla-insights` | `configure()` + context manager | Custom SDK |
| LangDB | `pylangdb[agno]` | `init()` from `pylangdb.agno` | Custom SDK |
| Langfuse | `langfuse`, `openinference-instrumentation-agno` | `AgnoInstrumentor().instrument()` | OpenInference |
| LangSmith | `openinference-instrumentation-agno` | `AgnoInstrumentor().instrument()` | OpenInference |
| Langtrace | `langtrace-python-sdk` | `langtrace.init()` | Auto-instrumentation |
| LangWatch | `langwatch`, `openinference-instrumentation-agno` | `langwatch.setup(instrumentors=[...])` | OpenInference |
| Maxim | `maxim-py` | `instrument_agno(Maxim().logger())` | Custom SDK |
| OpenLIT | `openlit` | `openlit.init(otlp_endpoint=...)` | OpenTelemetry |
| Traceloop | `traceloop-sdk` | `Traceloop.init(app_name=...)` | OpenLLMetry |
| Weave (WandB) | `weave` | `weave.init()` + decorators | Decorator-based |

## Quick Start Patterns

### Pattern 1: Auto-Instrumentation
For AgentOps and Langtrace:

```python
# Option A: AgentOps
import agentops
agentops.init()

# Option B: Langtrace
from langtrace_python_sdk import langtrace
langtrace.init()

from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(model=OpenAIResponses(id="gpt-4"))
agent.print_response("Hello!")  # Automatically traced
```

### Pattern 2: OpenInference
For Arize, Langfuse, LangSmith, LangWatch:

```python
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter(otlp_endpoint="your-endpoint"))
)
trace_api.set_tracer_provider(tracer_provider)

AgnoInstrumentor().instrument()

# All agent calls now traced automatically
from agno.agent import Agent
agent = Agent(model=...)
agent.run("query")
```

### Pattern 3: OpenTelemetry Direct
For OpenLIT:

```python
import openlit
openlit.init(otlp_endpoint="http://127.0.0.1:4318")

# All calls automatically traced
```

### Pattern 4: Decorator-Based
For Weave:

```python
import weave
weave.init("my-project")

@weave.op()
def run_agent(prompt: str):
    return agent.run(prompt)

run_agent("What's the weather?")
```

## Provider-Specific Setup

### AgentOps

```bash
uv pip install agentops
export AGENTOPS_API_KEY=<your-key>
```

```python
import agentops
agentops.init()
```

Traces are sent to AgentOps dashboard automatically.

### Arize Phoenix

```bash
uv pip install arize-phoenix openinference-instrumentation-agno \
  opentelemetry-sdk opentelemetry-exporter-otlp
export ARIZE_PHOENIX_API_KEY=<your-key>
```

```python
from phoenix.otel import register
import os

os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com"
tracer_provider = register(project_name="my-project", auto_instrument=True)
```

### Langfuse

```bash
uv pip install langfuse openinference-instrumentation-agno \
  opentelemetry-sdk opentelemetry-exporter-otlp
export LANGFUSE_PUBLIC_KEY=<your-key>
export LANGFUSE_SECRET_KEY=<your-secret>
```

Regions: `https://us.cloud.langfuse.com/api/public/otel` (US), `https://eu.cloud.langfuse.com/api/public/otel` (EU)

### Langtrace

```bash
uv pip install langtrace-python-sdk
export LANGTRACE_API_KEY=<your-key>
```

```python
from langtrace_python_sdk import langtrace
langtrace.init()
```

### LangWatch

```bash
uv pip install langwatch openinference-instrumentation-agno
export LANGWATCH_API_KEY=<your-key>
```

```python
import langwatch
from openinference.instrumentation.agno import AgnoInstrumentor

langwatch.setup(instrumentors=[AgnoInstrumentor()])
```

### LangSmith

```bash
uv pip install openinference-instrumentation-agno \
  opentelemetry-sdk opentelemetry-exporter-otlp
export LANGSMITH_API_KEY=<your-key>
export LANGSMITH_TRACING=true
export LANGSMITH_PROJECT=<your-project>
```

### OpenLIT

```bash
uv pip install openlit
```

```python
import openlit
openlit.init(otlp_endpoint="http://127.0.0.1:4318")
```

CLI alternative: `openlit-instrument --service-name my-app python app.py`

### Traceloop

```bash
uv pip install traceloop-sdk
export TRACELOOP_API_KEY=<your-key>
```

```python
from traceloop.sdk import Traceloop
Traceloop.init(app_name="my-app")
```

Privacy: Set `TRACELOOP_TRACE_CONTENT=false` to disable prompt logging.

### Maxim

```bash
uv pip install maxim-py
export MAXIM_API_KEY=<your-key>
export MAXIM_LOG_REPO_ID=<your-repo-id>
```

```python
from maxim import Maxim
from maxim.logger.agno import instrument_agno

instrument_agno(Maxim().logger())
```

### Atla

```bash
uv pip install atla-insights
export ATLA_API_KEY=<your-key>
```

```python
from atla_insights import configure, instrument_agno

configure(token=os.getenv("ATLA_API_KEY"))

with instrument_agno("openai"):
    response = agent.run("query")
```

### LangDB

```bash
uv pip install 'pylangdb[agno]'
export LANGDB_API_KEY=<your-key>
export LANGDB_PROJECT_ID=<your-id>
```

```python
from pylangdb.agno import init
init()

from agno.models.langdb import LangDB
agent = Agent(model=LangDB(id="openai/gpt-4"))
```

### Weave (WandB)

```bash
uv pip install weave
export WANDB_API_KEY=<your-key>
```

```python
import weave
weave.init("my-project-name")

@weave.op()
def my_agent_call(prompt: str):
    return agent.run(prompt)
```

## Common Imports

```python
# OpenInference (used by Arize, Langfuse, LangSmith, LangWatch)
from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Auto-instrumentation
import agentops
from langtrace_python_sdk import langtrace

# Decorator-based
import weave

# Direct OpenTelemetry
import openlit
```

## Notes

- This observability integration is **separate from Agno's built-in tracing** (`setup_tracing()`). See the Tracing reference for database-backed trace storage.
- Most platforms support environment variable configuration; check provider docs for additional options.
- OpenInference is the standard integration for multiple providers—use it when available.
- All 12 providers support the same agent code; choose based on your backend infrastructure.
