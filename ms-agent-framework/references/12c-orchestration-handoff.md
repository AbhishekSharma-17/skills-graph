# Handoff Orchestration — Dynamic Agent-to-Agent Control Transfer

## Overview

Agents transfer control to each other based on context. Implemented as a mesh topology — no central orchestrator. Each agent decides when to hand off via special tool calls. Supports interactive (human input) and autonomous modes.

```
User → Triage Agent ──→ Refund Agent
                    └──→ Order Agent ──→ Return Agent
```

## When to Use

- Customer support with specialized agents
- Expert routing systems
- Dynamic task delegation
- Interactive multi-agent conversations
- Approval workflows requiring human decisions
- Situations where agents need real-time human feedback

## Key Difference from Agent-as-Tools

| | Handoff | Agent-as-Tools |
|---|---|---|
| **Control** | Full control transfers to new agent | Primary agent stays in control |
| **Ownership** | Receiving agent owns the task | Primary agent delegates subtask |
| **Context** | Full conversation transfers | Primary agent provides filtered context |

## Implementation

### 1. Define Tools for Specialists

```python
from typing import Annotated
from agent_framework import tool

@tool
def process_refund(order_number: Annotated[str, "Order number"]) -> str:
    """Process a refund for a given order number."""
    return f"Refund processed for order {order_number}."

@tool
def check_order_status(order_number: Annotated[str, "Order number"]) -> str:
    """Check the status of a given order number."""
    return f"Order {order_number} ships in 2 business days."

@tool
def process_return(order_number: Annotated[str, "Order number"]) -> str:
    """Process a return for a given order number."""
    return f"Return initiated for order {order_number}."
```

### 2. Create Agents

```python
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

triage_agent = chat_client.as_agent(
    instructions="You are frontline triage. Route customers to the right specialist.",
    description="Triage agent for general inquiries.",
    name="triage_agent",
)

refund_agent = chat_client.as_agent(
    instructions="You process refund requests.",
    description="Handles refund requests.",
    name="refund_agent",
    tools=[process_refund],
)

order_agent = chat_client.as_agent(
    instructions="You handle order and shipping inquiries.",
    description="Handles order tracking and shipping.",
    name="order_agent",
    tools=[check_order_status],
)

return_agent = chat_client.as_agent(
    instructions="You manage product return requests.",
    description="Handles return processing.",
    name="return_agent",
    tools=[process_return],
)
```

### 3. Build Handoff Workflow

#### Default (All Can Handoff to All)

```python
from agent_framework.orchestrations import HandoffBuilder

workflow = (
    HandoffBuilder(
        name="customer_support",
        participants=[triage_agent, refund_agent, order_agent, return_agent],
    )
    .with_start_agent(triage_agent)
    .build()
)
```

#### Custom Handoff Rules with add_handoff()

```python
workflow = (
    HandoffBuilder(
        name="customer_support",
        participants=[triage_agent, refund_agent, order_agent, return_agent],
    )
    .with_start_agent(triage_agent)
    # Define allowed handoff paths
    .add_handoff(triage_agent, [order_agent, return_agent])    # Triage routes to specialists
    .add_handoff(return_agent, [refund_agent])                 # Return can go to refund
    .add_handoff(order_agent, [triage_agent])                  # Specialists can return to triage
    .add_handoff(return_agent, [triage_agent])
    .add_handoff(refund_agent, [triage_agent])
    .build()
)
```

## HandoffBuilder API

### Constructor

```python
HandoffBuilder(
    name: str,                          # Workflow name
    participants: list[Agent],          # All agents in the network
    termination_condition: callable | None = None,  # Optional end condition
)
```

### Builder Methods

| Method | Parameters | Description |
|--------|-----------|---|
| `.with_start_agent()` | `agent: Agent` | First agent to receive user input |
| `.add_handoff()` | `source: Agent`, `targets: list[Agent]` | Define allowed handoff paths |
| `.with_autonomous_mode()` | Multiple options (see below) | Enable automatic continuation without human input |
| `.build()` | | Create executable workflow |

### with_autonomous_mode Options

