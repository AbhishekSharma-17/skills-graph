# Agno Memory — Tools & Manager

## Contents
- [Memory Tools (Explicit Control)](#memory-tools-explicit-control)
- [MemoryManager (Custom Configuration)](#memorymanager-custom-configuration)
- [Retrieving Memories](#retrieving-memories)
- [Agents Sharing Memory](#agents-sharing-memory)

---

## Memory Tools (Explicit Control)

Give agents explicit tools for memory management without the automatic extraction overhead.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIResponses
from agno.tools.memory import MemoryTools

db = SqliteDb(db_file="tmp/memory.db")
memory_tools = MemoryTools(db=db)

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    tools=[memory_tools],
    markdown=True,
)

agent.print_response(
    "My name is John Doe and I like to hike. I'm planning to travel to Africa in December.",
    user_id="john_doe@example.com",
    stream=True,
)

agent.print_response(
    "What have you remembered about me?",
    stream=True,
    user_id="john_doe@example.com",
)
```

### Comparison

| Feature | Automatic | Memory Tools | Agentic |
|---------|-----------|-------------|---------|
| Token efficiency | High | Medium | Low |
| Agent control | None (auto) | Full (via tools) | Full (via decisions) |
| Real-time updates | No (batch at end) | Yes (on demand) | Yes (on demand) |
| Best for | Most apps | Custom workflows | Complex reasoning |

---

## MemoryManager (Custom Configuration)

Control which model processes memories and add custom rules for what gets stored.

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.models.openai import OpenAIResponses

db = SqliteDb(db_file="agent.db")

memory_manager = MemoryManager(
    db=db,
    model=OpenAIResponses(id="gpt-4o"),           # Separate model for memory ops
    additional_instructions="Don't store the user's real name. Say 'The User' instead.",
)

agent = Agent(
    db=db,
    memory_manager=memory_manager,
    update_memory_on_run=True,
)

agent.print_response("My name is John Doe and I like to play basketball on weekends.")
agent.print_response("What do I do on weekends?")
# Recalls hobby but not name (privacy rule applied)
```

### MemoryManager parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `db` | Database | Required — database connection |
| `model` | Model | LLM for memory operations (defaults to agent's model) |
| `additional_instructions` | str | Custom rules for memory capture |

Useful for privacy-sensitive applications (healthcare, legal, finance).

---

## Retrieving Memories

### Programmatic access

```python
memories = agent.get_user_memories(user_id="john_doe@example.com")

for m in memories:
    print(f"[{m.memory_id}] {m.memory}")
    print(f"  Topics: {m.topics}")
    print(f"  Updated: {m.updated_at}")
```

### Custom memory table

```python
from agno.db.postgres import PostgresDb

db = PostgresDb(
    db_url="postgresql://user:pass@localhost:5432/mydb",
    memory_table="my_custom_memories",  # Custom table name
)

agent = Agent(db=db, update_memory_on_run=True)
agent.print_response("I love sushi!", user_id="user_123")

memories = agent.get_user_memories(user_id="user_123")
```

### Context control

```python
# Default: memories included in agent context
agent = Agent(db=db, update_memory_on_run=True)

# Opt out: collect memories but don't auto-inject into context
agent = Agent(
    db=db,
    update_memory_on_run=True,
    add_memories_to_context=False,  # Keep context lean
)
```

Use `add_memories_to_context=False` when building analytics, keeping context small, or when the agent uses explicit search tools instead.

---

## Agents Sharing Memory

Connect multiple agents to the same database with the same `user_id` — they automatically share memories.

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.tools.websearch import WebSearchTools

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

chat_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    description="Helpful chat assistant",
    db=db,
    update_memory_on_run=True,
)

research_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    description="Research assistant",
    tools=[WebSearchTools()],
    db=db,
    update_memory_on_run=True,
)

user_id = "john_doe@example.com"

# Chat agent stores a memory
chat_agent.print_response(
    "My name is John Doe and I like hiking.",
    stream=True,
    user_id=user_id,
)

# Research agent can access the same memory
research_agent.print_response(
    "Search for hiking trails near me. Remember what I like!",
    stream=True,
    user_id=user_id,
)

# Both agents see all memories for this user
memories = research_agent.get_user_memories(user_id=user_id)
```

### Sharing memory AND history between agents

```python
from uuid import uuid4
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

db = SqliteDb(db_file="tmp/agent_sessions.db")

agent_1 = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You are really friendly and helpful.",
    db=db,
    add_history_to_context=True,
    update_memory_on_run=True,
)

agent_2 = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You are really grumpy and mean.",
    db=db,
    add_history_to_context=True,
    update_memory_on_run=True,
)

session_id = str(uuid4())
user_id = "john_doe@example.com"

# Agent 1 introduces user
agent_1.print_response("Hi! My name is John Doe.", session_id=session_id, user_id=user_id)

# Agent 2 recalls memory and history from shared session
agent_2.print_response("What is my name?", session_id=session_id, user_id=user_id)

# Agent 2 creates new memory
agent_2.print_response("I like to hike.", session_id=session_id, user_id=user_id)

# Agent 1 recalls memory created by Agent 2
agent_1.print_response("What are my hobbies?", session_id=session_id, user_id=user_id)
```

---

