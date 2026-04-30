# LangGraph — State Management

> Source: [docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api)

## Table of Contents

- [State Fundamentals](#state-fundamentals)
- [Schema Types](#schema-types)
- [Reducers](#reducers)
- [MessagesState](#messagesstate)
- [Input and Output Schemas](#input-and-output-schemas)
- [State Update Mechanics](#state-update-mechanics)
- [Private State and Internal Keys](#private-state-and-internal-keys)
- [Common Patterns](#common-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## State Fundamentals

State is the central data structure in LangGraph. It defines:
1. **Schema** — the shape of data flowing through the graph
2. **Reducers** — how updates from nodes are merged into existing state
3. **Default values** — initial values for state keys

Every node receives the full state as input and returns a partial update dict. The runtime applies each update through the key's reducer.

## Schema Types

### TypedDict (Recommended)

The most common and performant option:

```python
from typing import Annotated, TypedDict
from operator import add

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str
    step_count: int
```

### Dataclass

Supports default values:

```python
from dataclasses import dataclass, field

@dataclass
class AgentState:
    messages: Annotated[list, add_messages] = field(default_factory=list)
    context: str = ""
    step_count: int = 0
```

### Pydantic BaseModel

Adds runtime validation but with a performance cost:

```python
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    context: str = ""
    step_count: int = Field(default=0, ge=0)
```

**Performance note:** Pydantic validates recursively on every state update. Use TypedDict unless you need runtime validation.

## Reducers

Reducers control how node outputs merge into existing state. Without a reducer, the latest value overwrites the previous one.

### Default Behavior (Overwrite)

```python
class State(TypedDict):
    query: str       # Last write wins
    answer: str      # Last write wins

# Node returns {"query": "new"} → state["query"] becomes "new"
```

### Annotated Reducers

Use `typing.Annotated` to attach a reducer function:

```python
from typing import Annotated
from operator import add

class State(TypedDict):
    items: Annotated[list[str], add]  # Lists are concatenated
    count: int                         # Overwritten
```

### Built-in Reducers

| Reducer | Behavior | Use Case |
|---------|----------|----------|
| `operator.add` | Concatenate lists/strings | Collecting items |
| `add_messages` | Append messages with ID-based dedup | Chat history |
| Custom function | Any `(old, new) -> merged` | Domain-specific logic |

### Custom Reducers

```python
def max_reducer(current: int, update: int) -> int:
    return max(current, update)

def merge_dicts(current: dict, update: dict) -> dict:
    return {**current, **update}

class State(TypedDict):
    high_score: Annotated[int, max_reducer]
    metadata: Annotated[dict, merge_dicts]
```

### The `add_messages` Reducer

The most important built-in reducer for chat applications:

```python
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
```

**Behavior:**
- Appends new messages to the list
- If a message has an `id` matching an existing message, it **replaces** it
- Handles deserialization from dicts to LangChain message objects
- Supports `RemoveMessage` for deleting messages

```python
from langchain_core.messages import RemoveMessage

def trim_messages(state: State) -> dict:
    # Remove all but the last 10 messages
    to_remove = state["messages"][:-10]
    return {"messages": [RemoveMessage(id=m.id) for m in to_remove]}
```

## MessagesState

A pre-built state for common chat applications:

```python
from langgraph.graph import MessagesState

# Equivalent to:
# class MessagesState(TypedDict):
#     messages: Annotated[list[AnyMessage], add_messages]

graph = StateGraph(MessagesState)
```

**Extending MessagesState:**

```python
class MyState(MessagesState):
    context: str
    user_id: str
    step: int
```

## Input and Output Schemas

Control what the graph accepts as input and returns as output:

```python
class InputState(TypedDict):
    question: str

class OutputState(TypedDict):
    answer: str
    confidence: float

class FullState(TypedDict):
    question: str
    answer: str
    confidence: float
    intermediate_steps: list
    scratch_pad: str

graph = StateGraph(FullState, input=InputState, output=OutputState)
```

- **Input schema:** Only these keys are accepted from `invoke()`
- **Output schema:** Only these keys are returned from `invoke()`
- **Full state:** All keys available inside nodes

## State Update Mechanics

### How Updates Flow

```python
# Starting state: {"count": 0, "items": []}

# Node A returns: {"count": 5, "items": ["a"]}
# State becomes:  {"count": 5, "items": ["a"]}  (count overwritten, items reduced)

# Node B returns: {"items": ["b"]}
# State becomes:  {"count": 5, "items": ["a", "b"]}  (only items updated)
```

### Multiple Nodes in Same Super-Step

When parallel nodes update the same key, the reducer resolves conflicts:

```python
class State(TypedDict):
    results: Annotated[list[str], add]

# Node A returns: {"results": ["from_a"]}
# Node B returns: {"results": ["from_b"]}
# Both run in same super-step
# State becomes: {"results": ["from_a", "from_b"]}
```

**Without a reducer, parallel writes to the same key will raise an error.**

## Private State and Internal Keys

Keep internal data out of the graph's public interface:

```python
class PublicState(TypedDict):
    question: str
    answer: str

class PrivateState(PublicState):
    _retrieval_results: list  # Convention: prefix with _
    _llm_cache: dict

graph = StateGraph(PrivateState, input=PublicState, output=PublicState)
```

Or use the input/output schema approach for strict separation.

## Common Patterns

### Accumulating Results

```python
class State(TypedDict):
    queries: list[str]
    results: Annotated[list[dict], add]

def search_node(state: State) -> dict:
    new_results = [search(q) for q in state["queries"]]
    return {"results": new_results}
```

### Counter Pattern

```python
def increment_reducer(current: int, update: int) -> int:
    return current + update

class State(TypedDict):
    step_count: Annotated[int, increment_reducer]

def my_node(state: State) -> dict:
    return {"step_count": 1}  # Increments by 1 each time
```

### Conditional State Updates

```python
def my_node(state: State) -> dict:
    updates = {}
    if state["needs_context"]:
        updates["context"] = fetch_context(state["query"])
    updates["status"] = "processed"
    return updates
```

## Common Pitfalls

1. **Mutating state in-place** — Always return new dicts. Never do `state["items"].append(x)`.
2. **Missing reducer for parallel writes** — Two nodes writing the same key in one super-step without a reducer raises `InvalidUpdateError`.
3. **Non-serializable values** — State must be JSON-serializable for checkpointing. No functions, generators, or class instances.
4. **Overly large state** — Don't store entire documents in state. Use references or a store.
5. **Using Pydantic for high-throughput** — TypedDict is significantly faster. Reserve Pydantic for when you need validation.

---

> **Related:** [01-graph-api.md](01-graph-api.md) for building graphs, [05-memory.md](05-memory.md) for persistent memory beyond state
