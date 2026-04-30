# LangGraph — Functional API

> Source: [docs.langchain.com/oss/python/langgraph/functional-api](https://docs.langchain.com/oss/python/langgraph/functional-api)

## Table of Contents

- [Overview](#overview)
- [@entrypoint Decorator](#entrypoint-decorator)
- [@task Decorator](#task-decorator)
- [Execution Methods](#execution-methods)
- [Short-Term Memory with entrypoint.final](#short-term-memory-with-entrypointfinal)
- [Interrupts in Functional API](#interrupts-in-functional-api)
- [Streaming with Functional API](#streaming-with-functional-api)
- [When to Use Functional vs Graph API](#when-to-use-functional-vs-graph-api)
- [Design Rules](#design-rules)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

The Functional API provides LangGraph's key features (persistence, memory, human-in-the-loop, streaming) with minimal changes to existing Python code. Instead of defining explicit graph structure, you decorate functions with `@entrypoint` and `@task`.

```python
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver

@task
def fetch_data(query: str) -> dict:
    return {"results": search(query)}

@entrypoint(checkpointer=InMemorySaver())
def workflow(query: str) -> dict:
    data = fetch_data(query).result()
    return {"answer": process(data)}
```

## @entrypoint Decorator

Marks a function as a workflow starting point. The decorated function becomes a `Pregel` instance with `invoke`, `stream`, and async variants.

```python
@entrypoint(checkpointer=checkpointer)
def my_workflow(input_data: dict) -> dict:
    # Workflow logic here
    return {"result": "done"}
```

**Requirements:**
- Must accept a **single positional argument** (the input)
- Input and output must be JSON-serializable
- The `checkpointer` parameter enables persistence features

**Injectable parameters** (optional keyword-only arguments):

```python
@entrypoint(checkpointer=checkpointer)
def my_workflow(
    input_data: dict,
    *,
    previous: Any = None,    # Prior checkpoint state (short-term memory)
    store: BaseStore = None,  # Long-term memory store
    writer: StreamWriter = None,  # Custom streaming
    config: RunnableConfig = None,  # Runtime configuration
) -> dict:
    if previous:
        # Resume from last checkpoint
        pass
    return {"result": "done"}
```

**Async variant:**

```python
@entrypoint(checkpointer=checkpointer)
async def my_workflow(input_data: dict) -> dict:
    result = await async_operation()
    return {"result": result}
```

## @task Decorator

Represents a discrete unit of work that can be checkpointed and resumed. Tasks must be called from within an `@entrypoint` or a `StateGraph` node.

```python
from langgraph.func import task

@task
def expensive_computation(data: str) -> str:
    # Long-running operation
    return process(data)

@task
async def async_api_call(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

**Key characteristics:**
- Results are saved to checkpoints automatically
- On resume after interrupt, completed tasks return cached results
- Outputs must be JSON-serializable
- Support both sync and async functions (async requires Python 3.11+)

**Calling tasks:**

```python
# Synchronous — use .result()
@entrypoint(checkpointer=checkpointer)
def workflow(query: str) -> str:
    future = expensive_computation(query)
    return future.result()  # Block until done

# Asynchronous — use await
@entrypoint(checkpointer=checkpointer)
async def workflow(query: str) -> str:
    return await expensive_computation(query)

# Parallel execution
@entrypoint(checkpointer=checkpointer)
async def workflow(queries: list[str]) -> list[str]:
    futures = [expensive_computation(q) for q in queries]
    return [await f for f in futures]
```

## Execution Methods

The `@entrypoint`-decorated function exposes four execution methods:

```python
config = {"configurable": {"thread_id": "thread-1"}}

# Synchronous invoke
result = workflow.invoke(input_data, config)

# Async invoke
result = await workflow.ainvoke(input_data, config)

# Sync streaming
for chunk in workflow.stream(input_data, config):
    print(chunk)

# Async streaming
async for chunk in workflow.astream(input_data, config):
    print(chunk)
```

## Short-Term Memory with entrypoint.final

Decouple the value returned to callers from the value saved to the checkpoint:

```python
@entrypoint(checkpointer=checkpointer)
def running_total(number: int, *, previous: int | None = None) -> entrypoint.final[int, int]:
    previous = previous or 0
    total = previous + number
    # Returns `total` to caller, saves `total` as checkpoint for next call
    return entrypoint.final(value=total, save=total)

config = {"configurable": {"thread_id": "counter"}}
print(running_total.invoke(5, config))   # 5
print(running_total.invoke(3, config))   # 8
print(running_total.invoke(2, config))   # 10
```

**Type signature:** `entrypoint.final[ReturnType, SaveType]`
- `value` — what the caller receives
- `save` — what gets stored in the checkpoint (accessible as `previous` next call)

## Interrupts in Functional API

Combine `@task` with `interrupt()` for human-in-the-loop:

```python
from langgraph.types import interrupt, Command

@task
def generate_report(topic: str) -> str:
    return f"Report on {topic}: ..."

@entrypoint(checkpointer=InMemorySaver())
def workflow(topic: str) -> dict:
    report = generate_report(topic).result()
    
    approved = interrupt({
        "report": report,
        "question": "Do you approve this report?",
    })
    
    if approved:
        return {"report": report, "status": "published"}
    return {"report": report, "status": "rejected"}

# First call — generates report, then pauses at interrupt
config = {"configurable": {"thread_id": "t1"}}
result = workflow.invoke("AI Safety", config)
# Returns interrupt payload

# Resume with human decision
result = workflow.invoke(Command(resume=True), config)
# Returns {"report": "...", "status": "published"}
```

## Streaming with Functional API

### Custom Data Streaming

```python
from langgraph.config import get_stream_writer

@task
def process_items(items: list) -> list:
    writer = get_stream_writer()
    results = []
    for i, item in enumerate(items):
        result = transform(item)
        results.append(result)
        writer({"progress": f"{i+1}/{len(items)}"})
    return results
```

### With stream_mode

```python
for chunk in workflow.stream(input_data, config, stream_mode="custom"):
    print(chunk)  # {"progress": "1/5"}, {"progress": "2/5"}, ...
```

## When to Use Functional vs Graph API

| Scenario | Recommended API |
|----------|----------------|
| Simple linear pipeline with checkpointing | Functional |
| Complex multi-branch routing | Graph |
| Quick prototype with persistence | Functional |
| Multi-agent orchestration | Graph |
| Wrapping existing code with LangGraph features | Functional |
| Visual debugging and inspection | Graph |
| Map-reduce fan-out | Graph (Send) |
| Simple human-in-the-loop | Either |
| Subgraph composition | Graph |

## Design Rules

### Side Effects Must Be Inside Tasks

Tasks are checkpointed. If a workflow resumes after an interrupt, the entrypoint body re-executes, but completed tasks return cached results. Side effects outside tasks run again:

```python
# WRONG — file write happens twice on resume
@entrypoint(checkpointer=checkpointer)
def workflow(data: dict) -> str:
    with open("output.txt", "w") as f:
        f.write(json.dumps(data))
    return interrupt("Approve?")

# CORRECT — task caches the write
@task
def save_to_file(data: dict) -> str:
    with open("output.txt", "w") as f:
        f.write(json.dumps(data))
    return "saved"

@entrypoint(checkpointer=checkpointer)
def workflow(data: dict) -> str:
    save_to_file(data).result()
    return interrupt("Approve?")
```

### Control Flow Must Be Deterministic

Non-deterministic branching breaks resume behavior:

```python
# WRONG — time check gives different result on resume
import time
t0 = time.time()
if time.time() - t0 > 1:
    result = slow_task().result()

# CORRECT — wrap time in a task
@task
def get_elapsed(start: float) -> float:
    return time.time() - start

elapsed = get_elapsed(t0).result()
if elapsed > 1:
    result = slow_task().result()
```

## Common Pitfalls

1. **Calling tasks outside entrypoint** — Tasks can only run within `@entrypoint` or `StateGraph` nodes.
2. **Forgetting `.result()`** — Task calls return futures, not values. Call `.result()` or use `await`.
3. **Non-serializable task outputs** — Return JSON-serializable data only.
4. **Side effects in entrypoint body** — Wrap in `@task` to ensure idempotent replay.
5. **Using `previous` without checkpointer** — The `previous` parameter is always `None` without a checkpointer.

---

> **Related:** [01-graph-api.md](01-graph-api.md) for the graph-based alternative, [07-human-in-the-loop.md](07-human-in-the-loop.md) for interrupt patterns
