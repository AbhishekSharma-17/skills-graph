# Audit Report — redis

**Date:** 2026-06-22
**Skill version:** 1.0.0
**Source:** Redis `8.6`

## Quality Scores

| Dimension | Score (1–5) | Notes |
|-----------|:-----------:|-------|
| **Architecture** | 5 | Clean router → leaf structure. 13 reference files covering the full Redis surface from data types to cluster operations. No files exceed 500 lines. Files >300 lines include table of contents. |
| **Content Quality** | 5 | Practical code examples throughout — Redis CLI commands, Python redis-py (sync/async), Node.js ioredis, Lua scripting, Docker Compose configurations. Includes comparison tables, decision trees, and common pitfalls sections. |
| **Completeness** | 5 | Covers all major Redis capabilities: 7 core data types (strings, hashes, lists, sets, sorted sets, streams, JSON), advanced types (TimeSeries, vectors, probabilistic), pub/sub, caching patterns, transactions, Lua scripting, Redis Functions, persistence (RDB/AOF), replication, Sentinel HA, Cluster sharding, and client libraries. |
| **Maintainability** | 5 | VERSION.json tracks per-file source pages and update dates. check-updates.py validates against Docker Hub registry. 90-day staleness threshold. Clear update path for each reference file. |
| **Trigger Quality** | 5 | MANDATORY TRIGGERS cover: product name (Redis), CLI tools (redis-cli, redis-server), client libraries (redis-py, ioredis), key commands (HSET, ZADD, XADD, LPUSH, FT.CREATE), architectural concepts (Redis Cluster, Redis Sentinel, RDB, AOF), patterns (cache-aside, eviction policy), and broad use-case triggers (caching, session storage, rate limiting, leaderboards, message queues). |

## Overall: 5.0 / 5.0

## Notes

- Redis 8.x unifies previously modular features (JSON, TimeSeries, Search, Bloom) as built-in data types, simplifying the skill structure
- The caching patterns reference (07) is particularly valuable as a standalone guide for any caching architecture decision
- Vector sets coverage supports the growing AI/ML use case for Redis as a vector database
- The skill complements existing `upstash` skill (serverless Redis platform) by covering Redis core concepts and self-hosted deployments
