# Workflow State

Workflow state coordinates data across all workflow steps — agents, teams, and custom functions all share the same `session_state`. This is how steps pass information to each other and maintain context through a pipeline.

## Basic Workflow State

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.db.sqlite import SqliteDb
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow
from agno.run import RunContext

db = SqliteDb(db_file="tmp/workflow.db")

# Tools that read/write workflow session state
def add_item(run_context: RunContext, item: str) -> str:
    """Add an item to the shopping list.

    Args:
        item (str): The item to add.
    """
    existing = [i.lower() for i in run_context.session_state["shopping_list"]]
    if item.lower() not in existing:
        run_context.session_state["shopping_list"].append(item)
        return f"Added '{item}'"
    return f"'{item}' already in list"

def remove_item(run_context: RunContext, item: str) -> str:
    """Remove an item from the shopping list.

    Args:
        item (str): The item to remove.
    """
    shopping_list = run_context.session_state["shopping_list"]
    for i, existing in enumerate(shopping_list):
        if existing.lower() == item.lower():
            shopping_list.pop(i)
            return f"Removed '{existing}'"
    return f"'{item}' not found"

def remove_all_items(run_context: RunContext) -> str:
    """Remove all items from the shopping list."""
    run_context.session_state["shopping_list"] = []
    return "Cleared all items"

def list_items(run_context: RunContext) -> str:
    """List all items in the shopping list."""
    items = run_context.session_state["shopping_list"]
    if not items:
        return "Shopping list is empty."
    return "Shopping list:\n" + "\n".join(f"- {item}" for item in items)

# Create agents with tools
shopping_assistant = Agent(
    name="Shopping Assistant",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[add_item, remove_item, list_items],
    instructions=[
        "You help manage a shopping list.",
        "Use the provided tools to add, remove, and list items.",
    ],
)

list_manager = Agent(
    name="List Manager",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[list_items, remove_all_items],
    instructions=[
        "You can view the current shopping list and clear it when needed.",
        "Always show the current list when asked.",
    ],
)

# Create workflow steps
manage_step = Step(
    name="manage_items",
    description="Help manage shopping list items (add/remove)",
    agent=shopping_assistant,
)

view_step = Step(
    name="view_list",
    description="View and manage the complete shopping list",
    agent=list_manager,
)

# Create workflow with shared session_state
shopping_workflow = Workflow(
    name="Shopping List Workflow",
    db=db,
    steps=[manage_step, view_step],
    session_state={"shopping_list": []},
)

# Run the workflow — state persists across steps
shopping_workflow.print_response(input="Add milk, bread, and eggs")
print("State:", shopping_workflow.get_session_state())
# {'shopping_list': ['milk', 'bread', 'eggs']}

shopping_workflow.print_response(
    input="Add apples and bananas, then show the complete list"
)
print("State:", shopping_workflow.get_session_state())

shopping_workflow.print_response(input="Remove bread and show what's left")
print("State:", shopping_workflow.get_session_state())

shopping_workflow.print_response(input="Clear the entire list")
print("Final state:", shopping_workflow.get_session_state())
# {'shopping_list': []}
```

## How Workflow State Flows

```
Workflow (session_state={"shopping_list": []})
│
├── Step 1: "manage_items" (shopping_assistant agent)
│   └── Tools access run_context.session_state → same dict
│
├── Step 2: "view_list" (list_manager agent)
│   └── Tools access run_context.session_state → same dict
│
└── State persists between steps and across runs
```

All steps in the workflow share the same `session_state` dict. When Step 1 adds an item, Step 2 sees it immediately.

## State with Mixed Step Types

Workflows can mix agents, teams, and plain functions — all share state:

```python
from agno.workflow.step import Step
from agno.run import RunContext

# Custom function step
def validate_list(run_context: RunContext, input: str) -> str:
    """Validate the shopping list has at least 3 items."""
    items = run_context.session_state.get("shopping_list", [])
    if len(items) < 3:
        return f"Only {len(items)} items — need at least 3."
    return f"List validated: {len(items)} items ready."

validate_step = Step(
    name="validate",
    description="Validate the shopping list",
    function=validate_list,  # Plain function, not an agent
)

workflow = Workflow(
    name="Validated Shopping",
    steps=[manage_step, validate_step, view_step],
    session_state={"shopping_list": []},
    db=db,
)
```

## State in Conditions and Routers

Workflow state is available in condition and router evaluators for branching logic:

```python
from agno.workflow.step import Step

def check_list_size(run_context: RunContext, input: str) -> bool:
    """Check if list has enough items to proceed."""
    return len(run_context.session_state.get("shopping_list", [])) >= 3

conditional_step = Step(
    name="check_size",
    description="Check if shopping list is ready",
    condition=check_list_size,
    agent=list_manager,
)
```

## Workflow State Parameters

```python
workflow = Workflow(
    session_state={"key": "value"},         # Shared state across all steps
    db=SqliteDb(db_file="workflow.db"),      # Persistence
)
```

State is persisted to the database at the workflow level and loaded for subsequent runs in the same session.
