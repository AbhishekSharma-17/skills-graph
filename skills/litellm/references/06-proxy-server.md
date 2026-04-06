# Proxy Server

> Source: https://docs.litellm.ai/docs/simple_proxy • Written for litellm v1.52.x

The LiteLLM Proxy is a self-hosted HTTP gateway that exposes any provider behind an OpenAI-compatible API. Run it once, point all your apps at it, get unified auth, logging, budgets, and rate limits.

## Install

```bash
pip install 'litellm[proxy]'
# or
docker run -p 4000:4000 ghcr.io/berriai/litellm:main-stable --config /app/config.yaml
```

## Minimum config.yaml

```yaml
model_list:
  - model_name: gpt-4o-mini             # alias clients use
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: bedrock-haiku
    litellm_params:
      model: bedrock/anthropic.claude-3-haiku-20240307-v1:0
      aws_region_name: us-east-1
```

`os.environ/VAR_NAME` reads from the proxy process environment at startup.

## Run it

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
litellm --config config.yaml --port 4000
```

## Calling the proxy

It speaks the OpenAI wire protocol. Any OpenAI client works:

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-1234",                          # virtual key (or "anything" if auth disabled)
    base_url="http://localhost:4000",
)

resp = client.chat.completions.create(
    model="claude-sonnet",                      # alias from config.yaml
    messages=[{"role": "user", "content": "Hi"}],
)
```

```bash
curl http://localhost:4000/chat/completions \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'
```

## Authentication & virtual keys

To require API keys, set a master key and (optionally) attach a database for issuing virtual keys per team:

```yaml
general_settings:
  master_key: sk-master-supersecret           # admin key for /key/* endpoints
  database_url: postgres://user:pw@host/db    # required for virtual keys
```

Issue a virtual key:
```bash
curl -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer sk-master-supersecret" \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["gpt-4o-mini", "claude-sonnet"],
    "max_budget": 10.0,
    "duration": "30d",
    "metadata": {"team": "frontend"}
  }'
```

Returns `{"key": "sk-..."}` for that team. The proxy enforces the model allow-list and budget per key.

## Routing & load balancing

Add multiple deployments with the same `model_name`:

```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: azure/east-deployment
      api_key: os.environ/AZURE_KEY_EAST
      api_base: https://east.openai.azure.com/
      api_version: "2024-08-01-preview"
    tpm: 240000
    rpm: 1800
  - model_name: gpt-4
    litellm_params:
      model: azure/west-deployment
      api_key: os.environ/AZURE_KEY_WEST
      api_base: https://west.openai.azure.com/
      api_version: "2024-08-01-preview"
    tpm: 240000
    rpm: 1800

router_settings:
  routing_strategy: usage-based-routing-v2
  redis_host: localhost
  redis_port: 6379
```

## Fallbacks

```yaml
litellm_settings:
  fallbacks: [{"gpt-4": ["claude-sonnet"]}]
  context_window_fallbacks: [{"gpt-4": ["claude-sonnet-200k"]}]
  num_retries: 2
  request_timeout: 60
```

## Logging callbacks

```yaml
litellm_settings:
  success_callback: ["langfuse", "prometheus"]
  failure_callback: ["langfuse"]
  cache: true
  cache_params:
    type: redis
    host: localhost
    port: 6379
```

Set `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` in env. See `09-observability.md`.

## Health & admin endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness check (checks each deployment) |
| `GET /health/readiness` | Readiness probe |
| `GET /v1/models` | List available aliases |
| `POST /chat/completions` | Main inference endpoint |
| `POST /completions` | Legacy completions |
| `POST /embeddings` | Embedding endpoint |
| `POST /key/generate` | Issue virtual key (admin) |
| `POST /key/info` | Inspect a key |
| `POST /key/delete` | Revoke a key |
| `GET /spend/logs` | Per-request spend logs |
| `GET /metrics` | Prometheus metrics (if enabled) |

## Deployment

The proxy is stateless except for the optional Postgres + Redis backends. Typical production layout:
- 2+ replicas behind a load balancer
- Postgres for keys, teams, budgets, spend logs
- Redis for cache, rate limit accounting, router state

A pre-built Helm chart and Dockerfile are in the GitHub repo.

## Common pitfalls

- **No `master_key`** — `/key/*` endpoints will 401. You must set one to enable virtual keys.
- **Forgetting `database_url`** — Virtual keys need Postgres; otherwise only the master key works.
- **`os.environ/VAR` not interpolated** — The literal string is used if the env var is missing at startup. Check `/health`.
- **Routing across processes** — Without Redis, each replica routes independently and rate limit accounting drifts.
- **Calling `/v1/chat/completions` vs `/chat/completions`** — Both work; the OpenAI client adds the `/v1` automatically.

## Related
- Routing logic → `05-router.md`
- Observability config → `09-observability.md`
- Cost & budget enforcement → `10-cost-tracking.md`
