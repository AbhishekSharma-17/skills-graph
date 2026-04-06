---
name: litellm
description: "Unified LLM gateway and SDK for calling 100+ LLM providers (OpenAI, Anthropic, Bedrock, Vertex, Azure, Ollama, etc.) with a single OpenAI-compatible interface. MANDATORY TRIGGERS: litellm, litellm proxy, litellm router, litellm.completion, llm gateway, multi-provider llm, openai-compatible proxy, model fallback, llm cost tracking, llm load balancing. Also trigger when user wants to switch LLM providers without rewriting code, route requests across multiple models, add fallbacks/retries to LLM calls, track token costs, run a self-hosted OpenAI-compatible proxy, or unify observability across providers. When in doubt about whether to use this skill for any multi-provider LLM task, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["litellm", "llm", "gateway", "proxy", "openai", "anthropic", "bedrock", "router", "fallback", "cost-tracking"]
---

# LiteLLM — Skill Router

> Call 100+ LLMs (OpenAI, Anthropic, Azure, Bedrock, Vertex, Ollama, etc.) with the OpenAI input/output format. SDK + self-hostable proxy gateway with routing, fallbacks, caching, observability, and cost tracking.

**Source:** [docs.litellm.ai](https://docs.litellm.ai) | **Python SDK:** v1.52.x | **License:** MIT

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Quickstart** | `references/00-overview.md` | Getting started, install, core concepts, when to use SDK vs Proxy |
| **Completion API** | `references/01-completion-api.md` | `litellm.completion()`, params, messages, response shape |
| **Providers & Models** | `references/02-providers.md` | Provider prefixes, OpenAI, Anthropic, Bedrock, Vertex, Azure, Ollama |
| **Streaming** | `references/03-streaming.md` | Sync/async streaming, chunk parsing, stream wrappers |
| **Async & Concurrency** | `references/04-async.md` | `acompletion`, async batching, throughput patterns |
| **Router (SDK)** | `references/05-router.md` | Multi-deployment load balancing, routing strategies, model groups |
| **Proxy Server** | `references/06-proxy-server.md` | LiteLLM Proxy: config.yaml, virtual keys, /chat/completions endpoint |
| **Fallbacks & Retries** | `references/07-fallbacks-retries.md` | num_retries, fallback chains, context window fallbacks, timeout policy |
| **Caching** | `references/08-caching.md` | In-memory, Redis, S3 caching, semantic caching, cache controls |
| **Observability** | `references/09-observability.md` | Callbacks, Langfuse, Langsmith, OTEL, custom loggers |
| **Cost Tracking** | `references/10-cost-tracking.md` | Token counting, cost calculation, budgets, spend tracking |
| **Structured Outputs & Tools** | `references/11-structured-outputs.md` | JSON mode, response_format, function calling, tool_choice |
| **Embeddings & Other APIs** | `references/12-embeddings.md` | embedding(), image_generation(), transcription, moderation |

## Installation

```bash
# SDK only
pip install litellm

# Proxy server with extras
pip install 'litellm[proxy]'

# Run proxy
litellm --config config.yaml --port 4000
```

## Quick Reference

- **Docs:** https://docs.litellm.ai
- **GitHub:** https://github.com/BerriAI/litellm
- **PyPI:** https://pypi.org/project/litellm/
- **Provider matrix:** https://docs.litellm.ai/docs/providers
- **Proxy docs:** https://docs.litellm.ai/docs/simple_proxy
