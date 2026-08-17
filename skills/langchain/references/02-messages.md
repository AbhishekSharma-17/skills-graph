# Messages

> Source: https://docs.langchain.com/oss/python/langchain/messages

## Table of Contents

- [Overview](#overview)
- [Message Types](#message-types)
- [Content Blocks](#content-blocks)
- [Multimodal Messages](#multimodal-messages)
- [Tool Call Messages](#tool-call-messages)
- [Message Formats](#message-formats)
- [Token Usage](#token-usage)
- [Message Utilities](#message-utilities)
- [Serialization](#serialization)
- [Common Patterns](#common-patterns)

## Overview

Messages are the fundamental data structure for LLM interactions in LangChain. They represent conversation turns and support text, multimodal content, tool calls, and provider-specific metadata. All messages inherit from `BaseMessage` and carry a `content` attribute and a `role`.

## Message Types

### SystemMessage

Sets model behavior and context for the conversation.

```python
from langchain_core.messages import SystemMessage

system = SystemMessage("You are a helpful coding assistant specializing in Python.")
```

### HumanMessage

Represents user input. Supports text and multimodal content.

```python
from langchain_core.messages import HumanMessage

msg = HumanMessage("Explain decorators in Python")

msg_with_metadata = HumanMessage(
    content="Hello",
    name="alice",
    id="msg_001"
)
```

### AIMessage

Contains model-generated responses including text, tool calls, and usage metadata.

```python
from langchain_core.messages import AIMessage

response = model.invoke("Hello")
print(type(response))           # AIMessage
print(response.content)         # Text content
print(response.tool_calls)      # List of tool calls
print(response.usage_metadata)  # Token usage
print(response.response_metadata)  # Provider metadata
```

Key attributes:
- `content` — Text response or list of content blocks
- `tool_calls` — Parsed tool call requests
- `usage_metadata` — Input/output token counts
- `response_metadata` — Model ID, stop reason, etc.

### ToolMessage

Returns tool execution results to the model. Requires `tool_call_id` matching the original call.

```python
from langchain_core.messages import ToolMessage

tool_msg = ToolMessage(
    content="The weather in SF is 72°F and sunny.",
    tool_call_id="call_abc123",
    name="get_weather",
    artifact={"raw_data": {"temp": 72, "condition": "sunny"}}
)
```

The `artifact` field carries supplementary data that is not sent to the model but is available programmatically.

### AIMessageChunk

Streamed fragment of an AIMessage. Chunks can be combined with `+`:

```python
full = None
for chunk in model.stream("Hello"):
    full = chunk if full is None else full + chunk
print(full.content)
```

## Content Blocks

LangChain standardizes content representation through typed content blocks accessible via the `content_blocks` property.

### Standard Block Types

| Block Type | Purpose |
|------------|---------|
| `TextContentBlock` | Standard text with annotations |
| `ReasoningContentBlock` | Model reasoning/thinking steps |
| `ImageContentBlock` | Images (URL, base64, file_id) |
| `AudioContentBlock` | Audio data |
| `VideoContentBlock` | Video data |
| `FileContentBlock` | PDFs and documents |
| `PlainTextContentBlock` | Text documents (.txt, .md) |

### Accessing Content Blocks

```python
response = model.invoke("Explain quantum computing")

for block in response.content_blocks:
    if block["type"] == "text":
        print(f"Text: {block['text']}")
    elif block["type"] == "reasoning":
        print(f"Reasoning: {block['text']}")
```

## Multimodal Messages

### Image via URL

```python
message = HumanMessage(content=[
    {"type": "text", "text": "Describe this image."},
    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
])
```

### Image via Base64

```python
message = HumanMessage(content=[
    {"type": "text", "text": "What do you see?"},
    {"type": "image_url", "image_url": {
        "url": f"data:image/jpeg;base64,{b64_string}"
    }}
])
```

### PDF Document

```python
message = HumanMessage(content=[
    {"type": "text", "text": "Summarize this document."},
    {"type": "file", "base64": pdf_b64, "mime_type": "application/pdf"}
])
```

### Audio

```python
message = HumanMessage(content=[
    {"type": "text", "text": "Transcribe this audio."},
    {"type": "audio", "base64": audio_b64, "mime_type": "audio/wav"}
])
```

## Tool Call Messages

### Tool Call in AIMessage

```python
response = model_with_tools.invoke("What's the weather in NYC?")
for tc in response.tool_calls:
    print(f"Tool: {tc['name']}")
    print(f"Args: {tc['args']}")
    print(f"ID: {tc['id']}")
```

### Invalid Tool Calls

When the model produces malformed tool calls:

```python
for itc in response.invalid_tool_calls:
    print(f"Name: {itc['name']}")
    print(f"Args: {itc['args']}")  # Raw string
    print(f"Error: {itc['error']}")
```

## Message Formats

### LangChain Objects

```python
from langchain_core.messages import SystemMessage, HumanMessage

messages = [
    SystemMessage("You are helpful"),
    HumanMessage("Hello"),
]
response = model.invoke(messages)
```

### Dictionary Format (OpenAI-style)

```python
messages = [
    {"role": "system", "content": "You are helpful"},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
]
response = model.invoke(messages)
```

### String Input

```python
response = model.invoke("Hello")
```

LangChain automatically wraps strings in a `HumanMessage`.

## Token Usage

```python
response = model.invoke("Explain REST APIs")
usage = response.usage_metadata

print(f"Input: {usage['input_tokens']}")
print(f"Output: {usage['output_tokens']}")
print(f"Total: {usage['total_tokens']}")
```

Cache-aware usage (when prompt caching is active):

```python
if "cache_creation_input_tokens" in usage:
    print(f"Cache creation: {usage['cache_creation_input_tokens']}")
    print(f"Cache read: {usage['cache_read_input_tokens']}")
```

## Message Utilities

### trim_messages

Trim conversation history to fit token limits:

```python
from langchain_core.messages import trim_messages

trimmed = trim_messages(
    messages,
    max_tokens=1000,
    token_counter=model,
    strategy="last",
    start_on="human",
    include_system=True,
)
```

Parameters:
- `max_tokens` — Maximum token count
- `strategy` — `"last"` (keep recent) or `"first"` (keep oldest)
- `start_on` — Ensure result starts with this message type
- `include_system` — Always keep system message

### filter_messages

```python
from langchain_core.messages import filter_messages

humans_only = filter_messages(messages, include_types=["human"])
no_system = filter_messages(messages, exclude_types=["system"])
by_name = filter_messages(messages, include_names=["alice"])
```

### merge_message_runs

Combine consecutive messages of the same type:

```python
from langchain_core.messages import merge_message_runs

merged = merge_message_runs(messages)
```

## Serialization

### Save and Load Messages

```python
from langchain_core.load import dumpd, load

serialized = dumpd(message)
restored = load(serialized)
```

### JSON Conversion

```python
import json

data = [dumpd(m) for m in messages]
json_str = json.dumps(data)

messages = [load(d) for d in json.loads(json_str)]
```

## Common Patterns

### Build Conversation History

```python
from langchain_core.messages import HumanMessage, AIMessage

history = []
history.append(HumanMessage("What is Python?"))
response = model.invoke(history)
history.append(response)
history.append(HumanMessage("What are its main features?"))
response = model.invoke(history)
```

### Extract Text from Response

```python
response = model.invoke("Hello")

text = response.text  # Shorthand for text content
content = response.content  # Raw content (string or list)
blocks = response.content_blocks  # Typed content blocks
```

### RemoveMessage

Remove specific messages from state by ID:

```python
from langchain_core.messages import RemoveMessage

remove = RemoveMessage(id="msg_to_remove")
```
