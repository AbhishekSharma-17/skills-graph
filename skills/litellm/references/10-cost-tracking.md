# Cost Tracking

> Source: https://docs.litellm.ai/docs/completion/token_usage • Written for litellm v1.52.x

LiteLLM ships with a built-in pricing table for every supported provider model. It can compute per-call cost, count tokens, and (via the Proxy) enforce per-key/per-team budgets.

## Per-call cost

Every `completion()` response carries usage tokens. Convert to dollars:

```python
import litellm
from litellm import completion

resp = completion(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])

cost = litellm.completion_cost(completion_response=resp)
print(f"${cost:.6f}")
```

`completion_cost` knows the model and looks up `litellm.model_cost[model]` for input/output rates per 1K tokens.

You can also compute cost manually:
```python
input_tokens = resp.usage.prompt_tokens
output_tokens = resp.usage.completion_tokens
cost = litellm.cost_per_token(
    model="gpt-4o-mini",
    prompt_tokens=input_tokens,
    completion_tokens=output_tokens,
)
print(cost)  # (prompt_cost, completion_cost) in USD
```

## Token counting (without calling the model)

```python
from litellm import token_counter

n = token_counter(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello world"}],
)
print(n)
```

Internally uses `tiktoken` for OpenAI-family models and the appropriate tokenizer per provider. Falls back to a heuristic for unknown models.

## Get model context window

```python
from litellm import get_max_tokens, get_model_info

print(get_max_tokens("gpt-4o-mini"))
# 128000

info = get_model_info("anthropic/claude-3-5-sonnet-20241022")
print(info)
# {
#   "max_tokens": 8192,
#   "max_input_tokens": 200000,
#   "max_output_tokens": 8192,
#   "input_cost_per_token": 3e-06,
#   "output_cost_per_token": 1.5e-05,
#   "litellm_provider": "anthropic",
#   "mode": "chat",
#   ...
# }
```

## Registering custom model pricing

For self-hosted or fine-tuned models LiteLLM doesn't know:

```python
import litellm

litellm.register_model({
    "openai/my-finetuned-llama": {
        "max_tokens": 8192,
        "input_cost_per_token": 0.0000005,
        "output_cost_per_token": 0.0000015,
        "litellm_provider": "openai",
        "mode": "chat",
    }
})
```

Now `completion_cost` works for that model.

## Proxy: per-key budgets

```bash
curl -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer sk-master" \
  -d '{
    "models": ["gpt-4o-mini"],
    "max_budget": 25.00,
    "budget_duration": "30d",
    "metadata": {"team": "marketing"}
  }'
```

The proxy tracks spend per virtual key in Postgres. When `max_budget` is hit, the key is blocked until reset.

## Proxy: per-team budgets

```bash
curl -X POST http://localhost:4000/team/new \
  -H "Authorization: Bearer sk-master" \
  -d '{
    "team_alias": "marketing",
    "max_budget": 500.00,
    "models": ["gpt-4o-mini", "claude-sonnet"]
  }'
```

Then create keys under that team — they share the budget pool.

## Proxy: spend logs

```bash
curl http://localhost:4000/spend/logs \
  -H "Authorization: Bearer sk-master"
```

Returns per-request rows: `request_id, model, user, team, spend, input_tokens, output_tokens, start_time, end_time`.

## Cache hit cost

When responding from cache, LiteLLM reports `cost = 0` (the cached call cost nothing). Track cache savings via:
```python
print(resp._hidden_params.get("cache_hit"))
```

## Streaming cost

Streamed responses include token counts only if `stream_options={"include_usage": True}` is set. Otherwise LiteLLM estimates via `stream_chunk_builder` (uses tokenizer on the assembled output).

## Common pitfalls

- **Custom model → cost is None** — Register it via `register_model` first.
- **Tools / vision input not in token count** — Token counters underestimate when you pass image_url or tool definitions; vision tokens are added by the provider, not the tokenizer.
- **Batch endpoints discounted** — OpenAI batch API is 50% cheaper but LiteLLM uses the standard rate. Set custom pricing if using batch.
- **Cached input pricing** — Anthropic prompt caching and OpenAI prompt caching have separate read/write rates. The pricing table accounts for them only when the provider returns `cache_read_input_tokens` in usage.
- **Budgets without DB** — `max_budget` requires `database_url` in the proxy config; otherwise it's silently ignored.

## Related
- Caching for cost reduction → `08-caching.md`
- Proxy server admin → `06-proxy-server.md`
