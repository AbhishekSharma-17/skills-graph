# Fallbacks & Retries

> Source: https://docs.litellm.ai/docs/completion/reliable_completions • Written for litellm v1.52.x

LiteLLM has three layered reliability mechanisms: **retries**, **fallbacks**, and **context-window fallbacks**. They can be combined but you should understand how they nest.

## Retries (same model, same call)

Transient errors (rate limits, 5xx, network blips) get retried with exponential backoff:

```python
from litellm import completion

completion(
    model="gpt-4o-mini",
    messages=[...],
    num_retries=3,
    timeout=30,        # per attempt
)
```

Default behavior:
- Initial backoff: 1s, doubles each attempt, capped at 10s.
- Retries on: `RateLimitError`, `APIError`, `Timeout`, `ServiceUnavailableError`.
- Does NOT retry on: `AuthenticationError`, `BadRequestError`, `ContentPolicyViolationError`, `ContextWindowExceededError`.

## Fallbacks (switch to another model)

If all retries fail (or for non-retryable errors), fall back to a different model:

```python
completion(
    model="gpt-4o-mini",
    messages=[...],
    num_retries=2,
    fallbacks=["claude-3-5-sonnet-20241022", "anthropic/claude-3-haiku-20240307"],
)
```

Each fallback model is tried in order. The same `messages` and tool config are reused. The first one to succeed wins.

## Context window fallbacks

When the request exceeds a model's context limit, fail over to a model with a larger window:

```python
completion(
    model="gpt-4o-mini",
    messages=long_messages,
    context_window_fallbacks=[
        {"gpt-4o-mini": ["gpt-4o", "claude-3-5-sonnet-20241022"]},
    ],
)
```

This catches `ContextWindowExceededError` specifically and routes to the next-larger model.

## With the Router

The Router lets you set defaults once and override per call:

```python
from litellm import Router

router = Router(
    model_list=[...],
    num_retries=3,
    request_timeout=30,
    fallbacks=[
        {"gpt-4": ["claude-sonnet"]},
        {"claude-sonnet": ["gpt-3.5-turbo"]},
    ],
    context_window_fallbacks=[
        {"gpt-4": ["claude-sonnet-200k"]},
    ],
    allowed_fails=3,           # failures before deployment cools down
    cooldown_time=60,
)
```

## With the Proxy

In `config.yaml`:
```yaml
litellm_settings:
  num_retries: 3
  request_timeout: 60
  fallbacks: [{"gpt-4": ["claude-sonnet"]}]
  context_window_fallbacks: [{"gpt-4": ["claude-sonnet-200k"]}]
```

Clients calling the proxy get retries and fallbacks transparently.

## Custom retry policies

```python
from litellm import RetryPolicy, completion

policy = RetryPolicy(
    BadRequestErrorRetries=0,
    AuthenticationErrorRetries=0,
    TimeoutErrorRetries=4,
    RateLimitErrorRetries=4,
    ContentPolicyViolationErrorRetries=0,
    InternalServerErrorRetries=4,
)

completion(
    model="gpt-4o-mini",
    messages=[...],
    retry_policy=policy,
)
```

## Custom fallback handlers

```python
def on_fallback(original_exception, fallback_model_name):
    print(f"Falling back to {fallback_model_name} after {original_exception}")

completion(
    model="gpt-4o-mini",
    messages=[...],
    fallbacks=["claude-sonnet"],
    on_fallback=on_fallback,
)
```

## Layering — pick ONE place

The classic mistake: setting `num_retries=3` on the SDK call AND on the Router AND on the Proxy. Then a single failure becomes 3 × 3 × 3 = 27 attempts before the user sees an error, and you've blown your rate limits.

Pick the layer closest to your retry intent:
- **Single Python script** → retries on `completion(...)`
- **Long-lived service with multiple deployments** → retries on `Router`
- **Multi-app gateway** → retries on the Proxy `litellm_settings`, none in clients

## Common pitfalls

- **Compounded retries** — see above.
- **Retrying `BadRequestError`** — Pointless, your input is malformed; use `RetryPolicy` to disable.
- **Fallback to a model that doesn't support tools** — If your call has `tools=[...]` and the fallback model doesn't, it errors immediately. Match capabilities.
- **Context-window fallback skipped** — You're catching the exception yourself before LiteLLM can. Let the library raise.
- **Streaming + fallbacks** — Once a stream starts, partial output is lost on fallback. Avoid both for long generations.

## Related
- Router cooldowns and routing → `05-router.md`
- Proxy reliability config → `06-proxy-server.md`
