# LoRA Adapters

> Source: [docs.vllm.ai](https://docs.vllm.ai/) — v0.22.1

## Table of Contents
- [Overview](#overview)
- [Offline Inference with LoRA](#offline-inference-with-lora)
- [Serving LoRA Adapters](#serving-lora-adapters)
- [Dynamic Adapter Management](#dynamic-adapter-management)
- [Multiple Adapters](#multiple-adapters)
- [Advanced Configuration](#advanced-configuration)
- [LoRA Resolver Plugins](#lora-resolver-plugins)
- [Multimodal LoRA](#multimodal-lora)
- [Common Pitfalls](#common-pitfalls)

## Overview

vLLM supports serving LoRA (Low-Rank Adaptation) adapters on top of base models with minimal memory overhead. Different requests can use different LoRA adapters simultaneously, enabling multi-tenant serving from a single base model.

Key capabilities:
- Per-request adapter selection
- Static and dynamic adapter loading
- Multiple concurrent adapters
- Hot-swapping without service interruption
- Adapter resolver plugins for custom loading logic

## Offline Inference with LoRA

### Basic Usage

```python
from huggingface_hub import snapshot_download
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

# Download the adapter
adapter_path = snapshot_download(repo_id="jeeejeee/llama32-3b-text2sql-spider")

# Create LLM with LoRA enabled
llm = LLM(model="meta-llama/Llama-3.2-3B-Instruct", enable_lora=True)

params = SamplingParams(temperature=0, max_tokens=256)

# Generate with the LoRA adapter
outputs = llm.generate(
    ["Convert to SQL: Show all users over age 30"],
    params,
    lora_request=LoRARequest(
        lora_name="sql_adapter",     # Unique name for this adapter
        lora_int_id=1,               # Unique integer ID
        lora_local_path=adapter_path,
    ),
)
print(outputs[0].outputs[0].text)
```

### Without LoRA (Base Model)

```python
# Same LLM instance, no lora_request → uses base model
outputs = llm.generate(["Hello, world!"], params)
```

## Serving LoRA Adapters

### Static Loading at Startup

Register adapters when starting the server:

```bash
vllm serve meta-llama/Llama-3.2-3B-Instruct \
    --enable-lora \
    --lora-modules sql-lora=jeeejeee/llama32-3b-text2sql-spider
```

Multiple adapters:

```bash
vllm serve meta-llama/Llama-3.2-3B-Instruct \
    --enable-lora \
    --lora-modules \
        sql-lora=jeeejeee/llama32-3b-text2sql-spider \
        code-lora=/local/path/to/code-adapter
```

### Enhanced Format with Base Model Tracking

```bash
vllm serve meta-llama/Llama-3.2-3B-Instruct \
    --enable-lora \
    --lora-modules '{
        "name": "sql-lora",
        "path": "jeeejeee/llama32-3b-text2sql-spider",
        "base_model_name": "meta-llama/Llama-3.2-3B-Instruct"
    }'
```

This enables model lineage tracking — the `/v1/models` endpoint shows parent-child relationships.

### Requesting a LoRA Adapter

The adapter name becomes a model name in requests:

```python
from openai import OpenAI

client = OpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

# Use the LoRA adapter
response = client.chat.completions.create(
    model="sql-lora",  # LoRA adapter name
    messages=[{"role": "user", "content": "Convert to SQL: Show all users"}],
)

# Use the base model
response = client.chat.completions.create(
    model="meta-llama/Llama-3.2-3B-Instruct",  # Base model
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Listing Available Models

```bash
curl http://localhost:8000/v1/models
```

Returns both the base model and all registered LoRA adapters.

## Dynamic Adapter Management

Load and unload adapters at runtime without restarting the server.

### Enable Dynamic Management

```bash
VLLM_ALLOW_RUNTIME_LORA_UPDATING=True vllm serve model --enable-lora
```

### Load an Adapter

```bash
curl -X POST http://localhost:8000/v1/load_lora_adapter \
    -H "Content-Type: application/json" \
    -d '{
        "lora_name": "sql_adapter",
        "lora_path": "/path/to/adapter"
    }'
```

### Unload an Adapter

```bash
curl -X POST http://localhost:8000/v1/unload_lora_adapter \
    -H "Content-Type: application/json" \
    -d '{
        "lora_name": "sql_adapter"
    }'
```

### In-Place Reload

Replace an adapter's weights without interrupting inference:

```bash
curl -X POST http://localhost:8000/v1/load_lora_adapter \
    -H "Content-Type: application/json" \
    -d '{
        "lora_name": "sql_adapter",
        "lora_path": "/path/to/updated/adapter",
        "load_inplace": true
    }'
```

## Multiple Adapters

Serve multiple LoRA adapters concurrently from a single base model. Each request specifies which adapter to use.

### Configuration

```bash
vllm serve base-model \
    --enable-lora \
    --max-loras 4 \
    --max-lora-rank 64 \
    --lora-modules \
        adapter-a=/path/a \
        adapter-b=/path/b \
        adapter-c=/path/c
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--max-loras` | varies | Maximum number of LoRA adapters loaded simultaneously |
| `--max-lora-rank` | 16 | Maximum LoRA rank across all adapters |
| `--lora-extra-vocab-size` | 256 | Extra vocabulary size for LoRA adapters |

### Concurrent Requests

Different requests can use different adapters at the same time:

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key="EMPTY", base_url="http://localhost:8000/v1")

async def query(model_name, prompt):
    return await client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )

# Concurrent requests with different adapters
results = await asyncio.gather(
    query("sql-lora", "Convert to SQL: list all users"),
    query("code-lora", "Write a fibonacci function"),
    query("base-model", "Hello, how are you?"),
)
```

## Advanced Configuration

### Max LoRA Rank

Set to the maximum rank among all adapters. Higher values waste memory:

```bash
# Adapters have ranks 16, 32, 64
vllm serve model --enable-lora --max-lora-rank 64
```

### Target Module Restriction

Restrict LoRA to specific layers for performance:

```bash
# Apply only to output projections
vllm serve model --enable-lora --lora-target-modules o_proj
```

Module names use suffixes: `o_proj`, `qkv_proj`, `gate_proj`, `up_proj`, `down_proj`.

### Mixed MoE LoRA Format

For MoE models with adapters in different formats:

```bash
vllm serve Qwen/Qwen3.6-35B-A3B \
    --enable-lora \
    --enable-mixed-moe-lora-format \
    --lora-modules \
        '{"name": "lora-2d", "path": "...", "is_3d_lora_weight": false}' \
        '{"name": "lora-3d", "path": "...", "is_3d_lora_weight": true}'
```

Incorrect `is_3d_lora_weight` declarations silently produce wrong outputs.

## LoRA Resolver Plugins

Implement custom resolvers for loading adapters from custom sources:

### Built-in Resolvers

```bash
# Filesystem resolver
VLLM_PLUGINS=lora_filesystem_resolver \
VLLM_LORA_RESOLVER_CACHE_DIR=/cache/lora \
vllm serve model --enable-lora

# HuggingFace Hub resolver
VLLM_PLUGINS=lora_hf_hub_resolver \
VLLM_LORA_RESOLVER_HF_REPO_LIST="org/adapter1,org/adapter2" \
vllm serve model --enable-lora
```

### Custom Resolver

```python
from vllm.lora.resolver import LoRAResolverRegistry

class MyResolver:
    async def resolve(self, lora_name: str) -> str:
        # Return local path to adapter weights
        return f"/storage/adapters/{lora_name}"

LoRAResolverRegistry.register_resolver("my_resolver", MyResolver())
```

## Multimodal LoRA

For models like Granite Speech that use LoRA adapters for modality-specific processing:

```python
llm = LLM(
    model="ibm-granite/granite-speech-3.3-2b",
    enable_lora=True,
    default_mm_loras={"audio": "ibm-granite/granite-speech-3.3-2b"},
)
```

```bash
vllm serve ibm-granite/granite-speech-3.3-2b \
    --enable-lora \
    --default-mm-loras '{"audio": "ibm-granite/granite-speech-3.3-2b"}'
```

The audio LoRA is automatically applied when audio input is detected.

## Common Pitfalls

1. **Adapter/base model mismatch** — LoRA adapters must be trained on (or compatible with) the exact base model being served
2. **max_lora_rank too low** — if the adapter rank exceeds `--max-lora-rank`, loading fails; set it to the maximum rank across all adapters
3. **Dynamic loading security** — `VLLM_ALLOW_RUNTIME_LORA_UPDATING=True` is a security risk; only use in trusted, isolated environments
4. **Memory overhead** — each loaded adapter consumes GPU memory; monitor with `--max-loras` to limit concurrent adapters
5. **Mixed MoE format** — incorrect `is_3d_lora_weight` produces silently wrong outputs; always verify adapter format
6. **Base model in /v1/models** — both the base model and adapters appear in the models list; ensure clients use the correct name
