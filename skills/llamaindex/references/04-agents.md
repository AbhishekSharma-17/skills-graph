# Agents

> Source: [developers.llamaindex.ai — Agents](https://developers.llamaindex.ai/python/framework/understanding/agent/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [FunctionAgent](#functionagent)
- [ReActAgent](#reactagent)
- [Tool Creation](#tool-creation)
- [Pre-built Tools](#pre-built-tools)
- [Agent State](#agent-state)
- [Streaming](#streaming)
- [Human-in-the-Loop](#human-in-the-loop)
- [Structured Output](#structured-output)
- [Common Patterns](#common-patterns)

## Overview

An agent in LlamaIndex is an autonomous system powered by an LLM that receives a task and executes a series of steps toward solving it. At each step, the agent:

1. Evaluates the current state
2. Selects appropriate tools to call
3. Executes the chosen tool
4. Decides if the task is complete or needs more steps

LlamaIndex provides three agent types:

| Agent | Strategy | Best For |
|-------|----------|----------|
| `FunctionAgent` | Direct function/tool calling | Simple tool-use agents (recommended start) |
| `ReActAgent` | ReAct reasoning (thought → action → observation) | Complex reasoning chains |
| `CodeActAgent` | Code execution actions | Tasks requiring code generation |

## FunctionAgent

The simplest and most common agent type. Uses the LLM's native function-calling capability to select and invoke tools.

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

def search_database(query: str) -> str:
    """Search the product database and return matching results."""
    return f"Found 3 products matching '{query}'"

def calculate_discount(price: float, percent: float) -> float:
    """Calculate the discounted price given original price and discount percentage."""
    return price * (1 - percent / 100)

agent = FunctionAgent(
    tools=[search_database, calculate_discount],
    llm=OpenAI(model="gpt-4o-mini"),
    system_prompt="You are a helpful shopping assistant.",
)

import asyncio
response = asyncio.run(agent.run(user_msg="Find laptops under $1000 with 20% off"))
print(response)
```

Key parameters:
- `tools` — List of callable functions or `FunctionTool` objects
- `llm` — The LLM to power the agent
- `system_prompt` — Instructions guiding agent behavior
- `name` — Agent name (used in multi-agent systems)
- `can_handoff_to` — List of agent names this agent can delegate to
- `streaming` — Enable token streaming (default: True)

## ReActAgent

Uses the ReAct prompting strategy: Thought → Action → Observation loop.

```python
from llama_index.core.agent.workflow import ReActAgent

agent = ReActAgent(
    tools=[search_database, calculate_discount],
    llm=OpenAI(model="gpt-4o"),
    system_prompt="You are a research assistant. Think step by step.",
)

response = asyncio.run(agent.run(user_msg="Compare products A and B"))
```

ReActAgent is better when you need:
- Explicit reasoning traces
- Multi-step problem solving where order matters
- Models that don't support native function calling

## Tool Creation

### From Plain Functions

The simplest approach — LlamaIndex wraps the function automatically:

```python
def get_weather(city: str, unit: str = "celsius") -> str:
    """Get the current weather for a city.
    
    Args:
        city: The city name to get weather for.
        unit: Temperature unit, either 'celsius' or 'fahrenheit'.
    """
    return f"Weather in {city}: 22°{unit[0].upper()}, sunny"

agent = FunctionAgent(tools=[get_weather], llm=llm)
```

The agent uses:
- Function name → tool name
- Docstring → tool description (tells the LLM when to use it)
- Type hints → parameter schema
- Default values → optional parameters

### Using FunctionTool Explicitly

```python
from llama_index.core.tools import FunctionTool

def raw_search(q: str) -> str:
    return f"Results for {q}"

search_tool = FunctionTool.from_defaults(
    fn=raw_search,
    name="search",
    description="Search the knowledge base for relevant documents.",
)

agent = FunctionAgent(tools=[search_tool], llm=llm)
```

### Async Tools

```python
async def fetch_data(url: str) -> str:
    """Fetch data from a URL asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()

agent = FunctionAgent(tools=[fetch_data], llm=llm)
```

### Query Engine as Tool

Turn any index into an agent tool:

```python
from llama_index.core.tools import QueryEngineTool

query_engine = index.as_query_engine(similarity_top_k=5)
tool = QueryEngineTool.from_defaults(
    query_engine=query_engine,
    name="knowledge_base",
    description="Search the company knowledge base for policies and procedures.",
)

agent = FunctionAgent(tools=[tool], llm=llm)
```

## Pre-built Tools

LlamaHub provides ready-made tool specifications:

```bash
pip install llama-index-tools-google
pip install llama-index-tools-arxiv
```

```python
from llama_index.tools.google import GmailToolSpec

tool_spec = GmailToolSpec()
tools = tool_spec.to_tool_list()

agent = FunctionAgent(tools=tools, llm=llm)
```

Popular tool specs: Google (Gmail, Calendar, Search), Arxiv, Wikipedia, Wolfram Alpha, Slack, Notion.

## Agent State

Maintain state across agent interactions using `Context`:

```python
from llama_index.core.workflow import Context

agent = FunctionAgent(
    tools=[...],
    llm=llm,
    initial_state={"conversation_count": 0, "user_name": None},
)

ctx = Context(agent)

response = await agent.run(user_msg="My name is Alice", ctx=ctx)
response = await agent.run(user_msg="What's my name?", ctx=ctx)
```

### Accessing State in Tools

```python
async def save_note(ctx: Context, note: str) -> str:
    """Save a note to the agent's memory."""
    state = await ctx.get("state")
    notes = state.get("notes", [])
    notes.append(note)
    state["notes"] = notes
    await ctx.set("state", state)
    return f"Saved note: {note}"
```

The `ctx` parameter is automatically injected by the agent framework — the LLM never sees it.

## Streaming

### Token Streaming

```python
handler = agent.run(user_msg="Explain quantum computing")

async for event in handler.stream_events():
    if hasattr(event, "delta"):
        print(event.delta, end="", flush=True)

response = await handler
```

### Event Streaming

```python
from llama_index.core.agent.workflow import (
    ToolCall,
    ToolCallResult,
    AgentStream,
)

handler = agent.run(user_msg="Search for documents")

async for event in handler.stream_events():
    if isinstance(event, ToolCall):
        print(f"Calling tool: {event.tool_name}({event.tool_kwargs})")
    elif isinstance(event, ToolCallResult):
        print(f"Tool result: {event.tool_output}")
    elif isinstance(event, AgentStream):
        print(event.delta, end="")

response = await handler
```

## Human-in-the-Loop

Pause agent execution to request human approval:

```python
from llama_index.core.agent.workflow import (
    AgentWorkflow,
    FunctionAgent,
    HumanInput,
)

def dangerous_action(action: str) -> str:
    """Execute a potentially dangerous action that requires approval."""
    return f"Executed: {action}"

agent = FunctionAgent(
    tools=[dangerous_action],
    llm=llm,
    system_prompt="Always ask for confirmation before dangerous actions.",
)

workflow = AgentWorkflow(agents=[agent])

handler = workflow.run(user_msg="Delete all records")

async for event in handler.stream_events():
    if isinstance(event, HumanInput):
        human_response = input(f"Agent asks: {event.prompt}\nYour response: ")
        handler.ctx.send_event(HumanInput(response=human_response))
```

## Structured Output

Force agents to return structured Pydantic models:

```python
from pydantic import BaseModel

class ResearchResult(BaseModel):
    topic: str
    summary: str
    confidence: float
    sources: list[str]

agent = FunctionAgent(
    tools=[search_tool],
    llm=llm,
    system_prompt="You are a research assistant.",
    output_cls=ResearchResult,
)

response = await agent.run(user_msg="Research quantum computing")
```

## Common Patterns

### RAG Agent

Combine document retrieval with agent reasoning:

```python
from llama_index.core.tools import QueryEngineTool

doc_tool = QueryEngineTool.from_defaults(
    query_engine=index.as_query_engine(),
    name="docs",
    description="Search internal documentation.",
)

web_tool = FunctionTool.from_defaults(
    fn=search_web,
    name="web",
    description="Search the web for recent information.",
)

agent = FunctionAgent(
    tools=[doc_tool, web_tool],
    llm=OpenAI(model="gpt-4o"),
    system_prompt="Search docs first, then web if needed.",
)
```

### Conversational Agent with Memory

```python
ctx = Context(agent)

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    response = await agent.run(user_msg=user_input, ctx=ctx)
    print(f"Agent: {response}")
```

The `Context` automatically tracks conversation history across turns.
