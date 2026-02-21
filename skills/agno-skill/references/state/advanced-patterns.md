# Advanced State Patterns

## Multi-User State Isolation

Different users get completely isolated state, even with the same agent. State is keyed by `(user_id, session_id)`.

```python
import json
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb
from agno.run import RunContext

shopping_list = {}

def add_item(run_context: RunContext, item: str) -> str:
    """Add item to current user's shopping list.

    Args:
        item (str): The item to add.
    """
    uid = run_context.session_state["current_user_id"]
    sid = run_context.session_state["current_session_id"]
    shopping_list.setdefault(uid, {}).setdefault(sid, []).append(item)
    return f"Added '{item}'"

def get_list(run_context: RunContext) -> str:
    """Get current user's shopping list."""
    uid = run_context.session_state["current_user_id"]
    sid = run_context.session_state["current_session_id"]
    items = shopping_list.get(uid, {}).get(sid, [])
    return json.dumps(items) if items else "Empty list"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/data.db"),
    tools=[add_item, get_list],
    instructions=[
        "Current User ID: {current_user_id}",
        "Current Session ID: {current_session_id}",
    ],
    markdown=True,
)

# User 1 — isolated list
agent.print_response(
    "Add milk and eggs",
    user_id="john_doe",
    session_id="user_1_session",
)

# User 2 — separate list
agent.print_response(
    "Add tacos",
    user_id="mark_smith",
    session_id="user_2_session",
)
```

### Built-in State Variables

Agno automatically populates these keys in `session_state`:

| Variable | Description |
|----------|-------------|
| `current_user_id` | The `user_id` for the current run |
| `current_session_id` | The `session_id` for the current run |

These are available in `{key}` template syntax in instructions and via `run_context.session_state`.

## Overwrite vs Merge

**Default behavior (merge):** When a run provides `session_state`, it merges with the existing DB state. Existing keys are updated, new keys are added, missing keys remain.

**Overwrite behavior:** Completely replaces DB state with the new `session_state`.

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    session_state={},
    add_session_state_to_context=True,
    overwrite_db_session_state=True,     # Replace instead of merge
)

# First run
agent.print_response(
    "What's in state?",
    session_state={"shopping_list": ["Potatoes"]},
)
print(agent.get_session_state())
# {'shopping_list': ['Potatoes']}

# Second run — completely overwrites
agent.print_response(
    "What's in state now?",
    session_state={"secret_number": 43},
)
print(agent.get_session_state())
# {'secret_number': 43}  — shopping_list is gone
```

**When to overwrite:**
- Resetting state for a user
- Loading a completely new context
- Session "reset" functionality

**When to merge (default):**
- Incrementally building up state
- Multiple tools updating different keys
- Normal session progression

## Dynamic State with Tool Hooks

Use tool hooks to intercept tool calls and manage state dynamically:

```python
import json
from typing import Any, Callable, Dict
from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.openai import OpenAIResponses
from agno.tools import Toolkit
from agno.run import RunContext

class CustomerDBTools(Toolkit):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register(self.process_customer_request)

    def process_customer_request(
        self, agent: Agent, customer_id: str, action: str = "retrieve", name: str = ""
    ):
        """Process a customer request.

        Args:
            customer_id (str): The customer ID.
            action (str): Action to perform (create/retrieve).
            name (str): Customer name (for create).
        """
        return "Handled by hook"

def customer_hook(
    run_context: RunContext,
    function_name: str,
    function_call: Callable,
    arguments: Dict[str, Any],
):
    """Hook that manages customer state dynamically."""
    action = arguments.get("action", "retrieve")
    cust_id = arguments.get("customer_id")
    name = arguments.get("name", "")

    profiles = run_context.session_state.setdefault("customer_profiles", {})

    if action == "create":
        profiles[cust_id] = {"name": name}
        return f"Created customer {cust_id}: {name}"

    if action == "retrieve":
        profile = profiles.get(cust_id)
        if profile:
            return f"Customer {cust_id}: {json.dumps(profile)}"
        return f"Customer '{cust_id}' not found"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[CustomerDBTools()],
    tool_hooks=[customer_hook],
    session_state={"customer_profiles": {"123": {"name": "Jane Doe"}}},
    instructions="Profiles: {customer_profiles}",
    db=InMemoryDb(),
)

agent.print_response("Create customer 789 named Tom, then retrieve their profile")
```

## Cross-Session State Search

Search across previous sessions for the same user:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    user_id="user_1",
    db=SqliteDb(db_file="tmp/data.db"),
    add_history_to_context=True,
    num_history_runs=3,
    search_session_history=True,       # Search across sessions
    num_history_sessions=2,            # Limit to last 2 sessions
)

# Session 1
agent.print_response("Capital of France?", session_id="s1")
# Session 2
agent.print_response("Capital of Japan?", session_id="s2")
# Session 3 — can see sessions s1 and s2
agent.print_response("What did I ask in previous conversations?", session_id="s3")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search_session_history` | `bool` | `False` | Enable cross-session search |
| `num_history_sessions` | `int` | `None` | How many past sessions to search (keep low: 2-3) |

## State Priority Order

When state comes from multiple sources, Agno resolves in this order:

1. **`session_state` on run call** — highest priority (per-run override)
2. **Database state** — loaded from the session's stored state
3. **Default `session_state` on agent/team/workflow** — lowest priority (initial defaults)

With `overwrite_db_session_state=False` (default): run state merges with DB state.
With `overwrite_db_session_state=True`: run state replaces DB state entirely.
