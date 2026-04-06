# Async & Concurrency

> Source: https://docs.litellm.ai/docs/completion/stream • Written for litellm v1.52.x

LiteLLM ships native async support via `acompletion`. Use it for any high-throughput or concurrent workload.

## Basic async call

```python
import asyncio
from litellm import acompletion

async def main():
    response = await acompletion(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

`acompletion` accepts the exact same parameters as `completion`. The only difference is that it returns a coroutine.

## Concurrent requests

Use `asyncio.gather` to fan out:

```python
import asyncio
from litellm import acompletion

async def ask(prompt: str) -> str:
    resp = await acompletion(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

async def main():
    prompts = ["Translate hello to French", "Translate hello to German", "..."]
    results = await asyncio.gather(*(ask(p) for p in prompts))
    for r in results:
        print(r)

asyncio.run(main())
```

## Bounded concurrency with a semaphore

Avoid hammering the provider — rate limits hurt:

```python
import asyncio
from litellm import acompletion

sem = asyncio.Semaphore(10)  # 10 in-flight calls max

async def ask(prompt: str) -> str:
    async with sem:
        resp = await acompletion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            num_retries=2,
        )
        return resp.choices[0].message.content

async def main():
    results = await asyncio.gather(*(ask(p) for p in prompts))
```

## Batching with `litellm.batch_completion`

Sync helper to issue many calls in parallel under the hood:

```python
from litellm import batch_completion

responses = batch_completion(
    model="gpt-4o-mini",
    messages=[
        [{"role": "user", "content": "Q1"}],
        [{"role": "user", "content": "Q2"}],
        [{"role": "user", "content": "Q3"}],
    ],
)
for r in responses:
    print(r.choices[0].message.content)
```

There's also `batch_completion_models` (different model per call) and `batch_completion_models_all_responses` (one prompt to many models).

## Async streaming

Already covered in `03-streaming.md`, but the shape is:

```python
async for chunk in await acompletion(model=..., messages=..., stream=True):
    ...
```

Note the `await` is on `acompletion`, not on the iteration — you await the coroutine to get the async iterator.

## Retries & timeouts in async

```python
await acompletion(
    model="gpt-4o-mini",
    messages=[...],
    timeout=30,             # per-attempt seconds
    num_retries=3,          # exponential backoff between attempts
)
```

If you need a hard ceiling across all retries, wrap the call:
```python
async with asyncio.timeout(60):
    resp = await acompletion(...)
```

## httpx clients

LiteLLM uses an internal `httpx.AsyncClient`. You can pass your own for connection pooling control:

```python
import httpx
from litellm import acompletion

client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
)

await acompletion(
    model="gpt-4o-mini",
    messages=[...],
    client=client,
)
```

This matters at high concurrency — the default client has lower connection limits.

## Common pitfalls

- **Calling `completion` from async code** — Blocks the event loop. Always use `acompletion` in async contexts.
- **`asyncio.gather` without bounds** — A list of 10,000 prompts will trigger rate limit errors. Use a semaphore.
- **Sharing one process across event loops** — `asyncio.run` creates a new loop each call. For long-lived servers use one loop.
- **Ignoring `RateLimitError`** — In async fan-out, one rate limit failure cascades. Use retries + the Router for distribution (`05-router.md`).

## Related
- Router for load balancing → `05-router.md`
- Retries & fallbacks → `07-fallbacks-retries.md`
