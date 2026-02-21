# Magentic Orchestration — Dynamic Manager-Driven Coordination

## Overview

A dedicated manager agent dynamically coordinates a team of specialists. The manager creates a plan, selects which agent should act next based on evolving context, tracks progress, detects stalls, and can replan. Based on Microsoft's AutoGen Magentic-One system.

This is the most powerful and flexible orchestration pattern for complex, open-ended problems.

## Execution Flow

```
1. Planning Phase      → Manager creates initial plan
2. Plan Review         → (Optional) Human reviews/approves plan
3. Agent Selection     → Manager picks best agent for next subtask
4. Execution           → Selected agent executes
5. Progress Assessment → Manager evaluates what was accomplished
6. Stall Detection     → If no progress, auto-replan
7. Iterate             → Repeat 3-6 until done or limits reached
8. Final Synthesis     → Manager combines all outputs
```

## When to Use

- Complex, open-ended problems with unclear solution path
- Tasks requiring dynamic agent selection
- Research and documentation workflows
- Iterative solution refinement
- Tasks where you don't know the order of steps upfront
- Situations requiring human oversight of strategy
- Multi-stage projects that might need replanning

## Implementation

### Basic Setup

```python
from agent_framework.orchestrations import MagenticBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

research_agent = chat_client.as_agent(
    instructions="You are a research specialist. Gather and analyze information.",
    description="Research specialist",
    name="research_agent",
)

writer_agent = chat_client.as_agent(
    instructions="You are a technical writer. Create clear documentation.",
    description="Technical writer",
    name="writer_agent",
)

editor_agent = chat_client.as_agent(
    instructions="You are an editor. Review and refine content.",
    description="Editor",
    name="editor_agent",
)

# Basic setup with default manager
workflow = MagenticBuilder(
    name="research_documentation",
    participants=[research_agent, writer_agent, editor_agent],
).build()
```

## MagenticBuilder API

### Constructor

```python
MagenticBuilder(
    name: str,                      # Workflow name
    participants: list[Agent],      # Specialist agents
)
```

### Builder Methods

| Method | Parameters | Description |
|--------|-----------|---|
| `.with_plan_review()` | | Enable human plan review before execution |
| `.with_standard_manager()` | config | Use built-in manager with options |
| `.with_max_iterations()` | `count: int` | Maximum agent selections (safety limit) |
| `.with_stall_detection_threshold()` | `count: int` | Replan after N non-productive steps |
| `.with_checkpointing()` | `manager: CheckpointManager` | Enable state persistence |
| `.build()` | | Create executable workflow |

### Full Configuration Example

```python
workflow = (
    MagenticBuilder(
        name="complex_project",
        participants=[research_agent, writer_agent, editor_agent, designer_agent],
    )
    .with_plan_review()                    # Enable human plan approval
    .with_max_iterations(20)               # Safety limit
    .with_stall_detection_threshold(3)     # Replan after 3 non-productive steps
    .with_checkpointing(checkpoint_manager)  # Persist state
    .build()
)
```

## Running with Event Streaming

```python
from agent_framework import AgentResponseUpdate

output_event = None
last_message_id = None

async for event in workflow.run_stream("Research and document Python async/await patterns"):
    if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
        # Stream text updates in real-time
        message_id = event.data.message_id
        if message_id != last_message_id:
            if last_message_id is not None:
                print("\n")
            print(f"- {event.executor_id}:", end=" ", flush=True)
            last_message_id = message_id
        print(event.data, end="", flush=True)
    elif event.type == "output":
        # Final output
        output_event = event

if output_event:
    print(f"\n\nFinal Result: {output_event.data}")
```

## Human-in-the-Loop Plan Review

The most distinctive feature of Magentic — humans can review and approve/revise the manager's plan before execution.

### Enable Plan Review

```python
workflow = (
    MagenticBuilder(
        name="reviewed_magentic",
        participants=[research_agent, writer_agent, editor_agent],
    )
    .with_plan_review()  # Enable plan review requests
    .build()
)
```

### Handle Plan Review Requests

```python
import asyncio
import json
from typing import cast
from agent_framework.orchestrations import MagenticPlanReviewRequest

pending_request = None
pending_responses = None
output_event = None
task = "Research and write documentation for Python async/await patterns"

while not output_event:
    if pending_responses is not None:
        # Resume with human feedback
        stream = workflow.run(responses=pending_responses)
    else:
        # Start fresh
        stream = workflow.run_stream(task)

    async for event in stream:
        if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
            # Stream agent output
            print(event.data, end="", flush=True)
        elif event.type == "request_info":
            # Manager requests plan review
            if event.request_type is MagenticPlanReviewRequest:
                pending_request = event
        elif event.type == "output":
            # Workflow completed
            output_event = event
            pending_responses = None

    # Handle plan review
    if pending_request is not None:
        event_data = cast(MagenticPlanReviewRequest, pending_request.data)

        print("\n\n[Manager's Plan Review Request]")

        # Show current progress if available
        if event_data.current_progress is not None:
            print("\nCurrent Progress Ledger:")
            progress_dict = event_data.current_progress.to_dict()
            print(json.dumps(progress_dict, indent=2))

        # Show proposed plan
        print(f"\nProposed Plan:\n{event_data.plan.text}")

        # Get human feedback
        print("\nFeedback (press Enter to approve, or enter revision request):")
        reply = await asyncio.get_event_loop().run_in_executor(None, input, "> ")

        if reply.strip() == "":
            # Approve plan as-is
            print("Plan approved. Proceeding with execution...\n")
            pending_responses = {pending_request.request_id: event_data.approve()}
        else:
            # Request revision
            print("Plan revision requested. Manager will revise...\n")
            pending_responses = {pending_request.request_id: event_data.revise(reply)}

        pending_request = None
```

