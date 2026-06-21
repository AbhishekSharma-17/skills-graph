# Redis — Caching Patterns

> Source: [redis.io/docs](https://redis.io/docs/latest/) — Redis 8.6

## Table of Contents

- [Overview](#overview)
- [Cache-Aside (Lazy Loading)](#cache-aside-lazy-loading)
- [Write-Through](#write-through)
- [Write-Behind (Write-Back)](#write-behind-write-back)
- [Read-Through](#read-through)
- [TTL Strategies](#ttl-strategies)
- [Eviction Policies](#eviction-policies)
- [Cache Invalidation](#cache-invalidation)
- [Cache Stampede Prevention](#cache-stampede-prevention)
- [Distributed Locking](#distributed-locking)
- [Patterns & Best Practices](#patterns--best-practices)
- [Common Pitfalls](#common-pitfalls)

## Overview

Redis is the most popular caching solution. Choosing the right caching pattern depends on your read/write ratio, consistency requirements, and tolerance for stale data.

| Pattern | Reads | Writes | Consistency | Best For |
|---------|-------|--------|-------------|----------|
| Cache-aside | App checks cache, then DB | App writes DB, invalidates cache | Eventual | Read-heavy, tolerates stale data |
| Write-through | App reads cache | App writes cache + DB together | Strong | Read-heavy, needs consistency |
| Write-behind | App reads cache | App writes cache, async DB write | Eventual | Write-heavy, can tolerate data loss |
| Read-through | Cache fetches from DB on miss | Depends on write strategy | Varies | Abstracted cache layer |

## Cache-Aside (Lazy Loading)

The most common pattern. The application manages the cache explicitly.

```python
import redis
import json

r = redis.Redis()

def get_user(user_id: str) -> dict:
    # 1. Check cache
    cached = r.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)

    # 2. Cache miss — query database
    user = db.query("SELECT * FROM users WHERE id = %s", user_id)

    # 3. Populate cache with TTL
    r.setex(f"user:{user_id}", 3600, json.dumps(user))

    return user

def update_user(user_id: str, data: dict):
    # 1. Update database
    db.execute("UPDATE users SET ... WHERE id = %s", user_id)

    # 2. Invalidate cache (delete, don't update)
    r.delete(f"user:{user_id}")
```

**Advantages:** Only requested data is cached; cache failures don't break reads.
**Disadvantages:** Cache miss penalty on first access; potential for stale data between update and invalidation.

## Write-Through

Every write goes to both cache and database synchronously.

```python
def update_user(user_id: str, data: dict):
    # 1. Write to database
    db.execute("UPDATE users SET ... WHERE id = %s", user_id)

    # 2. Write to cache
    r.setex(f"user:{user_id}", 3600, json.dumps(data))

def get_user(user_id: str) -> dict:
    cached = r.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)

    user = db.query("SELECT * FROM users WHERE id = %s", user_id)
    r.setex(f"user:{user_id}", 3600, json.dumps(user))
    return user
```

**Advantages:** Cache is always consistent with database.
**Disadvantages:** Write latency increases (two writes per operation); caches data that may never be read.

## Write-Behind (Write-Back)

Writes go to cache immediately; database is updated asynchronously.

```python
def update_user(user_id: str, data: dict):
    # 1. Write to cache immediately
    r.setex(f"user:{user_id}", 3600, json.dumps(data))

    # 2. Queue database write for async processing
    r.rpush("write_queue", json.dumps({
        "table": "users",
        "id": user_id,
        "data": data,
        "timestamp": time.time()
    }))

# Background worker processes the queue
def write_worker():
    while True:
        item = r.blpop("write_queue", timeout=5)
        if item:
            payload = json.loads(item[1])
            db.execute("UPDATE ... SET ... WHERE id = %s", payload["id"])
```

**Advantages:** Lowest write latency; can batch database writes.
**Disadvantages:** Data loss risk if Redis crashes before DB write; complex failure handling.

## Read-Through

The cache itself fetches from the database on miss — requires a cache proxy or framework support.

```python
class ReadThroughCache:
    def __init__(self, redis_client, db, default_ttl=3600):
        self.r = redis_client
        self.db = db
        self.ttl = default_ttl

    def get(self, key: str, loader):
        cached = self.r.get(key)
        if cached:
            return json.loads(cached)

        value = loader()
        if value is not None:
            self.r.setex(key, self.ttl, json.dumps(value))
        return value

# Usage
cache = ReadThroughCache(r, db)
user = cache.get(f"user:{user_id}", lambda: db.get_user(user_id))
```

## TTL Strategies

### Fixed TTL

```redis
SET user:1001 "data" EX 3600          # 1 hour
SETEX session:abc "data" 1800          # 30 minutes
```

### Sliding TTL (Refresh on Access)

```python
def get_with_sliding_ttl(key: str, ttl: int = 3600):
    value = r.get(key)
    if value:
        r.expire(key, ttl)            # Reset TTL on each access
    return value
```

### TTL Guidelines

| Data Type | Suggested TTL | Rationale |
|-----------|---------------|-----------|
| Session data | 30 min | Security; inactive sessions should expire |
| User profiles | 1–6 hours | Changes infrequently |
| API responses | 5–60 min | Depends on update frequency |
| Static config | 24 hours | Rarely changes |
| Rate limit counters | 1–60 min | Window-based |
| Search results | 5–15 min | Can become stale quickly |

### Jittered TTL (Prevent Thundering Herd)

```python
import random

base_ttl = 3600
jitter = random.randint(-300, 300)     # ±5 minutes
r.setex(key, base_ttl + jitter, value)
```

## Eviction Policies

Configure with `maxmemory-policy` when Redis reaches `maxmemory`:

| Policy | Scope | Strategy | Best For |
|--------|-------|----------|----------|
| `noeviction` | — | Error on write | Non-cache use (databases) |
| `allkeys-lru` | All keys | Least Recently Used | General caching (recommended) |
| `allkeys-lfu` | All keys | Least Frequently Used | Power-law access patterns |
| `allkeys-random` | All keys | Random eviction | Uniform access patterns |
| `volatile-lru` | Keys with TTL | LRU among expiring keys | Mixed cache + persistent data |
| `volatile-lfu` | Keys with TTL | LFU among expiring keys | TTL keys with frequency skew |
| `volatile-ttl` | Keys with TTL | Nearest expiration first | Time-sensitive data |
| `volatile-random` | Keys with TTL | Random among expiring keys | Simple volatile eviction |

```redis
CONFIG SET maxmemory 1gb
CONFIG SET maxmemory-policy allkeys-lfu

# Monitor eviction stats
INFO stats | grep evicted_keys
```

**Recommendation:** Use `allkeys-lfu` for most caching workloads — it keeps frequently accessed data and evicts rarely used entries.

## Cache Invalidation

### Delete on Write (Recommended)

```python
def update_product(product_id: str, data: dict):
    db.update_product(product_id, data)
    r.delete(f"product:{product_id}")
    r.delete(f"product_list:category:{data['category']}")
```

### Pattern-Based Invalidation

```redis
# Find and delete related keys
SCAN 0 MATCH "product:*:cache" COUNT 100
# Then DEL each matched key

# Or use keyspace notifications
CONFIG SET notify-keyspace-events Kx
SUBSCRIBE __keyevent@0__:expired
```

### Tag-Based Invalidation

```python
def cache_with_tags(key: str, value: str, tags: list[str], ttl: int):
    r.setex(key, ttl, value)
    for tag in tags:
        r.sadd(f"tag:{tag}", key)
        r.expire(f"tag:{tag}", ttl)

def invalidate_by_tag(tag: str):
    keys = r.smembers(f"tag:{tag}")
    if keys:
        r.delete(*keys)
    r.delete(f"tag:{tag}")

# Usage
cache_with_tags("product:5001", data, ["category:electronics", "brand:acme"], 3600)
invalidate_by_tag("category:electronics")  # Clears all electronics products
```

## Cache Stampede Prevention

A cache stampede occurs when many requests simultaneously discover a cache miss and all hit the database.

### Locking (Mutex)

```python
def get_with_lock(key: str, loader, ttl: int = 3600):
    value = r.get(key)
    if value:
        return json.loads(value)

    lock_key = f"lock:{key}"
    if r.set(lock_key, "1", nx=True, ex=10):  # Acquire lock
        try:
            value = loader()
            r.setex(key, ttl, json.dumps(value))
            return value
        finally:
            r.delete(lock_key)
    else:
        time.sleep(0.1)
        return get_with_lock(key, loader, ttl)  # Retry
```

### Probabilistic Early Expiration

```python
import math
import random

def get_with_early_recompute(key: str, loader, ttl: int = 3600, beta: float = 1.0):
    cached = r.get(key)
    remaining_ttl = r.ttl(key)

    if cached and remaining_ttl > 0:
        # Probabilistically recompute before expiry
        if remaining_ttl > beta * math.log(random.random()) * -1:
            return json.loads(cached)

    value = loader()
    r.setex(key, ttl, json.dumps(value))
    return value
```

## Distributed Locking

### Simple Lock (SET NX)

```python
def acquire_lock(lock_name: str, owner: str, ttl: int = 30) -> bool:
    return r.set(f"lock:{lock_name}", owner, nx=True, ex=ttl)

def release_lock(lock_name: str, owner: str) -> bool:
    # Lua script for atomic check-and-delete
    script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """
    return r.eval(script, 1, f"lock:{lock_name}", owner)

# Usage
if acquire_lock("process-order-5001", "worker-1", ttl=30):
    try:
        process_order("5001")
    finally:
        release_lock("process-order-5001", "worker-1")
```

### Lock with Retry

```python
import time
import uuid

def acquire_lock_with_retry(
    lock_name: str, timeout: float = 10.0, ttl: int = 30
) -> str | None:
    owner = str(uuid.uuid4())
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if r.set(f"lock:{lock_name}", owner, nx=True, ex=ttl):
            return owner
        time.sleep(0.05)

    return None
```

## Patterns & Best Practices

### Multi-Level Caching

```
Request → L1 (In-Process) → L2 (Redis) → Database
```

```python
from functools import lru_cache

@lru_cache(maxsize=1000)                        # L1: in-process
def get_config(key: str) -> str:
    cached = r.get(f"config:{key}")              # L2: Redis
    if cached:
        return cached.decode()
    value = db.get_config(key)                   # L3: database
    r.setex(f"config:{key}", 3600, value)
    return value
```

### Cache Warming

```python
def warm_cache():
    """Pre-populate cache with hot data on startup."""
    popular_products = db.get_popular_products(limit=1000)
    pipeline = r.pipeline()
    for product in popular_products:
        pipeline.setex(
            f"product:{product['id']}",
            3600,
            json.dumps(product)
        )
    pipeline.execute()
```

## Common Pitfalls

1. **Caching everything** — Only cache data that's expensive to compute or frequently accessed.
2. **Inconsistent serialization** — Always use the same format (JSON, msgpack) for encode/decode.
3. **No TTL on cache keys** — Keys without expiry accumulate forever.
4. **Delete vs. update on write** — Prefer delete (invalidate) over set (update) to avoid race conditions.
5. **Cache-warming without jitter** — Loading all keys at once can overwhelm Redis. Stagger with random delays.
6. **Ignoring eviction metrics** — Monitor `evicted_keys` in INFO stats. High eviction = memory pressure.

## Related

- `00-overview.md` — Eviction policies and maxmemory configuration
- `01-strings.md` — SET/GET with TTL options
- `08-transactions-scripting.md` — Lua scripts for atomic cache operations
