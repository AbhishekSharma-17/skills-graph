# Tracing

> Source: https://deepeval.com/docs/evaluation-llm-tracing

## Overview

DeepEval's LLM tracing enables monitoring of applications from execution start to finish. A **trace** comprises multiple **spans**, where each span represents a user-defined scope for evaluation or debugging. The `@observe()` decorator is the foundational tool — each decorated call becomes a span, and the outermost call becomes the trace.

## The @observe Decorator

### Basic Usage

```python
from deepeval.tracing import observe

@observe()
def retriever(query: str) -> list[str]:
    return ["Context for the given query"]

@observe()
def generator(query: str, context: list[str]) -> str:
    return "Generated response"

@observe()
def llm_app(query: str) -> str:
    context = retriever(query)
    return generator(query, context)
```

When `llm_app()` is called, it creates a trace containing three spans:
- `llm_app` (trace-level span)
  - `retriever` (child span)
  - `generator` (child span)

### Decorator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `metrics` | `list[BaseMetric]` | Metrics for component-level evaluation |
| `name` | `str` | Custom span display name (defaults to function name) |
| `type` | `str` | Span classification (see types below) |
| `metric_collection` | `str` | Reference to stored metric collections |

### Span Types

The `type` parameter classifies spans without affecting scoring:

| Type | Purpose | Special Parameters |
|------|---------|-------------------|
| `"llm"` | Language model calls | `model`, token costs |
| `"retriever"` | Vector store retrieval | `embedder`, top_k, chunk_size |
| `"tool"` | Function invocations | `description` |
| `"agent"` | Autonomous steps | `available_tools`, `handoff_agents` |

```python
@observe(type="retriever")
def search_docs(query: str) -> list[str]:
    return vector_store.search(query)

@observe(type="llm")
def generate_response(prompt: str) -> str:
    return llm.generate(prompt)

@observe(type="tool")
def calculator(expression: str) -> float:
    return eval(expression)

@observe(type="agent")
def research_agent(query: str) -> str:
    docs = search_docs(query)
    return generate_response(f"Based on: {docs}, answer: {query}")
```

## update_current_trace and update_current_span

These functions register test case data for evaluation at trace or span level:

### update_current_trace

Sets data for the entire trace (end-to-end evaluation):

```python
from deepeval.tracing import observe, update_current_trace

@observe()
def my_agent(query: str) -> str:
    chunks = retrieve(query)
    answer = generate(query, chunks)
    update_current_trace(
        input=query,
        output=answer,
        retrieval_context=chunks,
        tags=["production", "v2"],
        metadata={"model": "gpt-4", "temperature": 0.7}
    )
    return answer
```

### update_current_span

Sets data for the current span (component-level evaluation):

```python
from deepeval.tracing import observe, update_current_span
from deepeval.test_case import LLMTestCase
from deepeval.metrics import ContextualRelevancyMetric

@observe(metrics=[ContextualRelevancyMetric()])
def retriever(query: str) -> list[str]:
    chunks = vector_store.search(query)
    update_current_span(
        test_case=LLMTestCase(
            input=query,
            retrieval_context=chunks
        )
    )
    return chunks
```

### Supported Parameters

Both functions accept (with `actual_output` renamed to `output`):

| Parameter | Type | Description |
|-----------|------|-------------|
| `input` | `str` | Input to the component |
| `output` | `str` | Output from the component |
| `expected_output` | `str` | Expected output |
| `retrieval_context` | `list[str]` | Retrieved chunks |
| `context` | `list[str]` | Ground truth context |
| `tools_called` | `list[ToolCall]` | Tools invoked |
| `expected_tools` | `list[ToolCall]` | Expected tools |
| `tags` | `list[str]` | Labels (trace-only) |
| `metadata` | `dict` | Arbitrary metadata |

## Component-Level Evaluation

Attach metrics to specific spans to evaluate individual components:

```python
from deepeval.tracing import observe, update_current_span
from deepeval.metrics import (
    ContextualRelevancyMetric,
    AnswerRelevancyMetric,
    FaithfulnessMetric
)
from deepeval.test_case import LLMTestCase

@observe(metrics=[ContextualRelevancyMetric()])
async def retrieve(query: str) -> list[str]:
    chunks = await vector_store.search(query)
    update_current_span(
        test_case=LLMTestCase(input=query, retrieval_context=chunks)
    )
    return chunks

@observe(metrics=[AnswerRelevancyMetric(), FaithfulnessMetric()])
async def generate(query: str, chunks: list[str]) -> str:
    response = await llm.generate(query, context=chunks)
    update_current_span(
        test_case=LLMTestCase(
            input=query,
            actual_output=response,
            retrieval_context=chunks
        )
    )
    return response

@observe()
async def rag_pipeline(query: str) -> str:
    chunks = await retrieve(query)
    answer = await generate(query, chunks)
    update_current_trace(input=query, output=answer)
    return answer
```

## Evaluation Loop with Tracing

```python
import asyncio
from deepeval.dataset import EvaluationDataset, Golden

dataset = EvaluationDataset(goldens=[
    Golden(input="Why is the sky blue?"),
    Golden(input="How does gravity work?"),
])

for golden in dataset.evals_iterator():
    task = asyncio.create_task(rag_pipeline(golden.input))
    dataset.evaluate(task)
```

Synchronous variant:

```python
from deepeval.dataset import AsyncConfig

for golden in dataset.evals_iterator(
    async_config=AsyncConfig(run_async=False)
):
    rag_pipeline(golden.input)
```

## Framework Integrations

DeepEval provides first-class integrations requiring minimal setup:

### LangChain / LangGraph

```python
from deepeval.integrations.langchain import CallbackHandler

result = agent.invoke(
    {"input": "Hello"},
    config={"callbacks": [CallbackHandler()]}
)
```

### OpenAI (Drop-in Replacement)

```python
from deepeval.openai import OpenAI

client = OpenAI()  # All calls automatically traced
```

### Anthropic (Drop-in Replacement)

```python
from deepeval.anthropic import Anthropic

client = Anthropic()  # All calls automatically traced
```

### Other Integrations

| Framework | Method |
|-----------|--------|
| Pydantic AI | `DeepEvalInstrumentationSettings()` |
| LlamaIndex | Event handler registration |
| CrewAI | Agent shim |
| Google ADK | Instrumentation function |
| OpenAI Agents | Instrumentation function |
| Strands | Instrumentation function |
| AgentCore | Instrumentation function |

## Environment Configuration

Control trace logging:

```bash
CONFIDENT_TRACE_VERBOSE=0    # Disable console trace output
CONFIDENT_TRACE_FLUSH=0      # Disable trace flush logging
```

## Key Characteristics

- **Non-intrusive:** Minimal code changes, no added latency
- **Production-safe:** Metrics only execute within `evaluate()` or `assert_test()`, not during normal function calls
- **Runtime flexibility:** Test cases defined at runtime as data flows through the system
- **Async support:** Both sync and async functions work with `@observe`

## Common Pitfalls

1. **Forgetting `update_current_trace`** — Without it, trace-level metrics have no data to score
2. **Metrics in wrong location** — `@observe(metrics=[...])` attaches to that span; pass metrics to `evals_iterator()` for trace-level
3. **Mixing trace and span data** — Use `update_current_trace` for end-to-end, `update_current_span` for components
4. **Not using framework integrations** — Drop-in replacements are much simpler than manual instrumentation
5. **Expecting metrics to run on every call** — Metrics only execute during evaluation loops, not regular function calls
