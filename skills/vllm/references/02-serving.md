# Online Serving — OpenAI-Compatible API

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Starting the Server](#starting-the-server)
- [Server Arguments](#server-arguments)
- [Supported Endpoints](#supported-endpoints)
- [Chat Completions API](#chat-completions-api)
- [Completions API](#completions-api)
- [Embeddings API](#embeddings-api)
- [Python Client Setup](#python-client-setup)
- [Streaming](#streaming)
- [Authentication](#authentication)
- [Server Configuration](#server-configuration)
- [Common Pitfalls](#common-pitfalls)

## Overview

vLLM provides an OpenAI-compatible HTTP server that implements the Chat Completions, Completions, Embeddings, and Models endpoints. This allows any OpenAI SDK client to connect to a vLLM server with zero code changes — just point `base_url` at your vLLM instance.

## Starting the Server

### Basic Launch

```bash
vllm serve <model>
```

```bash
# Serve a chat model
vllm serve Qwen/Qwen2.5-1.5B-Instruct

# Serve with custom host/port
vllm serve meta-llama/Llama-3.1-8B-Instruct --host 0.0.0.0 --port 8080

# Serve a quantized model on 2 GPUs
vllm serve TheBloke/Llama-2-70B-Chat-GPTQ \
    --quantization gptq \
    --tensor-parallel-size 2

# Serve with API key protection
vllm serve Qwen/Qwen2.5-1.5B-Instruct --api-key my-secret-key
```

### Using Python

```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --port 8000
```

## Server Arguments

### Essential Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--model` | required | HuggingFace model ID or local path |
| `--host` | `0.0.0.0` | Host to bind to |
| `--port` | `8000` | Port to listen on |
| `--api-key` | None | API key for authentication (or `VLLM_API_KEY` env) |
| `--served-model-name` | model ID | Custom name returned in `/v1/models` |
| `--chat-template` | auto | Jinja2 chat template path or string |
| `--response-role` | `assistant` | Role name in chat responses |

### Model Configuration

| Argument | Default | Description |
|----------|---------|-------------|
| `--dtype` | `auto` | Model dtype: auto, float16, bfloat16, float32 |
| `--max-model-len` | auto | Maximum context length in tokens |
| `--quantization` | None | Quantization method: awq, gptq, fp8, etc. |
| `--trust-remote-code` | False | Allow custom model code |
| `--revision` | None | Specific model revision (branch/tag/commit) |

### Performance Tuning

| Argument | Default | Description |
|----------|---------|-------------|
| `--tensor-parallel-size` | 1 | Number of GPUs for tensor parallelism |
| `--pipeline-parallel-size` | 1 | Number of pipeline stages |
| `--gpu-memory-utilization` | 0.9 | GPU memory fraction to use |
| `--max-num-seqs` | 256 | Maximum concurrent sequences |
| `--max-num-batched-tokens` | auto | Maximum tokens per batch |
| `--enforce-eager` | False | Disable CUDA graphs |
| `--enable-prefix-caching` | True | Enable automatic prefix caching |
| `--attention-backend` | auto | Attention kernel: FLASH_ATTN, FLASHINFER, etc. |

### Feature Flags

| Argument | Default | Description |
|----------|---------|-------------|
| `--enable-auto-tool-choice` | False | Enable automatic function calling |
| `--tool-call-parser` | None | Tool call parser for function calling |
| `--enable-lora` | False | Enable LoRA adapter support |
| `--generation-config` | auto | Generation config source: auto, model, vllm |

## Supported Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat completions (recommended for chat models) |
| `/v1/completions` | POST | Text completions |
| `/v1/embeddings` | POST | Text embeddings |
| `/v1/models` | GET | List available models |
| `/health` | GET | Server health check |
| `/v1/load_lora_adapter` | POST | Dynamically load a LoRA adapter |
| `/v1/unload_lora_adapter` | POST | Unload a LoRA adapter |
| `/metrics` | GET | Prometheus metrics |
| `/tokenize` | POST | Tokenize text |
| `/detokenize` | POST | Detokenize token IDs |

## Chat Completions API

### Basic Request

```bash
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-1.5B-Instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Who won the 2024 World Series?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }'
```

### Response Format

```json
{
    "id": "chat-abc123",
    "object": "chat.completion",
    "created": 1718000000,
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "The Los Angeles Dodgers won..."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 25,
        "completion_tokens": 42,
        "total_tokens": 67
    }
}
```

### Supported Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name |
| `messages` | array | Conversation messages |
| `temperature` | float | Sampling temperature (0.0–2.0) |
| `top_p` | float | Nucleus sampling |
| `max_tokens` | int | Maximum generation tokens |
| `stream` | bool | Enable streaming |
| `stop` | string/array | Stop sequences |
| `n` | int | Number of completions |
| `presence_penalty` | float | Presence penalty (-2.0–2.0) |
| `frequency_penalty` | float | Frequency penalty (-2.0–2.0) |
| `logprobs` | bool | Return log probabilities |
| `top_logprobs` | int | Number of top logprobs per token |
| `seed` | int | Random seed for reproducibility |

## Completions API

```bash
curl http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-1.5B-Instruct",
        "prompt": "San Francisco is a",
        "max_tokens": 50,
        "temperature": 0
    }'
```

Supports the same parameters as Chat Completions, plus `prompt` (string or array of strings) instead of `messages`.

## Embeddings API

```bash
curl http://localhost:8000/v1/embeddings \
    -H "Content-Type: application/json" \
    -d '{
        "model": "intfloat/e5-mistral-7b-instruct",
        "input": ["What is machine learning?"]
    }'
```

## Python Client Setup

```python
from openai import OpenAI

client = OpenAI(
    api_key="EMPTY",                       # Required but unused without --api-key
    base_url="http://localhost:8000/v1",
)

# Chat completions
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a joke."},
    ],
    temperature=0.7,
    max_tokens=100,
)
print(response.choices[0].message.content)

# Completions
response = client.completions.create(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    prompt="The best programming language is",
    max_tokens=50,
)
print(response.choices[0].text)
```

## Streaming

```python
stream = client.chat.completions.create(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    messages=[{"role": "user", "content": "Write a poem about coding."}],
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

### Streaming with curl

```bash
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-1.5B-Instruct",
        "messages": [{"role": "user", "content": "Tell a story"}],
        "stream": true
    }'
```

## Authentication

### Server-side

```bash
# Via CLI flag
vllm serve model --api-key my-secret-key

# Via environment variable
export VLLM_API_KEY=my-secret-key
vllm serve model
```

### Client-side

```python
client = OpenAI(
    api_key="my-secret-key",
    base_url="http://localhost:8000/v1",
)
```

```bash
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer my-secret-key" \
    -d '{...}'
```

## Server Configuration

### Custom Served Model Name

```bash
# Serve under a custom name
vllm serve meta-llama/Llama-3.1-8B-Instruct \
    --served-model-name my-llama

# Client uses the custom name
curl ... -d '{"model": "my-llama", ...}'
```

### Generation Config

```bash
# Use model's generation_config.json defaults
vllm serve model --generation-config model

# Use vLLM defaults instead
vllm serve model --generation-config vllm
```

### Custom Chat Template

```bash
vllm serve model --chat-template /path/to/template.jinja
```

## Common Pitfalls

1. **api_key required by OpenAI SDK** — even without server auth, the SDK requires a non-empty `api_key`; pass `"EMPTY"` or any string
2. **Model name mismatch** — the `model` in requests must match `--served-model-name` (defaults to the HuggingFace model ID)
3. **No chat template** — base (non-instruct) models don't have chat templates; use `/v1/completions` or provide `--chat-template`
4. **Port already in use** — vLLM defaults to 8000; change with `--port` if another service is there
5. **Embeddings on chat models** — embedding endpoints require models trained for embeddings; chat models return meaningless vectors
