# Group Chat Orchestration — Collaborative Multi-Agent Discussion

## Overview

Multiple agents collaborate in a shared conversation with iterative turns. A manager controls who speaks next and when the conversation ends. All agents see the full message history.

```
Manager selects speaker order:
  Turn 1: Writer speaks → all see it
  Turn 2: Reviewer speaks → all see it
  Turn 3: Writer responds → all see it
  ...until max_turns or manager terminates
```

## When to Use

- Collaborative brainstorming
- Debate and discussion simulations
- Panel discussions with multiple experts
- Consensus building
- Multi-perspective problem solving
- Iterative refinement through back-and-forth
- Decision-making with diverse viewpoints

## Implementation

### Basic Setup with Round-Robin Manager

```python
from agent_framework.orchestrations import GroupChatBuilder
from agent_framework.orchestrations.group_chat import RoundRobinGroupChatManager
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

writer = chat_client.as_agent(
    instructions="You are a creative copywriter. Suggest compelling narratives.",
    description="Creative copywriter",
    name="writer",
)

reviewer = chat_client.as_agent(
    instructions="You are a critical reviewer. Evaluate ideas objectively.",
    description="Content reviewer",
    name="reviewer",
)

# Build with round-robin turn management
workflow = (
    GroupChatBuilder(
        manager_factory=lambda agents: RoundRobinGroupChatManager(
            agents,
            max_turns=5,  # Maximum conversation turns
        )
    )
    .participants([writer, reviewer])
    .build()
)
```

## Running

### Streaming Execution

```python
from agent_framework import Message, WorkflowOutputEvent

messages = [Message(role="user", contents=["Create a tagline for an eco-friendly vehicle"])]

output_evt = None
async for event in workflow.run_stream(messages):
    if isinstance(event, WorkflowOutputEvent) or event.type == "output":
        output_evt = event
        if hasattr(event.data, 'text'):
            # Streaming update
            print(event.data.text, end="", flush=True)

if output_evt and not hasattr(output_evt.data, 'text'):
    # Final output
    for msg in output_evt.data:
        print(f"\n[{msg.author_name}]: {msg.text}")
```

### Non-Streaming Execution

```python
response = await workflow.run(messages)

for msg in response.messages:
    print(f"[{msg.author_name}]: {msg.text}")
```

## GroupChatBuilder API

### Constructor

```python
GroupChatBuilder(
    manager_factory: callable,  # Function that creates a GroupChatManager
    name: str | None = None,    # Optional workflow name
)
```

Manager factory signature:

```python
def manager_factory(agents: list[Agent]) -> GroupChatManager:
    """Return a GroupChatManager instance."""
    pass
```

### Builder Methods

| Method | Parameters | Description |
|--------|-----------|---|
| `.participants()` | `agents: list[Agent]` | Agents participating in the group chat |
| `.set_select_speakers_func()` | `func: callable` | Custom speaker selection function |
| `.set_manager()` | `manager: GroupChatManager` | Use a specific manager instance |
| `.with_request_info()` | `enabled: bool = True` | Enable mid-conversation human feedback |
| `.with_max_rounds()` | `max_rounds: int` | Maximum discussion rounds |
| `.with_checkpointing()` | `manager: CheckpointManager` | Enable state persistence |
| `.build()` | | Create executable workflow |

## Manager Types

### RoundRobinGroupChatManager

Default manager — agents take turns in cyclic order:

```python
from agent_framework.orchestrations.group_chat import RoundRobinGroupChatManager

manager = RoundRobinGroupChatManager(
    agents=[agent_a, agent_b, agent_c],
    max_turns=5,  # Maximum total turns
)

workflow = GroupChatBuilder(
    manager_factory=lambda agents: RoundRobinGroupChatManager(agents, max_turns=5)
).participants([agent_a, agent_b, agent_c]).build()
```

Turn order: Agent A → Agent B → Agent C → Agent A → Agent B → ...

### Custom Manager — Context-Aware Selection

Select next speaker based on conversation content:

