# Agno Memory

Memory stores learned user facts (preferences, habits, personal info) that persist across sessions. It's distinct from chat history (chronological messages). Memory is semantic — the agent remembers *what it learned*, not *what was said*.

**Two modes:** Automatic (MemoryManager extracts facts after each run) vs Agentic (agent gets tools to CRUD memories itself). Don't enable both.

## Sub-References

| Sub-Reference | File | Read When |
|---------------|------|-----------|
| **Core Concepts** | `memory/core-concepts.md` | Understanding automatic vs agentic memory, memory data model, basic setup, classification, storage backends |
| **Tools & Manager** | `memory/tools-manager.md` | MemoryTools (explicit control), MemoryManager (custom configuration), retrieving memories, agents sharing memory |
| **Patterns & Best Practices** | `memory/patterns-best-practices.md` | Teams with memory, multi-user multi-session, memory optimization, best practices, quick decision tree |

## Agent Memory Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `update_memory_on_run` | `bool` | `False` | Automatically extract and store user facts after each run |
| `memory_manager` | `Optional[MemoryManager]` | `None` | Custom MemoryManager for fine-grained control over memory extraction |
| `add_memories_to_context` | `bool` | `True` | Include stored memories in the agent's system message context |

## MemoryManager Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | `Database` | Required | Database connection for storing memories |
| `model` | `Optional[Model]` | `None` | LLM for memory extraction operations (defaults to agent's model if not set) |
| `additional_instructions` | `Optional[str]` | `None` | Custom rules governing what gets stored (e.g., privacy filters, content policies) |

## MemoryTools Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | `Database` | Required | Database connection for storing memories |

MemoryTools provides explicit tools for agents: `save_user_memory`, `delete_user_memory`, `get_user_memories`.

## Quick Start

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

# Automatic memory — facts extracted after each run
agent = Agent(
    db=SqliteDb(db_file="agent.db"),
    update_memory_on_run=True,
)

agent.print_response("My name is Sarah and I prefer email.", user_id="sarah")
agent.print_response("How should you reach me?", user_id="sarah")  # Recalls preference
```

## Key Imports

```python
from agno.memory import MemoryManager
from agno.tools.memory import MemoryTools
```
