# Agno Memory — Patterns & Best Practices

## Contents
- [Teams with Memory](#teams-with-memory)
- [Multi-User Multi-Session](#multi-user-multi-session)
- [Memory Optimization](#memory-optimization)
- [Best Practices](#best-practices)
- [Quick Decision Tree](#quick-decision-tree)

---

## Teams with Memory

Teams support the same memory patterns as agents.

### Automatic memory on a team

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.team import Team
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="team.db")

researcher = Agent(name="Researcher", model=OpenAIResponses(id="gpt-4o"), role="Research specialist")
writer = Agent(name="Writer", model=OpenAIResponses(id="gpt-4o"), role="Content writer")

team = Team(
    name="Content Team",
    model=OpenAIResponses(id="gpt-4o"),
    members=[researcher, writer],
    db=db,
    update_memory_on_run=True,
)

team.print_response("Hi! My name is John Doe.", user_id="john@example.com")
team.print_response("What is my name?", user_id="john@example.com")
```

### Agentic memory on a team

```python
team = Team(
    model=OpenAIResponses(id="gpt-4o"),
    members=[researcher, writer],
    db=db,
    enable_agentic_memory=True,
)

team.print_response(
    "My name is John Doe and I like hiking.",
    stream=True,
    user_id="john@example.com",
)

team.print_response("What are my hobbies?", stream=True, user_id="john@example.com")
```

### Team with custom MemoryManager

```python
from agno.memory import MemoryManager

memory_manager = MemoryManager(
    model=OpenAIResponses(id="gpt-4o"),
    additional_instructions="Only store professional preferences, not personal ones.",
)

team = Team(
    model=OpenAIResponses(id="gpt-4o"),
    members=[researcher, writer],
    db=db,
    memory_manager=memory_manager,
    update_memory_on_run=True,
)
```

---

## Multi-User Multi-Session

Isolate memories per user, conversations per session.

```python
import asyncio
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    update_memory_on_run=True,
)

async def run():
    # User 1, Session 1
    await agent.aprint_response(
        "My name is Mark and I like anime.",
        user_id="user_1@example.com",
        session_id="user1_session1",
    )

    # User 1, Session 2 — memory persists across sessions
    await agent.aprint_response(
        "What do I like?",
        user_id="user_1@example.com",
        session_id="user1_session2",
    )

    # User 2 — isolated memories
    await agent.aprint_response(
        "My name is Jane and I like cooking.",
        user_id="user_2@example.com",
        session_id="user2_session1",
    )

asyncio.run(run())

# Each user has separate memories
user1_memories = agent.get_user_memories(user_id="user_1@example.com")
user2_memories = agent.get_user_memories(user_id="user_2@example.com")
```

---

## Memory Optimization

As users accumulate 50+ memories, token costs grow because all memories load into context. Use optimization to consolidate.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses
from agno.memory.strategies.types import MemoryOptimizationStrategyType
from agno.memory import SummarizeStrategy

db = SqliteDb(db_file="tmp/memory_optimize.db")
user_id = "power_user"

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    db=db,
    update_memory_on_run=True,
)

# After many conversations, user accumulates lots of memories...
# Check memory count
memories_before = agent.get_user_memories(user_id=user_id)
print(f"Memory count: {len(memories_before)}")

# Measure token usage
strategy = SummarizeStrategy()
tokens_before = strategy.count_tokens(memories_before)
print(f"Token count: {tokens_before}")

# Optimize — combines memories into fewer, denser records
memory_manager = agent.memory_manager
memory_manager.optimize_memories(
    user_id=user_id,
    strategy=MemoryOptimizationStrategyType.SUMMARIZE,
    apply=True,  # Apply changes to database
)

# Check improvement
memories_after = agent.get_user_memories(user_id=user_id)
tokens_after = strategy.count_tokens(memories_after)
reduction = ((tokens_before - tokens_after) / tokens_before) * 100
print(f"Reduced: {reduction:.1f}% ({tokens_before - tokens_after} tokens saved)")
```

**When to optimize:**
- Users with 50+ memories
- Before high-cost operations
- Periodic maintenance for long-running applications
- Can achieve 50-80% token reduction

---

## Best Practices

### 1. Always pass user_id

```python
# Bad — all users share a default bucket
agent.print_response("I love pizza")

# Good — isolated per user
agent.print_response("I love pizza", user_id="user_123")
```

### 2. Default to automatic memory

Unless you specifically need real-time memory control, use `update_memory_on_run=True`. It's 8x more efficient.

### 3. Use a cheaper model for memory operations

```python
from agno.memory import MemoryManager

memory_manager = MemoryManager(
    db=db,
    model=OpenAIResponses(id="gpt-4o-mini"),  # Cheap model for memory
)

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),  # Expensive model for conversation
    db=db,
    memory_manager=memory_manager,
    enable_agentic_memory=True,
)
```

Can reduce memory-related costs by up to 98%.

### 4. Guide memory behavior with instructions

```python
agent = Agent(
    db=db,
    enable_agentic_memory=True,
    instructions=[
        "Only update memories when users share significant new information.",
        "Don't create memories for casual conversation or temporary states.",
        "Batch multiple memory updates together when possible.",
    ],
)
```

### 5. Set tool call limits for agentic memory

```python
agent = Agent(
    db=db,
    enable_agentic_memory=True,
    tool_call_limit=5,  # Prevents excessive memory operations
)
```

### 6. Implement memory pruning for long-running apps

```python
from datetime import datetime, timedelta

def prune_old_memories(agent, user_id, days=90):
    """Remove memories older than N days."""
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp())
    memories = agent.get_user_memories(user_id=user_id)
    for m in memories:
        if m.updated_at and m.updated_at < cutoff:
            # Delete via database directly
            pass  # Implementation depends on db backend
```

### 7. Monitor memory growth

```python
memories = agent.get_user_memories(user_id="user_123")
print(f"User has {len(memories)} memories")

if len(memories) > 500:
    print("Warning: Consider optimizing or pruning memories")
```

### 8. Test with realistic data

5 memories behave very differently from 100+. Always test with realistic memory counts before production.

### 9. Never double-enable

```python
# Bad — agentic silently overrides automatic
agent = Agent(db=db, update_memory_on_run=True, enable_agentic_memory=True)

# Good — choose one
agent = Agent(db=db, update_memory_on_run=True)       # Automatic
agent = Agent(db=db, enable_agentic_memory=True)       # Agentic
```

---

## Quick Decision Tree

| Question | Recommendation |
|----------|---------------|
| Cost-effective, predictable? | `update_memory_on_run=True` |
| Agent decides what to remember? | `enable_agentic_memory=True` |
| Don't auto-inject into context? | `add_memories_to_context=False` |
| 50+ memories accumulating? | Optimize with `SUMMARIZE` strategy |
| Multi-user system? | Always pass explicit `user_id` |
| Privacy requirements? | Custom `MemoryManager` with `additional_instructions` |
| Explicit control via tools? | Use `MemoryTools` |
| Multi-agent sharing? | Same database + same `user_id` |
