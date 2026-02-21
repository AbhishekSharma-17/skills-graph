# Agno Memory — Core Concepts

## Contents
- [Overview](#overview)
- [Memory Data Model](#memory-data-model)
- [Automatic Memory](#automatic-memory)
- [Agentic Memory](#agentic-memory)

## Overview

Memory stores learned user facts (preferences, habits, personal info) that persist across sessions. It's distinct from chat history, which stores messages chronologically. Memory is semantic — the agent remembers *what it learned*, not *what was said*.

**Use memory when:** you want agents to recall user preferences, personalize responses, or build long-term user profiles.

**Two approaches:**

| Approach | Parameter | How It Works | Token Cost | Best For |
|----------|-----------|-------------|-----------|----------|
| **Automatic** | `update_memory_on_run=True` | Single LLM call after each run extracts and stores memories | Low (8x cheaper) | Most applications |
| **Agentic** | `enable_agentic_memory=True` | Agent gets tools to create/update/delete memories in real-time | High | Complex reasoning, user-directed memory control |

**Never enable both** — if both are set, agentic takes precedence and automatic is silently ignored.

---

## Memory Data Model

Each memory record:

| Field | Type | Description |
|-------|------|-------------|
| `memory_id` | str | Unique identifier |
| `memory` | str | The memory content |
| `topics` | list | Topic tags for categorization |
| `input` | str | Input that generated it |
| `user_id` | str | User this belongs to |
| `agent_id` | str | Agent that created it |
| `team_id` | str | Team that created it (if applicable) |
| `updated_at` | int | Unix timestamp of last update |

Stored in the `agno_memories` table by default (customizable via `memory_table` on the database).

---

## Automatic Memory

Memories are extracted and stored after each agent run via a single LLM call. Most efficient approach.

### Basic setup

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="agent.db")

agent = Agent(
    db=db,
    update_memory_on_run=True,
)

agent.print_response(
    "My name is Sarah and I prefer email over phone calls.",
    user_id="sarah",
)
# Memory created: "User's name is Sarah. Prefers email over phone calls."

agent.print_response("What's the best way to reach me?", user_id="sarah")
# Agent recalls preference from memory
```

### With PostgreSQL

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.postgres import PostgresDb
from uuid import uuid4

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    db=db,
    update_memory_on_run=True,
)

session_id = str(uuid4())
user_id = "john_doe@example.com"

agent.print_response(
    "My name is John Doe and I like to hike in the mountains on weekends.",
    stream=True,
    user_id=user_id,
    session_id=session_id,
)

agent.print_response("What are my hobbies?", stream=True, user_id=user_id, session_id=session_id)

# Memory auto-updates when preferences change
agent.print_response(
    "I don't like hiking anymore, I play soccer instead.",
    stream=True,
    user_id=user_id,
    session_id=session_id,
)
```

### Why automatic is 8x more efficient

A 10-message conversation where the agent updates memory 7 times with 100 existing memories:

- **Automatic**: 1 LLM call at end → ~5,000 tokens
- **Agentic**: 7 nested LLM calls, each loading all 100 memories → ~40,000 tokens

---

## Agentic Memory

The agent gets built-in tools to create, update, and delete memories during the conversation. Agent decides in real-time what's worth remembering.

### Basic setup

```python
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIResponses

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    model=OpenAIResponses(id="gpt-4o"),
    db=db,
    enable_agentic_memory=True,
)

user_id = "john_doe@example.com"

agent.print_response(
    "My name is John Doe and I like to hike in the mountains on weekends.",
    stream=True,
    user_id=user_id,
)

agent.print_response("What are my hobbies?", stream=True, user_id=user_id)

# Agent can delete memories on request
agent.print_response("Remove all existing memories of me.", stream=True, user_id=user_id)

# Agent can update memories
agent.print_response("I don't paint anymore, I draw instead.", stream=True, user_id=user_id)
```

### When to use agentic

- User explicitly asks to forget something ("delete my address")
- Agent needs to reason about what's worth remembering
- Real-time memory updates during conversation matter
- Complex multi-step workflows where memory decisions are part of the logic

### The token trap

Each agentic memory operation triggers a nested LLM call that loads ALL existing user memories. Costs grow linearly with memory count. Mitigations below in Best Practices.

---

