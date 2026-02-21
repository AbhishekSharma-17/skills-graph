# Agno Learning System

Learning Machines let agents learn and improve with every interaction. They extract, store, and recall knowledge across six specialized stores — each capturing a different type of information.

## Quick Start

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

# One line enables learning (user_profile + user_memory in Always mode)
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    learning=True,
)

agent.print_response("My name is Sarah and I prefer email over phone calls.", user_id="sarah")
agent.print_response("What's the best way to reach me?", user_id="sarah")  # Remembers!
```

## Core Imports

```python
from agno.learn import (
    LearningMachine,
    LearningMode,
    UserProfileConfig,
    UserMemoryConfig,
    SessionContextConfig,
    EntityMemoryConfig,
    LearnedKnowledgeConfig,
    DecisionLogConfig,
)
```

## Learning Modes

```python
from agno.learn import LearningMode

LearningMode.ALWAYS    # Automatic extraction after each response
LearningMode.AGENTIC   # Agent receives tools and decides what to save
LearningMode.PROPOSE   # Agent proposes, user confirms (only LearnedKnowledge)
```

## Six Learning Stores

| Store | Scope | Default Mode | Captures | Tools |
|-------|-------|-------------|----------|-------|
| **User Profile** | Per user | Always | Structured facts (name, role, preferences) | `update_user_profile` |
| **User Memory** | Per user | Always | Unstructured observations | `save_user_memory`, `delete_user_memory` |
| **Session Context** | Per session | Always | Goals, plans, progress | None (automatic) |
| **Entity Memory** | Configurable | Always | Facts, events, relationships about external things | `search_entities`, `create_entity`, `update_entity`, `add_fact`, `add_event`, `add_relationship` |
| **Learned Knowledge** | Configurable | Agentic | Insights that transfer across users | `search_learnings`, `save_learning` |
| **Decision Log** | Per agent | Agentic | Decisions with reasoning and outcomes | `log_decision`, `record_outcome`, `search_decisions` |

## Full Configuration

### LearningMachine Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_profile` | `Optional[UserProfileConfig]` | `None` | Config for user profile store — structured facts (name, role, preferences) |
| `user_memory` | `Optional[UserMemoryConfig]` | `None` | Config for user memory store — unstructured observations |
| `session_context` | `Optional[SessionContextConfig]` | `None` | Config for session context store — goals, plans, progress |
| `entity_memory` | `Optional[EntityMemoryConfig]` | `None` | Config for entity memory store — facts/events/relationships about external things |
| `learned_knowledge` | `Optional[LearnedKnowledgeConfig]` | `None` | Config for learned knowledge store — insights that transfer across users |
| `decision_log` | `Optional[DecisionLogConfig]` | `None` | Config for decision log store — decisions with reasoning and outcomes |
| `knowledge` | `Optional[Knowledge]` | `None` | Knowledge base instance — required for learned_knowledge store |

### Store Config Parameters

| Config Class | Parameter | Type | Default | Description |
|-------------|-----------|------|---------|-------------|
| `UserProfileConfig` | `schema` | `Optional[Type]` | `None` | Custom dataclass for profile fields (None = default schema) |
| `UserProfileConfig` | `mode` | `LearningMode` | `ALWAYS` | Extraction mode: `ALWAYS`, `AGENTIC`, or `PROPOSE` |
| `UserMemoryConfig` | `mode` | `LearningMode` | `ALWAYS` | Extraction mode |
| `SessionContextConfig` | `enable_planning` | `bool` | `False` | Track goals, plans, and progress |
| `EntityMemoryConfig` | `namespace` | `str` | `"global"` | Scope: `"global"`, `"user"`, or custom string |
| `EntityMemoryConfig` | `mode` | `LearningMode` | `ALWAYS` | Extraction mode |
| `LearnedKnowledgeConfig` | `namespace` | `str` | `"global"` | Scope: `"global"`, `"user"`, or custom string |
| `LearnedKnowledgeConfig` | `mode` | `LearningMode` | `AGENTIC` | Extraction mode |
| `DecisionLogConfig` | `mode` | `LearningMode` | `AGENTIC` | Extraction mode |

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.postgres import PostgresDb
from agno.learn import (
    LearningMachine, LearningMode,
    UserProfileConfig, UserMemoryConfig, SessionContextConfig,
    EntityMemoryConfig, LearnedKnowledgeConfig, DecisionLogConfig,
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai"),
    learning=LearningMachine(
        user_profile=UserProfileConfig(
            schema=None,
            mode=LearningMode.ALWAYS,
        ),
        user_memory=UserMemoryConfig(
            mode=LearningMode.ALWAYS,
        ),
        session_context=SessionContextConfig(
            enable_planning=True,
        ),
        entity_memory=EntityMemoryConfig(
            namespace="global",
            mode=LearningMode.AGENTIC,
        ),
        learned_knowledge=LearnedKnowledgeConfig(
            namespace="global",
            mode=LearningMode.AGENTIC,
        ),
        decision_log=DecisionLogConfig(
            mode=LearningMode.AGENTIC,
        ),
        knowledge=knowledge,
    ),
)
```

## Accessing Stores Programmatically

```python
lm = agent.get_learning_machine()

# User Profile
profile = lm.user_profile_store.get(user_id="alice")
lm.user_profile_store.print(user_id="alice")

# User Memory
memories = lm.user_memory_store.get_memories(user_id="alice")
lm.user_memory_store.print(user_id="alice")

# Session Context
context = lm.session_context_store.get(session_id="api_design")

# Entity Memory
entities = lm.entity_memory_store.search(query="acme", entity_type="company", limit=10)

# Learned Knowledge
results = lm.learned_knowledge_store.search(query="cloud costs", limit=5)

# Decision Log
decisions = lm.decision_log_store.search(agent_id="my-agent", decision_type="tool_selection", days=7)
lm.decision_log_store.update_outcome(decision_id="dec_abc", outcome="User satisfied", outcome_quality="good")
```

## Maintenance (Curator)

```python
lm = agent.get_learning_machine()
lm.curator.prune(user_id="alice", max_age_days=90)
lm.curator.deduplicate(user_id="alice")
```

## Sub-References

Read only what the task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **Stores** | `references/learning/stores.md` | Detailed store APIs — data models, fields, configuration, tools for each of the 6 stores |
| **Custom Schemas** | `references/learning/custom-schemas.md` | Extending store schemas with custom fields (UserProfile, EntityMemory, LearnedKnowledge) |
| **Examples** | `references/learning/examples.md` | Complete production examples, store access patterns, and integration with Knowledge |
