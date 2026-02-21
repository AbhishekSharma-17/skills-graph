# Tools — Function Calling, MCP, and Tool Patterns

## Table of Contents
1. [Function Tools](#function-tools)
2. [Tool Requirements](#tool-requirements)
3. [Advanced Tool Patterns](#advanced-tool-patterns)
4. [MCP Integration](#mcp-integration)
5. [Tool Approval (Human-in-the-Loop)](#tool-approval)
6. [Built-in Tools](#built-in-tools)
7. [OpenAPI Integration](#openapi-integration)
8. [Common Mistakes](#common-mistakes)

---

## Function Tools

The `@tool` decorator converts Python functions into agent-callable tools. The framework extracts the function's name, docstring, type hints, and annotations to build the JSON schema the LLM uses for function calling.

### Basic Tool

```python
from agent_framework import tool
from typing import Annotated

@tool
def get_weather(
    location: Annotated[str, "City name, e.g. 'San Francisco'"],
    unit: Annotated[str, "Temperature unit: 'celsius' or 'fahrenheit'"] = "celsius",
) -> str:
    """Get current weather for a location.

    Returns temperature, conditions, and humidity.
    """
    # Real implementation would call a weather API
    return f"Weather in {location}: 22°C, partly cloudy, 65% humidity"
```

### Async Tool

```python
@tool
async def fetch_data(
    url: Annotated[str, "URL to fetch data from"],
    timeout: Annotated[int, "Request timeout in seconds"] = 30,
) -> dict:
    """Fetch data from a URL and return parsed JSON"""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout) as resp:
            return await resp.json()
```

### Tool Returning Complex Types

```python
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

@tool
def search_docs(
    query: Annotated[str, "Search query"],
    max_results: Annotated[int, "Maximum results"] = 5,
) -> list[SearchResult]:
    """Search documentation and return matching results"""
    return [SearchResult(title="...", url="...", snippet="...")]
```

---

## Tool Requirements

Every tool function MUST satisfy these requirements:

### Required Elements

| Element | What | Why |
|---------|------|-----|
| `@tool` decorator | Marks function as tool | Framework discovers it |
| Docstring | Describes purpose | LLM uses it to decide when to call |
| Type hints | All params + return | Framework builds JSON schema |
| `Annotated` | Parameter descriptions | LLM understands each parameter |
| Return type | Explicit return type | Framework validates output |

### Correct vs Incorrect

```python
# CORRECT ✓
@tool
def good_tool(
    query: Annotated[str, "Search query to execute"],
    limit: Annotated[int, "Max number of results"] = 10,
) -> list[str]:
    """Search the knowledge base for relevant documents"""
    return ["result1", "result2"]

# INCORRECT ✗ — No type hints
@tool
def bad_no_types(query, limit=10):
    """Search"""
    return ["result"]

# INCORRECT ✗ — No docstring
@tool
def bad_no_doc(query: Annotated[str, "Query"]) -> list[str]:
    return ["result"]

# INCORRECT ✗ — No Annotated descriptions
@tool
def bad_no_annotations(query: str) -> list[str]:
    """Search"""
    return ["result"]

# INCORRECT ✗ — No return type
@tool
def bad_no_return(query: Annotated[str, "Query"]):
    """Search"""
    return ["result"]
```

### Supported Parameter Types

| Python Type | JSON Schema Type | Notes |
|-------------|-----------------|-------|
| `str` | `string` | Most common |
| `int` | `integer` | |
| `float` | `number` | |
| `bool` | `boolean` | |
| `list[T]` | `array` | Items typed as T |
| `dict[str, T]` | `object` | |
| `Optional[T]` | Nullable T | Use with default `None` |
| `Literal["a", "b"]` | `enum` | Restricts values |
| `BaseModel` | `object` | Complex structured input |

---

## Advanced Tool Patterns

### Tool with Enum-Like Constraints

```python
from typing import Literal

@tool
def set_priority(
    task_id: Annotated[str, "Task identifier"],
    priority: Annotated[Literal["low", "medium", "high", "critical"], "Priority level"],
) -> str:
    """Set priority level for a task"""
    return f"Task {task_id} priority set to {priority}"
```

### Tool with Complex Input

```python
from pydantic import BaseModel

class EmailDraft(BaseModel):
    to: list[str]
    subject: str
    body: str
    cc: list[str] = []

@tool
def send_email(
    email: Annotated[EmailDraft, "Email details to send"],
) -> str:
    """Send an email with the specified details"""
    return f"Email sent to {', '.join(email.to)}"
```

### Database Tool

```python
@tool
def query_database(
    sql: Annotated[str, "SQL query to execute (SELECT only)"],
    database: Annotated[str, "Database name"] = "production",
) -> list[dict]:
    """Execute a read-only SQL query against the database.

    Only SELECT statements are allowed. The agent should never
    attempt INSERT, UPDATE, or DELETE operations.
    """
    if not sql.strip().upper().startswith("SELECT"):
        return [{"error": "Only SELECT queries are allowed"}]
    # Execute query...
    return [{"result": "data"}]
```

### File Operation Tool

```python
@tool
def read_file(
    path: Annotated[str, "File path to read"],
    encoding: Annotated[str, "File encoding"] = "utf-8",
) -> str:
    """Read contents of a text file"""
    with open(path, "r", encoding=encoding) as f:
        return f.read()

@tool
def write_file(
    path: Annotated[str, "File path to write"],
    content: Annotated[str, "Content to write"],
) -> str:
    """Write content to a file"""
    with open(path, "w") as f:
        f.write(content)
    return f"Written {len(content)} characters to {path}"
```

---

## MCP Integration

Model Context Protocol (MCP) allows agents to discover and use tools from external servers dynamically.

### Hosted MCP Tools (Azure AI Foundry)

```python
# Use pre-configured MCP servers in Azure AI Foundry
agent = client.as_agent(
    name="MCPAgent",
    instructions="You have access to web search and file search.",
    mcp_servers=[
        "web-search",       # Bing-powered web search
        "file-search",      # Search uploaded documents
    ],
)
```

### Local MCP Server (stdio)

```python
from agent_framework.tools import MCPStdioTool

# Connect to a local MCP server
github_mcp = MCPStdioTool(
    name="github",
    command="npx",
    args=["@modelcontextprotocol/server-github"],
    env={"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]},
)

agent = client.as_agent(
    name="DevAgent",
    instructions="You help with GitHub operations.",
    tools=[github_mcp],
)
```

### Remote MCP Server (WebSocket)

```python
from agent_framework.tools import MCPWebSocketTool

remote_mcp = MCPWebSocketTool(
    name="company-tools",
    url="wss://mcp.company.com/tools",
    auth_token="bearer-token",
)

agent = client.as_agent(
    name="EnterpriseAgent",
    tools=[remote_mcp],
)
```

### Remote MCP Server (HTTP)

```python
from agent_framework.tools import MCPHttpTool

http_mcp = MCPHttpTool(
    name="api-tools",
    base_url="https://mcp-api.company.com",
    headers={"Authorization": f"Bearer {token}"},
)
```

---

## Tool Approval

For sensitive operations, require human approval before tool execution:

```python
# Mark tool as requiring approval
@tool
def delete_record(
    record_id: Annotated[str, "Record ID to delete"],
) -> str:
    """Permanently delete a record from the database"""
    # Deletion logic
    return f"Deleted record {record_id}"

# Configure approval in agent
agent = client.as_agent(
    name="AdminAgent",
    tools=[delete_record],
    tool_approval={
        "delete_record": True,  # Requires human approval
    },
)
```

When the agent tries to call `delete_record`, the framework pauses and requests human confirmation before executing.

---

## Built-in Tools

Azure AI Foundry provides built-in tools:

| Tool | Description | Availability |
|------|-------------|-------------|
| **Code Interpreter** | Sandboxed Python execution | Azure OpenAI, OpenAI |
| **File Search** | Search uploaded documents | Azure OpenAI, OpenAI |
| **Web Search (Bing)** | Internet search via Bing | Azure AI Foundry |
| **Image Generation** | DALL-E image creation | Azure OpenAI |

### Code Interpreter

```python
# Enable code interpreter for data analysis
agent = client.as_agent(
    name="DataAnalyst",
    instructions="You analyze data. Use code interpreter for calculations and charts.",
    tools=["code_interpreter"],  # Built-in tool name
)
```

### File Search

```python
# Enable file search with uploaded documents
agent = client.as_agent(
    name="DocAgent",
    instructions="Answer questions using the uploaded documents.",
    tools=["file_search"],
    # Files uploaded via Azure AI Foundry
)
```

---

## OpenAPI Integration

Agents can connect to any REST API via OpenAPI specifications:

```python
from agent_framework.tools import OpenAPITool

# Load OpenAPI spec
api_tool = OpenAPITool(
    name="petstore",
    spec_url="https://petstore.swagger.io/v2/swagger.json",
    # Or: spec_path="./openapi.yaml"
    auth={"api_key": "your-key"},
)

agent = client.as_agent(
    name="PetStoreAgent",
    instructions="Help users manage the pet store.",
    tools=[api_tool],
)
```

The framework converts OpenAPI endpoints into callable tools automatically.

---

## Common Mistakes

### 1. Forgetting to pass tools to agent

```python
# WRONG — tool defined but not passed
@tool
def my_tool(...): ...

agent = client.as_agent(name="Agent", instructions="...")  # No tools!

# CORRECT
agent = client.as_agent(name="Agent", instructions="...", tools=[my_tool])
```

### 2. Vague docstrings

```python
# WRONG — LLM doesn't know when to use it
@tool
def process(data: Annotated[str, "Data"]) -> str:
    """Process data"""  # Too vague
    ...

# CORRECT — Clear purpose
@tool
def extract_email_addresses(text: Annotated[str, "Text to search for emails"]) -> list[str]:
    """Extract all email addresses from the given text using regex pattern matching"""
    ...
```

### 3. Tool that modifies global state without indication

```python
# WRONG — Side effects not documented
@tool
def update_config(key: Annotated[str, "Key"], value: Annotated[str, "Value"]) -> str:
    """Update config"""
    global_config[key] = value
    return "updated"

# CORRECT — Clear about side effects
@tool
def update_config(key: Annotated[str, "Config key to update"], value: Annotated[str, "New value"]) -> str:
    """Update a configuration setting. This PERMANENTLY changes the application config.
    The change takes effect immediately and persists across restarts."""
    global_config[key] = value
    return f"Config '{key}' updated to '{value}'"
```

### 4. Not handling tool errors

```python
# WRONG — Unhandled exception crashes agent
@tool
def fetch_url(url: Annotated[str, "URL"]) -> str:
    """Fetch URL content"""
    return requests.get(url).text  # May throw!

# CORRECT — Graceful error handling
@tool
def fetch_url(url: Annotated[str, "URL to fetch"]) -> str:
    """Fetch content from a URL. Returns error message if fetch fails."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text[:5000]  # Limit size
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"
```
