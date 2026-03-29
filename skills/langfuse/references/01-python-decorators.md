# Python SDK — Decorator-Based Tracing

> Source: [langfuse.com/docs/sdk/python/decorators](https://langfuse.com/docs/sdk/python/decorators)

## Table of Contents

- [Overview](#overview)
- [The @observe Decorator](#the-observe-decorator)
- [Parameters](#parameters)
- [Automatic Nesting](#automatic-nesting)
- [Async Support](#async-support)
- [Input/Output Capture](#inputoutput-capture)
- [Propagating Attributes](#propagating-attributes)
- [Updating Observations In-Flight](#updating-observations-in-flight)
- [Generation Tracking](#generation-tracking)
- [Error Handling](#error-handling)
- [OpenAI Drop-In Integration](#openai-drop-in-integration)
- [LangChain Callback Handler](#langchain-callback-handler)
- [Common Patterns](#common-patterns)
- [Pitfalls](#pitfalls)

---

## Overview

The `@observe()` decorator is the recommended way to instrument Python applications with Langfuse. It automatically captures function inputs, outputs, timing, and errors — creating hierarchical traces that reflect your call graph.

```python
from langfuse import observe

@observe()
def my_function(data: str) -> dict:
    return {"result": data.upper()}
```

## The @observe Decorator

Import from `langfuse`:

```python
from langfuse import observe
```

The decorator wraps any function (sync or async) and creates an observation in Langfuse. The first decorated function in a call chain creates a **trace**; nested decorated calls create **spans** or **generations** within that trace.

```python
@observe()
def outer():
    return inner()  # Creates a child span

@observe()
def inner():
    return "hello"
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Function name | Custom name for the observation |
| `as_type` | `str` | `"span"` | Observation type: `"span"` or `"generation"` |
| `capture_input` | `bool` | `True` | Capture function arguments as input |
| `capture_output` | `bool` | `True` | Capture return value as output |

```python
@observe(name="llm-call", as_type="generation")
def call_llm(prompt: str) -> str:
    # This creates a generation-type observation
    return llm.complete(prompt)

@observe(capture_input=False, capture_output=False)
def process_large_data(huge_payload: bytes) -> bytes:
    # Skip capturing large payloads to save bandwidth
    return transform(huge_payload)
```

## Automatic Nesting

When decorated functions call other decorated functions, Langfuse automatically captures the parent-child hierarchy. No manual span linking required.

```python
@observe()
def main_pipeline(query: str) -> str:
    """Top-level: creates a trace."""
    context = retrieve_documents(query)
    answer = generate_answer(query, context)
    return answer

@observe()
def retrieve_documents(query: str) -> list[str]:
    """Child span of main_pipeline."""
    return vector_db.search(query, top_k=5)

@observe(as_type="generation")
def generate_answer(query: str, context: list[str]) -> str:
    """Child generation of main_pipeline."""
    return openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Context: {context}"},
            {"role": "user", "content": query},
        ],
    ).choices[0].message.content
```

Resulting trace structure:
```
main_pipeline (trace)
├── retrieve_documents (span)
└── generate_answer (generation)
```

## Async Support

The decorator works with async functions out of the box:

```python
@observe(name="async-retrieval")
async def async_retrieve(query: str) -> list[str]:
    results = await vector_store.asearch(query)
    return results

@observe()
async def async_pipeline(query: str) -> str:
    docs = await async_retrieve(query)
    answer = await async_generate(query, docs)
    return answer
```

## Input/Output Capture

By default, all function arguments are captured as `input` and the return value as `output`. Disable for sensitive or large data:

```python
# Per-function
@observe(capture_input=False, capture_output=False)
def handle_pii(user_data: dict) -> dict:
    return anonymize(user_data)
```

Global disable via environment variable:

```bash
LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED=false
```

## Propagating Attributes

Use `propagate_attributes` to set trace-level metadata that flows to all child observations:

```python
from langfuse import observe, propagate_attributes

@observe()
def handle_request(user_id: str, session_id: str, query: str) -> str:
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=["production", "v2"],
        metadata={"pipeline": "rag", "version": "2.1"},
    ):
        return rag_pipeline(query)

@observe()
def rag_pipeline(query: str) -> str:
    # Automatically inherits user_id, session_id, tags, metadata
    docs = retrieve(query)
    return generate(query, docs)
```

Available attributes:
- `user_id` — associate trace with a user
- `session_id` — group traces into sessions (multi-turn)
- `tags` — list of string tags for filtering
- `metadata` — arbitrary key-value pairs
- `release` — application version/release identifier

## Updating Observations In-Flight

Modify the current trace or observation without holding a direct reference:

```python
from langfuse import observe, get_client

langfuse = get_client()

@observe()
def process_query(question: str) -> str:
    answer = call_llm(question)

    # Update the trace's top-level input/output
    langfuse.set_current_trace_io(
        input={"question": question},
        output={"answer": answer},
    )
    return answer

@observe(as_type="generation")
def call_llm(question: str) -> str:
    response = openai.chat.completions.create(...)

    # Update the current generation with model details
    langfuse.update_current_generation(
        model="gpt-4o",
        usage={"input": 150, "output": 50},
        metadata={"temperature": 0.7},
    )
    return response.choices[0].message.content
```

## Generation Tracking

Mark LLM calls as generations to track model-specific metrics:

```python
@observe(as_type="generation")
def call_model(prompt: str, model: str = "gpt-4o") -> str:
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    langfuse.update_current_generation(
        model=model,
        usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
        },
        model_parameters={"temperature": 0.7, "max_tokens": 500},
    )
    return response.choices[0].message.content
```

## Error Handling

Errors within decorated functions are automatically captured in the observation. The error is re-raised after recording:

```python
@observe()
def risky_operation():
    raise ValueError("Something went wrong")
    # Error captured in Langfuse, then re-raised
```

The observation will show:
- `level`: ERROR
- `status_message`: The exception message
- Timing: start to error timestamp

## OpenAI Drop-In Integration

The simplest way to trace OpenAI calls — swap the import:

```python
# Before
from openai import OpenAI

# After — just change the import
from langfuse.openai import openai

# All calls are now traced automatically
response = openai.chat.completions.create(
    name="my-generation",  # Optional: custom name
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    metadata={"feature": "chat"},  # Optional: custom metadata
)
```

Works with streaming, function calling, and all OpenAI features.

## LangChain Callback Handler

```python
from langfuse.langchain import CallbackHandler

handler = CallbackHandler()

# Use with any LangChain chain/agent
response = chain.invoke(
    {"input": "Hello"},
    config={"callbacks": [handler]},
)

# Or set globally
import langchain
langchain.callbacks.set_default(handler)
```

## Common Patterns

### RAG Pipeline

```python
@observe()
def rag_pipeline(query: str) -> str:
    with propagate_attributes(metadata={"pipeline": "rag"}):
        docs = retrieve(query)
        answer = generate(query, docs)
        return answer

@observe()
def retrieve(query: str) -> list[str]:
    embedding = embed(query)
    results = vector_db.search(embedding, top_k=5)
    return [r.text for r in results]

@observe(as_type="generation")
def generate(query: str, context: list[str]) -> str:
    return llm.complete(
        f"Context: {context}\nQuestion: {query}\nAnswer:"
    )
```

### Agent with Tool Calls

```python
@observe()
def agent_loop(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = call_llm(messages)
        if response.tool_calls:
            for tool_call in response.tool_calls:
                result = execute_tool(tool_call)
                messages.append(result)
        else:
            return response.content

@observe(as_type="generation")
def call_llm(messages: list) -> object:
    return openai.chat.completions.create(model="gpt-4o", messages=messages)

@observe()
def execute_tool(tool_call: object) -> dict:
    # Tool execution traced as a child span
    return run_tool(tool_call.function.name, tool_call.function.arguments)
```

## Pitfalls

1. **Forgetting `langfuse.flush()`** — In scripts and lambdas, events may be lost if the process exits before the background queue flushes. Always call `flush()` before exit.

2. **Thread safety** — The decorator uses context variables. In thread pools, wrap threaded work with proper context propagation or use `propagate_attributes`.

3. **Generator functions** — `@observe` captures the return value. For generators, the output is captured when the generator is fully consumed, not when it's created.

4. **Circular nesting** — Recursive decorated functions work, but deeply recursive calls may create very deep trace trees. Consider limiting depth.

5. **Large payloads** — Disable `capture_input`/`capture_output` for functions handling large data (images, audio, big JSON) to avoid excessive network usage.
