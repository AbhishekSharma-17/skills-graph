# Ollama — Modelfile Reference

> Source: [docs.ollama.com/modelfile](https://docs.ollama.com/modelfile) | Version: 0.22.x

## Table of Contents

- [What Is a Modelfile](#what-is-a-modelfile)
- [Instructions Overview](#instructions-overview)
- [FROM](#from)
- [PARAMETER](#parameter)
- [SYSTEM](#system)
- [TEMPLATE](#template)
- [ADAPTER](#adapter)
- [LICENSE](#license)
- [MESSAGE](#message)
- [Complete Examples](#complete-examples)
- [Common Pitfalls](#common-pitfalls)

---

## What Is a Modelfile

A Modelfile is a configuration file that defines how Ollama builds and runs a model. It is conceptually similar to a Dockerfile — it specifies the base model, customizations, and runtime parameters.

```bash
# Create a model from a Modelfile
ollama create my-assistant -f Modelfile

# Export an existing model's Modelfile
ollama show llama3.2 --modelfile > Modelfile
```

**Key rules:**
- Instructions are NOT case sensitive (`FROM` = `from` = `From`)
- Instructions can appear in any order
- `FROM` is the only required instruction
- Comments start with `#`

## Instructions Overview

| Instruction | Required | Description |
|-------------|----------|-------------|
| `FROM` | Yes | Base model to build from |
| `PARAMETER` | No | Set runtime parameters |
| `SYSTEM` | No | Set the system message |
| `TEMPLATE` | No | Define the prompt template |
| `ADAPTER` | No | Apply a LoRA adapter |
| `LICENSE` | No | Specify the license |
| `MESSAGE` | No | Define conversation history |

## FROM

Specifies the base model. Must appear at least once.

```dockerfile
# From a model in the Ollama library
FROM llama3.2

# From a specific tag
FROM qwen3:8b

# From a GGUF file on disk
FROM ./my-model.gguf

# From a Safetensors directory
FROM ./path/to/safetensors/
```

**FROM sources:**
1. **Ollama library model** — `FROM llama3.2` (pulls if not present)
2. **Local GGUF file** — `FROM ./model.gguf` (for custom quantized models)
3. **Safetensors directory** — `FROM ./safetensors/` (auto-converts to GGUF)

## PARAMETER

Set model runtime parameters. Multiple PARAMETER instructions are allowed.

```dockerfile
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
PARAMETER top_p 0.9
PARAMETER stop "<|end|>"
PARAMETER stop "<|user|>"
```

**All available parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temperature` | float | 0.8 | Controls randomness (0.0 = deterministic, 2.0 = very creative) |
| `top_k` | int | 40 | Limits next token to top K candidates |
| `top_p` | float | 0.9 | Nucleus sampling — cumulative probability cutoff |
| `min_p` | float | 0.0 | Minimum probability threshold for tokens |
| `num_ctx` | int | 2048 | Context window size (tokens) |
| `num_predict` | int | -1 | Max tokens to generate (-1 = unlimited, -2 = fill context) |
| `repeat_penalty` | float | 1.1 | Penalize repeated tokens |
| `repeat_last_n` | int | 64 | Look-back window for repeat penalty |
| `seed` | int | 0 | Random seed (0 = non-deterministic) |
| `stop` | string | — | Stop sequence (can specify multiple) |
| `num_gpu` | int | — | Layers to offload to GPU (0 = CPU only, 999 = all GPU) |
| `num_thread` | int | — | CPU threads for computation |
| `num_batch` | int | 512 | Batch size for prompt evaluation |
| `num_keep` | int | — | Tokens to always keep in context |
| `mirostat` | int | 0 | Mirostat sampling (0 = disabled, 1 = v1, 2 = v2) |
| `mirostat_tau` | float | 5.0 | Target entropy for Mirostat |
| `mirostat_eta` | float | 0.1 | Learning rate for Mirostat |
| `penalize_newline` | bool | true | Penalize newlines in generation |
| `tfs_z` | float | 1.0 | Tail free sampling (1.0 = disabled) |

## SYSTEM

Set the default system prompt for the model.

```dockerfile
SYSTEM """You are a senior Python developer. You write clean, 
well-documented code with type hints. You follow PEP 8 and 
use modern Python 3.12+ features. Always explain your reasoning."""
```

**Multi-line syntax:** Use `"""triple quotes"""` for multi-line system prompts.

The system prompt can be overridden per-request via the API's `system` field or the CLI's `/set system` command.

## TEMPLATE

Define the prompt template using Go template syntax. Controls how messages are formatted before being sent to the model.

```dockerfile
TEMPLATE """{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>
{{ .Response }}<|end|>
"""
```

**Template variables:**

| Variable | Description |
|----------|-------------|
| `{{ .System }}` | System message content |
| `{{ .Prompt }}` | User prompt (generate API) |
| `{{ .Response }}` | Model response (for training format) |
| `{{ .Messages }}` | Array of chat messages (chat API) |
| `{{ .Tools }}` | Available tool definitions |

**Iterating messages (chat format):**

```dockerfile
TEMPLATE """{{ range .Messages }}
{{ if eq .Role "system" }}<|system|>{{ .Content }}<|end|>
{{ else if eq .Role "user" }}<|user|>{{ .Content }}<|end|>
{{ else if eq .Role "assistant" }}<|assistant|>{{ .Content }}<|end|>
{{ end }}{{ end }}<|assistant|>
"""
```

Most models in the Ollama library already have correct templates. Only customize this when importing custom GGUF files or creating specialized formatting.

## ADAPTER

Apply a LoRA (Low-Rank Adaptation) fine-tuned adapter to the base model.

```dockerfile
FROM llama3.2
ADAPTER ./my-lora-adapter.gguf
```

**Supported adapter formats:**
- GGUF LoRA adapters
- Safetensors LoRA adapters (auto-converted)

**Workflow for using a fine-tuned model:**
1. Fine-tune with Axolotl, Unsloth, or similar tool
2. Export the LoRA adapter
3. Create a Modelfile with FROM + ADAPTER
4. Run `ollama create my-finetuned -f Modelfile`

## LICENSE

Embed license text in the model metadata.

```dockerfile
LICENSE """MIT License
Copyright (c) 2026 My Organization
..."""
```

## MESSAGE

Pre-seed the conversation with example messages (few-shot prompting).

```dockerfile
MESSAGE user What is 2+2?
MESSAGE assistant 2+2 equals 4.

MESSAGE user What is the capital of France?
MESSAGE assistant The capital of France is Paris.
```

These messages appear at the start of every conversation, providing examples of the expected interaction style.

## Complete Examples

### Coding Assistant

```dockerfile
FROM qwen3:8b
SYSTEM """You are an expert software engineer. Write clean, 
production-ready code with error handling and type hints.
Always explain your approach before writing code."""

PARAMETER temperature 0.3
PARAMETER num_ctx 8192
PARAMETER top_p 0.85
PARAMETER stop "<|endoftext|>"
```

### Creative Writer

```dockerfile
FROM llama3.2
SYSTEM "You are a creative fiction writer. Write vivid, engaging prose."

PARAMETER temperature 1.2
PARAMETER top_p 0.95
PARAMETER top_k 60
PARAMETER repeat_penalty 1.15
PARAMETER num_predict 2048
```

### RAG-Optimized Model

```dockerfile
FROM llama3.1:8b
SYSTEM """Answer questions using ONLY the provided context. 
If the answer is not in the context, say 'I don't have enough 
information to answer that.' Never make up facts."""

PARAMETER temperature 0.1
PARAMETER num_ctx 16384
PARAMETER top_p 0.7
PARAMETER repeat_penalty 1.0
```

### Fine-Tuned Model

```dockerfile
FROM llama3.2
ADAPTER ./medical-lora.gguf
SYSTEM "You are a medical information assistant."

PARAMETER temperature 0.2
PARAMETER num_ctx 4096
```

## Common Pitfalls

1. **Template breaking chat** — If you override TEMPLATE without handling `.Messages`, the chat API will not format messages correctly. Use `{{ range .Messages }}` for chat support.
2. **num_ctx too large** — Each doubling of context window roughly doubles memory usage. A 32K context on a 7B model needs ~12GB RAM.
3. **Multiple stop sequences** — Use separate `PARAMETER stop` lines for each stop token, not a comma-separated list.
4. **GGUF path errors** — Paths in `FROM` and `ADAPTER` are relative to the Modelfile location, not the working directory.
5. **Overriding built-in templates** — Models from the library already have correct templates. Only customize if you know the model's expected chat format.
