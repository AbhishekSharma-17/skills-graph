# User Confirmation

Require explicit user approval before executing a tool. When the agent tries to call a tool marked with `requires_confirmation=True`, execution pauses and the user must approve or reject before the tool runs.

## How It Works

1. Tool is marked with `@tool(requires_confirmation=True)`
2. Agent decides to call the tool → execution pauses (`is_paused=True`)
3. `active_requirements` populated with confirmation requirements
4. User approves (`confirm()`) or rejects (`reject()`)
5. `continue_run()` resumes execution

---

## Basic Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools import tool

@tool(requires_confirmation=True)
def sensitive_operation(data: str) -> str:
    """Perform a sensitive operation that requires confirmation.

    Args:
        data (str): The data to process.
    """
    return f"Operation completed on: {data}"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[sensitive_operation],
)

run_response = agent.run("Perform sensitive operation on user data")

for requirement in run_response.active_requirements:
    if requirement.needs_confirmation:
        print(f"Tool: {requirement.tool.tool_name}({requirement.tool.tool_args})")
        confirmed = input("Confirm? (y/n): ").lower() == "y"
        if confirmed:
            requirement.confirm()
        else:
            requirement.reject()

response = agent.continue_run(
    run_id=run_response.run_id,
    requirements=run_response.requirements,
)
```

## Toolkit-Level Confirmation

Mark specific tools in a toolkit for confirmation using `requires_confirmation_tools`:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.yfinance import YFinanceTools
from rich.console import Console
from rich.prompt import Prompt

console = Console()

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[YFinanceTools(requires_confirmation_tools=["get_stock_price"])],
    markdown=True,
)

run_response = agent.run("Get the current stock price of Apple?")

for requirement in run_response.active_requirements:
    if requirement.needs_confirmation:
        tool = requirement.tool
        console.print(f"Tool [bold blue]{tool.tool_name}({tool.tool_args})[/] requires confirmation.")
        message = Prompt.ask("Do you want to continue?", choices=["y", "n"], default="y").strip().lower()

        if message == "n":
            requirement.reject()
        else:
            requirement.confirm()

response = agent.continue_run(
    run_id=run_response.run_id,
    requirements=run_response.requirements,
)
```

## Providing Rejection Feedback

When rejecting, provide a note so the agent can adapt:

```python
for requirement in run_response.active_requirements:
    if requirement.needs_confirmation:
        print(f"Tool: {requirement.tool.tool_name}({requirement.tool.tool_args})")
        confirmed = input("Confirm? (y/n): ").lower() == "y"

        if confirmed:
            requirement.confirm()
        else:
            requirement.reject()
            requirement.tool.confirmation_note = (
                "This operation was rejected because it targets the wrong resource. "
                "Please use the alternative method."
            )

response = agent.continue_run(
    run_id=run_response.run_id,
    requirements=run_response.requirements,
)
# Agent receives the rejection note and can adapt its approach
```

## Mixed Tools (Confirmed + Unconfirmed)

Tools without `requires_confirmation=True` execute normally. Only marked tools pause:

```python
from agno.tools import tool

def safe_operation() -> str:
    """This runs automatically without confirmation."""
    return "Safe operation completed"

@tool(requires_confirmation=True)
def risky_operation() -> str:
    """This requires user confirmation before running."""
    return "Risky operation completed"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[safe_operation, risky_operation],
)

run_response = agent.run("Perform both operations")

# safe_operation already executed
# risky_operation is paused waiting for confirmation
if run_response.is_paused:
    for req in run_response.active_requirements:
        if req.needs_confirmation:
            req.confirm()

    response = agent.continue_run(
        run_id=run_response.run_id,
        requirements=run_response.requirements,
    )
```

## Async Support

```python
import asyncio

async def main():
    run_response = await agent.arun("Perform sensitive operation")

    if run_response.is_paused:
        for req in run_response.active_requirements:
            if req.needs_confirmation:
                req.confirm()

        response = await agent.acontinue_run(
            run_id=run_response.run_id,
            requirements=run_response.requirements,
        )

asyncio.run(main())
```

## Streaming Support

```python
for run_event in agent.run("Perform sensitive operation", stream=True):
    if run_event.is_paused:
        for req in run_event.active_requirements:
            if req.needs_confirmation:
                req.confirm()

        for response in agent.continue_run(
            run_id=run_event.run_id,
            requirements=run_event.requirements,
            stream=True,
        ):
            print(response.content, end="")
    else:
        print(run_event.content, end="")
```

## With Chat History

Combine confirmation with persistent sessions:

```python
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[sensitive_operation],
    db=SqliteDb(db_file="tmp/agent.db"),
    add_history_to_context=True,
    num_history_runs=3,
)

run_response = agent.run("Delete record 42", session_id="admin_session")
# Handle confirmation...
response = agent.continue_run(
    run_id=run_response.run_id,
    requirements=run_response.requirements,
)
```

## Requirement API

```python
requirement.needs_confirmation      # bool — True for confirmation requirements
requirement.tool.tool_name          # str — Name of the tool
requirement.tool.tool_args          # dict — Arguments agent wants to pass
requirement.confirm()               # Approve execution
requirement.reject()                # Reject execution
requirement.tool.confirmation_note  # str — Rejection feedback (optional)
```
