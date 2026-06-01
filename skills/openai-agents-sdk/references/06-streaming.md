# Streaming — Real-Time Agent Output

> Source: [openai.github.io/openai-agents-python/streaming](https://openai.github.io/openai-agents-python/streaming/)

## Overview

Streaming enables subscribing to agent run updates in real-time using `Runner.run_streamed()`. This returns a `RunResultStreaming` object whose `stream_events()` method yields `StreamEvent` objects as they arrive.

The run is not complete until the async iterator finishes — post-processing like session persistence occurs after visible tokens arrive.

## Basic Streaming

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be helpful and detailed.")

async def stream_response(user_input: str):
    result = Runner.run_streamed(agent, user_input)

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if hasattr(event.data, "delta"):
                print(event.data.delta, end="", flush=True)

    print()  # Newline after streaming
    print(f"Final: {result.final_output}")
```

## Event Types

### 1. RawResponsesStreamEvent

Raw LLM events in OpenAI Responses API format — ideal for token-by-token streaming:

```python
from openai.types.responses import ResponseTextDeltaEvent

async for event in result.stream_events():
    if event.type == "raw_response_event":
        if isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
```

Common raw event types:
- `response.created` — Response object created
- `response.output_text.delta` — Text token delta
- `response.output_text.done` — Text output complete
- `response.completed` — Full response finished

### 2. RunItemStreamEvent

Semantic-level events representing fully-generated items:

```python
async for event in result.stream_events():
    if event.type == "run_item_stream_event":
        print(f"Event: {event.name} — {event.item}")
```

### Run Item Event Names

| Event Name | Meaning |
|------------|---------|
| `message_output_created` | Agent generated a text message |
| `tool_called` | Agent invoked a tool |
| `tool_output` | Tool returned a result |
| `handoff_requested` | Agent requested a handoff |
| `handoff_occured` | Handoff completed (intentionally misspelled for backward compat) |
| `reasoning_item_created` | Reasoning/thinking item generated |
| `mcp_approval_requested` | MCP tool needs approval |
| `tool_search_called` | Tool search invoked |
| `tool_search_output_created` | Tool search returned results |

### 3. AgentUpdatedStreamEvent

Fires when the current agent changes (typically from handoffs):

```python
async for event in result.stream_events():
    if event.type == "agent_updated_stream_event":
        print(f"Now talking to: {event.new_agent.name}")
```

## Complete Streaming Example

```python
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

agent = Agent(
    name="Writer",
    instructions="Write creative stories.",
)

async def chat(user_input: str):
    result = Runner.run_streamed(agent, user_input)

    current_agent = None
    async for event in result.stream_events():
        # Track agent changes
        if event.type == "agent_updated_stream_event":
            current_agent = event.new_agent.name
            print(f"\n[Agent: {current_agent}]")

        # Stream text tokens
        elif event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)

        # Log semantic events
        elif event.type == "run_item_stream_event":
            if event.name == "tool_called":
                print(f"\n[Calling tool: {event.item.raw_item.name}]")
            elif event.name == "tool_output":
                print(f"\n[Tool result received]")

    print(f"\n\nDone. Final output length: {len(result.final_output)}")
```

## Streaming with Approvals

When tools require human approval, the stream pauses:

```python
result = Runner.run_streamed(agent, "Delete the file")

async for event in result.stream_events():
    # Process events normally
    pass

# Check for pending approvals
if result.interruptions:
    for interruption in result.interruptions:
        print(f"Approval needed: {interruption}")
        # Approve or reject
        interruption.approve()  # or interruption.reject()

    # Resume the run
    state = result.to_state()
    result = Runner.run_streamed(agent, state)
    async for event in result.stream_events():
        pass
```

## Cancellation

```python
result = Runner.run_streamed(agent, "Long task")

# Cancel immediately
result.cancel()

# Cancel after current turn completes
result.cancel(mode="after_turn")
```

## WebSocket Transport

Reduce latency by using WebSocket instead of HTTP for streaming:

```python
from agents import set_default_openai_responses_transport

# Global WebSocket transport
set_default_openai_responses_transport("websocket")

# Or per-session for connection reuse
from agents import responses_websocket_session

async with responses_websocket_session() as ws:
    result1 = Runner.run_streamed(agent, "First message")
    async for event in result1.stream_events():
        pass

    result2 = Runner.run_streamed(agent, "Second message")
    async for event in result2.stream_events():
        pass
```

## Streaming in Web Applications

### FastAPI Integration

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent

app = FastAPI()
agent = Agent(name="API Agent", instructions="Be helpful.")

@app.post("/chat")
async def chat(message: str):
    async def generate():
        result = Runner.run_streamed(agent, message)
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    yield f"data: {event.data.delta}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Common Pitfalls

- **Not consuming the full stream**: The run isn't complete until the iterator finishes — session persistence and cleanup happen after visible tokens
- **Assuming event order**: Raw events interleave with semantic events; don't assume text deltas arrive before tool calls
- **Missing `flush=True`**: Without flushing, streamed output may buffer and appear in chunks
- **Ignoring interruptions**: If tools need approval, check `result.interruptions` after the stream completes

## Related Topics

- **Running Agents:** `03-running-agents.md` — Runner.run_streamed()
- **Models:** `09-models.md` — WebSocket transport configuration
- **MCP Integration:** `10-mcp.md` — MCP tool approvals during streaming
