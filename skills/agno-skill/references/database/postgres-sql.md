# SQL & Relational Databases

## Contents

- [PostgreSQL (Sync)](#postgresql-sync)
- [PostgreSQL Async](#postgresql-async)
- [MySQL](#mysql)
- [SQLite](#sqlite)
- [Supabase](#supabase)
- [Neon](#neon)

---

## PostgreSQL (Sync)

The recommended production backend. Uses SQLAlchemy with psycopg driver.

### Constructor

```python
from agno.db.postgres import PostgresDb

db = PostgresDb(
    db_url="postgresql+psycopg://user:password@localhost:5432/mydb",
    # Optional overrides:
    db_schema=None,           # Database schema
    session_table=None,       # Default: agno_sessions
    memory_table=None,        # Default: agno_memories
    metrics_table=None,
    eval_table=None,
    knowledge_table=None,
    traces_table=None,
    spans_table=None,
)
```

### Connection string format

```
postgresql+psycopg://user:password@host:port/database
```

### Full example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.postgres import PostgresDb
from agno.tools.hackernews import HackerNewsTools

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    tools=[HackerNewsTools()],
    add_history_to_context=True,
    num_history_runs=3,
)

agent.print_response("How many people live in Canada?", session_id="chat_1")
agent.print_response("What is their national anthem called?", session_id="chat_1")
```

### Docker setup (with pgvector)

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

---

## PostgreSQL Async

For async applications. Uses `psycopg_async` driver.

### Constructor

```python
from agno.db.postgres import AsyncPostgresDb

db = AsyncPostgresDb(
    db_url="postgresql+psycopg_async://user:password@localhost:5432/mydb",
    # Same optional parameters as PostgresDb
)
```

### Connection string format (note the `_async` suffix)

```
postgresql+psycopg_async://user:password@host:port/database
```

### Full example

```python
import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.postgres import AsyncPostgresDb
from agno.tools.hackernews import HackerNewsTools

db = AsyncPostgresDb(db_url="postgresql+psycopg_async://ai:ai@localhost:5532/ai")

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    tools=[HackerNewsTools()],
    add_history_to_context=True,
    add_datetime_to_context=True,
)

async def main():
    await agent.aprint_response("How many people live in Canada?", session_id="async_chat")
    await agent.aprint_response("What is their national anthem?", session_id="async_chat")

asyncio.run(main())
```

### Common async pitfall

Using a sync engine with `AsyncPostgresDb` causes `MissingGreenlet`. Using an async engine with `PostgresDb` causes `AsyncContextNotStarted`. Match the engine type to the db class.

---

## MySQL

### Constructor

```python
from agno.db.mysql import MySQLDb

db = MySQLDb(
    db_url="mysql+pymysql://user:password@localhost:3306/mydb",
    db_schema=None,
    session_table=None,
    memory_table=None,
    metrics_table=None,
    eval_table=None,
    knowledge_table=None,
    traces_table=None,
    spans_table=None,
)
```

### Connection string format

```
mysql+pymysql://user:password@host:port/database
```

### Async MySQL

```python
from agno.db.mysql import AsyncMySQLDb

db = AsyncMySQLDb(db_url="mysql+aiomysql://user:password@localhost:3306/mydb")
```

### Connection string format (async)

```
mysql+aiomysql://user:password@host:port/database
```

### Docker setup

```bash
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=ai \
  -e MYSQL_DATABASE=ai \
  -e MYSQL_USER=ai \
  -e MYSQL_PASSWORD=ai \
  -p 3306:3306 \
  mysql:8
```

---

## SQLite

Zero-config local database. Great for development and prototyping.

### Constructor

```python
from agno.db.sqlite import SqliteDb

db = SqliteDb(
    db_file="agent.db",     # Path to SQLite file
    # OR
    db_url=None,             # SQLAlchemy URL: sqlite:///path/to/db
    db_engine=None,          # Existing SQLAlchemy engine
    session_table=None,
    memory_table=None,
    metrics_table=None,
    eval_table=None,
    knowledge_table=None,
    traces_table=None,
    spans_table=None,
)
```

### Full example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=SqliteDb(db_file="agent.db"),
    add_history_to_context=True,
    num_history_runs=3,
)

agent.print_response("I'm working on a Python API", session_id="dev")
agent.print_response("What testing framework should I use?", session_id="dev")
```

### Async SQLite

```python
from agno.db.sqlite import AsyncSqliteDb

db = AsyncSqliteDb(db_file="agent.db")
```

---

## Supabase

Supabase is a hosted PostgreSQL platform. Uses `PostgresDb` with a Supabase connection string.

### Setup

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from os import getenv

SUPABASE_PROJECT = getenv("SUPABASE_PROJECT")
SUPABASE_PASSWORD = getenv("SUPABASE_PASSWORD")

db = PostgresDb(
    db_url=f"postgresql://postgres:{SUPABASE_PASSWORD}@db.{SUPABASE_PROJECT}.supabase.co:5432/postgres"
)

agent = Agent(db=db, add_history_to_context=True)
```

### Connection string format

```
postgresql://postgres:PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres
```

All `PostgresDb` parameters (custom tables, schema, etc.) work identically with Supabase.

---

## Neon

Neon is a serverless Postgres platform. Uses `PostgresDb` with a Neon connection string.

### Setup

```python
from agno.db.postgres import PostgresDb

db = PostgresDb(db_url="postgresql://user:password@host.us-east-1.neon.tech/dbname")
```

### Connection string format

```
postgresql://user:password@host.region.neon.tech/dbname
```

All `PostgresDb` parameters (custom tables, schema, etc.) work identically with Neon.
