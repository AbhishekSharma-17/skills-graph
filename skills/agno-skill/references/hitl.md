# Agno Human-in-the-Loop (HITL) — Reference Router

Human-in-the-Loop enables human oversight of agent execution. When a tool requires human intervention, execution **pauses** (`is_paused=True`), requirements are populated, and the agent waits for resolution before continuing via `continue_run()`.

> **Note:** HITL currently supports `Agent` only. `Team` and `Workflow` support is coming soon.

## Docs Hierarchy

```
Human-in-the-Loop
├── Overview (/hitl/overview)
├── User Confirmation (/hitl/user-confirmation)
├── User Input (/hitl/user-input)
├── Dynamic User Input (/hitl/dynamic-user-input)
├── External Execution (/hitl/external-execution)
└── Usage
    ├── Agentic User Input
    ├── Confirmation Required
    ├── User Input Required
    └── External Tool Execution
```

## Four HITL Patterns

| Pattern | Marker | What Happens | Use Case |
|---------|--------|--------------|----------|
| **User Confirmation** | `@tool(requires_confirmation=True)` | Approve/reject before tool executes | Sensitive operations, API calls |
| **User Input** | `@tool(requires_user_input=True)` | Collect specific field values from user | Gather params agent can't determine |
| **Dynamic User Input** | `UserControlFlowTools()` | Agent decides what fields to request | Unpredictable interaction flows |
| **External Execution** | `@tool(external_execution=True)` | You execute the tool with custom logic | Sandboxed execution, DB ops |

**Mutual exclusivity:** Each tool can only use ONE of these patterns — `requires_confirmation`, `requires_user_input`, and `external_execution` are mutually exclusive on a single tool.

## Core Execution Flow

```
1. agent.run("message")           → Agent processes, hits HITL tool
2. run_response.is_paused = True  → Execution pauses
3. Handle active_requirements     → Confirm / provide input / execute externally
4. agent.continue_run(...)        → Agent continues with resolved requirements
5. (May pause again for more requirements — use while loop)
```

## Sub-References

Read only what the current task requires:

| Reference | File | Read When |
|-----------|------|-----------|
| **User Confirmation** | `references/hitl/user-confirmation.md` | Approve/reject tool calls before execution — `@tool(requires_confirmation=True)`, toolkit-level confirmation, rejection feedback, mixed tools, async/streaming |
| **User Input** | `references/hitl/user-input.md` | Collect specific fields from user — `@tool(requires_user_input=True)`, `user_input_fields`, `UserInputField` class, pre-filled values, async/streaming |
| **Dynamic User Input** | `references/hitl/dynamic-user-input.md` | Agent-driven input collection — `UserControlFlowTools`, `get_user_input()`, while loop pattern, multi-round input, custom instructions |
| **External Execution** | `references/hitl/external-execution.md` | Execute tools outside agent control — `@tool(external_execution=True)`, toolkit-level external execution, setting results, async/streaming |

## @tool Decorator HITL Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `requires_confirmation` | `bool` | `False` | Pause for user approval before tool executes |
| `requires_user_input` | `bool` | `False` | Pause to collect specific field values from user |
| `user_input_fields` | `Optional[List[UserInputField]]` | `None` | Fields to collect when `requires_user_input=True` |
| `external_execution` | `bool` | `False` | Pause for external/custom tool execution |

**Mutual exclusivity:** `requires_confirmation`, `requires_user_input`, and `external_execution` are mutually exclusive on a single tool.

## UserInputField Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Field identifier name |
| `field_type` | `Type` | Required | Python type: `str`, `int`, `float`, `bool`, `list`, `dict` |
| `description` | `Optional[str]` | `None` | Human-readable field description |
| `value` | `Optional[Any]` | `None` | Pre-filled or user-provided value |

## Requirement Object Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `needs_confirmation` | `bool` | Whether this requirement needs user approval |
| `needs_user_input` | `bool` | Whether this requirement needs user-provided field values |
| `is_external_tool_execution` | `bool` | Whether this requirement needs external execution |
| `tool` | `Tool` | Tool info (name, args) — for confirmation pattern |
| `user_input_schema` | `List[UserInputField]` | Fields to collect — for user input pattern |
| `tool_execution` | `ToolExecution` | Tool execution info — for external execution pattern |

## Requirement Methods

| Method | Description |
|--------|-------------|
| `confirm()` | Approve the tool call (confirmation pattern) |
| `reject(feedback=None)` | Reject the tool call with optional feedback |
| `set_user_input(field_name, value)` | Set a user input field value |
| `set_tool_result(result)` | Set the result of external execution |

## RunResponse HITL Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_paused` | `bool` | Whether run is paused waiting for human input |
| `active_requirements` | `List[Requirement]` | Pending requirements needing resolution |
| `requirements` | `List[Requirement]` | All requirements (resolved and pending) |
| `run_id` | `str` | Run ID for `continue_run()` |

## Quick Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools import tool

@tool(requires_confirmation=True)
def delete_record(record_id: str) -> str:
    """Delete a record from the database."""
    return f"Record {record_id} deleted"

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[delete_record],
)

run_response = agent.run("Delete record 42")

if run_response.is_paused:
    for req in run_response.active_requirements:
        if req.needs_confirmation:
            print(f"Tool: {req.tool.tool_name}({req.tool.tool_args})")
            if input("Approve? (y/n): ").lower() == "y":
                req.confirm()
            else:
                req.reject()

    response = agent.continue_run(
        run_id=run_response.run_id,
        requirements=run_response.requirements,
    )
```

## Key Classes

```python
# RunResponse properties for HITL
run_response.is_paused                # bool — Whether run is paused
run_response.active_requirements      # List[Requirement] — Pending requirements
run_response.requirements             # List[Requirement] — All requirements
run_response.run_id                   # str — Run ID for continue_run()

# Requirement object
requirement.needs_confirmation        # bool
requirement.needs_user_input          # bool
requirement.is_external_tool_execution  # bool
requirement.tool                      # Tool — For confirmation
requirement.user_input_schema         # List[UserInputField] — For user input
requirement.tool_execution            # ToolExecution — For external execution

# UserInputField
field.name                            # str
field.field_type                      # Type (str, int, float, bool, list, dict)
field.description                     # Optional[str]
field.value                           # Optional[Any] — Set by user or agent

# ToolExecution
tool_execution.tool_name              # str
tool_execution.tool_args              # Dict[str, Any]
tool_execution.external_execution_required  # bool
```

## Key Imports

```python
from agno.agent import Agent
from agno.tools import tool                              # @tool decorator with HITL flags
from agno.tools.function import UserInputField           # User input field schema
from agno.tools.user_control_flow import UserControlFlowTools  # Dynamic user input
from agno.tools.toolkit import Toolkit                   # Toolkit with HITL flags
```

## Core API Methods

```python
# Run agent (may pause)
run_response = agent.run("message")
run_response = await agent.arun("message")

# Continue after resolving requirements
response = agent.continue_run(run_id=run_response.run_id, requirements=run_response.requirements)
response = await agent.acontinue_run(run_id=run_response.run_id, requirements=run_response.requirements)

# Alternative: pass entire run_response
response = agent.continue_run(run_response=run_response)
```
