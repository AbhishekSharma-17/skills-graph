# Concurrent Orchestration — Parallel Agent Execution

## Overview

All agents run simultaneously with the same input. Results are aggregated into a single output — either as a combined message list or via a custom aggregator function.

```
         → Agent A →
Input ──→ Agent B →── Aggregator → Output
         → Agent C →
```

## When to Use

- Multiple expert perspectives on same question
- Market research from different angles
- Risk assessment (concurrent evaluations)
- A/B content generation
- Parallel analysis (legal + financial + technical)
- Consensus building from specialized viewpoints

## Implementation

### Basic Setup

```python
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

researcher = chat_client.as_agent(
    instructions="You are a research analyst. Provide market research insights.",
    description="Market research analyst",
    name="researcher",
)

marketer = chat_client.as_agent(
    instructions="You are a marketing strategist. Develop marketing angles.",
    description="Marketing strategist",
    name="marketer",
)

legal = chat_client.as_agent(
    instructions="You are a legal expert. Identify legal considerations.",
    description="Legal expert",
    name="legal",
)

# All three run in parallel with same input
workflow = ConcurrentBuilder(
    participants=[researcher, marketer, legal]
).build()
```

## Running

### Streaming Execution

```python
from agent_framework import Message, WorkflowOutputEvent

messages = [Message(role="user", contents=["We are launching a new budget-friendly electric bike."])]

output_evt = None
async for event in workflow.run_stream(messages):
    if isinstance(event, WorkflowOutputEvent) or event.type == "output":
        output_evt = event

if output_evt:
    # All agents' responses combined
    messages = output_evt.data
    for i, msg in enumerate(messages, start=1):
        name = msg.author_name or "expert"
        print(f"{i}. [{name}]: {msg.text[:200]}...")
```

### Non-Streaming Execution

```python
response = await workflow.run(messages)

for msg in response.messages:
    print(f"[{msg.author_name}]: {msg.text}")
```

## ConcurrentBuilder API

### Constructor

```python
ConcurrentBuilder(
    name: str | None = None,  # Optional workflow name
)
```

### Builder Methods

| Method | Parameters | Description |
|--------|-----------|---|
| `.participants()` | `agents: list[Agent]` | Set agents to run in parallel |
| `.with_aggregator()` | `func: callable` | Custom aggregation function |
| `.with_request_info()` | `enabled: bool = True` | Enable human-in-the-loop requests |
| `.with_checkpointing()` | `manager: CheckpointManager` | Enable state persistence |
| `.build()` | | Build and return the executable workflow |

### Example with All Options

```python
from agent_framework.orchestrations import ConcurrentBuilder

workflow = (
    ConcurrentBuilder(name="parallel_analysis")
    .participants([researcher, marketer, legal])
    .with_aggregator(custom_aggregator_func)
    .with_request_info(enabled=True)
    .build()
)
```

## Custom Aggregation

Default aggregation concatenates all responses. Use custom aggregators to synthesize:

### Aggregator Function Signature

```python
async def custom_aggregator(
    results: list[AgentExecutorResponse]
) -> str | list[Message] | Message:
    """
    Aggregate parallel agent results.

    Args:
        results: List of responses from each agent executor

    Returns:
        Aggregated result (string, message, or list of messages)
    """
    # Process results and return aggregation
    pass
```

### Example: LLM-Based Consolidation

```python
async def consolidate_expert_opinions(results: list) -> str:
    """Use chat client to synthesize expert opinions."""
    expert_sections = []

    for result in results:
        try:
            # Extract text from agent response
            if hasattr(result, 'agent_run_response'):
                messages = getattr(result.agent_run_response, 'messages', [])
            else:
                messages = getattr(result, 'messages', [])

            final_text = messages[-1].text if messages else "(no content)"
            executor_id = getattr(result, 'executor_id', 'expert')

            expert_sections.append(f"{executor_id}:\n{final_text}")
        except Exception as e:
            expert_sections.append(f"expert: (error: {e})")

    # Use LLM to synthesize
    from agent_framework import Message

    system_msg = Message(
        role="system",
        contents=[("text", "Consolidate these expert opinions into a comprehensive summary.")]
    )
    user_msg = Message(
        role="user",
        contents=[("text", f"Expert Opinions:\n\n{''.join(expert_sections)}")]
    )

    response = await chat_client.complete_async([system_msg, user_msg])
    return response.text

# Apply aggregator
workflow = (
    ConcurrentBuilder(participants=[researcher, marketer, legal])
    .with_aggregator(consolidate_expert_opinions)
    .build()
)
```

### Example: Custom Formatting

```python
async def format_expert_report(results: list) -> str:
    """Format expert opinions as a structured report."""
    report = "# Expert Analysis Report\n\n"

    for i, result in enumerate(results, 1):
        executor_id = getattr(result, 'executor_id', f'Expert {i}')

        # Extract content
        if hasattr(result, 'agent_run_response'):
            messages = result.agent_run_response.messages
        else:
            messages = getattr(result, 'messages', [])

        if messages:
            content = messages[-1].text
            report += f"## {executor_id}\n\n{content}\n\n"

    return report

workflow = (
    ConcurrentBuilder(participants=[researcher, marketer, legal])
    .with_aggregator(format_expert_report)
    .build()
)
```

### Example: Response Merging with Metadata

