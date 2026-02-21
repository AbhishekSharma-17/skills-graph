# PostgreSQL Backend

The recommended backend for production. Supports sync and async, custom schemas, and integrates with PgVector for knowledge/embeddings.

## Install

```bash
uv pip install -U agno psycopg[binary]
```

## Docker Setup

```bash
docker run -d \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  --name pgvector \
  agnohq/pgvector:16
```

The `agnohq/pgvector:16` image includes PgVector extension for vector search (useful for knowledge bases).

## Sync Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.postgres import PostgresDb

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

db = PostgresDb(db_url=db_url)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
)

agent.print_response("Hello!", session_id="user_123")
agent.print_response("What did I just say?", session_id="user_123")
```

## Async Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.postgres import AsyncPostgresDb

db_url = "postgresql+psycopg_async://ai:ai@localhost:5532/ai"

db = AsyncPostgresDb(db_url=db_url)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
)

# Use async methods
await agent.aprint_response("Hello!", session_id="user_123", stream=True)
```

## Connection String Formats

```
# Standard (sync)
postgresql+psycopg://user:password@host:port/database

# Async
postgresql+psycopg_async://user:password@host:port/database

# With schema
postgresql+psycopg://user:password@host:port/database?options=-csearch_path%3Dmy_schema
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `Optional[str]` | UUID | Database instance ID |
| `db_url` | `Optional[str]` | — | Database connection URL |
| `db_engine` | `Optional[Engine]` | — | Existing SQLAlchemy engine |
| `db_schema` | `Optional[str]` | — | Database schema (e.g., `public`) |
| `session_table` | `Optional[str]` | `agno_sessions` | Sessions table name |
| `memory_table` | `Optional[str]` | `agno_memories` | Memories table name |
| `metrics_table` | `Optional[str]` | `agno_metrics` | Metrics table name |
| `eval_table` | `Optional[str]` | `agno_evals` | Evaluation runs table |
| `knowledge_table` | `Optional[str]` | `agno_knowledge` | Knowledge content table |
| `traces_table` | `Optional[str]` | `agno_traces` | Traces table |
| `spans_table` | `Optional[str]` | `agno_spans` | Spans table |

## Custom Table Names

```python
db = PostgresDb(
    db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    session_table="my_agent_sessions",
    memory_table="my_agent_memories",
)
```

## Custom Schema

```python
db = PostgresDb(
    db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    db_schema="my_app",
)
```

## Existing SQLAlchemy Engine

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg://ai:ai@localhost:5532/ai",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

db = PostgresDb(db_engine=engine)
```

## Multi-User Pattern

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai"),
)

# User 1
agent.print_response("Hello!", session_id="session_1", user_id="alice@example.com")

# User 2
agent.print_response("Hello!", session_id="session_2", user_id="bob@example.com")
```

## Session Retrieval

```python
# Get full session
session = agent.get_session(session_id="session_1")
print(session.runs)

# Get chat history
history = agent.get_chat_history(session_id="session_1")

# Get session state
state = agent.get_session_state(session_id="session_1")

# Delete session
agent.delete_session(session_id="session_1")
```
