# Models & Model Providers

Models are the "brain" of agents. They understand natural language and enable agents to reason, act, and respond. Agno supports 50+ models from leading providers through a unified interface.

## Basic Usage

Any Python function with a docstring and type hints becomes a tool:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    description="Share 15 minute healthy recipes.",
    markdown=True,
)
agent.print_response("Share a breakfast recipe.", stream=True)
```

## Model-as-String Syntax

Format: `"provider:model_id"` eliminates the need to import model classes.

```python
agent = Agent(model="openai:gpt-4o")
```

Assign different models for different purposes on a single agent:

```python
agent = Agent(
    model="openai:gpt-4o",
    reasoning_model="anthropic:claude-sonnet-4-20250514",
    parser_model="openai:gpt-4o-mini",
    output_model="openai:gpt-4o",
)
```

## Provider String Format

| Provider | String Format | Example |
|----------|--------------|---------|
| OpenAI | `openai:model_id` | `"openai:gpt-4o"` |
| Anthropic | `anthropic:model_id` | `"anthropic:claude-sonnet-4-20250514"` |
| Google | `google:model_id` | `"google:gemini-2.0-flash-exp"` |
| Groq | `groq:model_id` | `"groq:llama-3.3-70b-versatile"` |
| Ollama | `ollama:model_id` | `"ollama:llama3.2"` |
| Azure AI Foundry | `azure-ai-foundry:model_id` | `"azure-ai-foundry:gpt-4o"` |
| Mistral | `mistral:model_id` | `"mistral:mistral-large-latest"` |
| LiteLLM | `litellm:model_id` | `"litellm:gpt-4o"` |
| OpenRouter | `openrouter:model_id` | `"openrouter:anthropic/claude-3.5-sonnet"` |
| Together | `together:model_id` | `"together:meta-llama/Llama-3-70b-chat-hf"` |

## Error Handling & Retries

Configure retry logic on the model, agent, or team level:

```python
from agno.models.openai import OpenAIResponses

