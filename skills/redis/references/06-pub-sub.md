# Redis — Pub/Sub

> Source: [redis.io/docs/interact/pubsub](https://redis.io/docs/latest/develop/interact/pubsub/) — Redis 8.6

## Table of Contents

- [Overview](#overview)
- [Core Commands](#core-commands)
- [Pattern Subscriptions](#pattern-subscriptions)
- [Sharded Pub/Sub](#sharded-pubsub)
- [Subscriber Mode](#subscriber-mode)
- [Patterns](#patterns)
- [Pub/Sub vs Streams](#pubsub-vs-streams)
- [Common Pitfalls](#common-pitfalls)

## Overview

Redis Pub/Sub implements a fire-and-forget messaging system. Publishers send messages to channels without knowing who receives them. Subscribers listen to channels and receive messages in real-time.

**Key characteristics:**
- **No persistence** — Messages are not stored; if no subscriber is listening, the message is lost
- **No acknowledgment** — No confirmation that a subscriber received the message
- **At-most-once delivery** — Messages delivered to all current subscribers, then discarded
- **Zero queue** — Messages are not buffered if subscribers are slow or disconnected
- **Decoupled** — Publishers and subscribers don't need to know about each other

## Core Commands

### Publishing

```redis
# Publish message to channel
PUBLISH chat:general "Hello, everyone!"
# Returns: (integer) 3  — number of subscribers that received the message

PUBLISH notifications:user:1001 '{"type":"message","from":"bob","text":"Hi!"}'
# Returns: (integer) 0  — no subscribers (message is lost)

# Publish returns count of recipients, NOT delivery confirmation
```

### Subscribing

```redis
# Subscribe to one or more channels
SUBSCRIBE chat:general

# Output when message received:
# 1) "message"
# 2) "chat:general"
# 3) "Hello, everyone!"

# Subscribe to multiple channels
SUBSCRIBE chat:general chat:support notifications
```

### Unsubscribing

```redis
# Unsubscribe from specific channels
UNSUBSCRIBE chat:general

# Unsubscribe from all channels
UNSUBSCRIBE
```

## Pattern Subscriptions

Subscribe to channels matching glob-style patterns:

```redis
# Subscribe to all chat channels
PSUBSCRIBE chat:*

# Subscribe to all user notifications
PSUBSCRIBE notifications:user:*

# Multiple patterns
PSUBSCRIBE chat:* notifications:* alerts:*

# Pattern matching rules:
# *     — matches any sequence of characters
# ?     — matches any single character
# [abc] — matches a, b, or c

# Output for pattern subscription:
# 1) "pmessage"
# 2) "chat:*"                    ← pattern that matched
# 3) "chat:general"              ← actual channel
# 4) "Hello!"                    ← message
```

### Unsubscribe from Patterns

```redis
PUNSUBSCRIBE chat:*
PUNSUBSCRIBE                     # Unsubscribe all patterns
```

## Sharded Pub/Sub

Introduced in Redis 7.0, sharded pub/sub restricts message delivery to subscribers on the same shard in Redis Cluster. This improves scalability by avoiding cluster-wide broadcast.

```redis
# Sharded publish (message stays on the shard owning the channel)
SPUBLISH orders:region:us "new order"

# Sharded subscribe
SSUBSCRIBE orders:region:us

# Sharded unsubscribe
SUNSUBSCRIBE orders:region:us
```

**When to use sharded pub/sub:**
- Redis Cluster deployments with high message volume
- Channel names that naturally partition (per-user, per-region)
- Reducing cross-node network traffic

## Subscriber Mode

When a client subscribes, it enters subscriber mode with restrictions:

**Allowed commands in subscriber mode:**
- `SUBSCRIBE`, `UNSUBSCRIBE`
- `PSUBSCRIBE`, `PUNSUBSCRIBE`
- `SSUBSCRIBE`, `SUNSUBSCRIBE`
- `PING`
- `RESET` (exit subscriber mode)

**NOT allowed in subscriber mode:**
- Any data commands (GET, SET, etc.)
- Transactions (MULTI/EXEC)
- Scripting (EVAL)

This means you need **separate connections** for subscribing and publishing:

```python
import redis

# Connection 1: subscriber
sub = redis.Redis().pubsub()
sub.subscribe("events")

# Connection 2: publisher (and regular commands)
pub = redis.Redis()
pub.publish("events", "hello")
pub.set("key", "value")  # regular commands work
```

## Introspection

```redis
# List active channels (with at least one subscriber)
PUBSUB CHANNELS

# List channels matching pattern
PUBSUB CHANNELS chat:*

# Count subscribers per channel
PUBSUB NUMSUB chat:general chat:support
# 1) "chat:general"
# 2) (integer) 5
# 3) "chat:support"
# 4) (integer) 2

# Count pattern subscribers
PUBSUB NUMPAT                    # Total pattern subscriptions

# Sharded channel list
PUBSUB SHARDCHANNELS
PUBSUB SHARDNUMSUB orders:region:us
```

## Patterns

### Real-Time Notifications

```python
import redis
import json

r = redis.Redis()

# Publisher side
def notify_user(user_id: str, message: dict):
    channel = f"notifications:user:{user_id}"
    r.publish(channel, json.dumps(message))

notify_user("1001", {"type": "message", "from": "bob", "text": "Hey!"})

# Subscriber side
pubsub = r.pubsub()
pubsub.subscribe("notifications:user:1001")

for message in pubsub.listen():
    if message["type"] == "message":
        data = json.loads(message["data"])
        handle_notification(data)
```

### Chat Room

```redis
# User joins room
SUBSCRIBE chat:room:42

# User sends message
PUBLISH chat:room:42 '{"user":"alice","text":"Hello!","ts":1719014400}'

# Monitor room activity
PSUBSCRIBE chat:room:*
```

### Cache Invalidation

```redis
# When data changes, notify all app instances
PUBLISH cache:invalidate '{"key":"user:1001","reason":"profile_updated"}'

# Each app instance subscribes
SUBSCRIBE cache:invalidate
# On message: delete local cache entry
```

### Event Broadcasting

```python
import redis
import json

r = redis.Redis()

# Broadcast system events
def broadcast_event(event_type: str, payload: dict):
    r.publish(f"events:{event_type}", json.dumps(payload))

broadcast_event("order.created", {"order_id": "5001", "total": 59.99})
broadcast_event("user.signup", {"user_id": "1001", "plan": "premium"})

# Subscribe to all order events
pubsub = r.pubsub()
pubsub.psubscribe("events:order.*")
```

### Keyspace Notifications

Redis can publish events for key operations:

```redis
# Enable keyspace notifications (in redis.conf or at runtime)
CONFIG SET notify-keyspace-events KEA
# K = keyspace events, E = keyevent events, A = all commands

# Subscribe to all SET operations
SUBSCRIBE __keyevent@0__:set

# Subscribe to all operations on a specific key
SUBSCRIBE __keyspace@0__:user:1001

# Subscribe to expired key events
SUBSCRIBE __keyevent@0__:expired
```

## Pub/Sub vs Streams

| Feature | Pub/Sub | Streams |
|---------|---------|---------|
| **Delivery** | At-most-once, fire-and-forget | At-least-once with acknowledgment |
| **Persistence** | No — messages lost if no subscriber | Yes — stored on disk |
| **Replay** | No — cannot read past messages | Yes — XRANGE for historical data |
| **Consumer groups** | No — all subscribers get all messages | Yes — load balancing with XREADGROUP |
| **Backpressure** | No — slow subscribers miss messages | Yes — pending messages tracked |
| **Performance** | Lower latency, simpler protocol | Slightly higher latency, more features |
| **Use case** | Real-time notifications, chat | Event sourcing, reliable queues, audit logs |

**Rule of thumb:** Use pub/sub for real-time notifications where message loss is acceptable. Use streams when you need reliability, replay, or consumer groups.

## Common Pitfalls

1. **Assuming message delivery** — Pub/sub is fire-and-forget. If no subscribers are connected, messages are lost forever.
2. **Using one connection for sub and pub** — Subscriber mode blocks regular commands. Use separate connections.
3. **No reconnection handling** — Subscribers miss all messages during disconnection. Implement reconnection logic.
4. **Slow subscribers** — Redis buffers messages for slow subscribers up to `client-output-buffer-limit`. Exceeding this disconnects the subscriber.
5. **Using pub/sub for job queues** — No acknowledgment or retry. Use streams with consumer groups instead.
6. **Pattern subscriptions at scale** — Each PSUBSCRIBE pattern is checked against every published message. Many patterns can degrade performance.

## Related

- `04-streams.md` — Persistent messaging with consumer groups
- `00-overview.md` — Redis configuration for pub/sub limits
- `12-client-libraries.md` — Language-specific pub/sub implementations
