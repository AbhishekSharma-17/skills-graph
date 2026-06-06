# Observability and Tracing

> Source: [developers.llamaindex.ai — Observability](https://developers.llamaindex.ai/python/framework/module_guides/observability/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [Instrumentation Module](#instrumentation-module)
- [Global Handler Setup](#global-handler-setup)
- [OpenTelemetry Integration](#opentelemetry-integration)
- [Arize Phoenix](#arize-phoenix)
- [Langfuse](#langfuse)
- [Weights and Biases](#weights-and-biases)
- [Other Integrations](#other-integrations)
- [Token Counting](#token-counting)
- [Debugging Tips](#debugging-tips)

## Overview

LlamaIndex provides observability through one-click integrations that enable:

- **Tracing** — Follow execution flow through indexing, retrieval, and synthesis
- **Token tracking** — Monitor LLM and embedding token usage
- **Performance monitoring** — Measure latency at each pipeline stage
- **Debugging** — Inspect LLM inputs/outputs and retrieval results
- **Evaluation** — Assess response quality in production

The modern approach uses the `instrumentation` module (v0.10.20+), replacing the legacy `CallbackManager`.

## Instrumentation Module

The core observability framework in LlamaIndex:

```python
from llama_index.core.instrumentation import get_dispatcher

dispatcher = get_dispatcher()

# Register a custom span handler
from llama_index.core.instrumentation.span_handlers import SimpleSpanHandler

span_handler = SimpleSpanHandler()
dispatcher.add_span_handler(span_handler)

# Register a custom event handler
from llama_index.core.instrumentation.event_handlers import BaseEventHandler

class MyEventHandler(BaseEventHandler):
    def handle(self, event):
        print(f"Event: {event.class_name()} - {event.id_}")

dispatcher.add_event_handler(MyEventHandler())
```

### Span Types

Spans capture the execution of operations:
- `LLMCompletionStartEvent` / `LLMCompletionEndEvent`
- `EmbeddingStartEvent` / `EmbeddingEndEvent`
- `RetrievalStartEvent` / `RetrievalEndEvent`
- `SynthesisStartEvent` / `SynthesisEndEvent`
- `QueryStartEvent` / `QueryEndEvent`
- `AgentToolCallEvent` / `AgentToolCallResultEvent`

## Global Handler Setup

The simplest way to enable observability:

```python
from llama_index.core import set_global_handler

# Enable a specific handler
set_global_handler("arize_phoenix")
set_global_handler("wandb")
set_global_handler("simple")
```

The `simple` handler logs LLM inputs/outputs to the console — useful for quick debugging.

## OpenTelemetry Integration

Standard-based tracing compatible with any OTel-compatible backend:

```bash
pip install llama-index-instrumentation-otel
```

```python
from llama_index.instrumentation.otel import OTelSpanHandler
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

# Set up OTel provider
provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Register with LlamaIndex
from llama_index.core.instrumentation import get_dispatcher

dispatcher = get_dispatcher()
otel_handler = OTelSpanHandler()
dispatcher.add_span_handler(otel_handler)
```

### Export to Jaeger

```python
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
provider.add_span_processor(BatchSpanProcessor(exporter))
```

### Export to Grafana/Tempo

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
provider.add_span_processor(BatchSpanProcessor(exporter))
```

## Arize Phoenix

LlamaIndex's recommended observability platform with purpose-built LLM trace visualization:

```bash
pip install arize-phoenix openinference-instrumentation-llama-index
```

### Local Phoenix

```python
import phoenix as px

# Launch Phoenix UI
px.launch_app()

# Instrument LlamaIndex
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.sdk import trace as trace_sdk

tracer_provider = trace_sdk.TracerProvider()
LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
```

### Hosted Phoenix (LlamaTrace)

```python
import os

os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://app.phoenix.arize.com"

from llama_index.core import set_global_handler
set_global_handler("arize_phoenix")
```

Phoenix provides:
- Trace waterfall visualization
- LLM input/output inspection
- Retrieval result analysis
- Token usage tracking
- Latency breakdown per component

## Langfuse

Open-source LLM observability with detailed traces:

```bash
pip install llama-index-instrumentation-langfuse
```

```python
from llama_index.instrumentation.langfuse import LangfuseSpanHandler
from llama_index.core.instrumentation import get_dispatcher

langfuse_handler = LangfuseSpanHandler(
    public_key="pk-...",
    secret_key="sk-...",
    host="https://cloud.langfuse.com",
)

dispatcher = get_dispatcher()
dispatcher.add_span_handler(langfuse_handler)
```

## Weights and Biases

W&B Weave integration for experiment tracking:

```bash
pip install weave
```

```python
import weave

weave.init("my-llama-project")

# All LlamaIndex operations are automatically traced
query_engine = index.as_query_engine()
response = query_engine.query("What is the revenue?")
```

W&B tracks:
- LLM calls with inputs/outputs
- Token counts and costs
- Execution time per operation
- Nested operation hierarchy

## Other Integrations

| Platform | Package | Setup |
|----------|---------|-------|
| MLflow | Built-in | `mlflow.llama_index.autolog()` |
| SigNoz | `openinference-instrumentation-llama-index` | OTel auto-instrumentation |
| Literal AI | `llama-index-callbacks-literalai` | Callback handler |
| Comet Opik | `opik` | Auto-instrumentation |
| DeepEval | `deepeval` | Evaluation integration |
| Langtrace | `langtrace-python-sdk` | Auto-instrumentation |
| AgentOps | `agentops` | Session tracking |

### MLflow

```python
import mlflow

mlflow.llama_index.autolog()

# All LlamaIndex operations auto-traced
with mlflow.start_run():
    response = query_engine.query("What happened?")
```

## Token Counting

Track token usage without a full observability platform:

```python
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
import tiktoken

token_counter = TokenCountingHandler(
    tokenizer=tiktoken.encoding_for_model("gpt-4o").encode,
    verbose=True,
)

from llama_index.core import Settings
Settings.callback_manager = CallbackManager([token_counter])

# After running queries
print(f"Embedding tokens: {token_counter.total_embedding_token_count}")
print(f"LLM prompt tokens: {token_counter.prompt_llm_token_count}")
print(f"LLM completion tokens: {token_counter.completion_llm_token_count}")
print(f"Total LLM tokens: {token_counter.total_llm_token_count}")

# Reset counters
token_counter.reset_counts()
```

## Debugging Tips

### Enable Verbose Logging

```python
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
```

### Inspect Retrieved Nodes

```python
response = query_engine.query("my question")
for node in response.source_nodes:
    print(f"Score: {node.score:.4f}")
    print(f"Node ID: {node.node_id}")
    print(f"Text: {node.text[:200]}")
    print(f"Metadata: {node.metadata}")
    print("---")
```

### Inspect Prompts

```python
prompts = query_engine.get_prompts()
for key, prompt in prompts.items():
    print(f"Prompt key: {key}")
    print(f"Template: {prompt.template}")
```

### Debug Agent Tool Calls

```python
from llama_index.core.agent.workflow import ToolCall, ToolCallResult

handler = agent.run(user_msg="my question")
async for event in handler.stream_events():
    if isinstance(event, ToolCall):
        print(f"Tool: {event.tool_name}")
        print(f"Args: {event.tool_kwargs}")
    elif isinstance(event, ToolCallResult):
        print(f"Result: {event.tool_output}")
```

### Simple Console Handler

```python
from llama_index.core import set_global_handler

set_global_handler("simple")

# Now all LLM calls print to console
response = query_engine.query("test")
```
