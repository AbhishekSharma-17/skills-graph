# Handoffs — Agent Delegation & Routing

> Source: [openai.github.io/openai-agents-python/handoffs](https://openai.github.io/openai-agents-python/handoffs/)

## Overview

Handoffs enable agents to delegate tasks to specialized agents. When a handoff occurs, the receiving agent takes over the conversation completely, with the full message history transferred. Handoffs are represented as tools to the LLM, with the naming convention `transfer_to_<agent_name>`.

## Handoffs vs Agents-as-Tools

| Feature | Handoffs | Agents as Tools |
|---------|----------|-----------------|
| Control flow | Receiving agent takes over | Calling agent retains control |
| Response | Receiving agent responds to user | Calling agent processes sub-agent output |
| History | Full conversation transferred | Sub-agent gets relevant context |
| Use case | Specialist owns the conversation | Orchestrator delegates subtasks |

## Creating Handoffs

### Basic — Direct Agent Reference

```python
from agents import Agent

billing_agent = Agent(name="Billing Agent", instructions="Handle billing questions.")
refund_agent = Agent(name="Refund Agent", instructions="Handle refund requests.")

triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "Route users to the right specialist. "
        "Use billing agent for payment questions. "
        "Use refund agent for return/refund requests."
    ),
    handoffs=[billing_agent, refund_agent],
)
```

### Customized — Using `handoff()` Function

```python
from agents import Agent, handoff, RunContextWrapper

def on_billing_handoff(ctx: RunContextWrapper):
    print("User routed to billing")

billing_handoff = handoff(
    agent=billing_agent,
    tool_name_override="route_to_billing",
    tool_description_override="Route to billing for payment and invoice questions",
    on_handoff=on_billing_handoff,
)

triage_agent = Agent(
    name="Triage Agent",
    handoffs=[billing_handoff, refund_agent],
)
```

### `handoff()` Parameters

| Parameter | Purpose |
|-----------|---------|
| `agent` | Target agent for delegation |
| `tool_name_override` | Custom tool name (default: `transfer_to_<name>`) |
| `tool_description_override` | Custom description for the handoff tool |
| `on_handoff` | Callback executed when handoff is invoked |
| `input_type` | Pydantic model for handoff arguments |
| `input_filter` | Filter/transform conversation history for receiving agent |
| `is_enabled` | Boolean or function controlling availability |
| `nest_handoff_history` | Per-handoff override for history nesting |

## Handoff Inputs

Provide model-generated metadata at handoff time:

```python
from pydantic import BaseModel
from agents import Agent, handoff, RunContextWrapper

class EscalationData(BaseModel):
    reason: str
    priority: str
    summary: str

async def on_escalation(ctx: RunContextWrapper, input_data: EscalationData):
    print(f"Escalation: {input_data.reason} (priority: {input_data.priority})")
    await log_escalation(input_data)

escalation_handoff = handoff(
    agent=escalation_agent,
    on_handoff=on_escalation,
    input_type=EscalationData,
)
```

Use `input_type` for small model-generated metadata (reason, language, priority). For existing application state, use `RunContextWrapper.context`.

## Input Filters

Control what conversation history the receiving agent sees via `HandoffInputData`:

```python
from agents import handoff
from agents.extensions import handoff_filters

# Remove all tool call/result items from history
clean_handoff = handoff(
    agent=faq_agent,
    input_filter=handoff_filters.remove_all_tools,
)
```

### Custom Input Filter

```python
from agents.handoffs import HandoffInputData

def custom_filter(data: HandoffInputData) -> HandoffInputData:
    # Keep only the last 5 items from history
    recent = data.input_history[-5:] if data.input_history else []
    return HandoffInputData(
        input_history=recent,
        pre_handoff_items=data.pre_handoff_items,
        new_items=data.new_items,
    )

filtered_handoff = handoff(
    agent=specialist_agent,
    input_filter=custom_filter,
)
```

### HandoffInputData Fields

| Field | Description |
|-------|-------------|
| `input_history` | Pre-run conversation history |
| `pre_handoff_items` | Items generated before handoff was invoked |
| `new_items` | Items from the current turn |
| `input_items` | Optional override for `new_items` |
| `run_context` | Active `RunContextWrapper` |

## Recommended Prompts

The SDK provides recommended prompt patterns for agents receiving handoffs:

```python
from agents import Agent
from agents.extensions.handoff_prompt import (
    RECOMMENDED_PROMPT_PREFIX,
    prompt_with_handoff_instructions,
)

# Option 1: Manual prefix
billing_agent = Agent(
    name="Billing Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You handle billing and payment questions.
    Always verify the account before making changes.""",
)

# Option 2: Automatic wrapping
billing_agent = Agent(
    name="Billing Agent",
    instructions=prompt_with_handoff_instructions(
        "You handle billing and payment questions. "
        "Always verify the account before making changes."
    ),
)
```

## Nested Handoffs (Beta)

Opt-in to collapse prior conversation history into a summary before handoffs:

```python
from agents import RunConfig

result = await Runner.run(
    triage_agent,
    "I need help with my account",
    run_config=RunConfig(nest_handoff_history=True),
)
```

When enabled, the receiving agent sees prior transcript wrapped in a `<CONVERSATION HISTORY>` block rather than the full raw history. This reduces token usage for long conversations.

Customize the summary format:

```python
config = RunConfig(
    nest_handoff_history=True,
    handoff_history_mapper=my_custom_mapper,
)
```

Override per-handoff:

```python
billing_handoff = handoff(
    agent=billing_agent,
    nest_handoff_history=True,   # Override the global setting
)
```

## Conditional Handoffs

Enable or disable handoffs based on runtime context:

```python
from agents import handoff, RunContextWrapper, AgentBase

def billing_enabled(ctx: RunContextWrapper, agent: AgentBase) -> bool:
    return ctx.context.has_billing_access

conditional_handoff = handoff(
    agent=billing_agent,
    is_enabled=billing_enabled,
)
```

## Multi-Level Handoff Chains

Agents can hand off to agents that hand off to other agents:

```python
l2_support = Agent(
    name="L2 Support",
    instructions="Handle complex technical issues.",
)

l1_support = Agent(
    name="L1 Support",
    instructions="Handle basic questions. Escalate complex issues.",
    handoffs=[l2_support],
)

triage = Agent(
    name="Triage",
    instructions="Route to L1 support.",
    handoffs=[l1_support],
)
```

## Common Pitfalls

- **Missing handoff_description**: Without it, the LLM has no context for when to hand off
- **Circular handoffs**: Agent A hands to B, B hands back to A — can loop indefinitely; use `max_turns`
- **Large history transfer**: Long conversations transfer full history; use `input_filter` or `nest_handoff_history` to manage token usage
- **Forgetting on_handoff side effects**: The callback runs before the receiving agent — use it for logging, not blocking operations

## Related Topics

- **Agents:** `01-agents.md` — Agent configuration
- **Multi-Agent:** `08-multi-agent.md` — Orchestration patterns
- **Running Agents:** `03-running-agents.md` — Runner and execution
