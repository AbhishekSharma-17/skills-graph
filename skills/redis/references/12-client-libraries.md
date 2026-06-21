# Redis — Client Libraries

> Source: [redis.io/docs/clients](https://redis.io/docs/latest/develop/clients/) — Redis 8.6

## Table of Contents

- [Overview](#overview)
- [Python (redis-py)](#python-redis-py)
- [Async Python](#async-python)
- [Node.js (ioredis)](#nodejs-ioredis)
- [Connection Pooling](#connection-pooling)
- [Pipelining in Clients](#pipelining-in-clients)
- [Pub/Sub in Clients](#pubsub-in-clients)
- [Stream Consumers](#stream-consumers)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)

## Overview

| Client | Language | Cluster | Sentinel | Async | Streams |
|--------|----------|---------|----------|-------|---------|
| **redis-py** | Python | Yes | Yes | Yes | Yes |
| **ioredis** | Node.js | Yes | Yes | Native | Yes |
| **Jedis** | Java | Yes | Yes | No | Yes |
| **Lettuce** | Java | Yes | Yes | Yes | Yes |
| **go-redis** | Go | Yes | Yes | N/A | Yes |
| **StackExchange.Redis** | C# | Yes | Yes | Yes | Yes |

## Python (redis-py)

### Installation

```bash
pip install redis             # Latest (8.0+)
pip install "redis[hiredis]"  # With C parser for better performance
```

### Basic Usage

```python
import redis

# Connect
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Basic operations
r.set("greeting", "hello")
r.get("greeting")                     # "hello"

# With password
r = redis.Redis(
    host="localhost",
    port=6379,
    password="secret",
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
)

# From URL
r = redis.from_url("redis://:password@localhost:6379/0")
r = redis.from_url("rediss://host:6380/0")  # TLS
```

### Data Types

```python
# Strings
r.set("key", "value", ex=3600)       # With 1-hour TTL
r.setnx("key", "value")              # Set if not exists
r.incr("counter")                     # Atomic increment
r.mset({"k1": "v1", "k2": "v2"})

# Hashes
r.hset("user:1001", mapping={"name": "Alice", "email": "alice@example.com"})
r.hget("user:1001", "name")           # "Alice"
r.hgetall("user:1001")                # {"name": "Alice", "email": "alice@example.com"}
r.hincrby("user:1001", "login_count", 1)

# Lists
r.lpush("queue", "job1", "job2")
r.rpop("queue")                       # "job1"
r.lrange("queue", 0, -1)              # All elements
r.blpop("queue", timeout=5)           # Blocking pop

# Sets
r.sadd("tags", "redis", "python", "cache")
r.smembers("tags")                    # {"redis", "python", "cache"}
r.sinter("tags1", "tags2")            # Intersection

# Sorted Sets
r.zadd("leaderboard", {"alice": 100, "bob": 85})
r.zrange("leaderboard", 0, -1, withscores=True)
r.zincrby("leaderboard", 10, "bob")   # bob: 95
r.zrevrange("leaderboard", 0, 9)      # Top 10

# JSON
r.json().set("doc:1", "$", {"name": "Alice", "scores": [90, 85, 92]})
r.json().get("doc:1", "$.name")       # ["Alice"]
r.json().numincrby("doc:1", "$.scores[0]", 5)
```

### Pipeline

```python
# Batch commands (transaction=False for raw pipelining)
pipe = r.pipeline(transaction=False)
for i in range(1000):
    pipe.set(f"key:{i}", f"value:{i}")
results = pipe.execute()

# Transactional pipeline (wrapped in MULTI/EXEC)
pipe = r.pipeline(transaction=True)
pipe.set("key1", "v1")
pipe.set("key2", "v2")
pipe.incr("counter")
results = pipe.execute()               # [True, True, 1]
```

### Lua Scripts

```python
# Register script
multiply = r.register_script("""
    local value = redis.call('GET', KEYS[1])
    if value then
        local result = tonumber(value) * tonumber(ARGV[1])
        redis.call('SET', KEYS[1], result)
        return result
    end
    return nil
""")

r.set("num", 10)
result = multiply(keys=["num"], args=[5])   # 50
```

## Async Python

```python
import redis.asyncio as aioredis

# Async connection
r = aioredis.Redis(host="localhost", port=6379, decode_responses=True)

async def main():
    await r.set("key", "value")
    value = await r.get("key")
    print(value)

    # Async pipeline
    async with r.pipeline(transaction=False) as pipe:
        for i in range(100):
            pipe.set(f"key:{i}", f"val:{i}")
        await pipe.execute()

    await r.aclose()

# FastAPI integration
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
        max_connections=50,
    )
    yield
    await app.state.redis.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    r = app.state.redis
    cached = await r.get(f"item:{item_id}")
    if cached:
        return {"item": cached, "source": "cache"}
    # Fetch from DB, cache it
    item = await fetch_from_db(item_id)
    await r.setex(f"item:{item_id}", 3600, item)
    return {"item": item, "source": "db"}
```

### Async Connection Pool

```python
pool = aioredis.ConnectionPool(
    host="localhost",
    port=6379,
    max_connections=50,
    decode_responses=True,
    socket_timeout=5,
    retry_on_timeout=True,
)

r = aioredis.Redis(connection_pool=pool)
```

## Node.js (ioredis)

### Installation

```bash
npm install ioredis
```

### Basic Usage

```javascript
const Redis = require("ioredis");

// Connect
const redis = new Redis({
  host: "localhost",
  port: 6379,
  password: "secret",
  db: 0,
  maxRetriesPerRequest: 3,
  retryStrategy(times) {
    return Math.min(times * 50, 2000);
  },
});

// Basic operations
await redis.set("key", "value", "EX", 3600);
const value = await redis.get("key");

// Hash
await redis.hset("user:1", "name", "Alice", "email", "alice@example.com");
const user = await redis.hgetall("user:1");

// Sorted set
await redis.zadd("leaderboard", 100, "alice", 85, "bob");
const top10 = await redis.zrevrange("leaderboard", 0, 9, "WITHSCORES");
```

### Pipeline

```javascript
const pipeline = redis.pipeline();
for (let i = 0; i < 1000; i++) {
  pipeline.set(`key:${i}`, `value:${i}`);
}
const results = await pipeline.exec();

// Transaction (MULTI/EXEC)
const tx = redis.multi();
tx.set("k1", "v1");
tx.set("k2", "v2");
tx.incr("counter");
const txResults = await tx.exec();
```

### Cluster

```javascript
const cluster = new Redis.Cluster([
  { host: "node1", port: 7000 },
  { host: "node2", port: 7001 },
  { host: "node3", port: 7002 },
], {
  scaleReads: "slave",           // Read from replicas
  redisOptions: { password: "secret" },
});
```

### Sentinel

```javascript
const redis = new Redis({
  sentinels: [
    { host: "sentinel1", port: 26379 },
    { host: "sentinel2", port: 26379 },
    { host: "sentinel3", port: 26379 },
  ],
  name: "mymaster",
  password: "redis-password",
  sentinelPassword: "sentinel-password",
});
```

## Connection Pooling

### Python

```python
# Sync pool
pool = redis.ConnectionPool(
    host="localhost",
    port=6379,
    max_connections=50,          # Pool size
    socket_timeout=5,
    socket_connect_timeout=5,
    health_check_interval=30,    # Periodic health checks
)
r = redis.Redis(connection_pool=pool)

# Check pool stats
pool_info = r.connection_pool
print(f"Active: {len(pool_info._in_use_connections)}")
print(f"Available: {len(pool_info._available_connections)}")
```

### Node.js (ioredis)

```javascript
// ioredis manages connection pooling internally
const redis = new Redis({
  host: "localhost",
  port: 6379,
  lazyConnect: true,             // Don't connect until first command
  keepAlive: 30000,              // TCP keepalive interval (ms)
  connectTimeout: 10000,
  maxRetriesPerRequest: 3,
});
```

## Pipelining in Clients

### Python with Context Manager

```python
with r.pipeline(transaction=False) as pipe:
    pipe.get("key1")
    pipe.get("key2")
    pipe.hgetall("user:1001")
    result1, result2, user = pipe.execute()
```

### Error Handling in Pipelines

```python
results = pipe.execute(raise_on_error=False)
for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"Command {i} failed: {result}")
    else:
        print(f"Command {i}: {result}")
```

## Pub/Sub in Clients

### Python

```python
# Subscriber (runs in thread or async)
pubsub = r.pubsub()
pubsub.subscribe("channel1", "channel2")
pubsub.psubscribe("events:*")

# Message loop
for message in pubsub.listen():
    if message["type"] == "message":
        print(f"Channel: {message['channel']}, Data: {message['data']}")

# Async subscriber
async def subscriber():
    pubsub = r.pubsub()
    await pubsub.subscribe("events")
    async for message in pubsub.listen():
        if message["type"] == "message":
            await handle_event(message["data"])

# Publisher (separate connection)
r.publish("channel1", "Hello!")
```

### Node.js

```javascript
const sub = redis.duplicate();
await sub.subscribe("events", (err, count) => {});

sub.on("message", (channel, message) => {
  console.log(`${channel}: ${message}`);
});

// Publish
await redis.publish("events", JSON.stringify({ type: "order", id: 123 }));
```

## Stream Consumers

### Python

```python
# Create consumer group
r.xgroup_create("events", "workers", id="0", mkstream=True)

# Consumer loop
while True:
    messages = r.xreadgroup(
        groupname="workers",
        consumername="worker-1",
        streams={"events": ">"},
        count=10,
        block=5000,
    )
    if messages:
        for stream, entries in messages:
            for msg_id, fields in entries:
                process(fields)
                r.xack("events", "workers", msg_id)
```

## Best Practices

1. **Always use connection pools** — Creating new connections per request is expensive.
2. **Set socket timeouts** — Prevent hanging connections with `socket_timeout` and `socket_connect_timeout`.
3. **Use `decode_responses=True`** — Avoid manual `.decode()` on every value (Python).
4. **Pipeline batch operations** — Reduce round trips for multiple commands.
5. **Close connections on shutdown** — Use `r.close()` or `await r.aclose()` to release resources.
6. **Use hiredis parser** — `pip install redis[hiredis]` for 10x faster response parsing.
7. **Retry on timeout** — Set `retry_on_timeout=True` for transient failures.
8. **Health checks** — Set `health_check_interval` to detect dead connections.
9. **Connection naming** — Use `CLIENT SETNAME` for easier debugging with `CLIENT LIST`.

## Common Pitfalls

1. **Sharing connections across threads** — redis-py handles this with its pool, but don't share async connections across tasks without a pool.
2. **Not closing connections** — Leaked connections exhaust the pool and Redis `maxclients`.
3. **Blocking commands on shared connections** — `BLPOP`, `SUBSCRIBE` block the connection. Use dedicated connections.
4. **Forgetting `decode_responses`** — Returns `b"hello"` instead of `"hello"` by default in Python.
5. **Large pipeline batches** — Sending 1M commands in one pipeline uses excessive memory. Chunk into batches of 500–1000.
6. **Not handling ConnectionError** — Network failures happen. Wrap operations with try/except for retries.

## Related

- `08-transactions-scripting.md` — Pipeline and transaction patterns
- `06-pub-sub.md` — Pub/sub messaging details
- `04-streams.md` — Stream consumer group patterns
