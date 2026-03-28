# Claude Agent SDK — MCP Integration

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [What Is MCP](#what-is-mcp)
- [Transport Types](#transport-types)
- [Configuring MCP Servers](#configuring-mcp-servers)
- [Tool Naming Convention](#tool-naming-convention)
- [Authentication](#authentication)
- [.mcp.json Configuration](#mcpjson-configuration)
- [Tool Search](#tool-search)
- [Checking MCP Status](#checking-mcp-status)
- [Dynamic Server Management](#dynamic-server-management)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## What Is MCP

The Model Context Protocol (MCP) is an open standard for connecting AI agents to external systems — databases, APIs, browsers, and more. The Claude Agent SDK supports MCP natively, allowing you to connect to any MCP-compatible server.

MCP servers expose **tools** (actions the agent can take) and **resources** (data the agent can read). The SDK discovers tools automatically and makes them available to Claude.

## Transport Types

| Type | Use Case | Configuration |
|------|----------|--------------|
| **stdio** | Local processes, CLI tools | `{command, args, env}` |
| **HTTP** | Cloud-hosted servers | `{type: "http", url, headers}` |
| **SSE** | Server-sent events streaming | `{type: "sse", url, headers}` |
| **SDK** | In-process custom tools | `{type: "sdk", name, instance}` |

### stdio — Local Process

Launches a subprocess and communicates via stdin/stdout.

```python
# Python
options = ClaudeAgentOptions(
    mcp_servers={
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]},
        }
    }
)
```

```typescript
// TypeScript
const q = query({
  prompt: "...",
  options: {
    mcpServers: {
      github: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-github"],
        env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN },
      },
    },
  },
});
```

### HTTP — Cloud Server

Connects to a remote MCP server over HTTP.

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "remote_db": {
            "type": "http",
            "url": "https://mcp.example.com/db",
            "headers": {"Authorization": "Bearer sk-..."},
        }
    }
)
```

### SSE — Server-Sent Events

Streaming transport for real-time communication.

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "streaming": {
            "type": "sse",
            "url": "https://mcp.example.com/stream",
            "headers": {"Authorization": "Bearer sk-..."},
        }
    }
)
```

### SDK — In-Process

For custom tools created with `create_sdk_mcp_server()`. No subprocess overhead.

```python
from claude_agent_sdk import create_sdk_mcp_server, tool

@tool("my_tool", "Does something", {"input": str})
async def my_tool(args):
    return {"content": [{"type": "text", "text": "done"}]}

server = create_sdk_mcp_server(name="my_server", version="1.0.0", tools=[my_tool])

options = ClaudeAgentOptions(
    mcp_servers={"my_server": server},  # In-process, no subprocess
)
```

## Configuring MCP Servers

### Multiple Servers

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": token},
        },
        "postgres": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres", db_url],
        },
        "custom": custom_sdk_server,  # SDK transport
    },
    allowed_tools=[
        "mcp__github__*",       # All GitHub tools
        "mcp__postgres__query",  # Only query tool from Postgres
    ],
)
```

### From Config File

```python
# Load from a JSON file path
options = ClaudeAgentOptions(
    mcp_servers="/path/to/.mcp.json",
)
```

## Tool Naming Convention

MCP tools follow the naming pattern: `mcp__{server_name}__{tool_name}`

Examples:
- `mcp__github__create_issue` — the `create_issue` tool from the `github` server
- `mcp__postgres__query` — the `query` tool from the `postgres` server
- `mcp__my_server__my_tool` — custom tool from an SDK server

### Wildcards

Use `*` in `allowed_tools` and `disallowed_tools`:

```python
allowed_tools=["mcp__github__*"]      # All tools from github server
disallowed_tools=["mcp__*__delete_*"]  # Block all delete tools from all servers
```

## Authentication

### Environment Variables (stdio)

```python
mcp_servers={
    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
            "GITHUB_TOKEN": os.environ["GITHUB_TOKEN"],
        },
    }
}
```

### Headers (HTTP/SSE)

```python
mcp_servers={
    "api": {
        "type": "http",
        "url": "https://mcp.example.com/api",
        "headers": {
            "Authorization": "Bearer " + os.environ["API_TOKEN"],
            "X-API-Key": os.environ["API_KEY"],
        },
    }
}
```

### OAuth2

Pass the OAuth2 access token via headers:

```python
mcp_servers={
    "service": {
        "type": "http",
        "url": "https://mcp.service.com/v1",
        "headers": {"Authorization": f"Bearer {oauth_access_token}"},
    }
}
```

## .mcp.json Configuration

The SDK can automatically load MCP server configs from a `.mcp.json` file in the working directory:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

> **Note:** `.mcp.json` is only loaded when `setting_sources` includes `"project"`. By default, `setting_sources` is `[]` and no filesystem configs are loaded.

## Tool Search

Tool search is enabled by default. When many MCP tools are available, the SDK withholds tool definitions from the context window and loads only relevant tools per turn.

**How it works:**
1. SDK registers all MCP tools but doesn't include definitions in context
2. Each turn, Claude uses `ToolSearch` to find relevant tools
3. Only matched tool definitions are loaded into context
4. Saves significant context window space with many tools

**Disable tool search:**

```python
# Load all tool definitions into context always
options = ClaudeAgentOptions(extra_args={"--no-tool-search": None})
```

## Checking MCP Status

### Python

```python
client = ClaudeSDKClient(options)
async with client:
    await client.connect()
    status = await client.get_mcp_status()
    for server in status.servers:
        print(f"{server.name}: {server.status}")
```

### TypeScript

```typescript
const q = query({ prompt: "...", options: {...} });
for await (const msg of q) {
    if (msg.type === "system" && msg.subtype === "init") {
        for (const server of msg.mcp_servers ?? []) {
            console.log(`${server.name}: ${server.status}`);
        }
    }
}
```

Check the `system:init` message for `mcp_servers` array — each entry has a `status` field (`"connected"` or error details).

## Dynamic Server Management

### Reconnect a Failed Server

```python
# Python
await client.reconnect_mcp_server("github")

# TypeScript
await q.reconnectMcpServer("github");
```

### Toggle Server On/Off

```python
# Python
await client.toggle_mcp_server("github", enabled=False)
await client.toggle_mcp_server("github", enabled=True)

# TypeScript
await q.toggleMcpServer("github", false);
await q.toggleMcpServer("github", true);
```

### TypeScript: Set Servers Mid-Session

```typescript
await q.setMcpServers({
  newServer: { command: "npx", args: [...] },
});
```

## Common Patterns

### GitHub + Database Agent

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": {"GITHUB_TOKEN": token}},
        "postgres": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres", db_url]},
    },
    allowed_tools=["mcp__github__*", "mcp__postgres__query"],
    disallowed_tools=["mcp__postgres__execute"],  # Read-only DB access
)
```

### Mixing SDK and External Servers

```python
custom_server = create_sdk_mcp_server(name="analytics", tools=[...])

options = ClaudeAgentOptions(
    mcp_servers={
        "analytics": custom_server,                    # In-process
        "github": {"command": "npx", "args": [...]},  # External process
        "api": {"type": "http", "url": "https://..."},  # Remote
    },
)
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Server not connecting | Wrong command/args | Check `command` exists in PATH |
| Tools not visible | `setting_sources` empty | Set `setting_sources=["project"]` or configure inline |
| Auth errors | Missing env vars | Pass via `env` field, not system env |
| Tool not found | Wrong naming | Use `mcp__{server}__{tool}` format |
| Context overflow | Too many tools | Enable tool search (default) or reduce servers |

## Related Topics

- [Custom Tools](03-custom-tools.md) — Build in-process tools with SDK transport
- [Built-in Tools](02-built-in-tools.md) — Available built-in tools
- [Configuration](01-configuration.md) — Full options reference
