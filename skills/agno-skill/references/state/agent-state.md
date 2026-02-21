# Agent State

Agent state persists data across runs within a session. Tools access state via `run_context.session_state`, and the agent can display state in its instructions.

## Basic State with Tools

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
    """Remove an item from the shopping list by name.

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
    instructions="Current shopping list: {shopping_list}",
    markdown=True,
)

# Multiple runs — state persists across them
agent.print_response("Add milk, eggs, and bread", stream=True)
print(f"State: {agent.get_session_state()}")
# {'shopping_list': ['milk', 'eggs', 'bread']}

agent.print_response("I got bread", stream=True)
print(f"State: {agent.get_session_state()}")
# {'shopping_list': ['milk', 'eggs']}

agent.print_response("What's on my list?", stream=True)
```

## State in Instructions

Reference state keys in instructions with `{key}` syntax. Agno substitutes values at runtime — do NOT use Python f-strings:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    session_state={"user_name": "John", "preferences": {"theme": "dark"}},
    # {key} syntax — NOT f-string
    instructions="User's name is {user_name}. Preferences: {preferences}",
)

agent.print_response("What is my name?", stream=True)
# Agent responds: "Your name is John"
```

## RunContext — What's Available in Tools

The `run_context` parameter is auto-injected when declared in a tool function signature. The model never sees it as a parameter.

```python
from agno.run import RunContext

def my_tool(run_context: RunContext, query: str) -> str:
    """Do something with context.

    Args:
        query (str): The query to process.
    """
    # Read/write state
    run_context.session_state["last_query"] = query

    # Access metadata
    print(f"Run ID: {run_context.run_id}")
    print(f"Session ID: {run_context.session_id}")
    print(f"User ID: {run_context.user_id}")
    print(f"Dependencies: {run_context.dependencies}")
    print(f"Metadata: {run_context.metadata}")

    return f"Processed: {query}"
```

**RunContext attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | `str` | Unique run identifier |
| `session_id` | `str` | Session identifier |
| `user_id` | `Optional[str]` | User identifier |
| `session_state` | `Dict[str, Any]` | Persistent session state (read/write) |
| `dependencies` | `Dict[str, Any]` | Injected dependencies |
| `knowledge_filters` | `Dict[str, Any]` | Knowledge base filters |
| `metadata` | `Dict[str, Any]` | Run metadata |

## Accessing State via `session_state` Parameter

Some tools use a simpler signature where `session_state` is passed directly (older pattern, still supported):

```python
def add_item(session_state, item: str) -> str:
    """Add item to shopping list."""
    session_state["shopping_list"].append(item)
    return f"List: {session_state['shopping_list']}"
```

The `run_context` pattern is preferred because it provides access to more metadata.

## Setting State Per Run

Override state for specific runs:

```python
agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    instructions="User's name is {user_name} and age is {age}",
)

# First run — sets state for this session
agent.print_response(
    "What is my name?",
    session_id="user_1_session",
    user_id="user_1",
    session_state={"user_name": "John", "age": 30},
)

# Same session — state loaded from DB automatically
agent.print_response("How old am I?", session_id="user_1_session", user_id="user_1")
# Agent responds: "You are 30 years old"
```

## Reading State Programmatically

```python
# Get current session state
state = agent.get_session_state()
print(state)  # {'shopping_list': ['milk', 'eggs']}

# Get state for a specific session
state = agent.get_session_state(session_id="session_123")

# Update state outside of a run
agent.update_session_state(
    session_id="session_123",
    session_state_updates={"counter": 42},
)
```

## Agent State Parameters

```python
agent = Agent(
    session_state={"key": "value"},             # Default state for new sessions
    db=SqliteDb(db_file="agent.db"),            # Persistence backend
    add_session_state_to_context=False,         # Include state in system prompt
    enable_agentic_state=False,                 # Built-in state update tool
    overwrite_db_session_state=False,           # Replace vs merge state
)
```