## MagenticPlanReviewRequest API

```python
from agent_framework.orchestrations import MagenticPlanReviewRequest

# Inside event handler
event_data = cast(MagenticPlanReviewRequest, event.data)

# Access properties
plan_text = event_data.plan.text                    # The manager's proposed plan
progress = event_data.current_progress              # Progress ledger (ProgressLedger or None)

# Create responses
approval_response = event_data.approve()            # Accept plan as-is
revision_response = event_data.revise(feedback)    # Request revision with feedback

# Progress ledger access
if progress:
    progress_dict = progress.to_dict()              # Convert to dict for display
    completed = progress.completed_tasks            # List of completed steps
    remaining = progress.pending_tasks              # List of pending steps
```

## Progress Ledger

Track what the manager has accomplished:

```python
class ProgressLedger:
    """Tracks plan progress and agent actions."""

    completed_tasks: list[str]      # Tasks that have been completed
    pending_tasks: list[str]        # Tasks still to do
    in_progress: str | None         # Current task being worked on
    agent_actions: dict[str, list]  # Actions taken by each agent

    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "completed": self.completed_tasks,
            "pending": self.pending_tasks,
            "in_progress": self.in_progress,
            "agent_actions": self.agent_actions,
        }

# Display progress in plan review
if event_data.current_progress:
    print("Progress Ledger:")
    for task in event_data.current_progress.completed_tasks:
        print(f"  ✓ {task}")
    for task in event_data.current_progress.pending_tasks:
        print(f"  - {task}")
    if event_data.current_progress.in_progress:
        print(f"  → {event_data.current_progress.in_progress}")
```

## Standard Manager Configuration

Use the built-in manager with options:

```python
from agent_framework.orchestrations import StandardMagenticManager

# Option 1: Basic configuration
workflow = (
    MagenticBuilder(participants=[agent_a, agent_b, agent_c])
    .with_standard_manager(
        chat_client=chat_client,
        max_round_count=10,      # Maximum iterations
        max_stall_count=3        # Replan after N non-productive rounds
    )
    .build()
)

# Option 2: With plan review
workflow = (
    MagenticBuilder(participants=[agent_a, agent_b, agent_c])
    .with_standard_manager(
        chat_client=chat_client,
        max_round_count=15,
        max_stall_count=2,
        enable_plan_review=True
    )
    .build()
)
```

### StandardMagenticManager Parameters

| Parameter | Type | Description |
|-----------|------|---|
| `chat_client` | ChatClient | LLM client for manager's planning |
| `max_round_count` | int | Maximum agent selections |
| `max_stall_count` | int | Stall threshold before replanning |
| `enable_plan_review` | bool | Allow human plan review |

## Stall Detection and Auto-Replanning

Automatically detect when no progress is being made and trigger replanning:

```python
# Replan after 3 consecutive non-productive steps
workflow = (
    MagenticBuilder(name="stall_aware", participants=[...])
    .with_stall_detection_threshold(3)
    .build()
)

# During execution:
# Step 1: Agent A selected, makes progress
# Step 2: Agent B selected, makes progress
# Step 3: Agent C selected, NO PROGRESS (stall count = 1)
# Step 4: Agent A selected, NO PROGRESS (stall count = 2)
# Step 5: Agent B selected, NO PROGRESS (stall count = 3) ← TRIGGER REPLAN
# Step 6: Manager revises plan
# Step 7: Continue with revised plan
```

## Combined Configuration Example

All features together:

```python
from agent_framework.orchestrations import MagenticBuilder

# Fully configured Magentic workflow
workflow = (
    MagenticBuilder(
        name="comprehensive_project",
        participants=[
            researcher,
            writer,
            editor,
            designer,
        ],
    )
    .with_plan_review()                    # Human oversight on plans
    .with_standard_manager(
        chat_client=chat_client,
        max_round_count=20,                # Safety limit
        max_stall_count=3,                 # Auto-replan threshold
        enable_plan_review=True
    )
    .with_checkpointing(checkpoint_manager)  # Persist state
    .build()
)
```

## Complete Example with Plan Review

End-to-end example with human-in-the-loop planning:

