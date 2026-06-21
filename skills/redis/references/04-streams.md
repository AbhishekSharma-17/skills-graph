# Redis — Streams

> Source: [redis.io/docs/data-types/streams](https://redis.io/docs/latest/develop/data-types/streams/) — Redis 8.6

## Table of Contents

- [Overview](#overview)
- [Adding Entries](#adding-entries)
- [Reading Entries](#reading-entries)
- [Consumer Groups](#consumer-groups)
- [Claiming & Recovery](#claiming--recovery)
- [Stream Management](#stream-management)
- [Patterns](#patterns)
- [Common Pitfalls](#common-pitfalls)

## Overview

Streams are append-only log data structures — Redis's most powerful data type for event processing and message queuing. Unlike pub/sub, streams persist messages and support consumer groups with acknowledgment.

**Key characteristics:**
- Append-only log with auto-generated IDs (timestamp-based)
- Multiple consumers can read independently
- Consumer groups for load balancing with message acknowledgment
- Efficient range queries and trimming
- Message persistence (survives restarts with AOF/RDB)

**Streams vs Lists vs Pub/Sub:**

| Feature | Streams | Lists | Pub/Sub |
|---------|---------|-------|---------|
| Persistence | Yes | Yes | No |
| Consumer groups | Yes | No | No |
| Acknowledgment | Yes | Manual | No |
| Multiple consumers | Yes | Competing | Broadcast |
| Range queries | Yes | Yes | No |
| Blocking reads | Yes | Yes | Yes (inherent) |

## Adding Entries

```redis
# Add entry with auto-generated ID
XADD events * user "alice" action "login" ip "1.2.3.4"
# Returns: "1719014400000-0" (timestamp-sequence)

# Add with specific ID
XADD events 1719014400000-0 user "alice" action "login"

# Add with partial ID (auto-sequence)
XADD events 1719014400000 user "alice" action "login"

# Auto-generated IDs are guaranteed to be:
# - Monotonically increasing
# - Unique within the stream
# - Format: <millisecond-timestamp>-<sequence>
```

### Stream Trimming

```redis
# Trim to max length
XADD events MAXLEN 10000 * user "bob" action "view"

# Approximate trim (~) — faster, trims to nearest internal node
XADD events MAXLEN ~ 10000 * user "bob" action "view"

# Trim by minimum ID (time-based retention)
XADD events MINID ~ 1719014400000 * user "bob" action "view"

# Standalone trim command
XTRIM events MAXLEN 10000
XTRIM events MINID 1719014400000
```

## Reading Entries

### XREAD — Independent Reading

```redis
# Read new entries from one or more streams
XREAD COUNT 10 STREAMS events 0
# Returns all entries from the beginning

# Read only new entries (entries added after this call)
XREAD COUNT 10 STREAMS events $

# Read from specific ID onwards
XREAD COUNT 10 STREAMS events 1719014400000-0

# Read from multiple streams
XREAD COUNT 10 STREAMS events notifications 0 0

# Blocking read (wait up to 5000ms for new entries)
XREAD BLOCK 5000 COUNT 10 STREAMS events $

# Block forever
XREAD BLOCK 0 COUNT 10 STREAMS events $
```

### XRANGE / XREVRANGE — Range Queries

```redis
# All entries
XRANGE events - +

# By ID range
XRANGE events 1719014400000 1719100800000

# First N entries
XRANGE events - + COUNT 10

# Last N entries
XREVRANGE events + - COUNT 10

# Entries after a specific ID (exclusive)
XRANGE events (1719014400000-5 +
```

### Entry Information

```redis
# Stream length
XLEN events                                  # Number of entries

# Stream metadata
XINFO STREAM events                          # Summary info
XINFO STREAM events FULL                     # Full details including all entries

# First and last entry IDs
XINFO STREAM events
# Returns: first-entry, last-entry, length, etc.
```

## Consumer Groups

Consumer groups enable multiple consumers to cooperate on processing a stream, with each message delivered to exactly one consumer in the group.

### Create Group

```redis
# Create group starting from latest entries
XGROUP CREATE events processor-group $ MKSTREAM

# Create group starting from beginning
XGROUP CREATE events processor-group 0

# Create group from specific ID
XGROUP CREATE events processor-group 1719014400000-0
```

### Read with Group

```redis
# Consumer reads new messages assigned to it
XREADGROUP GROUP processor-group consumer-1 COUNT 10 STREAMS events >

# ">" means only new (undelivered) messages
# Using a specific ID reads pending (already delivered but unacknowledged) messages

# Read pending messages for this consumer
XREADGROUP GROUP processor-group consumer-1 COUNT 10 STREAMS events 0

# Blocking read with group
XREADGROUP GROUP processor-group consumer-1 BLOCK 5000 COUNT 10 STREAMS events >
```

### Acknowledge Messages

```redis
# Mark message as processed
XACK events processor-group 1719014400000-0

# Acknowledge multiple messages
XACK events processor-group 1719014400000-0 1719014400001-0 1719014400002-0
```

### Pending Messages

```redis
# Summary of pending messages per consumer
XPENDING events processor-group - + 10

# Detailed pending list
XPENDING events processor-group IDLE 60000 - + 10
# Messages idle for >60 seconds

# Pending count per consumer
XPENDING events processor-group - + 10
# Returns: [consumer-name, count-of-pending, min-id, max-id]
```

## Claiming & Recovery

When a consumer crashes, its pending messages need to be reassigned:

### XCLAIM

```redis
# Claim messages idle for >300 seconds, assign to consumer-2
XCLAIM events processor-group consumer-2 300000 1719014400000-0

# Claim with JUSTID (return only IDs, not full entries)
XCLAIM events processor-group consumer-2 300000 1719014400000-0 JUSTID

# Force claim (reset idle time and delivery count)
XCLAIM events processor-group consumer-2 0 1719014400000-0 FORCE
```

### XAUTOCLAIM (Redis 6.2+)

Automatically claims idle messages without knowing their IDs:

```redis
# Auto-claim messages idle for >300 seconds
XAUTOCLAIM events processor-group consumer-2 300000 0-0
# Returns: [next-cursor, [claimed-messages], [deleted-ids]]

# With COUNT limit
XAUTOCLAIM events processor-group consumer-2 300000 0-0 COUNT 10

# Iterate with cursor
XAUTOCLAIM events processor-group consumer-2 300000 <next-cursor> COUNT 10
```

## Stream Management

### Group Management

```redis
# List all groups
XINFO GROUPS events

# List consumers in a group
XINFO CONSUMERS events processor-group

# Delete consumer from group
XGROUP DELCONSUMER events processor-group consumer-3

# Delete entire group
XGROUP DESTROY events processor-group

# Change group's last-delivered-id
XGROUP SETID events processor-group $        # Skip to latest
XGROUP SETID events processor-group 0        # Reprocess from beginning
```

### Delete Entries

```redis
# Delete specific entries
XDEL events 1719014400000-0 1719014400001-0

# Delete entries doesn't reclaim memory immediately (marks as deleted)
# Use XTRIM for memory reclamation
```

## Patterns

### Event Sourcing

```redis
# Append domain events
XADD orders * event "created" order_id "5001" customer "alice" total "59.99"
XADD orders * event "paid" order_id "5001" payment_method "card"
XADD orders * event "shipped" order_id "5001" tracking "TRK123"

# Replay events to rebuild state
XRANGE orders - +
```

### Fan-Out Processing

```redis
# Multiple consumer groups process the SAME stream independently
XGROUP CREATE events analytics-group 0
XGROUP CREATE events notifications-group 0
XGROUP CREATE events audit-group 0

# Analytics team processes events
XREADGROUP GROUP analytics-group analytics-1 COUNT 100 STREAMS events >

# Notifications team processes the SAME events independently
XREADGROUP GROUP notifications-group notifier-1 COUNT 100 STREAMS events >
```

### Reliable Worker Pattern

```python
# Python pseudocode for reliable stream consumer
import redis

r = redis.Redis()
group = "worker-group"
consumer = "worker-1"
stream = "tasks"

while True:
    # 1. Check for pending messages first (crashed consumer recovery)
    pending = r.xautoclaim(stream, group, consumer, min_idle_time=300000, start_id="0-0", count=10)

    for msg_id, fields in pending[1]:
        process(fields)
        r.xack(stream, group, msg_id)

    # 2. Read new messages
    messages = r.xreadgroup(group, consumer, {stream: ">"}, count=10, block=5000)

    if messages:
        for stream_name, entries in messages:
            for msg_id, fields in entries:
                try:
                    process(fields)
                    r.xack(stream, group, msg_id)
                except Exception:
                    pass  # Message stays pending, will be auto-claimed
```

### Capped Stream (Bounded Memory)

```redis
# Always trim when adding
XADD telemetry MAXLEN ~ 100000 * sensor "temp" value "23.5"

# Time-based retention: keep only last 24 hours
XADD telemetry MINID ~ 1718928000000 * sensor "temp" value "23.5"
```

## Common Pitfalls

1. **Not acknowledging messages** — Pending list grows unbounded, consuming memory.
2. **Using `$` as group start** — Misses entries added between group creation and first read. Use `0` to process from beginning.
3. **Ignoring XAUTOCLAIM** — Dead consumers leave orphaned pending messages forever.
4. **No MAXLEN/MINID on XADD** — Streams grow unbounded without trimming.
5. **Using streams as simple queues** — If you don't need persistence or consumer groups, blocking lists (BLPOP) are simpler.
6. **Large COUNT values** — Fetching millions of entries blocks Redis. Use reasonable COUNT with iteration.

## Related

- `02-hashes-lists.md` — Lists for simpler queue patterns
- `06-pub-sub.md` — Fire-and-forget messaging (no persistence)
- `08-transactions-scripting.md` — Atomic multi-command operations
