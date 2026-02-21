# Learning — Complete Examples

## 1. Minimal Learning Agent (SQLite)

One line to enable learning with user_profile + user_memory in Always mode:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    learning=True,
)

agent.print_response("My name is Sarah and I prefer email over phone calls.", user_id="sarah")
agent.print_response("What's the best way to reach me?", user_id="sarah")  # Uses memory
```

## 2. Agentic Learning (Agent Controls What to Save)

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb
from agno.learn import LearningMachine, LearningMode, UserProfileConfig, UserMemoryConfig

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    learning=LearningMachine(
        user_profile=UserProfileConfig(mode=LearningMode.AGENTIC),
        user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
    ),
)
```

In Agentic mode, the agent receives tools (`update_user_profile`, `save_user_memory`, etc.) and decides when/what to save rather than extracting automatically.

## 3. Full Production Setup (All 6 Stores)

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.postgres import PostgresDb
from agno.learn import (
    LearningMachine, LearningMode,
    UserProfileConfig, UserMemoryConfig, SessionContextConfig,
    EntityMemoryConfig, LearnedKnowledgeConfig, DecisionLogConfig,
)
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector, SearchType

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Knowledge base for learned_knowledge store
learnings_kb = Knowledge(
    vector_db=PgVector(
        table_name="agent_learnings",
        db_url=db_url,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        search_type=SearchType.hybrid,
    ),
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=PostgresDb(db_url=db_url),
    learning=LearningMachine(
        user_profile=UserProfileConfig(mode=LearningMode.ALWAYS),
        user_memory=UserMemoryConfig(mode=LearningMode.ALWAYS),
        session_context=SessionContextConfig(enable_planning=True),
        entity_memory=EntityMemoryConfig(namespace="global", mode=LearningMode.AGENTIC),
        learned_knowledge=LearnedKnowledgeConfig(namespace="global", mode=LearningMode.AGENTIC),
        decision_log=DecisionLogConfig(mode=LearningMode.AGENTIC),
        knowledge=learnings_kb,
    ),
)
```

## 4. Custom Profile + Entity Schemas

```python
from dataclasses import dataclass, field
from typing import Optional
from agno.learn.schemas import UserProfile, EntityMemory
from agno.learn import LearningMachine, UserProfileConfig, EntityMemoryConfig, LearningMode

@dataclass
class CustomerProfile(UserProfile):
    company: Optional[str] = field(default=None, metadata={"description": "Company name"})
    plan_tier: Optional[str] = field(default=None, metadata={"description": "Tier: free | pro | enterprise"})
    role: Optional[str] = field(default=None, metadata={"description": "Job title"})

@dataclass
class CompanyEntity(EntityMemory):
    industry: Optional[str] = field(default=None, metadata={"description": "Industry sector"})
    employee_count: Optional[int] = field(default=None, metadata={"description": "Number of employees"})

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    learning=LearningMachine(
        user_profile=UserProfileConfig(schema=CustomerProfile),
        entity_memory=EntityMemoryConfig(mode=LearningMode.AGENTIC),
    ),
)
```

## 5. Session Context with Planning

For long-running tasks where the agent needs to track goals and progress:

```python
from agno.learn import LearningMachine, SessionContextConfig

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    learning=LearningMachine(
        session_context=SessionContextConfig(enable_planning=True),
    ),
)

# Agent will track goals, plans, and progress across the session
agent.print_response("Help me design an API for user authentication", session_id="api_design")
agent.print_response("Now let's add rate limiting", session_id="api_design")  # Remembers context
```

## 6. Learned Knowledge with Knowledge Base

Agent discovers insights and stores them for reuse across all users:

```python
from agno.learn import LearningMachine, LearnedKnowledgeConfig, LearningMode
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector, SearchType

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

learnings_kb = Knowledge(
    vector_db=PgVector(
        table_name="agent_learnings",
        db_url=db_url,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        search_type=SearchType.hybrid,
    ),
)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=PostgresDb(db_url=db_url),
    learning=LearningMachine(
        learned_knowledge=LearnedKnowledgeConfig(
            namespace="global",
            mode=LearningMode.AGENTIC,
        ),
        knowledge=learnings_kb,
    ),
)

# Agent gets search_learnings + save_learning tools
# It can save insights like "Pagination works best with cursor-based approach for large datasets"
```

## 7. Gcode Pattern (Full Agent with Knowledge + Learning)

The canonical Agno example — a coding agent with knowledge, learning, and memory:

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.models.openai import OpenAIResponses
from agno.tools.coding import CodingTools
from agno.tools.reasoning import ReasoningTools

gcode = Agent(
    name="Gcode",
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="agno.db"),
    instructions=instructions,

    # Knowledge: searchable long-term memory
    knowledge=gcode_knowledge,
    search_knowledge=True,

    # Learning: agent extracts and stores learnings over time
    learning=LearningMachine(
        knowledge=gcode_learnings,
        learned_knowledge=LearnedKnowledgeConfig(
            mode=LearningMode.AGENTIC,
        ),
    ),

    # Tools
    tools=[CodingTools(base_dir=workspace, all=True), ReasoningTools()],

    # Memory: learn user preferences
    enable_agentic_memory=True,

    # Context: add last 10 runs
    add_history_to_context=True,
    num_history_runs=10,

    markdown=True,
)
```

## Accessing & Managing Stored Data

```python
lm = agent.get_learning_machine()

# Read all stores
profile = lm.user_profile_store.get(user_id="alice")
memories = lm.user_memory_store.get_memories(user_id="alice")
context = lm.session_context_store.get(session_id="my_session")
entities = lm.entity_memory_store.search(query="acme", entity_type="company")
learnings = lm.learned_knowledge_store.search(query="best practices")
decisions = lm.decision_log_store.search(agent_id="my-agent", days=7)

# Print formatted
lm.user_profile_store.print(user_id="alice")
lm.user_memory_store.print(user_id="alice")
lm.entity_memory_store.print(entity_id="acme_corp", entity_type="company")
lm.learned_knowledge_store.print(query="cloud costs")
lm.decision_log_store.print(agent_id="my-agent", limit=5)

# Record decision outcome
lm.decision_log_store.update_outcome(
    decision_id="dec_abc123",
    outcome="User was satisfied",
    outcome_quality="good",
)

# Maintenance
lm.curator.prune(user_id="alice", max_age_days=90)
lm.curator.deduplicate(user_id="alice")
```

## Mode Selection Guide

| Situation | Mode | Why |
|-----------|------|-----|
| Profile / preferences (always useful) | Always | Don't miss anything |
| Observations / notes | Always or Agentic | Always is simpler, Agentic is more selective |
| Session tracking | Always | Only mode supported |
| Entity knowledge graph | Agentic | Agent decides what's worth tracking |
| Cross-user insights | Agentic or Propose | High-value, worth being deliberate |
| Decision auditing | Agentic | Agent decides which decisions matter |

## Namespace Guide

| Namespace | Sharing Scope | Use Case |
|-----------|--------------|----------|
| `"global"` | Everyone (default) | Team-wide learnings |
| `"user"` | Only current user | Personal entities |
| Custom string | Shared within group | `"engineering"`, `"sales_west"` |
