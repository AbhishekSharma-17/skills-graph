# Ollama — Python Library

> Source: [github.com/ollama/ollama-python](https://github.com/ollama/ollama-python) | Package: `ollama` on PyPI

## Table of Contents

- [Installation](#installation)
- [Module-Level Functions](#module-level-functions)
- [Client Class](#client-class)
- [AsyncClient Class](#asyncclient-class)
- [Chat](#chat)
- [Generate](#generate)
- [Embeddings](#embeddings)
- [Streaming](#streaming)
- [Model Management](#model-management)
- [Tool Calling](#tool-calling)
- [Vision / Images](#vision--images)
- [Structured Output](#structured-output)
- [Error Handling](#error-handling)
- [Common Patterns](#common-patterns)

---

## Installation

```bash
pip install ollama

# With uv
uv add ollama
```

Requires Python >= 3.8. The Ollama server must be running (`ollama serve`).

## Module-Level Functions

The library provides module-level convenience functions that use a default client:

```python
from ollama import chat, generate, embeddings, list, show, pull, push, create, copy, delete

response = chat(model="llama3.2", messages=[{"role": "user", "content": "Hello"}])
```

These are equivalent to creating a `Client()` and calling methods on it.

## Client Class

The synchronous client for Ollama API calls.

```python
from ollama import Client

client = Client(host="http://localhost:11434")

response = client.chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.message.content)
```

**Constructor parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | str | `http://localhost:11434` | Ollama server URL |
| `timeout` | float | None | Request timeout in seconds |

## AsyncClient Class

The asynchronous client for use with `asyncio`.

```python
import asyncio
from ollama import AsyncClient

async def main():
    client = AsyncClient(host="http://localhost:11434")
    response = await client.chat(
        model="qwen3:8b",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(response.message.content)

asyncio.run(main())
```

AsyncClient has the same methods as Client, but all return coroutines.

## Chat

Multi-turn conversation with message history.

```python
from ollama import chat

messages = [
    {"role": "system", "content": "You are a Python expert."},
    {"role": "user", "content": "What's the difference between list and tuple?"},
]

response = chat(model="llama3.2", messages=messages)
print(response.message.content)

# Continue the conversation
messages.append({"role": "assistant", "content": response.message.content})
messages.append({"role": "user", "content": "Give me an example"})

response = chat(model="llama3.2", messages=messages)
print(response.message.content)
```

**Response object fields:**
- `response.message.content` — the response text
- `response.message.role` — always `"assistant"`
- `response.message.tool_calls` — tool calls (if tools were provided)
- `response.total_duration` — total time in nanoseconds
- `response.eval_count` — number of generated tokens

## Generate

Single-prompt text completion (no message history).

```python
from ollama import generate

response = generate(
    model="llama3.2",
    prompt="Write a haiku about Python",
    system="You are a creative poet.",
    options={"temperature": 1.0, "num_ctx": 4096},
)
print(response.response)
```

**Key parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | str | Model name |
| `prompt` | str | Input prompt |
| `system` | str | System message override |
| `template` | str | Prompt template override |
| `context` | list[int] | Context from previous generate call |
| `format` | str/dict | `"json"` or JSON schema |
| `options` | dict | Runtime parameters |
| `stream` | bool | Enable streaming (default: False) |
| `keep_alive` | str | Model keep-alive duration |
| `images` | list[str] | Base64-encoded images |

## Embeddings

Generate vector embeddings for text.

```python
from ollama import embeddings

response = embeddings(
    model="nomic-embed-text",
    prompt="Machine learning is a subset of artificial intelligence",
)

vector = response.embedding
print(f"Dimensions: {len(vector)}")  # 768 for nomic-embed-text
```

**Batch embeddings:**

```python
from ollama import Client

client = Client()
texts = ["First document", "Second document", "Third document"]

vectors = []
for text in texts:
    resp = client.embeddings(model="nomic-embed-text", prompt=text)
    vectors.append(resp.embedding)
```

## Streaming

Process responses token by token as they're generated.

### Synchronous Streaming

```python
from ollama import chat

stream = chat(
    model="llama3.2",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True,
)

for chunk in stream:
    print(chunk.message.content, end="", flush=True)
print()
```

### Async Streaming

```python
import asyncio
from ollama import AsyncClient

async def stream_chat():
    client = AsyncClient()
    stream = await client.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": "Tell me a story"}],
        stream=True,
    )
    async for chunk in stream:
        print(chunk.message.content, end="", flush=True)
    print()

asyncio.run(stream_chat())
```

## Model Management

```python
from ollama import list, show, pull, copy, delete

# List all models
models = list()
for model in models.models:
    print(f"{model.model}: {model.size / 1e9:.1f} GB")

# Show model details
info = show("llama3.2")
print(info.modelfile)

# Pull a model (with progress)
for progress in pull("qwen3:8b", stream=True):
    if progress.total:
        pct = (progress.completed or 0) / progress.total * 100
        print(f"\rDownloading: {pct:.1f}%", end="")

# Copy a model
copy("llama3.2", "my-llama")

# Delete a model
delete("my-llama")

# Create a model from a Modelfile string
from ollama import create

modelfile = """FROM llama3.2
SYSTEM You are a helpful assistant.
PARAMETER temperature 0.5"""

for progress in create("my-assistant", modelfile=modelfile, stream=True):
    print(progress.status)
```

## Tool Calling

Pass Python functions as tools for the model to call.

```python
from ollama import chat

def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: 72°F, sunny"

response = chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=[get_weather],
)

if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
        name = tool_call.function.name
        args = tool_call.function.arguments
        print(f"Tool: {name}, Args: {args}")

        result = get_weather(**args)

        # Feed result back to the model
        messages = [
            {"role": "user", "content": "What's the weather in Tokyo?"},
            response.message,
            {"role": "tool", "content": result},
        ]
        final = chat(model="qwen3:8b", messages=messages)
        print(final.message.content)
```

## Vision / Images

Send images to vision-capable models.

```python
from ollama import chat
import base64
from pathlib import Path

image_data = base64.b64encode(Path("photo.jpg").read_bytes()).decode()

response = chat(
    model="llava",
    messages=[{
        "role": "user",
        "content": "Describe this image in detail",
        "images": [image_data],
    }],
)
print(response.message.content)
```

## Structured Output

Get JSON responses conforming to a schema.

```python
from ollama import chat

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "skills": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name", "age", "skills"],
}

response = chat(
    model="llama3.2",
    messages=[{"role": "user", "content": "Tell me about a fictional programmer"}],
    format=schema,
)
print(response.message.content)
# {"name": "Alex Chen", "age": 28, "skills": ["Python", "Rust", "TypeScript"]}
```

## Error Handling

```python
from ollama import chat, ResponseError

try:
    response = chat(model="nonexistent", messages=[{"role": "user", "content": "Hi"}])
except ResponseError as e:
    print(f"Error {e.status_code}: {e.error}")
except Exception as e:
    print(f"Connection error: {e}")
```

Common errors:
- `ResponseError` with status 404 — model not found
- `ConnectionError` — Ollama server not running
- `TimeoutError` — request timeout (set via `Client(timeout=30)`)

## Common Patterns

### FastAPI Integration

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from ollama import AsyncClient
import json

app = FastAPI()
client = AsyncClient()

@app.post("/chat")
async def chat_endpoint(prompt: str):
    async def generate():
        stream = await client.chat(
            model="qwen3:8b",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        async for chunk in stream:
            yield json.dumps({"text": chunk.message.content}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
```

### Custom Client Configuration

```python
from ollama import Client

client = Client(
    host="http://gpu-server:11434",
    timeout=120,
)
```
