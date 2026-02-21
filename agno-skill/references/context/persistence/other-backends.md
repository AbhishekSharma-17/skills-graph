# Other Backends

MySQL, SingleStore, InMemory, and JSON file backends.

---

## MySQL

General-purpose relational database with wide ecosystem support.

### Install

```bash
uv pip install -U agno pymysql
```

### Docker Setup

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

### Sync Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.mysql import MySQLDb

db = MySQLDb(db_url="mysql+pymysql://ai:ai@localhost:3306/ai")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
)

agent.print_response("Hello!", session_id="mysql_session")
```

### Async Usage

```bash
uv pip install -U asyncmy
```

```python
from agno.db.mysql import AsyncMySQLDb

db = AsyncMySQLDb(db_url="mysql+asyncmy://ai:ai@localhost:3306/ai")
agent = Agent(db=db)
await agent.aprint_response("Hello!", session_id="mysql_session", stream=True)
```

### Connection String Formats

```
# Sync
mysql+pymysql://user:password@host:port/database

# Async
mysql+asyncmy://user:password@host:port/database

# With charset
mysql+pymysql://user:pass@host:port/db?charset=utf8mb4
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `Optional[str]` | UUID | Database instance ID |
| `db_url` | `Optional[str]` | — | Database connection URL |
| `db_engine` | `Optional[Engine]` | — | Existing SQLAlchemy engine |
| `db_schema` | `Optional[str]` | — | Database schema |
| `session_table` | `Optional[str]` | `agno_sessions` | Sessions table |
| `memory_table` | `Optional[str]` | `agno_memories` | Memories table |
| `metrics_table` | `Optional[str]` | `agno_metrics` | Metrics table |
| `eval_table` | `Optional[str]` | `agno_evals` | Eval runs table |
| `knowledge_table` | `Optional[str]` | `agno_knowledge` | Knowledge table |
| `traces_table` | `Optional[str]` | `agno_traces` | Traces table |
| `spans_table` | `Optional[str]` | `agno_spans` | Spans table |

---

## SingleStore

Distributed SQL database for high-volume analytics and real-time workloads.

### Install

```bash
uv pip install -U agno singlestoredb pymysql
```

### Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.singlestore import SingleStoreDb
from os import getenv

db_url = (
    f"mysql+pymysql://{getenv('SINGLESTORE_USERNAME')}:{getenv('SINGLESTORE_PASSWORD')}"
    f"@{getenv('SINGLESTORE_HOST')}:{getenv('SINGLESTORE_PORT')}"
    f"/{getenv('SINGLESTORE_DATABASE')}?charset=utf8mb4"
)

db = SingleStoreDb(db_url=db_url)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
)

agent.print_response("Hello!", session_id="singlestore_session")
```

### Constructor Parameters

Same as MySQL — uses `db_url`, `db_engine`, `db_schema`, and all `*_table` parameters.

---

## InMemory (Testing Only)

Data lives only in the current process. Lost when the process exits.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.in_memory import InMemoryDb

db = InMemoryDb()

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
)

agent.print_response("Hello!", session_id="test_session")
agent.print_response("What did I say?", session_id="test_session")
# Works within the same process, lost on restart
```

No constructor parameters required. Use for unit tests and quick demos.

---

## JSON (File-Based Testing)

Stores sessions as JSON files on disk. Not for production.

### Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.json import JsonDb

db = JsonDb(db_path="tmp/json_db")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
)

agent.print_response("Hello!", session_id="json_session")
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `Optional[str]` | UUID | Database instance ID |
| `db_path` | `Optional[str]` | — | Directory path for JSON files |
| `session_table` | `Optional[str]` | — | JSON file for sessions |
| `memory_table` | `Optional[str]` | — | JSON file for memories |
| `metrics_table` | `Optional[str]` | — | JSON file for metrics |
| `eval_table` | `Optional[str]` | — | JSON file for eval runs |
| `knowledge_table` | `Optional[str]` | — | JSON file for knowledge |
| `traces_table` | `Optional[str]` | — | JSON file for traces |
| `spans_table` | `Optional[str]` | — | JSON file for spans |

The `db_path` directory is created automatically if it doesn't exist.
