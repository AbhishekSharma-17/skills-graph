# Ollama — Overview & Setup

> Source: [docs.ollama.com](https://docs.ollama.com) | Package: `ollama` v0.22.x

## Table of Contents

- [What Is Ollama](#what-is-ollama)
- [When to Use Ollama](#when-to-use-ollama)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Architecture](#architecture)
- [Model Library](#model-library)
- [Model Naming Convention](#model-naming-convention)
- [Ecosystem & Integrations](#ecosystem--integrations)
- [Common Pitfalls](#common-pitfalls)

---

## What Is Ollama

Ollama is a lightweight runtime for downloading, running, and serving large language models locally. It provides:

- **Simple CLI** — `ollama run llama3` to download and chat with a model in one command
- **REST API** — full HTTP API on `localhost:11434` for programmatic access
- **OpenAI-compatible endpoint** — drop-in `/v1/chat/completions` for existing OpenAI clients
- **Model customization** — Modelfiles for system prompts, parameters, and LoRA adapters
- **Multi-model serving** — run multiple models concurrently with automatic memory management
- **GPU acceleration** — automatic NVIDIA CUDA, AMD ROCm, and Apple Metal support
- **Cross-platform** — macOS, Linux, and Windows with native desktop apps

Ollama has 170k+ GitHub stars, is MIT-licensed, and is the most widely used local LLM runtime.

## When to Use Ollama

**Use Ollama when you need:**
- Private, offline LLM inference with no data leaving your machine
- Fast prototyping with open-weight models (Llama, Qwen, Gemma, DeepSeek, Mistral)
- Local embeddings for RAG pipelines without API costs
- A drop-in local replacement for OpenAI API calls
- Custom model configurations with system prompts and parameter tuning
- Vision/multimodal inference with local image processing
- Tool calling and structured output with local models

**Don't use Ollama when:**
- You need cloud-scale inference for thousands of concurrent users (use vLLM, TGI)
- You require fine-tuning (Ollama serves models; use Axolotl/Unsloth to train, then import)
- You need hosted model APIs with SLAs (use OpenAI, Anthropic, Google)

## Installation

### macOS

```bash
# Install script (recommended)
curl -fsSL https://ollama.com/install.sh | sh

# Or download the desktop app from https://ollama.com/download
```

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh

# The script installs ollama as a systemd service
sudo systemctl status ollama
```

### Docker

```bash
# CPU only
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# NVIDIA GPU
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

### Python Library

```bash
pip install ollama
```

### Verify Installation

```bash
ollama --version
# ollama version is 0.22.0

ollama serve &  # Start the server (auto-starts on macOS/Linux install)
ollama run llama3.2 "Hello, world!"
```

## Quickstart

```bash
# Pull and run a model interactively
ollama run qwen3:8b

# Single-shot prompt
ollama run gemma3 "Explain REST APIs in 3 sentences"

# Pull a model without running
ollama pull llama3.1:70b

# List downloaded models
ollama list

# Show model details
ollama show qwen3:8b

# Run with specific parameters
ollama run llama3.2 --verbose
```

### Python Quickstart

```python
from ollama import chat

response = chat(
    model="qwen3:8b",
    messages=[{"role": "user", "content": "Explain Docker in 2 sentences"}],
)
print(response.message.content)
```

### API Quickstart

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:8b",
  "messages": [{"role": "user", "content": "Hello!"}],
  "stream": false
}'
```

## Architecture

```
┌─────────────┐
│  CLI / API  │  ← User interface layer
├─────────────┤
│  Scheduler  │  ← Model loading, memory management, request queuing
├─────────────┤
│   Runner    │  ← llama.cpp / MLX inference engine
├─────────────┤
│  GPU/CPU    │  ← Hardware acceleration (CUDA, ROCm, Metal, CPU)
└─────────────┘
```

**Key architectural details:**
- Written in Go with llama.cpp as the inference backend
- MLX runner for Apple Silicon (used for Gemma 4 and other models)
- Models stored in `~/.ollama/models` by default (configurable via `OLLAMA_MODELS`)
- Server listens on `localhost:11434` by default (configurable via `OLLAMA_HOST`)
- Automatic GPU detection and layer offloading
- Concurrent model serving with configurable parallel request handling

## Model Library

Ollama's model library at [ollama.com/library](https://ollama.com/library) hosts hundreds of models:

| Category | Popular Models | Sizes |
|----------|---------------|-------|
| **General** | Llama 3.1/3.2, Qwen 3, Gemma 3/4, DeepSeek-V3 | 1B–405B |
| **Code** | Qwen2.5-Coder, DeepSeek-Coder-V2, CodeLlama | 1.5B–33B |
| **Vision** | LLaVA 1.6, Gemma 4, Qwen2.5-VL, Llama 4 Scout | 4B–34B |
| **Embedding** | nomic-embed-text, all-minilm, mxbai-embed-large | 23M–334M |
| **Small/Edge** | Phi-3 Mini, Gemma 2B, Qwen2.5-0.5B | 0.5B–3.8B |

## Model Naming Convention

```
model:tag

# Examples:
llama3.1           # defaults to :latest
llama3.1:8b        # 8B parameter variant
llama3.1:70b-q4_0  # 70B with 4-bit quantization
myuser/mymodel:v1  # namespaced custom model
```

**Tag components:**
- Parameter count: `8b`, `70b`, `405b`
- Quantization: `q4_0`, `q4_1`, `q5_0`, `q5_1`, `q8_0`, `fp16`
- Variant: `instruct`, `chat`, `text`, `code`

## Ecosystem & Integrations

| Integration | Description |
|-------------|-------------|
| **Open WebUI** | Full-featured chat interface for Ollama |
| **LangChain** | `ChatOllama` and `OllamaEmbeddings` classes |
| **LlamaIndex** | `Ollama` LLM and embedding integrations |
| **LiteLLM** | Unified API proxy supporting Ollama backend |
| **Continue** | VS Code/JetBrains AI assistant with Ollama |
| **Dify** | Low-code LLM app builder with Ollama support |
| **n8n** | Workflow automation with Ollama nodes |
| **AnythingLLM** | RAG desktop app with Ollama embeddings |

## Common Pitfalls

1. **Server not running** — Ollama CLI commands require `ollama serve` to be running. On macOS/Linux installs it auto-starts, but Docker requires explicit `-p 11434:11434`
2. **Model too large for RAM** — A 70B model needs ~40GB RAM. Check `ollama ps` for memory usage. Use quantized variants (`q4_0`) to reduce memory
3. **Slow without GPU** — CPU inference is 10-50x slower. Verify GPU detection with `ollama ps` (the PROCESSOR column shows gpu/cpu split)
4. **Port conflict** — Default port 11434 may conflict. Set `OLLAMA_HOST=0.0.0.0:8080` to change
5. **Model name confusion** — `llama3` vs `llama3.1` vs `llama3.2` are different model families. Always specify the exact version
6. **Context window defaults** — Most models default to 2048 tokens context. Set `num_ctx` in Modelfile or API to increase (e.g., 8192, 32768)
