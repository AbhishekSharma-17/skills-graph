# Redis — Hashes & Lists

> Source: [redis.io/docs/data-types](https://redis.io/docs/latest/develop/data-types/) — Redis 8.6

## Table of Contents

- [Hashes Overview](#hashes-overview)
- [Hash Commands](#hash-commands)
- [Hash Patterns](#hash-patterns)
- [Lists Overview](#lists-overview)
- [List Commands](#list-commands)
- [Blocking Operations](#blocking-operations)
- [List Patterns](#list-patterns)
- [Common Pitfalls](#common-pitfalls)

## Hashes Overview

Hashes are collections of field-value pairs — like Python dicts or JavaScript objects. They are the natural way to store structured objects in Redis.

**Memory efficiency:** Hashes with few fields use a compact ziplist encoding, consuming less memory than equivalent separate string keys.

## Hash Commands

### Create & Update

```redis
# Set single field
HSET user:1001 name "Alice"

# Set multiple fields at once
HSET user:1001 name "Alice" email "alice@example.com" age "30" role "admin"

# Set only if field does NOT exist
HSETNX user:1001 created_at "2026-06-22"
```

### Read

```redis
# Get single field
HGET user:1001 name                   # "Alice"

# Get multiple fields
HMGET user:1001 name email role       # ["Alice", "alice@example.com", "admin"]

# Get all fields and values
HGETALL user:1001
# 1) "name"
# 2) "Alice"
# 3) "email"
# 4) "alice@example.com"
# ...

# Get all field names
HKEYS user:1001                       # ["name", "email", "age", "role"]

# Get all values
HVALS user:1001                       # ["Alice", "alice@example.com", "30", "admin"]

# Count fields
HLEN user:1001                        # 4

# Check field existence
HEXISTS user:1001 email               # 1 (exists)
HEXISTS user:1001 phone               # 0 (doesn't exist)

# Get string length of field value
HSTRLEN user:1001 name                # 5
```

### Delete

```redis
# Delete specific fields
HDEL user:1001 age role               # 2 (fields deleted)

# Delete entire hash
DEL user:1001
UNLINK user:1001                      # Non-blocking delete
```

### Numeric Operations

```redis
HSET product:5001 price 2999 stock 150

HINCRBY product:5001 stock -1         # 149 (atomic decrement)
HINCRBY product:5001 stock 10         # 159

HINCRBYFLOAT product:5001 price 0.50  # 2999.50
```

### Scan Hash Fields

```redis
# Iterate fields without blocking (safe for production)
HSCAN user:1001 0 COUNT 10
HSCAN user:1001 0 MATCH "addr*" COUNT 10
```

## Hash Patterns

### Object Storage

```redis
# Store user profile
HSET user:1001 \
  name "Alice Johnson" \
  email "alice@example.com" \
  plan "premium" \
  login_count "0" \
  created_at "2026-06-22T10:00:00Z"

# Increment login counter
HINCRBY user:1001 login_count 1

# Update plan
HSET user:1001 plan "enterprise"
```

### Shopping Cart

```redis
# Add items (field = product_id, value = quantity)
HSET cart:user:1001 product:100 2 product:200 1 product:300 3

# Update quantity
HINCRBY cart:user:1001 product:100 1    # Now 3

# Remove item
HDEL cart:user:1001 product:200

# Get full cart
HGETALL cart:user:1001

# Cart item count
HLEN cart:user:1001
```

### Configuration Store

```redis
HSET config:app \
  max_retries "3" \
  timeout_ms "5000" \
  feature_dark_mode "true" \
  api_version "v2"

HGET config:app timeout_ms              # "5000"
```

## Lists Overview

Lists are ordered collections of strings, implemented as linked lists. They support O(1) push/pop at both ends, making them ideal for queues, stacks, and recent-items lists.

## List Commands

### Push & Pop

```redis
# Push to head (left)
LPUSH tasks "task-3" "task-2" "task-1"   # [task-1, task-2, task-3]

# Push to tail (right)
RPUSH tasks "task-4" "task-5"            # [task-1, task-2, task-3, task-4, task-5]

# Push only if list exists
LPUSHX tasks "task-0"                    # Push only if "tasks" exists
RPUSHX tasks "task-6"

# Pop from head
LPOP tasks                               # "task-1"
LPOP tasks 2                             # ["task-2", "task-3"] (pop multiple)

# Pop from tail
RPOP tasks                               # "task-5"

# Pop from one list, push to another (atomic)
RPOPLPUSH source destination             # Deprecated, use LMOVE
LMOVE source destination LEFT RIGHT      # Pop from source LEFT, push to destination RIGHT
```

### Read

```redis
# Get elements by range (0-based, inclusive)
LRANGE tasks 0 -1                        # All elements
LRANGE tasks 0 4                         # First 5 elements
LRANGE tasks -3 -1                       # Last 3 elements

# Get by index
LINDEX tasks 0                           # First element
LINDEX tasks -1                          # Last element

# List length
LLEN tasks                               # Number of elements
```

### Modify

```redis
# Set element at index
LSET tasks 0 "updated-task"

# Insert before/after element
LINSERT tasks BEFORE "task-3" "task-2.5"
LINSERT tasks AFTER "task-3" "task-3.5"

# Remove elements by value
LREM tasks 0 "task-3"                   # Remove ALL occurrences
LREM tasks 1 "task-3"                   # Remove first occurrence
LREM tasks -2 "task-3"                  # Remove last 2 occurrences

# Trim to range (discard rest)
LTRIM tasks 0 99                         # Keep only first 100 elements

# Get and remove from position (Redis 6.2+)
LPOS tasks "task-3"                      # Find position of element
LPOS tasks "task-3" COUNT 0              # Find ALL positions
```

## Blocking Operations

Blocking list commands wait for elements instead of returning empty:

```redis
# Block until element available (timeout in seconds, 0 = forever)
BLPOP queue:jobs 30                      # Wait up to 30s for element
BRPOP queue:jobs 30

# Block move between lists
BLMOVE source destination LEFT RIGHT 30

# Block pop from multiple lists (first with data wins)
BLPOP queue:high queue:medium queue:low 0
```

Blocking operations are the foundation of Redis-based job queues.

## List Patterns

### Job Queue (FIFO)

```redis
# Producer: add jobs to the right
RPUSH queue:emails '{"to":"user@example.com","subject":"Welcome"}'
RPUSH queue:emails '{"to":"admin@example.com","subject":"Report"}'

# Consumer: take jobs from the left (blocking)
BLPOP queue:emails 0
# 1) "queue:emails"
# 2) "{\"to\":\"user@example.com\",\"subject\":\"Welcome\"}"
```

### Reliable Queue (with processing list)

```redis
# Atomically move from queue to processing list
LMOVE queue:jobs queue:processing LEFT RIGHT

# On success: remove from processing
LREM queue:processing 1 "<job-data>"

# On failure: move back to queue
LMOVE queue:processing queue:jobs LEFT LEFT
```

### Stack (LIFO)

```redis
# Push and pop from the same end
LPUSH stack:undo "action-1"
LPUSH stack:undo "action-2"
LPUSH stack:undo "action-3"

LPOP stack:undo              # "action-3" (last in, first out)
```

### Recent Items / Activity Feed

```redis
# Add new activity
LPUSH feed:user:1001 '{"action":"login","ts":"2026-06-22T10:00:00Z"}'

# Keep only last 100 entries
LTRIM feed:user:1001 0 99

# Get recent 10 entries
LRANGE feed:user:1001 0 9
```

### Capped List (Fixed Size)

```redis
# Add and trim in a pipeline
LPUSH notifications:user:1001 "New message from Bob"
LTRIM notifications:user:1001 0 49    # Keep max 50 notifications
```

## Common Pitfalls

1. **Using LINDEX on large lists** — O(N) for middle elements. Use sorted sets if you need random access.
2. **HGETALL on huge hashes** — Returns all fields at once, blocking Redis. Use HSCAN for large hashes.
3. **Forgetting LTRIM after LPUSH** — Lists grow unbounded without trimming.
4. **Hash field values are always strings** — `HSET user age 30` stores `"30"`, not integer 30.
5. **LRANGE 0 -1 on massive lists** — Returns everything. Paginate with proper ranges.

## Related

- `01-strings.md` — Simple key-value storage
- `03-sets-sorted-sets.md` — Unique collections and ranking
- `04-streams.md` — Persistent message queues (better than lists for queue patterns)
