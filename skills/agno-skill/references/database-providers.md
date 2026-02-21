# Database Providers

All 18 database backends supported by Agno for session storage, memory, knowledge, traces, and evals.

## Provider Index

### Relational Databases

| Provider | Class | Import | Connection |
|----------|-------|--------|------------|
| PostgreSQL | `PostgresDb` | `from agno.db.postgres import PostgresDb` | `PostgresDb(db_url="postgresql+psycopg://user:pass@host:5432/db")` |
| Async PostgreSQL | `AsyncPostgresDb` | `from agno.db.postgres import AsyncPostgresDb` | `AsyncPostgresDb(db_url="postgresql+asyncpg://user:pass@host:5432/db")` |
| MySQL | `MySQLDb` | `from agno.db.mysql import MySQLDb` | `MySQLDb(db_url="mysql+pymysql://user:pass@host:3306/db")` |
| Async MySQL | `AsyncMySQLDb` | `from agno.db.mysql import AsyncMySQLDb` | `AsyncMySQLDb(db_url="mysql+aiomysql://user:pass@host:3306/db")` |
| SQLite | `SqliteDb` | `from agno.db.sqlite import SqliteDb` | `SqliteDb(db_file="tmp/data.db")` |
| Async SQLite | `AsyncSqliteDb` | `from agno.db.sqlite import AsyncSqliteDb` | `AsyncSqliteDb(db_file="tmp/data.db")` |

### NoSQL Databases

| Provider | Class | Import | Connection |
|----------|-------|--------|------------|
| MongoDB | `MongoDb` | `from agno.db.mongo import MongoDb` | `MongoDb(db_url="mongodb://localhost:27017")` |
| Async MongoDB | `AsyncMongoDb` | `from agno.db.mongo import AsyncMongoDb` | `AsyncMongoDb(db_url="mongodb://localhost:27017")` |
| Redis | `RedisDb` | `from agno.db.redis import RedisDb` | `RedisDb(db_url="redis://localhost:6379")` |
| DynamoDB | `DynamoDb` | `from agno.db.dynamo import DynamoDb` | `DynamoDb()` (uses AWS credentials) |
| Firestore | `FirestoreDb` | `from agno.db.firestore import FirestoreDb` | `FirestoreDb(project_id="my-project")` |
| SurrealDB | `SurrealDb` | `from agno.db.surrealdb import SurrealDb` | `SurrealDb(None, url, creds, namespace, database)` |

### Database Services

| Provider | Class | Import | Connection |
|----------|-------|--------|------------|
| Neon | `PostgresDb` | `from agno.db.postgres import PostgresDb` | `PostgresDb(db_url=getenv("NEON_DB_URL"))` |
| Supabase | `PostgresDb` | `from agno.db.postgres import PostgresDb` | `PostgresDb(db_url=f"postgresql://postgres:{pw}@db.{project}:5432/postgres")` |
| SingleStore | `SingleStoreDb` | `from agno.db.singlestore import SingleStoreDb` | `SingleStoreDb(db_url="mysql+pymysql://user:pass@host:port/db")` |

### Storage & File Systems

| Provider | Class | Import | Connection |
|----------|-------|--------|------------|
| Google Cloud Storage | `GcsDb` | `from agno.db.gcs import GcsDb` | `GcsDb(bucket_name="my-bucket")` |
| JSON | `JsonDb` | `from agno.db.json import JsonDb` | `JsonDb(dir_path="tmp/json_db")` |
| In-Memory | `InMemoryDb` | `from agno.db.memory import InMemoryDb` | `InMemoryDb()` |

## Common Parameters

All database classes share these table/collection configuration parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `Optional[str]` | Database instance ID (UUID default) |
| `session_table` | `Optional[str]` | Table for Agent/Team/Workflow sessions |
| `memory_table` | `Optional[str]` | Table for user memories |
| `metrics_table` | `Optional[str]` | Table for metrics |
| `eval_table` | `Optional[str]` | Table for evaluation runs |
| `knowledge_table` | `Optional[str]` | Table for knowledge documents |
| `traces_table` | `Optional[str]` | Table for traces |
| `spans_table` | `Optional[str]` | Table for spans |

Note: MongoDB/Firestore use `*_collection` instead of `*_table`.

## Provider-Specific Parameters

### PostgreSQL / MySQL / SQLite (SQLAlchemy-based)

