# Dependency Injection

Dependencies allow you to inject external data and callable functions into agents and teams at runtime. This provides request-specific context (user IDs, order data, API responses) without hardcoding values into the agent configuration.


## Contents

- [Docs Hierarchy](#docs-hierarchy)
- [How Dependencies Work](#how-dependencies-work)
- [Parameters](#parameters)
- [For Agents](#for-agents)
- [For Teams](#for-teams)
- [When to Use Dependencies](#when-to-use-dependencies)
- [Dependencies vs State](#dependencies-vs-state)

## Docs Hierarchy

```
Dependency Injection
├── Overview (/dependencies/overview)
├── For Agents
│   ├── Overview (/dependencies/agent/overview)
│   └── Usage
│       ├── Add on Run (/dependencies/agent/add-dependencies-run)
│       ├── Add to Context (/dependencies/agent/add-dependencies-to-context)
│       └── Access in Tool (/dependencies/agent/access-dependencies-in-tool)
└── For Teams
    ├── Overview (/dependencies/team/overview)
    ├── Reference Dependencies (/dependencies/team/reference-dependencies)
    ├── Access Dependencies in Tool (/dependencies/team/access-dependencies-in-tool)
    └── Add on Run (/dependencies/team/add-dependencies-run)
```

## How Dependencies Work

1. **Define** — Pass dependencies as key-value pairs on Agent/Team or at `run()` time
2. **Resolve** — Agno resolves callable dependencies at runtime (functions are called, values are passed through)
3. **Inject into instructions** — Use `{dependency_name}` syntax in instructions (Agno substitutes at runtime, not f-strings)
4. **Inject into context** — When `add_dependencies_to_context=True`, resolved values are added to the user message
5. **Access in tools** — Tools access dependencies via `run_context.dependencies`

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dependencies` | `Dict[str, Any]` | `None` | Key-value pairs on Agent/Team constructor or `run()`/`print_response()` |
| `add_dependencies_to_context` | `bool` | `False` | Include resolved dependencies in user message as `<additional context>` |

---

## For Agents

### Static Dependencies on Agent

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    dependencies={"name": "John Doe"},
    instructions="You are a story writer. The current user is {name}.",
)

agent.print_response("Write a 5 second short story about {name}")
```

### Add Dependencies on Run

Pass different dependencies per request — ideal for multi-user apps:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    instructions="You are helping {user_name} (tier: {tier}).",
)

# User 1
agent.print_response(
    "What features do I have?",
    session_id="alice-session",
    dependencies={"user_name": "Alice", "tier": "premium"},
)

# User 2
agent.print_response(
    "What features do I have?",
    session_id="bob-session",
    dependencies={"user_name": "Bob", "tier": "free"},
)
```

### Add Dependencies to Context

When `add_dependencies_to_context=True`, the full dependencies dict is appended to the user message:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    name="order_support",
    model=OpenAIResponses(id="gpt-5.2"),
    add_dependencies_to_context=True,
)

response = agent.run(
    message="What's the status of my order?",
    dependencies={
        "order_id": "ORD-12345",
        "order_status": "shipped",
        "tracking_number": "1Z999AA1234567890",
        "estimated_delivery": "2025-12-18",
    },
)
```

**Resulting user message:**

```
What's the status of my order?

<additional context>
{"order_id": "ORD-12345", "order_status": "shipped", "tracking_number": "1Z999AA1234567890", "estimated_delivery": "2025-12-18"}
</additional context>
```

### Callable Dependencies (Dynamic)

Dependencies can be functions — Agno resolves them at runtime:

```python
import json
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

def get_user_profile() -> str:
    """Fetch and return the user profile."""
    user_profile = {
        "name": "John Doe",
        "experience_level": "senior",
    }
    return json.dumps(user_profile, indent=4)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    dependencies={"user_profile": get_user_profile},  # Callable — resolved at runtime
    add_dependencies_to_context=True,
    markdown=True,
)

agent.print_response(
    "Get the user profile and tell me about their experience level.",
    stream=True,
)
```

### Runtime Callable Dependencies

```python
from datetime import datetime
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

def get_current_context() -> dict:
    return {
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "PST",
        "day_of_week": datetime.now().strftime("%A"),
    }

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    markdown=True,
)

response = agent.run(
    "Please provide a personalized summary of today's priorities.",
    dependencies={"current_context": get_current_context},
    add_dependencies_to_context=True,
)
```

### Access Dependencies in Tools

Tools read dependencies via `run_context.dependencies`:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb
from agno.run import RunContext

def get_user_profile(run_context: RunContext) -> str:
    """Get the user profile for the current user."""
    user_profiles = run_context.dependencies["user_profiles"]
    profile = user_profiles.get(run_context.user_id, {})
    return f"Profile: {profile}"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    tools=[get_user_profile],
    dependencies={
        "user_profiles": {
            "user_1001": {"name": "John Doe", "experience_level": "senior"},
            "user_1002": {"name": "Jane Doe", "experience_level": "junior"},
        }
    },
)

agent.print_response(
    "Get the user profile for the current user.",
    user_id="user_1001",
    stream=True,
)
```

### RunContext Dependency Access

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_context.dependencies` | `Dict[str, Any]` | All resolved dependencies for this run |
| `run_context.run_id` | `str` | Current run ID |
| `run_context.session_id` | `str` | Current session ID |
| `run_context.user_id` | `Optional[str]` | User ID if provided |
| `run_context.session_state` | `Dict[str, Any]` | Persistent session state |
| `run_context.metadata` | `Dict[str, Any]` | Run metadata |

---

## For Teams

### Reference Dependencies in Team Instructions

```python
from datetime import datetime
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.team import Team

def get_user_profile() -> dict:
    return {
        "name": "John Doe",
        "preferences": {
            "communication_style": "professional",
            "topics_of_interest": ["AI/ML", "Software Engineering"],
            "experience_level": "senior",
        },
    }

agent1 = Agent(name="ProfileAnalyst", model=OpenAIResponses(id="gpt-5.2"))
agent2 = Agent(name="ContextAnalyst", model=OpenAIResponses(id="gpt-5.2"))

team = Team(
    name="PersonalizationTeam",
    model=OpenAIResponses(id="gpt-5.2"),
    members=[agent1, agent2],
    dependencies={"user_profile": get_user_profile},
    instructions=[
        "You are a personalization team.",
        "Here is the user profile: {user_profile}",
    ],
)

team.print_response("Provide personalized recommendations based on the profile.")
```

### Access Dependencies in Team Tools

Team member tools can access team-level dependencies via `run_context`:

```python
from agno.run import RunContext

def personalize_content(run_context: RunContext, topic: str) -> str:
    """Personalize content based on user profile."""
    profile = run_context.dependencies.get("user_profile", {})
    style = profile.get("preferences", {}).get("communication_style", "casual")
    return f"Content about {topic} in {style} style for {profile.get('name', 'user')}"
```

### Add Dependencies on Team Run

```python
team.print_response(
    "Provide recommendations",
    dependencies={
        "user_profile": get_user_profile,
        "session_context": {"current_page": "/dashboard", "referrer": "email"},
    },
)
```

---

## When to Use Dependencies

| Use Case | Approach |
|----------|----------|
| **User context** (name, ID, preferences) | Static deps on `run()` |
| **Request metadata** (order IDs, ticket numbers) | Static deps on `run()` |
| **External data** (API responses, DB lookups) | Callable deps (resolved at runtime) |
| **Multi-tenant apps** (per-user/per-org context) | Different deps per `run()` call |
| **Dynamic instructions** (template variables) | `{key}` syntax in `instructions` |
| **Tools needing external data** | Access via `run_context.dependencies` |
| **Team-wide context** | Team-level `dependencies` + `{key}` in team instructions |

## Dependencies vs State

| Feature | Dependencies | Session State |
|---------|-------------|---------------|
| Scope | Single run | Persists across runs |
| Source | External (passed in) | Internal (managed by agent) |
| Mutability | Read-only during run | Read/write via tools |
| Use case | Contextual data injection | Accumulated knowledge |
| Template syntax | `{key}` in instructions | `{key}` in instructions |
