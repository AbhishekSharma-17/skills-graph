# MCP Tools (Model Context Protocol)

MCP provides a standardized interface for connecting agents to external systems — file systems, databases, APIs, and any MCP-compliant server.

## Basic Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.mcp import MCPTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[MCPTools(url="https://mcp-server.example.com/sse")],
    markdown=True,
)
agent.print_response("List files in the project directory")
```

## Connection Management

### Automatic (Recommended)

When passed to an Agent or Team, connections are managed automatically:

```python
# Agent handles connect/disconnect lifecycle
agent = Agent(
    tools=[MCPTools(url="https://mcp-server.example.com/sse")],
)
agent.print_response("Do something")
# Connection cleaned up after the run
```

### Manual

```python
from agno.tools.mcp import MCPTools

mcp = MCPTools(url="https://mcp-server.example.com/sse")
mcp.connect()

agent = Agent(tools=[mcp])
agent.print_response("Do something")

mcp.close()
```

### Async Context Manager

```python
import asyncio
from agno.tools.mcp import MCPTools

async def main():
    async with MCPTools(url="https://mcp-server.example.com/sse") as mcp:
        agent = Agent(tools=[mcp])
        await agent.aprint_response("Do something")

asyncio.run(main())
```

## Transport Types

### Streamable HTTP (Default for URL)

```python
mcp = MCPTools(url="https://mcp-server.example.com/mcp")
```

### SSE (Server-Sent Events)

```python
mcp = MCPTools(url="https://mcp-server.example.com/sse")
```

### stdio (Local Process)

For MCP servers that run as local processes:

```python
from agno.tools.mcp import MCPTools, StdioTransport

transport = StdioTransport(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
)

mcp = MCPTools(transport=transport)
```

## Connection Refresh

For long-running agents, refresh the MCP connection on each run:

```python
mcp = MCPTools(
    url="https://mcp-server.example.com/sse",
    refresh_connection=True,  # Reconnect before each agent run
)
```

## Filesystem Agent Example

```python
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.mcp import MCPTools, StdioTransport

async def main():
    transport = StdioTransport(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"],
    )

    async with MCPTools(transport=transport) as mcp:
        agent = Agent(
            model=OpenAIResponses(id="gpt-5.2"),
            tools=[mcp],
            instructions=[
                "You have access to a filesystem. Use the tools to explore and manage files.",
            ],
            markdown=True,
        )
        await agent.aprint_response("List all Python files and show the project structure")

asyncio.run(main())
```

## Combining MCP with Other Tools

```python
from agno.tools.mcp import MCPTools
from agno.tools.python import PythonTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[
        MCPTools(url="https://mcp-server.example.com/sse"),
        PythonTools(),
    ],
    markdown=True,
)
```

## MCPTools Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | `None` | MCP server URL (HTTP or SSE) |
| `transport` | `Transport` | `None` | Custom transport (e.g., StdioTransport) |
| `refresh_connection` | `bool` | `False` | Reconnect before each run |
