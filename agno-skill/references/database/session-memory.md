# Agno Sessions & Memory Storage

## Contents
- [Memory Overview](#memory-overview)
- [Automatic Memory](#automatic-memory)
- [Agentic Memory](#agentic-memory)
- [Memory Data Model](#memory-data-model)
- [Sessions vs Runs](#sessions-vs-runs)
- [Multi-User Sessions](#multi-user-sessions)
- [Retrieve Sessions](#retrieve-sessions)
- [Session Data Model](#session-data-model)
- [Session Summaries](#session-summaries)
- [Works Everywhere: Agents, Teams, Workflows](#works-everywhere-agents-teams-workflows)

---

## Memory Overview

Memory stores learned user facts (preferences, habits) that persist across sessions. Different from chat history — memory is semantic, not chronological.

## Automatic Memory

Memories are extracted and stored after each run (recommended for most cases):

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

agent = Agent(
    db=SqliteDb(db_file="agent.db"),
    update_memory_on_run=True,       # Auto-extract memories
)

agent.print_response("My name is Sarah and I prefer email over phone calls.", user_id="sarah")
# Memory created: "User's name is Sarah. Prefers email over phone calls."

agent.print_response("What's the best way to reach me?", user_id="sarah")
# Agent recalls the preference from memory
```

## Agentic Memory

Agent gets tools to create/update/delete memories (agent controls what to remember):

```python
agent = Agent(
    db=SqliteDb(db_file="agent.db"),
    enable_agentic_memory=True,   # Agent decides what to remember
)
```

**Don't enable both** `update_memory_on_run` and `enable_agentic_memory` — they're mutually exclusive. If both are set, `enable_agentic_memory` takes precedence.

### Retrieve Memories

```python
memories = agent.get_user_memories(user_id="sarah")
for m in memories:
    print(f"[{m.memory_id}] {m.memory}")
```

## Memory Data Model

| Field | Type | Description |
|-------|------|-------------|
| `memory_id` | str | Unique identifier |
| `memory` | str | The memory content |
| `topics` | list | Topic tags |
| `input` | str | Input that generated it |
| `user_id` | str | User this belongs to |
| `agent_id` | str | Agent that created it |
| `updated_at` | int | Last update timestamp |

---

## Sessions vs Runs

- **Session** — a multi-turn conversation identified by `session_id`. Contains all runs, history, state, and metrics.
- **Run** — a single interaction within a session. Every `agent.run()` creates a new `run_id`.

## Multi-User Sessions

```python
agent = Agent(db=db, add_history_to_context=True)

# User 1's conversation
agent.print_response("My name is Alice", session_id="alice_chat", user_id="alice")
agent.print_response("What's my name?", session_id="alice_chat", user_id="alice")

# User 2's conversation (isolated)
agent.print_response("My name is Bob", session_id="bob_chat", user_id="bob")
agent.print_response("What's my name?", session_id="bob_chat", user_id="bob")
```

## Retrieve Sessions

```python
# Get full session object
session = agent.get_session(session_id="alice_chat")
print(session.session_id)
print(session.runs)         # List of all runs
print(session.session_data) # Session metadata

# Get session state
state = agent.get_session_state(session_id="alice_chat")

# Get metrics
metrics = agent.get_session_metrics(session_id="alice_chat")

# Delete a session
agent.delete_session(session_id="old_chat")
```

## Session Data Model

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | str | Unique session identifier |
| `session_type` | str | agent, team, or workflow |
| `agent_id` | str | Agent ID (if agent session) |
| `team_id` | str | Team ID (if team session) |
| `workflow_id` | str | Workflow ID (if workflow session) |
| `user_id` | str | User this session belongs to |
| `session_data` | dict | Session-specific data and state |
| `runs` | list | All interactions |
| `summary` | dict | Session summary (if enabled) |
| `created_at` | int | Unix timestamp |
| `updated_at` | int | Last update timestamp |

## Session Summaries

For long conversations, enable summaries to prevent context overflow:

```python
agent = Agent(
    db=db,
    add_history_to_context=True,
    enable_session_summaries=True,
    add_session_summary_to_context=True,
)
```

Agno summarizes older history into a compact summary, keeping recent messages intact.

---

## Works Everywhere: Agents, Teams, Workflows

Storage is identical across all three. Just pass `db=` to any of them:

```python
from agno.agent import Agent
from agno.team import Team
from agno.workflow import Workflow
from agno.db.postgres import PostgresDb

db = PostgresDb(db_url="postgresql+psycopg://user:pass@localhost:5432/mydb")

# Agent
agent = Agent(db=db, add_history_to_context=True)

# Team
team = Team(db=db, add_history_to_context=True, members=[...])

# Workflow
workflow = Workflow(db=db, steps=[...])

# Retrieve sessions from any of them
agent_session = agent.get_session(session_id="...")
team_session = team.get_session(session_id="...")
workflow_session = workflow.get_session(session_id="...")
```
