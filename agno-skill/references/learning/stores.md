# Learning Stores — Detailed Reference

## User Profile Store

Structured facts about users (name, role, preferences). Injected into system prompt automatically.

**Scope**: Per user | **Default Mode**: Always | **Supported Modes**: Always, Agentic

**Data Model**:
- `name`: Full name
- `preferred_name`: Preferred name
- Custom fields via schema extension (see `custom-schemas.md`)

**Config**:
```python
from agno.learn import UserProfileConfig, LearningMode

UserProfileConfig(
    schema=None,                   # Custom dataclass or None for defaults
    mode=LearningMode.ALWAYS,     # Always or Agentic
)
```

**Tools** (Agentic mode): `update_user_profile`

**Access**:
```python
lm = agent.get_learning_machine()
profile = lm.user_profile_store.get(user_id="alice@example.com")
lm.user_profile_store.print(user_id="alice@example.com")
```

---

## User Memory Store

Unstructured observations about users. Think of it as the agent's "notebook" — anything worth remembering that doesn't fit a structured field.

**Scope**: Per user | **Default Mode**: Always | **Supported Modes**: Always, Agentic

**Data Model**:
- `memory_id`: Unique identifier
- `memory`: The observation text
- `topics`: Extracted topic list
- `user_id`: User identifier
- `created_at`, `updated_at`: Timestamps

**Config**:
```python
from agno.learn import UserMemoryConfig, LearningMode

UserMemoryConfig(
    mode=LearningMode.ALWAYS,
)
```

**Tools** (Agentic mode): `save_user_memory`, `delete_user_memory`

**Access**:
```python
lm = agent.get_learning_machine()
memories = lm.user_memory_store.get_memories(user_id="alice@example.com")
lm.user_memory_store.print(user_id="alice@example.com")
```

**Maintenance**:
```python
lm.curator.prune(user_id="alice", max_age_days=90)    # Remove old memories
lm.curator.deduplicate(user_id="alice")                 # Remove duplicates
```

---

## Session Context Store

Tracks what's happening in the current session — summary, goals, plans, progress. Only supports Always mode (automatic).

**Scope**: Per session | **Default Mode**: Always | **Supported Modes**: Always only

**Two Operation Modes**:

1. **Summary Mode** (default): Captures essence of the conversation without planning
2. **Planning Mode**: Tracks goals, steps, and progress

**Data Model**:
- `session_id`: Session identifier
- `user_id`: User identifier
- `summary`: Session summary
- `goal`: Current goal (planning mode)
- `plan`: Step-by-step plan (planning mode)
- `progress`: Current progress (planning mode)
- `created_at`, `updated_at`: Timestamps

**Config**:
```python
from agno.learn import SessionContextConfig

# Summary mode
SessionContextConfig()

# Planning mode
SessionContextConfig(enable_planning=True)
```

**Access**:
```python
lm = agent.get_learning_machine()
context = lm.session_context_store.get(session_id="api_design")
lm.session_context_store.print(session_id="api_design")
```

---

## Entity Memory Store

Facts, events, and relationships about external entities (companies, people, projects). Think of it as a lightweight knowledge graph the agent builds over time.

**Scope**: Configurable | **Default Mode**: Always | **Supported Modes**: Always, Agentic

**Three Knowledge Types**:
- **Facts**: Timeless truths ("Acme uses Python")
- **Events**: Time-bound occurrences ("Acme raised Series A in 2024")
- **Relationships**: Entity connections ("Alice is CTO of Acme")

**Data Model**:
- `entity_id`: Unique entity identifier
- `entity_type`: Type (company, person, project, etc.)
- `name`: Entity name
- `description`: Entity description
- `properties`: Key-value metadata dict
- `facts`: List of facts
- `events`: List of events
- `relationships`: List of relationships

**Config**:
```python
from agno.learn import EntityMemoryConfig, LearningMode

EntityMemoryConfig(
    namespace="global",            # "global" | "user" | custom string
    mode=LearningMode.AGENTIC,
)
```

**Namespace Options**:
- `"global"`: Shared across all users (default)
- `"user"`: Isolated per user
- Custom string (e.g. `"sales_team"`, `"engineering"`): Shared within group

**Tools** (Agentic mode): `search_entities`, `create_entity`, `update_entity`, `add_fact`, `update_fact`, `delete_fact`, `add_event`, `add_relationship`

**Access**:
```python
lm = agent.get_learning_machine()
entities = lm.entity_memory_store.search(query="acme", entity_type="company", limit=10)
lm.entity_memory_store.print(entity_id="acme_corp", entity_type="company")
```

---

## Learned Knowledge Store

Insights that transfer across users — patterns, best practices, domain knowledge the agent discovers. Stored in a vector database for semantic search.

**Scope**: Configurable | **Default Mode**: Agentic | **Supported Modes**: Always, Agentic, Propose

**Prerequisites**: Requires a Knowledge base with a vector database.

```python
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector, SearchType

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="learnings",
        db_url=db_url,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        search_type=SearchType.hybrid,
    ),
)
```

**Data Model**:
- `title`: Learning title
- `learning`: The actual insight
- `context`: Context in which it was learned
- `tags`: Topic tags
- `namespace`: Sharing scope
- `user_id`: Who learned it
- `created_at`: Timestamp

**Config**:
```python
from agno.learn import LearnedKnowledgeConfig, LearningMode

LearnedKnowledgeConfig(
    namespace="global",            # "global" | "user" | custom string
    mode=LearningMode.AGENTIC,
)
```

**Tools**: `search_learnings`, `save_learning`

**Access**:
```python
lm = agent.get_learning_machine()
results = lm.learned_knowledge_store.search(query="cloud costs", limit=5)
lm.learned_knowledge_store.print(query="cloud costs")
```

---

## Decision Log Store

Records decisions the agent makes, with reasoning, alternatives, confidence, and outcome tracking. Useful for auditing and improving agent behavior.

**Scope**: Per agent | **Default Mode**: Agentic | **Supported Modes**: Always, Agentic

**Data Model**:
- `id`: Decision ID
- `decision`: What was decided
- `reasoning`: Why this was chosen
- `decision_type`: One of `tool_selection`, `response_style`, `clarification`, `escalation`, `approach`
- `context`: Situation context
- `alternatives`: Other options considered
- `confidence`: 0.0 to 1.0
- `outcome`: What actually happened (filled later)
- `outcome_quality`: `good` | `bad` | `neutral`
- `created_at`: Timestamp

**Config**:
```python
from agno.learn import DecisionLogConfig, LearningMode

DecisionLogConfig(
    mode=LearningMode.AGENTIC,
)
```

**Tools**: `log_decision`, `record_outcome`, `search_decisions`

**Access**:
```python
lm = agent.get_learning_machine()

# Search decisions
decisions = lm.decision_log_store.search(
    agent_id="my-agent",
    decision_type="tool_selection",
    days=7,
    limit=10,
)
lm.decision_log_store.print(agent_id="my-agent", limit=5)

# Record outcome for a decision
lm.decision_log_store.update_outcome(
    decision_id="dec_abc123",
    outcome="User was satisfied",
    outcome_quality="good",
)
```
