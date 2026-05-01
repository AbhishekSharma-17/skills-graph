# Changelog

All notable changes to the `ollama` skill will be documented in this file.

## [1.0.0] — 2026-05-01

**Source version tracked:** ollama 0.22.x (Python library latest)

### Added

- `00-overview.md` — What Ollama is, installation (macOS/Linux/Docker/pip), quickstart, architecture, model library, naming conventions, ecosystem
- `01-cli-reference.md` — All CLI commands (run, pull, push, create, list, show, cp, rm, serve, ps, stop), interactive mode commands, common patterns
- `02-api-reference.md` — REST API endpoints (/api/generate, /api/chat, /api/embeddings, /api/tags, /api/show, /api/create, /api/copy, /api/delete, /api/pull, /api/push, /api/ps), streaming, options reference
- `03-modelfile.md` — Modelfile instructions (FROM, PARAMETER, SYSTEM, TEMPLATE, ADAPTER, LICENSE, MESSAGE), complete parameter reference, template variables, examples
- `04-python-library.md` — Python SDK (Client, AsyncClient, chat, generate, embeddings, streaming, model management, tool calling, vision, structured output, error handling, FastAPI integration)
- `05-openai-compatibility.md` — OpenAI-compatible /v1 endpoints, OpenAI SDK usage, LangChain/LlamaIndex/LiteLLM integration, tool calling, parameter mapping, limitations
- `06-tool-calling.md` — Tool definition format, calling flow, Python library tools, streaming tool calls, multi-tool patterns, agent loop pattern
- `07-structured-output.md` — JSON mode, schema-enforced mode, Pydantic integration, Instructor library, complex schema patterns
- `08-vision-multimodal.md` — Vision models (LLaVA, Gemma 4, Qwen2.5-VL), CLI/API/Python/OpenAI SDK usage, image formats, OCR, chart analysis
- `09-embeddings-rag.md` — Embedding models, generating embeddings, RAG pipeline, ChromaDB/Qdrant integration, chunking strategies, LangChain/LlamaIndex RAG
- `10-gpu-performance.md` — GPU detection, layer offloading, multi-GPU, VRAM estimation, context sizing, concurrency, quantization, Apple Silicon, benchmarking
- `11-configuration.md` — Environment variables reference, server config, model storage, networking, CORS, Nginx proxy, systemd/launchd/Docker platform config
- `12-docker-deployment.md` — Docker quick start, Compose setup, GPU config, model pre-pulling, production architecture, Nginx proxy, health checks, scaling, security, backup

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,700