model = OpenAIResponses(
    id="gpt-5.2",
    retries=2,
    retry_delay=1,
    exponential_backoff=True,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retries` | `int` | `0` | Number of retry attempts on failure |
| `retry_delay` | `float` | `1` | Delay in seconds between retries |
| `exponential_backoff` | `bool` | `False` | Enable exponential backoff strategy |

## Response Caching

Enable with `cache_response=True` to avoid repeated API calls during development and testing:

```python
agent = Agent(
    model="openai:gpt-4o",
    cache_response=True,
    cache_ttl=3600,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cache_response` | `bool` | `False` | Enable local response caching |
| `cache_ttl` | `int` | `None` | Cache TTL in seconds (None = never expire) |
| `cache_dir` | `str` | `~/.agno/cache/model_responses` | Custom cache directory |

Response caching stores the entire response locally, whereas prompt caching (provider-side) caches the system prompt on the model provider's infrastructure.

Works seamlessly with agents, teams, and streaming.

## Model Compatibility Matrix

All models support streaming, tool calling, structured outputs, and async operations.

Multimodal support by provider:

| Provider | Image | Audio | Audio Response | Video | File Upload |
|----------|-------|-------|----------------|-------|-------------|
| Anthropic | ✅ | ✅ | | | |
| OpenAIChat | ✅ | ✅ | ✅ | | |
| OpenAIResponses | ✅ | ✅ | ✅ | ✅ | |
| Gemini | ✅ | ✅ | ✅ | ✅ | |
| Groq | ✅ | | | | |
| Cohere | ✅ | | | | |
| Mistral | ✅ | | | | |
| Ollama | ✅ | | | | |
| AWS Bedrock | ✅ | ✅ | | | |

## Model Providers by Category

### Native Providers

Direct access to provider APIs with optimized Agno integration:

Anthropic, Cohere, DashScope, DeepSeek, Google Gemini, Meta, Mistral, OpenAI (Chat & Responses), Perplexity, Vercel, xAI

### Local Models

Run models locally or on your infrastructure:

LlamaCpp, LM Studio, Ollama, VLLM

### Cloud Platforms

Hosted model access via cloud providers:

AWS Bedrock, Azure AI Foundry, Azure OpenAI, Vertex AI, IBM WatsonX

### API Gateways & Routing

Access multiple models through unified interfaces:

AI/ML API, Cerebras, CometAPI, DeepInfra, Fireworks, Groq, HuggingFace, LangDB, LiteLLM, Nebius, Neosantara, Nexus, NVIDIA, OpenRouter, Portkey, Requesty, Sambanova, SiliconFlow, Together

## Common Model Parameters (Base Class)

All model classes inherit these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `str` | Required | The model identifier (e.g. `"gpt-4o"`, `"claude-sonnet-4-5"`) |
| `name` | `Optional[str]` | `None` | Display name for logging and tracing |
| `provider` | `Optional[str]` | `None` | Provider name (auto-set by subclass) |
| `temperature` | `Optional[float]` | `None` | Controls randomness (0.0 = deterministic, 2.0 = max random) |
| `max_tokens` | `Optional[int]` | `None` | Maximum tokens to generate in the response |
| `top_p` | `Optional[float]` | `None` | Nucleus sampling — controls diversity (0.0 to 1.0) |
| `frequency_penalty` | `Optional[float]` | `None` | Penalizes tokens based on frequency in text so far (-2.0 to 2.0) |
| `presence_penalty` | `Optional[float]` | `None` | Penalizes tokens based on whether they appear at all (-2.0 to 2.0) |
| `stop` | `Optional[Union[str, List[str]]]` | `None` | Up to 4 sequences where the model stops generating |
| `seed` | `Optional[int]` | `None` | Random seed for deterministic/reproducible sampling |
| `stream` | `bool` | `True` | Whether to stream the response by default |
| `response_format` | `Optional[str]` | `None` | Response format specification |
| `request_params` | `Optional[Dict[str, Any]]` | `None` | Additional provider-specific parameters to include in requests |

## OpenAI-Specific Parameters

Additional parameters for `OpenAIChat` and `OpenAIResponses`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `Optional[str]` | `None` | OpenAI API key (or `OPENAI_API_KEY` env var) |
| `organization` | `Optional[str]` | `None` | OpenAI organization ID |
| `base_url` | `Optional[str]` | `None` | Custom base URL (for Azure, proxies, etc.) |
| `timeout` | `Optional[float]` | `None` | Request timeout in seconds |
| `max_retries` | `Optional[int]` | `None` | Max HTTP retries for failed requests |
| `reasoning_effort` | `Optional[str]` | `None` | Effort level for o1/o3 models: `"low"`, `"medium"`, `"high"` |
| `modalities` | `Optional[List[str]]` | `None` | Output modalities: `["text"]`, `["text", "audio"]` |
| `audio` | `Optional[Dict[str, Any]]` | `None` | Audio config: `{"voice": "alloy", "format": "wav"}` |
| `store` | `Optional[bool]` | `None` | Store conversation for training/fine-tuning |
| `service_tier` | `Optional[str]` | `None` | Service tier: `"auto"`, `"default"`, `"flex"`, `"priority"` |
| `strict_output` | `bool` | `True` | Controls schema adherence for structured output |
| `logit_bias` | `Optional[Any]` | `None` | Modifies likelihood of specific tokens |
| `logprobs` | `Optional[bool]` | `None` | Return log probabilities of output tokens |
| `top_logprobs` | `Optional[int]` | `None` | Number of top log probabilities to return (0-20) |
| `max_completion_tokens` | `Optional[int]` | `None` | Max completion tokens (alternative to `max_tokens`) |
| `collect_metrics_on_completion` | `bool` | `False` | Collect metrics only from the final chunk |
| `client_params` | `Optional[Dict[str, Any]]` | `None` | Additional client configuration |

## Claude-Specific Parameters

Additional parameters for `Claude` (Anthropic):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `Optional[str]` | `None` | Anthropic API key (or `ANTHROPIC_API_KEY` env var) |
| `max_tokens` | `Optional[int]` | `4096` | Max tokens (default higher than base class) |
| `thinking` | `Optional[Dict[str, Any]]` | `None` | Extended thinking config: `{"type": "enabled", "budget_tokens": 10000}` |
| `stop_sequences` | `Optional[List[str]]` | `None` | Strings where model stops generating |
| `top_k` | `Optional[int]` | `None` | Top-k sampling diversity |
| `cache_system_prompt` | `Optional[bool]` | `False` | Cache system prompt on Anthropic infrastructure for performance |
| `extended_cache_time` | `Optional[bool]` | `False` | Use extended cache time (1 hour instead of 5 minutes) |
| `mcp_servers` | `Optional[List[MCPServerConfiguration]]` | `None` | MCP server configurations |
| `default_headers` | `Optional[Dict[str, Any]]` | `None` | Default request headers |
| `client_params` | `Optional[Dict[str, Any]]` | `None` | Additional client config |

## Gemini-Specific Parameters

Additional parameters for `Gemini` (Google):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `Optional[str]` | `None` | Google API key (or `GOOGLE_API_KEY` env var) |
| `generation_config` | `Optional[Dict[str, Any]]` | `None` | Generation configuration dict |
| `safety_settings` | `Optional[List[Dict]]` | `None` | Content filtering/safety settings |
| `tool_config` | `Optional[Dict[str, Any]]` | `None` | Tool use configuration |
| `system_instruction` | `Optional[str]` | `None` | System instruction (alternative to system message) |
| `cached_content` | `Optional[str]` | `None` | Cached content ID for context caching |
| `thinking_enabled` | `Optional[bool]` | `None` | Enable thinking/reasoning mode |
| `client_params` | `Optional[Dict[str, Any]]` | `None` | Additional client config |

## OpenAI-Compatible Models

Use `OpenAILike` for any provider implementing the OpenAI API specification:

```python
from agno.models.openai.like import OpenAILike

agent = Agent(
    model=OpenAILike(
        id="mistralai/Mixtral-8x7B-Instruct-v0.1",
        api_key=getenv("TOGETHER_API_KEY"),
        base_url="https://api.together.xyz/v1",
    )
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | `str` | `"not-provided"` | Model identifier |
| `name` | `str` | `"OpenAILike"` | Display name |
| `api_key` | `str` | `"not-provided"` | API authentication key |
| `base_url` | `str` | `None` | Provider base URL |
| `collect_metrics_on_completion` | `bool` | `False` | Collect metrics from final chunk only |

## Open Responses API

For providers implementing the Open Responses standard:

```python
from agno.models.openai import OpenResponses

agent = Agent(
    model=OpenResponses(
        id="your-model-id",
        base_url="https://your-provider.com/v1",
        api_key="your-api-key",
    ),
)
```

## Key Imports

```python
from agno.models.openai import OpenAIResponses, OpenAIChat, OpenResponses
from agno.models.openai.like import OpenAILike
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.groq import Groq
from agno.models.ollama import Ollama
from agno.models.mistral import Mistral
from agno.models.cohere import Cohere
from agno.models.aws import BedrockChat, BedrockResponses
from agno.models.azure import AzureOpenAIChat, AzureOpenAIResponses
```