```python
# Option 1: All agents run autonomously (no human input needed)
.with_autonomous_mode()

# Option 2: Specific agents are autonomous, others wait for human input
.with_autonomous_mode(agents=[agent_a, agent_b])

# Option 3: Custom continuation prompts per agent
.with_autonomous_mode(
    agents=[agent_a],
    prompts={
        agent_a.name: "Continue with your best judgment.",
        agent_b.name: "Escalate if you need help."
    }
)

# Option 4: Limit autonomous turns per agent
.with_autonomous_mode(
    agents=[agent_a],
    turn_limits={
        agent_a.name: 3,  # Max 3 autonomous turns for agent_a
        agent_b.name: 1   # Max 1 for agent_b
    }
)

# Option 5: Combine prompts and turn limits
.with_autonomous_mode(
    agents=[agent_a, agent_b],
    prompts={agent_a.name: "Use your judgment"},
    turn_limits={agent_a.name: 5, agent_b.name: 2}
)
```

## Interactive Handoff

Run with human-in-the-loop, where agents pause for user confirmation:

```python
from agent_framework import WorkflowEvent
from agent_framework.orchestrations import HandoffAgentUserRequest

# Start workflow
events = [event async for event in workflow.run_stream("I need help with my order")]

# Process events and identify pending requests
pending_requests = []
for event in events:
    if event.type == "request_info" and isinstance(event.data, HandoffAgentUserRequest):
        pending_requests.append(event)
        request_data = event.data
        print(f"Agent {event.executor_id} awaits your input:")

        # Show last few messages from agent
        for msg in request_data.agent_response.messages[-3:]:
            print(f"  {msg.author_name}: {msg.text}")

# Interactive loop
while pending_requests:
    user_input = input("You: ")

    # Create response(s) for pending requests
    responses = {
        req.request_id: HandoffAgentUserRequest.create_response(user_input)
        for req in pending_requests
    }

    # Continue workflow with responses
    events = [event async for event in workflow.run(responses=responses)]

    # Check for new pending requests
    pending_requests = []
    for event in events:
        if event.type == "request_info" and isinstance(event.data, HandoffAgentUserRequest):
            pending_requests.append(event)
```

## HandoffAgentUserRequest API

```python
from agent_framework.orchestrations import HandoffAgentUserRequest

# Create response to continue
response = HandoffAgentUserRequest.create_response(user_input_text)

# Terminate the workflow instead
termination = HandoffAgentUserRequest.terminate()

# Retrieve request data
request_data = event.data  # HandoffAgentUserRequest instance
agent_response = request_data.agent_response  # Recent agent messages
messages = request_data.agent_response.messages  # List of Message objects
```

## Termination Conditions

Automatically end workflow when a condition is met:

```python
def conversation_resolved(conversation: list) -> bool:
    """Check if issue is resolved."""
    if not conversation:
        return False

    last_message = conversation[-1].text.lower()
    resolved_keywords = ["resolved", "issue fixed", "order placed", "return initiated"]

    return any(keyword in last_message for keyword in resolved_keywords)

workflow = (
    HandoffBuilder(
        name="support",
        participants=[triage_agent, refund_agent, order_agent],
        termination_condition=conversation_resolved
    )
    .with_start_agent(triage_agent)
    .build()
)
```

Or terminate from interactive loop:

```python
while pending_requests:
    user_input = input("You (or 'quit' to end): ")

    if user_input.lower() == "quit":
        # Terminate the workflow
        responses = {
            req.request_id: HandoffAgentUserRequest.terminate()
            for req in pending_requests
        }
    else:
        # Continue normally
        responses = {
            req.request_id: HandoffAgentUserRequest.create_response(user_input)
            for req in pending_requests
        }

    events = [event async for event in workflow.run(responses=responses)]
    # Process events...
```

## Full Autonomous Handoff Example

