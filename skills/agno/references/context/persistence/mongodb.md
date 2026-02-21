# MongoDB Backend

Document-oriented storage with flexible schema. Supports both sync and async with MongoDB Atlas or self-hosted.

## Install

```bash
uv pip install -U agno pymongo
```

## Docker Setup

```bash
docker run -d \
  --name local-mongo \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=mongoadmin \
  -e MONGO_INITDB_ROOT_PASSWORD=secret \
  mongo
```

## Sync Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.mongo import MongoDb

db = MongoDb(
    db_url="mongodb://mongoadmin:secret@localhost:27017",
    db_name="agno",
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
)

agent.print_response("Hello!", session_id="mongo_session")
```

## Async Usage

```python
from agno.db.mongo import AsyncMongoDb

db = AsyncMongoDb(
    db_url="mongodb://mongoadmin:secret@localhost:27017",
    db_name="agno",
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
)

await agent.aprint_response("Hello!", session_id="mongo_session", stream=True)
```

## Connection String Formats

```
# Local
mongodb://localhost:27017

# With auth
mongodb://username:password@localhost:27017

# MongoDB Atlas
mongodb+srv://username:password@cluster.mongodb.net

# With database
mongodb://username:password@localhost:27017/mydb
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `Optional[str]` | UUID | Database instance ID |
| `db_url` | `Optional[str]` | — | MongoDB connection URL |
| `db_client` | `Optional[MongoClient]` | — | Existing MongoDB client |
| `db_name` | `Optional[str]` | — | Database name |
| `session_collection` | `Optional[str]` | `agno_sessions` | Sessions collection |
| `memory_collection` | `Optional[str]` | `agno_memories` | Memories collection |
| `metrics_collection` | `Optional[str]` | `agno_metrics` | Metrics collection |
| `eval_collection` | `Optional[str]` | `agno_evals` | Evaluation runs collection |
| `knowledge_collection` | `Optional[str]` | `agno_knowledge` | Knowledge collection |
| `traces_collection` | `Optional[str]` | `agno_traces` | Traces collection |
| `spans_collection` | `Optional[str]` | `agno_spans` | Spans collection |

Note: MongoDB uses **collection** names instead of table names.

## Custom Collections

```python
db = MongoDb(
    db_url="mongodb://localhost:27017",
    db_name="my_agents",
    session_collection="agent_sessions",
    memory_collection="agent_memories",
)
```

## With Existing Client

```python
from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017",
    maxPoolSize=50,
    connectTimeoutMS=5000,
)

db = MongoDb(db_client=client, db_name="agno")
```

## MongoDB Atlas

```python
import os

db = MongoDb(
    db_url=os.getenv("MONGODB_ATLAS_URI"),
    db_name="production_agents",
)
```
