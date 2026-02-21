# Culture (Experimental)

Enable agents to share universal knowledge, principles, and best practices that compound across all interactions.

**Status:** Experimental — subject to change. Available since v2.1.10.

## Culture vs Memory

| Aspect | Culture | Memory |
|--------|---------|--------|
| **Purpose** | "How we do things here" — universal principles | "What I know about you" — user-specific facts |
| **Scope** | All agents, all interactions | Per-user, per-session |
| **Example** | "Always provide actionable solutions with clear next steps" | "Sarah prefers email" |

## How Culture Works

1. Agent starts a task → loads relevant cultural knowledge from database
2. Applies cultural knowledge during reasoning and response generation
3. After interaction → reflects on what worked well
4. Updates or adds cultural knowledge for future agents

## Agent Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_culture_to_context` | `bool` | `False` | Agent reads cultural knowledge at start of runs |
| `update_cultural_knowledge` | `bool` | `False` | Agent auto-updates culture after each run |
| `enable_agentic_culture` | `bool` | `False` | Agent gets tools to manage culture during runs |

## Quick Start

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="agno.db")

agent = Agent(
    db=db,
    add_culture_to_context=True,     # Read culture
    update_cultural_knowledge=True,   # Update culture automatically
)

agent.print_response(
    "How do I set up a FastAPI service using Docker?",
    stream=True,
)
```

---

## Three Approaches to Culture Management

### 1. Automatic Culture (`update_cultural_knowledge=True`)

After each agent run, the system automatically reflects on the interaction and updates cultural knowledge. **Recommended for most production use cases.**

```python
agent = Agent(
    db=db,
    add_culture_to_context=True,
    update_cultural_knowledge=True,
)
```

### 2. Agentic Culture (`enable_agentic_culture=True`)

Agent gets built-in tools to manage culture during conversations (not just after). It decides when and what to add.

```python
agent = Agent(
    db=db,
    add_culture_to_context=True,
    enable_agentic_culture=True,
)
```

**Best for:** Complex workflows where the agent should actively decide what principles to establish or update during the task.

### 3. Manual Culture Management

Create cultural knowledge explicitly using `CultureManager` or `CulturalKnowledge` objects. Perfect for seeding organizational standards.

```python
from agno.culture.manager import CultureManager
from agno.db.schemas.culture import CulturalKnowledge
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude

db = SqliteDb(db_file="agno.db")

# Option A: Use CultureManager with a model to process principles
culture_manager = CultureManager(
    db=db,
    model=Claude(id="claude-sonnet-4-5"),
)

message = """
All technical guidance should follow 'Operational Thinking':
1. State the Objective — What outcome and why
2. Show the Procedure — Clear, reproducible steps
3. Surface Pitfalls — What usually fails
4. Define Validation — How to confirm it works
5. Close the Loop — Suggest next iterations
"""

culture_manager.create_cultural_knowledge(message=message)

# Option B: Manually add cultural knowledge without a model
response_format = CulturalKnowledge(
    name="Response Format Standard",
    summary="Keep responses concise, scannable, and runnable-first",
    categories=["communication", "ux"],
    content=(
        "- Lead with minimal runnable snippet\n"
        "- Use numbered steps for procedures\n"
        "- End with validation checklist"
    ),
    notes=["Derived from user feedback"],
)

culture_manager.add_cultural_knowledge(response_format)
```

---

## CulturalKnowledge Data Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier (auto-generated) |
| `name` | `str` | Name/title of the cultural knowledge |
| `content` | `str` | Main content of the principle/knowledge |
| `summary` | `str` | Brief summary |
| `categories` | `list` | Categories (e.g., `"communication"`, `"engineering"`) |
| `notes` | `list` | Additional notes or context |
| `metadata` | `dict` | Arbitrary metadata (source, version, etc.) |
| `input` | `str` | Original input that generated this knowledge |
| `created_at` | `int` | Timestamp when created (epoch seconds) |
| `updated_at` | `int` | Timestamp when last updated (epoch seconds) |
| `agent_id` | `str` | ID of the agent that created it |
| `team_id` | `str` | ID of the team associated with it |

## CultureManager Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | `Database` | Required | Database connection for storing cultural knowledge |
| `model` | `Optional[Model]` | `None` | LLM for processing and generating cultural knowledge (required for `create_cultural_knowledge()`) |

### CultureManager Methods

| Method | Description |
|--------|-------------|
| `create_cultural_knowledge(message)` | Process a message through the model to create structured cultural knowledge |
| `add_cultural_knowledge(knowledge)` | Add a `CulturalKnowledge` object directly (no model required) |
| `get_all_knowledge()` | Retrieve all stored cultural knowledge entries |

## Storage

Cultural knowledge stored in database — supports all Agno backends (Postgres, SQLite, MongoDB, etc.).

Default table: `agno_cultural_knowledge` (configurable):

```python
from agno.db.postgres import PostgresDb

db = PostgresDb(
    db_url="postgresql://user:password@localhost:5432/my_database",
    cultural_knowledge_table="my_culture_table",  # Custom table name
)

agent = Agent(
    db=db,
    add_culture_to_context=True,
    update_cultural_knowledge=True,
)
```

## Manual Culture Retrieval

```python
from agno.culture.manager import CultureManager
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="agno.db")
culture_manager = CultureManager(db=db)

# Get all cultural knowledge
all_knowledge = culture_manager.get_all_knowledge()

# Preview cultural knowledge (truncated for readability)
for knowledge in all_knowledge:
    print(knowledge.preview())
```

---

## Common Use Cases

### Technical Documentation Standards

```python
doc_standard = CulturalKnowledge(
    name="Documentation Standard",
    summary="All docs follow structure: Example → Explanation → Validation",
    categories=["documentation", "engineering"],
    content=(
        "1. Start with a minimal working example\n"
        "2. Explain key concepts and decisions\n"
        "3. Provide validation steps\n"
        "4. Link to related resources"
    ),
)
```

### Customer Communication Tone

```python
comm_standard = CulturalKnowledge(
    name="Customer Communication Tone",
    summary="Professional, empathetic, solution-focused",
    categories=["communication", "support"],
    content=(
        "- Acknowledge the customer's situation first\n"
        "- Provide clear, actionable steps\n"
        "- Avoid jargon unless necessary\n"
        "- Always offer next steps or alternatives"
    ),
)
```

### Code Review Principles

```python
code_review = CulturalKnowledge(
    name="Code Review Standards",
    summary="Focus on maintainability, security, and performance",
    categories=["engineering", "code-review"],
    content=(
        "- Check for security vulnerabilities first\n"
        "- Verify error handling is comprehensive\n"
        "- Ensure code is self-documenting\n"
        "- Suggest performance optimizations where relevant"
    ),
)
```

## Best Practices

- **Start with manual seeding** — define core organizational principles, communication standards, and best practices upfront
- **Use automatic updates in production** — let `update_cultural_knowledge=True` handle evolution naturally
- **Review periodically** — check accumulated cultural knowledge and refine as needed
- **Keep culture focused** — universal principles, not task-specific details
- **Combine with Memory** — Culture for "how we do things" and Memory for "what I know about you"

## Key Imports

```python
from agno.culture.manager import CultureManager
from agno.db.schemas.culture import CulturalKnowledge
```
