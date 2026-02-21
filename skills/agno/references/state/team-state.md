# Team State

Teams share state across all members. The team's `session_state` is accessible to every member agent and team-level tool via `run_context.session_state`. State propagates through nested team structures.

## Shared State Across Members

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.team import Team
from agno.run import RunContext

# Member tools — access shared team state
def add_item(run_context: RunContext, item: str) -> str:
    """Add an item to the shopping list.

    Args:
        item (str): The item to add.
    """
    if item.lower() not in [i.lower() for i in run_context.session_state["shopping_list"]]:
        run_context.session_state["shopping_list"].append(item)
        return f"Added '{item}' to the shopping list"
    return f"'{item}' is already in the shopping list"

def remove_item(run_context: RunContext, item: str) -> str:
    """Remove an item from the shopping list.

    Args:
        item (str): The item to remove.
    """
    for i, list_item in enumerate(run_context.session_state["shopping_list"]):
        if list_item.lower() == item.lower():
            run_context.session_state["shopping_list"].pop(i)
            return f"Removed '{list_item}'"
    return f"'{item}' not found"

# Agent that manages the list
shopping_agent = Agent(
    name="Shopping List Agent",
    role="Manage the shopping list",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[add_item, remove_item],
)

# Team-level tools — also access shared state
def list_items(run_context: RunContext) -> str:
    """List all items in the shopping list."""
    items = run_context.session_state["shopping_list"]
    if not items:
        return "The shopping list is empty."
    return "Shopping list:\n" + "\n".join(f"- {item}" for item in items)

def add_chore(run_context: RunContext, chore: str) -> str:
    """Log a completed chore.

    Args:
        chore (str): The chore to log.
    """
    run_context.session_state.setdefault("chores", []).append(chore)
    return f"Logged chore: {chore}"

# Team with shared state
shopping_team = Team(
    name="Shopping Team",
    model=OpenAIResponses(id="gpt-5.2"),
    members=[shopping_agent],
    session_state={"shopping_list": [], "chores": []},
    tools=[list_items, add_chore],
    instructions=[
        "You manage a shopping list.",
        "Forward add/remove requests to the Shopping List Agent.",
        "Use list_items to show the current list.",
        "Log completed tasks using add_chore.",
    ],
)

shopping_team.print_response("Add milk, eggs, and bread", stream=True)
print(f"Shared state: {shopping_team.get_session_state()}")

shopping_team.print_response("I got the eggs", stream=True)
print(f"Shared state: {shopping_team.get_session_state()}")
```

Both the `shopping_agent` member and the team-level tools read and write the same `session_state`. When the member adds an item, the team sees it, and vice versa.

## State in Team Instructions

Same `{key}` syntax as agents:

```python
team = Team(
    members=[],
    session_state={"user_name": "John"},
    instructions="User's name is {user_name}",
    markdown=True,
)

team.print_response("What is my name?", stream=True)
```

## Setting State Per Run

```python
from agno.db.in_memory import InMemoryDb
from agno.models.openai import OpenAIResponses
from agno.team import Team

team = Team(
    db=InMemoryDb(),
    model=OpenAIResponses(id="gpt-5.2"),
    members=[],
    instructions="User's name is {user_name} and age is {age}",
)

# User 1
team.print_response(
    "What is my name?",
    session_id="user_1_session",
    user_id="user_1",
    session_state={"user_name": "John", "age": 30},
)

# Same session — state loaded from DB
team.print_response("How old am I?", session_id="user_1_session", user_id="user_1")

# User 2 — different state
team.print_response(
    "What is my name?",
    session_id="user_2_session",
    user_id="user_2",
    session_state={"user_name": "Jane", "age": 25},
)
```

## Sharing Member Interactions

Let team members see each other's responses:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.team import Team
from agno.db.sqlite import SqliteDb
from agno.tools.hackernews import HackerNewsTools

db = SqliteDb(db_file="tmp/agents.db")

web_agent = Agent(
    name="Web Research Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[HackerNewsTools()],
    instructions="Research the web for information.",
)

report_agent = Agent(
    name="Report Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    instructions="Write reports from research findings.",
)

team = Team(
    model=OpenAIResponses(id="gpt-5.2"),
    db=db,
    members=[web_agent, report_agent],
    share_member_interactions=True,     # Members see each other's work
    show_members_responses=True,        # Show member responses in output
    instructions=[
        "First, use the web research agent to find information.",
        "Then, use the report agent to write a report from the research.",
    ],
)

team.print_response("How are LEDs made?")
```

## State Propagation in Nested Teams

When teams contain other teams, state flows downward:

```python
inner_team = Team(
    name="Inner Team",
    members=[agent_a, agent_b],
    # No session_state — inherits from parent
)

outer_team = Team(
    name="Outer Team",
    members=[inner_team, agent_c],
    session_state={"project": "AI Research"},  # Flows to inner_team
)
```

All members of `inner_team` can access `run_context.session_state["project"]`.

## Team State Parameters

```python
team = Team(
    session_state={"key": "value"},             # Shared default state
    db=SqliteDb(db_file="team.db"),             # Persistence
    add_session_state_to_context=False,         # Show state in system prompt
    enable_agentic_state=False,                 # Built-in state update tool
    share_member_interactions=False,            # Members see each other's work
    show_members_responses=False,               # Display member responses
    add_team_history_to_members=False,          # Share team history with members
)
```