```python
from agent_framework import Message

async def merge_with_metadata(results: list) -> list[Message]:
    """Merge responses preserving executor metadata."""
    merged_messages = []

    for result in results:
        executor_id = getattr(result, 'executor_id', 'unknown')

        if hasattr(result, 'agent_run_response'):
            messages = result.agent_run_response.messages
        else:
            messages = getattr(result, 'messages', [])

        for msg in messages:
            # Add executor metadata
            msg.author_name = f"{executor_id}"
            merged_messages.append(msg)

    return merged_messages

workflow = (
    ConcurrentBuilder(participants=[researcher, marketer, legal])
    .with_aggregator(merge_with_metadata)
    .build()
)
```

## AgentExecutorResponse Structure

When implementing custom aggregators, you'll receive `AgentExecutorResponse` objects:

```python
class AgentExecutorResponse:
    executor_id: str              # Agent name/ID
    agent_run_response: object    # Agent's response containing messages
    status: str                   # Execution status
```

Access response data:

```python
# Get executor identifier
executor_name = result.executor_id

# Get messages
if hasattr(result, 'agent_run_response'):
    messages = result.agent_run_response.messages
else:
    messages = result.messages

# Get final text
final_text = messages[-1].text if messages else ""

# Get status
status = getattr(result, 'status', 'completed')
```

## Workflow as Agent

Wrap concurrent workflow as a reusable agent:

```python
# Convert to agent
workflow_agent = workflow.as_agent(name="Concurrent Analysis Agent")

# Create session
session = await workflow_agent.create_session()

# Run as agent
messages = [Message(role="user", contents=["Your question"])]

async for update in workflow_agent.run(messages, session=session, stream=True):
    if update.text:
        print(update.text, end="", flush=True)
```

## Execution Flow

```
Input Message
    ↓
Launch All Agents in Parallel:
    ├→ Agent A executes
    ├→ Agent B executes
    └→ Agent C executes
    ↓
Wait for All Completions
    ↓
Apply Aggregator Function
    ↓
Return Aggregated Output
```

## Real-World Example: Market Analysis

Complete concurrent workflow with custom aggregator:

```python
from agent_framework.orchestrations import ConcurrentBuilder
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework import Message
from azure.identity import AzureCliCredential

async def synthesize_market_analysis(results: list) -> str:
    """Synthesize market analysis from multiple experts."""
    analyses = {}

    for result in results:
        executor_id = result.executor_id
        messages = result.agent_run_response.messages
        analyses[executor_id] = messages[-1].text if messages else ""

    # Create synthesis prompt
    synthesis_prompt = f"""
You are a market strategy advisor. Synthesize these expert analyses into a unified recommendation:

Research Perspective:
{analyses.get('researcher', 'N/A')}

Marketing Perspective:
{analyses.get('marketer', 'N/A')}

Legal Perspective:
{analyses.get('legal', 'N/A')}

Provide a concise executive summary recommending next steps.
"""

    response = await chat_client.complete_async(synthesis_prompt)
    return response.text

async def main():
    chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

    researcher = chat_client.as_agent(
        instructions="Analyze market size, trends, and opportunities.",
        description="Market researcher",
        name="researcher",
    )

    marketer = chat_client.as_agent(
        instructions="Assess marketing channels, positioning, and strategy.",
        description="Marketing expert",
        name="marketer",
    )

    legal = chat_client.as_agent(
        instructions="Review compliance, regulations, and legal risks.",
        description="Legal advisor",
        name="legal",
    )

    # Build concurrent workflow
    workflow = (
        ConcurrentBuilder(name="market_analysis")
        .participants([researcher, marketer, legal])
        .with_aggregator(synthesize_market_analysis)
        .build()
    )

    # Run
    messages = [
        Message(
            role="user",
            contents=["Should we enter the budget electric vehicle market?"]
        )
    ]

    print("Launching parallel market analysis...\n")
    async for event in workflow.run_stream(messages):
        if event.type == "output":
            print(f"Analysis Result:\n{event.data}\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Key Characteristics

| Feature | Detail |
|---|---|
| **Parallel** | All agents run simultaneously |
| **Same Input** | Every agent receives identical input |
| **Independent** | Agents don't see each other's responses |
| **Aggregated** | Results combined at the end |
| **Scalable** | Add agents without changing orchestration |
| **Flexible Merging** | Custom aggregators for any synthesis strategy |

## Configuration Summary

| Method | Required | Description |
|---|:-:|---|
| `ConcurrentBuilder()` | ✅ | Initialize (name is optional) |
| `.participants()` | ✅ | List of agents to run in parallel |
| `.with_aggregator()` | ❌ | Custom aggregation function |
| `.with_request_info()` | ❌ | Enable human-in-the-loop |
| `.with_checkpointing()` | ❌ | Enable state persistence |
| `.build()` | ✅ | Create executable workflow |

## Best Practices

1. **Agent Independence**: Agents should not depend on each other's results (they run in parallel)
2. **Aggregation Strategy**: Choose aggregation that matches your use case (concat, synthesis, merging)
3. **Performance**: With many agents, consider execution time (all agents' slowest response determines total time)
4. **Error Handling**: Implement aggregators that gracefully handle failures from individual agents
5. **Output Format**: Ensure agents produce output in a format your aggregator can process
