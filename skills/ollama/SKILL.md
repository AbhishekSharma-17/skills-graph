---
name: ollama
description: "Run LLMs locally with Ollama — model management, REST API, Python SDK, OpenAI-compatible endpoints, tool calling, structured output, vision, embeddings, and production deployment. MANDATORY TRIGGERS: ollama, Ollama, ollama run, ollama pull, ollama serve, Modelfile, ollama python, ollama api, ollama docker. Also trigger when user wants to run LLMs locally, serve models on localhost, create custom model configurations, build local RAG pipelines with embeddings, use OpenAI-compatible local endpoints, or deploy self-hosted LLM inference. When in doubt about whether to use this skill for local LLM tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["ollama", "local-llm", "model-serving", "inference", "embeddings", "rag", "tool-calling", "vision", "docker", "gpu"]
---

# Ollama — Skill Router

> Run large language models locally with a simple CLI and API.

**Source:** [ollama.com/docs](https://docs.ollama.com) | **Package:** `ollama` v0.22.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, quickstart, what Ollama is |
| **CLI Reference** | `references/01-cli-reference.md` | run, pull, push, create, list, show, cp, rm, serve, ps commands |
| **REST API** | `references/02-api-reference.md` | /api/generate, /api/chat, /api/tags, /api/embeddings endpoints |
| **Modelfile** | `references/03-modelfile.md` | FROM, PARAMETER, SYSTEM, TEMPLATE, ADAPTER, custom models |
| **Python Library** | `references/04-python-library.md` | Client, AsyncClient, chat, generate, embeddings, streaming |
| **OpenAI Compatibility** | `references/05-openai-compatibility.md` | /v1/chat/completions, /v1/embeddings, drop-in replacement |
| **Tool Calling** | `references/06-tool-calling.md` | Function calling, tools field, streaming tool calls |
| **Structured Output** | `references/07-structured-output.md` | JSON mode, schema enforcement, format parameter |
| **Vision & Multimodal** | `references/08-vision-multimodal.md` | Image input, LLaVA, Gemma 4, Qwen2.5-VL, base64 images |
| **Embeddings & RAG** | `references/09-embeddings-rag.md` | nomic-embed-text, all-minilm, vector DB integration, RAG |
| **GPU & Performance** | `references/10-gpu-performance.md` | GPU layers, VRAM, multi-GPU, num_gpu, context sizing |
| **Configuration** | `references/11-configuration.md` | Environment variables, OLLAMA_HOST, networking, model storage |
| **Docker & Deployment** | `references/12-docker-deployment.md` | Docker setup, production deployment, scaling, monitoring |

## Installation

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Python library
pip install ollama

# Docker
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

## Quick Reference

- **Docs:** https://docs.ollama.com
- **GitHub:** https://github.com/ollama/ollama
- **Models:** https://ollama.com/library
- **PyPI:** https://pypi.org/project/ollama/
- **Blog:** https://ollama.com/blog
