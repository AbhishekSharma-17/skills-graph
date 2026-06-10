# Function Tools

> Source: [pydantic.dev/docs/ai/tools-toolsets/tools](https://pydantic.dev/docs/ai/tools-toolsets/tools/)

## Table of Contents

- [Overview](#overview)
- [Defining Tools](#defining-tools)
- [Tool Parameters and Schema](#tool-parameters-and-schema)
- [RunContext in Tools](#runcontext-in-tools)
- [Tool Return Types](#tool-return-types)
- [Tool Retries](#tool-retries)
- [Prepare Functions](#prepare-functions)
- [Agent-Wide Tool Filtering](#agent-wide-tool-filtering)
- [Deferred Tools and Approval](#deferred-tools-and-approval)
- [Message Injection](#message-injection)
- [Common Pitfalls](#common-pitfalls)

## Overview

Function tools let the model call Python functions to retrieve information, perform computations, or trigger side effects. Pydantic AI automatically generates JSON schemas from function signatures and docstrings, validates model-provided arguments with Pydantic, and returns results to the model.

## Defining Tools

### Decorator Registration

**`@agent.tool`** — tool with access to `RunContext` (dependencies, agent state):

```python
from pydantic_ai import Agent, RunContext

agent = Agent('openai:gpt-5.2', deps_type=str)

@agent.tool
async def get_user_info(ctx: RunContext[str]) -> str:
    """Get information about the current user."""
    return f"User: {ctx.deps}"
```

**`@agent.tool_plain`** — tool without context (no `RunContext` parameter):

```python
import random

@agent.tool_plain
def roll_dice() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))
```

### Constructor Registration

Pass tools as a list to the `Agent` constructor:

```python
from pydantic_ai import Agent, Tool

agent = Agent(
    'openai:gpt-5.2',
    deps_type=str,
    tools=[
        Tool(get_user_info, takes_ctx=True),
        Tool(roll_dice, takes_ctx=False),
    ],
)
```

## Tool Parameters and Schema

Function parameters (excluding `RunContext`) become the tool's JSON schema. Pydantic AI extracts descriptions from docstrings using griffe (supports Google, NumPy, and Sphinx formats):

```python
@agent.tool_plain(docstring_format='google', require_parameter_descriptions=True)
def search_products(query: str, category: str, max_results: int = 10) -> str:
    """Search the product catalog.

    Args:
        query: The search query string.
        category: Product category to filter by.
        max_results: Maximum number of results to return.
    """
    return f"Found products for '{query}' in {category}"
```

### Generated Schema

The above produces:

```json
{
  "name": "search_products",
  "description": "Search the product catalog.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "The search query string."},
      "category": {"type": "string", "description": "Product category to filter by."},
      "max_results": {"type": "integer", "description": "Maximum number of results to return.", "default": 10}
    },
    "required": ["query", "category"]
  }
}
```

### Complex Parameter Types

```python
from pydantic import BaseModel

class SearchFilter(BaseModel):
    category: str
    min_price: float | None = None
    max_price: float | None = None

@agent.tool_plain
def advanced_search(query: str, filters: SearchFilter) -> str:
    """Search with advanced filters."""
    return f"Searching '{query}' with filters: {filters}"
```

## RunContext in Tools

`RunContext` is always the first parameter when using `@agent.tool`. The framework detects it automatically and excludes it from the tool schema:

```python
@agent.tool
async def fetch_order(ctx: RunContext[AppDeps], order_id: str) -> dict:
    """Fetch an order by ID."""
    resp = await ctx.deps.http_client.get(f'/orders/{order_id}')
    return resp.json()
```

Useful `RunContext` attributes in tools:

- `ctx.deps` — the dependency instance
- `ctx.retry` — current retry count (useful for exponential backoff)
- `ctx.run_step` — which step of the agent loop this is

## Tool Return Types

Tools can return anything Pydantic can serialize to JSON:

```python
@agent.tool_plain
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    return {'city': city, 'temp': 22, 'condition': 'sunny'}

@agent.tool_plain
def list_items() -> list[str]:
    return ['item1', 'item2', 'item3']
```

## Tool Retries

When a tool detects invalid input, raise `ModelRetry` to ask the model to try again:

```python
from pydantic_ai import ModelRetry

@agent.tool(retries=3)
def get_user(ctx: RunContext[str], name: str) -> int:
    """Look up a user ID by name."""
    user_id = database.get(name)
    if user_id is None:
        raise ModelRetry(f'No user named "{name}". Try a different name.')
    return user_id
```

The `retries` parameter sets the maximum number of retries for that tool. The `ModelRetry` message is sent back to the model so it can adjust its arguments.

## Prepare Functions

Customize or filter tool definitions at each step of the agent loop:

```python
from pydantic_ai import Agent, RunContext, ToolDefinition

agent = Agent('openai:gpt-5.2', deps_type=int)

async def only_if_42(
    ctx: RunContext[int], tool_def: ToolDefinition
) -> ToolDefinition | None:
    if ctx.deps == 42:
        return tool_def  # Include tool
    return None  # Exclude tool for this step

@agent.tool(prepare=only_if_42)
def hitchhiker(ctx: RunContext[int], answer: str) -> str:
    return f'{ctx.deps} {answer}'
```

### Dynamic Parameter Modification

```python
async def customize_description(
    ctx: RunContext[str], tool_def: ToolDefinition
) -> ToolDefinition | None:
    tool_def.parameters_json_schema['properties']['name']['description'] = (
        f'Name of the {ctx.deps} to greet.'
    )
    return tool_def

@agent.tool(prepare=customize_description)
def greet(ctx: RunContext[str], name: str) -> str:
    return f'Hello, {name}!'
```

## Agent-Wide Tool Filtering

Use `PrepareTools` capability to filter all tools:

```python
from dataclasses import replace
from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.capabilities import PrepareTools

async def enforce_strict_mode(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition] | None:
    if ctx.model.system == 'openai':
        return [replace(td, strict=True) for td in tool_defs]
    return tool_defs

agent = Agent('openai:gpt-5.2', capabilities=[PrepareTools(enforce_strict_mode)])
```

## Deferred Tools and Approval

Tools can require human approval before execution:

```python
@agent.tool_plain(requires_approval=True)
def delete_file(path: str) -> str:
    """Delete a file from the system."""
    return f'File {path!r} deleted'
```

Handle approval via hooks:

```python
from pydantic_ai.capabilities import Hooks

hooks = Hooks()

@hooks.on.deferred_tool_calls
async def auto_approve(ctx, *, requests):
    return requests.build_results(approve_all=True)

agent = Agent('openai:gpt-5.2', capabilities=[hooks])
```

## Message Injection

Tools can inject follow-up messages into the conversation:

```python
@agent.tool
async def process_data(ctx: RunContext[None], data_id: str) -> str:
    """Process a data record."""
    result = await process(data_id)
    ctx.enqueue(f"Note: Processing took {result.duration}ms")
    return result.summary
```

## Common Pitfalls

- **Missing docstrings** — without a docstring, the tool has no description; models perform worse without descriptions
- **`@agent.tool` vs `@agent.tool_plain`** — use `tool_plain` when you don't need `RunContext`; using `tool` without a `RunContext` parameter raises an error
- **Large return values** — tool results are sent back to the model as context; keep returns concise to avoid wasting tokens
- **Side effects in tools** — tools may be called multiple times during retries; make destructive operations idempotent
- **Docstring format** — Pydantic AI uses griffe to parse docstrings; if parameter descriptions aren't appearing, check your docstring format matches the `docstring_format` setting

## Related

- `02-dependencies.md` — RunContext and dependency injection
- `05-capabilities.md` — Capabilities that bundle tools
- `06-hooks.md` — Tool execution hooks
