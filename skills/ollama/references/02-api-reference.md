# Ollama — REST API Reference

> Source: [docs.ollama.com/api](https://docs.ollama.com/api/introduction) | API version: 0.22.x

## Table of Contents

- [Overview](#overview)
- [POST /api/generate](#post-apigenerate)
- [POST /api/chat](#post-apichat)
- [POST /api/embeddings](#post-apiembeddings)
- [POST /api/create](#post-apicreate)
- [GET /api/tags](#get-apitags)
- [POST /api/show](#post-apishow)
- [POST /api/copy](#post-apicopy)
- [DELETE /api/delete](#delete-apidelete)
- [POST /api/pull](#post-apipull)
- [POST /api/push](#post-apipush)
- [GET /api/ps](#get-apips)
- [GET /](#get-)
- [Streaming](#streaming)
- [Error Handling](#error-handling)

---

## Overview

Ollama exposes a REST API on `http://localhost:11434` by default. Two API surfaces are available:

| Surface | Base Path | Description |
|---------|-----------|-------------|
| **Native API** | `/api/*` | Full Ollama-native endpoints |
| **OpenAI-compatible** | `/v1/*` | Drop-in replacement for OpenAI SDK |

All endpoints accept and return JSON. Streaming endpoints return newline-delimited JSON objects.

## POST /api/generate

Generate a text completion from a prompt (non-chat format).

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Explain quantum computing",
  "stream": false
}'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model name |
| `prompt` | string | Yes | The prompt text |
| `stream` | bool | No | Stream response (default: true) |
| `images` | string[] | No | Base64-encoded images (vision models) |
| `system` | string | No | System message override |
| `template` | string | No | Prompt template override |
| `context` | int[] | No | Context from previous /api/generate call |
| `format` | string/object | No | `"json"` or JSON schema object |
| `options` | object | No | Runtime parameters (temperature, num_ctx, etc.) |
| `keep_alive` | string | No | How long to keep model loaded (e.g., `"5m"`, `"0"` to unload) |
| `suffix` | string | No | Suffix for fill-in-the-middle completion |

**Response (non-streaming):**

```json
{
  "model": "llama3.2",
  "created_at": "2026-05-01T10:00:00Z",
  "response": "Quantum computing uses quantum bits...",
  "done": true,
  "total_duration": 1234567890,
  "load_duration": 123456789,
  "prompt_eval_count": 15,
  "prompt_eval_duration": 100000000,
  "eval_count": 42,
  "eval_duration": 800000000
}
```

**Performance fields:**
- `total_duration` — total time in nanoseconds
- `load_duration` — model loading time
- `prompt_eval_count` — number of prompt tokens processed
- `eval_count` — number of generated tokens
- Tokens/sec = `eval_count / (eval_duration / 1e9)`

## POST /api/chat

Chat with a model using message history.

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:8b",
  "messages": [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Write a Python hello world"}
  ],
  "stream": false
}'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model name |
| `messages` | object[] | Yes | Array of message objects |
| `stream` | bool | No | Stream response (default: true) |
| `format` | string/object | No | `"json"` or JSON schema object |
| `options` | object | No | Runtime parameters |
| `tools` | object[] | No | Tool definitions for function calling |
| `keep_alive` | string | No | How long to keep model loaded |

**Message object:**

```json
{
  "role": "user|assistant|system|tool",
  "content": "message text",
  "images": ["base64..."],
  "tool_calls": [{"function": {"name": "...", "arguments": {...}}}]
}
```

**Response:**

```json
{
  "model": "qwen3:8b",
  "created_at": "2026-05-01T10:00:00Z",
  "message": {
    "role": "assistant",
    "content": "Here's a Python hello world..."
  },
  "done": true,
  "total_duration": 987654321,
  "eval_count": 35
}
```

## POST /api/embeddings

Generate vector embeddings for text.

```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "The quick brown fox"
}'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Embedding model name |
| `prompt` | string | Yes | Text to embed |
| `options` | object | No | Runtime parameters |
| `keep_alive` | string | No | How long to keep model loaded |

**Response:**

```json
{
  "embedding": [0.123, -0.456, 0.789, ...]
}
```

The embedding array length depends on the model (e.g., 768 for nomic-embed-text, 384 for all-minilm).

## POST /api/create

Create a model from a Modelfile.

```bash
curl http://localhost:11434/api/create -d '{
  "name": "my-assistant",
  "modelfile": "FROM llama3.2\nSYSTEM You are a helpful assistant.\nPARAMETER temperature 0.7"
}'
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Name for the new model |
| `modelfile` | string | Yes | Contents of the Modelfile |
| `stream` | bool | No | Stream progress (default: true) |
| `quantize` | string | No | Quantization level (q4_0, q4_1, q5_0, q5_1, q8_0) |

## GET /api/tags

List all locally available models.

```bash
curl http://localhost:11434/api/tags
```

**Response:**

```json
{
  "models": [
    {
      "name": "llama3.2:latest",
      "modified_at": "2026-05-01T10:00:00Z",
      "size": 2000000000,
      "digest": "sha256:abc123...",
      "details": {
        "format": "gguf",
        "family": "llama",
        "parameter_size": "3.2B",
        "quantization_level": "Q4_0"
      }
    }
  ]
}
```

## POST /api/show

Show detailed model information.

```bash
curl http://localhost:11434/api/show -d '{"name": "llama3.2"}'
```

Returns model details, Modelfile, parameters, template, and license.

## POST /api/copy

Copy a model to a new name.

```bash
curl http://localhost:11434/api/copy -d '{
  "source": "llama3.2",
  "destination": "my-llama"
}'
```

## DELETE /api/delete

Delete a model.

```bash
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "llama3.2"}'
```

## POST /api/pull

Pull a model from the registry.

```bash
curl http://localhost:11434/api/pull -d '{
  "name": "qwen3:8b",
  "stream": false
}'
```

## POST /api/push

Push a model to the registry.

```bash
curl http://localhost:11434/api/push -d '{
  "name": "myuser/mymodel:v1",
  "stream": false
}'
```

## GET /api/ps

List running models.

```bash
curl http://localhost:11434/api/ps
```

**Response:**

```json
{
  "models": [
    {
      "name": "llama3.2:latest",
      "model": "llama3.2:latest",
      "size": 3800000000,
      "digest": "sha256:abc123...",
      "expires_at": "2026-05-01T10:05:00Z",
      "size_vram": 3800000000
    }
  ]
}
```

## GET /

Health check endpoint.

```bash
curl http://localhost:11434/
# Returns: "Ollama is running"
```

## Streaming

Streaming endpoints return newline-delimited JSON. Each line is a complete JSON object:

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [{"role": "user", "content": "Hello"}]
}'
# Streams:
# {"model":"llama3.2","message":{"role":"assistant","content":"Hello"},"done":false}
# {"model":"llama3.2","message":{"role":"assistant","content":"!"},"done":false}
# {"model":"llama3.2","message":{"role":"assistant","content":""},"done":true,"total_duration":...}
```

Disable streaming with `"stream": false` to get a single complete response.

## Error Handling

Errors return HTTP status codes with a JSON body:

```json
{
  "error": "model 'nonexistent' not found, try pulling it first"
}
```

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request (invalid model name, missing fields) |
| 404 | Model not found |
| 500 | Server error |

**Options object** (usable in generate, chat, embeddings):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temperature` | float | 0.8 | Creativity (0.0–2.0) |
| `top_p` | float | 0.9 | Nucleus sampling threshold |
| `top_k` | int | 40 | Top-k sampling |
| `num_ctx` | int | 2048 | Context window size |
| `num_predict` | int | -1 | Max tokens to generate (-1 = infinite) |
| `repeat_penalty` | float | 1.1 | Repetition penalty |
| `seed` | int | 0 | Random seed (0 = random) |
| `stop` | string[] | — | Stop sequences |
| `num_gpu` | int | — | Number of GPU layers |
| `num_thread` | int | — | Number of CPU threads |
