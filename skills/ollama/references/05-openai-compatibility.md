# Ollama — OpenAI-Compatible API

> Source: [docs.ollama.com/api/openai-compatibility](https://docs.ollama.com/api/openai-compatibility) | Version: 0.22.x

## Table of Contents

- [Overview](#overview)
- [Supported Endpoints](#supported-endpoints)
- [Chat Completions](#chat-completions)
- [Embeddings](#embeddings)
- [Models](#models)
- [Using with OpenAI Python SDK](#using-with-openai-python-sdk)
- [Using with LangChain](#using-with-langchain)
- [Using with LlamaIndex](#using-with-llamaindex)
- [Using with LiteLLM](#using-with-litellm)
- [Tool Calling via OpenAI API](#tool-calling-via-openai-api)
- [Streaming](#streaming)
- [Supported Parameters](#supported-parameters)
- [Limitations vs OpenAI](#limitations-vs-openai)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

Ollama provides OpenAI-compatible API endpoints at `/v1/*`, enabling existing OpenAI SDK clients to work with local models with minimal changes. This means you can swap `api.openai.com` for `localhost:11434` and use the same code.

**Base URL:** `http://localhost:11434/v1`

No API key is required by default, but clients that mandate one accept any non-empty string.

## Supported Endpoints

| Endpoint | Method | OpenAI Equivalent |
|----------|--------|-------------------|
| `/v1/chat/completions` | POST | Chat completions |
| `/v1/embeddings` | POST | Embeddings |
| `/v1/models` | GET | List models |

## Chat Completions

```bash
curl http://localhost:11434/v1/chat/completions -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ]
}'
```

**Response format** matches OpenAI's schema:

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1714567890,
  "model": "llama3.2",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

## Embeddings

```bash
curl http://localhost:11434/v1/embeddings -d '{
  "model": "nomic-embed-text",
  "input": "The quick brown fox"
}'
```

Supports both single string and array inputs:

```bash
curl http://localhost:11434/v1/embeddings -d '{
  "model": "nomic-embed-text",
  "input": ["First text", "Second text", "Third text"]
}'
```

Also supports `encoding_format: "base64"` to reduce payload size.

## Models

```bash
curl http://localhost:11434/v1/models

# Response:
{
  "object": "list",
  "data": [
    {
      "id": "llama3.2",
      "object": "model",
      "created": 1714567890,
      "owned_by": "library"
    }
  ]
}
```

## Using with OpenAI Python SDK

The most common use case — use your existing OpenAI code with local models:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # any non-empty string works
)

response = client.chat.completions.create(
    model="qwen3:8b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain async/await in Python"},
    ],
    temperature=0.7,
    max_tokens=500,
)
print(response.choices[0].message.content)
```

### Streaming with OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

stream = client.chat.completions.create(
    model="llama3.2",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Async OpenAI SDK

```python
from openai import AsyncOpenAI
import asyncio

client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

async def main():
    response = await client.chat.completions.create(
        model="qwen3:8b",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## Using with LangChain

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen3:8b",
    temperature=0.7,
)

response = llm.invoke("Explain microservices")
print(response.content)
```

LangChain also has a dedicated `ChatOllama` class that uses the native API:

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen3:8b", temperature=0.7)
response = llm.invoke("Explain microservices")
```

## Using with LlamaIndex

```python
from llama_index.llms.ollama import Ollama

llm = Ollama(model="llama3.2", request_timeout=120.0)
response = llm.complete("Explain vector databases")
print(response.text)
```

## Using with LiteLLM

```python
import litellm

response = litellm.completion(
    model="ollama/qwen3:8b",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://localhost:11434",
)
print(response.choices[0].message.content)
```

## Tool Calling via OpenAI API

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    },
}]

response = client.chat.completions.create(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "Weather in Paris?"}],
    tools=tools,
)

if response.choices[0].message.tool_calls:
    for tc in response.choices[0].message.tool_calls:
        print(f"{tc.function.name}({tc.function.arguments})")
```

## Streaming

SSE (Server-Sent Events) streaming matches OpenAI's format:

```bash
curl http://localhost:11434/v1/chat/completions -d '{
  "model": "llama3.2",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": true
}'
# Returns SSE events:
# data: {"id":"...","choices":[{"delta":{"content":"Hello"}}],...}
# data: [DONE]
```

## Supported Parameters

| Parameter | Supported | Notes |
|-----------|-----------|-------|
| `model` | Yes | Ollama model name |
| `messages` | Yes | Full message array support |
| `temperature` | Yes | 0.0–2.0 |
| `top_p` | Yes | Nucleus sampling |
| `max_tokens` | Yes | Maps to `num_predict` |
| `stream` | Yes | SSE streaming |
| `stop` | Yes | Stop sequences |
| `tools` | Yes | Function calling |
| `response_format` | Yes | `{"type": "json_object"}` |
| `seed` | Yes | Reproducibility |
| `frequency_penalty` | Yes | Maps to `repeat_penalty` |
| `presence_penalty` | Partial | Limited support |
| `n` | No | Only n=1 supported |
| `logprobs` | Yes | Log probabilities (MLX models) |

## Limitations vs OpenAI

1. **No image generation** — Ollama is inference-only, no DALL-E equivalent
2. **No audio endpoints** — No Whisper/TTS support via API
3. **Single completion only** — `n > 1` is not supported
4. **No fine-tuning API** — Fine-tune externally, import via Modelfile ADAPTER
5. **No assistants API** — No threads, runs, or file search
6. **Model names differ** — Use Ollama model names, not OpenAI names (e.g., `llama3.2` not `gpt-4`)

## Common Pitfalls

1. **API key requirement** — Some SDKs require a non-empty API key. Use any string (e.g., `"ollama"`)
2. **Model not found** — OpenAI SDK returns a different error format. Pull the model first with `ollama pull`
3. **Slow first request** — The first request loads the model into memory. Subsequent requests are fast
4. **Token counting** — `usage.prompt_tokens` and `usage.completion_tokens` may differ slightly from OpenAI's tokenizer
5. **Response format** — `response_format: {"type": "json_object"}` requires the prompt to mention JSON output
