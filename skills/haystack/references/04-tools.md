# Haystack Tools

> Source: [docs.haystack.deepset.ai/docs/tool](https://docs.haystack.deepset.ai/docs/tool) | haystack-ai 2.30.0

## Table of Contents

- [What Are Tools](#what-are-tools)
- [Creating Tools](#creating-tools)
- [Tool Class Fields](#tool-class-fields)
- [ComponentTool](#componenttool)
- [PipelineTool](#pipelinetool)
- [MCPTool and MCPToolset](#mcptool-and-mcptoolset)
- [Toolset and SearchableToolset](#toolset-and-searchabletoolset)
- [Output Configuration](#output-configuration)
- [State Integration](#state-integration)
- [Function Calling Pattern](#function-calling-pattern)
- [Common Pitfalls](#common-pitfalls)

## What Are Tools

Tools are data structures representing functions that LLMs can invoke. The LLM doesn't execute tools directly — it generates tool call requests with arguments. Haystack's `ToolInvoker` or `Agent` component executes the actual function.

Tool calling flow:
1. Tool definitions (name, description, JSON schema) are sent to the LLM
2. LLM decides which tool to call and with what arguments
3. `ToolInvoker` or `Agent` executes the function
4. Results are returned to the LLM for the next step

## Creating Tools

### @tool Decorator (Recommended)

Automatically generates JSON schema from type hints:

```python
from typing import Annotated, Literal
from haystack.tools import tool

@tool
def get_weather(
    city: Annotated[str, "The city to get weather for"],
    unit: Annotated[Literal["celsius", "fahrenheit"], "Temperature unit"] = "celsius",
) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: 20°{unit[0].upper()}, sunny"
```

The decorator extracts:
- **name** from the function name
- **description** from the docstring
- **parameters** from type hints and `Annotated` descriptions

### @tool with Custom Options

```python
@tool(
    name="weather_lookup",
    outputs_to_state={"last_weather": {"source": "result"}},
)
def get_weather(city: str) -> dict:
    """Look up weather."""
    return {"result": f"Sunny in {city}"}
```

### create_tool_from_function()

Wrap existing functions without decorating them:

```python
from haystack.tools import create_tool_from_function

def existing_function(query: str) -> str:
    return f"Results for: {query}"

my_tool = create_tool_from_function(
    existing_function,
    name="search",
    description="Search for information",
)
```

### Manual Tool Initialization

Full control over the JSON schema:

```python
from haystack.tools import Tool

parameters = {
    "type": "object",
    "properties": {
        "a": {"type": "integer", "description": "First number"},
        "b": {"type": "integer", "description": "Second number"},
    },
    "required": ["a", "b"],
}

add_tool = Tool(
    name="add",
    description="Add two numbers together",
    parameters=parameters,
    function=lambda a, b: a + b,
)
```

## Tool Class Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Tool identifier (used by LLM to select) |
| `description` | str | Explains purpose (critical for LLM decision-making) |
| `parameters` | dict | JSON schema for expected inputs |
| `function` | callable | The actual function to execute |
| `outputs_to_string` | dict\|None | Format tool output for LLM consumption |
| `inputs_from_state` | dict\|None | Map agent state keys to tool parameters |
| `outputs_to_state` | dict\|None | Write tool results to agent state |

### tool_spec Property

Returns the tool specification dict (name, description, parameters) for sending to the LLM.

### invoke() Method

Executes the tool function with provided arguments:

```python
result = my_tool.invoke(a=5, b=3)
```

## ComponentTool

Wraps any Haystack component as a callable tool:

```python
from haystack.tools import ComponentTool
from haystack.components.websearch import SerperDevWebSearch

web_search = ComponentTool(
    component=SerperDevWebSearch(top_k=3),
    name="web_search",
    description="Search the web for current information on any topic",
)
```

Use cases:
- Expose retrievers, converters, or any component as agent tools
- Wrap entire agents as tools (multi-agent pattern)

```python
# Wrap a retriever
retriever_tool = ComponentTool(
    component=InMemoryBM25Retriever(document_store=store, top_k=5),
    name="search_docs",
    description="Search the document knowledge base",
)
```

## PipelineTool

Wraps a complete Haystack pipeline as a single tool:

```python
from haystack.tools import PipelineTool

# Create a RAG pipeline
rag_pipe = Pipeline()
rag_pipe.add_component("retriever", InMemoryBM25Retriever(document_store=store))
rag_pipe.add_component("prompt", ChatPromptBuilder(template=rag_template))
rag_pipe.add_component("llm", OpenAIChatGenerator())
rag_pipe.connect("retriever.documents", "prompt.documents")
rag_pipe.connect("prompt", "llm")

# Wrap as a tool
rag_tool = PipelineTool(
    pipeline=rag_pipe,
    name="answer_from_docs",
    description="Answer questions using the document knowledge base",
)
```

## MCPTool and MCPToolset

Connect to Model Context Protocol servers:

```python
from haystack.tools import MCPTool, MCPToolset

# Single tool from MCP server
file_tool = MCPTool(
    name="read_file",
    server_url="http://localhost:8080",
)

# All tools from an MCP server
toolset = MCPToolset(server_url="http://localhost:8080")

# Stdio-based MCP server
toolset = MCPToolset(
    server_command=["npx", "-y", "@modelcontextprotocol/server-filesystem"],
    server_args=["--root", "/path/to/dir"],
)
```

**Requires**: `pip install mcp-haystack`

## Toolset and SearchableToolset

### Toolset

Group multiple tools for easier management:

```python
from haystack.tools import Toolset

math_tools = Toolset([add_tool, subtract_tool, multiply_tool])

# Add tools dynamically
math_tools.add(divide_tool)
math_tools.add(another_toolset)

# Use with agent
agent = Agent(tools=[math_tools])
```

### SearchableToolset

For large tool catalogs — uses keyword search to surface relevant tools:

```python
from haystack.tools import SearchableToolset

large_toolset = SearchableToolset(
    tools=[tool_1, tool_2, ..., tool_100],
    top_k=5,  # Only show top 5 relevant tools to the LLM
)

agent = Agent(tools=[large_toolset])
```

The LLM sees only the most relevant tools per query, reducing confusion with large catalogs.

## Output Configuration

### outputs_to_string

Controls how tool results are formatted for the LLM:

```python
from haystack import Document

def format_docs(docs: list[Document]) -> str:
    return "\n".join(f"- {doc.content}" for doc in docs)

search_tool = Tool(
    name="search",
    function=search_fn,
    parameters=schema,
    outputs_to_string={
        "source": "documents",
        "handler": format_docs,
    },
)
```

### Multiple Output Formatters

```python
outputs_to_string={
    "formatted_docs": {"source": "docs", "handler": format_documents},
    "summary": {"source": "metadata", "handler": format_metadata},
}
```

### Raw Multimodal Output

Return images and text directly to the LLM:

```python
from haystack.dataclasses import ImageContent, TextContent

def get_chart():
    return [
        TextContent("Here is the sales chart:"),
        ImageContent.from_file_path("chart.png"),
    ]

chart_tool = create_tool_from_function(
    get_chart,
    outputs_to_string={"raw_result": True},
)
```

## State Integration

### Writing to State

```python
@tool(outputs_to_state={"collected_data": {"source": "data"}})
def fetch_data(url: str) -> dict:
    """Fetch data from a URL."""
    return {"data": [{"url": url, "content": "..."}]}
```

### Reading from State

```python
report_tool = Tool(
    name="generate_report",
    function=generate_report_fn,
    parameters=schema,
    inputs_from_state={"data": "collected_data"},
)
```

## Function Calling Pattern

Manual three-step pattern (without Agent):

```python
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.tools import ToolInvoker
from haystack.dataclasses import ChatMessage

# Step 1: LLM generates tool calls
generator = OpenAIChatGenerator(tools=[weather_tool])
response = generator.run(
    messages=[ChatMessage.from_user("Weather in Berlin?")]
)

# Step 2: Execute tools
invoker = ToolInvoker(tools=[weather_tool])
if response["replies"][0].tool_calls:
    tool_results = invoker.run(messages=response["replies"])

    # Step 3: Feed results back to LLM
    all_messages = [
        ChatMessage.from_user("Weather in Berlin?"),
        *response["replies"],
        *tool_results["tool_messages"],
    ]
    final = generator.run(messages=all_messages)
    print(final["replies"][0].text)
```

For most use cases, the `Agent` component handles this loop automatically.

## Common Pitfalls

**Poor tool descriptions**: LLMs use descriptions to decide which tool to call. Vague descriptions lead to wrong tool selection.

**Missing type hints**: The `@tool` decorator relies on type hints to generate the JSON schema. Without them, the schema will be empty.

**Returning non-serializable objects**: Tool return values must be serializable to pass to the LLM. Return strings, dicts, or lists — not custom objects.

**Too many tools without SearchableToolset**: More than ~15 tools degrades LLM performance. Use `SearchableToolset` or split into specialist agents.

## Related Topics

- Agents → `03-agents.md`
- Generators (tool support) → `05-generators.md`
- Function calling in pipelines → `02-pipelines.md`
