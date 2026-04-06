# Router (SDK)

> Source: https://docs.litellm.ai/docs/routing • Written for litellm v1.52.x

The `Router` is LiteLLM's in-process load balancer. You define one **logical model name** that fans out across multiple **deployments** (e.g. `azure-east`, `azure-west`, `openai-direct`) — and the Router picks one per call based on a strategy.

This is the SDK equivalent of what the Proxy does over HTTP.

## When to use it

- You have multiple Azure deployments of the same model and want to spread load.
- You want fallbacks across providers when one is throttled.
- You want per-deployment rate limit awareness.
- You want a clean abstraction so app code says `model="gpt-4"` and never knows about regions.

## Basic setup

```python
from litellm import Router

model_list = [
    {
        "model_name": "gpt-4",  # logical alias used by your app
        "litellm_params": {
            "model": "azure/my-east-deployment",
            "api_key": os.environ["AZURE_API_KEY_EAST"],
            "api_base": "https://east.openai.azure.com/",
            "api_version": "2024-08-01-preview",
        },
        "tpm": 240000,   # tokens per minute capacity
        "rpm": 1800,     # requests per minute capacity
    },
    {
        "model_name": "gpt-4",
        "litellm_params": {
            "model": "azure/my-west-deployment",
            "api_key": os.environ["AZURE_API_KEY_WEST"],
            "api_base": "https://west.openai.azure.com/",
            "api_version": "2024-08-01-preview",
        },
        "tpm": 240000,
        "rpm": 1800,
    },
    {
        "model_name": "gpt-4",
        "litellm_params": {
            "model": "openai/gpt-4o",
            "api_key": os.environ["OPENAI_API_KEY"],
        },
    },
]

router = Router(model_list=model_list, routing_strategy="usage-based-routing-v2")

response = router.completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
)
```

## Routing strategies

| Strategy | Behavior |
|----------|----------|
| `simple-shuffle` (default) | Random pick weighted by `weight` |
| `least-busy` | Picks the deployment with fewest in-flight requests |
| `usage-based-routing-v2` | Picks based on observed TPM/RPM headroom; needs Redis for cross-process sharing |
| `latency-based-routing` | Picks the deployment with lowest recent latency |
| `cost-based-routing` | Picks the cheapest model for the request |

Set with:
```python
Router(model_list=..., routing_strategy="latency-based-routing")
```

## Async router

```python
response = await router.acompletion(model="gpt-4", messages=[...])
```

`router.aembedding()`, `router.aimage_generation()`, etc. all exist.

## Fallbacks

Define ordered fallback chains per model alias:

```python
router = Router(
    model_list=model_list,
    fallbacks=[
        {"gpt-4": ["claude-sonnet"]},
        {"claude-sonnet": ["gpt-3.5"]},
    ],
    context_window_fallbacks=[
        {"gpt-4": ["claude-sonnet-200k"]},
    ],
    num_retries=2,
    timeout=30,
)
```

Now if every `gpt-4` deployment fails, the router transparently retries against `claude-sonnet`. If the request exceeds `gpt-4`'s context window, it goes to `claude-sonnet-200k`.

## Cooldowns

When a deployment errors, it's automatically cooled down for `cooldown_time` seconds (default 60) and skipped during routing:

```python
Router(
    model_list=model_list,
    cooldown_time=120,                  # seconds
    allowed_fails=3,                    # failures before cooldown
)
```

## Cross-process state via Redis

For multiple Python workers to share routing state (rate-limit accounting, cooldowns):

```python
Router(
    model_list=model_list,
    routing_strategy="usage-based-routing-v2",
    redis_host="localhost",
    redis_port=6379,
    redis_password=None,
)
```

Without Redis, each process makes routing decisions independently — fine for a single worker, suboptimal at scale.

## Pre-call checks

Skip a deployment whose model context can't fit the request:

```python
Router(
    model_list=model_list,
    enable_pre_call_checks=True,
)
```

## Per-call overrides

```python
router.completion(
    model="gpt-4",
    messages=[...],
    metadata={"user_id": "abc"},     # passed to logging callbacks
    fallbacks=["claude-sonnet"],     # ad-hoc fallback for this call
    num_retries=5,                   # override default
)
```

## Common pitfalls

- **Not setting `tpm`/`rpm`** — Usage-based routing falls back to round-robin without capacity hints.
- **Mixing `num_retries` everywhere** — Retries set on `Router` AND on `completion` AND on the proxy compound badly. Set in one place.
- **Forgetting Redis in multi-worker setups** — Each worker rate-limits independently and you'll exceed quotas.
- **Cool-down too short** — Throttled deployments come back immediately and re-fail. Bump `cooldown_time`.

## Related
- Proxy server (same routing over HTTP) → `06-proxy-server.md`
- Fallbacks deep-dive → `07-fallbacks-retries.md`
