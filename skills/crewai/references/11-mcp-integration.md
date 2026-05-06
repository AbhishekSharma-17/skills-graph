# CrewAI MCP Integration

> Source: https://docs.crewai.com/en/mcp/overview

## Overview

CrewAI natively supports the Model Context Protocol (MCP), allowing agents to discover and use tools hosted on MCP servers. This enables agents to access external services, databases, APIs, and more through a standardized protocol.

## MCP Integration Methods

CrewAI supports two primary ways to integrate MCP servers:

1. **`mcps` field on agents** — Direct agent-level MCP configuration
2. **Context manager pattern** — Manual connection management

## Agent-Level MCP (Recommended)

### String Reference (Simple)

```python
from crewai import Agent

agent = Agent(
    role="Data Analyst",
    goal="Analyze data using available tools",
    backstory="Expert data analyst.",
    mcps=["my-mcp-server"],  # String reference
)
```

### Structured Configuration (Stdio)

```python
from crewai import Agent
from crewai.tools.mcp import MCPServerStdio

agent = Agent(
    role="File Manager",
    goal="Manage files and directories",
    backstory="Expert at file operations.",
    mcps=[
        MCPServerStdio(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        )
    ],
)
```

### Structured Configuration (HTTP/SSE)

```python
from crewai import Agent
from crewai.tools.mcp import MCPServerHTTP

agent = Agent(
    role="Database Admin",
    goal="Query and manage databases",
    backstory="Expert DBA.",
    mcps=[
        MCPServerHTTP(
            name="postgres-mcp",
            url="http://localhost:3001/sse",
            headers={"Authorization": "Bearer token123"},
        )
    ],
)
```

## Context Manager Pattern

For manual lifecycle control:

```python
from crewai import Agent, Task, Crew
from crewai.tools.mcp import MCPServerStdio

server = MCPServerStdio(
    name="brave-search",
    command="npx",
    args=["-y", "@anthropic/mcp-server-brave-search"],
    env={"BRAVE_API_KEY": "your-key"},
)

with server as mcp:
    tools = mcp.tools()

    researcher = Agent(
        role="Web Researcher",
        goal="Search the web for information",
        backstory="Expert researcher.",
        tools=tools,
    )

    task = Task(
        description="Search for the latest AI news.",
        expected_output="Summary of top 5 AI news items.",
        agent=researcher,
    )

    crew = Crew(agents=[researcher], tasks=[task])
    result = crew.kickoff()
```

## Multiple MCP Servers

```python
from crewai import Agent
from crewai.tools.mcp import MCPServerStdio, MCPServerHTTP

agent = Agent(
    role="Full-Stack Assistant",
    goal="Help with development tasks",
    backstory="Versatile developer assistant.",
    mcps=[
        MCPServerStdio(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "."],
        ),
        MCPServerStdio(
            name="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": "ghp_..."},
        ),
        MCPServerHTTP(
            name="database",
            url="http://localhost:3001/sse",
        ),
    ],
)
```

## Common MCP Servers

| Server | Package | Purpose |
|--------|---------|---------|
| Filesystem | `@modelcontextprotocol/server-filesystem` | File read/write |
| GitHub | `@modelcontextprotocol/server-github` | GitHub operations |
| Brave Search | `@anthropic/mcp-server-brave-search` | Web search |
| PostgreSQL | `@modelcontextprotocol/server-postgres` | Database queries |
| Slack | `@modelcontextprotocol/server-slack` | Slack messaging |
| Google Drive | `@modelcontextprotocol/server-gdrive` | Google Drive access |
| Memory | `@modelcontextprotocol/server-memory` | Persistent memory |

## MCP with Flows

```python
from crewai import Agent, Task, Crew
from crewai.flow.flow import Flow, listen, start
from crewai.tools.mcp import MCPServerStdio

class DataPipeline(Flow):
    @start()
    def fetch_data(self):
        agent = Agent(
            role="Data Fetcher",
            goal="Fetch data from external sources",
            backstory="Expert at data retrieval.",
            mcps=[
                MCPServerHTTP(name="data-api", url="http://localhost:3001/sse")
            ],
        )
        task = Task(
            description="Fetch the latest sales data.",
            expected_output="Raw sales data as JSON.",
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task])
        return crew.kickoff().raw

    @listen(fetch_data)
    def analyze_data(self, raw_data):
        agent = Agent(
            role="Analyst",
            goal="Analyze sales data",
            backstory="Expert data analyst.",
            mcps=[
                MCPServerStdio(
                    name="filesystem",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "./reports"],
                )
            ],
        )
        task = Task(
            description=f"Analyze this data and save report: {raw_data}",
            expected_output="Analysis report saved to file.",
            agent=agent,
        )
        crew = Crew(agents=[agent], tasks=[task])
        return crew.kickoff().raw
```

## Environment Variables for MCP

```python
from crewai.tools.mcp import MCPServerStdio

server = MCPServerStdio(
    name="secure-server",
    command="npx",
    args=["-y", "my-mcp-server"],
    env={
        "API_KEY": "secret-key",
        "DATABASE_URL": "postgres://...",
        "NODE_ENV": "production",
    },
)
```

## Error Handling

CrewAI's MCP integration handles failures gracefully:

```python
from crewai import Agent
from crewai.tools.mcp import MCPServerStdio

# If the MCP server fails to start, agent continues without those tools
agent = Agent(
    role="Researcher",
    goal="Research topics",
    backstory="Expert researcher.",
    mcps=[
        MCPServerStdio(
            name="search",
            command="npx",
            args=["-y", "@anthropic/mcp-server-brave-search"],
        )
    ],
    tools=[fallback_tool],  # Regular tools work as fallback
)
```

## Building Custom MCP Servers for CrewAI

```python
# server.py — Simple MCP server using FastMCP
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-tools")

@mcp.tool()
def search_database(query: str) -> str:
    """Search the internal database."""
    results = db.search(query)
    return f"Found: {results}"

@mcp.tool()
def create_ticket(title: str, description: str) -> str:
    """Create a support ticket."""
    ticket_id = tickets.create(title=title, desc=description)
    return f"Created ticket #{ticket_id}"

if __name__ == "__main__":
    mcp.run()
```

Use with CrewAI:

```python
agent = Agent(
    role="Support Agent",
    goal="Help customers",
    backstory="Expert support agent.",
    mcps=[
        MCPServerStdio(
            name="support-tools",
            command="python",
            args=["server.py"],
        )
    ],
)
```

## Common Pitfalls

1. **MCP server not installed** — Ensure npx packages are available or pre-installed
2. **Missing environment variables** — Pass secrets via the `env` parameter
3. **Server startup timeout** — Some servers take time; handle gracefully
4. **Too many MCP tools** — Like regular tools, agents get confused with too many options
5. **Not using context manager for cleanup** — Stdio servers need proper shutdown
6. **HTTP server not running** — Verify MCP HTTP servers are accessible before crew kickoff
