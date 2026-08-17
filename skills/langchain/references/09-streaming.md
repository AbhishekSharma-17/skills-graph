# Streaming

> Source: https://docs.langchain.com/oss/python/langchain/streaming

## Table of Contents

- [Overview](#overview)
- [Stream Modes](#stream-modes)
- [Token Streaming](#token-streaming)
- [Agent Progress Streaming](#agent-progress-streaming)
- [Event Streaming (v3)](#event-streaming-v3)
- [Custom Updates](#custom-updates)
- [Multi-Mode Streaming](#multi-mode-streaming)
- [Reasoning Token Streaming](#reasoning-token-streaming)
- [Streaming Tool Calls](#streaming-tool-calls)
- [Sub-Agent Streaming](#sub-agent-streaming)
- [LCEL Chain Streaming](#lcel-chain-streaming)

## Overview

Streaming surfaces real-time updates from LLM operations, improving perceived latency. LangChain supports streaming at every level — individual model calls, LCEL chains, and agent loops. For new applications, event streaming (v3) with typed projections is recommended.

## Stream Modes

| Mode | Purpose | Output |
|------|---------|--------|
| `updates` | State updates after each agent step | Dict with node → state |
| `messages` | LLM tokens as they generate | Tuple of (token, metadata) |
| `custom` | User-defined signals from tools | Custom data via stream writer |

## Token Streaming

### Chat Model Streaming

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o")

for chunk in model.stream("Write a haiku about Python"):
    print(chunk.content, end="", flush=True)
```

### Async Streaming

```python
async for chunk in model.astream("Write a haiku about Python"):
    print(chunk.content, end="", flush=True)
```

### Combining Chunks

```python
full = None
for chunk in model.stream("Hello"):
    full = chunk if full is None else full + chunk

print(full.content)
print(full.usage_metadata)
```

## Agent Progress Streaming

Stream state updates as the agent processes:

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="openai:gpt-4o",
    tools=[search],
    checkpointer=InMemorySaver()
)

config = {"configurable": {"thread_id": "t1"}}

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Search for AI news"}]},
    config=config,
    stream_mode="updates",
    version="v2"
):
    source = list(chunk["data"].keys())[0]
    print(f"Step: {source}")
```

## Event Streaming (v3)

The recommended API for new applications. Provides typed projections for text, reasoning, and tool calls:

```python
stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "What is AI?"}]},
    version="v3"
)

for kind, item in stream.interleave("messages", "tool_calls"):
    if kind == "messages":
        for token in item.text:
            print(token, end="", flush=True)
    elif kind == "tool_calls":
        print(f"\nTool: {item.tool_name}({item.input})")
```

### Text-Only Streaming

```python
stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "Hello"}]},
    version="v3"
)

for message in stream.messages:
    for token in message.text:
        print(token, end="", flush=True)
```

## Custom Updates

Send progress signals from tools using stream writer:

```python
from langchain.tools import tool, ToolRuntime

@tool
def process_data(query: str, runtime: ToolRuntime) -> str:
    """Process data with progress updates."""
    writer = runtime.stream_writer
    writer("Starting search...")
    writer("Analyzing results...")
    writer("Formatting output...")
    return "Processing complete"
```

Or with `get_stream_writer`:

```python
from langgraph.config import get_stream_writer

@tool
def long_task(query: str) -> str:
    """Run a long task with updates."""
    writer = get_stream_writer()
    writer({"step": 1, "status": "loading"})
    writer({"step": 2, "status": "processing"})
    return "Done"
```

Consume custom updates:

```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Process data"}]},
    stream_mode="custom",
    version="v2"
):
    if chunk["type"] == "custom":
        print(f"Progress: {chunk['data']}")
```

## Multi-Mode Streaming

Combine multiple stream modes in one call:

```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Search and analyze"}]},
    stream_mode=["updates", "messages", "custom"],
    version="v2"
):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        print(f"Token: {token.content}", end="")
    elif chunk["type"] == "updates":
        print(f"\nStep update: {list(chunk['data'].keys())}")
    elif chunk["type"] == "custom":
        print(f"\nCustom: {chunk['data']}")
```

Each chunk is a `StreamPart` dict with `type`, `ns`, and `data` keys.

## Reasoning Token Streaming

Stream model thinking/reasoning tokens (Claude extended thinking, o1):

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(
    model="claude-sonnet-4-6",
    thinking={"type": "enabled", "budget_tokens": 5000}
)
agent = create_agent(model=model, tools=[search])

stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "Solve this complex problem"}]},
    version="v3"
)

for message in stream.messages:
    for token in message.reasoning:
        print(f"[thinking] {token}", end="")
    for token in message.text:
        print(token, end="", flush=True)
```

## Streaming Tool Calls

Access incremental tool call arguments and completed parsed calls:

```python
for chunk in agent.stream(
    {"messages": [input_message]},
    stream_mode=["messages", "updates"],
    version="v2"
):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        if hasattr(token, "text") and token.text:
            print(token.text, end="|")
    elif chunk["type"] == "updates":
        for source, update in chunk["data"].items():
            if source == "model" and update.get("messages"):
                msg = update["messages"][-1]
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"\nTool call: {tc['name']}({tc['args']})")
```

## Sub-Agent Streaming

Disambiguate sources in multi-agent systems:

```python
weather_agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather],
    name="weather_agent"
)

supervisor = create_agent(
    model="openai:gpt-4o",
    tools=[call_weather_agent],
    name="supervisor"
)

for chunk in supervisor.stream(
    {"messages": [{"role": "user", "content": "What's the weather?"}]},
    stream_mode=["messages", "updates"],
    subgraphs=True,
    version="v2"
):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        agent_name = metadata.get("lc_agent_name", "unknown")
        print(f"[{agent_name}] {token.text}")
```

## LCEL Chain Streaming

LCEL chains support streaming end-to-end:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

chain = (
    ChatPromptTemplate.from_template("Tell me about {topic}")
    | ChatOpenAI(model="gpt-4o")
    | StrOutputParser()
)

for chunk in chain.stream({"topic": "Python"}):
    print(chunk, end="", flush=True)
```

### astream_events on Chains

```python
async for event in chain.astream_events({"topic": "AI"}, version="v2"):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="")
    elif event["event"] == "on_chain_end":
        print("\nChain complete")
```

### Disable Streaming

```python
model = ChatOpenAI(model="gpt-4o", streaming=False)
# or
model = ChatOpenAI(model="gpt-4o", disable_streaming=True)
```
