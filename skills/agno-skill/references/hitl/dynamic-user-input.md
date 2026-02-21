# Dynamic User Input

Let the **agent** decide what information to request from the user and when. Unlike static `user_input_fields`, the agent uses `UserControlFlowTools` with a `get_user_input()` tool to dynamically construct field requests during execution.

## How It Works

1. Agent is given `UserControlFlowTools()` alongside regular tools
2. When the agent needs user input, it calls `get_user_input()` with field definitions
3. Execution pauses (`is_paused=True`)
4. `user_input_schema` populated with agent-created `UserInputField` objects
5. User fills values
6. `continue_run()` resumes — agent may pause **again** for more info
7. **Use a `while` loop** to handle multiple rounds of input

---

## Key Difference from Static User Input

| Static (`requires_user_input=True`) | Dynamic (`UserControlFlowTools`) |
|--------------------------------------|----------------------------------|
| Fields predefined on the tool | Agent constructs fields at runtime |
| Always asks for the same fields | Fields vary based on conversation |
| Single pause-resume cycle | May pause multiple times |
| You control what's asked | Agent controls what's asked |

## Basic Example

```python
from typing import List
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.function import UserInputField
from agno.tools.toolkit import Toolkit
from agno.tools.user_control_flow import UserControlFlowTools
from agno.utils import pprint

class EmailTools(Toolkit):
    def __init__(self, *args, **kwargs):
        super().__init__(
            name="EmailTools",
            tools=[self.send_email, self.get_emails],
            *args,
            **kwargs,
        )

    def send_email(self, subject: str, body: str, to_address: str) -> str:
        """Send an email to the given address.

        Args:
            subject (str): The subject of the email.
            body (str): The body of the email.
            to_address (str): The address to send the email to.
        """
        return f"Sent email to {to_address} with subject {subject} and body {body}"

    def get_emails(self, date_from: str, date_to: str) -> list[dict[str, str]]:
        """Get all emails between the given dates.

        Args:
            date_from (str): The start date (YYYY-MM-DD).
            date_to (str): The end date (YYYY-MM-DD).
        """
        return [
            {"subject": "Hello", "body": "Hello, world!", "to_address": "test@test.com", "date": date_from},
            {"subject": "Update", "body": "Project update", "to_address": "john@doe.com", "date": date_to},
        ]

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[EmailTools(), UserControlFlowTools()],
    markdown=True,
)

run_response = agent.run("Send an email with the body 'What is the weather in Tokyo?'")

# CRITICAL: Use a while loop — agent may pause multiple times
while run_response.is_paused:
    for requirement in run_response.active_requirements:
        if requirement.needs_user_input:
            input_schema: List[UserInputField] = requirement.user_input_schema

            for field in input_schema:
                print(f"\nField: {field.name}")
                print(f"Description: {field.description}")
                print(f"Type: {field.field_type}")

                if field.value is None:
                    user_value = input(f"Please enter a value for {field.name}: ")
                else:
                    print(f"Value (from agent): {field.value}")
                    user_value = field.value

                field.value = user_value

    run_response = agent.continue_run(
        run_id=run_response.run_id,
        requirements=run_response.requirements,
    )

    if not run_response.is_paused:
        pprint.pprint_run_response(run_response)
        break
```

## How the Agent Constructs Fields

When the agent calls `get_user_input()`, it creates field definitions like:

```python
[
    {
        "field_name": "to_address",
        "field_type": "str",
        "field_description": "The email address to send to"
    },
    {
        "field_name": "subject",
        "field_type": "str",
        "field_description": "The subject line for the email"
    }
]
```

These become `UserInputField` objects in `requirement.user_input_schema`.

## The While Loop Pattern

**Critical:** Always use a `while` loop. The agent may pause multiple times as it gathers information step by step:

```python
run_response = agent.run("Send an email and schedule a meeting")

while run_response.is_paused:
    # Iteration 1: Agent might ask for email details
    # Iteration 2: Agent might ask for meeting details
    for requirement in run_response.active_requirements:
        if requirement.needs_user_input:
            for field in requirement.user_input_schema:
                if field.value is None:
                    field.value = input(f"Enter {field.name}: ")

    run_response = agent.continue_run(
        run_id=run_response.run_id,
        requirements=run_response.requirements,
    )
```

## Customizing UserControlFlowTools

```python
# Custom instructions for how agent should request input
custom_instructions = """
When you need user input:
1. Only request fields you absolutely need
2. Group related fields together
3. Provide clear, concise descriptions
4. Never request the same information twice
"""

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[
        EmailTools(),
        UserControlFlowTools(
            instructions=custom_instructions,
            add_instructions=True,
        ),
    ],
    markdown=True,
)
```

### Disabling get_user_input

```python
# Disable the dynamic input tool
UserControlFlowTools(enable_get_user_input=False)
```

## With Database Persistence

```python
from agno.db.sqlite import SqliteDb

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[EmailTools(), UserControlFlowTools()],
    db=SqliteDb(db_file="tmp/agentic_user_input.db"),
    markdown=True,
)
```

## Async Support

```python
import asyncio

async def main():
    run_response = await agent.arun("Send an email")

    while run_response.is_paused:
        for requirement in run_response.active_requirements:
            if requirement.needs_user_input:
                for field in requirement.user_input_schema:
                    if field.value is None:
                        field.value = input(f"Enter {field.name}: ")

        run_response = await agent.acontinue_run(
            run_id=run_response.run_id,
            requirements=run_response.requirements,
        )

asyncio.run(main())
```

## Streaming Support

```python
run_response = agent.run("Send an email", stream=True)

for run_event in run_response:
    if run_event.is_paused:
        for requirement in run_event.active_requirements:
            if requirement.needs_user_input:
                for field in requirement.user_input_schema:
                    if field.value is None:
                        field.value = input(f"Enter {field.name}: ")

        for continued_event in agent.continue_run(
            run_id=run_event.run_id,
            requirements=run_event.requirements,
            stream=True,
        ):
            print(continued_event.content, end="")
    else:
        print(run_event.content, end="")
```

## When to Use Dynamic vs Static

| Scenario | Use |
|----------|-----|
| Known fields that always need user input | Static: `@tool(requires_user_input=True, user_input_fields=[...])` |
| Interaction flow is unpredictable | Dynamic: `UserControlFlowTools()` |
| Conversational multi-step gathering | Dynamic |
| Simple form-like input | Static |
| Agent should decide what to ask | Dynamic |
| You want explicit control over what's asked | Static |
