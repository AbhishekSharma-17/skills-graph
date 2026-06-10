# Streaming

> Source: [pydantic.dev/docs/ai/core-concepts/agent](https://pydantic.dev/docs/ai/core-concepts/agent/) — Streaming sections

## Table of Contents

- [Overview](#overview)
- [Streaming Text](#streaming-text)
- [Delta Streaming](#delta-streaming)
- [Streaming Structured Output](#streaming-structured-output)
- [Streaming Events](#streaming-events)
- [Node-by-Node Iteration](#node-by-node-iteration)
- [Cancelling Streams](#cancelling-streams)
- [Stream Response Validation](#stream-response-validation)
- [Message History After Cancellation](#message-history-after-cancellation)
- [Common Pitfalls](#common-pitfalls)

## Overview

Pydantic AI supports three streaming modes:

| Method | Use Case |
|--------|----------|
| `run_stream()` | Stream text or structured output to the user |
| `run_stream_events()` | Observe all events (tool calls, model responses, etc.) |
| `iter()` | Full control over each graph node with optional per-node streaming |

All streaming methods are async context managers that yield results progressively.

## Streaming Text

Basic cumulative text streaming:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

async def main():
    async with agent.run_stream('Tell me about Python') as result:
        async for text in result.stream_text():
            print(text)
            # Yields complete text so far:
            # "Python"
            # "Python is a"
            # "Python is a programming language..."
```

## Delta Streaming

Get only new chunks (not cumulative):

```python
async with agent.run_stream('Tell me about Python') as result:
    async for chunk in result.stream_text(delta=True):
        print(chunk, end='', flush=True)
        # Yields only new text:
        # "Python"
        # " is a"
        # " programming language..."
```

## Streaming Structured Output

Stream partial structured data as it builds:

```python
from typing_extensions import NotRequired, TypedDict
from pydantic_ai import Agent

class UserProfile(TypedDict):
    name: str
    dob: NotRequired[str]
    bio: NotRequired[str]

agent = Agent(
    'openai:gpt-5.2',
    output_type=UserProfile,
    instructions='Extract a user profile from input.'
)

async def main():
    async with agent.run_stream('Ben, born Jan 28 1990, loves Python') as result:
        async for profile in result.stream_output():
            print(profile)
            # {'name': 'Ben'}
            # {'name': 'Ben', 'dob': '1990-01-28'}
            # {'name': 'Ben', 'dob': '1990-01-28', 'bio': 'Loves Python'}
```

### Fine-Grained Control With stream_response

```python
from pydantic import ValidationError

async with agent.run_stream('Extract user info') as result:
    async for message in result.stream_response(debounce_by=0.01):
        try:
            profile = await result.validate_response_output(
                message,
                allow_partial=message.state == 'incomplete',
            )
        except ValidationError:
            continue
        print(profile)
```

## Streaming Events

Observe all events during a run — tool calls, model responses, final results:

```python
from pydantic_ai import Agent, FinalResultEvent, PartStartEvent

agent = Agent('openai:gpt-5.2')

async def main():
    async with agent.run_stream_events('Write a poem') as stream:
        async for event in stream:
            if isinstance(event, PartStartEvent):
                print(f'Started: {event.part!r}')
            elif isinstance(event, FinalResultEvent):
                print(f'Final result available')
                break
```

### Event Types

| Event | Description |
|-------|-------------|
| `PartStartEvent` | A new response part started |
| `PartDeltaEvent` | New content in current part |
| `FunctionToolCallEvent` | Model called a function tool |
| `FunctionToolResultEvent` | Tool returned a result |
| `FinalResultEvent` | Final output is available |

### Event Stream Handler

Register a handler that processes events alongside streaming:

```python
async def my_handler(ctx, event_stream):
    async for event in event_stream:
        if isinstance(event, FunctionToolCallEvent):
            print(f"Tool called: {event.part.tool_name}")

async with agent.run_stream(
    'Research this topic',
    event_stream_handler=my_handler
) as run:
    async for output in run.stream_text():
        print(output)
```

## Node-by-Node Iteration

Full control over each step of the agent graph:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

async def main():
    async with agent.iter('Analyze this data') as agent_run:
        async for node in agent_run:
            if Agent.is_model_request_node(node):
                # Stream this specific model request
                async with node.stream(agent_run.ctx) as stream:
                    async for event in stream:
                        print(event)
            elif Agent.is_call_tools_node(node):
                print(f'Calling tools: {node}')
```

## Cancelling Streams

### Cancel run_stream

```python
async with agent.run_stream('Write a long essay') as result:
    text = ''
    async for chunk in result.stream_text(delta=True):
        text += chunk
        if len(text) > 100:
            await result.cancel()
            break

print(result.cancelled)                        # True
print(result.response.state == 'interrupted')  # True
```

### Cancel run_stream_events

```python
async with agent.run_stream_events('Long task') as stream:
    async for event in stream:
        if isinstance(event, FinalResultEvent):
            break  # Stops iteration
```

### Cancel iter

```python
async with agent.iter('Long task') as run:
    async for node in run:
        if Agent.is_model_request_node(node):
            async with node.stream(run.ctx) as stream:
                async for event in stream:
                    if isinstance(event, FinalResultEvent):
                        await stream.cancel()
                        break
```

## Stream Response Validation

Validate structured output during streaming with partial allowance:

```python
from pydantic import ValidationError

agent = Agent('openai:gpt-5.2', output_type=UserProfile)

async with agent.run_stream('Extract user info') as result:
    async for message in result.stream_response(debounce_by=0.01):
        try:
            profile = await result.validate_response_output(
                message,
                allow_partial=message.state == 'incomplete',
            )
        except ValidationError:
            continue
        print(profile)
```

## Message History After Cancellation

After cancelling a stream, messages are preserved with an interrupted state:

```python
async with agent.run_stream('Tell me about Python') as result:
    async for text in result.stream_text(delta=True):
        break  # Cancel after first chunk
    await result.cancel()

messages = result.all_messages()
print(messages[-1].state)  # 'interrupted'

# Can continue the conversation
result2 = await agent.run(
    'Continue from where you left off',
    message_history=messages,
)
```

## Common Pitfalls

- **Using `run_stream` result outside context manager** — the stream is only valid inside `async with`; access `result.output` after the block exits
- **Delta vs cumulative confusion** — `stream_text()` is cumulative by default; pass `delta=True` for incremental chunks
- **Output validators with streaming** — validators fire on partials; check `ctx.partial_output` to skip side effects
- **Debouncing** — use `debounce_by=0.01` with `stream_response()` to batch rapid updates and reduce processing overhead
- **Cancellation ordering** — call `await result.cancel()` before breaking from the loop to ensure clean shutdown

## Related

- `01-agents.md` — Run methods overview
- `03-output.md` — Structured output and validators
- `06-hooks.md` — Event stream hooks
