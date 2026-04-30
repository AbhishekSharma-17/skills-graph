# LangGraph — Graph API

> Source: [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api)

## Table of Contents

- [StateGraph Class](#stategraph-class)
- [Adding Nodes](#adding-nodes)
- [Adding Edges](#adding-edges)
- [Conditional Edges](#conditional-edges)
- [Compiling the Graph](#compiling-the-graph)
- [Invoking the Graph](#invoking-the-graph)
- [Special Constants](#special-constants)
- [Send and Map-Reduce](#send-and-map-reduce)
- [Command Object](#command-object)
- [Runtime Context](#runtime-context)
- [Node Caching](#node-caching)
- [Common Patterns](#common-patterns)

---

## StateGraph Class

`StateGraph` is the primary class for building LangGraph workflows. It's parameterized by a state schema that defines the data flowing through the graph.

```python
from langgraph.graph import StateGraph, START, END

class MyState(TypedDict):
    messages: list
    context: str

graph = StateGraph(MyState)
```

**Constructor parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `state_schema` | `Type` | TypedDict, dataclass, or Pydantic BaseModel defining state |
| `input` | `Type` | Optional input schema (subset of state) |
| `output` | `Type` | Optional output schema (subset of state) |
| `context_schema` | `Type` | Optional runtime context schema |

```python
class InputState(TypedDict):
    query: str

class OutputState(TypedDict):
    answer: str

class FullState(TypedDict):
    query: str
    answer: str
    intermediate: list

graph = StateGraph(FullState, input=InputState, output=OutputState)
```

## Adding Nodes

Nodes are Python functions registered with `add_node()`. They receive the current state and return state updates.

```python
def my_node(state: MyState) -> dict:
    return {"messages": state["messages"] + ["processed"]}

graph.add_node("processor", my_node)
```

**Node function signatures:**

```python
# Basic — receives state only
def node(state: MyState) -> dict:
    return {"key": "value"}

# With config — access thread_id, metadata, etc.
from langchain_core.runnables import RunnableConfig

def node(state: MyState, config: RunnableConfig) -> dict:
    thread_id = config["configurable"]["thread_id"]
    return {"key": "value"}

# With store — access long-term memory
from langgraph.store.base import BaseStore

def node(state: MyState, config: RunnableConfig, *, store: BaseStore) -> dict:
    memories = store.search(("user", config["configurable"]["user_id"]))
    return {"key": "value"}

# Async nodes
async def node(state: MyState) -> dict:
    result = await some_async_operation()
    return {"key": result}
```

**Node return values:**
- Return a dict with keys matching the state schema
- Only include keys you want to update (partial updates)
- Values are merged using the channel's reducer function
- Return `None` or `{}` for no-op nodes

## Adding Edges

### Static Edges

Direct connections between nodes ensuring sequential execution:

```python
graph.add_edge(START, "node_a")      # Entry point
graph.add_edge("node_a", "node_b")   # Sequential flow
graph.add_edge("node_b", END)        # Terminal
```

### Multiple Entry/Exit Points

```python
graph.add_edge(START, "fetch_data")
graph.add_edge(START, "fetch_config")  # Both run in parallel
graph.add_edge("fetch_data", "process")
graph.add_edge("fetch_config", "process")
graph.add_edge("process", END)
```

## Conditional Edges

Route dynamically based on state using `add_conditional_edges()`:

```python
def route_decision(state: MyState) -> str:
    if state["needs_review"]:
        return "review"
    return "publish"

graph.add_conditional_edges(
    "analyze",           # Source node
    route_decision,      # Routing function
    {                    # Optional: map return values to node names
        "review": "review_node",
        "publish": "publish_node",
    }
)
```

**Without explicit mapping** (return value must match node name):

```python
def router(state: MyState) -> str:
    if state["done"]:
        return END
    return "continue_processing"

graph.add_conditional_edges("check", router)
```

**Returning multiple destinations** (fan-out to parallel nodes):

```python
def router(state: MyState) -> list[str]:
    destinations = ["always_run"]
    if state["needs_review"]:
        destinations.append("review")
    return destinations

graph.add_conditional_edges("check", router)
```

## Compiling the Graph

Compilation validates the graph structure and prepares it for execution. **You must compile before invoking.**

```python
# Basic compile
app = graph.compile()

# With checkpointer for persistence
from langgraph.checkpoint.memory import InMemorySaver
app = graph.compile(checkpointer=InMemorySaver())

# With interrupts for human-in-the-loop
app = graph.compile(
    checkpointer=InMemorySaver(),
    interrupt_before=["review_node"],
    interrupt_after=["generate_node"],
)

# With caching
from langgraph.cache.memory import InMemoryCache
app = graph.compile(cache=InMemoryCache())
```

**Compile parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `checkpointer` | `BaseCheckpointSaver` | Enables persistence, required for interrupts |
| `interrupt_before` | `list[str]` | Pause before these nodes |
| `interrupt_after` | `list[str]` | Pause after these nodes |
| `cache` | `BaseCache` | Enable node-level result caching |
| `store` | `BaseStore` | Long-term memory store |

## Invoking the Graph

```python
config = {"configurable": {"thread_id": "my-thread"}}

# Synchronous
result = app.invoke({"messages": [...]}, config)

# Asynchronous
result = await app.ainvoke({"messages": [...]}, config)

# Streaming (sync)
for chunk in app.stream({"messages": [...]}, config):
    print(chunk)

# Streaming (async)
async for chunk in app.astream({"messages": [...]}, config):
    print(chunk)

# With recursion limit
result = app.invoke(
    {"messages": [...]},
    config={"recursion_limit": 50, "configurable": {"thread_id": "t1"}}
)
```

## Special Constants

```python
from langgraph.graph import START, END

START  # Virtual entry node — edges from START define where execution begins
END    # Virtual terminal node — edges to END define where execution stops
```

## Send and Map-Reduce

`Send` enables dynamic fan-out patterns where you spawn multiple instances of a node with different inputs:

```python
from langgraph.types import Send

def fan_out(state: MyState) -> list[Send]:
    return [
        Send("process_item", {"item": item})
        for item in state["items"]
    ]

graph.add_conditional_edges("splitter", fan_out)
```

Each `Send` creates an independent execution of the target node with its own state. Results are collected using the target node's reducer.

```python
# Full map-reduce example
class State(TypedDict):
    topics: list[str]
    summaries: Annotated[list[str], operator.add]

def generate_topics(state: State) -> dict:
    return {"topics": ["AI", "Web", "Cloud"]}

def summarize(state: State) -> dict:
    return {"summaries": [f"Summary of {state['topic']}"]}

def fan_out(state: State) -> list[Send]:
    return [Send("summarize", {"topic": t}) for t in state["topics"]]

graph = StateGraph(State)
graph.add_node("generate", generate_topics)
graph.add_node("summarize", summarize)
graph.add_conditional_edges("generate", fan_out)
graph.add_edge("summarize", END)
graph.add_edge(START, "generate")
```

## Command Object

`Command` combines state updates with control flow in a single return value:

```python
from langgraph.types import Command
from typing import Literal

def my_node(state: State) -> Command[Literal["next_a", "next_b"]]:
    if state["score"] > 0.8:
        return Command(update={"status": "approved"}, goto="next_a")
    return Command(update={"status": "needs_review"}, goto="next_b")
```

**Command parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `update` | `dict` | State updates to apply |
| `goto` | `str \| list[str] \| Send` | Next node(s) to execute |
| `resume` | `Any` | Value to resume from an interrupt |
| `graph` | `Command.PARENT` | Navigate to parent graph (for subgraphs) |

## Runtime Context

Inject runtime configuration without polluting state:

```python
from dataclasses import dataclass

@dataclass
class AppContext:
    llm_provider: str = "anthropic"
    temperature: float = 0.7

graph = StateGraph(State, context_schema=AppContext)

def my_node(state: State, config: RunnableConfig) -> dict:
    ctx = config["configurable"]["context"]
    # Use ctx.llm_provider, ctx.temperature
    return {"result": "..."}

app = graph.compile()
app.invoke(inputs, context=AppContext(llm_provider="openai"))
```

## Node Caching

Cache node results to avoid re-execution for identical inputs:

```python
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy

graph.add_node("expensive_op", my_func, cache_policy=CachePolicy(ttl=300))
app = graph.compile(cache=InMemoryCache())
```

## Common Patterns

### Chatbot with Tool Loop

```python
def should_continue(state: State) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

graph.add_node("agent", call_model)
graph.add_node("tools", tool_executor)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")
```

### Parallel Execution

```python
graph.add_edge(START, "fetch_a")
graph.add_edge(START, "fetch_b")
graph.add_edge("fetch_a", "merge")
graph.add_edge("fetch_b", "merge")
graph.add_edge("merge", END)
```

---

> **Related:** [02-state-management.md](02-state-management.md) for state schemas and reducers, [07-human-in-the-loop.md](07-human-in-the-loop.md) for interrupts
