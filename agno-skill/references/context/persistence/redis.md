# Redis Backend

In-memory data store with optional TTL-based expiry. Ideal for session caching and high-throughput scenarios.

## Install

```bash
uv pip install -U agno redis
```

## Docker Setup

```bash
docker run -d \
  --name my-redis \
  -p 6379:6379 \
  redis
```

## Basic Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.redis import RedisDb

db = RedisDb(db_url="redis://localhost:6379")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
)

agent.print_response("Hello!", session_id="redis_session")
```

## With TTL Expiry

Sessions automatically expire after the specified time:

```python
db = RedisDb(
    db_url="redis://localhost:6379",
    expire=86400,  # Sessions expire after 24 hours
)
```

## With Key Prefix

Namespace your keys to avoid collisions:

```python
db = RedisDb(
    db_url="redis://localhost:6379",
    db_prefix="my_app",   # Keys prefixed with "my_app:"
    expire=3600,           # 1 hour TTL
)
```

## Connection String Formats

```
# Standard
redis://localhost:6379

# With auth
redis://user:password@localhost:6379

# With database number
redis://localhost:6379/0

# SSL/TLS
rediss://user:password@host:port/db
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `Optional[str]` | UUID | Database instance ID |
| `db_url` | `Optional[str]` | — | Redis connection URL |
| `redis_client` | `Optional[Redis]` | — | Existing Redis client |
| `db_prefix` | `str` | `"agno"` | Prefix for all Redis keys |
| `expire` | `Optional[int]` | — | TTL for keys in seconds |
| `session_table` | `Optional[str]` | — | Sessions key namespace |
| `memory_table` | `Optional[str]` | — | Memories key namespace |
| `metrics_table` | `Optional[str]` | — | Metrics key namespace |
| `eval_table` | `Optional[str]` | — | Eval runs key namespace |
| `knowledge_table` | `Optional[str]` | — | Knowledge key namespace |
| `traces_table` | `Optional[str]` | — | Traces key namespace |
| `spans_table` | `Optional[str]` | — | Spans key namespace |

## With Existing Client

```python
import redis

client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
    max_connections=20,
)

db = RedisDb(redis_client=client, db_prefix="my_app")
```

## Notes

- Redis stores data in memory — ensure you have enough RAM for your session volume.
- Use `expire` to automatically clean up old sessions.
- Redis is single-threaded but extremely fast for read/write operations.
- No async variant currently available — sync only.
- Data persistence depends on Redis configuration (RDB snapshots, AOF, or none).