```python
from agent_framework.orchestrations import HandoffBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

async def main():
    chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

    # Create agents with tools
    triage = chat_client.as_agent(
        instructions="Route customer to appropriate specialist.",
        name="triage",
    )

    billing = chat_client.as_agent(
        instructions="Handle billing and payment issues.",
        name="billing",
        tools=[check_account, process_payment]
    )

    technical = chat_client.as_agent(
        instructions="Resolve technical issues.",
        name="technical",
        tools=[check_system_status, restart_service]
    )

    # Build with full autonomous mode
    workflow = (
        HandoffBuilder(
            name="support_auto",
            participants=[triage, billing, technical]
        )
        .with_start_agent(triage)
        .add_handoff(triage, [billing, technical])
        .add_handoff(billing, [triage])
        .add_handoff(technical, [triage])
        .with_autonomous_mode()  # All agents run without human input
        .build()
    )

    # Run to completion without intervention
    events = []
    async for event in workflow.run_stream("My credit card keeps getting declined"):
        if event.type == "output":
            if hasattr(event.data, 'text'):
                print(event.data.text, end="", flush=True)
        events.append(event)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Partial Autonomous with Fallback to Human

```python
# Only triage agent is autonomous; others wait for human approval
workflow = (
    HandoffBuilder(
        name="mixed_mode",
        participants=[triage_agent, billing_agent, technical_agent]
    )
    .with_start_agent(triage_agent)
    .with_autonomous_mode(agents=[triage_agent])  # Only triage autonomous
    .build()
)

# Execution: triage routes automatically, specialists pause for user approval
pending_requests = []
async for event in workflow.run_stream("I have an issue"):
    if event.type == "request_info":
        pending_requests.append(event)
        print(f"Specialist {event.executor_id} needs your approval")

# User approves or modifies specialist's action
while pending_requests:
    user_approval = input("Approve? (y/n): ")
    responses = {
        req.request_id: HandoffAgentUserRequest.create_response(
            "Proceed" if user_approval.lower() == 'y' else "Ask clarifying questions"
        )
        for req in pending_requests
    }
    # ... continue
```

## Workflow as Agent

Wrap handoff workflow as a reusable agent:

```python
# Convert to agent
workflow_agent = workflow.as_agent(name="Customer Support Agent")

# Create session
session = await workflow_agent.create_session()

# Run as agent
messages = [Message(role="user", contents=["I need help with my order"])]

async for update in workflow_agent.run(messages, session=session, stream=True):
    if update.text:
        print(update.text, end="", flush=True)
```

## Mesh Topology Routing

Handoff creates a mesh where agents route to each other:

```
      ┌─ Billing Agent ─┐
      │                 │
Triage Agent ├─ Technical Agent ─┤
      │                 │
      └─ Escalation Agent

Each agent can communicate with any allowed agent directly
No central controller
Decisions are distributed
```

## Key Characteristics

| Feature | Detail |
|---|---|
| **Dynamic Routing** | Agents hand off based on context |
| **Mesh Topology** | No central orchestrator |
| **Full Context Transfer** | Complete conversation passes to new agent |
| **Interactive Mode** | Can pause for human approval at each agent |
| **Autonomous Mode** | Can run fully automatic without human input |
| **Customizable Routes** | Control which agents can hand off to which |
| **Termination Control** | Define conditions to end workflow or terminate interactively |

## Configuration Summary

| Method | Required | Description |
|---|:-:|---|
| `HandoffBuilder()` | ✅ | Initialize with name and participants |
| `.with_start_agent()` | ✅ | Set initial agent |
| `.add_handoff()` | ❌ | Restrict handoff paths (if not specified, all can handoff to all) |
| `.with_autonomous_mode()` | ❌ | Enable full or partial autonomy |
| `termination_condition` | ❌ | Lambda to determine when to end |
| `.build()` | ✅ | Create executable workflow |

## Best Practices

1. **Clear Agent Roles**: Each agent should have specific, non-overlapping expertise
2. **Handoff Instructions**: Include handoff instructions in each agent's system prompt
3. **Routing Strategy**: Use `add_handoff()` to prevent irrelevant transitions
4. **Mode Selection**: Choose interactive for complex decisions, autonomous for simple routing
5. **Error Recovery**: Implement termination conditions for stuck conversations
6. **Tool Safety**: Ensure tools are idempotent and safe to call autonomously
