# Function Tools — @tool Decorator, Parameters, Patterns

## The @tool Decorator

Every function tool MUST have all four elements:

```python
from agent_framework import tool
from typing import Annotated

@tool                                                    # 1. @tool decorator
def get_weather(
    location: Annotated[str, "The city name"],           # 2. Annotated type hints
    unit: Annotated[str, "C or F"] = "C",                # 3. Default values optional
) -> str:                                                # 4. Return type
    """Get current weather for a location."""             # 5. Docstring (REQUIRED)
    return f"Weather in {location}: 22{unit}"
```

### What Each Element Does

| Element | Purpose | Required |
|---|---|:-:|
| `@tool` | Registers function as agent tool | ✅ |
| Docstring | Becomes tool description for the LLM | ✅ |
| `Annotated[type, "desc"]` | Parameter name, type, and description for LLM | ✅ |
| Return type hint | Documents what the tool returns | ✅ |
| Default values | Makes parameters optional for the LLM | ❌ |

### ❌ Wrong — Missing Elements

```python
# WRONG: No decorator
def get_weather(location):
    return f"Weather in {location}"

# WRONG: No docstring
@tool
def get_weather(location: Annotated[str, "City"]) -> str:
    return f"Weather in {location}"

# WRONG: No type hints
@tool
def get_weather(location) -> str:
    """Get weather."""
    return f"Weather in {location}"

# WRONG: No Annotated description
@tool
def get_weather(location: str) -> str:
    """Get weather."""
    return f"Weather in {location}"
```

## Passing Tools to Agent

```python
@tool
def search_docs(query: Annotated[str, "Search query"]) -> str:
    """Search documentation."""
    return f"Found results for: {query}"

@tool
def send_email(
    to: Annotated[str, "Recipient email address"],
    subject: Annotated[str, "Email subject"],
    body: Annotated[str, "Email body"],
) -> str:
    """Send an email to someone."""
    return f"Email sent to {to}"

# Pass as list
agent = client.as_agent(
    name="Assistant",
    instructions="Help users search docs and send emails.",
    tools=[search_docs, send_email],
)

# Or pass single tool (no list needed)
agent = client.as_agent(
    name="SearchBot",
    instructions="Search documentation.",
    tools=search_docs,
)
```

## Adding Extra Tools Per-Run

```python
# Agent has default tools
agent = client.as_agent(tools=[search_docs])

# Add extra tools for a specific run
result = await agent.run(
    "Send an email with the search results",
    tools=[send_email],  # Added alongside default tools
)
```

## Parameter Types

### Supported Types

```python
@tool
def complex_tool(
    name: Annotated[str, "Person name"],
    age: Annotated[int, "Person age"],
    score: Annotated[float, "Score from 0 to 1"],
    active: Annotated[bool, "Is person active"],
    tags: Annotated[list[str], "List of tags"],
    count: Annotated[int, "Number of items"] = 10,  # Optional with default
) -> dict:
    """Process complex data."""
    return {"name": name, "age": age, "score": score}
```

### Enum Parameters

```python
from enum import Enum

class TemperatureUnit(str, Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"

@tool
def get_temperature(
    city: Annotated[str, "City name"],
    unit: Annotated[TemperatureUnit, "Temperature unit"] = TemperatureUnit.CELSIUS,
) -> str:
    """Get temperature for a city."""
    return f"22 {unit.value} in {city}"
```

## Async Tools

Tools can be async:

```python
@tool
async def fetch_data(url: Annotated[str, "URL to fetch"]) -> str:
    """Fetch data from a URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

## Tool Execution Flow

```
User message → LLM decides to call tool → Framework executes tool function
→ Tool result sent back to LLM → LLM generates final response
```

The LLM can call multiple tools in sequence before generating a final response. The framework handles the entire tool call loop automatically.

## Tool Approval (Human-in-the-Loop)

For sensitive tools, you can require approval before execution using function middleware:

```python
from agent_framework import FunctionInvocationContext
from collections.abc import Awaitable, Callable

async def approval_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    """Require approval for sensitive tools."""
    sensitive_tools = ["send_email", "delete_record", "make_payment"]

    if context.function.name in sensitive_tools:
        # In production: prompt user for approval
        print(f"⚠️  Tool '{context.function.name}' requires approval")
        print(f"   Arguments: {context.arguments}")
        approved = input("Approve? (y/n): ").lower() == "y"

        if not approved:
            context.terminate = True
            return

    await next(context)

# Register middleware
agent = client.as_agent(
    tools=[send_email, search_docs],
    middleware=[approval_middleware],
)
```

## Real-World Tool Examples

### Database Query Tool
```python
@tool
async def query_database(
    sql: Annotated[str, "SQL query to execute"],
    database: Annotated[str, "Database name"] = "main",
) -> str:
    """Execute a read-only SQL query against the database."""
    # Use connection pool
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(sql)
        return json.dumps([dict(r) for r in rows])
```

### API Integration Tool
```python
@tool
async def create_ticket(
    title: Annotated[str, "Ticket title"],
    description: Annotated[str, "Detailed description"],
    priority: Annotated[str, "Priority: low, medium, high"] = "medium",
) -> str:
    """Create a support ticket in the ticketing system."""
    ticket = await ticketing_api.create(
        title=title,
        description=description,
        priority=priority,
    )
    return f"Created ticket #{ticket.id}: {ticket.url}"
```

## Tips

- Keep tool functions focused — one tool = one action
- Return strings — the LLM needs to read the result
- Include error handling — return error messages as strings, don't raise
- Use descriptive docstrings — the LLM uses them to decide when to call the tool
- Parameter descriptions matter — they guide the LLM on what to pass
