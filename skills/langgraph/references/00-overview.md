# LangGraph — Overview & Setup

> Source: [docs.langchain.com/oss/python/langgraph](https://docs.langchain.com/oss/python/langgraph/overview) | Package: `langgraph` v1.x

## Table of Contents

- [What Is LangGraph](#what-is-langgraph)
- [When to Use LangGraph](#when-to-use-langgraph)
- [Core Architecture](#core-architecture)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Graph API vs Functional API](#graph-api-vs-functional-api)
- [Ecosystem](#ecosystem)
- [Key Concepts at a Glance](#key-concepts-at-a-glance)
- [Common Pitfalls](#common-pitfalls)

---

## What Is LangGraph

LangGraph is an agent orchestration framework for building stateful, multi-actor AI applications modeled as directed graphs. Built by the LangChain team, it provides:

- **Durable execution** — agents persist through failures and can resume from checkpoints
- **Human-in-the-loop** — pause execution, inspect state, get human approval, then continue
- **Comprehensive memory** — short-term (thread-scoped) and long-term (cross-thread) memory
- **Streaming** — token-by-token output, state updates, and custom data streams
- **Debugging** — time-travel debugging via LangSmith integration

LangGraph has 30.9k+ GitHub stars, is MIT-licensed, and powers production agent systems at scale.

## When to Use LangGraph

**Use LangGraph when you need:**
- Agents that call tools in loops with conditional branching
- Multi-step workflows with state that persists across interactions
- Human approval gates in automated pipelines
- Multi-agent systems with supervisor or peer-to-peer coordination
- Complex routing logic beyond simple linear chains

**Don't use LangGraph when:**
- A simple prompt → response is sufficient (use LangChain directly)
- You need a no-code agent builder (consider LangFlow or Flowise)
- Your workflow is purely synchronous with no branching (a simple function suffices)

## Core Architecture

LangGraph models agent workflows as **directed graphs** where:

```
Nodes = Functions that process and update state
Edges = Transitions between nodes (static or conditional)
State = Typed data that flows through the graph
```

Execution follows a **message-passing** model in discrete **super-steps**:
1. A node receives the current state
2. It performs computation (LLM calls, tool execution, etc.)
3. It returns state updates
4. The runtime applies updates via reducers and routes to the next node(s)
5. Parallel nodes execute simultaneously within a single super-step

```
START → node_a → [conditional] → node_b → END
                               → node_c → END
```

## Installation

```bash
# Core (required)
pip install -U langgraph

# Prebuilt agents (ReAct, etc.)
pip install -U langgraph-prebuilt

# Checkpoint backends (pick based on environment)
pip install langgraph-checkpoint-sqlite    # Local/dev
pip install langgraph-checkpoint-postgres  # Production

# LLM providers (pick one or more)
pip install langchain-openai
pip install langchain-anthropic
pip install langchain-google-genai

# Full dev setup
pip install langgraph langgraph-prebuilt langgraph-checkpoint-sqlite langchain-openai
```

**With uv:**
```bash
uv add langgraph langgraph-prebuilt langchain-anthropic
```

## Quickstart

### Minimal Chat Agent

```python
from typing import Annotated, TypedDict
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

model = ChatAnthropic(model="claude-sonnet-4-20250514")

def chatbot(state: State):
    return {"messages": [model.invoke(state["messages"])]}

graph = StateGraph(State)
graph.add_node("chatbot", chatbot)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

app = graph.compile()
result = app.invoke({"messages": [{"role": "user", "content": "Hello!"}]})
print(result["messages"][-1].content)
```

### Agent with Tools

```python
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"It's sunny in {city}!"

agent = create_react_agent(
    model=ChatAnthropic(model="claude-sonnet-4-20250514"),
    tools=[get_weather],
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in Paris?"}]}
)
```

### With Persistence

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke({"messages": [{"role": "user", "content": "Hi!"}]}, config)
# State is now persisted — next invocation with same thread_id continues
```

## Graph API vs Functional API

LangGraph offers two ways to define workflows:

| Aspect | Graph API | Functional API |
|--------|-----------|----------------|
| **Abstraction** | `StateGraph` with nodes and edges | `@entrypoint` + `@task` decorators |
| **Best for** | Complex routing, multi-agent, visual debugging | Linear workflows, minimal boilerplate |
| **State** | Explicit schema with reducers | Implicit via function arguments |
| **Visualization** | Full graph visualization | Limited |
| **Learning curve** | Higher — graph concepts required | Lower — feels like regular Python |
| **Streaming** | All modes supported | All modes supported |
| **Persistence** | Via checkpointer on compile | Via checkpointer on decorator |

**Rule of thumb:** Start with Graph API for agent systems. Use Functional API for simpler orchestration where you want LangGraph's persistence/streaming without the graph mental model.

## Ecosystem

| Component | Purpose |
|-----------|---------|
| `langgraph` | Core graph engine, state management, execution |
| `langgraph-prebuilt` | Ready-made agents (ReAct), tool nodes |
| `langgraph-checkpoint-*` | Persistence backends (SQLite, Postgres, etc.) |
| `langchain-core` | Base abstractions (messages, tools, runnables) |
| `langchain-*` | LLM provider integrations (OpenAI, Anthropic, etc.) |
| **LangSmith** | Observability, tracing, evaluation, deployment |
| **LangGraph Platform** | Managed deployment infrastructure |

## Key Concepts at a Glance

| Concept | Description |
|---------|-------------|
| **StateGraph** | Main class for defining graph structure with typed state |
| **Node** | A function that receives state and returns updates |
| **Edge** | Connection between nodes (static or conditional) |
| **Reducer** | Function that merges state updates (e.g., `add_messages`) |
| **Checkpointer** | Persistence backend for saving state snapshots |
| **Thread** | An isolated conversation/execution identified by `thread_id` |
| **Super-step** | One round of parallel node execution in the graph |
| **Interrupt** | Pauses execution for human input, resumes via `Command` |
| **Command** | Object for combining state updates with control flow |
| **Send** | Object for dynamic fan-out (map-reduce patterns) |

## Common Pitfalls

1. **Forgetting to compile** — `StateGraph` must be compiled before use: `app = graph.compile()`
2. **Missing checkpointer for interrupts** — Human-in-the-loop requires a checkpointer
3. **Exceeding recursion limit** — Default is 1000 steps; infinite loops will hit this. Set `recursion_limit` in config
4. **State mutations** — Never mutate state in-place; always return new state dicts from nodes
5. **Missing thread_id** — Persistence requires `{"configurable": {"thread_id": "..."}}` in config
6. **Non-serializable state** — All state values must be JSON-serializable for checkpointing
7. **Confusing LangChain chains with LangGraph** — LangGraph is for stateful agents; LangChain is for composable prompt chains

---

> **Related:** [01-graph-api.md](01-graph-api.md) for StateGraph details, [03-functional-api.md](03-functional-api.md) for the alternative API
