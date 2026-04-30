# LangGraph — Prebuilt Agents

> Source: [reference.langchain.com/python/langgraph.prebuilt](https://reference.langchain.com/python/langgraph.prebuilt/chat_agent_executor/create_react_agent)

## Table of Contents

- [Overview](#overview)
- [create_react_agent](#create_react_agent)
- [Configuration Options](#configuration-options)
- [Custom System Prompts](#custom-system-prompts)
- [Adding Persistence](#adding-persistence)
- [Human-in-the-Loop with Prebuilt Agents](#human-in-the-loop-with-prebuilt-agents)
- [Customizing Agent Behavior](#customizing-agent-behavior)
- [Extending Prebuilt Agents](#extending-prebuilt-agents)
- [When to Use Prebuilt vs Custom](#when-to-use-prebuilt-vs-custom)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

`langgraph-prebuilt` provides ready-made agent architectures so you don't have to build the graph from scratch. The primary offering is the **ReAct agent** — an agent that alternates between reasoning (calling the LLM) and acting (executing tools) until it has enough information to respond.

```bash
pip install langgraph-prebuilt
```

## create_react_agent

The main entry point for creating a tool-calling agent:

```python
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

agent = create_react_agent(
    model=ChatAnthropic(model="claude-sonnet-4-20250514"),
    tools=[search, calculator],
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "What is 42 * 17?"}]
})
print(result["messages"][-1].content)
```

### How It Works

```
START → agent (LLM) → [has tool_calls?] → tools (execute) → agent → ...
                     → [no tool_calls]  → END
```

The agent loops between calling the LLM and executing tools until the LLM produces a response without tool calls (the stopping condition).

## Configuration Options

```python
agent = create_react_agent(
    model=model,
    tools=tools,
    
    # System prompt
    prompt="You are a helpful research assistant.",
    
    # Persistence
    checkpointer=InMemorySaver(),
    
    # Long-term memory
    store=InMemoryStore(),
    
    # Interrupt before tool execution
    interrupt_before=["tools"],
    
    # Interrupt after tool execution
    interrupt_after=["tools"],
    
    # Custom state schema
    state_schema=CustomState,
    
    # Recursion limit (max loops)
    recursion_limit=50,
    
    # Response format (structured output)
    response_format=MyResponseModel,
)
```

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `BaseChatModel` | LLM with tool-calling support |
| `tools` | `list[Tool]` | Available tools for the agent |
| `prompt` | `str \| ChatPromptTemplate` | System instructions |
| `checkpointer` | `BaseCheckpointSaver` | Enable persistence and HITL |
| `store` | `BaseStore` | Long-term memory store |
| `interrupt_before` | `list[str]` | Pause before these nodes |
| `interrupt_after` | `list[str]` | Pause after these nodes |
| `state_schema` | `Type` | Custom state (extends MessagesState) |
| `response_format` | `Type` | Structured output schema |
| `recursion_limit` | `int` | Max tool-calling loops |

## Custom System Prompts

### Static Prompt

```python
agent = create_react_agent(
    model=model,
    tools=tools,
    prompt="You are a financial analyst. Always cite your sources. "
           "Use the search tool to find current market data.",
)
```

### Dynamic Prompt (Function)

```python
from langchain_core.prompts import ChatPromptTemplate

def get_prompt(state):
    system = f"You are helping user {state.get('user_name', 'unknown')}. "
    system += "Today's date is 2026-04-30."
    return [{"role": "system", "content": system}] + state["messages"]

agent = create_react_agent(
    model=model,
    tools=tools,
    prompt=get_prompt,
)
```

### With Chat Template

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are {role}. Focus on {domain}."),
    ("placeholder", "{messages}"),
])

agent = create_react_agent(
    model=model,
    tools=tools,
    prompt=prompt,
)

agent.invoke({
    "messages": [{"role": "user", "content": "Help me"}],
    "role": "a data scientist",
    "domain": "machine learning",
})
```

## Adding Persistence

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_react_agent(
    model=model,
    tools=tools,
    checkpointer=InMemorySaver(),
)

config = {"configurable": {"thread_id": "session-1"}}

# Multi-turn conversation
agent.invoke({"messages": [{"role": "user", "content": "My name is Alice"}]}, config)
agent.invoke({"messages": [{"role": "user", "content": "What's my name?"}]}, config)
# Agent remembers: "Your name is Alice"
```

## Human-in-the-Loop with Prebuilt Agents

### Approve Tool Calls

```python
agent = create_react_agent(
    model=model,
    tools=tools,
    checkpointer=InMemorySaver(),
    interrupt_before=["tools"],  # Pause before tool execution
)

config = {"configurable": {"thread_id": "t1"}}

# Agent decides to call a tool, pauses before execution
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Search for AI news"}]},
    config,
)

# Inspect what tool the agent wants to call
state = agent.get_state(config)
print(state.values["messages"][-1].tool_calls)

# Approve — resume execution
result = agent.invoke(None, config)
```

### Reject and Redirect

```python
from langchain_core.messages import ToolMessage

state = agent.get_state(config)
last_msg = state.values["messages"][-1]

# Reject the tool call — provide a fake tool response
agent.update_state(
    config,
    {
        "messages": [
            ToolMessage(
                content="Tool call rejected by user. Please try a different approach.",
                tool_call_id=last_msg.tool_calls[0]["id"],
            )
        ]
    },
    as_node="tools",
)

# Resume — agent will see the rejection and adjust
result = agent.invoke(None, config)
```

## Customizing Agent Behavior

### Custom State

```python
class ResearchState(MessagesState):
    sources: Annotated[list[str], operator.add]
    confidence: float

agent = create_react_agent(
    model=model,
    tools=tools,
    state_schema=ResearchState,
)
```

### Structured Output

```python
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    summary: str
    confidence: float
    key_findings: list[str]

agent = create_react_agent(
    model=model,
    tools=tools,
    response_format=AnalysisResult,
)

result = agent.invoke({"messages": [{"role": "user", "content": "Analyze market trends"}]})
# result["messages"][-1] contains structured AnalysisResult
```

## Extending Prebuilt Agents

### Adding Pre/Post Processing Nodes

```python
# Get the prebuilt graph and add custom nodes
agent = create_react_agent(model=model, tools=tools)

# The prebuilt agent is a compiled graph
# For extension, build a wrapper graph:

wrapper = StateGraph(MessagesState)
wrapper.add_node("preprocess", preprocess_node)
wrapper.add_node("agent", agent)  # Use prebuilt as a subgraph
wrapper.add_node("postprocess", postprocess_node)

wrapper.add_edge(START, "preprocess")
wrapper.add_edge("preprocess", "agent")
wrapper.add_edge("agent", "postprocess")
wrapper.add_edge("postprocess", END)

app = wrapper.compile()
```

### Adding Memory to Prebuilt

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

agent = create_react_agent(
    model=model,
    tools=tools,
    checkpointer=InMemorySaver(),
    store=store,
)

# Tools can access the store
@tool
def save_note(content: str, config: RunnableConfig, store: BaseStore) -> str:
    """Save a note for later reference."""
    user_id = config["configurable"]["user_id"]
    store.put(("users", user_id, "notes"), str(uuid4()), {"content": content})
    return "Note saved"
```

## When to Use Prebuilt vs Custom

| Scenario | Recommendation |
|----------|---------------|
| Simple tool-calling agent | `create_react_agent` |
| Agent with human approval gates | `create_react_agent` + `interrupt_before` |
| Multi-agent orchestration | Custom `StateGraph` |
| Complex routing logic | Custom `StateGraph` |
| Prototype / POC | `create_react_agent` |
| Non-standard loop patterns | Custom `StateGraph` |
| Agent with subgraphs | Custom `StateGraph` |
| RAG + tools agent | `create_react_agent` (usually sufficient) |

## Common Pitfalls

1. **Using a model without tool-calling** — Not all models support tool-calling. Check the provider docs.
2. **Tools without docstrings** — The agent can't understand what a tool does without a description.
3. **Infinite tool loops** — Set `recursion_limit` to prevent runaway agents.
4. **Forgetting checkpointer for HITL** — `interrupt_before`/`interrupt_after` require a checkpointer.
5. **Expecting graph customization** — Prebuilt agents have a fixed structure. For custom graphs, build with `StateGraph`.

---

> **Related:** [08-tool-integration.md](08-tool-integration.md) for tool definition, [10-multi-agent.md](10-multi-agent.md) for multi-agent systems
