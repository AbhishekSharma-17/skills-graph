# Redis — Overview & Setup

> Source: [redis.io/docs](https://redis.io/docs/latest/) — Redis 8.6

## What Is Redis

Redis (Remote Dictionary Server) is an open-source, in-memory data structure store used as a database, cache, streaming engine, and message broker. It supports strings, hashes, lists, sets, sorted sets, streams, JSON, time series, vector sets, and probabilistic data structures.

Redis achieves sub-millisecond latency by keeping data in memory, using a single-threaded event loop for command processing, and supporting asynchronous I/O for persistence and replication.

## When to Use Redis

| Use Case | Why Redis |
|----------|-----------|
| **Caching** | Sub-ms reads, TTL-based expiration, LRU/LFU eviction |
| **Session storage** | Fast key-value access, automatic expiration |
| **Rate limiting** | Atomic INCR with TTL |
| **Leaderboards** | Sorted sets with O(log N) insert/rank |
| **Real-time analytics** | HyperLogLog for cardinality, streams for event ingestion |
| **Message queues** | Streams with consumer groups, pub/sub |
| **Distributed locks** | SET NX with TTL (Redlock algorithm) |
| **Search** | Full-text search, vector similarity, aggregation pipelines |
| **AI/ML** | Vector sets for embeddings, RAG pipelines |

## Architecture

```
┌─────────────────────────────────────────────┐
│                Redis Server                  │
│                                              │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │ Event Loop    │    │ Data Structures  │   │
│  │ (single-     │    │ (in-memory)      │   │
│  │  threaded)   │    │                  │   │
│  └──────┬───────┘    └────────┬─────────┘   │
│         │                      │             │
│  ┌──────▼──────────────────────▼─────────┐  │
│  │           Command Processor            │  │
│  └──────┬────────────────────┬───────────┘  │
│         │                    │               │
│  ┌──────▼───────┐    ┌──────▼──────────┐   │
│  │ Persistence  │    │ Replication      │   │
│  │ (RDB / AOF)  │    │ (async to        │   │
│  │              │    │  replicas)        │   │
│  └──────────────┘    └─────────────────┘   │
└─────────────────────────────────────────────┘
```

**Key design principles:**
- **Single-threaded command processing** — No locks, no race conditions, atomic operations by default
- **I/O multiplexing** — epoll/kqueue handles thousands of concurrent connections
- **Memory-first** — All data in RAM; disk used only for persistence
- **Optional durability** — RDB snapshots, AOF logging, or both

## Installation

### Docker (Recommended)

```bash
# Basic
docker run -d --name redis -p 6379:6379 redis:8.6-alpine

# With persistence
docker run -d --name redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:8.6-alpine redis-server --appendonly yes

# With password
docker run -d --name redis \
  -p 6379:6379 \
  redis:8.6-alpine redis-server --requirepass mypassword
```

### Docker Compose

```yaml
services:
  redis:
    image: redis:8.6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  redis-data:
```

### macOS

```bash
brew install redis
brew services start redis
```

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Verify Installation

```bash
redis-cli ping
# PONG

redis-cli INFO server | grep redis_version
# redis_version:8.6.0
```

## Configuration

### Key Configuration Options

```conf
# redis.conf

# Network
bind 127.0.0.1 -::1         # Listen addresses (use 0.0.0.0 for all)
port 6379                     # Default port
protected-mode yes            # Reject external connections without auth
tcp-keepalive 300             # TCP keepalive interval (seconds)

# Security
requirepass <password>        # Set password
# ACL rules (Redis 6+)
user default on >password ~* +@all  # Default user with password

# Memory
maxmemory 256mb               # Memory limit
maxmemory-policy allkeys-lru  # Eviction policy when limit reached

# Persistence
save 3600 1 300 100 60 10000  # RDB: save after 3600s if 1 key changed, etc.
appendonly yes                 # Enable AOF
appendfsync everysec           # AOF sync policy

# Logging
loglevel notice               # verbose, debug, notice, warning
logfile /var/log/redis/redis.log

# Connections
maxclients 10000              # Max concurrent connections
timeout 0                     # Client idle timeout (0 = disabled)
```

### Eviction Policies

| Policy | Description |
|--------|-------------|
| `noeviction` | Return error when memory limit reached (default) |
| `allkeys-lru` | Evict least recently used key from all keys |
| `allkeys-lfu` | Evict least frequently used key from all keys |
| `allkeys-random` | Evict random key from all keys |
| `volatile-lru` | Evict LRU key from keys with TTL set |
| `volatile-lfu` | Evict LFU key from keys with TTL set |
| `volatile-random` | Evict random key from keys with TTL set |
| `volatile-ttl` | Evict key with nearest TTL from keys with TTL set |

### Runtime Configuration

```bash
# View config
redis-cli CONFIG GET maxmemory
redis-cli CONFIG GET maxmemory-policy

# Set at runtime (no restart needed)
redis-cli CONFIG SET maxmemory 512mb
redis-cli CONFIG SET maxmemory-policy allkeys-lfu

# Persist runtime changes to redis.conf
redis-cli CONFIG REWRITE
```

## Redis CLI Basics

```bash
# Connect
redis-cli                           # localhost:6379
redis-cli -h host -p 6379 -a pass  # Remote with auth

# Basic operations
SET greeting "hello"
GET greeting                        # "hello"

# Key operations
KEYS *                              # List all keys (avoid in production)
SCAN 0 COUNT 100                    # Safe cursor-based iteration
EXISTS mykey                        # 1 (exists) or 0
TYPE mykey                          # string, list, set, zset, hash, stream
DEL mykey                           # Delete key
UNLINK mykey                        # Delete asynchronously (non-blocking)
RENAME oldkey newkey

# TTL / Expiration
EXPIRE mykey 60                     # Expire in 60 seconds
PEXPIRE mykey 60000                 # Expire in 60000 milliseconds
TTL mykey                           # Remaining seconds (-1 = no expiry, -2 = doesn't exist)
PERSIST mykey                       # Remove expiration

# Server info
INFO                                # Full server info
INFO memory                         # Memory usage
INFO replication                    # Replication status
INFO clients                        # Connected clients
DBSIZE                              # Number of keys in current DB
MONITOR                             # Watch all commands in real-time (debug only)
SLOWLOG GET 10                      # Last 10 slow queries
```

## Databases

Redis supports multiple logical databases (default: 16, numbered 0–15):

```bash
SELECT 1            # Switch to DB 1
DBSIZE              # Keys in current DB
FLUSHDB             # Clear current DB
FLUSHALL            # Clear ALL databases (dangerous)
MOVE mykey 2        # Move key to DB 2
SWAPDB 0 1          # Swap DB 0 and DB 1 atomically
```

In production, prefer key namespacing over multiple databases:

```bash
SET user:1001:name "Alice"
SET user:1001:email "alice@example.com"
SET order:5001:status "shipped"
```

## Common Pitfalls

1. **Using `KEYS *` in production** — Blocks the server scanning all keys. Use `SCAN` instead.
2. **No `maxmemory` set** — Redis grows unbounded and can OOM-kill the process. Always set a memory limit.
3. **`noeviction` policy with full memory** — Write commands fail. Use `allkeys-lru` or `allkeys-lfu` for caches.
4. **Storing large values** — Values >100KB degrade performance. Break into smaller chunks or use streams.
5. **No authentication in production** — Always set `requirepass` and use ACLs.
6. **Forgetting persistence** — Default config may not persist data. Enable AOF or RDB explicitly.

## Related

- `01-strings.md` — String data type and key operations
- `07-caching-patterns.md` — Cache strategies and eviction
- `09-persistence.md` — RDB and AOF configuration
- `12-client-libraries.md` — Language-specific clients
