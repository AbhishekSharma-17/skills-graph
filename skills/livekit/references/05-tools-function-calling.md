# Tools & Function Calling

> Source: [docs.livekit.io/agents/logic/tools](https://docs.livekit.io/agents/logic/tools/) — Function tools, provider tools, MCP

## Table of Contents

- [Tool Types](#tool-types)
- [Function Tools](#function-tools)
- [Tool Context](#tool-context)
- [Speech Within Tools](#speech-within-tools)
- [Dynamic Tools](#dynamic-tools)
- [Provider Tools](#provider-tools)
- [MCP Integration](#mcp-integration)
- [Frontend Tool Forwarding](#frontend-tool-forwarding)
- [Error Handling](#error-handling)
- [Common Patterns](#common-patterns)

---

## Tool Types

LiveKit supports two categories of tools:

1. **Function Tools** — Python/Node.js functions in your codebase that the LLM can call
2. **Provider Tools** — Built-in server-side tools from LLM providers (web search, code execution, etc.)

## Function Tools

Use the `@function_tool` decorator to expose functions to the LLM:

```python
from livekit.agents import function_tool, RunContext, AgentSession, Agent

@function_tool()
async def get_weather(
    context: RunContext,
    city: str,
) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to look up weather for.
    """
    # Call your weather API
    weather = await fetch_weather(city)
    return f"The weather in {city} is {weather.temp}°F and {weather.condition}"

# Register tools with the agent
agent = Agent(
    instructions="You are a helpful assistant with weather lookup capabilities.",
    tools=[get_weather],
)
```

**Key rules:**
- First parameter must be `RunContext` (injected automatically)
- Remaining parameters are exposed to the LLM
- Docstring becomes the tool description (critical for LLM understanding)
- Return a string — this is sent back to the LLM as the tool result
- Use type hints — they inform the LLM about expected parameter types

### Parameter Types

```python
@function_tool()
async def search_products(
    context: RunContext,
    query: str,                    # Required string
    category: str = "all",         # Optional with default
    max_results: int = 10,         # Integer parameter
    in_stock: bool = True,         # Boolean parameter
) -> str:
    """Search the product catalog.

    Args:
        query: Search query text.
        category: Product category filter.
        max_results: Maximum results to return.
        in_stock: Only show in-stock items.
    """
    results = await product_api.search(query, category, max_results, in_stock)
    return json.dumps([r.to_dict() for r in results])
```

## Tool Context

`RunContext` provides access to session state within tools:

```python
@function_tool()
async def check_order(context: RunContext, order_id: str) -> str:
    """Check the status of an order."""
    # Access the AgentSession
    session: AgentSession = context.session

    # Access userdata set on the session
    user_id = context.session.userdata.get("user_id")

    # Access the conversation history
    history = context.session.conversation

    return f"Order {order_id} is shipped"
```

## Speech Within Tools

Tools can make the agent speak while executing:

```python
@function_tool()
async def book_appointment(context: RunContext, date: str, time: str) -> str:
    """Book an appointment."""
    session = context.session

    # Speak while the tool is running
    await session.say("Let me check availability for that time.")

    available = await calendar_api.check(date, time)
    if available:
        await calendar_api.book(date, time)
        return "Appointment booked successfully."
    else:
        return "That time slot is not available."
```

**Important:** `session.say()` is non-blocking by default. The tool continues executing while speech plays.

## Dynamic Tools

Create tools programmatically (not via decorator):

```python
from livekit.agents import function_tool, FunctionTool

# Create a tool from a function at runtime
def make_db_query_tool(table_name: str) -> FunctionTool:
    async def query_table(context: RunContext, where_clause: str) -> str:
        """Query a database table."""
        results = await db.query(f"SELECT * FROM {table_name} WHERE {where_clause}")
        return json.dumps(results)

    return function_tool(
        name=f"query_{table_name}",
        description=f"Query the {table_name} database table",
    )(query_table)

# Register dynamic tools
tools = [make_db_query_tool("users"), make_db_query_tool("orders")]
agent = Agent(instructions="...", tools=tools)
```

## Provider Tools

Built-in server-side tools from LLM providers:

### OpenAI

```python
from livekit.plugins import openai

agent = Agent(
    instructions="Help users research topics.",
    tools=[
        openai.WebSearch(),         # Search the web
        openai.FileSearch(),        # Search uploaded files
        openai.CodeInterpreter(),   # Execute Python code
    ],
)
```

### Google Gemini

```python
from livekit.plugins import google

agent = Agent(
    tools=[
        google.GoogleSearch(),      # Google search
        google.GoogleMaps(),        # Maps and places
        google.URLContext(),         # Fetch and parse URLs
        google.ToolCodeExecution(), # Run code
    ],
)
```

### Anthropic

```python
from livekit.plugins import anthropic

agent = Agent(
    tools=[
        anthropic.ComputerUse(),    # Computer use
    ],
)
```

### xAI (Grok)

```python
from livekit.plugins import openai  # xAI uses OpenAI compat

agent = Agent(
    tools=[
        openai.WebSearch(),         # Web search
        openai.XSearch(),           # X/Twitter search
    ],
)
```

Provider tools and function tools can be mixed freely in the `tools` list.

## MCP Integration

LiveKit has native Model Context Protocol (MCP) support:

```python
from livekit.agents import AgentSession, Agent
from livekit.agents.mcp import MCPServerHTTP

# Connect to an MCP server
mcp_server = MCPServerHTTP(url="http://localhost:8080/mcp")

session = AgentSession(
    stt="deepgram/nova-3:en",
    llm="openai/gpt-4.1-mini",
    tts="cartesia/sonic-3:voice-id",
    mcp_servers=[mcp_server],  # LLM auto-discovers MCP tools
)
```

The LLM automatically discovers and uses tools exposed by MCP servers. No additional configuration needed.

**Multiple MCP servers:**

```python
session = AgentSession(
    mcp_servers=[
        MCPServerHTTP(url="http://localhost:8080/weather"),
        MCPServerHTTP(url="http://localhost:8081/calendar"),
    ],
)
```

## Frontend Tool Forwarding

Tools can be fulfilled on the frontend via RPC:

```python
@function_tool()
async def show_product(context: RunContext, product_id: str) -> str:
    """Show a product to the user in their browser."""
    session = context.session

    # Call a function on the frontend via RPC
    result = await session.room.local_participant.perform_rpc(
        destination_identity=session.linked_participant.identity,
        method="showProduct",
        payload=json.dumps({"product_id": product_id}),
    )

    return f"Product {product_id} displayed to user"
```

Frontend handler (React):

```javascript
room.localParticipant.registerRpcMethod('showProduct', async (data) => {
  const { product_id } = JSON.parse(data.payload);
  setActiveProduct(product_id);
  return JSON.stringify({ success: true });
});
```

## Error Handling

```python
@function_tool()
async def risky_operation(context: RunContext, param: str) -> str:
    """Perform an operation that might fail."""
    try:
        result = await external_api.call(param)
        return f"Success: {result}"
    except TimeoutError:
        return "The operation timed out. Please try again."
    except ValueError as e:
        return f"Invalid input: {e}"
    except Exception as e:
        # Return error as string — LLM can decide how to handle it
        return f"Error occurred: {e}"
```

**Best practice:** Return errors as strings rather than raising exceptions. The LLM can then communicate the error naturally to the user.

## Common Patterns

### Tool with session state

```python
@function_tool()
async def add_to_cart(context: RunContext, product_id: str, quantity: int = 1) -> str:
    """Add a product to the shopping cart."""
    cart = context.session.userdata.setdefault("cart", [])
    cart.append({"product_id": product_id, "quantity": quantity})
    return f"Added {quantity}x {product_id} to cart. Cart now has {len(cart)} items."
```

### Max tool steps

```python
# Limit consecutive tool calls (prevent infinite loops)
session = AgentSession(
    max_tool_steps=5,  # Default: 3
)
```

### Tool that triggers agent handoff

```python
@function_tool()
async def transfer_to_support(context: RunContext, reason: str) -> str:
    """Transfer the conversation to a human support agent."""
    # Handoff logic (see multi-agent workflows)
    await context.session.handoff(support_agent, reason=reason)
    return "Transferring to support."
```
