# Sequential Orchestration — Linear Agent Pipelines

## Overview

Agents execute one after another in order. Each agent sees the full conversation history including all previous agents' responses. Like an assembly line.

```
Agent A → Agent B → Agent C → Final Output
```

## When to Use

- Content creation pipelines (writer → reviewer → editor)
- Multi-stage processing (extract → transform → validate)
- Refinement chains (draft → feedback → revision)
- Validation pipelines (analyze → verify → approve)

## Implementation

### Basic Setup

```python
from agent_framework.orchestrations import SequentialBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

# Create agents
writer = chat_client.as_agent(
    instructions="You are a professional copywriter. Write compelling taglines.",
    description="Professional copywriter",
    name="writer",
)

reviewer = chat_client.as_agent(
    instructions="You review copy for clarity and effectiveness. Provide constructive feedback.",
    description="Copy reviewer",
    name="reviewer",
)

# Build: writer → reviewer
workflow = SequentialBuilder(participants=[writer, reviewer]).build()
```

## Running

### Streaming Execution

```python
from agent_framework import Message, WorkflowEvent

output_evt: WorkflowEvent | None = None
async for event in workflow.run_stream("Write a tagline for a budget-friendly eBike."):
    if event.type == "output":
        output_evt = event

if output_evt:
    print("===== Final Conversation =====")
    messages: list[Message] = output_evt.data
    for i, msg in enumerate(messages, start=1):
        name = msg.author_name or ("assistant" if msg.role == "assistant" else "user")
        print(f"{i:02d} [{name}]: {msg.text}")
```

### Non-Streaming Execution

```python
messages = [Message(role="user", contents=["Write a tagline for a budget-friendly eBike."])]

response = await workflow.run(messages)

for message in response.messages:
    name = message.author_name or "assistant"
    print(f"[{name}]: {message.text}")
```

## SequentialBuilder API

### Constructor

```python
SequentialBuilder(
    participants: list[Agent],  # Execution order
    name: str | None = None,    # Optional workflow name
)
```

### Builder Methods

| Method | Parameters | Description |
|--------|-----------|---|
| `.participants()` | `agents: list[Agent]` | Set or add agents to execute in sequence |
| `.with_request_info()` | `enabled: bool = True` | Enable human-in-the-loop requests during execution |
| `.with_checkpointing()` | `manager: CheckpointManager` | Enable state persistence across restarts |
| `.build()` | | Build and return the executable workflow |

### Example with All Options

```python
from agent_framework.orchestrations import SequentialBuilder
from agent_framework.checkpointing import CheckpointManager

# Build with all configuration options
workflow = (
    SequentialBuilder(
        participants=[agent_a, agent_b, agent_c],
        name="content_processing"
    )
    .with_request_info(enabled=True)  # Allow human input during execution
    .with_checkpointing(checkpoint_manager)  # Save state for resumption
    .build()
)
```

## Workflow as Agent

Wrap the sequential workflow as a reusable agent:

```python
# Convert the workflow to an agent
workflow_agent = workflow.as_agent(name="Sequential Pipeline Agent")

# Create a session
session = await workflow_agent.create_session()

# Run as a regular agent
messages = [Message(role="user", contents=["Your input here"])]

async for update in workflow_agent.run(messages, session=session, stream=True):
    if update.text:
        print(update.text, end="", flush=True)
```

### as_agent Parameters

| Parameter | Type | Description |
|-----------|------|---|
| `name` | `str \| None` | Optional display name for the agent |

## Context Flow and Message Passing

Context flows sequentially through the pipeline:

```
User Input
    ↓
Agent A (receives: [user_message])
    ↓ (adds its response to conversation)
Agent B (receives: [user_message, agent_a_response])
    ↓ (adds its response to conversation)
Agent C (receives: [user_message, agent_a_response, agent_b_response])
    ↓
Final Output (all messages in order)
```

Each agent:
1. Receives complete conversation history up to that point
2. Generates a response based on all previous context
3. Response added to shared conversation
4. Next agent receives updated conversation

## Request Info / Human-in-the-Loop

Enable pausing for human approval at any agent:

```python
workflow = (
    SequentialBuilder(participants=[agent_a, agent_b, agent_c])
    .with_request_info(enabled=True)
    .build()
)

pending_requests = []
output_event = None

async for event in workflow.run_stream("Your task"):
    if event.type == "request_info":
        # An agent has paused and requested human input
        pending_requests.append(event)
        print(f"Agent {event.executor_id} is awaiting your input")

        # Agent's last message
        request_data = event.data
        if hasattr(request_data, 'messages'):
            for msg in request_data.messages[-2:]:
                print(f"  {msg.author_name}: {msg.text}")

    elif event.type == "output":
        output_event = event

# Handle requests interactively
while pending_requests:
    user_input = input("Your response: ")

    # Send response(s) to resume
    responses = {
        req.request_id: req.data.create_response(user_input)
        for req in pending_requests
    }

    pending_requests = []
    async for event in workflow.run(responses=responses):
        if event.type == "request_info":
            pending_requests.append(event)
        elif event.type == "output":
            output_event = event
```