```python
from agent_framework.orchestrations.group_chat import GroupChatManager
from agent_framework import Message
from typing import Optional

class ContextAwareGroupChatManager(GroupChatManager):
    """Selects next speaker based on conversation content."""

    async def select_next_speaker(
        self,
        messages: list[Message]
    ) -> Optional[str]:
        """
        Return the name of the agent who should speak next.
        Return None to end the conversation.
        """
        if not messages:
            # Start with first agent
            return self.agents[0].name

        last_message = messages[-1].text.lower()

        # If last message asks for feedback, call reviewer
        if "feedback" in last_message or "review" in last_message:
            return "reviewer"

        # If last message is a critique, call writer to improve
        if "suggestion" in last_message or "improvement" in last_message:
            return "writer"

        # Default: round-robin
        turn_index = (len(messages) + 1) % len(self.agents)
        return self.agents[turn_index].name

# Use custom manager
workflow = (
    GroupChatBuilder(
        manager_factory=lambda agents: ContextAwareGroupChatManager(agents, max_turns=8)
    )
    .participants([writer, reviewer])
    .build()
)
```

### Custom Manager — LLM-Based Selection

Use an LLM agent to decide who speaks next:

```python
class LLMGroupChatManager(GroupChatManager):
    """Uses an LLM to decide who speaks next."""

    def __init__(self, agents: list, chat_client, max_turns: int = 10):
        super().__init__(agents, max_turns=max_turns)
        self.chat_client = chat_client

    async def select_next_speaker(
        self,
        messages: list[Message]
    ) -> Optional[str]:
        """Ask LLM who should speak next."""
        agent_names = [a.name for a in self.agents]

        # Build conversation summary
        recent = messages[-5:] if messages else []
        conversation = "\n".join(
            f"{m.author_name}: {m.text[:100]}"
            for m in recent
        )

        prompt = f"""Given this conversation, who should speak next?

Available agents: {', '.join(agent_names)}

Recent conversation:
{conversation}

Reply with ONLY the agent name (no explanation):"""

        from agent_framework import Message as ChatMessage

        result = await self.chat_client.complete_async(prompt)
        chosen = result.text.strip()

        # Validate and return
        return chosen if chosen in agent_names else agent_names[0]

# Use LLM-based manager
workflow = (
    GroupChatBuilder(
        manager_factory=lambda agents: LLMGroupChatManager(agents, chat_client, max_turns=10)
    )
    .participants([writer, reviewer, editor])
    .build()
)
```

## GroupChatContext

Access group chat state information:

```python
class GroupChatContext:
    """Information about the group chat conversation."""

    messages: list[Message]      # All messages in conversation
    agents: list[Agent]          # Participating agents
    current_turn: int            # Current turn number
    max_turns: int               # Maximum turns allowed

    def get_agent(self, name: str) -> Agent | None:
        """Get agent by name."""
        pass

    def get_speaker_count(self, agent_name: str) -> int:
        """Count how many times an agent has spoken."""
        pass
```

## Set Custom Speaker Selection Function

Alternative to custom manager classes — provide a simple function:

```python
async def smart_speaker_selection(messages: list[Message], agents: list) -> str:
    """Select next speaker based on message content."""
    if not messages:
        return agents[0].name

    last_message = messages[-1].text.lower()

    # Check for specific keywords
    if "budget" in last_message or "cost" in last_message:
        return "finance_agent"
    elif "design" in last_message or "look" in last_message:
        return "designer_agent"
    else:
        # Default round-robin
        return agents[len(messages) % len(agents)].name

workflow = (
    GroupChatBuilder(
        manager_factory=lambda agents: RoundRobinGroupChatManager(agents)
    )
    .participants([writer, designer, finance])
    .set_select_speakers_func(smart_speaker_selection)
    .build()
)
```

## Set Specific Manager Instance

Provide an already-configured manager:

```python
custom_manager = CustomGroupChatManager(
    agents=[writer, reviewer],
    max_turns=10,
    custom_config={"debate_mode": True}
)

workflow = (
    GroupChatBuilder(manager_factory=lambda _: custom_manager)
    .participants([writer, reviewer])
    .set_manager(custom_manager)
    .build()
)
```

## Mid-Conversation Human Feedback

Pause the discussion for human input:

```python
workflow = (
    GroupChatBuilder(
        manager_factory=lambda agents: RoundRobinGroupChatManager(agents, max_turns=10)
    )
    .participants([writer, reviewer, editor])
    .with_request_info(enabled=True)  # Allow pausing for feedback
    .build()
)

pending_requests = []
async for event in workflow.run_stream("Should we redesign our homepage?"):
    if event.type == "request_info":
        pending_requests.append(event)
        print(f"\nHuman feedback requested during discussion")
        print(f"Current speakers: {[a.name for a in workflow.agents]}")

    elif event.type == "output":
        if hasattr(event.data, 'text'):
            print(event.data.text, end="", flush=True)

# Provide feedback to continue
while pending_requests:
    feedback = input("\nYour feedback: ")

    responses = {
        req.request_id: feedback
        for req in pending_requests
    }

    async for event in workflow.run(responses=responses):
        # Continue processing...
        pass
```

