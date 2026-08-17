# Callbacks & Tracing

> Source: https://docs.langchain.com/oss/python/langchain/callbacks

## Table of Contents

- [Overview](#overview)
- [Callback Handlers](#callback-handlers)
- [Lifecycle Events](#lifecycle-events)
- [Passing Callbacks](#passing-callbacks)
- [Built-in Handlers](#built-in-handlers)
- [LangSmith Tracing](#langsmith-tracing)
- [OpenTelemetry Integration](#opentelemetry-integration)
- [Custom Handlers](#custom-handlers)
- [Common Patterns](#common-patterns)

## Overview

Callbacks are Python objects that implement lifecycle methods triggered during LLM operations — model calls, tool executions, chain steps, and retrieval. They enable logging, tracing, monitoring, and debugging without modifying core logic. LangSmith integration provides production-grade observability.

## Callback Handlers

A callback handler implements one or more lifecycle methods:

```python
from langchain_core.callbacks import BaseCallbackHandler

class MyHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"LLM started with {len(prompts)} prompts")
    
    def on_llm_end(self, response, **kwargs):
        print(f"LLM finished: {response.generations[0][0].text[:50]}")
    
    def on_llm_error(self, error, **kwargs):
        print(f"LLM error: {error}")
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        print(f"Chain started: {serialized.get('name', 'unknown')}")
    
    def on_chain_end(self, outputs, **kwargs):
        print("Chain finished")
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"Tool started: {serialized.get('name')}")
    
    def on_tool_end(self, output, **kwargs):
        print(f"Tool finished: {output[:50]}")
    
    def on_retriever_start(self, serialized, query, **kwargs):
        print(f"Retriever query: {query}")
    
    def on_retriever_end(self, documents, **kwargs):
        print(f"Retrieved {len(documents)} documents")
```

### Async Handler

```python
from langchain_core.callbacks import AsyncCallbackHandler

class AsyncMyHandler(AsyncCallbackHandler):
    async def on_llm_start(self, serialized, prompts, **kwargs):
        await log_to_database("llm_start", prompts)
    
    async def on_llm_end(self, response, **kwargs):
        await log_to_database("llm_end", response)
```

## Lifecycle Events

| Event | Trigger |
|-------|---------|
| `on_llm_start` / `on_chat_model_start` | Model invocation begins |
| `on_llm_new_token` | New token generated (streaming) |
| `on_llm_end` | Model invocation completes |
| `on_llm_error` | Model invocation fails |
| `on_chain_start` | Chain/runnable begins |
| `on_chain_end` | Chain/runnable completes |
| `on_chain_error` | Chain/runnable fails |
| `on_tool_start` | Tool execution begins |
| `on_tool_end` | Tool execution completes |
| `on_tool_error` | Tool execution fails |
| `on_retriever_start` | Retriever query begins |
| `on_retriever_end` | Retriever returns results |
| `on_agent_action` | Agent decides to use a tool |
| `on_agent_finish` | Agent completes execution |

## Passing Callbacks

### At Invocation Time

```python
handler = MyHandler()

response = model.invoke("Hello", config={"callbacks": [handler]})

chain.invoke({"topic": "AI"}, config={"callbacks": [handler]})

agent.invoke(
    {"messages": [{"role": "user", "content": "Search for news"}]},
    config={"callbacks": [handler]}
)
```

### At Construction Time

```python
model = ChatOpenAI(model="gpt-4o", callbacks=[handler])

chain = prompt | model | parser
chain = chain.with_config(callbacks=[handler])
```

### With Tags and Metadata

```python
response = chain.invoke(
    {"topic": "AI"},
    config={
        "callbacks": [handler],
        "tags": ["production", "v2"],
        "metadata": {"user_id": "u123", "request_id": "r456"}
    }
)
```

## Built-in Handlers

### StdOutCallbackHandler

Print all events to stdout:

```python
from langchain_core.callbacks import StdOutCallbackHandler

handler = StdOutCallbackHandler()
model.invoke("Hello", config={"callbacks": [handler]})
```

### OpenAI Cost Tracker

```python
from langchain_community.callbacks import get_openai_callback

with get_openai_callback() as cb:
    model.invoke("First call")
    model.invoke("Second call")
    
    print(f"Total tokens: {cb.total_tokens}")
    print(f"Prompt tokens: {cb.prompt_tokens}")
    print(f"Completion tokens: {cb.completion_tokens}")
    print(f"Total cost: ${cb.total_cost:.4f}")
```

### Streaming StdOut

```python
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

model = ChatOpenAI(
    model="gpt-4o",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)
model.invoke("Write a poem")
```

## LangSmith Tracing

LangSmith provides production-grade observability for LangChain applications.

### Setup

```bash
pip install langsmith
export LANGSMITH_API_KEY="lsv2_..."
export LANGSMITH_TRACING=true
export LANGSMITH_PROJECT="my-project"
```

### Automatic Tracing

With environment variables set, all LangChain operations are automatically traced:

```python
chain = prompt | model | parser
result = chain.invoke({"topic": "AI"})
```

### Manual Tracing with @traceable

```python
from langsmith import traceable

@traceable(name="custom_pipeline")
def my_pipeline(question: str) -> str:
    docs = retriever.invoke(question)
    context = "\n".join(d.page_content for d in docs)
    return chain.invoke({"context": context, "question": question})
```

### Run Trees

```python
from langsmith import RunTree

with RunTree(name="experiment", project_name="my-project") as rt:
    result = chain.invoke({"topic": "AI"})
    rt.end(outputs={"result": result})
```

### Feedback

```python
from langsmith import Client

client = Client()
client.create_feedback(
    run_id="run-uuid",
    key="correctness",
    score=1.0,
    comment="Accurate response"
)
```

## OpenTelemetry Integration

Export LangChain traces to any OpenTelemetry-compatible backend:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from langchain_core.callbacks import OpenTelemetryCallbackHandler

provider = TracerProvider()
provider.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
)
trace.set_tracer_provider(provider)

otel_handler = OpenTelemetryCallbackHandler(tracer_provider=provider)

chain.invoke(
    {"topic": "AI"},
    config={"callbacks": [otel_handler]}
)
```

## Custom Handlers

### Token Counter

```python
class TokenCounter(BaseCallbackHandler):
    def __init__(self):
        self.total_tokens = 0
    
    def on_llm_end(self, response, **kwargs):
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            self.total_tokens += usage.get("total_tokens", 0)
    
    def report(self):
        print(f"Total tokens used: {self.total_tokens}")
```

### Latency Tracker

```python
import time

class LatencyTracker(BaseCallbackHandler):
    def __init__(self):
        self.start_times = {}
    
    def on_llm_start(self, serialized, prompts, *, run_id, **kwargs):
        self.start_times[run_id] = time.time()
    
    def on_llm_end(self, response, *, run_id, **kwargs):
        elapsed = time.time() - self.start_times.pop(run_id, time.time())
        print(f"LLM call took {elapsed:.2f}s")
```

### Error Logger

```python
import logging

logger = logging.getLogger("langchain")

class ErrorLogger(BaseCallbackHandler):
    def on_llm_error(self, error, **kwargs):
        logger.error(f"LLM error: {error}", exc_info=True)
    
    def on_tool_error(self, error, **kwargs):
        logger.error(f"Tool error: {error}", exc_info=True)
    
    def on_chain_error(self, error, **kwargs):
        logger.error(f"Chain error: {error}", exc_info=True)
```

## Common Patterns

### Multiple Handlers

```python
chain.invoke(
    {"topic": "AI"},
    config={"callbacks": [
        StdOutCallbackHandler(),
        TokenCounter(),
        LatencyTracker(),
        ErrorLogger(),
    ]}
)
```

### Conditional Tracing

```python
import os

callbacks = []
if os.getenv("LANGSMITH_TRACING") == "true":
    callbacks.append(langsmith_handler)
if os.getenv("DEBUG") == "true":
    callbacks.append(StdOutCallbackHandler())

chain.invoke({"topic": "AI"}, config={"callbacks": callbacks})
```

### Agent-Level Callbacks

```python
agent = create_agent(
    model="openai:gpt-4o",
    tools=[search],
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Search for news"}]},
    config={
        "callbacks": [MyHandler()],
        "tags": ["agent-run"],
        "metadata": {"session": "s1"}
    }
)
```
