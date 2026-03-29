# Claude Agent SDK — Custom Tools

> Source: [platform.claude.com/docs/en/agent-sdk](https://platform.claude.com/docs/en/agent-sdk/overview) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [How Custom Tools Work](#how-custom-tools-work)
- [Python: @tool Decorator](#python-tool-decorator)
- [TypeScript: tool() Function](#typescript-tool-function)
- [Input Schemas](#input-schemas)
- [Return Types](#return-types)
- [Tool Annotations](#tool-annotations)
- [Creating an MCP Server](#creating-an-mcp-server)
- [Connecting Tools to an Agent](#connecting-tools-to-an-agent)
- [Error Handling](#error-handling)
- [Advanced Patterns](#advanced-patterns)
- [Common Pitfalls](#common-pitfalls)

## How Custom Tools Work

Custom tools are implemented as in-process MCP servers. The flow:

1. Define tool functions with `@tool` (Python) or `tool()` (TypeScript)
2. Bundle them into an SDK MCP server with `create_sdk_mcp_server()` / `createSdkMcpServer()`
3. Pass the server to `ClaudeAgentOptions.mcp_servers`
4. Tools become available as `mcp__{server_name}__{tool_name}`

This runs entirely in-process — no subprocess or network overhead.

### Tool Naming Convention

```
mcp__{server_name}__{tool_name}

Examples:
  mcp__validators__validate_email    ← specific tool
  mcp__validators__*                 ← all tools from validators server
  mcp__github__get_issue             ← specific MCP tool
```

**Used in:** `allowed_tools`, `disallowed_tools`, and `mcp_servers` keys.

### Claude Tool Call Format

When Claude invokes a custom tool, it sends:

```json
{
  "type": "tool_use",
  "id": "tooluse_abc123",
  "name": "mcp__validators__validate_email",
  "input": {
    "email": "user@example.com"
  }
}
```

Your handler receives `args = {"email": "user@example.com"}` and must return the content block format.

## Python: @tool Decorator

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool(
    name="get_weather",
    description="Get current weather for a city",
    input_schema={"city": str, "units": str},
)
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    city = args["city"]
    units = args.get("units", "celsius")
    # ... fetch weather data ...
    return {
        "content": [{"type": "text", "text": f"Weather in {city}: 22{units[0].upper()}"}]
    }
```

### Decorator Signature

```python
@tool(
    name: str,                          # Tool name (used in mcp__{server}__{name})
    description: str,                   # What the tool does (shown to Claude)
    input_schema: dict | dict[str, Any], # Parameter definitions
    annotations: ToolAnnotations = None, # Optional hints
)
```

### Sync vs Async

Both sync and async handlers are supported:

```python
# Async (preferred for I/O operations)
@tool("fetch_data", "Fetch data from API", {"url": str})
async def fetch_data(args: dict[str, Any]) -> dict[str, Any]:
    ...

# Sync (fine for CPU-bound or simple operations)
@tool("calculate", "Do math", {"expression": str})
def calculate(args: dict[str, Any]) -> dict[str, Any]:
    ...
```

## TypeScript: tool() Function

```typescript
import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

const getWeather = tool(
  "get_weather",
  "Get current weather for a city",
  { city: z.string(), units: z.string().optional() },
  async (args) => {
    const { city, units = "celsius" } = args;
    return {
      content: [{ type: "text", text: `Weather in ${city}: 22${units[0].toUpperCase()}` }],
    };
  },
  { annotations: { readOnlyHint: true } }
);
```

### Function Signature

```typescript
function tool<Schema extends AnyZodRawShape>(
  name: string,
  description: string,
  inputSchema: Schema,              // Zod schema (supports Zod 3 and 4)
  handler: (args: InferShape<Schema>, extra: unknown) => Promise<CallToolResult>,
  extras?: { annotations?: ToolAnnotations }
): SdkMcpToolDefinition<Schema>;
```

## Input Schemas

### Python: Simple Dict

Map parameter names to Python types:

```python
@tool("search", "Search documents", {
    "query": str,
    "limit": int,
    "include_metadata": bool,
})
```

### Python: JSON Schema (Advanced)

For enums, ranges, optional fields, and nested objects:

```python
@tool("create_issue", "Create a GitHub issue", {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Issue title"},
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "labels": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Labels to apply",
        },
        "assignee": {"type": "string", "description": "GitHub username"},
    },
    "required": ["title", "priority"],
})
```

### TypeScript: Zod Schema

```typescript
const createIssue = tool(
  "create_issue",
  "Create a GitHub issue",
  {
    title: z.string().describe("Issue title"),
    priority: z.enum(["low", "medium", "high"]),
    labels: z.array(z.string()).optional().describe("Labels to apply"),
    assignee: z.string().optional().describe("GitHub username"),
  },
  async (args) => { ... }
);
```

Both Zod 3 and Zod 4 are supported.

## Return Types

Tools must return an object with a `content` array. Each element is a content block:

### Text Content

```python
return {
    "content": [{"type": "text", "text": "Operation completed successfully"}]
}
```

### Image Content

```python
import base64

return {
    "content": [{
        "type": "image",
        "data": base64.b64encode(image_bytes).decode(),
        "mimeType": "image/png",
    }]
}
```

### Resource Content

```python
return {
    "content": [{
        "type": "resource",
        "resource": {
            "uri": "file:///path/to/output.json",
            "text": json.dumps(data),
            "mimeType": "application/json",
        }
    }]
}
```

### Multiple Content Blocks

```python
return {
    "content": [
        {"type": "text", "text": "Found 3 results:"},
        {"type": "text", "text": json.dumps(results, indent=2)},
        {"type": "image", "data": chart_b64, "mimeType": "image/png"},
    ]
}
```

### Error Response

Return `is_error: True` to signal an error **without** stopping the agent loop:

```python
return {
    "content": [{"type": "text", "text": "API rate limit exceeded, try again later"}],
    "is_error": True,
}
```

> **Important:** Returning `is_error: True` keeps the agent loop alive — Claude will see the error and can retry or try a different approach. Raising an exception stops the entire `query()`.

## Tool Annotations

Annotations hint to Claude and the SDK about tool behavior:

```python
from claude_agent_sdk import ToolAnnotations

@tool(
    "delete_file",
    "Delete a file from the project",
    {"path": str},
    annotations=ToolAnnotations(
        title="Delete File",
        readOnlyHint=False,       # Default: False — tool may modify state
        destructiveHint=True,     # Default: True — tool may destroy data
        idempotentHint=False,     # Default: False — repeated calls may differ
        openWorldHint=True,       # Default: True — tool interacts with external world
    ),
)
```

```typescript
const deleteTool = tool(
  "delete_file", "Delete a file", { path: z.string() },
  async (args) => { ... },
  {
    annotations: {
      title: "Delete File",
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: false,
      openWorldHint: true,
    },
  }
);
```

| Annotation | Default | Meaning |
|-----------|---------|---------|
| `readOnlyHint` | `false` | `true` = tool only reads, never writes |
| `destructiveHint` | `true` | `true` = tool may destroy data |
| `idempotentHint` | `false` | `true` = safe to call multiple times |
| `openWorldHint` | `true` | `true` = interacts with external systems |

## Creating an MCP Server

Bundle tools into a server:

### Python

```python
from claude_agent_sdk import create_sdk_mcp_server

server = create_sdk_mcp_server(
    name="my_tools",
    version="1.0.0",
    tools=[get_weather, create_issue, delete_file],
)
```

### TypeScript

```typescript
import { createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";

const server = createSdkMcpServer({
  name: "my_tools",
  version: "1.0.0",
  tools: [getWeather, createIssue, deleteTool],
});
```

## Connecting Tools to an Agent

### Python

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    mcp_servers={"my_tools": server},
    allowed_tools=["mcp__my_tools__*"],  # Pre-approve all tools
)

async for msg in query(prompt="What's the weather in Tokyo?", options=options):
    ...
```

### TypeScript

```typescript
const q = query({
  prompt: "What's the weather in Tokyo?",
  options: {
    mcpServers: { my_tools: server },
    allowedTools: ["mcp__my_tools__*"],
  },
});
```

**Tool naming convention:** `mcp__{server_name}__{tool_name}`

## Error Handling

### Graceful Errors (Keep Agent Running)

```python
@tool("api_call", "Call external API", {"endpoint": str})
async def api_call(args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = await fetch(args["endpoint"])
        return {"content": [{"type": "text", "text": json.dumps(result)}]}
    except TimeoutError:
        return {
            "content": [{"type": "text", "text": "API timeout — try a different endpoint"}],
            "is_error": True,
        }
```

### Fatal Errors (Stop Agent)

```python
@tool("critical_op", "Critical operation", {"data": str})
async def critical_op(args: dict[str, Any]) -> dict[str, Any]:
    if not validate(args["data"]):
        raise ValueError("Invalid data — cannot proceed")  # Stops query()
    ...
```

## Advanced Patterns

### Tool with Database Access

```python
@tool("query_db", "Run a read-only SQL query", {
    "type": "object",
    "properties": {
        "sql": {"type": "string", "description": "SQL SELECT query"},
    },
    "required": ["sql"],
})
async def query_db(args: dict[str, Any]) -> dict[str, Any]:
    sql = args["sql"]
    if not sql.strip().upper().startswith("SELECT"):
        return {
            "content": [{"type": "text", "text": "Only SELECT queries allowed"}],
            "is_error": True,
        }
    rows = await db.fetch_all(sql)
    return {"content": [{"type": "text", "text": json.dumps(rows, default=str)}]}
```

### Tool Calling External APIs

```python
@tool("github_search", "Search GitHub repositories", {"query": str, "language": str})
async def github_search(args: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": f"{args['query']} language:{args['language']}"},
            headers={"Authorization": f"token {os.environ['GITHUB_TOKEN']}"},
        )
        data = resp.json()
    results = [{"name": r["full_name"], "stars": r["stargazers_count"]} for r in data["items"][:5]]
    return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}
```

## Complete End-to-End Example

Two custom tools packaged into one MCP server and used in an agent:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, query, ClaudeAgentOptions
import json
import re
import hashlib


@tool(
    name="validate_email",
    description="Validate an email address and extract its parts (username, domain)",
    input_schema={
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "Email address to check",
            }
        },
        "required": ["email"],
    },
)
async def validate_email(args: dict) -> dict:
    email = args["email"]
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    is_valid = bool(re.match(pattern, email))

    username, domain = (email.split("@", 1) if "@" in email else (email, None))

    result = {
        "email": email,
        "is_valid": is_valid,
        "username": username,
        "domain": domain,
    }
    return {"content": [{"type": "text", "text": json.dumps(result)}]}


@tool(
    name="calculate_hash",
    description="Calculate the MD5 or SHA256 hash of a string",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to hash"},
            "algorithm": {
                "type": "string",
                "enum": ["md5", "sha256"],
                "description": "Hash algorithm to use",
            },
        },
        "required": ["text", "algorithm"],
    },
)
async def calculate_hash(args: dict) -> dict:
    text = args["text"]
    algo = args["algorithm"]
    if algo == "md5":
        result = hashlib.md5(text.encode()).hexdigest()
    else:
        result = hashlib.sha256(text.encode()).hexdigest()
    return {"content": [{"type": "text", "text": result}]}


# Package both tools into one in-process MCP server
server = create_sdk_mcp_server(
    name="validators",
    version="1.0.0",
    tools=[validate_email, calculate_hash],
)

# Use the server in an agent
options = ClaudeAgentOptions(
    model="sonnet",
    mcp_servers={"validators": server},
    allowed_tools=[
        "mcp__validators__validate_email",
        "mcp__validators__calculate_hash",
    ],
    permission_mode="bypassPermissions",
)

async def main():
    async for message in query(
        prompt="Validate admin@example.com and hash it with SHA256",
        options=options,
    ):
        print(message)
```

**Tool naming in this example:**
- Server name: `"validators"`
- Tool 1: `mcp__validators__validate_email`
- Tool 2: `mcp__validators__calculate_hash`
- Wildcard: `mcp__validators__*`

---

## Common Pitfalls

1. **Raising exceptions stops `query()`** — use `is_error: True` in the return value to report errors gracefully
2. **Tool names must be unique** within a server — duplicates silently overwrite
3. **Server names must be unique** across all `mcp_servers` entries
4. **Input schema types** — Python simple dict only supports basic types (`str`, `int`, `float`, `bool`); use JSON Schema dict for enums, arrays, optional fields
5. **Content block format** — always return `{"content": [{"type": "text", "text": "..."}]}`, not a plain string
6. **Tool naming** — tools are referenced as `mcp__{server}__{name}` in `allowed_tools` and `disallowed_tools`

## Related Topics

- [MCP Integration](04-mcp-integration.md) — External MCP servers
- [Built-in Tools](02-built-in-tools.md) — Available built-in tools
- [Hooks](05-hooks.md) — Intercept tool execution
