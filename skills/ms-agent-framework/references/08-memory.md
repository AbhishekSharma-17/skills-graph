# Memory — History Providers, Context Providers, Persistence

## Memory Architecture

```
Agent Run
  → Context Providers generate context strings (prepended to messages)
  → History Provider loads previous messages
  → Combined context + history + new message → LLM
  → Response stored by History Provider
```

## InMemoryHistoryProvider

Built-in in-memory history storage:

```python
from agent_framework import InMemoryHistoryProvider

# Primary memory — loads messages into context
memory = InMemoryHistoryProvider(
    name="memory",
    load_messages=True,  # Messages are included in LLM context
)

# Audit store — records everything but doesn't load into context
audit = InMemoryHistoryProvider(
    name="audit",
    load_messages=False,           # NOT included in LLM context
    store_context_messages=True,   # But captures enriched messages
)

agent = client.as_agent(
    name="MemoryAgent",
    instructions="You remember conversations.",
    context_providers=[memory, audit],
)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | required | Unique name for this provider |
| `load_messages` | `bool` | `True` | Whether to load stored messages into LLM context |
| `store_context_messages` | `bool` | `False` | Whether to store context-enriched messages |

### Critical Rule

**Only ONE history provider should have `load_messages=True`**. Multiple providers loading messages causes duplicate context and token waste.

## Context Providers

Inject dynamic information into agent context on every turn. They run before each LLM call.

### BaseContextProvider

```python
from agent_framework import BaseContextProvider, AgentSession

class UserProfileProvider(BaseContextProvider):
    """Injects user profile into every agent turn."""

    async def get_context(self, session: AgentSession, **kwargs) -> str:
        user_id = session.state.get("user_id")
        if not user_id:
            return ""

        profile = await fetch_user_profile(user_id)
        return f"""Current user: {profile.name}
Role: {profile.role}
Preferences: {profile.preferences}"""

# Register with agent
agent = client.as_agent(
    name="PersonalizedAgent",
    context_providers=[UserProfileProvider()],
)
```

### How Context Providers Work

```
Turn 1:
  Context Provider output → "User: Alice, Role: Admin"
  + Instructions → "You are a helpful assistant"
  + User message → "Help me with permissions"
  → All sent to LLM

Turn 2:
  Context Provider runs AGAIN → "User: Alice, Role: Admin"
  + Updated context
  + Conversation history
  + New user message
  → All sent to LLM
```

## Custom History Provider (Database-Backed)

```python
from agent_framework import BaseContextProvider

class DatabaseHistoryProvider(BaseContextProvider):
    """Store and load conversation history from a database."""

    def __init__(self, db_client, name="db_history"):
        self.db_client = db_client
        self.name = name

    async def get_history(self, session_id: str):
        """Load previous messages from database."""
        return await self.db_client.get_messages(session_id)

    async def store_message(self, session_id: str, message):
        """Save new message to database."""
        await self.db_client.insert_message(session_id, message)

# Use with agent
history = DatabaseHistoryProvider(db_client)
agent = client.as_agent(
    context_providers=[history],
)
```

## Real-World Context Providers

### Time-Aware Provider

```python
class TimeContextProvider(BaseContextProvider):
    async def get_context(self, session: AgentSession, **kwargs) -> str:
        from datetime import datetime
        now = datetime.now()
        is_business = 9 <= now.hour < 17 and now.weekday() < 5
        return f"""Current time: {now.strftime('%Y-%m-%d %H:%M')}
Business hours: {'Yes' if is_business else 'No'}"""
```

### RAG Context Provider

```python
class RAGProvider(BaseContextProvider):
    def __init__(self, vector_store):
        self.vector_store = vector_store

    async def get_context(self, session: AgentSession, **kwargs) -> str:
        last_msg = session.messages[-1].text if session.messages else ""
        if not last_msg:
            return ""

        results = await self.vector_store.search(last_msg, top_k=5)
        if not results:
            return "No relevant documents found."

        parts = ["Relevant documents:"]
        for i, r in enumerate(results, 1):
            parts.append(f"[{i}] {r.title}: {r.content[:300]}")
        return "\n".join(parts)
```

### Config-Based Provider

```python
class FeatureFlagProvider(BaseContextProvider):
    async def get_context(self, session: AgentSession, **kwargs) -> str:
        flags = await get_feature_flags(session.state.get("user_id"))
        enabled = [f for f, v in flags.items() if v]
        return f"Enabled features: {', '.join(enabled)}"
```

## Multiple Providers Together

```python
agent = client.as_agent(
    name="FullFeaturedAgent",
    instructions="You are a helpful assistant.",
    context_providers=[
        InMemoryHistoryProvider("history", load_messages=True),  # History
        UserProfileProvider(),            # User context
        TimeContextProvider(),            # Time awareness
        RAGProvider(vector_store),        # Document retrieval
        FeatureFlagProvider(),            # Feature flags
    ],
)
```

**Execution order:** Providers run in the order they're listed. All output is combined before sending to the LLM.

## Memory Provider Requirements

1. Store messages under session-scoped keys
2. Keep returned history within model context limits
3. Persist provider-specific identifiers in `session.state`
4. Only one provider should use `load_messages=True`
5. Providers run on every turn — keep them fast

## Persistence Patterns

### Redis-Based Memory

```python
import redis.asyncio as redis

class RedisHistoryProvider(BaseContextProvider):
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    async def get_context(self, session: AgentSession, **kwargs) -> str:
        key = f"history:{session.id}"
        messages = await self.redis.lrange(key, 0, -1)
        return "\n".join(m.decode() for m in messages)
```

### Session Expiration

```python
async def get_or_create_session(user_id: str, max_age_hours=24):
    cached = await redis.get(f"session:{user_id}")
    if cached:
        data = json.loads(cached)
        created = datetime.fromisoformat(data.get("_created", ""))
        if (datetime.utcnow() - created).total_seconds() < max_age_hours * 3600:
            return AgentSession.from_dict(data)

    session = agent.create_session()
    session.state["_created"] = datetime.utcnow().isoformat()
    return session
```