```python
import asyncio
import json
from typing import cast
from agent_framework.orchestrations import MagenticBuilder, MagenticPlanReviewRequest
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework import AgentResponseUpdate, Message
from azure.identity import AzureCliCredential

async def main():
    chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

    researcher = chat_client.as_agent(
        instructions="Research topics thoroughly. Provide verified facts and sources.",
        description="Research specialist",
        name="researcher",
    )

    writer = chat_client.as_agent(
        instructions="Write clear, well-structured technical documentation.",
        description="Technical writer",
        name="writer",
    )

    reviewer = chat_client.as_agent(
        instructions="Review for accuracy, clarity, and completeness.",
        description="Content reviewer",
        name="reviewer",
    )

    # Build with plan review
    workflow = (
        MagenticBuilder(
            name="doc_creation",
            participants=[researcher, writer, reviewer],
        )
        .with_plan_review()
        .build()
    )

    task = "Research and document Rust's ownership system for beginners"
    print(f"Task: {task}\n")
    print("=" * 70)

    pending_request = None
    pending_responses = None
    output_event = None

    while not output_event:
        if pending_responses is not None:
            stream = workflow.run(responses=pending_responses)
        else:
            stream = workflow.run_stream(task)

        async for event in stream:
            if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
                # Stream agent output
                print(event.data.text, end="", flush=True)
            elif event.type == "request_info":
                if isinstance(event.data, MagenticPlanReviewRequest):
                    pending_request = event
            elif event.type == "output":
                output_event = event
                pending_responses = None

        # Handle plan review
        if pending_request is not None:
            event_data = cast(MagenticPlanReviewRequest, pending_request.data)

            print("\n\n" + "=" * 70)
            print("[MANAGER'S PLAN REQUIRES REVIEW]")
            print("=" * 70)

            # Show progress
            if event_data.current_progress:
                print("\nProgress so far:")
                progress = event_data.current_progress.to_dict()
                if progress.get("completed"):
                    print("  Completed:")
                    for task in progress["completed"]:
                        print(f"    ✓ {task}")
                if progress.get("pending"):
                    print("  Still to do:")
                    for task in progress["pending"]:
                        print(f"    - {task}")

            # Show plan
            print(f"\nProposed Plan:\n{event_data.plan.text}")

            # Get feedback
            print("\nOptions:")
            print("  1. Press Enter to approve")
            print("  2. Type feedback to request revision")

            reply = await asyncio.get_event_loop().run_in_executor(None, input, "\n> ")

            if reply.strip() == "":
                print("\nApproved! Proceeding with execution...")
                pending_responses = {pending_request.request_id: event_data.approve()}
            else:
                print(f"\nFeedback sent: {reply}")
                pending_responses = {pending_request.request_id: event_data.revise(reply)}

            pending_request = None

    print("\n" + "=" * 70)
    print("Documentation complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Workflow as Agent

Wrap Magentic workflow as a reusable agent:

```python
# Convert to agent
workflow_agent = workflow.as_agent(name="Magentic Coordinator Agent")

# Create session
session = await workflow_agent.create_session()

# Run as agent
messages = [Message(role="user", contents=["Your complex task"])]

async for update in workflow_agent.run(messages, session=session, stream=True):
    if update.text:
        print(update.text, end="", flush=True)
```

## Key Characteristics

| Feature | Detail |
|---|---|
| **Dynamic Selection** | Manager picks agent based on context and progress |
| **Planning** | Initial plan created, can be revised |
| **Progress Tracking** | Ledger of what's been accomplished |
| **Stall Detection** | Auto-replan when progress stalls |
| **Human Oversight** | Optional plan review and approval |
| **Flexible Order** | Any agent can be called multiple times in any order |
| **Auto-Replanning** | Manager creates new plan when stuck |
| **Synthesis** | Manager combines all agent outputs at the end |

## Configuration Summary

| Method | Required | Description |
|---|:-:|---|
| `MagenticBuilder()` | ✅ | Initialize with name and participants |
| `.with_plan_review()` | ❌ | Enable human plan review |
| `.with_standard_manager()` | ❌ | Configure built-in manager |
| `.with_max_iterations()` | ❌ | Limit total agent selections |
| `.with_stall_detection_threshold()` | ❌ | Trigger replan after N non-productive steps |
| `.with_checkpointing()` | ❌ | Enable state persistence |
| `.build()` | ✅ | Create executable workflow |

## When Magentic vs Other Patterns

| Requirement | Use |
|---|---|
| Known steps, fixed order | Sequential |
| Independent parallel analysis | Concurrent |
| Dynamic routing, customer support | Handoff |
| Discussion, consensus | Group Chat |
| Complex open-ended, flexible coordination | **Magentic** |
| Don't know steps upfront | **Magentic** |
| Need plan review by humans | **Magentic** |
| Adaptive replanning needed | **Magentic** |

## Best Practices

1. **Specialist Agents**: Each agent should have clear, focused expertise
2. **Plan Review**: Use with_plan_review() for complex tasks with stakes
3. **Stall Threshold**: Set based on task complexity (lower = more aggressive replanning)
4. **Max Iterations**: Set safety limit to prevent infinite loops
5. **Clear Instructions**: Ensure each agent understands its role and constraints
6. **Progress Tracking**: Monitor the progress ledger to understand workflow behavior
7. **Checkpointing**: Enable for long-running tasks
