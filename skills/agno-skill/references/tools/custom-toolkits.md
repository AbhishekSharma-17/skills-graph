# Custom Toolkits

Toolkits bundle related tools into a reusable class. They inherit from `agno.tools.Toolkit` and provide configuration, shared state, and selective tool enabling.

## Basic Toolkit

```python
from typing import List
from agno.tools import Toolkit

class ShellTools(Toolkit):
    def __init__(self, working_directory: str = "/", **kwargs):
        self.working_directory = working_directory

        tools = [
            self.run_shell_command,
            self.list_files,
        ]

        super().__init__(name="shell_tools", tools=tools, **kwargs)

    def run_shell_command(self, args: List[str], tail: int = 100) -> str:
        """Runs a shell command and returns the output or error.

        Args:
            args (List[str]): The command to run as a list of strings.
            tail (int): The number of lines to return from the output.

        Returns:
            str: The output of the command.
        """
        import subprocess
        result = subprocess.run(
            args, capture_output=True, text=True, cwd=self.working_directory
        )
        output = result.stdout if result.stdout else result.stderr
        return output[-tail * 80:]

    def list_files(self, directory: str) -> str:
        """List files in the given directory.

        Args:
            directory (str): The directory to list files from.
        """
        import os
        files = os.listdir(os.path.join(self.working_directory, directory))
        return "\n".join(files)


# Usage
agent = Agent(tools=[ShellTools(working_directory="/home/user")], markdown=True)
```

**Key pattern:** Collect methods into a `tools` list, then pass to `super().__init__()`. Each method needs a docstring with `Args:` — these become the tool definitions the model sees.

## Async Toolkits

For I/O-bound operations, provide both sync and async implementations. Agno automatically uses the async version when the agent runs with `arun()` or `aprint_response()`:

```python
import httpx
from agno.tools import Toolkit

class APITools(Toolkit):
    def __init__(self, base_url: str, timeout: float = 30.0, **kwargs):
        self.base_url = base_url
        self.timeout = timeout

        # Sync tools (used by agent.run() / agent.print_response())
        tools = [self.fetch_data, self.post_data]

        # Async tools (used by agent.arun() / agent.aprint_response())
        # Format: (async_method, "tool_name_it_replaces")
        async_tools = [
            (self.afetch_data, "fetch_data"),
            (self.apost_data, "post_data"),
        ]

        super().__init__(
            name="api_tools", tools=tools, async_tools=async_tools, **kwargs
        )

    # --- Sync methods ---
    def fetch_data(self, endpoint: str) -> dict:
        """Fetch data from an API endpoint.

        Args:
            endpoint (str): The API endpoint path.
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()

    def post_data(self, endpoint: str, data: dict) -> dict:
        """Post data to an API endpoint.

        Args:
            endpoint (str): The API endpoint path.
            data (dict): The data to post.
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()

    # --- Async methods ---
    async def afetch_data(self, endpoint: str) -> dict:
        """Fetch data from an API endpoint asynchronously.

        Args:
            endpoint (str): The API endpoint path.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()

    async def apost_data(self, endpoint: str, data: dict) -> dict:
        """Post data to an API endpoint asynchronously.

        Args:
            endpoint (str): The API endpoint path.
            data (dict): The data to post.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
```

The `async_tools` list uses tuples of `(async_method, "sync_tool_name")` to map async methods to their sync counterparts. When `arun()` is used, Agno swaps in the async version automatically.

## Toolkit Parameters

The `Toolkit` base class accepts these configuration parameters:

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `name` | `str` | required | Descriptive name for the toolkit |
| `tools` | `List[Callable]` | `[]` | List of sync tool methods |
| `async_tools` | `List[tuple]` | `[]` | List of `(async_method, "name")` tuples |
| `instructions` | `str` | `None` | Usage instructions added to agent's system prompt |
| `add_instructions` | `bool` | `True` | Whether to inject instructions into agent context |
| `include_tools` | `list[str]` | `None` | Whitelist: only expose these tool names |
| `exclude_tools` | `list[str]` | `None` | Blacklist: hide these tool names |
| `requires_confirmation_tools` | `list[str]` | `None` | Tools requiring user confirmation |
| `external_execution_required_tools` | `list[str]` | `None` | Tools executed outside agent loop |
| `stop_after_tool_call_tools` | `list[str]` | `None` | Tools that stop agent after execution |
| `show_result_tools` | `list[str]` | `None` | Tools whose results are shown to user |
| `cache_results` | `bool` | `False` | Enable result caching for all tools |
| `cache_ttl` | `int` | `3600` | Cache time-to-live in seconds |
| `cache_dir` | `str` | `None` | Cache directory path |
| `auto_register` | `bool` | `True` | Auto-register tools on initialization |

## Selective Tool Enabling

Most pre-built toolkits follow a pattern of `enable_*` flags:

```python
from agno.tools.duckduckgo import DuckDuckGoTools

# Only enable web search, disable news
agent = Agent(
    tools=[DuckDuckGoTools(enable_search=True, enable_news=False)],
)
```

For custom toolkits, use `include_tools` / `exclude_tools`:

```python
# Only expose specific tools from the toolkit
agent = Agent(
    tools=[
        APITools(
            base_url="https://api.example.com",
            include_tools=["fetch_data"],        # Only this tool is visible
        )
    ],
)

# Or exclude specific tools
agent = Agent(
    tools=[
        APITools(
            base_url="https://api.example.com",
            exclude_tools=["post_data"],         # Everything except this
        )
    ],
)
```

## Toolkit Instructions

Toolkits can inject usage instructions into the agent's system prompt:

```python
class DatabaseTools(Toolkit):
    def __init__(self, connection_string: str, **kwargs):
        self.conn_str = connection_string
        tools = [self.query, self.list_tables]
        super().__init__(
            name="database_tools",
            tools=tools,
            instructions=(
                "Use the database tools to query data. "
                "Always use parameterized queries to prevent SQL injection. "
                "Limit results to 100 rows unless the user requests more."
            ),
            **kwargs,
        )
```

Set `add_instructions=False` on the toolkit (or agent level) to suppress instruction injection.

## Real-World Toolkit Pattern

```python
from agno.tools import Toolkit
from agno.run import RunContext

class OrderTools(Toolkit):
    def __init__(self, api_base: str, api_key: str, **kwargs):
        self.api_base = api_base
        self.api_key = api_key
        tools = [self.get_order, self.list_orders, self.cancel_order]
        async_tools = [
            (self.aget_order, "get_order"),
            (self.alist_orders, "list_orders"),
            (self.acancel_order, "cancel_order"),
        ]
        super().__init__(
            name="order_tools",
            tools=tools,
            async_tools=async_tools,
            instructions="Use these tools to manage customer orders.",
            requires_confirmation_tools=["cancel_order"],  # Confirm before cancel
            **kwargs,
        )

    def get_order(self, run_context: RunContext, order_id: str) -> dict:
        """Get details of a specific order.

        Args:
            order_id (str): The order ID to look up.
        """
        # run_context gives access to session_state, user_id, etc.
        ...

    def cancel_order(self, order_id: str, reason: str) -> str:
        """Cancel an existing order.

        Args:
            order_id (str): The order ID to cancel.
            reason (str): Reason for cancellation.
        """
        ...

    # Async variants
    async def aget_order(self, run_context: RunContext, order_id: str) -> dict:
        """Get order details asynchronously."""
        ...

    async def acancel_order(self, order_id: str, reason: str) -> str:
        """Cancel an order asynchronously."""
        ...
```
