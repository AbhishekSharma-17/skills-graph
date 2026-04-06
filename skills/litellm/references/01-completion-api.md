# Completion API

> Source: https://docs.litellm.ai/docs/completion/input • Written for litellm v1.52.x

The `completion()` function is the heart of LiteLLM. It mirrors `openai.chat.completions.create` but works for every supported provider.

## Signature

```python
from litellm import completion

response = completion(
    model: str,                       # "provider/model_id"
    messages: list[dict],             # OpenAI-format messages
    temperature: float | None = None,
    top_p: float | None = None,
    n: int | None = None,
    stream: bool = False,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    max_completion_tokens: int | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    logit_bias: dict | None = None,
    user: str | None = None,
    response_format: dict | None = None,    # JSON mode / structured outputs
    seed: int | None = None,
    tools: list[dict] | None = None,        # function calling
    tool_choice: str | dict | None = None,
    parallel_tool_calls: bool | None = None,
    timeout: float | None = None,
    api_base: str | None = None,
    api_key: str | None = None,
    api_version: str | None = None,
    num_retries: int = 0,
    fallbacks: list[str] | None = None,
    metadata: dict | None = None,           # for logging callbacks
    **provider_specific_params,
)
```

## Messages

Standard OpenAI message shape:
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is 2 + 2?"},
    {"role": "assistant", "content": "4"},
    {"role": "user", "content": "Multiply that by 7."},
]
```

### Multimodal (vision)
```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": "https://.../cat.jpg"}},
    ],
}]
```
LiteLLM translates this to each provider's native format (Anthropic blocks, Bedrock content, etc.).

## Response shape

Every provider returns the same OpenAI-shaped object:

```python
ModelResponse(
    id="chatcmpl-...",
    object="chat.completion",
    created=1717171717,
    model="gpt-4o-mini",
    choices=[
        Choices(
            index=0,
            message=Message(role="assistant", content="..."),
            finish_reason="stop",   # or "length", "tool_calls", "content_filter"
        )
    ],
    usage=Usage(
        prompt_tokens=12,
        completion_tokens=8,
        total_tokens=20,
    ),
)
```

Access pattern:
```python
text = response.choices[0].message.content
tokens_in = response.usage.prompt_tokens
tokens_out = response.usage.completion_tokens
finish = response.choices[0].finish_reason
```

LiteLLM responses are also dict-subscriptable: `response["choices"][0]["message"]["content"]`.

## Setting credentials

Three options, in order of precedence:

1. **Per-call kwargs** — `completion(..., api_key="sk-...")`
2. **Per-call env override** — `os.environ["OPENAI_API_KEY"] = "..."` before the call
3. **`.env` loaded by your app** — LiteLLM reads env vars at call time

For Azure / Vertex / Bedrock you also need `api_base`, `api_version`, and/or AWS credentials. See `02-providers.md`.

## Drop-in replacement for `openai`

LiteLLM exposes a sub-module that mimics the OpenAI Python client exactly:
```python
from litellm import openai_proxy as openai  # or use the proxy directly

# But the more common pattern is just:
from litellm import completion
resp = completion(model="gpt-4o-mini", messages=[...])
```

Existing code using `openai.ChatCompletion.create(...)` ports by replacing the import.

## Common parameters

| Parameter | Purpose | Notes |
|-----------|---------|-------|
| `temperature` | Randomness 0–2 | Some providers cap at 1.0; LiteLLM clamps automatically |
| `max_tokens` | Output cap | Renamed to provider's native field (e.g. `max_tokens_to_sample` for old Anthropic) |
| `stop` | Stop sequences | List or string; provider-translated |
| `seed` | Deterministic sampling | Only some providers honor it |
| `response_format` | `{"type": "json_object"}` or schema | See `11-structured-outputs.md` |
| `tools` | Function calling | OpenAI-format tool defs work everywhere |
| `timeout` | Request timeout (seconds) | Default ~600s |
| `num_retries` | Retry on transient errors | See `07-fallbacks-retries.md` |

## Provider-specific kwargs

Any unknown kwarg is passed through to the provider:
```python
completion(
    model="anthropic/claude-3-5-sonnet-20241022",
    messages=[...],
    extra_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"},
)
```

## Errors

LiteLLM raises OpenAI-compatible exception classes:
```python
from litellm import (
    APIError,
    Timeout,
    RateLimitError,
    BadRequestError,
    AuthenticationError,
    ServiceUnavailableError,
    ContextWindowExceededError,
    ContentPolicyViolationError,
)

try:
    completion(model="gpt-4o-mini", messages=[...])
except RateLimitError:
    ...
except ContextWindowExceededError:
    ...   # automatically triggers context_window_fallbacks if configured
```

## Common pitfalls

- **`max_tokens` ignored** — Some newer models use `max_completion_tokens`; LiteLLM accepts both.
- **Tool calls returned as strings** — Always parse `message.tool_calls[i].function.arguments` with `json.loads`.
- **Response not OpenAI-shaped** — You're probably using the raw provider client somewhere. Always import from `litellm`.
- **Streaming + retries** — Retries apply per-attempt; partial streamed content is discarded on retry.

## Related
- Streaming → `03-streaming.md`
- Async version → `04-async.md`
- Tool/function calling → `11-structured-outputs.md`