| Parameter | Type | Description |
|-----------|------|-------------|
| `db_url` | `Optional[str]` | SQLAlchemy connection URL |
| `db_engine` | `Optional[Engine]` | Pre-configured SQLAlchemy engine |
| `db_schema` | `Optional[str]` | Database schema (Postgres only) |
| `db_file` | `Optional[str]` | Database file path (SQLite only) |

### Redis

| Parameter | Type | Description |
|-----------|------|-------------|
| `db_url` | `Optional[str]` | Redis URL (redis:// or rediss://) |
| `redis_client` | `Optional[Redis]` | Pre-configured Redis client |
| `db_prefix` | `str` | Key prefix (default: "agno") |
| `expire` | `Optional[int]` | TTL for keys in seconds |

### DynamoDB

| Parameter | Type | Description |
|-----------|------|-------------|
| `region_name` | `Optional[str]` | AWS region |
| `aws_access_key_id` | `Optional[str]` | AWS access key |
| `aws_secret_access_key` | `Optional[str]` | AWS secret key |
| `db_client` | `None` | Pre-configured DynamoDB client |

### MongoDB

| Parameter | Type | Description |
|-----------|------|-------------|
| `db_url` | `Optional[str]` | MongoDB connection URL |
| `db_name` | `Optional[str]` | Database name |
| `db_client` | `Optional[MongoClient]` | Pre-configured client |

### Firestore

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | `Optional[str]` | GCP project ID |
| `db_client` | `Optional[Client]` | Pre-configured Firestore client |

### SurrealDB

| Parameter | Type | Description |
|-----------|------|-------------|
| `db_url` | `str` | Connection URL (ws:// or http://) |
| `db_creds` | `dict` | Credentials (username, password) |
| `db_ns` | `str` | Namespace |
| `db_db` | `str` | Database name |

## Docker Quick Start Commands

```bash
# PostgreSQL with pgvector
docker run -d -e POSTGRES_DB=ai -e POSTGRES_USER=ai -e POSTGRES_PASSWORD=ai \
  -p 5532:5432 --name pgvector agnohq/pgvector:16

# MongoDB
docker run -d --name local-mongo -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=mongoadmin -e MONGO_INITDB_ROOT_PASSWORD=secret mongo

# Redis
docker run -d --name my-redis -p 6379:6379 redis

# SurrealDB
docker run --rm -p 8000:8000 surrealdb/surrealdb:latest start --user root --pass root
```

## Custom Tables

Select specific tables to use instead of defaults:

```python
from agno.db.postgres import PostgresDb

db = PostgresDb(
    db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    session_table="my_sessions",
    memory_table="my_memories",
    traces_table="my_traces",
)
```

## Usage Examples

### PostgreSQL Setup

```python
from agno.db.postgres import PostgresDb

db = PostgresDb(
    db_url="postgresql+psycopg://user:password@localhost:5432/agno_db"
)
```

### Redis with TTL

```python
from agno.db.redis import RedisDb

db = RedisDb(
    db_url="redis://localhost:6379",
    db_prefix="my_app",
    expire=3600  # 1 hour TTL
)
```

### MongoDB with Custom Collections

```python
from agno.db.mongo import MongoDb

db = MongoDb(
    db_url="mongodb://localhost:27017",
    db_name="agno_db",
    session_collection="sessions",
    memory_collection="memories"
)
```

### SQLite for Development

```python
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="agno.db")
```

### DynamoDB with AWS

```python
from agno.db.dynamo import DynamoDb

db = DynamoDb(
    region_name="us-east-1",
    aws_access_key_id="YOUR_KEY",
    aws_secret_access_key="YOUR_SECRET"
)
```

### Firestore with GCP

```python
from agno.db.firestore import FirestoreDb

db = FirestoreDb(project_id="my-gcp-project")
```

## Connection Strategies

### URL-Based Connections (Most Providers)

Most databases accept connection URLs:

```python
db = PostgresDb(db_url="postgresql+psycopg://user:pass@host:5432/db")
db = MySQLDb(db_url="mysql+pymysql://user:pass@host:3306/db")
db = MongoDb(db_url="mongodb://localhost:27017")
```

### Client-Based Connections

For databases requiring pre-configured clients:

```python
from agno.db.mongo import MongoDb
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = MongoDb(db_client=client, db_name="agno_db")
```

### File-Based (SQLite, JSON)

```python
from agno.db.sqlite import SqliteDb
from agno.db.json import JsonDb

sqlite_db = SqliteDb(db_file="data/agno.db")
json_db = JsonDb(dir_path="data/json_store")
```

## Cross-References

→ Database concepts: `references/database.md`
→ Context persistence: `references/context/persistence.md`
