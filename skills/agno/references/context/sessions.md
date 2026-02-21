# Sessions

A session is a multi-turn conversation identified by a `session_id`. Each call to `agent.run()` or `agent.print_response()` creates a new **run** within the session. Without a database, sessions live only in memory; with a database, they persist across restarts.

## Session Lifecycle

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(model=OpenAIResponses(id="gpt-5.2"))

# Auto-generates session_id and run_id
response = agent.run("Tell me a short story about a robot")
print(f"Run ID: {response.run_id}")         # Auto-generated UUID
print(f"Session ID: {response.session_id}")  # Auto-generated UUID
```

Each run within a session stores messages, tool calls, metrics, and the response.

## Custom Session IDs

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agent.db"),
)

# Auto-generated session_id
agent.run("Message 1")

# Custom session_id — use this to maintain conversation threads
agent.run("Message 2", session_id="user_123_session_456")

# Same session_id = continues the conversation
agent.run("Message 3", session_id="user_123_session_456")
```

You can also set a default session_id on the agent:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agent.db"),
    session_id="default_session",  # All runs use this unless overridden
)
```

## Multi-User Sessions

Different users get isolated conversation threads:

```python
# User 1 — own session
agent.print_response("Hello!", session_id="session_456", user_id="alice@example.com")

# User 2 — own session
agent.print_response("Hello!", session_id="session_789", user_id="bob@example.com")

# Same user, different session (like browser tabs)
agent.print_response("Continue...", session_id="session_999", user_id="alice@example.com")
```

## Session Caching

Cache sessions in memory to avoid repeated database reads:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agent.db"),
    session_id="my_session",
    cache_session=True,  # Cache in memory for speed
)

# First run: loads from DB and caches
agent.run("First message")

# Subsequent runs: uses cached session (faster)
agent.run("Second message")
```

**When caching helps:** many sequential turns in the same session, latency-sensitive deployments, or expensive database connections (Postgres, serverless).

## Session Naming

### Manual

```python
agent.set_session_name(
    session_id="session_001",
    session_name="Product Launch Planning",
)
name = agent.get_session_name(session_id="session_001")
print(name)  # "Product Launch Planning"
```

### Auto-Generated

Uses the model to generate a short name from the conversation:

```python
agent.set_session_name(session_id="session_123", autogenerate=True)
name = agent.get_session_name(session_id="session_123")
print(name)  # e.g., "E-commerce API Planning" (≤5 words)
```

## Accessing Session Data

```python
# Full session object
session = agent.get_session(session_id="session_123")

# All messages (including system, tool calls)
messages = session.get_messages()

# Simplified chat history (user/assistant pairs only)
chat_history = agent.get_chat_history(session_id="session_123")

# Session messages (user/assistant from each run)
messages = agent.get_session_messages(session_id="session_123")

# Last run output with metrics and tool calls
last_run = agent.get_last_run_output()

# Session state
state = agent.get_session_state(session_id="session_123")

# Session summary
summary = agent.get_session_summary(session_id="session_123")
```

## Deleting Sessions

```python
agent.delete_session(session_id="session_123")
```

## What Gets Stored

Each session record contains:

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | Unique session identifier |
| `session_type` | `str` | `"agent"`, `"team"`, or `"workflow"` |
| `agent_id` | `str` | Parent agent ID |
| `user_id` | `str` | User this session belongs to |
| `session_data` | `dict` | Name, state, media |
| `agent_data` | `dict` | Agent config and metadata |
| `metadata` | `dict` | Custom metadata |
| `runs` | `list` | All RunOutput objects |
| `summary` | `dict` | SessionSummary (if enabled) |
| `created_at` | `int` | Unix timestamp |
| `updated_at` | `int` | Unix timestamp |

## AgentSession Class

```python
@dataclass
class AgentSession:
    session_id: str
    agent_id: Optional[str] = None
    team_id: Optional[str] = None
    user_id: Optional[str] = None
    workflow_id: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    agent_data: Optional[Dict[str, Any]] = None
    team_data: Optional[Dict[str, Any]] = None
    workflow_data: Optional[Dict[str, Any]] = None
    runs: Optional[List[RunOutput]] = None
    summary: Optional[SessionSummary] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
```

**Key methods:**

```python
session.upsert_run(run)                 # Add/update a run
run = session.get_run(run_id)           # Get specific run
messages = session.get_messages(...)     # Get messages with filtering
summary = session.get_session_summary() # Get summary
history = session.get_chat_history(last_n_runs=None)
```
