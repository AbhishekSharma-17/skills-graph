# Redis — Strings & Keys

> Source: [redis.io/docs/data-types/strings](https://redis.io/docs/latest/develop/data-types/strings/) — Redis 8.6

## Table of Contents

- [Overview](#overview)
- [Basic Commands](#basic-commands)
- [SET Options](#set-options)
- [Counters](#counters)
- [Bulk Operations](#bulk-operations)
- [String Manipulation](#string-manipulation)
- [Bitmaps](#bitmaps)
- [Bitfields](#bitfields)
- [Key Expiration](#key-expiration)
- [Patterns](#patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Strings are the simplest Redis data type — a sequence of bytes. Despite the name, they can store text, serialized JSON, binary data, or integers (up to 512MB per value). Most Redis use cases start with strings.

## Basic Commands

```redis
# SET and GET
SET user:1001 "Alice"
GET user:1001                    # "Alice"

# SET with TTL
SET session:abc123 "data" EX 3600   # Expires in 3600 seconds
SET session:abc123 "data" PX 60000  # Expires in 60000 milliseconds

# SET conditionally
SET lock:resource "owner1" NX       # Only set if key does NOT exist
SET config:version "2.0" XX         # Only set if key DOES exist

# GET and SET atomically
GETSET counter "0"                  # Returns old value, sets new
GETDEL tempkey                      # Returns value and deletes key
GETEX mykey EX 100                  # Returns value and sets TTL
```

## SET Options

The `SET` command supports combining multiple flags:

```redis
SET key value [NX | XX] [GET] [EX seconds | PX ms | EXAT ts | PXAT ms-ts | KEEPTTL]
```

| Flag | Meaning |
|------|---------|
| `NX` | Set only if key does not exist (distributed lock pattern) |
| `XX` | Set only if key already exists (update only) |
| `GET` | Return the old value before setting |
| `EX seconds` | Set expiry in seconds |
| `PX milliseconds` | Set expiry in milliseconds |
| `EXAT timestamp` | Set expiry at Unix timestamp (seconds) |
| `PXAT ms-timestamp` | Set expiry at Unix timestamp (milliseconds) |
| `KEEPTTL` | Retain existing TTL when overwriting |

```redis
# Distributed lock — set if not exists with 30s expiry
SET lock:order:5001 "worker-1" NX EX 30

# Update and get previous value
SET user:1001:name "Bob" GET
# Returns "Alice" (previous value)
```

## Counters

Strings storing numeric values support atomic increment/decrement:

```redis
SET pageviews:home 0

INCR pageviews:home              # 1 (increment by 1)
INCR pageviews:home              # 2
INCRBY pageviews:home 10         # 12 (increment by N)
DECR pageviews:home              # 11
DECRBY pageviews:home 5          # 6

INCRBYFLOAT price:item1 2.50     # Floating point increment
INCRBYFLOAT price:item1 -1.25   # Decrement with negative value
```

All counter operations are **atomic** — safe for concurrent access without locks.

### Rate Limiter Pattern

```redis
# Simple rate limiter: 100 requests per minute
SET ratelimit:user:1001 0 EX 60 NX    # Create counter with 60s TTL
INCR ratelimit:user:1001               # Increment
# If value > 100, reject the request
```

## Bulk Operations

```redis
# Set multiple keys
MSET user:1:name "Alice" user:1:email "alice@example.com" user:2:name "Bob"

# Get multiple keys (returns array)
MGET user:1:name user:1:email user:2:name
# 1) "Alice"
# 2) "alice@example.com"
# 3) "Bob"

# Set multiple only if NONE exist (atomic)
MSETNX key1 "v1" key2 "v2"     # Returns 1 if ALL set, 0 if ANY existed

# Set multiple with expiry (Redis 8.4+)
MSETEX 3600 session:a "data-a" session:b "data-b"
```

`MGET` and `MSET` reduce round trips — use them when operating on multiple keys.

## String Manipulation

```redis
SET greeting "Hello"

APPEND greeting " World"         # "Hello World" (returns new length: 11)
STRLEN greeting                  # 11

# Substring operations
GETRANGE greeting 0 4            # "Hello"
GETRANGE greeting 6 -1           # "World"
SETRANGE greeting 6 "Redis"     # "Hello Redis"

# Length
STRLEN greeting                  # 11
```

## Bitmaps

Bitmaps are not a separate data type — they are string operations that treat values as bit arrays:

```redis
# Track daily active users (user IDs as bit offsets)
SETBIT active:2026-06-22 1001 1    # User 1001 was active
SETBIT active:2026-06-22 1002 1    # User 1002 was active
SETBIT active:2026-06-22 1003 1    # User 1003 was active

GETBIT active:2026-06-22 1001      # 1 (active)
GETBIT active:2026-06-22 9999      # 0 (not active)

BITCOUNT active:2026-06-22         # 3 (total active users)

# Bitwise AND — users active on BOTH days
BITOP AND active:both active:2026-06-21 active:2026-06-22
BITCOUNT active:both

# Find first set/unset bit
BITPOS active:2026-06-22 1         # First active user's offset
BITPOS active:2026-06-22 0         # First inactive user's offset
```

Bitmaps are extremely memory-efficient: tracking 100M users costs only ~12MB.

## Bitfields

Efficiently encode multiple counters in a single string:

```redis
# Store multiple counters: u8 = unsigned 8-bit, i16 = signed 16-bit
BITFIELD game:player:1001 SET u8 #0 100    # Health = 100
BITFIELD game:player:1001 SET u8 #1 50     # Mana = 50
BITFIELD game:player:1001 SET u16 #2 1500  # Score = 1500

# Read multiple fields
BITFIELD game:player:1001 GET u8 #0 GET u8 #1 GET u16 #2
# 1) 100  2) 50  3) 1500

# Increment with overflow control
BITFIELD game:player:1001 INCRBY u8 #0 -10  # Health - 10
BITFIELD game:player:1001 OVERFLOW SAT INCRBY u8 #1 200  # Mana saturates at 255
```

## Key Expiration

```redis
# Set expiry on existing key
EXPIRE mykey 300              # 300 seconds
PEXPIRE mykey 300000          # 300000 milliseconds
EXPIREAT mykey 1750000000     # Unix timestamp (seconds)
PEXPIREAT mykey 1750000000000 # Unix timestamp (ms)

# Check remaining time
TTL mykey                     # Seconds remaining (-1 = no expiry, -2 = doesn't exist)
PTTL mykey                    # Milliseconds remaining

# Remove expiry
PERSIST mykey

# Check if expiry is set
TTL mykey                     # -1 means no expiry
```

**Expiration behavior:**
- Keys are lazily expired on access AND actively expired by periodic background scan
- Redis samples 20 random keys with TTL every 100ms, deleting expired ones
- If >25% are expired, repeat immediately — ensures memory reclamation

## Patterns

### Session Storage

```redis
# Create session with 30-minute expiry
SET session:abc123 '{"user_id":1001,"role":"admin"}' EX 1800

# Extend session on activity
GETEX session:abc123 EX 1800

# Delete session (logout)
DEL session:abc123
```

### Feature Flags

```redis
SET feature:dark-mode "enabled"
SET feature:beta-ui "disabled"

GET feature:dark-mode    # "enabled"
```

### Idempotency Keys

```redis
# Prevent duplicate payment processing
SET idempotency:pay:req-123 "processing" NX EX 86400
# Returns OK if first attempt, nil if duplicate
```

## Common Pitfalls

1. **Storing large JSON as strings** — Use Redis JSON (JSON.SET) for structured data that needs partial updates.
2. **Not setting TTL on cache keys** — Keys accumulate without expiry, exhausting memory.
3. **Using INCR on non-numeric strings** — Returns `ERR value is not an integer`.
4. **Exceeding 512MB string limit** — Use streams or lists for large data.
5. **MSETNX partial success** — It's all-or-nothing; if ANY key exists, NONE are set.

## Related

- `02-hashes-lists.md` — Complex data structures
- `07-caching-patterns.md` — TTL strategies and eviction
- `00-overview.md` — Key management and CLI basics
