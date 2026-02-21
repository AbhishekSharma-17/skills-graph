# Agno State Management — Reference Router

State is persistent data that survives across multiple runs within a session. It enables agents, teams, and workflows to remember information (shopping lists, user preferences, counters, todo items) across interactions.

## How State Works

1. **Initialize** — Set default `session_state` when creating agents/teams/workflows
2. **Access** — Tools read/write state via `run_context.session_state`
3. **Persist** — Modifications automatically save to the database (if configured)
4. **Reload** — Subsequent runs in the same session retrieve stored state

## State Scope Hierarchy

```
Workflow State (shared across all steps)
├── Team State (shared across all team members)
│   └── Agent State (private to agent, or inherited from team)
└── Step State (agents/teams/functions in steps access workflow state)
```

State propagates downward: workflow state flows into step agents/teams, team state flows into member agents.

## Sub-References

Read only what the current task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **Agent State** | `references/state/agent-state.md` | Basic session state, RunContext, state in instructions, tools accessing state, state per run |
| **Agentic State** | `references/state/agentic-state.md` | Automatic state management without custom tools (agent + team), `enable_agentic_state` |
| **Team State** | `references/state/team-state.md` | Shared state across members, team tools, member interactions, team state propagation |
| **Workflow State** | `references/state/workflow-state.md` | State across workflow steps, agents/teams/functions sharing state in pipelines |
| **Advanced Patterns** | `references/state/advanced-patterns.md` | Multi-user state isolation, dynamic state with hooks, overwrite vs merge, cross-session history, built-in state variables |

## Quick Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb
from agno.run import RunContext

def add_item(run_context: RunContext, item: str) -> str:
    """Add item to shopping list."""
    run_context.session_state["shopping_list"].append(item)
    return f"Added '{item}'. List: {run_context.session_state['shopping_list']}"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/state.db"),
    session_state={"shopping_list": []},
    tools=[add_item],
    instructions="Current shopping list: {shopping_list}",
)

agent.print_response("Add milk and eggs", session_id="shop_session")
print(agent.get_session_state())  # {'shopping_list': ['milk', 'eggs']}
```

## Key Parameters (Agent/Team/Workflow)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_state` | `dict` | `{}` | Default state for new sessions. Keys are accessible in tools via `run_context.session_state` and in instructions via `{key_name}` template syntax |
| `db` | `AgnoDb` | `None` | Database for persistence — state auto-saves after each run |
| `add_session_state_to_context` | `bool` | `False` | Show state in system prompt so the agent can see current state values |
| `enable_agentic_state` | `bool` | `False` | Give agent a built-in `update_session_state` tool for automatic state management |
| `overwrite_db_session_state` | `bool` | `False` | When `True`, replaces DB state with code defaults on load. When `False` (default), merges DB state with defaults |

## RunContext State Access (in Tools)

| Attribute / Method | Type | Description |
|--------------------|------|-------------|
| `run_context.session_state` | `Dict` | Read/write access to session state dictionary |
| `run_context.session_state["key"]` | `Any` | Get or set individual state values |

```python
from agno.run import RunContext

def add_to_cart(run_context: RunContext, item: str) -> str:
    """Tools access state via run_context.session_state."""
    run_context.session_state["cart"].append(item)
    return f"Added {item}. Cart: {run_context.session_state['cart']}"
```
