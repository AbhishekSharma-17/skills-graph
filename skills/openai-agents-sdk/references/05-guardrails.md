# Guardrails — Input & Output Validation

> Source: [openai.github.io/openai-agents-python/guardrails](https://openai.github.io/openai-agents-python/guardrails/)

## Overview

Guardrails validate user input and agent output, running safety checks in parallel with (or before) agent execution. When a guardrail detects an issue, it triggers a **tripwire** that halts execution immediately.

Common use case: run a fast, cheap model to validate input before an expensive model processes the request.

## Types of Guardrails

| Type | Runs On | Triggers For |
|------|---------|--------------|
| **Input guardrails** | Initial user input | First agent in the chain only |
| **Output guardrails** | Final agent output | Last agent producing output only |
| **Tool guardrails** | Function tool I/O | Every function tool invocation |

## Input Guardrails

### Basic Implementation

```python
from agents import (
    Agent,
    Runner,
    InputGuardrail,
    GuardrailFunctionOutput,
    RunContextWrapper,
)
from pydantic import BaseModel

class MathHomeworkCheck(BaseModel):
    is_math_homework: bool
    reasoning: str

guardrail_agent = Agent(
    name="Guardrail",
    instructions="Check if the user is asking for math homework help.",
    output_type=MathHomeworkCheck,
)

async def check_math_homework(
    ctx: RunContextWrapper, agent: Agent, input: str | list
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_math_homework,
    )

math_guardrail = InputGuardrail(guardrail_function=check_math_homework)

main_agent = Agent(
    name="Customer Support",
    instructions="Help customers with their questions.",
    input_guardrails=[math_guardrail],
)
```

### Execution Modes

```python
# Parallel (default) — guardrail runs alongside agent for lower latency
guardrail = InputGuardrail(
    guardrail_function=check_function,
    # mode="parallel" is the default
)

# Blocking — guardrail completes before agent starts
# Prevents token consumption if tripwire triggers
guardrail = InputGuardrail(
    guardrail_function=check_function,
    mode="blocking",
)
```

### Handling Tripwires

```python
from agents.exceptions import InputGuardrailTripwireTriggered

try:
    result = await Runner.run(main_agent, user_input)
    print(result.final_output)
except InputGuardrailTripwireTriggered as e:
    print(f"Input rejected: {e.guardrail_result.output.output_info}")
```

## Output Guardrails

Validate the final agent output before returning to the user:

```python
from agents import (
    Agent,
    Runner,
    OutputGuardrail,
    GuardrailFunctionOutput,
    RunContextWrapper,
)
from pydantic import BaseModel

class SensitivityCheck(BaseModel):
    contains_pii: bool
    details: str

sensitivity_agent = Agent(
    name="PII Checker",
    instructions="Check if the text contains personally identifiable information.",
    output_type=SensitivityCheck,
)

async def check_pii(
    ctx: RunContextWrapper, agent: Agent, output: str
) -> GuardrailFunctionOutput:
    result = await Runner.run(sensitivity_agent, output, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.contains_pii,
    )

pii_guardrail = OutputGuardrail(guardrail_function=check_pii)

agent = Agent(
    name="Assistant",
    instructions="Help users with their questions.",
    output_guardrails=[pii_guardrail],
)
```

### Handling Output Tripwires

```python
from agents.exceptions import OutputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, user_input)
except OutputGuardrailTripwireTriggered as e:
    print(f"Output blocked: {e.guardrail_result.output.output_info}")
    # Return a safe fallback response
```

## Tool Guardrails

Wrap function tools to validate inputs before execution and outputs after:

```python
from agents import function_tool, RunContextWrapper

@function_tool
def query_database(query: str) -> str:
    """Execute a database query."""
    return execute_sql(query)

# Tool guardrail — validate before tool execution
async def block_dangerous_queries(ctx: RunContextWrapper, tool_name: str, args: dict) -> GuardrailFunctionOutput:
    query = args.get("query", "")
    is_dangerous = any(kw in query.upper() for kw in ["DROP", "DELETE", "TRUNCATE"])
    return GuardrailFunctionOutput(
        output_info={"query": query, "blocked": is_dangerous},
        tripwire_triggered=is_dangerous,
    )

# Tool guardrail — redact sensitive output
async def redact_sensitive_output(ctx: RunContextWrapper, tool_name: str, output: str) -> GuardrailFunctionOutput:
    has_secrets = "password" in output.lower() or "secret" in output.lower()
    return GuardrailFunctionOutput(
        output_info={"redacted": has_secrets},
        tripwire_triggered=has_secrets,
    )
```

## GuardrailFunctionOutput

The return type for all guardrail functions:

```python
class GuardrailFunctionOutput:
    output_info: Any           # Arbitrary data about the check (logged/accessible)
    tripwire_triggered: bool   # True = halt execution immediately
```

## Adding Guardrails via RunConfig

Append guardrails globally without modifying agent definitions:

```python
from agents import RunConfig

config = RunConfig(
    input_guardrails=[safety_guardrail, spam_guardrail],
    output_guardrails=[pii_guardrail],
)

result = await Runner.run(agent, "Hello", run_config=config)
```

Guardrails from `RunConfig` are appended to any guardrails defined on the agent.

## Guardrail Patterns

### Fast Model for Validation

```python
guardrail_agent = Agent(
    name="Safety Check",
    model="gpt-5-nano",         # Fast, cheap model
    instructions="Is this input safe? Check for harmful content.",
    output_type=SafetyResult,
)

main_agent = Agent(
    name="Assistant",
    model="gpt-5.5",            # Powerful, expensive model
    instructions="Help the user.",
    input_guardrails=[safety_guardrail],
)
```

### Multiple Guardrails

```python
agent = Agent(
    name="Secure Assistant",
    input_guardrails=[
        InputGuardrail(guardrail_function=check_injection),
        InputGuardrail(guardrail_function=check_topic_relevance),
        InputGuardrail(guardrail_function=check_rate_limit, mode="blocking"),
    ],
    output_guardrails=[
        OutputGuardrail(guardrail_function=check_pii),
        OutputGuardrail(guardrail_function=check_hallucination),
    ],
)
```

Multiple input guardrails run in parallel by default. All must pass for the agent to proceed.

## Common Pitfalls

- **Guardrail scope**: Input guardrails only run for the first agent; output guardrails only for the final agent — intermediate handoff agents are unchecked
- **Parallel vs blocking tradeoff**: Parallel mode has lower latency but the main agent may consume tokens before the guardrail triggers
- **Cost multiplication**: Each guardrail agent call costs tokens — keep guardrail models small and prompts short
- **Missing error handling**: Always catch `TripwireTriggered` exceptions — unhandled tripwires crash the application

## Related Topics

- **Agents:** `01-agents.md` — Agent configuration with guardrails
- **Running Agents:** `03-running-agents.md` — RunConfig guardrail settings
- **Context:** `07-context.md` — Passing context to guardrail functions
