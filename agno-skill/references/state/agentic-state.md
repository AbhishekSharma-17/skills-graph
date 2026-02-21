# Agentic State

Agentic state lets agents and teams automatically manage session state without writing custom tool functions. Agno provides a built-in state management tool that the model calls to update state directly.

## Agent Agentic State

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/agents.db")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    session_state={"shopping_list": []},
    add_session_state_to_context=True,   # Required: model must see current state
    enable_agentic_state=True,           # Adds built-in state update tool
)

agent.print_response("Add milk, eggs, and bread to the shopping list", stream=True)
print(f"State: {agent.get_session_state()}")
# {'shopping_list': ['milk', 'eggs', 'bread']}

agent.print_response("I picked up the eggs, now what's on my list?", stream=True)
print(f"State: {agent.get_session_state()}")
# {'shopping_list': ['milk', 'bread']}
```

**Requirements:**
- `add_session_state_to_context=True` — the model needs to see the current state to know what to update
- `enable_agentic_state=True` — injects the built-in state management tool

**When to use agentic state vs custom tools:**
- **Agentic state:** Simple key-value updates, rapid prototyping, straightforward state management
- **Custom tools:** Complex validation logic, business rules, external API calls, computed state

## Team Agentic State

Teams and their members can both manage shared state automatically:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb
from agno.team import Team

db = SqliteDb(db_file="tmp/agents.db")

shopping_agent = Agent(
    name="Shopping List Agent",
    role="Manage the shopping list",
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    add_session_state_to_context=True,   # Member sees shared state
    enable_agentic_state=True,           # Member can update shared state
)

team = Team(
    model=OpenAIResponses(id="gpt-5.2"),
    members=[shopping_agent],
    session_state={"shopping_list": []},
    db=db,
    add_session_state_to_context=True,   # Team sees shared state
    enable_agentic_state=True,           # Team can update shared state
    description="You are a team that manages a shopping list and chores",
    show_members_responses=True,
)

team.print_response("Add milk, eggs, and bread to the shopping list")
team.print_response("I picked up the eggs, now what's on my list?")
print(f"State: {team.get_session_state()}")
```

Both the team coordinator and the member agent can modify the same shared `session_state`. Changes propagate automatically.

## How It Works Under the Hood

When `enable_agentic_state=True`, Agno registers a tool that lets the model directly manipulate session state. The model sees the current state (via `add_session_state_to_context`) and uses the tool to add, remove, or update keys.

The model effectively does what your custom tools would do, but without you having to write the tool functions. The trade-off is less control over validation and business logic.

## Combining Agentic State with Custom Tools

You can use both — agentic state for simple updates and custom tools for complex operations:

```python
from agno.run import RunContext

def calculate_total(run_context: RunContext) -> str:
    """Calculate the total price of items in the shopping list."""
    items = run_context.session_state.get("shopping_list", [])
    prices = run_context.session_state.get("prices", {})
    total = sum(prices.get(item, 0) for item in items)
    run_context.session_state["total"] = total
    return f"Total: ${total:.2f}"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    db=SqliteDb(db_file="tmp/agents.db"),
    session_state={"shopping_list": [], "prices": {}, "total": 0},
    add_session_state_to_context=True,
    enable_agentic_state=True,       # For simple list updates
    tools=[calculate_total],          # For complex logic
)
```

The model uses the agentic state tool for simple add/remove operations and calls `calculate_total` when it needs to compute the total.
