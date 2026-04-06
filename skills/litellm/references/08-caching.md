# Caching

> Source: https://docs.litellm.ai/docs/caching/all_caches • Written for litellm v1.52.x

LiteLLM can cache LLM responses in-memory, in Redis, or in S3 — and it supports semantic (embedding-similarity) caching too. Identical (or near-identical) requests return cached results without hitting the provider.

## Cache backends

| Backend | Use case |
|---------|----------|
| `local` | Single-process scripts, dev |
| `redis` | Multi-process, multi-host production |
| `s3` | Cheap long-term storage, batch workloads |
| `redis-semantic` | Cache by semantic similarity (vector embeddings) |
| `qdrant-semantic` | Same, but using Qdrant |

## SDK setup

```python
import litellm
from litellm.caching import Cache

# In-memory
litellm.cache = Cache(type="local")

# Redis
litellm.cache = Cache(
    type="redis",
    host="localhost",
    port=6379,
    password=None,
)

# S3
litellm.cache = Cache(
    type="s3",
    s3_bucket_name="my-llm-cache",
    s3_region_name="us-east-1",
)
```

After setting `litellm.cache`, every `completion()` / `acompletion()` automatically reads/writes the cache.

## Cache key

By default the key is a hash of `model + messages + temperature + max_tokens + tools` (the request fingerprint). Identical requests hit the cache.

To force-bypass for a single call:
```python
completion(model=..., messages=..., cache={"no-cache": True})
```

To force a write but not a read (refresh):
```python
completion(model=..., messages=..., cache={"no-store": False, "no-cache": True})
```

## TTL

```python
litellm.cache = Cache(type="redis", host="...", ttl=3600)  # 1 hour
```

Per-call override:
```python
completion(model=..., messages=..., cache={"ttl": 60})
```

## Semantic caching (Redis)

Cache by **embedding similarity** rather than exact match. Two semantically-similar prompts return the same response:

```python
litellm.cache = Cache(
    type="redis-semantic",
    host="localhost",
    port=6379,
    redis_semantic_cache_embedding_model="text-embedding-3-small",
    similarity_threshold=0.9,    # 0–1, higher = stricter
)
```

LiteLLM embeds each request, looks for nearby vectors, and returns the cached response if similarity ≥ threshold.

This requires the Redis Stack image (with RediSearch and RedisJSON modules).

## Caching only certain calls

Toggle per-call without disabling the global cache:

```python
litellm.cache = Cache(type="redis", host="...")

# uses cache
completion(model="gpt-4o-mini", messages=[...])

# bypasses cache for this call
completion(model="gpt-4o-mini", messages=[...], caching=False)
```

## Proxy caching

In `config.yaml`:
```yaml
litellm_settings:
  cache: true
  cache_params:
    type: redis
    host: localhost
    port: 6379
    password: ""
    ttl: 3600
    supported_call_types: ["acompletion", "completion", "embedding"]
```

Clients see cached responses transparently. Per-request bypass via header:
```
Cache-Control: no-cache
```

## What gets cached

- `completion` / `acompletion` (chat)
- `embedding` / `aembedding`
- `text_completion` (legacy)
- Streaming: by default streamed responses are NOT cached. Enable with:
  ```python
  litellm.cache = Cache(type="redis", host="...", supported_call_types=["completion", "acompletion"])
  ```
  Streamed cache hits are replayed as a stream.

## Cache hit signal

The response object carries cache metadata:
```python
resp = completion(...)
print(resp._hidden_params.get("cache_hit"))  # True | False
```

## Common pitfalls

- **Tools/`response_format` cache misses** — Different `tools` arrays produce different keys. Tiny ordering changes break the cache. Sort tool lists.
- **Caching with random seeds** — `temperature > 0` without `seed` is non-deterministic, but the cache will still return the first answer forever. Surprising for users.
- **Semantic cache collisions** — Threshold too low → wrong answers returned for different intents. Start at 0.95+ and tune down.
- **Streaming + cache** — On a hit, you replay the cached chunks; the user can't tell the difference, but `usage` may be a recomputed estimate.
- **TTL too long** — Stale answers when system prompts or tool definitions change. Bust the cache on deployment.

## Related
- Observability of cache hits → `09-observability.md`
- Cost savings from caching → `10-cost-tracking.md`
