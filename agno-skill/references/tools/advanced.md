# Advanced Tool Patterns


## Contents

- [Built-in Tool Parameters (Auto-Injected)](#built-in-tool-parameters-auto-injected)
- [Tool Hooks](#tool-hooks)
- [Exceptions for Control Flow](#exceptions-for-control-flow)
- [Result Caching](#result-caching)
- [Concurrent Tool Execution](#concurrent-tool-execution)

## Built-in Tool Parameters (Auto-Injected)

Declare any of these in your tool function signature and Agno injects them automatically — they are **not** exposed to the model as parameters.

### RunContext — Session State & Dependencies

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.run import RunContext
from agno.db.sqlite import SqliteDb

def add_item(run_context: RunContext, item: str) -> str:
    """Add an item to the shopping list.

    Args:
        item (str): The item to add.
    """
    run_context.session_state["shopping_list"].append(item)
    return f"Shopping list: {run_context.session_state['shopping_list']}"

def remove_item(run_context: RunContext, item: str) -> str:
    """Remove an item from the shopping list.

    Args:
        item (str): The item to remove.
    """
    shopping_list = run_context.session_state["shopping_list"]
    if item in shopping_list:
        shopping_list.remove(item)
    return f"Shopping list: {shopping_list}"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    session_state={"shopping_list": []},
    db=SqliteDb(db_file="tmp/agents.db"),
    tools=[add_item, remove_item],
    instructions="Current shopping list: {shopping_list}",
    markdown=True,
)
```

**RunContext attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | `str` | Unique run identifier |
| `session_id` | `str` | Session identifier |
| `user_id` | `Optional[str]` | User identifier |
| `session_state` | `Dict[str, Any]` | Persistent session state (read/write) |
| `dependencies` | `Dict[str, Any]` | Injected dependencies |
| `knowledge_filters` | `Dict[str, Any]` | Knowledge base filters |
| `metadata` | `Dict[str, Any]` | Run metadata |

### Agent & Team Access

```python
from agno.agent import Agent

def get_agent_info(agent: Agent) -> str:
    """Get information about the current agent.

    Returns:
        str: Agent details.
    """
    return f"Agent: {agent.name}, Model: {agent.model.id}"
```

### Media Parameters

```python
from typing import Optional, List
from agno.media import Image, Video, Audio, File

def analyze_images(images: Optional[List[Image]], query: str) -> str:
    """Analyze uploaded images.

    Args:
        query (str): What to analyze in the images.
    """
    if not images:
        return "No images provided."
    return f"Analyzing {len(images)} images for: {query}"

def process_files(files: Optional[List[File]]) -> str:
    """Process uploaded files.

    Returns:
        str: Processing result.
    """
    if not files:
        return "No files provided."
    return f"Processing {len(files)} files"
```

## Tool Hooks

Hooks wrap tool execution for logging, validation, timing, or transformation.

### Hook Function Signature

```python
import time
import logging

logger = logging.getLogger(__name__)

def logger_hook(
    function_name: str,
    function_call,
    arguments: dict,
    **kwargs,
):
    """Log tool execution time and arguments."""
    start = time.time()
    logger.info(f"Calling {function_name} with {arguments}")

    result = function_call(**arguments)

    duration = time.time() - start
    logger.info(f"{function_name} completed in {duration:.2f}s")
    return result
```

**Available kwargs in hooks:** `agent`, `team`, `run_context` — request them by name.

### Pre and Post Hooks

```python
from agno.tools.function import FunctionCall

def pre_hook(fc: FunctionCall):
    """Runs before tool execution."""
    print(f"About to call: {fc.function.name}")
    print(f"Arguments: {fc.arguments}")

def post_hook(fc: FunctionCall):
    """Runs after tool execution."""
    print(f"Completed: {fc.function.name}")
    print(f"Result: {fc.result}")

@tool(pre_hook=pre_hook, post_hook=post_hook)
def my_tool(query: str) -> str:
    """Do something.

    Args:
        query (str): The query.
    """
    return f"Result for: {query}"
```

### Applying Hooks

```python
from agno.agent import Agent
from agno.tools.hackernews import HackerNewsTools

# On the agent (applies to all tools)
agent = Agent(
    tools=[HackerNewsTools()],
    tool_hooks=[logger_hook],
)

# On a specific tool
@tool(tool_hooks=[logger_hook, auth_hook])
def secure_operation(data: str) -> str:
    """Perform a secure operation."""
    ...

# On a toolkit
agent = Agent(
    tools=[HackerNewsTools(tool_hooks=[logger_hook])],
)
```

## Exceptions for Control Flow

### RetryAgentRun — Ask Model to Try Again

Raises a message back to the model with instructions to retry, without ending the run:

```python
from agno.exceptions import RetryAgentRun
from agno.run import RunContext

def add_item(run_context: RunContext, item: str) -> str:
    """Add item to shopping list (minimum 3 items required).

    Args:
        item (str): The item to add.
    """
    run_context.session_state.setdefault("shopping_list", [])
    run_context.session_state["shopping_list"].append(item)

    count = len(run_context.session_state["shopping_list"])
    if count < 3:
        raise RetryAgentRun(
            f"Shopping list has {count} items: {run_context.session_state['shopping_list']}. "
            f"Minimum 3 required. Add {3 - count} more."
        )

    return f"Shopping list complete: {run_context.session_state['shopping_list']}"
```

The model receives the error message and can call the tool again to meet the requirement.

### StopAgentRun — Force Stop

Immediately ends the tool call loop and returns the message as the final response:

```python
from agno.exceptions import StopAgentRun

def check_limit(run_context: RunContext, value: int) -> str:
    """Check if a value is within limits.

    Args:
        value (int): The value to check.
    """
    if value > 100:
        raise StopAgentRun(f"Value {value} exceeds maximum of 100. Operation aborted.")
    return f"Value {value} is within limits."
```

## Result Caching

Cache tool results to avoid repeated expensive operations (API calls, DB queries, etc.).

### On a Toolkit Instance

```python
from agno.tools.hackernews import HackerNewsTools
from agno.tools.yfinance import YFinanceTools

agent = Agent(
    tools=[
        HackerNewsTools(cache_results=True, cache_ttl=1800),
        YFinanceTools(cache_results=True, cache_dir="/tmp/finance_cache"),
    ],
)
```

### On Individual Tools

```python
@tool(cache_results=True, cache_ttl=3600, cache_dir="/tmp/my_cache")
def expensive_lookup(query: str) -> str:
    """Perform an expensive lookup.

    Args:
        query (str): The lookup query.
    """
    # This result is cached for 1 hour
    ...
```

**Cache parameters:**
- `cache_results` (bool): Enable/disable caching
- `cache_ttl` (int): Time-to-live in seconds (default: 3600)
- `cache_dir` (str): Directory for cache files (default: system temp)

## Concurrent Tool Execution

Models can request multiple tool calls in a single response. When using async, these execute concurrently:

```python
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

async def fetch_weather(city: str) -> str:
    """Fetch weather for a city.

    Args:
        city (str): The city name.
    """
    await asyncio.sleep(1)  # Simulate API call
    return f"Weather in {city}: 22C, sunny"

async def fetch_news(topic: str) -> str:
    """Fetch news about a topic.

    Args:
        topic (str): The news topic.
    """
    await asyncio.sleep(1)  # Simulate API call
    return f"Latest news about {topic}: ..."

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[fetch_weather, fetch_news],
)

# Both tools can execute concurrently if model requests both at once
asyncio.run(
    agent.aprint_response(
        "What's the weather in NYC and latest AI news?", stream=True
    )
)
```

Concurrent execution requires models that support parallel function calling (OpenAI enables `parallel_tool_calls` by default). Synchronous functions execute on separate threads in async contexts.
