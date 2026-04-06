# Providers & Models

> Source: https://docs.litellm.ai/docs/providers • Written for litellm v1.52.x

LiteLLM supports 100+ providers. The model string format is **`provider/model_id`** (the prefix tells LiteLLM which adapter to use).

## Provider prefix table

| Provider | Prefix | Example model string | Required env vars |
|----------|--------|----------------------|-------------------|
| OpenAI | `openai/` (optional) | `gpt-4o-mini` | `OPENAI_API_KEY` |
| Azure OpenAI | `azure/` | `azure/my-deployment-name` | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION` |
| Anthropic | `anthropic/` | `anthropic/claude-3-5-sonnet-20241022` | `ANTHROPIC_API_KEY` |
| AWS Bedrock | `bedrock/` | `bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION_NAME` |
| Google Vertex AI | `vertex_ai/` | `vertex_ai/gemini-1.5-pro` | `VERTEXAI_PROJECT`, `VERTEXAI_LOCATION`, GCP creds |
| Google AI Studio | `gemini/` | `gemini/gemini-1.5-pro` | `GEMINI_API_KEY` |
| Mistral | `mistral/` | `mistral/mistral-large-latest` | `MISTRAL_API_KEY` |
| Cohere | `cohere/` | `cohere/command-r-plus` | `COHERE_API_KEY` |
| Groq | `groq/` | `groq/llama-3.1-70b-versatile` | `GROQ_API_KEY` |
| Together AI | `together_ai/` | `together_ai/meta-llama/Llama-3-70b-chat-hf` | `TOGETHER_API_KEY` |
| Fireworks | `fireworks_ai/` | `fireworks_ai/accounts/fireworks/models/llama-v3p1-70b-instruct` | `FIREWORKS_AI_API_KEY` |
| DeepSeek | `deepseek/` | `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` |
| Ollama | `ollama/` or `ollama_chat/` | `ollama_chat/llama3.1` | (set `api_base`) |
| vLLM | `openai/` | `openai/<model>` + custom `api_base` | — |
| Hugging Face | `huggingface/` | `huggingface/meta-llama/Llama-2-7b-chat-hf` | `HUGGINGFACE_API_KEY` |
| Replicate | `replicate/` | `replicate/meta/meta-llama-3-70b-instruct` | `REPLICATE_API_KEY` |
| OpenRouter | `openrouter/` | `openrouter/anthropic/claude-3.5-sonnet` | `OPENROUTER_API_KEY` |
| Perplexity | `perplexity/` | `perplexity/llama-3.1-sonar-large-128k-online` | `PERPLEXITYAI_API_KEY` |
| xAI | `xai/` | `xai/grok-beta` | `XAI_API_KEY` |

## OpenAI

```python
import os
from litellm import completion

os.environ["OPENAI_API_KEY"] = "sk-..."
completion(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
```

## Azure OpenAI

Azure uses **deployment names**, not model IDs. The deployment is mapped to a base model in the Azure portal.

```python
os.environ["AZURE_API_KEY"] = "..."
os.environ["AZURE_API_BASE"] = "https://myorg.openai.azure.com/"
os.environ["AZURE_API_VERSION"] = "2024-08-01-preview"

completion(
    model="azure/my-gpt4-deployment",
    messages=[...],
)
```

## Anthropic

```python
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
completion(
    model="anthropic/claude-3-5-sonnet-20241022",
    messages=[...],
    max_tokens=1024,
)
```

LiteLLM translates OpenAI-format tool calls to Anthropic's `tool_use` blocks automatically.

## AWS Bedrock

```python
os.environ["AWS_ACCESS_KEY_ID"] = "..."
os.environ["AWS_SECRET_ACCESS_KEY"] = "..."
os.environ["AWS_REGION_NAME"] = "us-east-1"

completion(
    model="bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
    messages=[...],
)
```

For cross-region inference profiles, use the inference profile ARN/ID:
```python
model="bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
```

## Google Vertex AI

```python
os.environ["VERTEXAI_PROJECT"] = "my-gcp-project"
os.environ["VERTEXAI_LOCATION"] = "us-central1"
# Auth via gcloud ADC or GOOGLE_APPLICATION_CREDENTIALS

completion(
    model="vertex_ai/gemini-1.5-pro",
    messages=[...],
)
```

## Ollama (local)

```python
completion(
    model="ollama_chat/llama3.1",
    messages=[...],
    api_base="http://localhost:11434",
)
```

Use `ollama_chat/` (not `ollama/`) for the chat endpoint — it handles message formatting properly.

## vLLM / self-hosted OpenAI-compatible

Anything that exposes `/v1/chat/completions` works with the `openai/` prefix and a custom `api_base`:
```python
completion(
    model="openai/meta-llama/Meta-Llama-3-70B-Instruct",
    messages=[...],
    api_base="http://my-vllm-server:8000/v1",
    api_key="EMPTY",   # vLLM ignores this
)
```

## Discovering supported models

```python
import litellm

# All known models
print(litellm.model_list)

# Provider for a model
print(litellm.get_llm_provider("claude-3-5-sonnet-20241022"))

# Cost per 1K tokens (input, output)
print(litellm.model_cost["gpt-4o-mini"])
```

## Common pitfalls

- **Wrong prefix** — `bedrock/claude-3-sonnet` will fail; Bedrock model IDs include the vendor: `bedrock/anthropic.claude-3-sonnet-...`.
- **Azure deployment vs model name** — Use the deployment name, not `gpt-4o`.
- **Vertex location mismatch** — Some Gemini models are only in `us-central1`.
- **Ollama using `ollama/` instead of `ollama_chat/`** — The non-chat variant uses the legacy completion endpoint and handles roles poorly.
- **Forgetting region for Bedrock** — Different regions host different model IDs.

## Related
- Provider-specific params → `01-completion-api.md`
- Routing across multiple deployments → `05-router.md`
