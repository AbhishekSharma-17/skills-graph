# Claude Agent SDK — Streaming

> Source: [platform.claude.com/docs/en/agent-sdk/streaming-output](https://platform.claude.com/docs/en/agent-sdk/streaming-output) — Python v0.1.51, TypeScript v0.2.86

## Contents

- [Streaming Overview](#streaming-overview)
- [Enabling Partial Messages](#enabling-partial-messages)
- [StreamEvent Structure](#streamevent-structure)
- [Event Types](#event-types)
- [Message Flow with Streaming](#message-flow-with-streaming)
- [Building a Streaming UI (Python)](#building-a-streaming-ui-python)
- [Building a Streaming UI (TypeScript)](#building-a-streaming-ui-typescript)
- [Streaming vs Single Mode Input](#streaming-vs-single-mode-input)
- [Streaming Input with ClaudeSDKClient](#streaming-input-with-claudesdkclient)
- [Streaming Input with AsyncGenerator (TypeScript)](#streaming-input-with-asyncgenerator-typescript)
- [Image Uploads via Streaming Input](#image-uploads-via-streaming-input)
- [Limitations](#limitations)
- [Common Patterns](#common-patterns)

## Streaming Overview

By default, the SDK buffers Claude's responses and yields complete `AssistantMessage` objects. With streaming enabled, you also receive `StreamEvent` messages containing raw Claude API events — allowing you to display text character-by-character as it's generated.

| Mode | Messages Received | Use Case |
|------|------------------|----------|
| **Default** | `SystemMessage`, `AssistantMessage`, `ResultMessage` | Batch processing, pipelines |
| **Streaming** | Above + `StreamEvent` (real-time deltas) | Interactive UIs, live terminals |

## Enabling Partial Messages

### Python

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    include_partial_messages=True,
)

async for message in query(prompt="Write a Python function", options=options):
    if message.type == "stream_event":
        # Raw Claude API event
        handle_stream_event(message)
    elif message.type == "assistant":
        # Complete message (after all streaming is done)
        print("\n--- Complete message ---")
```

### TypeScript

```typescript
const q = query({
  prompt: "Write a Python function",
  options: { includePartialMessages: true },
});

for await (const message of q) {
  if (message.type === "stream_event") {
    handleStreamEvent(message);
  } else if (message.type === "assistant") {
    console.log("--- Complete message ---");
  }
}
```

## StreamEvent Structure

Each `StreamEvent` contains a raw Claude API server-sent event:

```python
# StreamEvent fields
message.type          # "stream_event"
message.uuid          # Unique event ID
message.session_id    # Current session
message.event         # Raw Claude API event object
message.parent_tool_use_id  # If event is from a subagent tool call
```

The `event` field contains the actual Claude API event with its own `type` field.

## Event Types

The Claude API emits these event types during streaming:

| Event Type | Description | Key Fields |
|-----------|-------------|------------|
| `message_start` | New message begins | `message` (full message object) |
| `content_block_start` | New content block starts | `index`, `content_block` (type, id) |
| `content_block_delta` | Incremental content update | `index`, `delta` (text or input_json) |
| `content_block_stop` | Content block complete | `index` |
| `message_delta` | Message-level update | `delta` (stop_reason, stop_sequence), `usage` |
| `message_stop` | Message fully complete | (empty) |

### Delta Types

```python
# Text delta — streaming text content
{"type": "text_delta", "text": "def hello"}

# Tool input JSON delta — streaming tool call arguments
{"type": "input_json_delta", "partial_json": "{\"file_path\":"}
```

### Processing Deltas

```python
async for message in query(prompt="...", options=options):
    if message.type == "stream_event":
        event = message.event
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                # Real-time text output
                print(delta["text"], end="", flush=True)
            elif delta.get("type") == "input_json_delta":
                # Tool input being constructed
                pass
```

## Message Flow with Streaming

The complete message flow when streaming is enabled:

```
1. SystemMessage (subtype: "init")
   │
2. StreamEvent (message_start)
   StreamEvent (content_block_start)     ─┐
   StreamEvent (content_block_delta) x N  │ Real-time text
   StreamEvent (content_block_stop)      ─┘
   StreamEvent (content_block_start)     ─┐
   StreamEvent (content_block_delta) x N  │ Tool call being built
   StreamEvent (content_block_stop)      ─┘
   StreamEvent (message_delta)
   StreamEvent (message_stop)
   │
3. AssistantMessage (complete, with all content blocks)
   │
4. [Tool executes, results feed back]
   │
5. Steps 2-4 repeat for next turn
   │
6. ResultMessage (final result)
```

## Building a Streaming UI (Python)

```python
import sys
from claude_agent_sdk import query, ClaudeAgentOptions

async def streaming_ui():
    options = ClaudeAgentOptions(
        include_partial_messages=True,
        permission_mode="acceptEdits",
    )

    current_block_type = None

    async for msg in query(prompt="Refactor auth.py", options=options):
        if msg.type == "stream_event":
            event = msg.event
            event_type = event.get("type")

            if event_type == "content_block_start":
                block = event.get("content_block", {})
                current_block_type = block.get("type")
                if current_block_type == "tool_use":
                    tool_name = block.get("name", "unknown")
                    print(f"\n[Tool: {tool_name}] ", end="")

            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    sys.stdout.write(delta["text"])
                    sys.stdout.flush()

            elif event_type == "content_block_stop":
                current_block_type = None

        elif msg.type == "result":
            print(f"\n\nDone! Cost: ${msg.total_cost_usd:.4f}")
```

## Building a Streaming UI (TypeScript)

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const q = query({
  prompt: "Refactor auth.py",
  options: { includePartialMessages: true, permissionMode: "acceptEdits" },
});

let currentBlockType: string | null = null;

for await (const msg of q) {
  if (msg.type === "stream_event") {
    const event = msg.event;

    if (event.type === "content_block_start") {
      currentBlockType = event.content_block?.type;
      if (currentBlockType === "tool_use") {
        process.stdout.write(`\n[Tool: ${event.content_block.name}] `);
      }
    } else if (event.type === "content_block_delta") {
      if (event.delta?.type === "text_delta") {
        process.stdout.write(event.delta.text);
      }
    } else if (event.type === "content_block_stop") {
      currentBlockType = null;
    }
  } else if (msg.type === "result") {
    console.log(`\n\nDone! Cost: $${msg.total_cost_usd.toFixed(4)}`);
  }
}
```

## Streaming vs Single Mode Input

The SDK supports two input modes for sending prompts:

| Feature | Streaming Input | Single Message Input |
|---------|----------------|---------------------|
| **How** | `ClaudeSDKClient` (Python) / AsyncGenerator (TS) | `query()` with string prompt |
| **Image uploads** | Supported | Not supported |
| **Queue messages** | Yes, while agent runs | No |
| **Real-time interruption** | Yes | No |
| **Hook integration** | Full support | Limited |
| **Multi-turn** | Built-in | `continue_conversation=True` |

### When to Use Each

- **Streaming Input** (recommended): Interactive applications, multi-turn conversations, image uploads, real-time feedback
- **Single Message Input**: One-shot automation, CI/CD pipelines, batch processing

## Streaming Input with ClaudeSDKClient

Python uses `ClaudeSDKClient` for streaming input:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def interactive():
    options = ClaudeAgentOptions(
        include_partial_messages=True,
        permission_mode="acceptEdits",
    )

    client = ClaudeSDKClient(options=options)
    async with client:
        await client.connect(prompt="Analyze this project")

        async for msg in client.receive_messages():
            # Process messages...
            pass

        # Queue follow-up while processing
        await client.query("Now add tests")
        async for msg in client.receive_response():
            pass

        # Interrupt if needed
        await client.interrupt()
```

## Streaming Input with AsyncGenerator (TypeScript)

TypeScript uses an `AsyncGenerator` for streaming input:

```typescript
import { query, SDKUserMessage } from "@anthropic-ai/claude-agent-sdk";

async function* inputStream(): AsyncGenerator<SDKUserMessage> {
  yield { type: "user", content: [{ type: "text", text: "Analyze this project" }] };

  // Wait for some condition, then send follow-up
  await someCondition();
  yield { type: "user", content: [{ type: "text", text: "Now add tests" }] };
}

const q = query({ prompt: inputStream(), options: { includePartialMessages: true } });

for await (const msg of q) {
  // Process messages
}
```

## Image Uploads via Streaming Input

Streaming input supports image attachments (single message mode does not):

### Python

```python
import base64

async with ClaudeSDKClient(options=options) as client:
    # Send image via streaming input
    await client.connect()
    await client.query({
        "type": "user",
        "content": [
            {"type": "image", "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": base64.b64encode(image_bytes).decode(),
            }},
            {"type": "text", "text": "What's in this screenshot?"},
        ],
    })
```

### TypeScript

```typescript
async function* inputWithImage(): AsyncGenerator<SDKUserMessage> {
  yield {
    type: "user",
    content: [
      { type: "image", source: { type: "base64", media_type: "image/png", data: imageB64 } },
      { type: "text", text: "What's in this screenshot?" },
    ],
  };
}
```

## Limitations

1. **Extended thinking disables StreamEvent** — when thinking is enabled, you won't receive `StreamEvent` messages; only complete `AssistantMessage` objects
2. **Structured output JSON is not streamed** — the structured output result is only available in the final `ResultMessage`
3. **Tool input streaming** — `input_json_delta` events contain partial JSON that isn't parseable until complete
4. **Parallel tool calls** — multiple content blocks may interleave in stream events; track by `index` field
5. **Subagent events** — events from subagents have `parent_tool_use_id` set; use this to route display

## Common Patterns

### Progress Indicator

```python
async for msg in query(prompt="...", options=options):
    if msg.type == "stream_event":
        event = msg.event
        if event.get("type") == "content_block_start":
            block = event.get("content_block", {})
            if block.get("type") == "tool_use":
                print(f"  Running: {block.get('name')}...")
    elif msg.type == "assistant":
        # Tool finished
        for block in msg.content:
            if block.type == "tool_use":
                print(f"  Done: {block.name}")
```

### Separate Text and Tool Streams

```python
text_buffer = []
tool_events = []

async for msg in query(prompt="...", options=options):
    if msg.type == "stream_event":
        delta = msg.event.get("delta", {})
        if delta.get("type") == "text_delta":
            text_buffer.append(delta["text"])
        elif delta.get("type") == "input_json_delta":
            tool_events.append(delta)
```

## Related Topics

- [Overview](00-overview.md) — Message types and basic iteration
- [Configuration](01-configuration.md) — `include_partial_messages` option
- [Sessions](07-sessions.md) — ClaudeSDKClient for streaming input
