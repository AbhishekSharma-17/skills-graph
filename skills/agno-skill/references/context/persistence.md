# Persistence & Database Backends

Sessions need a database to persist across restarts. Without a database, sessions live only in memory for the current process. Agno supports 12+ backends with a unified interface — swap backends by changing one line.

## Quick Start

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="agent.db"),        # Sessions now persist
    add_history_to_context=True,
    num_history_runs=3,
)

agent.print_response("I'm building a Python API", session_id="dev_session")
# Later (even after restart):
agent.print_response("What was I working on?", session_id="dev_session")
```

## Session Storage Schema

Every backend stores this identical structure:

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | Unique conversation thread identifier |
| `session_type` | `str` | `"agent"`, `"team"`, or `"workflow"` |
| `agent_id` / `team_id` / `workflow_id` | `str` | Parent entity ID |
| `user_id` | `str` | User this session belongs to |
| `session_data` | `dict` | Session name, state, media |
| `agent_data` / `team_data` / `workflow_data` | `dict` | Entity configuration |
| `metadata` | `dict` | Custom metadata |
| `runs` | `list` | All RunOutput objects |
| `summary` | `dict` | Session summary (if enabled) |
| `created_at` / `updated_at` | `int` | Unix timestamps |

## What Gets Stored Automatically

When a database is configured, Agno stores: messages (user + assistant), run metadata (timestamps, tokens, model), session state, tool calls and results, and media references.

## Choosing a Backend

| Backend | Best For | Async | Production |
|---------|----------|-------|------------|
| **PostgreSQL** | Production workloads, teams, high concurrency | Yes | Yes |
| **SQLite** | Local development, prototyping, single-user | Yes | No |
| **MongoDB** | Document-oriented storage, flexible schema | Yes | Yes |
| **Redis** | Session caching, high-throughput, TTL-based expiry | No | Yes |
| **MySQL** | General purpose, existing MySQL infrastructure | Yes | Yes |
| **DynamoDB** | AWS-native, serverless, auto-scaling | No | Yes |
| **Firestore** | Google Cloud native, real-time sync | No | Yes |
| **Supabase** | Managed PostgreSQL, quick setup | Yes | Yes |
| **Neon** | Serverless PostgreSQL, auto-scaling | Yes | Yes |
| **SingleStore** | Distributed SQL, high-volume analytics | No | Yes |
| **InMemory** | Testing and demos only | No | No |
| **JSON** | File-based testing only | No | No |

## Backend Sub-References

Read only the backend you need:

| Reference | File | Read When |
|-----------|------|-----------|
| **PostgreSQL** | `references/context/persistence/postgres.md` | Production setup, sync/async, Docker, custom tables, PgVector integration |
| **SQLite** | `references/context/persistence/sqlite.md` | Development setup, file-based, async variant |
| **MongoDB** | `references/context/persistence/mongodb.md` | Document storage, MongoDB Atlas, sync/async, custom collections |
| **Redis** | `references/context/persistence/redis.md` | Session caching, TTL expiry, key prefixes |
| **Cloud Backends** | `references/context/persistence/cloud-backends.md` | DynamoDB, Firestore, Supabase, Neon — managed/serverless options |
| **Other Backends** | `references/context/persistence/other-backends.md` | MySQL, SingleStore, InMemory, JSON |

## Common Table Parameters

All backends share these configurable table/collection names:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `session_table` | `agno_sessions` | Sessions storage |
| `memory_table` | `agno_memories` | Memories storage |
| `metrics_table` | `agno_metrics` | Metrics storage |
| `eval_table` | `agno_evals` | Evaluation runs |
| `knowledge_table` | `agno_knowledge` | Knowledge content |
| `traces_table` | `agno_traces` | Traces |
| `spans_table` | `agno_spans` | Spans |

For MongoDB/Firestore, these are collection names instead of table names.

## Usage with Teams & Workflows

```python
from agno.team import Team
from agno.workflow import Workflow

# Teams
team = Team(
    db=PostgresDb(db_url="..."),
    add_history_to_context=True,
    add_team_history_to_members=True,  # Share history across members
)

# Workflows
workflow = Workflow(
    db=SqliteDb(db_file="workflow.db"),
    add_workflow_history_to_steps=True,
    num_history_runs=5,
)
```
