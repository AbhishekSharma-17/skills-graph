# Memory & Persistence

> Source: https://docs.langchain.com/oss/python/langchain/memory

## Table of Contents

- [Overview](#overview)
- [Checkpointers](#checkpointers)
- [Thread Management](#thread-management)
- [Stores (Long-term Memory)](#stores-long-term-memory)
- [Message History Management](#message-history-management)
- [Conversation Memory Patterns](#conversation-memory-patterns)
- [Common Patterns](#common-patterns)

## Overview

LangChain provides two levels of memory for agents:

1. **Short-term (Checkpointers)** — Conversation history persisted per thread. Messages accumulate across turns. Backed by in-memory, SQLite, or Postgres.
2. **Long-term (Stores)** — Persistent key-value storage for user preferences, facts, and cross-conversation data. Accessible from tools via `ToolRuntime`.

## Checkpointers

Checkpointers persist agent state between invocations, enabling multi-turn conversations.

### InMemorySaver

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    checkpointer=InMemorySaver()
)
```

State is lost when the process exits. Suitable for development and testing.

### SQLite Saver

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    checkpointer=checkpointer
)
```

### Postgres Saver

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/mydb"
)

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    checkpointer=checkpointer
)
```

## Thread Management

Each conversation is identified by a `thread_id`. The same thread preserves full message history.

### Creating a Thread

```python
from langchain_core.utils.uuid import uuid7

thread_id = str(uuid7())
config = {"configurable": {"thread_id": thread_id}}
```

### Multi-Turn Conversation

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    checkpointer=InMemorySaver()
)

config = {"configurable": {"thread_id": "conversation-1"}}

# Turn 1
result = agent.invoke(
    {"messages": [{"role": "user", "content": "My name is Alice"}]},
    config=config
)
print(result["messages"][-1].content)

# Turn 2 — agent remembers the name
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    config=config
)
print(result["messages"][-1].content)  # "Your name is Alice"
```

### Multiple Threads

```python
thread_alice = {"configurable": {"thread_id": "alice-thread"}}
thread_bob = {"configurable": {"thread_id": "bob-thread"}}

agent.invoke(
    {"messages": [{"role": "user", "content": "I'm Alice"}]},
    config=thread_alice
)
agent.invoke(
    {"messages": [{"role": "user", "content": "I'm Bob"}]},
    config=thread_bob
)
```

### Get Thread State

```python
state = agent.get_state(config)
print(state.values["messages"])
```

### Update Thread State

```python
from langchain_core.messages import HumanMessage

agent.update_state(
    config,
    {"messages": [HumanMessage("Injected message")]}
)
```

## Stores (Long-term Memory)

Key-value stores persist data across threads and conversations.

### InMemoryStore

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

agent = create_agent(
    model="openai:gpt-4o",
    tools=[save_fact, get_fact],
    store=store,
    checkpointer=InMemorySaver()
)
```

### Store Operations

```python
store.put(("users",), "alice", {"name": "Alice", "role": "engineer"})

item = store.get(("users",), "alice")
print(item.value)  # {"name": "Alice", "role": "engineer"}

items = store.search(("users",))
for item in items:
    print(f"{item.key}: {item.value}")

store.delete(("users",), "alice")
```

### Namespaced Storage

```python
store.put(("users", "alice", "preferences"), "theme", {"value": "dark"})
store.put(("users", "alice", "preferences"), "lang", {"value": "en"})

store.put(("users", "bob", "preferences"), "theme", {"value": "light"})
```

### Accessing Store from Tools

```python
from langchain.tools import tool, ToolRuntime

@tool
def remember_fact(key: str, value: str, runtime: ToolRuntime) -> str:
    """Remember a fact about the user."""
    store = runtime.store
    store.put(("facts",), key, {"value": value})
    return f"Remembered: {key} = {value}"

@tool
def recall_fact(key: str, runtime: ToolRuntime) -> str:
    """Recall a previously stored fact."""
    store = runtime.store
    item = store.get(("facts",), key)
    return item.value["value"] if item else "Not found"
```

## Message History Management

### trim_messages

Keep conversation history within token limits:

```python
from langchain_core.messages import trim_messages

trimmed = trim_messages(
    messages,
    max_tokens=4000,
    token_counter=model,
    strategy="last",
    start_on="human",
    include_system=True,
)
```

| Parameter | Description |
|-----------|-------------|
| `max_tokens` | Maximum allowed tokens |
| `strategy` | `"last"` (keep recent) or `"first"` (keep oldest) |
| `start_on` | Ensure result starts with this type (`"human"`) |
| `include_system` | Always preserve system message |
| `token_counter` | Model or function for counting tokens |

### filter_messages

```python
from langchain_core.messages import filter_messages

recent_human = filter_messages(messages, include_types=["human"])
no_tools = filter_messages(messages, exclude_types=["tool"])
```

### merge_message_runs

Combine consecutive same-type messages:

```python
from langchain_core.messages import merge_message_runs

merged = merge_message_runs(messages)
```

### RemoveMessage

Remove specific messages from agent state:

```python
from langchain_core.messages import RemoveMessage

remove = RemoveMessage(id="msg_to_remove")
```

## Conversation Memory Patterns

### Summarization Memory

Summarize old messages to save context window space:

```python
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[
        SummarizationMiddleware(
            model="openai:gpt-4o-mini",
            max_messages=20,
        )
    ],
    checkpointer=InMemorySaver()
)
```

### Window Memory

Keep only the last N message pairs:

```python
def window_memory(messages, window_size=10):
    system = [m for m in messages if m.type == "system"]
    recent = messages[-window_size * 2:]
    return system + recent
```

### Token-Based Trimming in Chains

```python
from langchain_core.runnables import RunnablePassthrough

chain = (
    RunnablePassthrough.assign(
        messages=lambda x: trim_messages(
            x["messages"],
            max_tokens=4000,
            token_counter=model,
            strategy="last",
            include_system=True,
        )
    )
    | prompt
    | model
)
```

## Common Patterns

### Chat with Memory

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[],
    system_prompt="You are a helpful assistant. Remember user preferences.",
    checkpointer=InMemorySaver()
)

thread = {"configurable": {"thread_id": "chat-1"}}
agent.invoke({"messages": [{"role": "user", "content": "I prefer dark mode"}]}, config=thread)
agent.invoke({"messages": [{"role": "user", "content": "What's my preference?"}]}, config=thread)
```

### Agent with Both Memory Types

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

agent = create_agent(
    model="openai:gpt-4o",
    tools=[remember_fact, recall_fact],
    checkpointer=InMemorySaver(),  # Short-term
    store=InMemoryStore(),          # Long-term
)
```
