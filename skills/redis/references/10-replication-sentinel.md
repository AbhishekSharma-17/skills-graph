# Redis — Replication & Sentinel

> Source: [redis.io/docs/management/replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/) — Redis 8.6

## Table of Contents

- [Replication Overview](#replication-overview)
- [Configuration](#configuration)
- [Synchronization Process](#synchronization-process)
- [Read Replicas](#read-replicas)
- [Redis Sentinel](#redis-sentinel)
- [Sentinel Configuration](#sentinel-configuration)
- [Sentinel Commands](#sentinel-commands)
- [Client Integration](#client-integration)
- [High Availability Patterns](#high-availability-patterns)
- [Common Pitfalls](#common-pitfalls)

## Replication Overview

Redis uses asynchronous leader-follower replication. One master handles all writes; replicas receive a continuous stream of updates and serve read queries.

```
┌─────────────┐      ┌──────────────┐
│   Master    │─────▶│  Replica 1   │  (read queries)
│  (writes)   │      └──────────────┘
│             │      ┌──────────────┐
│             │─────▶│  Replica 2   │  (read queries)
│             │      └──────────────┘
│             │      ┌──────────────┐
│             │─────▶│  Replica 3   │  (read queries)
└─────────────┘      └──────────────┘
```

**Key characteristics:**
- Asynchronous by default (configurable synchronous acknowledgment with WAIT)
- Non-blocking on master — clients served during replication
- Replicas can have their own replicas (cascading replication)
- Replication uses RDB snapshots for initial sync, then streaming commands

## Configuration

### Basic Replica Setup

```conf
# replica redis.conf
replicaof 192.168.1.100 6379

# If master requires authentication
masterauth <master-password>
masteruser <master-username>

# Read-only mode (default, recommended)
replica-read-only yes

# Serve stale data during sync (yes = return potentially stale data)
replica-serve-stale-data yes
```

### Runtime Configuration

```redis
# Make this instance a replica of master
REPLICAOF 192.168.1.100 6379

# Promote replica to standalone master
REPLICAOF NO ONE

# Check replication status
INFO replication
# role:slave
# master_host:192.168.1.100
# master_port:6379
# master_link_status:up
# master_last_io_seconds_ago:1
# slave_repl_offset:12345

# Get role information
ROLE
```

### Diskless Replication

Skip writing RDB to disk during sync — send directly to replica over the network:

```conf
# Master config
repl-diskless-sync yes           # Send RDB via socket, not disk
repl-diskless-sync-delay 5       # Wait 5s for more replicas before starting
repl-diskless-sync-period 0      # Repeat sync for late replicas (0 = disabled)

# Replica config
repl-diskless-load disabled      # disabled, on-empty-db, or swapdb
```

Use diskless replication when disk is slow but network is fast.

### Write Safety

```conf
# Require minimum replicas before accepting writes
min-replicas-to-write 1          # At least 1 replica connected
min-replicas-max-lag 10          # With replication lag ≤ 10 seconds

# If conditions not met, master rejects writes with error
```

### Synchronous Replication with WAIT

```redis
SET important:data "critical"

# Wait until at least 2 replicas acknowledge
WAIT 2 5000
# Returns: number of replicas that acknowledged within 5000ms timeout

# WAIT 0 = wait for ALL replicas (no timeout)
```

## Synchronization Process

### Initial Full Sync

```
1. Replica connects and sends PSYNC ? -1 (first sync)
2. Master starts BGSAVE (fork + RDB snapshot)
3. Master buffers new writes in replication backlog
4. Master sends RDB file to replica
5. Replica loads RDB (replaces existing data)
6. Master sends buffered commands
7. Ongoing: master streams all writes to replica
```

### Partial Resynchronization

After a brief disconnection, replicas attempt to resume from where they left off:

```
1. Replica reconnects with PSYNC <repl-id> <offset>
2. Master checks if offset is still in replication backlog
3. If yes: sends only missing commands (fast)
4. If no: triggers full resynchronization (slow)
```

```conf
# Replication backlog size (affects partial sync window)
repl-backlog-size 256mb          # Default: 1mb — increase for busy servers

# How long to keep backlog after last replica disconnects
repl-backlog-ttl 3600
```

## Read Replicas

### Scaling Reads

```python
import redis

# Write to master
master = redis.Redis(host="master", port=6379)
master.set("key", "value")

# Read from replicas (round-robin)
replicas = [
    redis.Redis(host="replica1", port=6379),
    redis.Redis(host="replica2", port=6379),
]

import itertools
replica_cycle = itertools.cycle(replicas)

def read(key: str):
    return next(replica_cycle).get(key)
```

### Replication Lag

```redis
# On master: check replica lag
INFO replication
# slave0:ip=10.0.0.2,port=6379,state=online,offset=12345,lag=0
# slave1:ip=10.0.0.3,port=6379,state=online,offset=12340,lag=1

# On replica: check own offset
INFO replication
# slave_repl_offset:12345
# slave_read_repl_offset:12345
```

## Redis Sentinel

Sentinel provides automatic failover and monitoring for Redis master-replica deployments.

### Architecture

```
┌───────────┐  ┌───────────┐  ┌───────────┐
│ Sentinel 1│  │ Sentinel 2│  │ Sentinel 3│
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘
      │               │               │
      └───────┬───────┴───────┬───────┘
              │               │
      ┌───────▼───────┐ ┌────▼──────────┐
      │    Master     │ │   Replicas    │
      └───────────────┘ └───────────────┘
```

**Sentinel responsibilities:**
- **Monitoring** — Checks if master and replicas are reachable
- **Notification** — Alerts when something goes wrong
- **Automatic failover** — Promotes replica to master if master fails
- **Configuration provider** — Clients query Sentinel for current master address

### Minimum Deployment

- **3 Sentinel instances** (for quorum voting)
- **1 master + 2 replicas** (minimum for safe failover)
- Sentinels should be on separate machines/VMs

## Sentinel Configuration

```conf
# sentinel.conf
port 26379

# Monitor master named "mymaster" at 192.168.1.100:6379
# Quorum of 2 = 2 Sentinels must agree master is down
sentinel monitor mymaster 192.168.1.100 6379 2

# Time before marking master as down (milliseconds)
sentinel down-after-milliseconds mymaster 5000

# Number of replicas to reconfigure simultaneously during failover
sentinel parallel-syncs mymaster 1

# Failover timeout (milliseconds)
sentinel failover-timeout mymaster 60000

# Master password
sentinel auth-pass mymaster <password>

# Sentinel password (for Sentinel-to-Sentinel auth)
requirepass <sentinel-password>
```

### Starting Sentinel

```bash
# As a dedicated process
redis-sentinel /etc/redis/sentinel.conf

# Or via redis-server
redis-server /etc/redis/sentinel.conf --sentinel
```

## Sentinel Commands

```redis
# Connect to Sentinel
redis-cli -p 26379

# Get current master address
SENTINEL get-master-addr-by-name mymaster
# 1) "192.168.1.100"
# 2) "6379"

# List all monitored masters
SENTINEL masters

# List replicas of a master
SENTINEL replicas mymaster

# List other Sentinels
SENTINEL sentinels mymaster

# Check master status
SENTINEL is-master-down-by-addr 192.168.1.100 6379 0 *

# Manual failover
SENTINEL failover mymaster

# Reset Sentinel state
SENTINEL reset mymaster

# Change configuration at runtime
SENTINEL SET mymaster down-after-milliseconds 10000
```

## Client Integration

Clients should connect through Sentinel to automatically discover the master:

### Python (redis-py)

```python
from redis.sentinel import Sentinel

# Connect to Sentinels
sentinel = Sentinel(
    [
        ("sentinel1", 26379),
        ("sentinel2", 26379),
        ("sentinel3", 26379),
    ],
    socket_timeout=0.5,
    password="sentinel-password",
)

# Get master connection (auto-discovers current master)
master = sentinel.master_for("mymaster", password="redis-password", db=0)
master.set("key", "value")

# Get replica connection (for reads)
replica = sentinel.slave_for("mymaster", password="redis-password", db=0)
value = replica.get("key")
```

### Node.js (ioredis)

```javascript
const Redis = require("ioredis");

const redis = new Redis({
  sentinels: [
    { host: "sentinel1", port: 26379 },
    { host: "sentinel2", port: 26379 },
    { host: "sentinel3", port: 26379 },
  ],
  name: "mymaster",
  password: "redis-password",
  sentinelPassword: "sentinel-password",
});

await redis.set("key", "value");
```

## High Availability Patterns

### Recommended Production Setup

```
3 Sentinels (separate machines)
1 Master + 2 Replicas

sentinel.conf:
  sentinel monitor mymaster <master-ip> 6379 2
  sentinel down-after-milliseconds mymaster 5000
  sentinel failover-timeout mymaster 60000
  sentinel parallel-syncs mymaster 1

Master redis.conf:
  min-replicas-to-write 1
  min-replicas-max-lag 10
  appendonly yes

Replica redis.conf:
  replicaof <master-ip> 6379
  replica-read-only yes
  appendonly yes
```

### Failover Process

```
1. Sentinel detects master is unreachable (SDOWN — subjective down)
2. Multiple Sentinels confirm (ODOWN — objective down, requires quorum)
3. Sentinels elect a leader Sentinel
4. Leader selects best replica (most data, lowest lag)
5. Selected replica promoted: REPLICAOF NO ONE
6. Other replicas reconfigured to follow new master
7. Clients notified via Sentinel pub/sub
8. Old master becomes replica when it comes back
```

## Common Pitfalls

1. **Only 1-2 Sentinels** — Need at least 3 for reliable quorum voting. Even numbers risk split-brain.
2. **Sentinel on same machine as Redis** — If the machine dies, you lose both Sentinel and Redis. Use separate hosts.
3. **Persistence disabled on master** — If master restarts with empty dataset, replicas wipe their data too.
4. **Not using Sentinel-aware clients** — Hardcoding master IP means no automatic failover for the application.
5. **Ignoring replication lag** — Reads from replicas may return stale data. Use WAIT for critical reads.
6. **Small replication backlog** — Causes full resync after brief disconnections. Set `repl-backlog-size` to at least 256MB for busy servers.

## Related

- `09-persistence.md` — Persistence settings for master and replicas
- `11-cluster.md` — Redis Cluster for horizontal scaling (vs. Sentinel for HA)
- `12-client-libraries.md` — Sentinel-aware client configuration
