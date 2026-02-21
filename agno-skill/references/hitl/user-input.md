# User Input

Collect specific field values from users during execution. When the agent calls a tool marked with `requires_user_input=True`, execution pauses and the user must provide values for specified fields.

## How It Works

1. Tool marked with `@tool(requires_user_input=True)`
2. Optionally specify which fields need user input via `user_input_fields=[...]`
3. Agent calls tool → execution pauses (`is_paused=True`)
4. `user_input_schema` populated with `UserInputField` objects
5. Agent pre-fills fields it can determine; user fills the rest
6. `continue_run()` resumes with user-provided values

---

## UserInputField Class

```python
from agno.tools.function import UserInputField

class UserInputField:
    name: str                           # Field name
    field_type: Type                    # Required type (str, int, float, bool, list, dict)
    description: Optional[str] = None   # Description for the user
    value: Optional[Any] = None         # Value — pre-filled by agent or set by user
```

## Basic Example — Specific Fields

Use `user_input_fields` to specify which parameters need user input. The agent fills the rest from context:

```python
from typing import List
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools import tool
from agno.tools.function import UserInputField
from agno.utils import pprint

@tool(requires_user_input=True, user_input_fields=["to_address"])
def send_email(subject: str, body: str, to_address: str) -> str:
    """Send an email.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        to_address (str): The address to send the email to.
    """
    return f"Sent email to {to_address} with subject {subject} and body {body}"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[send_email],
    markdown=True,
)

run_response = agent.run(
    "Send an email with the subject 'Hello' and the body 'Hello, world!'"
)

for requirement in run_response.active_requirements:
    if requirement.needs_user_input:
        input_schema: List[UserInputField] = requirement.user_input_schema

        for field in input_schema:
            print(f"\nField: {field.name}")
            print(f"Description: {field.description}")
            print(f"Type: {field.field_type}")

            if field.value is None:
                # User needs to provide this value
                user_value = input(f"Please enter a value for {field.name}: ")
            else:
                # Agent pre-filled this value
                print(f"Value (from agent): {field.value}")
                user_value = field.value

            field.value = user_value

run_response = agent.continue_run(
    run_id=run_response.run_id,
    requirements=run_response.requirements,
)

pprint.pprint_run_response(run_response)
```

**What happens with `user_input_fields=["to_address"]`:**

- `subject` → Agent fills from prompt ("Hello")
- `body` → Agent fills from prompt ("Hello, world!")
- `to_address` → User must provide (field.value is None)

## All Fields — User Provides Everything

Omit `user_input_fields` to require user input for all parameters:

```python
@tool(requires_user_input=True)  # No user_input_fields → all fields need user input
def send_email(subject: str, body: str, to_address: str) -> str:
    """Send an email.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        to_address (str): The address to send the email to.
    """
    return f"Sent email to {to_address} with subject {subject} and body {body}"
```

## Handling Pre-Filled Values

Always check `field.value` before prompting — the agent may have already filled some fields:

```python
for requirement in run_response.active_requirements:
    if requirement.needs_user_input:
        for field in requirement.user_input_schema:
            print(f"\nField: {field.name} ({field.field_type.__name__}) -> {field.description}")

            if field.value is None:
                # Agent couldn't determine this — ask the user
                user_value = input(f"Please enter a value for {field.name}: ")
                field.value = user_value
            else:
                # Agent pre-filled this value
                print(f"Value provided by the agent: {field.value}")
                # Optionally let user override:
                # override = input(f"Agent suggests '{field.value}'. Accept? (y/n): ")
                # if override.lower() == "n":
                #     field.value = input("Enter your value: ")
```

## Async Support

```python
import asyncio

async def main():
    run_response = await agent.arun("Send an email with the subject 'Hello'")

    for requirement in run_response.active_requirements:
        if requirement.needs_user_input:
            for field in requirement.user_input_schema:
                if field.value is None:
                    field.value = input(f"Please enter {field.name}: ")

    response = await agent.acontinue_run(
        run_id=run_response.run_id,
        requirements=run_response.requirements,
    )

asyncio.run(main())
```

## Streaming Support

```python
for run_event in agent.run("Send an email", stream=True):
    if run_event.is_paused:
        for requirement in run_event.active_requirements:
            if requirement.needs_user_input:
                for field in requirement.user_input_schema:
                    if field.value is None:
                        field.value = input(f"Please enter {field.name}: ")

        for response in agent.continue_run(
            run_id=run_event.run_id,
            requirements=run_event.requirements,
            stream=True,
        ):
            print(response.content, end="")
    else:
        print(run_event.content, end="")
```

## Requirement API

```python
requirement.needs_user_input          # bool — True for user input requirements
requirement.user_input_schema         # List[UserInputField] — Fields to collect

# UserInputField
field.name                            # str — Parameter name
field.field_type                      # Type — str, int, float, bool, list, dict
field.description                     # Optional[str] — Help text
field.value                           # Optional[Any] — None if user must provide
```

## Key Constraint

`@tool(requires_user_input=True)` is mutually exclusive with `@tool(requires_confirmation=True)` and `@tool(external_execution=True)`. A single tool can only use one HITL pattern.
