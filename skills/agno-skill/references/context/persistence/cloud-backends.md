# Cloud Backends

Managed and serverless database options for cloud-native deployments.

---

## DynamoDB (AWS)

Serverless NoSQL with auto-scaling. No infrastructure management needed.

### Install

```bash
uv pip install -U agno boto3
```

### Configuration

Set AWS credentials via environment variables:

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.dynamo import DynamoDb

# Credentials from environment
db = DynamoDb()

# Or explicit credentials
db = DynamoDb(
    region_name="us-east-1",
    aws_access_key_id="YOUR_KEY",
    aws_secret_access_key="YOUR_SECRET",
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
)

agent.print_response("Hello!", session_id="dynamo_session")
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `Optional[str]` | UUID | Database instance ID |
| `region_name` | `Optional[str]` | — | AWS region |
| `aws_access_key_id` | `Optional[str]` | — | AWS access key |
| `aws_secret_access_key` | `Optional[str]` | — | AWS secret key |
| `session_table` | `Optional[str]` | — | Sessions table name |
| `memory_table` | `Optional[str]` | — | Memories table name |
| `metrics_table` | `Optional[str]` | — | Metrics table name |
| `eval_table` | `Optional[str]` | — | Eval runs table name |
| `knowledge_table` | `Optional[str]` | — | Knowledge table name |
| `traces_table` | `Optional[str]` | — | Traces table name |
| `spans_table` | `Optional[str]` | — | Spans table name |

---

## Firestore (Google Cloud)

Google Cloud's serverless document database with real-time sync.

### Install

```bash
uv pip install -U agno google-cloud-firestore
```

### Prerequisites

1. Enable Firestore in your GCP project
2. Configure gcloud credentials: `gcloud auth application-default login`

### Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.firestore import FirestoreDb

db = FirestoreDb(project_id="my-gcp-project")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
)

agent.print_response("Hello!", session_id="firestore_session")
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `Optional[str]` | UUID | Database instance ID |
| `project_id` | `Optional[str]` | — | GCP project ID |
| `db_client` | `Optional[Client]` | — | Existing Firestore client |
| `session_collection` | `Optional[str]` | — | Sessions collection |
| `memory_collection` | `Optional[str]` | — | Memories collection |
| `metrics_collection` | `Optional[str]` | — | Metrics collection |
| `eval_collection` | `Optional[str]` | — | Eval runs collection |
| `knowledge_collection` | `Optional[str]` | — | Knowledge collection |
| `traces_collection` | `Optional[str]` | — | Traces collection |
| `spans_collection` | `Optional[str]` | — | Spans collection |

---

## Supabase (Managed PostgreSQL)

Supabase provides managed PostgreSQL. Uses the same `PostgresDb` class since Supabase is PostgreSQL under the hood.

### Install

```bash
uv pip install -U agno psycopg[binary]
```

### Setup

1. Create a Supabase project at https://supabase.com
2. Get your project URL and database password from Settings > Database

### Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.postgres import PostgresDb
from os import getenv

SUPABASE_PROJECT = getenv("SUPABASE_PROJECT")
SUPABASE_PASSWORD = getenv("SUPABASE_PASSWORD")

db_url = f"postgresql://postgres:{SUPABASE_PASSWORD}@db.{SUPABASE_PROJECT}.supabase.co:5432/postgres"

db = PostgresDb(db_url=db_url)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
)

agent.print_response("Hello!", session_id="supabase_session")
```

### Async Variant

```python
from agno.db.postgres import AsyncPostgresDb

db_url = f"postgresql+psycopg_async://postgres:{SUPABASE_PASSWORD}@db.{SUPABASE_PROJECT}.supabase.co:5432/postgres"
db = AsyncPostgresDb(db_url=db_url)
```

---

## Neon (Serverless PostgreSQL)

Neon provides serverless PostgreSQL with auto-scaling and branching. Also uses the `PostgresDb` class.

### Install

```bash
uv pip install -U agno psycopg[binary]
```

### Setup

1. Sign up at https://neon.tech
2. Create a project and get the connection string

### Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.postgres import PostgresDb
from os import getenv

db = PostgresDb(db_url=getenv("NEON_DB_URL"))

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_history_to_context=True,
)

agent.print_response("Hello!", session_id="neon_session")
```

### Async Variant

```python
from agno.db.postgres import AsyncPostgresDb

db = AsyncPostgresDb(db_url=getenv("NEON_DB_URL_ASYNC"))
```
