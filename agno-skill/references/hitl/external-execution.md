# External Tool Execution

Execute tools outside the agent's control for enhanced security and flexibility. When a tool is marked with `external_execution=True`, the agent never calls the function — **you** are responsible for executing it with your own logic, security checks, and environment.

## How It Works

1. Tool marked with `@tool(external_execution=True)`
2. Agent decides to call tool → execution pauses (`is_paused=True`)
3. `active_requirements` populated with external execution requirements
4. You receive `tool_name` and `tool_args` from the requirement
5. You execute the tool with your own logic and set `external_execution_result`
6. `continue_run()` feeds the result back to the agent

---

## Basic Example

```python
import subprocess
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools import tool
from agno.utils import pprint

@tool(external_execution=True)
def execute_shell_command(command: str) -> str:
    """Execute a shell command.

    Args:
        command (str): The shell command to execute.

    Returns:
        str: The output of the shell command.
    """
    return subprocess.check_output(command, shell=True).decode("utf-8")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[execute_shell_command],
    markdown=True,
)

run_response = agent.run("What files do I have in my current directory?")

for requirement in run_response.active_requirements:
    if requirement.is_external_tool_execution:
        tool_exec = requirement.tool_execution
        print(f"Executing {tool_exec.tool_name} with args {tool_exec.tool_args} externally")

        # Execute the tool yourself with your own security/environment
        result = execute_shell_command.entrypoint(**tool_exec.tool_args)

        # Set the result so agent can continue
        requirement.external_execution_result = result

run_response = agent.continue_run(
    run_id=run_response.run_id,
    requirements=run_response.requirements,
)

pprint.pprint_run_response(run_response)
```

## ToolExecution Object

```python
requirement.tool_execution.tool_name              # str — Name of the tool
requirement.tool_execution.tool_args              # Dict[str, Any] — Arguments from agent
requirement.tool_execution.external_execution_required  # bool — True
requirement.external_execution_result             # Any — Set this with your result
```

## Toolkit-Level External Execution

Mark specific tools in a toolkit for external execution using `external_execution_required_tools`:

```python
import subprocess
from agno.tools.toolkit import Toolkit

class ShellTools(Toolkit):
    def __init__(self, *args, **kwargs):
        super().__init__(
            tools=[self.list_dir, self.get_env],
            external_execution_required_tools=["list_dir"],  # Only list_dir is external
            *args,
            **kwargs,
        )

    def list_dir(self, directory: str) -> str:
        """Lists the contents of a directory.

        Args:
            directory (str): The directory to list.
        """
        return subprocess.check_output(f"ls {directory}", shell=True).decode("utf-8")

    def get_env(self, var_name: str) -> str:
        """Gets an environment variable.

        Args:
            var_name (str): The variable name.
        """
        import os
        return os.getenv(var_name, "Not found")

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[ShellTools()],
    markdown=True,
)

run_response = agent.run("What files are in my current directory and what's my PATH?")

# get_env runs normally inside the agent
# list_dir pauses for external execution
for requirement in run_response.active_requirements:
    if requirement.is_external_tool_execution:
        if requirement.tool_execution.tool_name == "list_dir":
            result = ShellTools().list_dir(**requirement.tool_execution.tool_args)
            requirement.external_execution_result = result

response = agent.continue_run(
    run_id=run_response.run_id,
    requirements=run_response.requirements,
)
```

## Mixed Tools (External + Normal)

```python
from agno.tools import tool

@tool(external_execution=True)
def sensitive_database_query(query: str) -> str:
    """Execute a database query."""
    pass  # Never called by agent — you execute it

@tool
def safe_calculation(x: int, y: int) -> int:
    """Perform a safe calculation."""
    return x + y

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[sensitive_database_query, safe_calculation],
)

response = agent.run("Calculate 5 + 10 and query the users table")

# safe_calculation already executed normally
# sensitive_database_query is paused for external execution
for requirement in response.active_requirements:
    if requirement.is_external_tool_execution:
        if requirement.tool_execution.tool_name == "sensitive_database_query":
            # Execute with YOUR own DB connection and security checks
            import sqlite3
            conn = sqlite3.connect("my_secure.db")
            result = conn.execute(requirement.tool_execution.tool_args["query"]).fetchall()
            conn.close()
            requirement.external_execution_result = str(result)

response = agent.continue_run(
    run_id=response.run_id,
    requirements=response.requirements,
)
```

## Error Handling

Always wrap external execution in try-catch:

```python
for requirement in run_response.active_requirements:
    if requirement.is_external_tool_execution:
        try:
            result = execute_tool_externally(requirement.tool_execution.tool_args)
            requirement.external_execution_result = result
        except Exception as e:
            # Set error as result so agent knows what happened
            requirement.external_execution_result = f"Error: {str(e)}"
```

## Async Support

```python
import asyncio

async def main():
    run_response = await agent.arun("What files are in my directory?")

    for requirement in run_response.active_requirements:
        if requirement.is_external_tool_execution:
            # Execute your async external logic
            result = await my_async_external_service(requirement.tool_execution.tool_args)
            requirement.external_execution_result = result

    response = await agent.acontinue_run(
        run_id=run_response.run_id,
        requirements=run_response.requirements,
    )
    print(response.content)

asyncio.run(main())
```

## Streaming Support

```python
for run_event in agent.run("What files are in my directory?", stream=True):
    if run_event.is_paused:
        for requirement in run_event.active_requirements:
            if requirement.is_external_tool_execution:
                result = execute_externally(requirement.tool_execution.tool_args)
                requirement.external_execution_result = result

        for response in agent.continue_run(
            run_id=run_event.run_id,
            requirements=run_event.requirements,
            stream=True,
        ):
            print(response.content, end="")
    else:
        print(run_event.content, end="")
```

## Use Cases

| Scenario | Why External Execution |
|----------|----------------------|
| **Database queries** | Use your own connection pool, credentials, and query sanitization |
| **Shell commands** | Sandbox execution environment, validate commands |
| **API calls** | Use your own auth tokens, rate limiting, error handling |
| **File operations** | Control file access permissions, paths, validation |
| **Third-party services** | Use your own client libraries, retry logic, circuit breakers |
| **Audit-sensitive operations** | Log execution details before running |

## Best Practices

- **Always set results** before calling `continue_run()` — agent needs the result to continue
- **Error handling** — catch exceptions and pass error messages as results
- **Security validation** — validate `tool_args` before executing (especially shell commands, SQL)
- **Logging** — log tool name, args, and results for audit trails
- **Timeouts** — add timeouts to prevent hanging on external services
- **Sandboxing** — execute in restricted environments when possible

## Key Constraint

`@tool(external_execution=True)` is mutually exclusive with `@tool(requires_confirmation=True)` and `@tool(requires_user_input=True)`. A single tool can only use one HITL pattern.
