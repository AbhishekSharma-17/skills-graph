---
name: redis
description: "Redis in-memory data store — data types, caching patterns, pub/sub, streams, transactions, persistence, replication, clustering, search, and client libraries. MANDATORY TRIGGERS: redis, Redis, redis-server, redis-cli, redis-py, ioredis, HSET, ZADD, XADD, LPUSH, pub/sub, Redis Cluster, Redis Sentinel, RDB, AOF, RedisJSON, RedisTimeSeries, Redis Search, FT.CREATE, FT.SEARCH, eviction policy, cache-aside. Also trigger when user wants to implement caching, session storage, rate limiting, leaderboards, message queues, real-time analytics, pub/sub messaging, distributed locks, or any in-memory data store pattern. When in doubt about whether to use this skill for caching or data store tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["redis", "caching", "database", "in-memory", "pub-sub", "streams", "data-structures", "clustering", "replication", "search"]
---

# Redis — Skill Router

> The open-source, in-memory data store used as a database, cache, streaming engine, and message broker.

**Source:** [redis.io/docs](https://redis.io/docs/latest/) | **Version:** `8.6` | **GitHub:** 66K+ stars

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Installation, configuration, architecture, Docker setup, CLI basics |
| **Strings & Keys** | `references/01-strings.md` | GET/SET, counters, TTL, key expiration, bitmaps, bitfields |
| **Hashes & Lists** | `references/02-hashes-lists.md` | HSET/HGET, LPUSH/RPUSH, object storage, queues, stacks |
| **Sets & Sorted Sets** | `references/03-sets-sorted-sets.md` | SADD/SMEMBERS, ZADD/ZRANGE, leaderboards, ranking, intersections |
| **Streams** | `references/04-streams.md` | XADD/XREAD, consumer groups, event sourcing, message processing |
| **JSON, TimeSeries & Vectors** | `references/05-json-timeseries-vectors.md` | JSON.SET/GET, TS.ADD/RANGE, vector sets, HNSW similarity search |
| **Pub/Sub** | `references/06-pub-sub.md` | SUBSCRIBE/PUBLISH, pattern matching, sharded pub/sub, real-time messaging |
| **Caching Patterns** | `references/07-caching-patterns.md` | Cache-aside, write-through, write-behind, TTL, eviction policies, stampede prevention |
| **Transactions & Scripting** | `references/08-transactions-scripting.md` | MULTI/EXEC, WATCH, pipelining, Lua EVAL, Redis Functions |
| **Persistence** | `references/09-persistence.md` | RDB snapshots, AOF, hybrid persistence, backup, disaster recovery |
| **Replication & Sentinel** | `references/10-replication-sentinel.md` | Master-replica, REPLICAOF, Redis Sentinel, automatic failover, HA |
| **Cluster** | `references/11-cluster.md` | Hash slots, sharding, resharding, failover, adding/removing nodes |
| **Client Libraries** | `references/12-client-libraries.md` | Python redis-py, Node.js ioredis, async patterns, connection pooling |

## Installation

```bash
# Docker (recommended)
docker run -d --name redis -p 6379:6379 redis:8.6-alpine

# macOS
brew install redis && brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# Python client
pip install redis

# Node.js client
npm install ioredis
```

## Quick Reference

- [Redis Documentation](https://redis.io/docs/latest/)
- [Command Reference](https://redis.io/docs/latest/commands/)
- [Redis University](https://university.redis.io)
- [GitHub](https://github.com/redis/redis)
- [Redis Playground](https://try.redis.io)
