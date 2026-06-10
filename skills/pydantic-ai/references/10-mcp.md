# MCP Integration

> Source: [pydantic.dev/docs/ai/mcp/overview](https://pydantic.dev/docs/ai/mcp/overview/)

## Table of Contents

- [Overview](#overview)
- [MCP Client — Connecting to Servers](#mcp-client--connecting-to-servers)
- [FastMCP Toolset](#fastmcp-toolset)
- [Native MCP Tools](#native-mcp-tools)
- [MCP Server Mode](#mcp-server-mode)
- [On-Demand MCP Loading](#on-demand-mcp-loading)
- [Common Pitfalls](#common-pitfalls)

## Overview

Pydantic AI supports the Model Context Protocol (MCP) in four ways:

1. **MCP Client** — connect to MCP servers and use their tools in agents
2. **FastMCP Toolset** — connect via the FastMCP Client library
3. **Native MCP Tools** — let providers connect to MCP servers natively
4. **MCP Server Mode** — expose agents as MCP tools for other clients

## MCP Client — Connecting to Servers

Connect to local or remote MCP servers using `MCPServer`:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServer

# Connect to a stdio-based MCP server
server = MCPServer(
    command='npx',
    args=['-y', '@modelcontextprotocol/server-filesystem', '/tmp'],
)

agent = Agent('openai:gpt-5.2', capabilities=[server])

async def main():
    async with server:
        result = await agent.run('List files in /tmp')
        print(result.output)
```

### SSE Transport (Remote Servers)

```python
from pydantic_ai.mcp import MCPServer

server = MCPServer(url='https://mcp-server.example.com/sse')

agent = Agent('openai:gpt-5.2', capabilities=[server])

async def main():
    async with server:
        result = await agent.run('Search for documents')
```

### Multiple MCP Servers

```python
filesystem = MCPServer(command='npx', args=['-y', '@mcp/server-filesystem', '/data'])
database = MCPServer(command='npx', args=['-y', '@mcp/server-postgres', 'postgresql://...'])

agent = Agent(
    'openai:gpt-5.2',
    capabilities=[filesystem, database],
)

async def main():
    async with filesystem, database:
        result = await agent.run('Query orders and save to file')
```

## FastMCP Toolset

Use the FastMCP Client library for connecting to MCP servers:

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

# Connect to a FastMCP server
toolset = FastMCPToolset('http://localhost:8000/mcp')

agent = Agent('openai:gpt-5.2', tools=[toolset])

async def main():
    async with toolset:
        result = await agent.run('Use the server tools')
```

### Building a FastMCP Server

```python
from fastmcp import FastMCP

mcp = FastMCP("My Tools")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool()
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

# Run: fastmcp run server.py
```

Then connect from Pydantic AI:

```python
toolset = FastMCPToolset('http://localhost:8000/mcp')
agent = Agent('openai:gpt-5.2', tools=[toolset])
```

## Native MCP Tools

Some providers connect to MCP servers natively (server-side):

```python
from pydantic_ai import Agent
from pydantic_ai.native_tools import MCPServerTool

mcp_tool = MCPServerTool(
    server_label='filesystem',
    server_url='https://mcp-server.example.com/sse',
    allowed_tools=['list_files', 'read_file'],
)

agent = Agent(
    'openai-responses:gpt-5.2',
    native_tools=[mcp_tool],
)
```

Native MCP tools execute on the provider side, reducing latency for provider-supported servers.

## MCP Server Mode

Expose a Pydantic AI agent as an MCP server:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import AgentMCPServer

agent = Agent(
    'openai:gpt-5.2',
    instructions='You are a helpful code assistant.',
)

@agent.tool_plain
def analyze_code(code: str) -> str:
    """Analyze Python code for issues."""
    return f"Analysis of code: {len(code)} chars"

# Expose as MCP server
mcp_server = AgentMCPServer(agent)

# Run as stdio server
if __name__ == '__main__':
    mcp_server.run_stdio()
```

Other MCP clients (Claude Desktop, VS Code, etc.) can connect to your agent as a tool.

## On-Demand MCP Loading

Defer MCP server loading until the model needs it:

```python
from pydantic_ai.mcp import MCPServer

server = MCPServer(
    command='npx',
    args=['-y', '@mcp/server-postgres', 'postgresql://...'],
    defer_loading=True,
    id='database',
    description='Use for database queries and schema inspection.',
)

agent = Agent('openai:gpt-5.2', capabilities=[server])
```

The MCP server starts only when the model calls `load_capability(id='database')`, saving resources when the tools aren't needed.

## Common Pitfalls

- **Forgetting async context** — MCP servers need `async with server:` to manage the connection lifecycle
- **Stdio vs SSE** — stdio servers (`command=`) run as subprocesses; SSE servers (`url=`) connect over HTTP
- **Tool name conflicts** — MCP tools may conflict with agent-defined tools; use `PrefixTools` or `allowed_tools` to manage
- **Native MCP limitations** — not all providers support native MCP; falls back to client-side
- **Server cleanup** — always use `async with` or explicit `close()` to clean up MCP server connections

## Related

- `05-capabilities.md` — Capabilities and on-demand loading
- `04-tools.md` — Function tools
- `08-models.md` — Provider-specific features
