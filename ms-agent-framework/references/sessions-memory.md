# Sessions & Memory — State Management

## Table of Contents
1. [Sessions Overview](#sessions-overview)
2. [Creating and Using Sessions](#creating-and-using-sessions)
3. [Session Persistence](#session-persistence)
4. [Context Providers](#context-providers)
5. [Memory Providers](#memory-providers)
6. [Custom Context Provider](#custom-context-provider)
7. [Production Patterns](#production-patterns)

---

## Sessions Overview

An `AgentSession` manages conversation context across multiple `agent.run()` calls. Without a session, each call is independent — the agent has no memory of previous messages.

### With vs Without Session

```python
# WITHOUT session — no memory
r1 = await agent.run("My name is Alice")     # "Nice to meet you, Alice!"
r2 = await agent.run("What's my name?")      # "I don't know your name."

# WITH session — has memory
session = await agent.create_session()
r1 = await agent.run("My name is Alice", session=session)   # "Nice to meet you, Alice!"
r2 = await agent.run("What's my name?", session=session)    # "Your name is Alice!"
```

### Session Contains

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Local session identifier |
| `service_session_id` | `str` | Remote service session ID |
| `state` | `dict` | Mutable key-value store for custom data |
| `messages` | `List[Message]` | Conversation history |

---

## Creating and Using Sessions

### Create Session

```python
# Default session
session = await agent.create_session()

# With custom ID
session = await agent.create_session(session_id="user-123-session-1")
```

### Multi-Turn Conversation

```python
session = await agent.create_session()

messages = [
    "I'm planning a birthday party for 20 people",
    "It's for a 5-year-old who loves dinosaurs",
    "What decorations do you suggest?",
    "What about the cake?",
]

for msg in messages:
    response = await agent.run(msg, session=session)
    print(f"User: {msg}")
    print(f"Agent: {response}\n")
# Each response builds on all previous context
```

### Store Custom State

```python
session = await agent.create_session()

# Store arbitrary data
session.state["user_id"] = "user-123"
session.state["preferences"] = {
    "language": "en",
    "timezone": "US/Pacific",
    "dietary": ["vegetarian"],
}
session.state["conversation_topic"] = "party planning"

# Access in context providers
```

### Retrieve Existing Session

```python
# Get session by service ID
session = await agent.get_session(service_session_id="abc-123")

# Continue conversation
response = await agent.run("Where were we?", session=session)
```

---

## Session Persistence

### Serialize / Deserialize

```python
# Save session state
session_dict = session.to_dict()

# Store to database, file, Redis, etc.
import json
with open("session_backup.json", "w") as f:
    json.dump(session_dict, f)

# Later: restore session
with open("session_backup.json", "r") as f:
    data = json.load(f)

restored_session = AgentSession.from_dict(data)
response = await agent.run("Continue our conversation", session=restored_session)
```

### Database Persistence Pattern

```python
import json
from your_db import database

async def save_session(user_id: str, session: AgentSession):
    data = json.dumps(session.to_dict())
    await database.upsert("sessions", {
        "user_id": user_id,
        "session_data": data,
        "updated_at": datetime.utcnow(),
    })

async def load_session(user_id: str) -> AgentSession:
    row = await database.get("sessions", user_id=user_id)
    if row:
        return AgentSession.from_dict(json.loads(row["session_data"]))
    return await agent.create_session()
```

---

## Context Providers

Context providers inject dynamic information into the agent's context on every turn. They run before each LLM call and their output is prepended to the conversation.

### How Context Providers Work

```
User Message
  → Context Provider 1 generates context string
  → Context Provider 2 generates context string
  → All context + instructions + messages → LLM
  → Response
```

### Built-in: InMemoryHistoryProvider

Stores and loads conversation history:

```python
from agent_framework import InMemoryHistoryProvider

memory = InMemoryHistoryProvider(
    "conversation_memory",
    load_messages=True,          # Load history into context
    store_context_messages=True, # Also store context provider output
)

audit = InMemoryHistoryProvider(
    "audit_log",
    load_messages=False,         # Don't load into context
    store_context_messages=True, # But do record everything
)

agent = client.as_agent(
    name="MemoryAgent",
    instructions="You remember previous conversations.",
    context_providers=[memory, audit],
)
```

---

## Memory Providers

### Provider Comparison

| Provider | Persistence | Performance | Use Case |
|----------|:-----------:|:-----------:|----------|
| **InMemoryHistoryProvider** | Session only | Fastest | Development, testing |
| **RedisContextProvider** | Redis store | Fast | Distributed, multi-server |
| **Mem0ContextProvider** | Mem0 cloud | Medium | External memory service |
| **DurableAgentSession** | Azure Durable | Reliable | Long-running workflows |

### Redis Provider

```python
from agent_framework.memory import RedisContextProvider

redis_memory = RedisContextProvider(
    redis_url="redis://localhost:6379",
    db=0,
    ttl=86400,  # 24 hours
)

agent = client.as_agent(
    name="PersistentAgent",
    context_providers=[redis_memory],
)
```

### Mem0 Provider

```python
from agent_framework.memory import Mem0ContextProvider

mem0 = Mem0ContextProvider(
    api_key=os.environ["MEM0_API_KEY"],
    org_id="your-org-id",
)

agent = client.as_agent(
    name="LongTermMemoryAgent",
    context_providers=[mem0],
)
```

### Sliding Window History

Keeps only the last N messages to manage token costs:

```python
from agent_framework.memory import SlidingWindowHistoryProvider

window = SlidingWindowHistoryProvider(
    max_window_size=20,  # Keep last 20 messages
    base_provider=InMemoryHistoryProvider("history"),
)

agent = client.as_agent(
    name="EfficientAgent",
    context_providers=[window],
)
```

---

## Custom Context Provider

Implement `BaseContextProvider` for custom memory and context injection:

### Basic Custom Provider

```python
from agent_framework import BaseContextProvider, AgentSession

class UserProfileProvider(BaseContextProvider):
    async def get_context(self, session: AgentSession, **kwargs) -> str:
        user_id = session.state.get("user_id")
        if not user_id:
            return ""

        # Fetch from database
        profile = await fetch_user_profile(user_id)
        return f"""User Profile:
- Name: {profile.name}
- Role: {profile.role}
- Preferences: {profile.preferences}
- Recent activity: {profile.recent_activity}"""
```

### RAG Context Provider

```python
class RAGContextProvider(BaseContextProvider):
    def __init__(self, vector_store):
        self.vector_store = vector_store

    async def get_context(self, session: AgentSession, **kwargs) -> str:
        # Get the latest user message
        last_message = session.messages[-1].content if session.messages else ""

        # Search vector store
        results = await self.vector_store.search(last_message, top_k=5)

        if not results:
            return ""

        context_parts = ["Relevant documents:"]
        for i, result in enumerate(results, 1):
            context_parts.append(f"{i}. {result.text} (score: {result.score:.2f})")

        return "\n".join(context_parts)
```

### Time-Aware Context Provider

```python
class BusinessHoursProvider(BaseContextProvider):
    async def get_context(self, session: AgentSession, **kwargs) -> str:
        from datetime import datetime
        now = datetime.now()
        is_business = 9 <= now.hour < 17 and now.weekday() < 5

        return f"""Current time: {now.strftime('%Y-%m-%d %H:%M %Z')}
Business hours: {'Yes - full support available' if is_business else 'No - limited support'}"""
```

### Lifecycle Hooks

```python
class AnalyticsProvider(BaseContextProvider):
    async def get_context(self, session, **kwargs) -> str:
        return ""

    async def on_session_created(self, session: AgentSession) -> None:
        """Called when session is created"""
        await analytics.track("session_started", session.id)

    async def on_session_closed(self, session: AgentSession) -> None:
        """Called when session is closed"""
        msg_count = len(session.messages)
        await analytics.track("session_ended", session.id, messages=msg_count)
```

---

## Production Patterns

### Pattern: Session per User

```python
class UserSessionManager:
    def __init__(self, agent, db):
        self.agent = agent
        self.db = db

    async def chat(self, user_id: str, message: str) -> str:
        # Load or create session
        session_data = await self.db.get(f"session:{user_id}")
        if session_data:
            session = AgentSession.from_dict(json.loads(session_data))
        else:
            session = await self.agent.create_session()
            session.state["user_id"] = user_id

        # Run agent
        response = await self.agent.run(message, session=session)

        # Save session
        await self.db.set(f"session:{user_id}", json.dumps(session.to_dict()))

        return response
```

### Pattern: Session Expiration

```python
async def get_or_create_session(user_id: str, max_age_hours: int = 24):
    session_data = await redis.get(f"session:{user_id}")

    if session_data:
        data = json.loads(session_data)
        created = datetime.fromisoformat(data.get("created_at", ""))
        age = datetime.utcnow() - created

        if age.total_seconds() < max_age_hours * 3600:
            return AgentSession.from_dict(data)

    # Expired or doesn't exist — create new
    session = await agent.create_session()
    session.state["created_at"] = datetime.utcnow().isoformat()
    return session
```

### Pattern: Multi-Agent Shared Memory

```python
# Shared memory across multiple agents
shared_memory = RedisContextProvider(redis_url="redis://localhost:6379")

research_agent = client.as_agent(
    name="Researcher",
    context_providers=[shared_memory],
    tools=[search_web],
)

writer_agent = client.as_agent(
    name="Writer",
    context_providers=[shared_memory],
    tools=[write_document],
)

# Both agents share the same memory store
# Research findings are available to the writer
```
