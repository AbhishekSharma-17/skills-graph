# SQLite Backend

Lightweight, zero-config, single-file database. Great for development, prototyping, and single-user applications.

## Install

```bash
uv pip install -U agno
```

SQLite is included with Python — no extra dependencies needed.

## Basic Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/agent.db")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
)

agent.print_response("Hello!", session_id="dev_session")
agent.print_response("What did I say?", session_id="dev_session")
```

## Async Usage

```python
from agno.db.sqlite import AsyncSqliteDb

db = AsyncSqliteDb(db_file="tmp/agent.db")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
)

await agent.aprint_response("Hello!", session_id="dev_session", stream=True)
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `Optional[str]` | UUID | Database instance ID |
| `db_file` | `Optional[str]` | — | Path to SQLite database file |
| `db_url` | `Optional[str]` | — | SQLAlchemy URL (e.g., `sqlite:///path.db`) |
| `db_engine` | `Optional[Engine]` | — | Existing SQLAlchemy engine |
| `session_table` | `Optional[str]` | `agno_sessions` | Sessions table name |
| `memory_table` | `Optional[str]` | `agno_memories` | Memories table name |
| `metrics_table` | `Optional[str]` | `agno_metrics` | Metrics table name |
| `eval_table` | `Optional[str]` | `agno_evals` | Evaluation runs table |
| `knowledge_table` | `Optional[str]` | `agno_knowledge` | Knowledge content table |
| `traces_table` | `Optional[str]` | `agno_traces` | Traces table |
| `spans_table` | `Optional[str]` | `agno_spans` | Spans table |

## Connection Variants

```python
# File path (simplest)
db = SqliteDb(db_file="tmp/agent.db")

# SQLAlchemy URL
db = SqliteDb(db_url="sqlite:///tmp/agent.db")

# In-memory (lost on exit)
db = SqliteDb(db_url="sqlite:///:memory:")
```

## Custom Table Names

```python
db = SqliteDb(
    db_file="agent.db",
    session_table="my_sessions",
    memory_table="my_memories",
)
```

## With Session State

```python
from agno.run import RunContext

def add_item(run_context: RunContext, item: str) -> str:
    """Add item to list."""
    run_context.session_state["items"].append(item)
    return f"Added: {item}"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/state.db"),
    session_state={"items": []},
    tools=[add_item],
    instructions="Current items: {items}",
)

agent.print_response("Add milk and eggs", session_id="shopping")
print(agent.get_session_state())  # {'items': ['milk', 'eggs']}
```

## Notes

- SQLite is single-writer — only one process can write at a time. For multi-process or multi-user production setups, use PostgreSQL.
- The database file is created automatically if it doesn't exist.
- Tables are auto-created on first use.
