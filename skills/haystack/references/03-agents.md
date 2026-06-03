# Haystack Agents

> Source: [docs.haystack.deepset.ai/docs/agents](https://docs.haystack.deepset.ai/docs/agents) | haystack-ai 2.30.0

## Table of Contents

- [What Are Agents](#what-are-agents)
- [Agent Architecture](#agent-architecture)
- [Creating an Agent](#creating-an-agent)
- [Agent Parameters](#agent-parameters)
- [State Management](#state-management)
- [Streaming](#streaming)
- [Human-in-the-Loop](#human-in-the-loop)
- [Multi-Agent Systems](#multi-agent-systems)
- [Multimodal Agents](#multimodal-agents)
- [MCP Integration](#mcp-integration)
- [Agent in Pipelines](#agent-in-pipelines)
- [Common Pitfalls](#common-pitfalls)

## What Are Agents

Agents are loop-based components that use LLMs and tools to solve complex queries iteratively. Unlike simple pipelines, agents make autonomous decisions about which tools to call, process results, and continue until they have a final answer.

The agent loop:
1. Send messages + tool descriptions to the LLM
2. LLM decides: respond with text OR request tool calls
3. If tool calls: execute tools, append results, go to step 1
4. If text: return final response (or check exit conditions)

## Agent Architecture

```
User Message → Agent Loop:
    ┌→ LLM (chat generator)
    │    ├→ Text response → Exit (if "text" in exit_conditions)
    │    └→ Tool calls → ToolInvoker → Tool results ─┐
    └──────────────────────────────────────────────────┘
```

Four pillars:
- **LLM Core**: ChatGenerator making decisions
- **Tools**: Functions the agent can call
- **Memory**: Conversation history (messages list)
- **State**: Typed data shared between tools across iterations

## Creating an Agent

### Basic Agent

```python
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage
from haystack.tools import tool

@tool
def search_docs(query: str) -> str:
    """Search internal documentation."""
    return f"Results for: {query}"

agent = Agent(
    chat_generator=OpenAIChatGenerator(model="gpt-4o-mini"),
    tools=[search_docs],
    system_prompt="You are a documentation assistant.",
)

result = agent.run(
    messages=[ChatMessage.from_user("How do I deploy to production?")]
)
print(result["last_message"].text)
```

### Agent with Multiple Tools

```python
from typing import Annotated, Literal
from haystack.tools import tool

@tool
def get_weather(
    city: Annotated[str, "City name"],
    unit: Annotated[Literal["celsius", "fahrenheit"], "Temperature unit"] = "celsius",
) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: 22°{unit[0].upper()}, sunny"

@tool
def calculator(expression: Annotated[str, "Math expression to evaluate"]) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression, {"__builtins__": {}}))

agent = Agent(
    chat_generator=OpenAIChatGenerator(),
    tools=[get_weather, calculator],
    system_prompt="You can check weather and do math.",
    max_agent_steps=10,
)
```

## Agent Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chat_generator` | ChatGenerator | required | LLM backing the agent |
| `tools` | list[Tool\|Toolset] | `[]` | Available tools |
| `system_prompt` | str | `None` | System message (plain or Jinja2) |
| `exit_conditions` | list[str] | `["text"]` | When to stop the loop |
| `state_schema` | dict | `None` | Typed state shared across tool calls |
| `max_agent_steps` | int | `100` | Max LLM + tool iterations |
| `streaming_callback` | callable | `None` | Token-by-token streaming |
| `raise_on_tool_invocation_failure` | bool | `False` | Raise on tool errors vs. continue |
| `confirmation_strategies` | dict | `None` | Human review per tool |
| `user_prompt` | str | `None` | Jinja2 template appended to user messages |

### Exit Conditions

```python
# Stop when the LLM responds with text (default)
agent = Agent(exit_conditions=["text"], ...)

# Stop when a specific tool is called
agent = Agent(exit_conditions=["final_answer_tool"], ...)

# Stop on either text or a specific tool
agent = Agent(exit_conditions=["text", "submit_result"], ...)
```

## State Management

State lets tools share typed data and accumulate results across iterations:

```python
from haystack import Document

@tool(outputs_to_state={"research_docs": {"source": "docs"}})
def search_knowledge_base(query: str) -> dict:
    """Search the knowledge base and store results in state."""
    docs = [Document(content=f"Result for: {query}")]
    return {"docs": docs}

@tool(outputs_to_state={"final_summary": {"source": "summary"}})
def summarize(text: str) -> dict:
    """Summarize the given text."""
    return {"summary": f"Summary of: {text}"}

agent = Agent(
    chat_generator=OpenAIChatGenerator(),
    tools=[search_knowledge_base, summarize],
    state_schema={
        "research_docs": {"type": list[Document]},
        "final_summary": {"type": str},
    },
)

result = agent.run(
    messages=[ChatMessage.from_user("Research and summarize AI trends")]
)
# Access state values from result
docs = result["research_docs"]
summary = result["final_summary"]
```

### Reading from State

Tools can read state values via `inputs_from_state`:

```python
draft_tool = Tool(
    name="draft_report",
    function=draft_report_fn,
    inputs_from_state={"documents": "research_docs"},
    ...
)
```

## Streaming

Enable token-by-token streaming:

```python
from haystack.components.generators.utils import print_streaming_chunk

agent = Agent(
    chat_generator=OpenAIChatGenerator(),
    tools=[search_docs],
    streaming_callback=print_streaming_chunk,
)
```

Custom streaming callback:

```python
def my_callback(chunk):
    if chunk.content:
        print(chunk.content, end="", flush=True)

agent = Agent(
    chat_generator=OpenAIChatGenerator(),
    streaming_callback=my_callback,
)
```

## Human-in-the-Loop

Intercept tool calls for human review before execution:

```python
from haystack.components.agents.agent import ConfirmationStrategy

def review_tool_call(tool_name, tool_args):
    print(f"Agent wants to call: {tool_name}({tool_args})")
    response = input("Allow? (y/n): ")
    return response.lower() == "y"

agent = Agent(
    chat_generator=OpenAIChatGenerator(),
    tools=[dangerous_tool, safe_tool],
    confirmation_strategies={
        "dangerous_tool": ConfirmationStrategy(callback=review_tool_call),
    },
)
```

## Multi-Agent Systems

Wrap agents as tools for coordinator/specialist patterns:

```python
from haystack.tools import ComponentTool

# Specialist agents
research_agent = Agent(
    chat_generator=OpenAIChatGenerator(),
    tools=[web_search, doc_search],
    system_prompt="You are a research specialist.",
)

writing_agent = Agent(
    chat_generator=OpenAIChatGenerator(),
    tools=[text_editor],
    system_prompt="You are a writing specialist.",
)

# Wrap as tools
research_tool = ComponentTool(
    component=research_agent,
    name="research",
    description="Research a topic using web and document search",
)

writing_tool = ComponentTool(
    component=writing_agent,
    name="write",
    description="Write and edit text content",
)

# Coordinator agent
coordinator = Agent(
    chat_generator=OpenAIChatGenerator(model="gpt-4o"),
    tools=[research_tool, writing_tool],
    system_prompt="Coordinate research and writing tasks.",
)
```

## Multimodal Agents

Process images alongside text using vision-capable models:

```python
from haystack.dataclasses import ImageContent, ChatMessage

image = ImageContent.from_url("https://example.com/chart.png")
# Or from file: ImageContent.from_file_path("chart.png")

result = agent.run(
    messages=[
        ChatMessage.from_user(
            content_parts=["Describe this chart:", image]
        )
    ]
)
```

Tools can return images using `outputs_to_string={"raw_result": True}`:

```python
from haystack.dataclasses import ImageContent, TextContent

@tool
def get_chart():
    """Retrieve a chart image."""
    return [
        TextContent("Here is the chart:"),
        ImageContent.from_file_path("chart.png"),
    ]

chart_tool = create_tool_from_function(
    get_chart,
    outputs_to_string={"raw_result": True},
)
```

## MCP Integration

Connect agents to MCP servers:

```python
from haystack.tools import MCPTool, MCPToolset

# Single MCP tool
mcp_tool = MCPTool(
    name="file_search",
    server_url="http://localhost:8080",
)

# Full MCP toolset
mcp_toolset = MCPToolset(server_url="http://localhost:8080")

agent = Agent(
    chat_generator=OpenAIChatGenerator(),
    tools=[mcp_toolset],
)
```

Expose agents as MCP servers via Hayhooks for compatibility with Claude Desktop, Cursor, and other MCP clients.

## Agent in Pipelines

Agents are components and can be used inside pipelines:

```python
pipe = Pipeline()
pipe.add_component("agent", Agent(
    chat_generator=OpenAIChatGenerator(),
    tools=[search_tool],
))
pipe.run({"agent": {"messages": [ChatMessage.from_user("Find info")]}})
```

Typically placed after a `ChatPromptBuilder` for template-based prompting.

## Common Pitfalls

**Too many tools**: LLMs struggle with 20+ tools. Use `SearchableToolset` for large catalogs or split into specialist agents.

**No max_agent_steps**: Default is 100, which may be too high. Set a reasonable limit to prevent runaway loops:

```python
agent = Agent(max_agent_steps=10, ...)
```

**Vague tool descriptions**: The LLM relies on tool names and descriptions to decide what to call. Be specific and include usage examples in docstrings.

**Missing error handling**: Set `raise_on_tool_invocation_failure=False` (default) to let the agent recover from tool errors gracefully.

## Related Topics

- Tools → `04-tools.md`
- Generators → `05-generators.md`
- RAG agents → `11-rag-patterns.md`
