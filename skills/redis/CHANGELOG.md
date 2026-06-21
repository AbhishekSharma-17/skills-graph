# Changelog

## [1.0.0] — 2026-06-22

**Source version tracked:** Redis `8.6`

### Added

- `00-overview.md` — Architecture, installation (Docker/brew/apt), configuration, eviction policies, CLI basics, key management
- `01-strings.md` — Strings, GET/SET options (NX/XX/EX/PX), counters (INCR/DECR), MGET/MSET, bitmaps, bitfields, expiration
- `02-hashes-lists.md` — Hashes (HSET/HGET/HGETALL), Lists (LPUSH/RPUSH/LPOP/RPOP), blocking operations, queue patterns
- `03-sets-sorted-sets.md` — Sets (SADD/SMEMBERS/SINTER), Sorted Sets (ZADD/ZRANGE/ZRANK), leaderboards, priority queues
- `04-streams.md` — Streams (XADD/XREAD/XRANGE), consumer groups (XREADGROUP/XACK), XAUTOCLAIM, event sourcing
- `05-json-timeseries-vectors.md` — JSON (JSON.SET/GET), TimeSeries (TS.ADD/RANGE), Vector Sets (VADD/VSIM), HyperLogLog, Bloom filters, geospatial
- `06-pub-sub.md` — Pub/Sub (SUBSCRIBE/PUBLISH), pattern matching, sharded pub/sub, keyspace notifications
- `07-caching-patterns.md` — Cache-aside, write-through, write-behind, TTL strategies, eviction policies, stampede prevention, distributed locks
- `08-transactions-scripting.md` — MULTI/EXEC/DISCARD, WATCH (optimistic locking), pipelining, Lua scripting (EVAL/EVALSHA), Redis Functions
- `09-persistence.md` — RDB snapshots, AOF (Append Only File), hybrid persistence, backup strategies, disaster recovery
- `10-replication-sentinel.md` — Master-replica replication, Redis Sentinel, automatic failover, client integration
- `11-cluster.md` — Redis Cluster, hash slots, sharding, resharding, failover, Docker setup
- `12-client-libraries.md` — Python redis-py (sync/async), Node.js ioredis, connection pooling, pipeline APIs, stream consumers

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~5,100