## Maximum Rounds Configuration

```python
workflow = (
    GroupChatBuilder(
        manager_factory=lambda agents: RoundRobinGroupChatManager(agents, max_turns=10)
    )
    .participants([agent_a, agent_b, agent_c])
    .with_max_rounds(15)  # Alternative: set max_rounds via builder
    .build()
)
```

## Workflow as Agent

Wrap group chat as a reusable agent:

```python
# Convert to agent
workflow_agent = workflow.as_agent(name="Panel Discussion Agent")

# Create session
session = await workflow_agent.create_session()

# Run as agent
messages = [Message(role="user", contents=["Discuss the future of remote work"])]

current_author = None
async for update in workflow_agent.run(messages, session=session, stream=True):
    # Show speaker changes
    if update.author_name and update.author_name != current_author:
        if current_author:
            print("\n" + "-" * 40)
        print(f"\n[{update.author_name}]:")
        current_author = update.author_name

    if update.text:
        print(update.text, end="", flush=True)

print("\n" + "=" * 40)
```

## Multi-Expert Panel Example

Complete example: engineer, designer, PM discussing product feature:

```python
from agent_framework.orchestrations import GroupChatBuilder
from agent_framework.orchestrations.group_chat import RoundRobinGroupChatManager
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework import Message
from azure.identity import AzureCliCredential

async def main():
    chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

    engineer = chat_client.as_agent(
        instructions="Think about technical feasibility, implementation details, and scalability.",
        description="Software engineer",
        name="engineer",
    )

    designer = chat_client.as_agent(
        instructions="Think about user experience, visual design, and usability.",
        description="UX designer",
        name="designer",
    )

    pm = chat_client.as_agent(
        instructions="Think about business value, timeline, prioritization, and resources.",
        description="Product manager",
        name="pm",
    )

    # Build group chat with round-robin
    panel = (
        GroupChatBuilder(
            manager_factory=lambda agents: RoundRobinGroupChatManager(agents, max_turns=9)
        )
        .participants([engineer, designer, pm])
        .build()
    )

    # Run discussion
    topic = "Should we add AI-powered search to our product?"
    messages = [Message(role="user", contents=[topic])]

    print(f"Topic: {topic}\n")
    print("=" * 60)

    async for event in panel.run_stream(messages):
        if event.type == "output":
            if hasattr(event.data, 'text'):
                print(event.data.text, end="", flush=True)
            elif isinstance(event.data, list):
                for msg in event.data:
                    print(f"\n[{msg.author_name}]: {msg.text}\n")

    print("\n" + "=" * 60)
    print("Panel discussion completed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Key Characteristics

| Feature | Detail |
|---|---|
| **Shared History** | All agents see full conversation |
| **Turn-Based** | One agent speaks at a time |
| **Manager-Driven** | Manager controls turn order and termination |
| **Iterative** | Multiple rounds of back-and-forth |
| **Not Parallel** | Agents speak sequentially (use Concurrent for parallel) |
| **Flexible Selection** | Built-in and custom manager implementations |
| **Context-Aware** | Can make speaker decisions based on conversation content |

## Configuration Summary

| Method | Required | Description |
|---|:-:|---|
| `GroupChatBuilder()` | ✅ | Initialize with manager_factory |
| `.participants()` | ✅ | List of agents in the group chat |
| `.set_select_speakers_func()` | ❌ | Custom speaker selection logic |
| `.set_manager()` | ❌ | Provide specific manager instance |
| `.with_request_info()` | ❌ | Enable mid-conversation pauses |
| `.with_max_rounds()` | ❌ | Set maximum discussion rounds |
| `.with_checkpointing()` | ❌ | Enable state persistence |
| `.build()` | ✅ | Create executable workflow |

## Best Practices

1. **Clear Roles**: Each agent should have distinct expertise/perspective
2. **Turn Limit**: Always set max_turns to prevent infinite loops
3. **Manager Choice**:
   - Use RoundRobinGroupChatManager for balanced discussion
   - Use context-aware for topic-specific routing
   - Use LLM-based for complex decision-making
4. **Instructions**: Frame instructions to encourage discussion and disagreement
5. **Observation**: Monitor output to understand agent dynamics
6. **Iteration**: Adjust manager logic based on discussion quality
