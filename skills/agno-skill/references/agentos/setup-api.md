# AgentOS: Setup & API

Guide to running AgentOS locally and using the API endpoints.


## Contents

- [Running AgentOS Locally](#running-agentos-locally)
- [API Endpoints](#api-endpoints)
- [Connecting to Control Plane](#connecting-to-control-plane)
- [Using the API](#using-the-api)
- [AgentOS with Registry](#agentos-with-registry)
- [AgentOS Tracing Setup](#agentos-tracing-setup)

## Running AgentOS Locally

### 1. Setup Virtual Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Agno with OS Support

```bash
uv pip install -U 'agno[os]'
```

### 3. Create Your AgentOS

Create a file `my_os.py`:

```python
from agno.os import AgentOS
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude

# Create an agent
agent = Agent(
    name="Assistant",
    model=Claude(id="claude-sonnet-4-5"),
    db=SqliteDb(db_file="agno.db"),
    add_history_to_context=True,
    markdown=True,
)

# Create AgentOS instance
agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    db=SqliteDb(db_file="agno.db"),
)

# Export for FastAPI dev server
app = agent_os.get_app()
```

### 4. Run the Server

```bash
fastapi dev my_os.py
```

Your AgentOS is now running at `http://localhost:8000`

## API Endpoints

The AgentOS exposes 50+ endpoints for managing agents, teams, workflows, and sessions.

### Base Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check / root endpoint |
| `/docs` | GET | Swagger UI documentation |
| `/config` | GET | Retrieve AgentOS configuration |
| `/openapi.json` | GET | OpenAPI schema |

### Agent Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents` | GET | List all agents |
| `/agents/{name}` | GET | Get agent by name |
| `/agents/{name}/run` | POST | Run agent with message |
| `/agents/{name}/sessions` | GET | List agent sessions |
| `/agents/{name}/messages` | GET | Get agent messages |

### Team Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/teams` | GET | List all teams |
| `/teams/{name}` | GET | Get team by name |
| `/teams/{name}/run` | POST | Run team with message |

### Workflow Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflows` | GET | List all workflows |
| `/workflows/{name}` | GET | Get workflow by name |
| `/workflows/{name}/run` | POST | Run workflow |

### Session Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sessions` | GET | List sessions |
| `/sessions/{session_id}` | GET | Get session details |
| `/sessions/{session_id}/run` | POST | Run in specific session |

### Memory Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/memory` | GET | List memory entries |
| `/memory/{id}` | GET | Get memory by ID |
| `/memory` | POST | Create memory entry |
| `/memory/{id}` | PUT | Update memory entry |
| `/memory/{id}` | DELETE | Delete memory entry |

### Knowledge Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/knowledge` | GET | List knowledge bases |
| `/knowledge/{id}/search` | POST | Search knowledge base |
| `/knowledge/{id}/add` | POST | Add document to knowledge |

### Evaluation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/evals` | GET | List evaluations |
| `/evals` | POST | Run evaluation |
| `/evals/{id}` | GET | Get evaluation results |

### Metrics Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/metrics` | GET | Get system metrics |
| `/metrics/runs` | GET | List run metrics |

## Connecting to Control Plane

The control plane at **os.agno.com** provides a browser interface to manage your AgentOS.

### Setup Steps

1. **Create Control Plane Account**
   - Visit https://os.agno.com
   - Sign up or log in with your account

2. **Add New AgentOS**
   - Click "Add New OS" in the dashboard
   - Fill in the following fields:

| Field | Value | Notes |
|-------|-------|-------|
| **OS Name** | `my_os` | Unique identifier |
| **Environment** | `development` or `production` | Use `development` for local testing |
| **Endpoint URL** | `http://localhost:8000` | Public URL where AgentOS runs |
| **OS Key** | Auto-generated | Store securely in `OS_SECURITY_KEY` env var |
| **Tags** | Optional | For organization (e.g., `dev`, `demo`) |

3. **Configure Environment**
   - Set `OS_SECURITY_KEY` environment variable:
   ```bash
   export OS_SECURITY_KEY="your_key_from_control_plane"
   ```

### Control Plane Features

**Chat Interface**
- Chat with agents, teams, and workflows directly from browser
- Switch between different agents without code changes
- Access full conversation history

**Tracing & Debugging**
- Tree view of agent execution flow
- Waterfall visualization of API calls
- Timing and performance metrics
- Token usage tracking

**Session Management**
- View all user sessions
- Track session metadata and history
- Archive or delete old sessions

**Knowledge Management**
- Upload documents and knowledge bases
- Search indexed content
- Manage document versions

**Memory Management**
- View and edit agent memories
- Search memory entries
- Clear old memories

**User Management**
- Invite team members (Owner/Member roles)
- Control access to AgentOS instances
- Audit logs for compliance

## Using the API

### Running an Agent

**Streaming Response**

```bash
curl -X POST "http://localhost:8000/agents/Assistant/run" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?",
    "stream": true
  }' \
  -N  # Enable streaming output
```

**Non-Streaming Response**

```bash
curl -X POST "http://localhost:8000/agents/Assistant/run" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?"
  }'
```

### Running with Session

```bash
curl -X POST "http://localhost:8000/agents/Assistant/run" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Remember this: I like Python",
    "session_id": "user_123",
    "user_id": "user_123"
  }'
```

### Passing Dependencies

```python
from agno.os import AgentOS
from agno.agent import Agent
from agno.models.anthropic import Claude

agent = Agent(
    name="DataAnalyst",
    model=Claude(id="claude-sonnet-4-5"),
    tools=[some_tool],  # Pass tools/dependencies
)

agent_os = AgentOS(agents=[agent])
```

### Using Output Schema

Enforce structured responses:

```python
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    summary: str
    key_points: list[str]
    confidence: float

agent = Agent(
    name="Analyst",
    model=Claude(id="claude-sonnet-4-5"),
    output_schema=AnalysisResult,  # Enforce structure
)
```

### Cancelling Runs

```bash
# Start a run and get run_id
RUN_ID=$(curl -X POST "http://localhost:8000/agents/Assistant/run" \
  -H "Content-Type: application/json" \
  -d '{"message": "Long operation..."}' \
  -s | jq -r '.run_id')

# Cancel the run
curl -X POST "http://localhost:8000/runs/$RUN_ID/cancel" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Authentication with JWT

For secure AgentOS with RBAC enabled:

```bash
# Get JWT token from control plane or generate locally
JWT_TOKEN="your.jwt.token.here"

# Use in API requests
curl -X POST "http://localhost:8000/agents/Assistant/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"message": "Secure message"}'
```

## AgentOS with Registry

Pre-register tools, models, and databases for visual builder:

```python
from agno.os import AgentOS, Registry
from agno.agent import Agent
from agno.tools import WebSearch, Calculator
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb

# Create registry
registry = Registry()
registry.register_tool("web_search", WebSearch())
registry.register_tool("calculator", Calculator())
registry.register_model("claude", Claude(id="claude-sonnet-4-5"))
registry.register_db("sqlite", SqliteDb(db_file="agno.db"))

# Use registry in AgentOS
agent_os = AgentOS(
    name="my_os",
    agents=[Agent(name="Assistant", model=Claude())],
    registry=registry,
)
```

## AgentOS Tracing Setup

Enable tracing to capture all agent executions, tool calls, and API interactions.

### Single Database Setup

```python
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb

agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    db=SqliteDb(db_file="agno.db"),
    tracing=True,  # Enable tracing
)
```

### Multiple Databases

Separate agent data from trace data:

```python
from agno.os import AgentOS
from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb

agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    db=PostgresDb(connection_string="postgresql://..."),  # Agent data
    tracing=True,
    # Traces automatically use the primary db
)
```

### Using setup_tracing()

Advanced tracing configuration:

```python
from agno.os import AgentOS, setup_tracing
from agno.db.sqlite import SqliteDb

setup_tracing(
    db=SqliteDb(db_file="traces.db"),
    service_name="my_agent_os",
    enabled=True,
)

agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    tracing=True,
)
```

### Scenarios Table

The tracing system automatically creates a `scenarios` table to group related traces:

```sql
SELECT * FROM scenarios;
-- Returns: id, name, created_at, description, status
```

View traces for a scenario in the control plane UI under Tracing > Tree View.
