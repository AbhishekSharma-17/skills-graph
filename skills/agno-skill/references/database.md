# Agno Database & Storage

Databases in Agno provide persistent storage for chat history, session state, memory, metrics, traces, and knowledge. Every database backend exposes the same interface — swap backends by changing one line.

**What gets stored:** chat history, session state, memory, metrics, traces/spans, and knowledge. Tables are auto-created on first use.

## Sub-References

| Sub-Reference | File | Read When |
|---------------|------|-----------|
| **Backends** | `database/backends.md` | Setting up PostgreSQL, MongoDB, Redis, SQLite, DynamoDB, MySQL, Supabase, Neon — constructors, connection strings, Docker commands, choosing a backend |
| **Chat History** | `database/chat-history.md` | Enabling multi-turn context, controlling history size, on-demand/cross-session history, team/workflow history |
| **Sessions & Memory** | `database/session-memory.md` | Automatic vs agentic memory, session management, multi-user isolation, session data model, session summaries |

## Quick Start

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
)
```
