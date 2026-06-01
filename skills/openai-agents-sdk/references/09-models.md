# Models — OpenAI & Non-OpenAI Integration

> Source: [openai.github.io/openai-agents-python/models](https://openai.github.io/openai-agents-python/models/)

## Table of Contents

- [OpenAI Models](#openai-models)
- [Model Settings](#model-settings)
- [Non-OpenAI Models](#non-openai-models)
- [Mixing Models](#mixing-models)
- [WebSocket Transport](#websocket-transport)
- [Runner-Managed Retries](#runner-managed-retries)
- [Third-Party Adapters](#third-party-adapters)

## OpenAI Models

The SDK provides two model implementations:

| Implementation | API | Recommended |
|---------------|-----|-------------|
| `OpenAIResponsesModel` | Responses API | Yes (default) |
| `OpenAIChatCompletionsModel` | Chat Completions API | For non-OpenAI providers |

### Default Model

The current default is `gpt-5.4-mini` with `reasoning.effort="none"` and `verbosity="low"`.

```python
# Override default globally via environment variable
# export OPENAI_DEFAULT_MODEL=gpt-5.5

# Override per-run via RunConfig
from agents import RunConfig
result = await Runner.run(agent, "Hello", run_config=RunConfig(model="gpt-5.5"))

# Override per-agent
agent = Agent(name="Smart Agent", model="gpt-5.5")
```

## Model Settings

Fine-tune model behavior with `ModelSettings`:

```python
from agents import Agent, ModelSettings
from openai.types.shared import Reasoning

agent = Agent(
    name="Research Agent",
    model="gpt-5.5",
    model_settings=ModelSettings(
        temperature=0.7,
        top_p=0.9,
        reasoning=Reasoning(effort="high"),
        verbosity="low",
        parallel_tool_calls=False,
        truncation="auto",
        store=True,
        context_management=[{"type": "compaction", "compact_threshold": 200_000}],
        prompt_cache_retention="24h",
        response_include=["web_search_call.action.sources"],
        top_logprobs=5,
    ),
)
```

### Key ModelSettings Fields

| Field | Purpose | Default |
|-------|---------|---------|
| `temperature` | Randomness (0-2) | Model default |
| `top_p` | Nucleus sampling | Model default |
| `tool_choice` | `"auto"`, `"required"`, `"none"`, or tool name | `"auto"` |
| `parallel_tool_calls` | Allow multiple tool calls per turn | `True` |
| `truncation` | `"auto"` for automatic context overflow handling | None |
| `reasoning` | `Reasoning(effort="high/medium/low/none")` | Varies |
| `verbosity` | Response verbosity level | `"low"` |
| `store` | Server-side response persistence | None |
| `extra_args` | Provider-specific fields | `{}` |

### Extra Arguments

For newer or provider-specific fields:

```python
agent = Agent(
    name="Agent",
    model_settings=ModelSettings(
        temperature=0.1,
        extra_args={"service_tier": "flex", "user": "user_12345"},
    ),
)
```

## Non-OpenAI Models

### Using Chat Completions API

Many non-OpenAI providers support Chat Completions but not the Responses API:

```python
from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled

set_tracing_disabled(True)  # Disable tracing for non-OpenAI keys

client = AsyncOpenAI(api_key="your-provider-key", base_url="https://api.provider.com/v1")
model = OpenAIChatCompletionsModel(model="provider-model-name", openai_client=client)

agent = Agent(
    name="Agent",
    instructions="Be helpful.",
    model=model,
)
```

### Integration Approaches

| Approach | Scope | Use When |
|----------|-------|----------|
| `set_default_openai_client(client)` | Global | All agents use the same provider |
| `RunConfig(model_provider=provider)` | Per-run | Different provider for specific runs |
| `Agent(model=model_instance)` | Per-agent | Different agents use different providers |

### Global Client Override

```python
from agents import set_default_openai_client, AsyncOpenAI

client = AsyncOpenAI(api_key="...", base_url="https://api.together.xyz/v1")
set_default_openai_client(client)
```

### Per-Run Provider

```python
from agents import RunConfig, OpenAIProvider

provider = OpenAIProvider(
    openai_client=AsyncOpenAI(api_key="...", base_url="..."),
    use_responses="never",  # Force Chat Completions API
)

result = await Runner.run(agent, "Hello", run_config=RunConfig(model_provider=provider))
```

### Tracing with Non-OpenAI Models

Three solutions for tracing conflicts:

```python
# Option 1: Disable tracing
from agents import set_tracing_disabled
set_tracing_disabled(True)

# Option 2: Separate OpenAI key for tracing
from agents import set_tracing_export_api_key
set_tracing_export_api_key("sk-your-openai-key")

# Option 3: Per-run configuration
result = await Runner.run(
    agent, "Hello",
    run_config=RunConfig(tracing={"api_key": "sk-..."}),
)
```

## Mixing Models

Different agents can use different models in a single workflow:

```python
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel

# Fast model for triage
triage_agent = Agent(
    name="Triage",
    model="gpt-5-nano",
    instructions="Route questions to specialists.",
    handoffs=[billing_agent, support_agent],
)

# Powerful model for complex reasoning
support_agent = Agent(
    name="Support",
    model="gpt-5.5",
    instructions="Resolve complex technical issues.",
)

# External model for translation
translation_model = OpenAIChatCompletionsModel(
    model="deepseek-v3",
    openai_client=AsyncOpenAI(api_key="...", base_url="..."),
)

translate_agent = Agent(
    name="Translator",
    model=translation_model,
    instructions="Translate text accurately.",
)
```

## WebSocket Transport

Use WebSocket for lower-latency streaming:

```python
from agents import set_default_openai_responses_transport

# Global WebSocket transport
set_default_openai_responses_transport("websocket")
```

### Provider-Level WebSocket

```python
from agents import OpenAIProvider, RunConfig

provider = OpenAIProvider(
    use_responses_websocket=True,
    websocket_base_url="wss://your-proxy.example/v1",
    responses_websocket_options={"ping_interval": 20.0, "ping_timeout": 60.0},
)

result = await Runner.run(agent, "Hello", run_config=RunConfig(model_provider=provider))
```

### MultiProvider for Mixed Routing

```python
from agents import MultiProvider, RunConfig

provider = MultiProvider(
    openai_base_url="https://openrouter.ai/api/v1",
    openai_api_key="...",
    openai_use_responses_websocket=True,
    openai_prefix_mode="model_id",
)

agent = Agent(name="Agent", model="openai/gpt-4.1")
result = await Runner.run(agent, "Hello", run_config=RunConfig(model_provider=provider))
```

## Runner-Managed Retries

Explicit opt-in retry logic for transient failures:

```python
from agents import Agent, ModelSettings, ModelRetrySettings, retry_policies

agent = Agent(
    name="Reliable Agent",
    model="gpt-5.5",
    model_settings=ModelSettings(
        retry=ModelRetrySettings(
            max_retries=4,
            backoff={
                "initial_delay": 0.5,
                "max_delay": 5.0,
                "multiplier": 2.0,
                "jitter": True,
            },
            policy=retry_policies.any(
                retry_policies.provider_suggested(),
                retry_policies.retry_after(),
                retry_policies.network_error(),
                retry_policies.http_status([408, 429, 500, 502, 503, 504]),
            ),
        ),
    ),
)
```

### Built-in Retry Policies

| Policy | Behavior |
|--------|----------|
| `retry_policies.never()` | Never retry |
| `retry_policies.provider_suggested()` | Follow provider retry advice |
| `retry_policies.network_error()` | Retry on transient network failures |
| `retry_policies.http_status([...])` | Retry on specific HTTP status codes |
| `retry_policies.retry_after()` | Respect retry-after headers |
| `retry_policies.any(...)` | Retry when any nested policy approves |
| `retry_policies.all(...)` | Retry only when all nested policies approve |

## Third-Party Adapters

### Any-LLM

```bash
pip install 'openai-agents[any-llm]'
```

```python
from agents import Agent, MultiProvider

provider = MultiProvider()
agent = Agent(name="Agent", model="any-llm/anthropic/claude-sonnet-4-20250514")
```

### LiteLLM

```bash
pip install 'openai-agents[litellm]'
```

```python
from agents.extensions.models.litellm_model import LitellmModel

model = LitellmModel(model="anthropic/claude-sonnet-4-20250514")
agent = Agent(name="Agent", model=model)
```

## Common Pitfalls

- **Responses API not supported**: Many non-OpenAI providers need `OpenAIChatCompletionsModel` or `use_responses="never"`
- **Structured output limitations**: Some providers reject JSON schema output; check provider docs
- **Tracing key conflict**: Non-OpenAI API keys can't export traces to OpenAI — use `set_tracing_export_api_key`
- **Feature gaps across providers**: OpenAI supports structured outputs, multimodal, hosted tools — many providers lack these

## Related Topics

- **Running Agents:** `03-running-agents.md` — RunConfig model overrides
- **Streaming:** `06-streaming.md` — WebSocket transport for streaming
- **Tracing:** `12-tracing.md` — Tracing with non-OpenAI models
