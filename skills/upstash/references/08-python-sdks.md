# Upstash — Python SDKs

## Table of Contents

- [upstash-redis](#upstash-redis) — Init, basic ops, data types, pipeline, transactions, async
- [upstash-ratelimit](#upstash-ratelimit-python) — Rate limiting with three algorithms
- [upstash-qstash](#upstash-qstash-python) — Messaging, scheduling, signature verification
- [upstash-vector](#upstash-vector-python) — Vector storage, search, namespaces, filtering
- [upstash-workflow](#upstash-workflow-python) — Durable serverless workflows
- [Common Pitfalls](#common-pitfalls)

---

## Overview

All Upstash Python SDKs use HTTP/REST (no TCP connections), making them ideal for serverless. Each SDK provides sync and async clients, and supports `from_env()` initialization.

---

## upstash-redis

```bash
pip install upstash-redis
```

### Initialization

```python
from upstash_redis import Redis

redis = Redis(url="https://your-endpoint.upstash.io", token="your-token")
redis = Redis.from_env()  # reads UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN

# Async client
from upstash_redis.asyncio import Redis as AsyncRedis
async_redis = AsyncRedis.from_env()
```

### Basic Operations

```python
redis = Redis.from_env()

redis.set("key", "value")
value = redis.get("key")                    # "value"
redis.set("session:abc", "data", ex=3600)   # with TTL (seconds)
redis.set("lock", "holder", nx=True)        # set-if-not-exists

redis.incr("counter")                       # 1
redis.incrby("counter", 5)                  # 6

redis.expire("key", 300)
redis.delete("key", "counter")
exists = redis.exists("key")

redis.mset({"k1": "v1", "k2": "v2"})
values = redis.mget("k1", "k2")            # ["v1", "v2"]
```

### Hash Operations

```python
redis.hset("user:1", {"name": "Alice", "age": "30"})
name = redis.hget("user:1", "name")       # "Alice"
user = redis.hgetall("user:1")            # {"name": "Alice", "age": "30"}
redis.hexists("user:1", "name")           # True
redis.hdel("user:1", "age")
redis.hincrby("user:1", "age", 1)         # increment numeric field
```

### List Operations

```python
redis.lpush("queue", "task3", "task2", "task1")
redis.rpush("queue", "task4")
first = redis.lpop("queue")               # "task1"
last = redis.rpop("queue")                # "task4"
items = redis.lrange("queue", 0, -1)      # all items
redis.llen("queue")                        # length
redis.ltrim("queue", 0, 99)               # keep first 100
```

### Set Operations

```python
redis.sadd("tags", "python", "redis", "serverless")
members = redis.smembers("tags")           # {"python", "redis", "serverless"}
redis.sismember("tags", "python")          # True
redis.srem("tags", "redis")
redis.sunion("set1", "set2")              # union
redis.sinter("set1", "set2")              # intersection
redis.sdiff("set1", "set2")              # difference
```

### Sorted Set Operations

```python
redis.zadd("leaderboard", {"alice": 100, "bob": 85})
redis.zrank("leaderboard", "alice")        # 0-based rank
redis.zscore("leaderboard", "bob")         # 85.0
redis.zrange("leaderboard", 0, -1, withscores=True)
redis.zrevrange("leaderboard", 0, 2, withscores=True)
redis.zrangebyscore("leaderboard", 80, 95)
redis.zincrby("leaderboard", 10, "bob")   # 95.0
redis.zrem("leaderboard", "bob")
```

### JSON Operations

All JSON paths use JSONPath syntax (prefix `$`). Results from `json.get` are arrays.

```python
redis.json.set("doc:1", "$", {"name": "Alice", "age": 30, "scores": [95, 87]})
doc = redis.json.get("doc:1", "$")
name = redis.json.get("doc:1", "$.name")           # ["Alice"]
redis.json.set("doc:1", "$.age", 31)               # update field
redis.json.arrappend("doc:1", "$.scores", 88)      # append to array
redis.json.numincrby("doc:1", "$.age", 1)          # increment
redis.json.delete("doc:1", "$.scores")             # delete path
```

### Pipeline and Transactions

```python
# Pipeline — batch commands into a single HTTP request
pipe = redis.pipeline()
pipe.set("key1", "value1")
pipe.incr("counter")
pipe.get("key1")
results = pipe.execute()  # [True, 1, "value1"]

# Transaction — atomic execution
tx = redis.multi()
tx.decrby("balance:alice", 25)
tx.incrby("balance:bob", 25)
results = tx.execute()    # [75, 25]
```

### Async Usage

Every method has an async counterpart via the `asyncio` submodule. Pipelines and transactions also support `await`.

```python
from upstash_redis.asyncio import Redis

redis = Redis.from_env()

async def main():
    await redis.set("key", "value")
    value = await redis.get("key")

    pipe = redis.pipeline()
    pipe.set("a", "1")
    pipe.get("a")
    results = await pipe.execute()
```

---

## upstash-ratelimit (Python)

```bash
pip install upstash-ratelimit
```

```python
from upstash_ratelimit import Ratelimit, SlidingWindow
from upstash_redis import Redis

ratelimit = Ratelimit(
    redis=Redis.from_env(),
    limiter=SlidingWindow(max_requests=10, window=10),  # window in seconds
)

response = ratelimit.limit("user:123")
# response.allowed, response.remaining, response.reset (Unix timestamp)
```

### Algorithms

```python
from upstash_ratelimit import FixedWindow, SlidingWindow, TokenBucket

FixedWindow(max_requests=10, window=60)                    # resets at fixed intervals
SlidingWindow(max_requests=10, window=60)                  # weighted sliding window
TokenBucket(max_tokens=10, refill_rate=5, interval=30)     # burst-capable
```

### Async Support {#ratelimit-async-support}

```python
from upstash_ratelimit.asyncio import Ratelimit
from upstash_redis.asyncio import Redis

ratelimit = Ratelimit(redis=Redis.from_env(), limiter=SlidingWindow(max_requests=10, window=10))
response = await ratelimit.limit(user_id)
```

---

## upstash-qstash (Python)

Package is named `qstash` (not `upstash-qstash`).

```bash
pip install qstash
```

### Publishing Messages

```python
from qstash import QStash

qstash = QStash(token="your-qstash-token")

qstash.message.publish_json(
    url="https://your-endpoint.com/api/process",
    body={"task": "process", "id": "123"},
    delay=300,   # optional delay in seconds
    retries=3,   # optional retries
)

# Fan-out to multiple endpoints via topic
qstash.message.publish_json(topic="notifications", body={"type": "alert"})
```

### Scheduling

```python
qstash.schedule.create(
    destination="https://your-endpoint.com/api/report",
    cron="0 9 * * *",
    body='{"type": "daily_report"}',
)
schedules = qstash.schedule.list()
qstash.schedule.delete(schedule_id="sched_xxx")
```

### Signature Verification

```python
from qstash import Receiver

receiver = Receiver(current_signing_key="sig_current...", next_signing_key="sig_next...")

def handle_webhook(request):
    body = request.body.decode("utf-8")
    signature = request.headers.get("upstash-signature")
    receiver.verify(body=body, signature=signature)  # raises on invalid
```

---

## upstash-vector (Python)

```bash
pip install upstash-vector
```

### Usage {#vector-usage}

```python
from upstash_vector import Index

index = Index(url="https://your-index.upstash.io", token="your-token")
index = Index.from_env()  # reads UPSTASH_VECTOR_REST_URL + UPSTASH_VECTOR_REST_TOKEN

# Upsert with text (uses built-in embedding) or pre-computed vectors
index.upsert([
    {"id": "doc-1", "data": "Upstash is a serverless platform", "metadata": {"source": "docs"}},
])
# Or: {"id": "vec-1", "vector": [0.1, 0.2, ...], "metadata": {...}}

# Query
results = index.query(data="serverless database", top_k=5, include_metadata=True)
for r in results:
    print(f"{r.id}: {r.score} — {r.metadata}")

index.fetch(["doc-1"], include_metadata=True)
index.delete(["doc-1"])
info = index.info()
```

### Namespaces

```python
ns = index.namespace("production")
ns.upsert([{"id": "prod-1", "data": "Production doc", "metadata": {"env": "prod"}}])
results = ns.query(data="production data", top_k=5, include_metadata=True)
ns.delete(["prod-1"])
ns.reset()  # delete all vectors in namespace
```

### Metadata Filtering

SQL-like filter syntax. Operators: `=`, `!=`, `<`, `<=`, `>`, `>=`, `IN`, `AND`, `OR`.

```python
results = index.query(
    data="serverless platform",
    top_k=10,
    filter="source IN ('docs', 'blog') AND year >= 2024",
    include_metadata=True,
)
```

---

## upstash-workflow (Python)

Durable serverless workflows with automatic retries. Each `context.run()` step executes at most once; interrupted workflows resume from the last completed step.

```bash
pip install upstash-workflow
```

```python
from fastapi import FastAPI
from upstash_workflow.fastapi import Serve

app = FastAPI()
serve = Serve(app)

@serve.post("/api/workflow")
async def my_workflow(context):
    data = await context.run("fetch-data", lambda: fetch_from_api())
    await context.sleep("wait", 60)  # durable sleep
    result = await context.run("process", lambda: transform(data))
    await context.run("notify", lambda: send_email(result))
```

---

## Common Pitfalls

1. **Async imports** — import from the `asyncio` submodule for async usage (e.g., `from upstash_redis.asyncio import Redis`).
2. **`from_env()` variable names** — expects `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` exactly.
3. **Pipeline result ordering** — `execute()` returns results in command order; no key-based lookup.
4. **JSON paths start with `$`** — e.g., `$.name` not `name`. `json.get` returns arrays.
5. **Ratelimit window in seconds** — Python SDK uses integers, not string durations like TypeScript.
6. **QStash package name** — install `qstash`, not `upstash-qstash`.
7. **Vector `data` vs `vector`** — `data` (string) for built-in embeddings; `vector` (list[float]) for pre-computed. Don't mix.
8. **No connection pooling** — HTTP-based; no pools, no close needed.
9. **Token security** — use `from_env()` or secrets manager; never hardcode tokens.
10. **Workflow idempotency** — `context.run()` steps may retry; keep them idempotent.
