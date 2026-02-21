# Workflows Core — Executors, Edges, Events, Builder, Execution

## Architecture

```
Workflow = Graph of Executors connected by Edges
  → Executor receives input via WorkflowContext
  → Executor processes and sends output via ctx.send_message() or ctx.yield_output()
  → Edges route data between executors (optionally conditional)
  → WorkflowEvents collect all outputs and state
```

## Executors

An executor is a node in the workflow graph. Two implementation styles:

### Class-Based Executor

```python
from agent_framework.workflows import Executor, handler, WorkflowContext

class UpperCase(Executor):
    """Convert text to uppercase."""

    def __init__(self, id: str):
        super().__init__(id=id)

    @handler
    async def to_upper_case(self, text: str, ctx: WorkflowContext[str]) -> None:
        """Receives text, uppercases it, sends to next node."""
        await ctx.send_message(text.upper())
```

### Function-Based Executor

```python
from agent_framework.workflows import executor, WorkflowContext
from typing import Never

@executor(id="reverse_text")
async def reverse_text(text: str, ctx: WorkflowContext[Never, str]) -> None:
    """Reverse string and yield as final workflow output."""
    await ctx.yield_output(text[::-1])
```

### Custom Executor with Initialization

```python
class ContentCreator(Executor):
    """Executor with custom initialization and state."""

    def __init__(self, client, style: str = "formal"):
        super().__init__(id="content_creator")
        self.client = client
        self.style = style

    @handler
    async def create(self, topic: str, ctx: WorkflowContext[str]) -> None:
        prompt = f"Write about {topic} in a {self.style} style."
        response = await self.client.complete_async(prompt)
        await ctx.send_message(response.text)
```

### Executor with Multiple Handlers

```python
class DataProcessor(Executor):
    def __init__(self):
        super().__init__(id="processor")

    @handler
    async def process_text(self, text: str, ctx: WorkflowContext[str]) -> None:
        """Handle text input."""
        await ctx.send_message(f"Processed text: {text}")

    @handler
    async def process_data(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        """Handle dict input."""
        await ctx.send_message({"processed": True, **data})
```

## WorkflowContext

The context object passed to every executor. It controls data flow.

### Methods

| Method | Purpose | When to Use |
|---|---|---|
| `ctx.send_message(data)` | Send data to next connected node(s) | Intermediate nodes |
| `ctx.send_message(data, target="node_name")` | Send to specific node | Conditional routing |
| `ctx.yield_output(data)` | Yield final workflow output | Exit nodes only |

### Type Parameters

```python
# Intermediate node: receives str, forwards to next
ctx: WorkflowContext[str]

# Exit node: receives input, yields str output
ctx: WorkflowContext[Never, str]  # Never = no forwarding

# Both: receives str input, can yield dict output
ctx: WorkflowContext[str, dict]
```

## Edges — Connecting Nodes

### Simple Edge

```python
workflow = Workflow()
workflow.add_node("clean", text_cleaner)
workflow.add_node("analyze", text_analyzer)
workflow.connect("clean", "analyze")  # clean → analyze
```

### Fan-Out (One to Many)

```python
workflow.connect("input", "branch_a")
workflow.connect("input", "branch_b")
# input sends to BOTH branch_a and branch_b
```

### Fan-In (Many to One)

```python
workflow.connect("branch_a", "merge")
workflow.connect("branch_b", "merge")
# Both branches feed into merge
```

### Conditional Routing via send_message

```python
class Router(Executor):
    def __init__(self):
        super().__init__(id="router")

    @handler
    async def route(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        if data.get("priority") == "high":
            await ctx.send_message(data, target="urgent_handler")
        else:
            await ctx.send_message(data, target="normal_handler")

# Wire up
workflow.connect("router", "urgent_handler")
workflow.connect("router", "normal_handler")
```

## Building a Workflow

### Step-by-Step

```python
from agent_framework.workflows import Workflow

# 1. Create workflow
workflow = Workflow()

# 2. Add nodes
workflow.add_node("step1", my_first_executor)
workflow.add_node("step2", my_second_executor)
workflow.add_node("step3", my_exit_executor)

# 3. Connect nodes
workflow.connect("step1", "step2")
workflow.connect("step2", "step3")

# 4. Set entry and exit
workflow.set_entry_node("step1")   # Receives initial input
workflow.set_exit_node("step3")    # Must use ctx.yield_output()
```

### Rules

| Rule | Details |
|---|---|
| Exactly ONE entry node | Set with `set_entry_node()` — receives `workflow.run()` input |
| Exactly ONE exit node | Set with `set_exit_node()` — must call `ctx.yield_output()` |
| All nodes must be connected | Disconnected nodes cause errors |
| Entry receives initial input | Data type must match executor's handler signature |
| Exit must yield output | Use `ctx.yield_output()`, not `ctx.send_message()` |

## Running a Workflow

### Basic Execution

```python
events = await workflow.run("hello world")

# Get outputs
outputs = events.get_outputs()
print(f"Result: {outputs}")

# Get final state
state = events.get_final_state()
```

### Streaming Execution

```python
async for event in workflow.run_stream("hello world"):
    if event.type == "output":
        print(f"Output from {event.executor_id}: {event.data}")
    elif event.type == "error":
        print(f"Error: {event.data}")
```

## WorkflowEvents

The return value of `workflow.run()`:

```python
events = await workflow.run(input_data)

events.get_outputs()       # Final output(s) from exit node
events.get_final_state()   # Workflow state after completion
```

## Event Types (from run_stream)

| Event Type | Description |
|---|---|
| `"output"` | Data yielded by an executor |
| `"request_info"` | Executor requesting external input (human-in-loop) |
| `"error"` | Error during execution |

```python
from agent_framework import WorkflowEvent, WorkflowOutputEvent

async for event in workflow.run_stream(input_data):
    if isinstance(event, WorkflowOutputEvent):
        print(f"Final output: {event.data}")
    elif event.type == "request_info":
        # Human-in-the-loop request
        print(f"Request from {event.executor_id}: {event.data}")
    elif event.type == "error":
        print(f"Error in {event.executor_id}: {event.data}")
```

## Complete Example

```python
import asyncio
from agent_framework.workflows import Workflow, Executor, handler, executor, WorkflowContext
from typing import Never

class TextCleaner(Executor):
    def __init__(self):
        super().__init__(id="cleaner")

    @handler
    async def clean(self, text: str, ctx: WorkflowContext[str]) -> None:
        await ctx.send_message(text.strip().lower())

class WordCounter(Executor):
    def __init__(self):
        super().__init__(id="counter")

    @handler
    async def count(self, text: str, ctx: WorkflowContext[str]) -> None:
        words = text.split()
        await ctx.send_message({"text": text, "count": len(words), "words": words})

@executor(id="formatter")
async def formatter(data: dict, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output(f"'{data['text']}' has {data['count']} words: {data['words']}")

async def main():
    wf = Workflow()
    wf.add_node("clean", TextCleaner())
    wf.add_node("count", WordCounter())
    wf.add_node("format", formatter)

    wf.connect("clean", "count")
    wf.connect("count", "format")
    wf.set_entry_node("clean")
    wf.set_exit_node("format")

    events = await wf.run("  Hello World from Agent Framework  ")
    print(events.get_outputs())

asyncio.run(main())
```
