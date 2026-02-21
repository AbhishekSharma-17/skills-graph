# AgentOS: Configuration & Security

Guide to configuring AgentOS, implementing security, and using background hooks and custom lifespan.


## Contents

- [Configuration](#configuration)
- [Security](#security)
- [Background Hooks](#background-hooks)
- [Custom Lifespan](#custom-lifespan)

## Configuration

AgentOS can be configured via YAML file or Python class.

### YAML Configuration

Create `agentOS.yaml`:

```yaml
name: my_os
environment: development

# Chat interface configuration
chat:
  suggested_prompts:
    - "What can you help me with?"
    - "Tell me about yourself"
  search_knowledge: true
  use_markdown: true

# Quick prompts for agents
quick_prompts:
  - prompt: "Summarize this"
    title: "Summary"
    triggers: ["summarize", "summary"]
  - prompt: "Find issues in this code"
    title: "Code Review"
    triggers: ["review", "check"]

# Memory configuration
memory:
  type: db  # Store in database
  max_size: 100
  retention_days: 90

# Knowledge bases
knowledge:
  - name: "documentation"
    path: "./docs"
    enabled: true
  - name: "policies"
    path: "./policies"
    enabled: true

# Session configuration
session:
  max_sessions: 1000
  session_timeout_minutes: 60
  store_in_db: true

# Evaluation configuration
evals:
  display_name: "Quality Metrics"
  scenarios:
    - name: "accuracy"
      type: "metric"
    - name: "latency"
      type: "metric"

# Domain-specific database configuration
domain_config:
  agents:
    db: sqlite
    path: "./agents.db"
  knowledge:
    db: postgres
    url: "postgresql://localhost/knowledge"
```

### Python Configuration

```python
from agno.os import AgentOS, AgentOSConfig

config = AgentOSConfig(
    name="my_os",
    environment="development",
    chat={
        "suggested_prompts": [
            "What can you help me with?",
            "Tell me about yourself",
        ],
        "search_knowledge": True,
        "use_markdown": True,
    },
    memory={
        "type": "db",
        "max_size": 100,
        "retention_days": 90,
    },
    knowledge=[
        {"name": "documentation", "path": "./docs", "enabled": True},
        {"name": "policies", "path": "./policies", "enabled": True},
    ],
    session={
        "max_sessions": 1000,
        "session_timeout_minutes": 60,
        "store_in_db": True,
    },
)

agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    config=config,
)
```

### Accessing Configuration

```python
# Get configuration via API
import requests

response = requests.get("http://localhost:8000/config")
config = response.json()

print(config["name"])        # "my_os"
print(config["environment"]) # "development"
```

## Security

### Basic Authentication

Enable simple API key authentication:

```python
import os
from agno.os import AgentOS

agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    # AgentOS reads OS_SECURITY_KEY environment variable
    # All API requests must include: X-API-Key header
)

# Set environment variable
os.environ["OS_SECURITY_KEY"] = "your-secret-key-here"
```

**Usage in API Requests:**

```bash
curl -X POST "http://localhost:8000/agents/Assistant/run" \
  -H "X-API-Key: your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### RBAC with JWT Authorization

Enable Role-Based Access Control with JWT tokens:

```python
import os
from agno.os import AgentOS

agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    authorization=True,  # Enable RBAC
)

# Set JWT verification key (from control plane)
os.environ["JWT_VERIFICATION_KEY"] = "your-jwt-key-here"
```

**JWT Token Structure:**

```json
{
  "sub": "user_123",
  "role": "owner",
  "scopes": ["read", "write", "delete"],
  "exp": 1709875200
}
```

**Token Scopes:**

| Scope | Permission | Resource |
|-------|-----------|----------|
| `read` | View agents, sessions, memory | All |
| `write` | Run agents, create sessions, edit memory | All |
| `delete` | Delete sessions, memory entries | All |
| `admin` | Manage users, RBAC configuration | AgentOS instance |

**Role Hierarchy:**

| Role | Scopes | Description |
|------|--------|-------------|
| `owner` | `read`, `write`, `delete`, `admin` | Full control |
| `member` | `read`, `write` | Run agents, create sessions |
| `viewer` | `read` | View-only access |

**Using JWT in API Requests:**

```bash
# Get token from control plane or generate locally
JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Include in Authorization header
curl -X POST "http://localhost:8000/agents/Assistant/run" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

**Generate JWT Locally (Development Only):**

```python
import jwt
from datetime import datetime, timedelta

secret = os.environ.get("JWT_VERIFICATION_KEY")

payload = {
    "sub": "user_123",
    "role": "owner",
    "scopes": ["read", "write", "delete"],
    "exp": datetime.utcnow() + timedelta(hours=24),
}

token = jwt.encode(payload, secret, algorithm="HS256")
print(f"Authorization: Bearer {token}")
```

## Background Hooks

Run non-blocking operations without delaying API responses.

### Why Background Hooks?

- User gets response immediately
- Long operations continue in background
- Prevents request timeouts
- Improves perceived performance

### Two Configuration Options

**Option 1: Global Background Mode**

Run all hooks in background:

```python
from agno.os import AgentOS

agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    run_hooks_in_background=True,  # All hooks run in background
)
```

**Option 2: Per-Hook Configuration**

Run specific hooks in background:

```python
from agno.hooks import hook

@hook(run_in_background=True)
def save_to_external_system(result):
    """This hook runs in background"""
    # Send data to external service
    requests.post("https://external-service.com/data", json=result)
    # Agent response returned before this completes

@hook(run_in_background=False)
def validate_result(result):
    """This hook runs before returning response"""
    # Validation must complete before response
    return validate(result)
```

### How It Works

Background hooks use **FastAPI BackgroundTasks**:

```python
from fastapi import BackgroundTasks
from agno.hooks import hook

@hook(run_in_background=True)
def process_async(data):
    # Receives deep copy of data (isolated from response)
    # Runs after response sent to client
    # Errors logged but don't affect client response
    pass
```

### Data Isolation

Background hooks receive **deep copies** of data:

```python
@hook(run_in_background=True)
def log_response(response):
    # response is a deep copy, not reference
    response["logged_at"] = datetime.now()  # Won't affect client response
    # Safe to modify without side effects
```

### Error Handling

Exceptions in background hooks are logged but don't affect responses:

```python
@hook(run_in_background=True)
def external_call(result):
    try:
        requests.post("https://service.com/log", json=result, timeout=5)
    except Exception as e:
        logger.error(f"Background hook failed: {e}")
        # Request already returned to client
        # Error logged for debugging
```

### Limitations

Background hooks have restrictions:

| Limitation | Reason |
|-----------|--------|
| Cannot modify request | Request already processed |
| Cannot modify response | Response already sent to client |
| Cannot access response body | Data isolated after serialization |
| Must handle own errors | No exception propagation to client |
| Timeout sensitive | Server shutdown may interrupt |

**Correct Usage:**

```python
# ✓ Log/audit data
@hook(run_in_background=True)
def audit_log(result):
    audit_db.insert({"action": "agent_run", "result": result})

# ✓ Sync to external systems
@hook(run_in_background=True)
def sync_to_crm(result):
    crm_client.create_contact(result["contact_data"])

# ✗ Cannot modify response
@hook(run_in_background=True)
def modify_response(response):
    response["added_field"] = "too late"  # Won't affect client
```

## Custom Lifespan

Manage startup and shutdown logic with custom lifespan context managers.

### Basic Lifespan

```python
from contextlib import asynccontextmanager
from agno.os import AgentOS

@asynccontextmanager
async def lifespan(app):
    # Startup logic
    print("AgentOS starting up...")
    db_pool = await initialize_database()
    cache = await initialize_cache()

    yield  # Application runs here

    # Shutdown logic
    print("AgentOS shutting down...")
    await db_pool.close()
    await cache.close()

agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    lifespan=lifespan,
)
```

### With Existing FastAPI App

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from agno.os import AgentOS

# Define custom lifespan
@asynccontextmanager
async def lifespan(app):
    # Startup
    print("Custom startup")
    yield
    # Shutdown
    print("Custom shutdown")

# Create custom FastAPI app
app = FastAPI(lifespan=lifespan)

# AgentOS wraps existing lifespan
agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    base_app=app,
    lifespan=lifespan,
)
```

### Use Cases

**Resource Initialization**

```python
@asynccontextmanager
async def lifespan(app):
    # Initialize connections
    app.state.db = await AsyncDatabase.connect("postgresql://...")
    app.state.redis = await aioredis.create_redis_pool("redis://...")
    app.state.llm_client = AsyncLLMClient(api_key=os.getenv("LLM_KEY"))

    yield

    # Cleanup
    await app.state.db.disconnect()
    app.state.redis.close()
    await app.state.llm_client.close()
```

**Health Checks**

```python
@asynccontextmanager
async def lifespan(app):
    # Check health on startup
    try:
        db_health = await check_database()
        cache_health = await check_cache()
        if not db_health or not cache_health:
            raise RuntimeError("Dependency health check failed")
    except Exception as e:
        logger.error(f"Startup health check failed: {e}")
        raise

    yield

    # Log shutdown
    logger.info("AgentOS shutdown completed")
```

**Scheduled Tasks**

```python
import asyncio
from agno.os import AgentOS

@asynccontextmanager
async def lifespan(app):
    # Start background task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Cancel on shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

async def periodic_cleanup():
    while True:
        await asyncio.sleep(3600)  # Every hour
        await cleanup_old_sessions()
        await cleanup_stale_memory()
```

### Complete Example

```python
from contextlib import asynccontextmanager
from agno.os import AgentOS
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    # STARTUP
    logger.info("Starting AgentOS...")

    # Initialize database
    app.state.db = SqliteDb(db_file="agno.db")
    await app.state.db.initialize()

    # Load configuration
    app.state.config = load_config("agentOS.yaml")

    # Validate environment
    if not validate_environment():
        raise RuntimeError("Environment validation failed")

    logger.info("AgentOS ready")

    yield  # Application runs

    # SHUTDOWN
    logger.info("Shutting down AgentOS...")

    # Cleanup database
    await app.state.db.close()

    # Cancel pending tasks
    pending = asyncio.all_tasks()
    for task in pending:
        task.cancel()

    logger.info("AgentOS shutdown complete")

# Create agent and OS
agent = Agent(
    name="Assistant",
    model=Claude(id="claude-sonnet-4-5"),
)

agent_os = AgentOS(
    name="my_os",
    agents=[agent],
    lifespan=lifespan,
)

app = agent_os.get_app()
```

### Key Points

- **Async first**: Use `async def` and `await` for all I/O operations
- **Error handling**: Exceptions in startup prevent server from starting
- **Cleanup guarantee**: Shutdown code runs even if errors occur during request handling
- **Wrap existing**: Custom lifespan wraps any existing FastAPI app lifespan
- **Resource state**: Store initialized resources in `app.state` for access in route handlers
