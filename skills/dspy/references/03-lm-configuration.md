# DSPy — LM Configuration

> Source: https://dspy.ai/learn/programming/language_models — Written for DSPy v2.5.x

## Overview

DSPy uses `dspy.LM` as a unified client for any LLM provider. It's a thin wrapper around LiteLLM, so you get OpenAI, Anthropic, Azure, Bedrock, Vertex AI, Ollama, vLLM, Together, Groq, Fireworks, HuggingFace, and 100+ providers with a single API. You configure a default LM once and every module uses it; you can override per-module or per-call when you need a different model.

## The `dspy.LM` constructor

```python
import dspy

lm = dspy.LM(
    model="openai/gpt-4o-mini",   # "<provider>/<model>" or just "gpt-4o-mini"
    api_key="sk-...",
    api_base=None,                # override for proxies / self-hosted
    temperature=0.0,
    max_tokens=1024,
    cache=True,                   # on-disk prompt cache
    num_retries=3,
    model_type="chat",            # "chat" or "text"
)
```

Most fields are passed through to LiteLLM. The provider prefix is optional for well-known aliases but recommended for clarity.

## Setting the default

```python
dspy.configure(lm=lm)
```

This stores the LM in a thread-local context. Every `Predict`, `ChainOfThought`, etc. uses it unless you pass `lm=` explicitly to the call.

For long-running services, configure once at startup:

```python
# app.py
import dspy, os

dspy.configure(
    lm=dspy.LM("openai/gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"]),
)
```

## Provider cheat sheet

| Provider | Model string | Env vars |
|----------|-------------|----------|
| OpenAI | `openai/gpt-4o-mini`, `openai/gpt-4o`, `openai/o3-mini` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-opus-4-6`, `anthropic/claude-sonnet-4-6`, `anthropic/claude-haiku-4-5-20251001` | `ANTHROPIC_API_KEY` |
| Azure OpenAI | `azure/<deployment>` + `api_base`, `api_version` | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION` |
| Google Vertex AI | `vertex_ai/gemini-1.5-pro` | `GOOGLE_APPLICATION_CREDENTIALS` |
| AWS Bedrock | `bedrock/anthropic.claude-opus-4-6` | AWS creds |
| Ollama (local) | `ollama/llama3.1`, `ollama_chat/llama3.1` | `api_base="http://localhost:11434"` |
| vLLM (OpenAI-compat) | `openai/<served-name>` | `api_base="http://host:8000/v1"` |
| Together | `together_ai/meta-llama/Llama-3.1-70B` | `TOGETHER_API_KEY` |
| Groq | `groq/llama-3.1-70b-versatile` | `GROQ_API_KEY` |
| HF Inference API | `huggingface/<model>` | `HUGGINGFACE_API_KEY` |

## Per-module and per-call overrides

Every module accepts `lm=` at construction and at call time:

```python
fast_lm = dspy.LM("openai/gpt-4o-mini")
smart_lm = dspy.LM("anthropic/claude-opus-4-6")

classifier = dspy.Predict("text -> label", lm=fast_lm)
reasoner   = dspy.ChainOfThought("question -> answer", lm=smart_lm)

# Override at call time
pred = classifier(text="...", lm=smart_lm)
```

Use `dspy.settings.context(lm=...)` to override scoped blocks:

```python
with dspy.settings.context(lm=smart_lm):
    answer = program(question="...")
```

## Local models (Ollama, vLLM, LM Studio)

**Ollama:**

```python
lm = dspy.LM(
    "ollama_chat/llama3.1",
    api_base="http://localhost:11434",
    api_key="",  # unused but required
)
dspy.configure(lm=lm)
```

**vLLM served via OpenAI-compatible endpoint:**

```bash
vllm serve meta-llama/Llama-3.1-70B-Instruct --port 8000
```

```python
lm = dspy.LM(
    "openai/meta-llama/Llama-3.1-70B-Instruct",
    api_base="http://localhost:8000/v1",
    api_key="EMPTY",
)
```

**LM Studio** exposes an OpenAI-compatible server as well; point `api_base` at `http://localhost:1234/v1`.

## Caching

DSPy has a built-in on-disk LRU cache keyed by the full request (model, prompt, temperature, etc.). It dramatically speeds up eval loops because re-runs with the same prompt are free.

```python
lm = dspy.LM("openai/gpt-4o-mini", cache=True)  # default

# Disable for non-deterministic sampling evals
noisy = dspy.LM("openai/gpt-4o-mini", cache=False, temperature=0.7)
```

Clear the cache:

```python
import dspy
dspy.cache.reset()
```

## Token counting and cost

Inspect what was spent on the most recent call via the LM's history:

```python
lm.inspect_history(n=1)          # print the last call

usage = lm.history[-1]["usage"]  # {"prompt_tokens": 123, "completion_tokens": 45, ...}
```

`usage` is a standard OpenAI-style dict. For cross-provider cost tracking, use LiteLLM's cost helpers (see the LiteLLM skill) or a wrapper like Langfuse.

## Async & concurrency

DSPy modules have a `__call__` (sync) and an `acall` (async) method in recent versions. Most optimizers and `dspy.Evaluate` also accept `num_threads` to parallelize LM calls.

```python
import asyncio

async def main():
    result = await program.acall(question="What is DSPy?")
    print(result.answer)

asyncio.run(main())
```

For throughput-bound workloads, bump `num_threads` on evaluators and compilers rather than doing your own `asyncio.gather` — DSPy handles the rate limiting and retries consistently.

## Request-level customisation

You can pass arbitrary kwargs that the underlying provider accepts:

```python
lm = dspy.LM(
    "openai/gpt-4o-mini",
    response_format={"type": "json_object"},
    seed=42,
    user="user-42",
)
```

These are forwarded to LiteLLM and on to the provider.

## Common pitfalls

- **Re-creating `dspy.LM` per request.** It's cheap but the cache is per-instance in some configurations; share one instance.
- **Forgetting `api_key=""` for Ollama / vLLM.** Some LiteLLM versions reject missing keys even when the server doesn't need one.
- **Using `cache=True` during a noisy sampling eval.** You'll get the same deterministic answer every time regardless of temperature. Turn the cache off when measuring variance.
- **Mixing `chat` and `text` model types.** DSPy's prompts are built for chat by default; using `model_type="text"` breaks most signature rendering.
- **Hard-coding model names inside modules.** Always take the LM via `dspy.configure` or a constructor arg so you can swap models without code changes.
- **Sending an enormous context to a local model that advertised a smaller window.** LiteLLM will truncate or error; set `max_tokens` explicitly and check the model's real context length.

## Related topics

- **Using the LM inside modules:** `02-modules.md`
- **Multi-provider gateway (LiteLLM) for observability and cost tracking:** see `skills/litellm/`
- **Deployment patterns and serving:** `08-deployment.md`
