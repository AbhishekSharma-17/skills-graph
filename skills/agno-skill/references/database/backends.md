# Agno Database Backends

## Contents
- [Supported Backends](#supported-backends)
- [PostgreSQL (Sync)](#postgresql-sync)
- [PostgreSQL Async](#postgresql-async)
- [MongoDB](#mongodb)
- [Redis](#redis)
- [Supabase](#supabase)
- [SQLite](#sqlite)
- [DynamoDB](#dynamodb)
- [MySQL](#mysql)
- [Quick Reference: Choosing a Backend](#quick-reference-choosing-a-backend)
- [Install Dependencies](#install-dependencies)

---

## Supported Backends

| Backend | Class | Import | Best For |
|---------|-------|--------|----------|
| **PostgreSQL** | `PostgresDb` | `agno.db.postgres` | Production (sync) |
| **PostgreSQL Async** | `AsyncPostgresDb` | `agno.db.postgres` | Production (async) |
| **MongoDB** | `MongoDb` | `agno.db.mongo` | Document-oriented, flexible schemas |
| **MongoDB Async** | `AsyncMongoDb` | `agno.db.mongo` | Async document storage |
| **Redis** | `RedisDb` | `agno.db.redis` | Fast in-memory, TTL-based expiry |
| **SQLite** | `SqliteDb` | `agno.db.sqlite` | Development, local testing |
| **SQLite Async** | `AsyncSqliteDb` | `agno.db.sqlite` | Async local development |
| **MySQL** | `MySQLDb` | `agno.db.mysql` | MySQL production environments |
| **MySQL Async** | `AsyncMySQLDb` | `agno.db.mysql` | Async MySQL |
| **DynamoDB** | `DynamoDb` | `agno.db.dynamo` | AWS serverless |
| **Supabase** | `PostgresDb` | `agno.db.postgres` | Hosted Postgres (uses PostgresDb) |
| **Neon** | `PostgresDb` | `agno.db.postgres` | Serverless Postgres (uses PostgresDb) |
| **Firestore** | `FirestoreDb` | `agno.db.firestore` | Google Cloud |
| **SurrealDB** | `SurrealDb` | `agno.db.surrealdb` | Multi-model database |
| **In-Memory** | `InMemoryDb` | `agno.db.memory` | Testing, ephemeral |
| **JSON** | `JsonDb` | `agno.db.json` | File-based storage |

All backends share the same table/collection parameters:

| Parameter | Default | Stores |
|-----------|---------|--------|
| `session_table` | `agno_sessions` | Sessions and chat history |
| `memory_table` | `agno_memories` | User memories |
| `metrics_table` | `agno_metrics` | Usage metrics |
| `eval_table` | `agno_evals` | Evaluations |
| `knowledge_table` | `agno_knowledge` | RAG knowledge |
| `traces_table` | `agno_traces` | Execution traces |
| `spans_table` | `agno_spans` | Trace spans |

Tables are auto-created on first use — no manual migration needed.

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

## MongoDB

Document-oriented storage. Uses collections instead of tables.

### Constructor

```python
from agno.db.mongo import MongoDb

db = MongoDb(
    db_url="mongodb://localhost:27017",
    db_name=None,                    # Database name
    db_client=None,                  # Existing MongoClient instance
    session_collection=None,         # Default: agno_sessions
    memory_collection=None,          # Default: agno_memories
    metrics_collection=None,
    eval_collection=None,
    knowledge_collection=None,
    traces_collection=None,
    spans_collection=None,
)
```

### Connection string formats

```
mongodb://localhost:27017
mongodb://username:password@host:port/database
mongodb+srv://username:password@cluster.mongodb.net/database
```

### Full example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.mongo import MongoDb
from agno.tools.hackernews import HackerNewsTools

db = MongoDb(db_url="mongodb://localhost:27017")

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    tools=[HackerNewsTools()],
    add_history_to_context=True,
)

agent.print_response("How many people live in Canada?", session_id="mongo_chat")
agent.print_response("What is their national anthem?", session_id="mongo_chat")
```

### Async MongoDB

```python
from agno.db.mongo import AsyncMongoDb

db = AsyncMongoDb(db_url="mongodb://localhost:27017")
```

### Docker setup

```bash
docker run -d \
  --name local-mongo \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=mongoadmin \
  -e MONGO_INITDB_ROOT_PASSWORD=secret \
  mongo
```

---

## Redis

In-memory key-value store. Fastest backend with optional TTL for auto-expiry.

### Constructor

```python
from agno.db.redis import RedisDb

db = RedisDb(
    db_url="redis://localhost:6379",
    redis_client=None,        # Existing Redis client
    db_prefix="agno",         # Prefix for all keys
    expire=None,              # TTL in seconds (None = no expiry)
    session_table=None,
    memory_table=None,
    metrics_table=None,
    eval_table=None,
    knowledge_table=None,
    traces_table=None,
    spans_table=None,
)
```

### Connection string formats

```
redis://localhost:6379
redis://localhost:6379/0
rediss://user:password@host:port/db
```

### Full example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.redis import RedisDb

db = RedisDb(db_url="redis://localhost:6379")

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    add_history_to_context=True,
)

agent.print_response("My name is Alice", session_id="redis_chat")
agent.print_response("What's my name?", session_id="redis_chat")
```

### With TTL (auto-expire sessions after 1 hour)

```python
db = RedisDb(
    db_url="redis://localhost:6379",
    expire=3600,  # Sessions expire after 3600 seconds
)
```

### Docker setup

```bash
docker run -d --name my-redis -p 6379:6379 redis
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

## DynamoDB

AWS serverless database. Uses AWS credentials from environment.

### Constructor

```python
from agno.db.dynamo import DynamoDb

db = DynamoDb(
    region_name=None,              # AWS region (or AWS_REGION env var)
    aws_access_key_id=None,        # Or AWS_ACCESS_KEY_ID env var
    aws_secret_access_key=None,    # Or AWS_SECRET_ACCESS_KEY env var
    db_client=None,                # Existing DynamoDB client
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
from agno.db.dynamo import DynamoDb

db = DynamoDb()  # Uses AWS credentials from environment

agent = Agent(db=db, add_history_to_context=True)
```

### Environment variables

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

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

### Async MySQL

```python
from agno.db.mysql import AsyncMySQLDb

db = AsyncMySQLDb(db_url="mysql+aiomysql://user:password@localhost:3306/mydb")
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

## Quick Reference: Choosing a Backend

| Scenario | Recommended Backend |
|----------|-------------------|
| Local development | `SqliteDb` |
| Production (general) | `PostgresDb` |
| Production (async) | `AsyncPostgresDb` |
| Hosted Postgres | `PostgresDb` with Supabase or Neon URL |
| Document-oriented | `MongoDb` |
| Fast caching / TTL | `RedisDb` |
| AWS serverless | `DynamoDb` |
| MySQL environment | `MySQLDb` |
| Testing | `InMemoryDb` |

## Install Dependencies

```bash
# PostgreSQL
uv pip install -U 'agno[postgres]'

# MongoDB
uv pip install -U 'agno[mongo]'

# Redis
uv pip install -U 'agno[redis]'

# MySQL
uv pip install -U 'agno[mysql]'

# DynamoDB
uv pip install -U 'agno[aws]'

# SQLite — included, no extra install needed
```
