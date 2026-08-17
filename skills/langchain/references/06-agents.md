# Agents

> Source: https://docs.langchain.com/oss/python/langchain/agents

## Table of Contents

- [Overview](#overview)
- [create_agent](#create_agent)
- [Agent State](#agent-state)
- [Invocation](#invocation)
- [Context Passing](#context-passing)
- [Middleware](#middleware)
- [Human-in-the-Loop](#human-in-the-loop)
- [Structured Output in Agents](#structured-output-in-agents)
- [Pre-built Agents](#pre-built-agents)
- [Common Patterns](#common-patterns)

## Overview

An agent is a model calling tools in a loop until a task is complete. The architecture follows **Agent = Model + Harness**, where the harness includes prompts, tools, middleware, and state management. LangChain's `create_agent` provides a minimal, highly configurable harness.

## create_agent

```python
from langchain.agents import create_agent

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",  # Provider:model string or model instance
    tools=[search, calculator],            # List of tools
    system_prompt="You are helpful.",       # System message
    response_format=None,                  # Structured output schema
    middleware=[],                          # Middleware hooks
    checkpointer=None,                     # State persistence
    store=None,                            # Long-term memory
    state_schema=None,                     # Custom state class
    context_schema=None,                   # Per-run context type
    name=None,                             # Agent name (for multi-agent)
)
```

### Model Specification

```python
# String format — provider:model
agent = create_agent(model="openai:gpt-4o", tools=[])
agent = create_agent(model="anthropic:claude-sonnet-4-6", tools=[])
agent = create_agent(model="google_genai:gemini-2.0-flash", tools=[])

# Model instance
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o", temperature=0)
agent = create_agent(model=model, tools=[])
```

### System Prompt

```python
from langchain_core.messages import SystemMessage

agent = create_agent(
    model="openai:gpt-4o",
    tools=[search],
    system_prompt="You are a research assistant. Always cite sources."
)

# Or with SystemMessage
agent = create_agent(
    model="openai:gpt-4o",
    tools=[search],
    system_prompt=SystemMessage("You are a research assistant.")
)
```

## Agent State

Every agent has `AgentState` holding conversation history:

```python
from langchain.agents import AgentState

# Default state has one field:
# messages: list[BaseMessage]  — Full conversation history (append-only)
```

### Custom State

```python
from langchain.agents import AgentState, create_agent

class MyState(AgentState):
    user_id: str
    call_count: int
    preferences: dict

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[],
    state_schema=MyState
)
```

## Invocation

### Basic

```python
result = agent.invoke({
    "messages": [{"role": "user", "content": "What's the weather in SF?"}]
})
print(result["messages"][-1].content)
```

### With Thread Persistence

```python
from langchain_core.utils.uuid import uuid7
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[],
    checkpointer=InMemorySaver()
)

config = {"configurable": {"thread_id": str(uuid7())}}

# First turn
result = agent.invoke(
    {"messages": [{"role": "user", "content": "My name is Alice"}]},
    config=config
)

# Second turn — remembers context
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    config=config
)
```

### Streaming

```python
stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "Search for AI news"}]},
    version="v3"
)

for kind, item in stream.interleave("messages", "tool_calls"):
    if kind == "messages":
        for token in item.text:
            print(token, end="", flush=True)
    elif kind == "tool_calls":
        print(f"\nCalling: {item.tool_name}({item.input})")
```

## Context Passing

Pass per-run data (user IDs, API keys, feature flags) via context:

```python
from dataclasses import dataclass

@dataclass
class Context:
    user_id: str
    locale: str = "en"

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[get_account_info],
    context_schema=Context,
    checkpointer=InMemorySaver()
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Show my account"}]},
    config={"configurable": {"thread_id": "t1"}},
    context=Context(user_id="user-123", locale="en")
)
```

Tools access context via `runtime.context`.

## Middleware

Composable hooks that customize agent behavior at specific lifecycle points.

### Model Retry

```python
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search],
    middleware=[
        ModelRetryMiddleware(max_retries=3),
        ToolRetryMiddleware(max_retries=2),
    ]
)
```

### PII Detection

```python
from langchain.agents.middleware import PIIMiddleware

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search],
    middleware=[PIIMiddleware("email")]
)
```

### Custom Model Middleware

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

@wrap_model_call
def log_model_calls(request: ModelRequest, handler):
    """Log every model invocation."""
    print(f"Model called with {len(request.messages)} messages")
    response = handler(request)
    print(f"Model responded with {len(response.tool_calls)} tool calls")
    return response

agent = create_agent(
    model="openai:gpt-4o",
    tools=[search],
    middleware=[log_model_calls]
)
```

### Custom Tool Middleware

```python
from langchain.agents.middleware import wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage

@wrap_tool_call
def audit_tool_calls(request: ToolCallRequest, handler) -> ToolMessage:
    """Audit every tool invocation."""
    print(f"Tool: {request.tool_call['name']}, Args: {request.tool_call['args']}")
    result = handler(request)
    print(f"Result: {result.content[:100]}")
    return result
```

## Human-in-the-Loop

Pause agent execution for human approval before specific actions:

```python
from langchain.agents.middleware import HumanInTheLoopMiddleware

agent = create_agent(
    model="openai:gpt-4o",
    tools=[search, write_file, delete_file],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={"write_file": True, "delete_file": True}
        )
    ],
    checkpointer=InMemorySaver()
)

config = {"configurable": {"thread_id": "t1"}}

# Agent will pause when it tries to call write_file or delete_file
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Create a report file"}]},
    config=config,
    stream_mode=["messages", "updates"]
):
    if chunk["type"] == "updates":
        for source, update in chunk["data"].items():
            if source == "__interrupt__":
                print("Agent paused for approval!")
```

### Resume After Approval

```python
from langgraph.types import Command

for chunk in agent.stream(
    Command(resume={interrupt_id: {"decisions": [{"type": "approve"}]}}),
    config=config,
    stream_mode=["messages", "updates"]
):
    pass
```

## Structured Output in Agents

```python
from pydantic import BaseModel, Field

class Analysis(BaseModel):
    summary: str = Field(description="Analysis summary")
    confidence: float = Field(ge=0, le=1)
    key_findings: list[str]

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search],
    response_format=Analysis
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Analyze AI market trends"}]
})
print(result["structured_response"])  # Analysis instance
```

## Pre-built Agents

### Deep Agents

Batteries-included agent with filesystem, summarization, subagents, and memory:

```python
from langchain.agents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search],
)
```

### Sub-Agents

Delegate subtasks to specialized agents:

```python
from deepagents.middleware.subagents import SubAgentMiddleware

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search],
    middleware=[
        SubAgentMiddleware(
            backend=backend,
            subagents=[{
                "name": "researcher",
                "description": "Searches and summarizes",
                "system_prompt": "Research and provide summaries",
                "tools": [search],
                "model": "anthropic:claude-sonnet-4-6"
            }]
        )
    ]
)
```

## Common Patterns

### ReAct Pattern

The default agent loop follows ReAct: observe → reason → act → repeat until done.

### Multi-Turn with Memory

```python
agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    checkpointer=InMemorySaver()
)

thread = {"configurable": {"thread_id": "conversation-1"}}

agent.invoke({"messages": [{"role": "user", "content": "I'm Alice"}]}, config=thread)
agent.invoke({"messages": [{"role": "user", "content": "Who am I?"}]}, config=thread)
```

### Agent with Store

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
agent = create_agent(
    model="openai:gpt-4o",
    tools=[save_preference, get_preference],
    store=store,
    checkpointer=InMemorySaver()
)
```
