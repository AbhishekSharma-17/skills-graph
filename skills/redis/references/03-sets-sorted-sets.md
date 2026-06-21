# Redis — Sets & Sorted Sets

> Source: [redis.io/docs/data-types](https://redis.io/docs/latest/develop/data-types/) — Redis 8.6

## Table of Contents

- [Sets Overview](#sets-overview)
- [Set Commands](#set-commands)
- [Set Operations](#set-operations)
- [Set Patterns](#set-patterns)
- [Sorted Sets Overview](#sorted-sets-overview)
- [Sorted Set Commands](#sorted-set-commands)
- [Range Queries](#range-queries)
- [Sorted Set Patterns](#sorted-set-patterns)
- [Common Pitfalls](#common-pitfalls)

## Sets Overview

Sets are unordered collections of unique strings. All add, remove, and membership check operations are O(1). Sets support powerful operations like intersection, union, and difference.

## Set Commands

### Add & Remove

```redis
# Add members
SADD tags:post:1001 "redis" "database" "caching" "nosql"   # 4 (members added)
SADD tags:post:1001 "redis"                                  # 0 (already exists)

# Remove members
SREM tags:post:1001 "nosql"                                  # 1 (removed)

# Pop random member(s)
SPOP tags:post:1001                                          # Random member (removed)
SPOP tags:post:1001 2                                        # 2 random members

# Get random member(s) WITHOUT removing
SRANDMEMBER tags:post:1001                                   # Random member
SRANDMEMBER tags:post:1001 3                                 # 3 random unique members
SRANDMEMBER tags:post:1001 -3                                # 3 random (may repeat)

# Move member between sets
SMOVE source destination "member"
```

### Read

```redis
# Get all members
SMEMBERS tags:post:1001                  # All members (unordered)

# Check membership
SISMEMBER tags:post:1001 "redis"         # 1 (member exists)
SISMEMBER tags:post:1001 "mysql"         # 0 (not a member)

# Check multiple members at once (Redis 6.2+)
SMISMEMBER tags:post:1001 "redis" "mysql" "caching"
# [1, 0, 1]

# Count members
SCARD tags:post:1001                     # Number of members

# Safe iteration
SSCAN tags:post:1001 0 MATCH "c*" COUNT 10
```

## Set Operations

```redis
SADD team:frontend "Alice" "Bob" "Charlie"
SADD team:backend "Bob" "Diana" "Eve"
SADD team:devops "Charlie" "Eve" "Frank"

# Intersection — members in ALL sets
SINTER team:frontend team:backend                    # ["Bob"]

# Union — members in ANY set
SUNION team:frontend team:backend                    # ["Alice", "Bob", "Charlie", "Diana", "Eve"]

# Difference — members in first set but NOT others
SDIFF team:frontend team:backend                     # ["Alice", "Charlie"]

# Store results in a new set
SINTERSTORE team:fullstack team:frontend team:backend
SUNIONSTORE team:all team:frontend team:backend team:devops
SDIFFSTORE team:frontend-only team:frontend team:backend

# Count intersection without storing (Redis 7.0+)
SINTERCARD 2 team:frontend team:backend              # 1
SINTERCARD 2 team:frontend team:backend LIMIT 5      # With early termination
```

## Set Patterns

### Tag System

```redis
# Tag posts
SADD post:1001:tags "python" "redis" "tutorial"
SADD post:1002:tags "python" "fastapi" "api"
SADD post:1003:tags "redis" "caching" "performance"

# Reverse index: tag → posts
SADD tag:python:posts "1001" "1002"
SADD tag:redis:posts "1001" "1003"

# Find posts with BOTH tags
SINTER tag:python:posts tag:redis:posts   # ["1001"]

# Find posts with EITHER tag
SUNION tag:python:posts tag:redis:posts   # ["1001", "1002", "1003"]
```

### Unique Visitors

```redis
# Track unique visitors per page per day
SADD visitors:homepage:2026-06-22 "user:1001" "user:1002" "user:1003"

# Count unique visitors
SCARD visitors:homepage:2026-06-22        # 3

# Compare days
SDIFF visitors:homepage:2026-06-22 visitors:homepage:2026-06-21
# New visitors today
```

### Online Users

```redis
SADD online:users "user:1001" "user:1002"
SREM online:users "user:1001"              # User went offline
SISMEMBER online:users "user:1001"         # 0 (offline)
SCARD online:users                         # Count online users
```

## Sorted Sets Overview

Sorted sets (zsets) combine the uniqueness of sets with an ordering score. Each member has an associated floating-point score, and members are sorted by score (ascending). Members with equal scores are sorted lexicographically.

**Performance:** Add, remove, and rank operations are O(log N), making sorted sets efficient even with millions of members.

## Sorted Set Commands

### Add & Update

```redis
# Add members with scores
ZADD leaderboard 1500 "Alice" 1200 "Bob" 1800 "Charlie" 1350 "Diana"

# Update score (same command as add)
ZADD leaderboard 1600 "Alice"              # Updated Alice's score

# Add only if NOT exists
ZADD leaderboard NX 1000 "Eve"             # Only if "Eve" not in set

# Update only if EXISTS
ZADD leaderboard XX 1700 "Alice"           # Only if "Alice" already in set

# Add and return changed count
ZADD leaderboard GT 1900 "Alice"           # Only update if new score > old
ZADD leaderboard LT 1100 "Bob"            # Only update if new score < old

# Increment score
ZINCRBY leaderboard 50 "Bob"               # Bob's score += 50
```

### Read

```redis
# Get score
ZSCORE leaderboard "Alice"                 # 1700

# Get multiple scores (Redis 6.2+)
ZMSCORE leaderboard "Alice" "Bob"          # [1700, 1250]

# Get rank (0-based, ascending)
ZRANK leaderboard "Alice"                  # Rank by score ascending
ZREVRANK leaderboard "Alice"               # Rank by score descending

# Count members
ZCARD leaderboard                          # Total members

# Count members in score range
ZCOUNT leaderboard 1000 1500               # Members with score 1000-1500
ZCOUNT leaderboard "-inf" "+inf"           # All members
ZCOUNT leaderboard "(1000" 1500            # Exclusive lower bound
```

### Remove

```redis
ZREM leaderboard "Eve"                     # Remove specific member

# Remove by rank range
ZREMRANGEBYRANK leaderboard 0 2            # Remove bottom 3

# Remove by score range
ZREMRANGEBYSCORE leaderboard 0 1000        # Remove scores 0-1000

# Pop members with highest/lowest scores
ZPOPMIN leaderboard                        # Pop lowest score
ZPOPMAX leaderboard 3                      # Pop 3 highest scores

# Blocking pop (wait for elements)
BZPOPMIN leaderboard 30                    # Wait up to 30s
BZPOPMAX leaderboard 30
```

## Range Queries

```redis
# By rank (position)
ZRANGE leaderboard 0 -1                     # All, ascending by score
ZRANGE leaderboard 0 9                      # Top 10 (lowest scores)
ZRANGE leaderboard 0 -1 WITHSCORES          # Include scores

# Reverse order (highest first)
ZRANGE leaderboard 0 9 REV                  # Top 10 highest scores
# Or legacy command:
ZREVRANGE leaderboard 0 9 WITHSCORES

# By score range
ZRANGEBYSCORE leaderboard 1000 2000         # Scores between 1000-2000
ZRANGEBYSCORE leaderboard "-inf" "+inf"     # All
ZRANGEBYSCORE leaderboard 1000 2000 LIMIT 0 10  # Paginate

# By lexicographic range (when all scores are equal)
ZRANGEBYLEX leaderboard "[A" "[D"           # Members starting A-D
ZLEXCOUNT leaderboard "[A" "[D"             # Count in lex range

# Unified ZRANGE (Redis 6.2+)
ZRANGE leaderboard 1000 2000 BYSCORE LIMIT 0 10
ZRANGE leaderboard "[A" "[D" BYLEX
ZRANGE leaderboard 0 9 BYSCORE REV WITHSCORES
```

### Set Operations on Sorted Sets

```redis
ZADD math:scores 90 "Alice" 85 "Bob" 78 "Charlie"
ZADD science:scores 88 "Alice" 92 "Bob" 70 "Diana"

# Intersection (default: sum scores)
ZINTERSTORE combined 2 math:scores science:scores
# Alice: 178, Bob: 177

# With aggregate options
ZINTERSTORE combined 2 math:scores science:scores AGGREGATE MIN
ZINTERSTORE combined 2 math:scores science:scores AGGREGATE MAX
ZINTERSTORE combined 2 math:scores science:scores WEIGHTS 1 2

# Union
ZUNIONSTORE all_scores 2 math:scores science:scores

# Difference (Redis 6.2+)
ZDIFFSTORE math_only 2 math:scores science:scores

# Return results directly without storing (Redis 6.2+)
ZINTER 2 math:scores science:scores WITHSCORES
ZUNION 2 math:scores science:scores WITHSCORES
ZDIFF 2 math:scores science:scores WITHSCORES
```

## Sorted Set Patterns

### Leaderboard

```redis
# Update scores
ZADD game:leaderboard 15000 "player:alice"
ZINCRBY game:leaderboard 500 "player:alice"

# Top 10 players
ZRANGE game:leaderboard 0 9 REV WITHSCORES

# Player rank (1-based for display)
ZREVRANK game:leaderboard "player:alice"     # 0-based rank
# Add 1 for display: rank + 1

# Players around a specific rank
ZRANGE game:leaderboard 5 15 REV WITHSCORES   # Ranks 6-16
```

### Priority Queue

```redis
# Add tasks with priority (lower score = higher priority)
ZADD queue:tasks 1 "critical-fix" 5 "feature-request" 10 "nice-to-have"

# Take highest priority task
ZPOPMIN queue:tasks                          # "critical-fix" (score 1)

# Blocking priority queue
BZPOPMIN queue:tasks 0                       # Wait for tasks
```

### Time-Based Sorted Data

```redis
# Store events with Unix timestamp as score
ZADD events:user:1001 1719014400 '{"type":"login","ip":"1.2.3.4"}'
ZADD events:user:1001 1719100800 '{"type":"purchase","amount":59.99}'

# Query last 24 hours
ZRANGEBYSCORE events:user:1001 1719014400 +inf

# Remove events older than 7 days
ZREMRANGEBYSCORE events:user:1001 0 1718409600
```

### Sliding Window Rate Limiter

```redis
# Add request with timestamp as score and unique ID as member
ZADD ratelimit:user:1001 1719014423 "req:uuid-1"

# Remove old entries (older than 60 seconds)
ZREMRANGEBYSCORE ratelimit:user:1001 0 1719014363

# Count requests in window
ZCARD ratelimit:user:1001
# If count > limit, reject
```

## Common Pitfalls

1. **SMEMBERS on large sets** — Returns everything at once. Use SSCAN for sets with 10K+ members.
2. **ZRANGEBYSCORE without LIMIT** — Can return millions of results. Always paginate.
3. **Forgetting score precision** — Scores are IEEE 754 doubles; integers up to 2^53 are exact, beyond that precision is lost.
4. **Using sorted sets as queues** — Streams (XADD/XREADGROUP) are better for job queues with acknowledgment.
5. **SINTERSTORE with many large sets** — Can be slow. Consider precomputing intersections.

## Related

- `02-hashes-lists.md` — Hashes for objects, lists for ordered sequences
- `04-streams.md` — Persistent message queues with consumer groups
- `07-caching-patterns.md` — Using sorted sets for cache invalidation
