# LangGraph — Persistence & Checkpointing

> Source: [docs.langchain.com/oss/python/langgraph](https://docs.langchain.com/oss/python/langgraph/overview)

## Table of Contents

- [How Checkpointing Works](#how-checkpointing-works)
- [Checkpointer Backends](#checkpointer-backends)
- [Thread Management](#thread-management)
- [State Inspection and Modification](#state-inspection-and-modification)
- [Durable Execution](#durable-execution)
- [Time-Travel Debugging](#time-travel-debugging)
- [Production Setup](#production-setup)
- [Common Pitfalls](#common-pitfalls)

---

## How Checkpointing Works

LangGraph automatically saves a **checkpoint** (state snapshot) after every super-step. This enables:
- Resuming after failures or interrupts
- Multi-turn conversations across requests
- Time-travel debugging by replaying from any checkpoint
- Human-in-the-loop workflows with pause/resume

```
invoke() → Step 1 → [checkpoint] → Step 2 → [checkpoint] → ... → Result
```

Each checkpoint stores:
- Full graph state at that point
- Metadata (timestamp, step number, node info)
- Parent checkpoint reference (for history traversal)

## Checkpointer Backends

### InMemorySaver (Development)

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)
```

- Zero dependencies, fastest option
- Data lost on process restart
- Use for prototyping and tests only

### SQLiteSaver (Local/Development)

```python
# pip install langgraph-checkpoint-sqlite

from langgraph.checkpoint.sqlite import SqliteSaver

# File-based (persists across restarts)
checkpointer = SqliteSaver.from_conn_string("checkpoints.sqlite")

# In-memory
checkpointer = SqliteSaver.from_conn_string(":memory:")

app = graph.compile(checkpointer=checkpointer)
```

### AsyncSqliteSaver (Async Applications)

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    app = graph.compile(checkpointer=checkpointer)
    result = await app.ainvoke(inputs, config)
```

### PostgresSaver (Production)

```python
# pip install langgraph-checkpoint-postgres

from langgraph.checkpoint.postgres import PostgresSaver

# Synchronous
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/mydb"
)
checkpointer.setup()  # Creates checkpoint tables
app = graph.compile(checkpointer=checkpointer)
```

**Critical setup requirements:**
- `autocommit=True` — required for `.setup()` to commit tables
- `row_factory=dict_row` — required for row access pattern

```python
import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(
    "postgresql://user:pass@localhost:5432/mydb",
    autocommit=True,
    row_factory=dict_row,
)
checkpointer = PostgresSaver(conn)
checkpointer.setup()
```

### AsyncPostgresSaver (Async Production)

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async with await AsyncPostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/mydb"
) as checkpointer:
    await checkpointer.setup()
    app = graph.compile(checkpointer=checkpointer)
```

### Comparison

| Backend | Persistence | Async | Production | Install |
|---------|:-----------:|:-----:|:----------:|---------|
| `InMemorySaver` | No | Yes | No | `langgraph` |
| `SqliteSaver` | Yes | No | Dev only | `langgraph-checkpoint-sqlite` |
| `AsyncSqliteSaver` | Yes | Yes | Dev only | `langgraph-checkpoint-sqlite` |
| `PostgresSaver` | Yes | No | Yes | `langgraph-checkpoint-postgres` |
| `AsyncPostgresSaver` | Yes | Yes | Yes | `langgraph-checkpoint-postgres` |

## Thread Management

Threads isolate conversations. Each thread has its own checkpoint history.

```python
# Thread 1 — User Alice
config_alice = {"configurable": {"thread_id": "alice-session-1"}}
app.invoke({"messages": [...]}, config_alice)

# Thread 2 — User Bob (completely independent state)
config_bob = {"configurable": {"thread_id": "bob-session-1"}}
app.invoke({"messages": [...]}, config_bob)
```

**Thread ID best practices:**
- Use UUIDs or user-scoped IDs (`f"user-{user_id}-{session_id}"`)
- Thread IDs are strings — keep them deterministic for resumability
- Different thread = completely independent state and history

## State Inspection and Modification

### Get Current State

```python
config = {"configurable": {"thread_id": "t1"}}
state = app.get_state(config)

print(state.values)       # Current state dict
print(state.next)         # Next node(s) to execute (if paused)
print(state.config)       # Config with checkpoint_id
print(state.metadata)     # Step number, source, etc.
print(state.created_at)   # Timestamp
print(state.parent_config)  # Parent checkpoint config
```

### Get State History

```python
for snapshot in app.get_state_history(config):
    print(f"Step: {snapshot.metadata['step']}")
    print(f"Node: {snapshot.metadata.get('source')}")
    print(f"State: {snapshot.values}")
    print("---")
```

### Update State Externally

Modify graph state without executing nodes:

```python
app.update_state(
    config,
    {"messages": [{"role": "system", "content": "Updated instructions"}]},
    as_node="agent",  # Which node "produced" this update
)
```

## Durable Execution

Checkpointing enables automatic recovery from failures:

```python
# If this crashes mid-execution...
try:
    result = app.invoke(inputs, config)
except Exception:
    pass

# ...re-invoke with the same thread_id to resume from last checkpoint
result = app.invoke(None, config)
```

The graph resumes from the last successful checkpoint, skipping completed nodes.

## Time-Travel Debugging

Replay execution from any historical checkpoint:

```python
# Get history
history = list(app.get_state_history(config))

# Find a specific checkpoint
target = history[3]  # e.g., the 4th checkpoint

# Replay from that point
result = app.invoke(
    None,
    target.config,  # Config pointing to specific checkpoint
)
```

**Use cases:**
- Debug non-deterministic agent behavior
- Explore "what-if" scenarios by branching from historical states
- Recover from bad outputs by rolling back

### Fork and Branch

```python
# Get state at a past checkpoint
past_state = app.get_state(target_config)

# Modify state and re-run from that point
app.update_state(target_config, {"context": "corrected data"})
result = app.invoke(None, target_config)
```

## Production Setup

### PostgreSQL with Connection Pool

```python
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

pool = ConnectionPool(
    conninfo="postgresql://user:pass@host:5432/db",
    min_size=5,
    max_size=20,
    kwargs={"autocommit": True, "row_factory": dict_row},
)

checkpointer = PostgresSaver(pool)
checkpointer.setup()
```

### Checkpoint Cleanup

Long-running applications accumulate checkpoints. Consider periodic cleanup:

```python
# Application-level cleanup (not built into LangGraph)
# Delete checkpoints older than 30 days for completed threads
```

### Concurrency Considerations

- Each thread should be accessed by one process at a time
- PostgresSaver handles concurrent reads safely
- Concurrent writes to the same thread may cause conflicts
- Use thread-per-user patterns to avoid contention

## Common Pitfalls

1. **Missing `thread_id`** — All persistence operations require `{"configurable": {"thread_id": "..."}}`.
2. **Using InMemorySaver in production** — Data is lost on restart. Use PostgresSaver.
3. **Forgetting `checkpointer.setup()`** — PostgresSaver needs `.setup()` to create tables.
4. **Missing `autocommit=True`** — PostgresSaver connections require autocommit mode.
5. **Stale thread state** — Long-idle threads may have outdated state. Consider TTL patterns.
6. **Large state objects** — Checkpointing serializes full state. Keep state lean.

---

> **Related:** [05-memory.md](05-memory.md) for long-term memory, [07-human-in-the-loop.md](07-human-in-the-loop.md) for interrupt-driven persistence
