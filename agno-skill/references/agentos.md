# AgentOS

The production runtime and control plane for multi-agent systems. Transforms agents into production APIs with 50+ endpoints, SSE streaming, tracing, and RBAC.

## Docs Hierarchy
- /agent-os/introduction
- /agent-os/run-your-os
- /agent-os/connect-your-os
- /agent-os/control-plane
- /agent-os/overview
- /agent-os/using-the-api
- /agent-os/config
- /agent-os/background-tasks/overview
- /agent-os/lifespan
- /agent-os/security/overview

## Quick Start

```python
from agno.os import AgentOS
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude

agent = Agent(
    name="My Agent",
    model=Claude(id="claude-sonnet-4-5"),
    db=SqliteDb(db_file="agno.db"),
    add_history_to_context=True,
    markdown=True,
)

agent_os = AgentOS(agents=[agent])
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="my_os:app", reload=True)
```

## Install
```bash
uv pip install -U 'agno[os]'
```

## Sub-References

| Reference | File | Read When |
|-----------|------|-----------|
| Setup & API | `agentos/setup-api.md` | Running AgentOS, connecting to control plane, API endpoints, curl examples |
| Configuration & Security | `agentos/config-security.md` | YAML/class config, RBAC, JWT auth, background hooks, custom lifespan |

## Key Features
- 50+ endpoints with SSE streaming for real-time communication
- Data sovereignty: sessions, memory, traces stored in YOUR database
- Request-level isolation for users and sessions
- JWT-based RBAC with hierarchical scopes
- Built-in tracing without third-party egress
- Control plane at os.agno.com (browser connects directly, no data relayed)
- Support for agents, teams, and workflows

## AgentOS Parameters (Quick Reference)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | None | AgentOS instance name |
| `agents` | `List[Agent]` | None | Agents to include in OS |
| `teams` | `List[Team]` | None | Teams to include in OS |
| `workflows` | `List[Workflow]` | None | Workflows to include in OS |
| `db` | `BaseDb` | None | Database backend for AgentOS |
| `tracing` | `bool` | False | Enable built-in tracing |
| `knowledge` | `List[Knowledge]` | None | Knowledge bases |
| `interfaces` | `List[BaseInterface]` | None | Custom agent interfaces |
| `config` | `str`/`AgentOSConfig` | None | Config YAML path or config object |
| `base_app` | `FastAPI` | None | Custom FastAPI app instance |
| `lifespan` | `Any` | None | Custom lifespan context manager |
| `authorization` | `bool` | False | Enable RBAC with JWT |
| `enable_mcp_server` | `bool` | False | Enable MCP server integration |
| `cors_allowed_origins` | `List[str]` | None | CORS allowed origins |
| `run_hooks_in_background` | `bool` | False | Run all hooks in background |

## Methods

```python
# Returns configured FastAPI application
app = agent_os.get_app()

# Start development or production server
agent_os.serve(app="module:app", host="localhost", port=7777, reload=False)

# Reload agents, teams, and workflows from definitions
agent_os.resync()
```

## Cross-References
→ Tracing: `references/tracing.md`
→ Hooks: `references/hooks.md`
→ Deploy: `references/deploy.md`
