# Tools — Function Tools, Hosted Tools & Agents as Tools

> Source: [openai.github.io/openai-agents-python/tools](https://openai.github.io/openai-agents-python/tools/)

## Table of Contents

- [Tool Categories](#tool-categories)
- [Function Tools](#function-tools)
- [Schema Generation](#schema-generation)
- [Timeouts & Error Handling](#timeouts--error-handling)
- [Returning Rich Content](#returning-rich-content)
- [Custom Function Tools](#custom-function-tools)
- [Hosted Tools](#hosted-tools)
- [Tool Search (Deferred Loading)](#tool-search-deferred-loading)
- [Agents as Tools](#agents-as-tools)

## Tool Categories

| Type | Description | Execution |
|------|-------------|-----------|
| **Function tools** | Python functions wrapped as tools | Local/runtime |
| **Hosted tools** | OpenAI-provided (web search, code interpreter, etc.) | OpenAI servers |
| **MCP tools** | Model Context Protocol servers | Local or remote |
| **Agents as tools** | Other agents exposed as callable tools | Local runtime |
| **Codex tool** | Workspace-scoped task execution (experimental) | OpenAI servers |

## Function Tools

The `@function_tool` decorator turns any Python function into a tool:

```python
from agents import Agent, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Fetch weather for a given city.

    Args:
        city: The city name to look up.
    """
    return f"The weather in {city} is sunny, 22°C"

@function_tool
async def search_database(query: str, limit: int = 10) -> str:
    """Search the product database.

    Args:
        query: Search query string.
        limit: Max results to return.
    """
    results = await db.search(query, limit=limit)
    return json.dumps(results)

agent = Agent(
    name="Assistant",
    tools=[get_weather, search_database],
)
```

Both sync and async functions are supported. The SDK automatically extracts:
- **Tool name** from the function name (or `@function_tool(name="custom_name")`)
- **Description** from the docstring
- **Schema** from function arguments using Pydantic

### Accessing Context in Tools

Tools can receive the run context as their first parameter:

```python
from agents import function_tool, RunContextWrapper

@function_tool
async def get_user_orders(ctx: RunContextWrapper[UserContext], limit: int = 5) -> str:
    """Fetch recent orders for the current user."""
    orders = await ctx.context.fetch_orders(limit=limit)
    return json.dumps(orders)
```

## Schema Generation

The SDK generates JSON schemas automatically from function signatures:

```python
from typing import Annotated
from pydantic import Field

@function_tool
def score_review(
    score: Annotated[int, Field(ge=0, le=100, description="Review score 0-100")],
    comment: str,
) -> str:
    """Submit a review score with comment."""
    return f"Score {score}: {comment}"
```

Supported types: Python primitives, Pydantic models, TypedDicts, `Annotated` with `Field` constraints. Docstring formats: Google, Sphinx, NumPy.

## Timeouts & Error Handling

### Timeouts

```python
@function_tool(timeout=5.0)
async def slow_api_call(query: str) -> str:
    """Call a slow external API."""
    return await external_api.query(query)
```

Timeout behaviors:
- `timeout_behavior="error_as_result"` (default) — returns error message to the model, which can retry
- `timeout_behavior="raise_exception"` — raises `ToolTimeoutError`

Custom timeout message:

```python
def timeout_message(ctx, error):
    return "The API is taking too long. Try a simpler query."

@function_tool(timeout=5.0, timeout_error_function=timeout_message)
async def slow_lookup(query: str) -> str:
    ...
```

### Error Handling

```python
def friendly_error(ctx: RunContextWrapper, error: Exception) -> str:
    return "An internal error occurred. Please try a different approach."

@function_tool(failure_error_function=friendly_error)
def risky_operation(data: str) -> str:
    """Perform an operation that might fail."""
    ...
```

Pass `failure_error_function=None` to re-raise exceptions instead of catching them.

## Returning Rich Content

Tools can return images, files, and structured content:

```python
from agents.tool import ToolOutputImage, ToolOutputText, ToolOutputFileContent

@function_tool
def generate_chart(data: str) -> list:
    """Generate a chart from data."""
    image_bytes = create_chart(data)
    return [
        ToolOutputText(text="Here's the chart:"),
        ToolOutputImage(image_data=base64.b64encode(image_bytes).decode(), media_type="image/png"),
    ]

@function_tool
def export_report(report_id: str) -> ToolOutputFileContent:
    """Export a report as a file."""
    content = generate_report(report_id)
    return ToolOutputFileContent(data=base64.b64encode(content).decode(), media_type="application/pdf")
```

## Custom Function Tools

Build tools manually when the decorator doesn't fit:

```python
from agents import FunctionTool
from pydantic import BaseModel

class ProcessInput(BaseModel):
    user_id: str
    action: str

async def run_process(ctx, args_json: str) -> str:
    args = ProcessInput.model_validate_json(args_json)
    return f"Processed {args.action} for {args.user_id}"

tool = FunctionTool(
    name="process_user",
    description="Process a user action",
    params_json_schema=ProcessInput.model_json_schema(),
    on_invoke_tool=run_process,
)

agent = Agent(name="Processor", tools=[tool])
```

## Hosted Tools

OpenAI-provided tools that run on OpenAI's infrastructure:

```python
from agents import Agent
from agents.tool import WebSearchTool, CodeInterpreterTool, FileSearchTool, ImageGenerationTool

agent = Agent(
    name="Research Agent",
    tools=[
        WebSearchTool(),                              # Web search
        CodeInterpreterTool(),                        # Code execution sandbox
        FileSearchTool(vector_store_ids=["vs_123"]),  # RAG over documents
        ImageGenerationTool(),                        # Image generation
    ],
)
```

### Shell & Computer Tools (Local Runtime)

```python
from agents.tool import ShellTool, ComputerTool, ApplyPatchTool

agent = Agent(
    name="Coding Agent",
    tools=[
        ShellTool(executor=my_shell_executor),
        ApplyPatchTool(editor=my_patch_editor),
    ],
)
```

## Tool Search (Deferred Loading)

Defer large tool surfaces until the model actually needs them:

```python
from agents import Agent, function_tool
from agents.tool import ToolSearchTool, tool_namespace

@function_tool(defer_loading=True)
def rare_tool_a(x: str) -> str:
    """A rarely used tool."""
    return x

@function_tool(defer_loading=True)
def rare_tool_b(x: str) -> str:
    """Another rarely used tool."""
    return x

namespace = tool_namespace(
    name="rare_tools",
    description="Collection of rarely used utilities",
    tools=[rare_tool_a, rare_tool_b],
)

agent = Agent(
    name="Efficient Agent",
    tools=[
        common_tool,          # Always available
        namespace,            # Deferred namespace
        ToolSearchTool(),     # Required when using deferred tools
    ],
)
```

## Agents as Tools

Invoke agents as tools without full handoffs — the calling agent retains control:

```python
from agents import Agent

spanish_agent = Agent(
    name="Spanish Translator",
    instructions="Translate the given text to Spanish.",
)

french_agent = Agent(
    name="French Translator",
    instructions="Translate the given text to French.",
)

orchestrator = Agent(
    name="Orchestrator",
    instructions="Translate text to the requested language.",
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_spanish",
            tool_description="Translate text to Spanish",
        ),
        french_agent.as_tool(
            tool_name="translate_french",
            tool_description="Translate text to French",
        ),
    ],
)
```

### Agent-as-Tool Options

```python
from pydantic import BaseModel, Field

class TranslationInput(BaseModel):
    text: str = Field(description="Text to translate")
    formality: str = Field(description="formal or informal")

tool = translator_agent.as_tool(
    tool_name="translate",
    tool_description="Translate text",
    parameters=TranslationInput,         # Structured input schema
    include_input_schema=True,           # Expose schema to caller
    max_turns=5,                         # Limit nested turns
    needs_approval=True,                 # Require approval before execution
    is_enabled=lambda ctx, agent: True,  # Conditional availability
)
```

### Custom Output Extraction

```python
async def extract_translation(run_result) -> str:
    """Extract only the translated text from the sub-agent's output."""
    return run_result.final_output.strip()

tool = translator_agent.as_tool(
    tool_name="translate",
    tool_description="Translate text",
    custom_output_extractor=extract_translation,
)
```

### Streaming from Nested Agents

```python
async def handle_stream(event):
    print(f"[nested] {event['agent'].name}: {event['event'].type}")

tool = sub_agent.as_tool(
    tool_name="analyze",
    tool_description="Analyze data",
    on_stream=handle_stream,
)
```

## Common Pitfalls

- **Missing docstrings**: Without a docstring, the tool gets no description and the model may misuse it
- **Non-serializable return types**: Tools must return strings or `ToolOutput*` types — returning raw objects fails
- **Context type mismatch**: If a tool accepts `RunContextWrapper[T]`, the agent must be `Agent[T]`
- **Deferred tools without ToolSearchTool**: Deferred tools won't load unless `ToolSearchTool()` is in the tools list

## Related Topics

- **Agents:** `01-agents.md` — Agent configuration
- **MCP Integration:** `10-mcp.md` — External MCP tools
- **Multi-Agent:** `08-multi-agent.md` — Orchestration patterns
