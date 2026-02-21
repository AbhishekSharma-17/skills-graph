# Workflows — Graph-Based Orchestration

## What is a Workflow

A workflow is a directed graph where nodes are **executors** (agents or functions) and edges define data flow. Use workflows when you need explicit control over execution order.

## Core Components

| Component | Description |
|---|---|
| **Workflow** | The graph container |
| **Executor** | A node — class-based or function-based |
| **WorkflowContext** | Passed to executors — for sending messages and yielding output |
| **Edges** | Connections between nodes |

## Executor Types

### Class-Based Executor

```python
from agent_framework.workflows import Executor, handler, WorkflowContext

class UpperCase(Executor):
    """Convert text to uppercase."""

    def __init__(self, id: str):
        super().__init__(id=id)

    @handler
    async def to_upper_case(self, text: str, ctx: WorkflowContext[str]) -> None:
        """Convert input to uppercase and forward to next node."""
        await ctx.send_message(text.upper())
```

### Function-Based Executor

```python
from agent_framework.workflows import executor, WorkflowContext
from typing import Never

@executor(id="reverse_text")
async def reverse_text(text: str, ctx: WorkflowContext[Never, str]) -> None:
    """Reverse string and yield as workflow output."""
    await ctx.yield_output(text[::-1])
```

## WorkflowContext Methods

| Method | Purpose | When to Use |
|---|---|---|
| `ctx.send_message(data)` | Send data to next connected node | Intermediate nodes |
| `ctx.yield_output(data)` | Yield final workflow output | Exit nodes |

### WorkflowContext Type Parameters

```python
# Intermediate node — receives str, sends to next node
ctx: WorkflowContext[str]

# Exit node — yields str output (Never = no forwarding)
ctx: WorkflowContext[Never, str]

# Both input and output types
ctx: WorkflowContext[str, str]
```

## Building a Workflow

### Step-by-Step

```python
from agent_framework.workflows import Workflow

# 1. Create workflow
workflow = Workflow()

# 2. Add nodes (executors)
workflow.add_node("upper", UpperCase("upper_case"))
workflow.add_node("reverse", reverse_text)

# 3. Connect nodes
workflow.connect("upper", "reverse")

# 4. Set entry and exit points
workflow.set_entry_node("upper")
workflow.set_exit_node("reverse")
```

### Run Workflow

```python
# Execute workflow
events = await workflow.run("hello world")

# Get outputs
outputs = events.get_outputs()
print(f"Output: {outputs}")  # "DLROW OLLEH"

# Get final state
final_state = events.get_final_state()
```

## Complete Example

```python
import asyncio
from agent_framework.workflows import Workflow, Executor, handler, executor, WorkflowContext
from typing import Never

# Class-based executor
class TextCleaner(Executor):
    def __init__(self):
        super().__init__(id="cleaner")

    @handler
    async def clean(self, text: str, ctx: WorkflowContext[str]) -> None:
        cleaned = text.strip().lower()
        await ctx.send_message(cleaned)

# Function-based executor
@executor(id="word_counter")
async def word_counter(text: str, ctx: WorkflowContext[Never, dict]) -> None:
    words = text.split()
    await ctx.yield_output({
        "text": text,
        "word_count": len(words),
        "words": words,
    })

# Build workflow
def create_pipeline():
    wf = Workflow()
    wf.add_node("clean", TextCleaner())
    wf.add_node("count", word_counter)
    wf.connect("clean", "count")
    wf.set_entry_node("clean")
    wf.set_exit_node("count")
    return wf

async def main():
    pipeline = create_pipeline()
    events = await pipeline.run("  Hello World from Agent Framework  ")
    outputs = events.get_outputs()
    print(outputs)
    # {'text': 'hello world from agent framework', 'word_count': 5, ...}

asyncio.run(main())
```

## Workflow Patterns

### Sequential Pipeline
```
Node A → Node B → Node C
```
```python
wf.connect("a", "b")
wf.connect("b", "c")
wf.set_entry_node("a")
wf.set_exit_node("c")
```

### Concurrent / Fan-Out
```
         → Node B →
Node A ─┤         ├─ Node D
         → Node C →
```
```python
wf.connect("a", "b")
wf.connect("a", "c")
wf.connect("b", "d")
wf.connect("c", "d")
```

### Conditional Branching
```python
# Executor that routes based on content
class Router(Executor):
    def __init__(self):
        super().__init__(id="router")

    @handler
    async def route(self, data: dict, ctx: WorkflowContext[dict]) -> None:
        if data.get("type") == "urgent":
            await ctx.send_message(data, target="urgent_handler")
        else:
            await ctx.send_message(data, target="normal_handler")
```

## Agent as Workflow Node

Wrap an agent as an executor in a workflow:

```python
class AgentExecutor(Executor):
    def __init__(self, agent, id: str):
        super().__init__(id=id)
        self.agent = agent

    @handler
    async def process(self, input_text: str, ctx: WorkflowContext[str]) -> None:
        session = self.agent.create_session()
        result = await self.agent.run(input_text, session=session)
        await ctx.send_message(result.text)

# Use in workflow
research_executor = AgentExecutor(research_agent, "researcher")
writer_executor = AgentExecutor(writer_agent, "writer")

wf = Workflow()
wf.add_node("research", research_executor)
wf.add_node("write", writer_executor)
wf.connect("research", "write")
```

## Workflow Rules

1. Exactly **one entry node** required (`set_entry_node`)
2. Exactly **one exit node** required (`set_exit_node`)
3. All nodes must be connected
4. Entry node receives the initial input from `workflow.run()`
5. Exit node must use `ctx.yield_output()` to produce workflow output
6. Intermediate nodes use `ctx.send_message()` to forward data

## When to Use Workflows vs Agents

| Scenario | Use |
|---|---|
| Single conversational task | Agent |
| Well-defined processing steps | Workflow |
| Need explicit control over order | Workflow |
| Multiple agents need to coordinate | Workflow |
| Dynamic tool selection | Agent |
| Both open-ended and structured | Agent inside Workflow |
