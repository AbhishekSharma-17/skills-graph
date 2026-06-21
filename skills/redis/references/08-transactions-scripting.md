# Redis — Transactions & Scripting

> Source: [redis.io/docs/interact](https://redis.io/docs/latest/develop/interact/) — Redis 8.6

## Table of Contents

- [Transactions Overview](#transactions-overview)
- [MULTI/EXEC](#multiexec)
- [WATCH (Optimistic Locking)](#watch-optimistic-locking)
- [Pipelining](#pipelining)
- [Lua Scripting](#lua-scripting)
- [Redis Functions](#redis-functions)
- [Patterns](#patterns)
- [Common Pitfalls](#common-pitfalls)

## Transactions Overview

Redis transactions execute a group of commands sequentially and atomically — no other client's commands can run between them. However, Redis transactions have no rollback: if a command fails during EXEC, the remaining commands still execute.

## MULTI/EXEC

```redis
# Start transaction
MULTI

# Queue commands (not executed yet — Redis replies "QUEUED")
SET user:1001:balance 500
DECRBY user:1001:balance 100
INCRBY user:1002:balance 100

# Execute all queued commands atomically
EXEC
# Returns results of each command:
# 1) OK
# 2) (integer) 400
# 3) (integer) 100

# Cancel transaction
MULTI
SET key1 "value1"
DISCARD                               # All queued commands discarded
```

### Error Handling

**Command syntax errors (before EXEC):**

```redis
MULTI
SET key1 "value1"
NONSENSE                              # Syntax error — transaction is flagged
EXEC
# Returns error — entire transaction rejected
```

**Runtime errors (during EXEC):**

```redis
SET key1 "hello"
MULTI
INCR key1                             # Will fail — "hello" is not a number
SET key2 "world"                      # Will succeed
EXEC
# 1) ERR value is not an integer
# 2) OK                               # key2 is set despite key1 error
```

**No rollback** — Redis intentionally does not support rollback because:
- Commands only fail due to programming errors (wrong type), not data errors
- No-rollback keeps Redis simple and fast

## WATCH (Optimistic Locking)

WATCH monitors keys for changes. If any watched key is modified before EXEC, the entire transaction is aborted.

```redis
# Optimistic locking pattern
WATCH user:1001:balance

# Read current value
GET user:1001:balance
# "500"

# Start transaction
MULTI
DECRBY user:1001:balance 100
EXEC
# Returns results if no one else modified user:1001:balance
# Returns nil if another client changed it (retry needed)
```

### Compare-and-Set Pattern

```python
def transfer(r, from_user: str, to_user: str, amount: int) -> bool:
    from_key = f"user:{from_user}:balance"
    to_key = f"user:{to_user}:balance"

    while True:
        try:
            r.watch(from_key)
            balance = int(r.get(from_key) or 0)

            if balance < amount:
                r.unwatch()
                return False

            pipe = r.pipeline(True)  # True = use MULTI/EXEC
            pipe.decrby(from_key, amount)
            pipe.incrby(to_key, amount)
            pipe.execute()
            return True
        except redis.WatchError:
            continue  # Key was modified, retry
```

## Pipelining

Pipelining sends multiple commands without waiting for responses, then reads all responses at once. This dramatically reduces round-trip latency.

```python
import redis

r = redis.Redis()

# Without pipeline: N round trips
for i in range(1000):
    r.set(f"key:{i}", f"value:{i}")    # 1000 round trips

# With pipeline: 1 round trip
pipe = r.pipeline(transaction=False)    # No MULTI/EXEC wrapping
for i in range(1000):
    pipe.set(f"key:{i}", f"value:{i}")
results = pipe.execute()                # Send all, get all results
```

### Pipeline vs Transaction

| Feature | Pipeline | Transaction (MULTI/EXEC) |
|---------|----------|--------------------------|
| Round trips | 1 | 1 |
| Atomicity | No | Yes (sequential execution) |
| Interleaving | Other clients may run between commands | No interleaving |
| Use case | Batch operations for speed | Atomic multi-key operations |

```python
# Pipeline without transaction (faster, no atomicity)
pipe = r.pipeline(transaction=False)
pipe.set("key1", "value1")
pipe.get("key2")
pipe.incr("counter")
results = pipe.execute()     # [True, b"value2", 42]

# Pipeline with transaction (atomic)
pipe = r.pipeline(transaction=True)  # Default
pipe.set("key1", "value1")
pipe.set("key2", "value2")
results = pipe.execute()     # Wrapped in MULTI/EXEC
```

### Batch Size

```python
# For very large batches, chunk the pipeline
def batch_set(r, data: dict, chunk_size: int = 500):
    items = list(data.items())
    for i in range(0, len(items), chunk_size):
        pipe = r.pipeline(transaction=False)
        for key, value in items[i:i + chunk_size]:
            pipe.set(key, value)
        pipe.execute()
```

## Lua Scripting

Lua scripts execute atomically on the server — no other command runs during script execution. Use for complex atomic operations that can't be done with MULTI/EXEC.

### EVAL

```redis
# EVAL script numkeys key [key ...] arg [arg ...]
EVAL "return redis.call('SET', KEYS[1], ARGV[1])" 1 mykey "myvalue"

# Conditional set with custom logic
EVAL "
    local current = redis.call('GET', KEYS[1])
    if current == false or tonumber(current) < tonumber(ARGV[1]) then
        redis.call('SET', KEYS[1], ARGV[1])
        return 1
    end
    return 0
" 1 highscore "1500"
```

### EVALSHA (Cached Scripts)

```redis
# Load script and get SHA1 hash
SCRIPT LOAD "return redis.call('GET', KEYS[1])"
# "e0e1f9fabfc9d4800c877a703b823ac0578ff831"

# Execute by hash (avoids re-sending script body)
EVALSHA e0e1f9fabfc9d4800c877a703b823ac0578ff831 1 mykey
```

### Common Lua Patterns

```redis
# Rate limiter (atomic increment with TTL initialization)
EVAL "
    local count = redis.call('INCR', KEYS[1])
    if count == 1 then
        redis.call('EXPIRE', KEYS[1], ARGV[1])
    end
    return count
" 1 ratelimit:user:1001 60

# Compare-and-swap
EVAL "
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        return redis.call('SET', KEYS[1], ARGV[2])
    else
        return nil
    end
" 1 mykey "old_value" "new_value"

# Conditional delete (safe lock release)
EVAL "
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        return redis.call('DEL', KEYS[1])
    else
        return 0
    end
" 1 lock:resource "owner-id"
```

### Script Guidelines

```redis
# Script flags (Redis 7.0+)
#!lua flags=no-writes,allow-stale

# Read-only scripts can run on replicas
EVAL_RO "return redis.call('GET', KEYS[1])" 1 mykey

# Script management
SCRIPT EXISTS <sha1> [sha1 ...]     # Check if script is cached
SCRIPT FLUSH                         # Clear script cache
SCRIPT KILL                          # Kill running script
```

### Lua API

```lua
-- Call Redis commands
redis.call("SET", KEYS[1], ARGV[1])          -- Raises error on failure
redis.pcall("SET", KEYS[1], ARGV[1])         -- Returns error as value

-- Logging
redis.log(redis.LOG_WARNING, "something happened")

-- JSON encoding (Redis 7.2+)
local obj = cjson.decode(ARGV[1])
local json_str = cjson.encode(obj)

-- Key types
redis.call("TYPE", KEYS[1])

-- Return values
return 1                    -- Integer
return "hello"              -- String
return {1, 2, 3}           -- Array
return redis.status_reply("OK")
return redis.error_reply("ERR something wrong")
```

## Redis Functions

Redis Functions (Redis 7.0+) are named, reusable server-side scripts that are persisted and replicated — unlike EVAL scripts which are ephemeral.

```redis
# Register a function library
FUNCTION LOAD "#!lua name=mylib
redis.register_function('myfunc', function(keys, args)
    return redis.call('GET', keys[1])
end)

redis.register_function('my_set_if_greater', function(keys, args)
    local current = tonumber(redis.call('GET', keys[1]) or 0)
    local new_val = tonumber(args[1])
    if new_val > current then
        redis.call('SET', keys[1], args[1])
        return 1
    end
    return 0
end)
"

# Call function
FCALL myfunc 1 mykey
FCALL my_set_if_greater 1 highscore 1500

# Read-only call (can run on replicas)
FCALL_RO myfunc 1 mykey

# List functions
FUNCTION LIST
FUNCTION DUMP                    # Serialize for backup
FUNCTION RESTORE <dump>          # Restore from backup
FUNCTION DELETE mylib
```

## Patterns

### Atomic Counter with Expiry

```python
def rate_limit(r, key: str, limit: int, window: int) -> bool:
    lua = """
    local count = redis.call('INCR', KEYS[1])
    if count == 1 then
        redis.call('EXPIRE', KEYS[1], ARGV[1])
    end
    return count
    """
    count = r.eval(lua, 1, key, window)
    return count <= limit
```

### Inventory Reservation

```python
reserve_script = r.register_script("""
    local stock = tonumber(redis.call('GET', KEYS[1]))
    local qty = tonumber(ARGV[1])
    if stock and stock >= qty then
        redis.call('DECRBY', KEYS[1], qty)
        return 1
    end
    return 0
""")

success = reserve_script(keys=["product:5001:stock"], args=[2])
```

## Common Pitfalls

1. **Long-running Lua scripts** — Block ALL Redis operations. Keep scripts under 5ms. Default timeout is 5 seconds (`lua-time-limit`).
2. **Non-deterministic scripts** — Avoid `TIME`, `RANDOMKEY`, `math.random()` in scripts — they break replication.
3. **WATCH without retry loop** — WATCH-based transactions can fail under contention. Always retry.
4. **Pipeline without error checking** — Check each result in `pipe.execute()`. Failures are returned as exceptions in the result list.
5. **Using KEYS in Lua** — `redis.call('KEYS', '*')` blocks Redis. Declare all keys in the KEYS array.
6. **Forgetting UNWATCH** — If you WATCH but don't EXEC/DISCARD, the watch persists until the connection closes.

## Related

- `07-caching-patterns.md` — Distributed locking with Lua
- `04-streams.md` — Event processing with atomic acknowledgment
- `12-client-libraries.md` — Pipeline and script APIs in Python/Node.js
