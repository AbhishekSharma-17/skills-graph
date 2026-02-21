# Session State

> **Deep Dive Available:** For comprehensive state coverage including team state, workflow state, agentic state, multi-user isolation, and advanced patterns, read `references/state.md` (the dedicated State Management module).

Session state is persistent key-value data that survives across multiple runs within a session. Use it for shopping lists, user preferences, todo lists, counters — any data that tools need to read and write across interactions.

## How State Works

1. **Initialize** — Set default `session_state` when creating the agent
2. **Access** — Tools read/write state via `run_context.session_state`
3. **Persist** — Modifications automatically save to the database
4. **Reload** — Subsequent runs in the same session retrieve stored state

## Basic Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb
from agno.run import RunContext

def add_item(run_context: RunContext, item: str) -> str:
    """Add an item to the shopping list.

    Args:
        item (str): The item to add.
    """
    run_context.session_state["shopping_list"].append(item)
    return f"Added '{item}'. List: {run_context.session_state['shopping_list']}"

def remove_item(run_context: RunContext, item: str) -> str:
    """Remove an item from the shopping list.

    Args:
        item (str): The item to remove.
    """
    shopping_list = run_context.session_state["shopping_list"]
    for i, list_item in enumerate(shopping_list):
        if list_item.lower() == item.lower():
            shopping_list.pop(i)
            return f"Removed '{list_item}'. List: {shopping_list}"
    return f"'{item}' not found in the list"

def list_items(run_context: RunContext) -> str:
    """List all items in the shopping list."""
    items = run_context.session_state["shopping_list"]
    if not items:
        return "The shopping list is empty."
    return "Shopping list:\n" + "\n".join(f"- {item}" for item in items)

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/state.db"),
    session_state={"shopping_list": []},           # Default state
    tools=[add_item, remove_item, list_items],
    instructions="Current shopping list: {shopping_list}",  # State in prompt
    markdown=True,
)

agent.print_response("Add milk, eggs, and bread", stream=True)
print(f"State: {agent.get_session_state()}")
# {'shopping_list': ['milk', 'eggs', 'bread']}

agent.print_response("I got bread", stream=True)
print(f"State: {agent.get_session_state()}")
# {'shopping_list': ['milk', 'eggs']}
```

## Using State in Instructions

Reference state keys directly in the instructions string with `{key}` syntax (not f-strings — Agno substitutes at runtime):

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    session_state={"user_name": "John", "preferences": {"theme": "dark"}},
    instructions="User's name is {user_name}. Preferences: {preferences}",
)
```

## Agentic Session State

Let the agent automatically update state without custom tools — Agno provides a built-in state management tool:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    session_state={"shopping_list": []},
    add_session_state_to_context=True,   # Required: shows state to the model
    enable_agentic_state=True,           # Adds built-in state update tool
)

agent.print_response("Add milk, eggs, and bread to the shopping list", stream=True)
print(f"State: {agent.get_session_state()}")
# {'shopping_list': ['milk', 'eggs', 'bread']}
```

This is simpler than writing custom tools but gives less control over validation and business logic.

## Setting State Per Run

Pass different state for different users or sessions:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    instructions="User's name is {user_name} and age is {age}",
)

# User 1
agent.print_response(
    "What is my name?",
    session_id="user_1_session",
    user_id="user_1",
    session_state={"user_name": "John", "age": 30},
)

# Same session — state loaded from DB automatically
agent.print_response("How old am I?", session_id="user_1_session", user_id="user_1")

# User 2 — different state
agent.print_response(
    "What is my name?",
    session_id="user_2_session",
    user_id="user_2",
    session_state={"user_name": "Jane", "age": 25},
)
```

## Overwrite vs Merge

By default, state from a new run **merges** with existing DB state. To completely **replace** it:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    session_state={},
    add_session_state_to_context=True,
    overwrite_db_session_state=True,  # Replace instead of merge
)

# First run
agent.print_response(
    "What's in state?",
    session_state={"shopping_list": ["Potatoes"]},
)
print(agent.get_session_state())  # {'shopping_list': ['Potatoes']}

# Second run — completely overwrites
agent.print_response(
    "What's in state now?",
    session_state={"secret_number": 43},
)
print(agent.get_session_state())  # {'secret_number': 43}
# shopping_list is gone
```

## Programmatic State Updates

Update state outside of agent runs:

```python
agent.update_session_state(
    session_id="session_123",
    session_state_updates={"counter": 42, "status": "active"},
)
```

## RunContext Attributes

The `run_context` parameter gives tools full access to run metadata:

```python
from agno.run import RunContext

def my_tool(run_context: RunContext, param: str) -> str:
    """A tool that uses run context.

    Args:
        param (str): Input parameter.
    """
    print(f"Run ID: {run_context.run_id}")
    print(f"Session ID: {run_context.session_id}")
    print(f"User ID: {run_context.user_id}")
    print(f"State: {run_context.session_state}")
    print(f"Dependencies: {run_context.dependencies}")
    print(f"Metadata: {run_context.metadata}")
    return "Done"
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | `str` | Unique run identifier |
| `session_id` | `str` | Session identifier |
| `user_id` | `Optional[str]` | User identifier |
| `session_state` | `Dict[str, Any]` | Persistent session state (read/write) |
| `dependencies` | `Dict[str, Any]` | Injected dependencies |
| `knowledge_filters` | `Dict[str, Any]` | Knowledge base filters |
| `metadata` | `Dict[str, Any]` | Run metadata |

## Agent State Parameters

```python
agent = Agent(
    session_state={"key": "value"},             # Default state
    add_session_state_to_context=False,         # Show state in system prompt
    enable_agentic_state=False,                 # Built-in state update tool
    overwrite_db_session_state=False,           # Replace vs merge on load
)
```
