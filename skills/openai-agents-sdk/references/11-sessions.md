# Sessions — Conversation Persistence

> Source: [openai.github.io/openai-agents-python/sessions](https://openai.github.io/openai-agents-python/sessions/)

## Overview

Sessions provide automatic conversation history management across multiple agent runs. Before each run, the runner retrieves conversation history for the session and prepends it to the input. After each run, new items are stored automatically.

Sessions cannot be combined with `conversation_id`, `previous_response_id`, or `auto_previous_response_id` in the same run.

## Quick Start

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant", instructions="Reply concisely.")
session = SQLiteSession("conversation_123")

# Turn 1 — history saved automatically
result = await Runner.run(
    agent, "What city is the Golden Gate Bridge in?", session=session
)
print(result.final_output)  # "San Francisco"

# Turn 2 — prior context loaded automatically
result = await Runner.run(
    agent, "What state is it in?", session=session
)
print(result.final_output)  # "California"
```

## Session Implementations

### SQLiteSession (Development)

```python
from agents import SQLiteSession

# In-memory (temporary — lost when process exits)
session = SQLiteSession("user_123")

# File-based (persistent across restarts)
session = SQLiteSession("user_123", "conversations.db")
```

### SQLAlchemySession (Production)

Production-ready persistence across any SQLAlchemy-supported database:

```python
from agents.extensions.memory import SQLAlchemySession

# From database URL
session = SQLAlchemySession.from_url(
    "user_123",
    url="postgresql+asyncpg://user:pass@localhost/db",
    create_tables=True,
)

# From existing engine
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
session = SQLAlchemySession("user_123", engine=engine, create_tables=True)
```

### EncryptedSession

Transparent encryption wrapper for any session implementation:

```python
from agents.extensions.memory import EncryptedSession, SQLAlchemySession

underlying = SQLAlchemySession.from_url(
    "user_123",
    url="sqlite+aiosqlite:///conversations.db",
    create_tables=True,
)

session = EncryptedSession(
    session_id="user_123",
    underlying_session=underlying,
    encryption_key="your-secret-key-min-32-chars",
    ttl=600,  # 10 minutes — items older than this are expired
)

result = await Runner.run(agent, "Hello", session=session)
```

### All Session Types

| Type | Best For |
|------|----------|
| `SQLiteSession` | Development, simple apps |
| `AsyncSQLiteSession` | Async SQLite via `aiosqlite` |
| `SQLAlchemySession` | Production — PostgreSQL, MySQL, etc. |
| `RedisSession` | Shared memory across workers |
| `MongoDBSession` | MongoDB-backed storage |
| `DaprSession` | Cloud-native with Dapr sidecars |
| `OpenAIConversationsSession` | Server-managed via OpenAI API |
| `OpenAIResponsesCompactionSession` | Long conversations with auto-compaction |
| `AdvancedSQLiteSession` | SQLite with branching and analytics |
| `EncryptedSession` | Encryption wrapper for any session |

## Session Operations

```python
session = SQLiteSession("user_123", "conversations.db")

# Get all stored items
items = await session.get_items()

# Add items manually
await session.add_items([
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
])

# Remove the most recent item (undo last turn)
last_item = await session.pop_item()

# Clear all history
await session.clear_session()
```

## Controlling History Retrieval

Limit how much history is loaded per run:

```python
from agents import RunConfig, SessionSettings

# Load only the last 50 items
result = await Runner.run(
    agent, "Summarize recent discussion.",
    session=session,
    run_config=RunConfig(session_settings=SessionSettings(limit=50)),
)

# Load all items (default)
result = await Runner.run(
    agent, "Full context needed.",
    session=session,
    run_config=RunConfig(session_settings=SessionSettings(limit=None)),
)
```

## Customizing History Merge

Control how history and new input combine:

```python
from agents import RunConfig

def keep_recent(history, new_input):
    """Keep only the last 10 history items."""
    return history[-10:] + new_input

result = await Runner.run(
    agent, "Continue from recent context.",
    session=session,
    run_config=RunConfig(session_input_callback=keep_recent),
)
```

## Multi-Agent Session Sharing

Different agents sharing the same session see unified history:

```python
support_agent = Agent(name="Support", instructions="Handle account issues.")
billing_agent = Agent(name="Billing", instructions="Handle billing questions.")

session = SQLiteSession("customer_456")

# Support agent handles first message
result = await Runner.run(support_agent, "My account is locked", session=session)

# Billing agent sees the full conversation when it takes over
result = await Runner.run(billing_agent, "What are my charges?", session=session)
```

## Custom Session Implementation

Implement the `SessionABC` interface for custom backends:

```python
from agents.memory.session import SessionABC
from agents.items import TResponseInputItem

class MyCustomSession(SessionABC):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._store: list[TResponseInputItem] = []

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        if limit is not None:
            return self._store[-limit:]
        return list(self._store)

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        self._store.extend(items)

    async def pop_item(self) -> TResponseInputItem | None:
        return self._store.pop() if self._store else None

    async def clear_session(self) -> None:
        self._store.clear()
```

## Session ID Naming Patterns

| Pattern | Example | Use Case |
|---------|---------|----------|
| User-based | `"user_12345"` | Per-user conversations |
| Thread-based | `"thread_abc123"` | Multi-thread support |
| Context-based | `"ticket_456"` | Per-ticket/per-case |
| Composite | `"user_123_thread_abc"` | User + thread isolation |

## Common Pitfalls

- **Mixing session with server state**: Can't use `session` with `conversation_id` or `previous_response_id` in the same run
- **Unbounded history**: Without `SessionSettings(limit=N)`, long conversations load all history, consuming excessive tokens
- **Missing persistence**: `SQLiteSession("id")` without a file path is in-memory only — history is lost on restart
- **Encryption key management**: `EncryptedSession` keys must be stored securely; losing the key means losing access to all encrypted history
- **Cross-session confusion**: Using the same session_id for unrelated conversations causes context pollution

## Related Topics

- **Running Agents:** `03-running-agents.md` — Session configuration in RunConfig
- **Context:** `07-context.md` — RunContextWrapper vs session state
- **Multi-Agent:** `08-multi-agent.md` — Shared sessions across agents
