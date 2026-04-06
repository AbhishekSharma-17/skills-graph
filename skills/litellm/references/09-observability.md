# Observability

> Source: https://docs.litellm.ai/docs/observability/callbacks • Written for litellm v1.52.x

LiteLLM emits structured events for every call (success, failure, stream completion). You can route them to dozens of observability backends with one line of config.

## Built-in integrations

| Backend | Setting |
|---------|---------|
| Langfuse | `"langfuse"` |
| Langsmith | `"langsmith"` |
| Helicone | `"helicone"` |
| Lunary | `"lunary"` |
| Arize Phoenix | `"arize"` |
| Weights & Biases | `"wandb"` |
| Datadog | `"datadog"` |
| Logfire | `"logfire"` |
| OpenTelemetry | `"otel"` |
| Prometheus | `"prometheus"` (proxy only) |
| Sentry | `"sentry"` |
| Slack | `"slack"` |
| MLflow | `"mlflow"` |
| Custom function | callable |

## SDK setup

```python
import litellm

litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse", "sentry"]
```

Set the integration's env vars (e.g. `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`) and that's it — every `completion()` call now logs.

## Adding metadata

Pass `metadata` to attach trace context, user IDs, session IDs, tags:

```python
completion(
    model="gpt-4o-mini",
    messages=[...],
    metadata={
        "trace_id": "trace-123",
        "user_id": "user-42",
        "session_id": "session-7",
        "tags": ["onboarding", "first-message"],
        "generation_name": "intro_summary",
    },
)
```

Each integration maps these to its own trace model (Langfuse traces, Langsmith runs, OTEL spans).

## Custom callbacks

Implement a function that receives the call data:

```python
import litellm

def my_logger(kwargs, completion_response, start_time, end_time):
    """Synchronous success callback."""
    print({
        "model": kwargs["model"],
        "prompt_tokens": completion_response.usage.prompt_tokens,
        "completion_tokens": completion_response.usage.completion_tokens,
        "duration_s": (end_time - start_time).total_seconds(),
        "user": kwargs.get("metadata", {}).get("user_id"),
    })

litellm.success_callback = [my_logger]
```

Async version:
```python
async def my_async_logger(kwargs, completion_response, start_time, end_time):
    ...

litellm.success_callback = [my_async_logger]
```

There's also `litellm.failure_callback` (called with `kwargs, exception, start, end`) and `litellm.async_success_callback`.

## Custom logger class

For more structured handling, subclass `CustomLogger`:

```python
from litellm.integrations.custom_logger import CustomLogger
import litellm

class MyHandler(CustomLogger):
    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        ...

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        ...

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        ...

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        ...

litellm.callbacks = [MyHandler()]
```

## OpenTelemetry

```python
litellm.callbacks = ["otel"]
```

Set the standard OTEL env vars:
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=my-llm-app
```

LiteLLM emits spans named `litellm_request` with attributes for model, provider, tokens, latency, and any `metadata` you pass.

## Proxy callbacks

Same callbacks, configured in `config.yaml`:

```yaml
litellm_settings:
  success_callback: ["langfuse", "prometheus"]
  failure_callback: ["langfuse", "sentry"]
```

Per-request metadata can be sent in the OpenAI request body via the `metadata` field — the proxy strips it before forwarding to the upstream provider:

```python
client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    extra_body={"metadata": {"user_id": "abc", "trace_id": "..."}},
)
```

## Prometheus (proxy)

```yaml
litellm_settings:
  success_callback: ["prometheus"]
```

Exposes `/metrics` with:
- `litellm_requests_total{model,team}`
- `litellm_request_latency_seconds{model}`
- `litellm_input_tokens_total{model}`
- `litellm_output_tokens_total{model}`
- `litellm_spend_total{model,team}`

## Common pitfalls

- **Callback exceptions silently swallowed** — A buggy callback won't break inference but you'll see no logs. Test it.
- **Sync callback in async code** — Slows the event loop. Prefer `async_success_callback`.
- **Forgetting `metadata`** — Without trace IDs you lose end-to-end tracing.
- **PII in logs** — Langfuse/Helicone capture full prompts. Strip sensitive content first if compliance matters.
- **Cost shown as 0** — LiteLLM only computes cost if it knows the model. Custom/private models need entries in `litellm.model_cost` or a `register_model` call.

## Related
- Cost tracking detail → `10-cost-tracking.md`
- Proxy server config → `06-proxy-server.md`
