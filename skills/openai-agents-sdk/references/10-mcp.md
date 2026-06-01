# MCP Integration — Model Context Protocol

> Source: [openai.github.io/openai-agents-python/mcp](https://openai.github.io/openai-agents-python/mcp/)

## Table of Contents

- [Overview](#overview)
- [Transport Options](#transport-options)
- [Hosted MCP Tools](#hosted-mcp-tools)
- [Streamable HTTP](#streamable-http)
- [stdio Servers](#stdio-servers)
- [MCP Server Manager](#mcp-server-manager)
- [Tool Filtering](#tool-filtering)
- [Approval Policies](#approval-policies)
- [Agent-Level Configuration](#agent-level-configuration)
- [MCP Prompts](#mcp-prompts)

## Overview

The Model Context Protocol (MCP) standardizes how applications expose tools and context to LLMs. The SDK supports five MCP integration approaches, from fully hosted to local subprocess servers.

## Transport Options

| Transport | Class | Use When |
|-----------|-------|----------|
| **Hosted MCP** | `HostedMCPTool` | Remote MCP servers run on OpenAI infrastructure |
| **Streamable HTTP** | `MCPServerStreamableHttp` | Self-hosted HTTP servers you control |
| **SSE** (deprecated) | `MCPServerSse` | Legacy Server-Sent Events servers |
| **stdio** | `MCPServerStdio` | Local subprocess servers |
| **Manager** | `MCPServerManager` | Connect multiple servers at once |

## Hosted MCP Tools

Push tool execution to OpenAI's infrastructure — no callbacks to your Python process:

```python
from agents import Agent
from agents.tool import HostedMCPTool

agent = Agent(
    name="Assistant",
    instructions="Use the DeepWiki MCP server to research repositories.",
    tools=[
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "deepwiki",
                "server_url": "https://mcp.deepwiki.com/mcp",
                "require_approval": "never",
            }
        )
    ],
)
```

### Connector-Backed Servers

```python
HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_label": "google_calendar",
        "connector_id": "connector_googlecalendar",
        "authorization": os.environ["GOOGLE_CALENDAR_AUTH"],
        "require_approval": "never",
    }
)
```

## Streamable HTTP

For MCP servers you host yourself:

```python
from agents import Agent, Runner, ModelSettings
from agents.mcp import MCPServerStreamableHttp

async with MCPServerStreamableHttp(
    name="Math Server",
    params={
        "url": "http://localhost:8000/mcp",
        "headers": {"Authorization": f"Bearer {token}"},
        "timeout": 10,
    },
    cache_tools_list=True,
    max_retry_attempts=3,
) as server:
    agent = Agent(
        name="Assistant",
        instructions="Use the MCP tools to answer questions.",
        mcp_servers=[server],
    )
    result = await Runner.run(agent, "Add 7 and 22.")
```

### Constructor Options

| Option | Purpose |
|--------|---------|
| `cache_tools_list` | Cache tool definitions to reduce latency |
| `max_retry_attempts` | Automatic retries on failure |
| `retry_backoff_seconds_base` | Base delay between retries |
| `client_session_timeout_seconds` | HTTP read timeout |
| `tool_filter` | Expose specific tools only |
| `require_approval` | Human-in-the-loop policies |
| `failure_error_function` | Customize error messages |
| `tool_meta_resolver` | Inject per-call metadata |

### Per-Call Metadata

```python
from agents.mcp import MCPToolMetaContext

def resolve_meta(context: MCPToolMetaContext) -> dict[str, str] | None:
    tenant_id = context.run_context.context.get("tenant_id")
    if tenant_id is None:
        return None
    return {"tenant_id": str(tenant_id), "source": "agents-sdk"}

server = MCPServerStreamableHttp(
    name="Multi-Tenant MCP",
    params={"url": "http://localhost:8000/mcp"},
    tool_meta_resolver=resolve_meta,
)
```

## stdio Servers

Local subprocess servers — the SDK spawns, maintains, and closes pipes:

```python
from agents.mcp import MCPServerStdio

async with MCPServerStdio(
    name="Filesystem Server",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", str(data_dir)],
    },
) as server:
    agent = Agent(
        name="File Assistant",
        instructions="Use the filesystem tools to read and list files.",
        mcp_servers=[server],
    )
    result = await Runner.run(agent, "List all files in the directory.")
```

## MCP Server Manager

Connect multiple servers at once with fault tolerance:

```python
from agents.mcp import MCPServerManager, MCPServerStreamableHttp

servers = [
    MCPServerStreamableHttp(name="calendar", params={"url": "http://localhost:8000/mcp"}),
    MCPServerStreamableHttp(name="docs", params={"url": "http://localhost:8001/mcp"}),
    MCPServerStreamableHttp(name="search", params={"url": "http://localhost:8002/mcp"}),
]

async with MCPServerManager(servers, drop_failed_servers=True) as manager:
    print(f"Connected: {len(manager.active_servers)}")
    print(f"Failed: {len(manager.failed_servers)}")

    agent = Agent(
        name="Multi-Tool Agent",
        instructions="Use MCP tools as needed.",
        mcp_servers=manager.active_servers,
    )
    result = await Runner.run(agent, "What meetings do I have today?")
```

### Manager Options

| Option | Purpose |
|--------|---------|
| `drop_failed_servers` | Keep running with partial connectivity (default: `True`) |
| `strict` | Raise on first connection failure |
| `connect_timeout_seconds` | Connection timeout per server |
| `cleanup_timeout_seconds` | Cleanup timeout on exit |
| `connect_in_parallel` | Connect servers concurrently |

### Reconnecting Failed Servers

```python
await manager.reconnect(failed_only=True)
```

## Tool Filtering

### Static Filtering

```python
from agents.mcp import create_static_tool_filter

server = MCPServerStdio(
    params={"command": "npx", "args": [...]},
    tool_filter=create_static_tool_filter(
        allowed_tool_names=["read_file", "write_file"],
        # OR
        blocked_tool_names=["delete_file", "execute_command"],
    ),
)
```

When both `allowed_tool_names` and `blocked_tool_names` are provided, the allow-list is applied first, then blocked tools are removed.

### Dynamic Filtering

```python
from agents.mcp import ToolFilterContext

async def context_aware_filter(context: ToolFilterContext, tool) -> bool:
    if context.agent.name == "Read-Only Agent" and tool.name.startswith("write_"):
        return False
    return True

server = MCPServerStdio(
    params={"command": "npx", "args": [...]},
    tool_filter=context_aware_filter,
)
```

The filter receives `run_context`, the requesting `agent`, and `server_name`.

## Approval Policies

Control which MCP tools need human approval:

```python
# All tools require approval
server = MCPServerStreamableHttp(
    params={"url": "..."},
    require_approval="always",
)

# No tools require approval
server = MCPServerStreamableHttp(
    params={"url": "..."},
    require_approval="never",
)

# Per-tool policies
server = MCPServerStreamableHttp(
    params={"url": "..."},
    require_approval={
        "always": {"tool_names": ["delete_file", "send_email"]},
        "never": {"tool_names": ["read_file", "list_files"]},
    },
)
```

## Agent-Level Configuration

Configure MCP behavior per-agent:

```python
agent = Agent(
    name="Assistant",
    mcp_servers=[server],
    mcp_config={
        "convert_schemas_to_strict": True,
        "failure_error_function": None,
        "include_server_in_tool_names": True,
    },
)
```

| Option | Purpose |
|--------|---------|
| `convert_schemas_to_strict` | Convert MCP schemas to strict JSON (best-effort) |
| `failure_error_function` | How tool failures surface to the model (`None` raises) |
| `include_server_in_tool_names` | Prefix tool names with server name to avoid collisions |

## MCP Prompts

MCP servers can provide dynamic prompts for agent instructions:

```python
# List available prompts
prompts = await server.list_prompts()

# Get a specific prompt with arguments
prompt_result = await server.get_prompt(
    "generate_code_review_instructions",
    {"focus": "security", "language": "python"},
)

# Use as agent instructions
agent = Agent(
    name="Code Reviewer",
    instructions=prompt_result.messages[0].content.text,
    mcp_servers=[server],
)
```

## Caching

```python
# Cache tool definitions — safe if tools don't change frequently
server = MCPServerStreamableHttp(
    params={"url": "..."},
    cache_tools_list=True,
)

# Force refresh
server.invalidate_tools_cache()
```

## Common Pitfalls

- **Missing async context manager**: MCP servers must be used within `async with` blocks for proper lifecycle management
- **SSE transport deprecated**: Use Streamable HTTP or stdio for new integrations
- **Tool name collisions**: Multiple servers may expose tools with the same name; enable `include_server_in_tool_names`
- **Schema strictness**: Some MCP schemas aren't strict JSON; `convert_schemas_to_strict` does best-effort conversion
- **Cached stale tools**: With `cache_tools_list=True`, call `invalidate_tools_cache()` if server tools change

## Related Topics

- **Tools:** `02-tools.md` — Hosted tools and function tools
- **Models:** `09-models.md` — Provider configuration
- **Streaming:** `06-streaming.md` — MCP approvals during streaming