## Checkpointing and Resumption

Save and resume workflow state:

```python
from agent_framework.checkpointing import CheckpointManager, FileCheckpointStorage

# Create checkpoint manager
storage = FileCheckpointStorage("./checkpoints")
checkpoint_manager = CheckpointManager(storage)

# Build with checkpointing
workflow = (
    SequentialBuilder(participants=[agent_a, agent_b, agent_c])
    .with_checkpointing(checkpoint_manager)
    .build()
)

# Run and automatically save checkpoints
session = await workflow_agent.create_session()
messages = [Message(role="user", contents=["Your task"])]

# If interrupted, the session can be resumed
async for update in workflow_agent.run(messages, session=session, stream=True):
    if update.text:
        print(update.text, end="", flush=True)

# Later: resume the same session
resumed_session = session  # Or load from storage
async for update in workflow_agent.run([], session=resumed_session, stream=True):
    if update.text:
        print(update.text, end="", flush=True)
```

## Three-Stage Content Pipeline Example

Complete example: research → write → edit

```python
from agent_framework.orchestrations import SequentialBuilder
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework import Message
from azure.identity import AzureCliCredential

async def main():
    chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

    researcher = chat_client.as_agent(
        instructions="Research the topic. Provide key facts, statistics, and sources.",
        description="Research analyst",
        name="researcher",
    )

    writer = chat_client.as_agent(
        instructions="Write a compelling article based on the research provided.",
        description="Article writer",
        name="writer",
    )

    editor = chat_client.as_agent(
        instructions="Edit for clarity, grammar, and readability. Output final version.",
        description="Editor",
        name="editor",
    )

    # Build sequential pipeline
    pipeline = SequentialBuilder(
        participants=[researcher, writer, editor],
        name="content_creation"
    ).build()

    # Convert to agent
    pipeline_agent = pipeline.as_agent(name="Content Creation Pipeline")

    # Run
    session = await pipeline_agent.create_session()
    messages = [Message(role="user", contents=["The impact of AI on healthcare"])]

    print("Starting content pipeline...\n")

    current_author = None
    async for update in pipeline_agent.run(messages, session=session, stream=True):
        # Show author changes
        if update.author_name and update.author_name != current_author:
            if current_author:
                print("\n" + "-" * 50)
            print(f"\n[{update.author_name}]:")
            current_author = update.author_name

        if update.text:
            print(update.text, end="", flush=True)

    print("\n" + "=" * 50)
    print("Content pipeline completed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Event Streaming

Sequential workflows emit events for observability:

```python
from agent_framework import WorkflowEvent

async for event in workflow.run_stream("task"):
    # Event types:
    # - "output": Agent produced output (AgentResponseUpdate or final messages)
    # - "request_info": Agent paused for human input
    # - "execution_start": Workflow/agent started
    # - "execution_end": Workflow/agent completed

    if event.type == "output":
        if hasattr(event.data, 'text'):
            # AgentResponseUpdate (streaming)
            print(event.data.text, end="", flush=True)
        else:
            # Final output (list[Message])
            for msg in event.data:
                print(f"[{msg.author_name}]: {msg.text}")

    elif event.type == "request_info":
        print(f"\nPending input for {event.executor_id}")
```

## Key Characteristics

| Feature | Detail |
|---|---|
| **Shared Context** | Each agent sees ALL previous messages |
| **Ordered** | Strictly follows `participants` list order |
| **Cumulative** | Later agents build on earlier responses |
| **Deterministic** | No branching or conditional routing |
| **Linear** | One agent active at a time |
| **Composable** | Can be wrapped as an agent and used in other workflows |

## Configuration Summary

| Method | Required | Description |
|---|:-:|---|
| `SequentialBuilder()` | ✅ | Initialize with participants list |
| `.with_request_info()` | ❌ | Enable human-in-the-loop pauses |
| `.with_checkpointing()` | ❌ | Enable state persistence |
| `.build()` | ✅ | Create executable workflow |
| `.as_agent()` | ❌ | Wrap as reusable agent |

## Best Practices

1. **Clear Instructions**: Each agent's instructions should be specific about their role in the pipeline
2. **Output Format**: Earlier agents should produce output that later agents can easily parse
3. **Error Handling**: Use request_info to allow recovery from errors
4. **Checkpointing**: Enable for long-running pipelines that might be interrupted
5. **Agent Composition**: Use as_agent() to build higher-level workflows from simpler ones
