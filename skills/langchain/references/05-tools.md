# Tools

> Source: https://docs.langchain.com/oss/python/langchain/tools

## Table of Contents

- [Overview](#overview)
- [Creating Tools with @tool](#creating-tools-with-tool)
- [Advanced Schema Definition](#advanced-schema-definition)
- [ToolRuntime — Accessing Context](#toolruntime--accessing-context)
- [Return Values](#return-values)
- [Error Handling](#error-handling)
- [Dynamic Tool Selection](#dynamic-tool-selection)
- [Headless Tools](#headless-tools)
- [Common Patterns](#common-patterns)

## Overview

Tools are functions that models can call to interact with external systems — databases, APIs, file systems, or any Python code. LangChain tools have a name, description (guides model usage), and input schema (auto-generated from type hints). Tools are the primary way agents interact with the world.

## Creating Tools with @tool

### Basic Tool

```python
from langchain.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.
    
    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"
```

The docstring becomes the tool description. Type hints define the input schema. Both are required.

### Custom Name and Description

```python
@tool("web_search")
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

@tool("calculator", description="Perform arithmetic. Use for any math problems.")
def calc(expression: str) -> str:
    """Evaluate mathematical expressions."""
    return str(eval(expression))
```

### Async Tools

```python
@tool
async def fetch_data(url: str) -> str:
    """Fetch data from a URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

### return_direct

Skip further model processing and return tool output directly:

```python
@tool(return_direct=True)
def fetch_order_status(order_id: str) -> str:
    """Fetch the current status of a customer order."""
    return f"Order {order_id} is shipped."
```

## Advanced Schema Definition

### Pydantic Model Schema

```python
from pydantic import BaseModel, Field
from typing import Literal

class WeatherInput(BaseModel):
    """Input for weather queries."""
    location: str = Field(description="City name or coordinates")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="Temperature unit preference"
    )
    include_forecast: bool = Field(
        default=False,
        description="Include 5-day forecast"
    )

@tool(args_schema=WeatherInput)
def get_weather(location: str, units: str = "celsius",
                include_forecast: bool = False) -> str:
    """Get current weather and optional forecast."""
    temp = 22 if units == "celsius" else 72
    return f"Weather in {location}: {temp}°"
```

### JSON Schema

```python
weather_schema = {
    "type": "object",
    "properties": {
        "location": {"type": "string"},
        "units": {"type": "string", "enum": ["celsius", "fahrenheit"]},
    },
    "required": ["location"]
}

@tool(args_schema=weather_schema)
def get_weather(location: str, units: str = "celsius") -> str:
    """Get current weather."""
    return f"Weather in {location}: sunny"
```

## ToolRuntime — Accessing Context

`ToolRuntime` provides access to agent state, user context, persistent storage, and execution metadata. It is hidden from the model's schema.

### Reserved Parameter Names

`config` and `runtime` cannot be used as tool argument names — they are reserved for internal use.

### Accessing State (Short-term Memory)

```python
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage

@tool
def get_last_user_message(runtime: ToolRuntime) -> str:
    """Get the most recent message from the user."""
    messages = runtime.state["messages"]
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    return "No user messages found"
```

### Updating State with Command

```python
from langchain.messages import ToolMessage
from langgraph.types import Command

@tool
def set_user_name(new_name: str, runtime: ToolRuntime) -> Command:
    """Set the user's name in conversation state."""
    return Command(update={
        "user_name": new_name,
        "messages": [ToolMessage(
            content=f"Name set to {new_name}.",
            tool_call_id=runtime.tool_call_id,
        )]
    })
```

### Accessing Context (User-Specific Data)

```python
from dataclasses import dataclass

@dataclass
class UserContext:
    user_id: str

@tool
def get_account_info(runtime: ToolRuntime[UserContext]) -> str:
    """Get the current user's account information."""
    user_id = runtime.context.user_id
    user = USER_DATABASE.get(user_id)
    if user:
        return f"Account: {user['name']}, Type: {user['account_type']}"
    return "User not found"
```

### Long-term Memory (Store)

```python
from typing import Any

@tool
def save_preference(key: str, value: str, runtime: ToolRuntime) -> str:
    """Save a user preference to persistent storage."""
    store = runtime.store
    store.put(("preferences",), key, {"value": value})
    return f"Saved {key}={value}"

@tool
def get_preference(key: str, runtime: ToolRuntime) -> str:
    """Get a user preference from persistent storage."""
    store = runtime.store
    item = store.get(("preferences",), key)
    return str(item.value) if item else "Not set"
```

### Stream Writer for Progress

```python
@tool
def process_data(data: str, runtime: ToolRuntime) -> str:
    """Process data with progress updates."""
    writer = runtime.stream_writer
    writer("Starting data processing...")
    writer("50% complete...")
    writer("Processing finished.")
    return "Data processed successfully"
```

### Execution Info

```python
@tool
def log_context(runtime: ToolRuntime) -> str:
    """Log execution identity information."""
    info = runtime.execution_info
    return f"Thread: {info.thread_id}, Run: {info.run_id}, Attempt: {info.node_attempt}"
```

## Return Values

### String (Default)

```python
@tool
def greet(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"
```

### Structured Data

```python
@tool
def get_stats(user_id: str) -> dict:
    """Get user statistics."""
    return {"user_id": user_id, "posts": 42, "followers": 1000}
```

### Multimodal Content

```python
@tool
def capture_screenshot() -> list[dict]:
    """Capture a screenshot."""
    return [
        {"type": "text", "text": "Screenshot:"},
        {"type": "image", "url": "https://example.com/screenshot.png"},
    ]
```

### Command (State Update)

```python
@tool
def set_language(lang: str, runtime: ToolRuntime) -> Command:
    """Set preferred language."""
    return Command(update={
        "language": lang,
        "messages": [ToolMessage(
            content=f"Language set to {lang}.",
            tool_call_id=runtime.tool_call_id,
        )]
    })
```

## Error Handling

### Middleware-Based Error Handling

```python
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest

@wrap_tool_call
def handle_errors(request: ToolCallRequest, handler) -> ToolMessage:
    """Convert tool exceptions into ToolMessages."""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: {e}. Please check your input.",
            tool_call_id=request.tool_call["id"],
        )

agent = create_agent(
    model="openai:gpt-4o",
    tools=[search],
    middleware=[handle_errors],
)
```

## Dynamic Tool Selection

### Filter by State

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

@wrap_model_call
def auth_filter(request: ModelRequest, handler):
    """Only show admin tools to authenticated users."""
    is_auth = request.state.get("authenticated", False)
    if not is_auth:
        tools = [t for t in request.tools if t.name.startswith("public_")]
        request = request.override(tools=tools)
    return handler(request)
```

### Filter by User Role

```python
@wrap_model_call
def role_filter(request: ModelRequest, handler):
    """Filter tools based on user role."""
    role = request.runtime.context.user_role if request.runtime else "viewer"
    if role != "admin":
        tools = [t for t in request.tools if t.name != "delete_data"]
        request = request.override(tools=tools)
    return handler(request)
```

## Headless Tools

Schema-only tools where execution happens client-side (browser):

```python
from langchain.tools import tool

@tool
def get_geolocation() -> dict:
    """Get the user's current geographic location."""
    raise NotImplementedError("Client-side only")
```

When the model calls this tool, the agent pauses with an interrupt. The client executes it locally and resumes with the result.

## Common Patterns

### Bind Tools to Model

```python
model_with_tools = model.bind_tools([search, calculator])
response = model_with_tools.invoke("What is 42 * 17?")
for tc in response.tool_calls:
    print(f"{tc['name']}({tc['args']})")
```

### Tool Naming Convention

Use `snake_case` for tool names to maximize provider compatibility across OpenAI, Anthropic, Google, etc.
