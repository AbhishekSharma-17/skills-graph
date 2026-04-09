# Multi-Agent Workflows

> Source: [docs.livekit.io/agents/logic/workflows](https://docs.livekit.io/agents/logic/workflows/) — Agent handoffs, tasks, and task groups

## Table of Contents

- [Workflow Architecture](#workflow-architecture)
- [Agents](#agents)
- [Agent Handoffs](#agent-handoffs)
- [Tasks](#tasks)
- [Task Groups](#task-groups)
- [Workflow Patterns](#workflow-patterns)
- [Context Preservation](#context-preservation)
- [Best Practices](#best-practices)

---

## Workflow Architecture

LiveKit's workflow system has four interconnected constructs:

```
┌─────────────────────────────────────────────────┐
│                 AgentSession                      │
│                                                   │
│  ┌──────────┐  handoff  ┌──────────┐             │
│  │  Agent A  │ ────────► │  Agent B  │             │
│  │ (Greeter) │           │ (Support) │             │
│  └──────────┘           └──────────┘             │
│       │                       │                    │
│       │ calls tool            │ creates task       │
│       ▼                       ▼                    │
│  ┌──────────┐           ┌──────────┐             │
│  │   Tool    │           │   Task    │             │
│  │ (lookup)  │           │ (verify)  │             │
│  └──────────┘           └──────────┘             │
└─────────────────────────────────────────────────┘
```

| Construct | Lifetime | Purpose |
|-----------|----------|---------|
| **AgentSession** | Entire conversation | Orchestrates everything |
| **Agent** | Long-lived | Holds control, instructions, tools |
| **Tool** | Single invocation | Executes side effects |
| **Task** | Temporary | Discrete operation, returns typed result |
| **Task Group** | Temporary | Ordered sequence of tasks |

## Agents

Agents define a personality, instructions, and available tools:

```python
from livekit.agents import Agent

greeter_agent = Agent(
    instructions="""You are a friendly greeter for Acme Corp.
    Welcome the caller and ask how you can help.
    If they need technical support, transfer to the support agent.
    If they need billing help, transfer to the billing agent.""",
    tools=[transfer_to_support, transfer_to_billing, check_hours],
)

support_agent = Agent(
    instructions="""You are a technical support specialist.
    Help users troubleshoot technical issues.
    You can look up their account and check system status.""",
    tools=[lookup_account, check_system_status, create_ticket],
)

billing_agent = Agent(
    instructions="""You are a billing specialist.
    Help users with invoices, payments, and plan changes.""",
    tools=[get_invoice, process_refund, change_plan],
)
```

## Agent Handoffs

Transfer control from one agent to another:

```python
from livekit.agents import function_tool, RunContext

@function_tool()
async def transfer_to_support(context: RunContext, reason: str) -> str:
    """Transfer the conversation to technical support.

    Args:
        reason: Why the user needs technical support.
    """
    await context.session.handoff(
        support_agent,
        reason=reason,
    )
    return "Transferring you to technical support now."

@function_tool()
async def transfer_to_billing(context: RunContext, reason: str) -> str:
    """Transfer the conversation to billing support.

    Args:
        reason: Why the user needs billing help.
    """
    await context.session.handoff(
        billing_agent,
        reason=reason,
    )
    return "Connecting you with our billing team."
```

**Handoff behavior:**
- The new agent takes over the session
- Previous agent's tools are replaced by new agent's tools
- Instructions change to the new agent's instructions
- Conversation history can be preserved or reset

## Tasks

Tasks are temporary, scoped operations that return typed results:

```python
from livekit.agents import Agent, Task
from pydantic import BaseModel

class VerificationResult(BaseModel):
    verified: bool
    customer_id: str | None = None

verify_identity_task = Task(
    instructions="""Verify the caller's identity by asking for:
    1. Full name
    2. Last 4 digits of their account number
    3. Email address on file

    Do not proceed until all three are confirmed.""",
    output_type=VerificationResult,
)
```

**Using a task:**

```python
@function_tool()
async def verify_caller(context: RunContext) -> str:
    """Verify the caller's identity before accessing account info."""
    result: VerificationResult = await context.session.run_task(verify_identity_task)

    if result.verified:
        context.session.userdata["customer_id"] = result.customer_id
        return f"Identity verified for customer {result.customer_id}"
    else:
        return "Identity verification failed."
```

**Tasks vs Agents:**
- **Tasks** are temporary — they complete and return a result
- **Agents** persist — they hold ongoing conversational control
- Use tasks for discrete operations (verification, data collection, consent)
- Use agents for ongoing personas (support, sales, triage)

## Task Groups

Ordered sequences of tasks for multi-step flows:

```python
from livekit.agents import TaskGroup

onboarding_flow = TaskGroup(
    tasks=[
        Task(
            instructions="Collect the user's full name and email.",
            output_type=ContactInfo,
        ),
        Task(
            instructions="Ask which plan they want: Basic, Pro, or Enterprise.",
            output_type=PlanSelection,
        ),
        Task(
            instructions="Confirm all details and get verbal agreement.",
            output_type=Confirmation,
        ),
    ],
)
```

**Task group features:**
- Tasks execute in order
- All tasks share conversation context
- Users can request to go back to a previous step
- The group returns results from all tasks

```python
@function_tool()
async def start_onboarding(context: RunContext) -> str:
    """Begin the new customer onboarding process."""
    results = await context.session.run_task_group(onboarding_flow)
    contact = results[0]  # ContactInfo
    plan = results[1]     # PlanSelection
    confirmed = results[2]  # Confirmation
    return f"Onboarding complete for {contact.name} on {plan.plan} plan"
```

## Workflow Patterns

### Triage → Specialist Pattern

```python
# Entry agent triages and routes
triage_agent = Agent(
    instructions="Determine what the caller needs and route to the right specialist.",
    tools=[transfer_to_support, transfer_to_billing, transfer_to_sales],
)

# Start session with triage agent
await session.start(room=ctx.room, agent=triage_agent)
```

### Verification Gate Pattern

```python
# Verify identity before allowing account access
main_agent = Agent(
    instructions="Help users with their account. Always verify identity first.",
    tools=[verify_caller, lookup_account, update_account],
)
```

### Escalation Pattern

```python
@function_tool()
async def escalate_to_human(context: RunContext, summary: str) -> str:
    """Escalate to a human agent when you cannot resolve the issue."""
    # Notify your backend to connect a human agent
    await notify_human_queue(
        room=context.session.room.name,
        summary=summary,
    )
    await context.session.say("I'm connecting you with a human agent. Please hold.")
    return "Escalation initiated. Human agent will join shortly."
```

## Context Preservation

When handing off between agents, decide how to handle conversation history:

```python
# Preserve full history (default)
await context.session.handoff(support_agent)

# Handoff with additional context
await context.session.handoff(
    support_agent,
    reason="User needs help with login issues. They've already verified identity.",
)
```

**Best practices:**
- Preserve context when the next agent needs to know what was discussed
- Provide a reason/summary for the handoff
- Use `userdata` to pass structured data between agents

## Best Practices

1. **Create separate agents** when distinct reasoning behavior or tool access is needed
2. **Use tasks** for discrete operations that must complete before continuing
3. **Expose external actions through tools** with clear purpose and meaningful returns
4. **Plan context preservation** — some transitions need full history, others benefit from a clean slate
5. **Build incrementally** — start with one agent, add handoffs when complexity warrants it
6. **Test handoffs** — verify that context transfers correctly and tools are accessible
7. **Limit tool count per agent** — LLMs perform better with focused tool sets (5-10 per agent)
8. **Use task groups** for sequential data collection with regression support
