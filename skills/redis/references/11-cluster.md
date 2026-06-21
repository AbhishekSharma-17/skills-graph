# Redis — Cluster

> Source: [redis.io/docs/management/scaling](https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/) — Redis 8.6

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Hash Slots & Sharding](#hash-slots--sharding)
- [Cluster Setup](#cluster-setup)
- [Cluster Operations](#cluster-operations)
- [Resharding](#resharding)
- [Failover](#failover)
- [Client Connections](#client-connections)
- [Consistency Guarantees](#consistency-guarantees)
- [Common Pitfalls](#common-pitfalls)

## Overview

Redis Cluster provides horizontal scaling by automatically sharding data across multiple Redis nodes. It combines data partitioning with high availability through automatic failover.

**Key characteristics:**
- 16,384 hash slots distributed across master nodes
- Each master handles a subset of hash slots
- Each master can have one or more replicas for failover
- No proxy required — clients connect directly to nodes
- Automatic failover when a master becomes unreachable

## Architecture

```
┌──────────────────────────────────────────────────┐
│                 Redis Cluster                     │
│                                                   │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐        │
│  │Master A │   │Master B │   │Master C │         │
│  │slots    │   │slots    │   │slots    │         │
│  │0-5460   │   │5461-    │   │10923-   │         │
│  │         │   │10922    │   │16383    │         │
│  └────┬────┘   └────┬────┘   └────┬────┘        │
│       │              │              │             │
│  ┌────▼────┐   ┌────▼────┐   ┌────▼────┐        │
│  │Replica  │   │Replica  │   │Replica  │         │
│  │A1       │   │B1       │   │C1       │         │
│  └─────────┘   └─────────┘   └─────────┘        │
│                                                   │
│  Cluster Bus: node-to-node gossip protocol        │
└──────────────────────────────────────────────────┘
```

### Network Ports

Each node needs two ports:
- **Client port** (default: 6379) — For client commands
- **Cluster bus port** (client port + 10000, default: 16379) — For node-to-node communication

Both ports must be open in firewalls.

## Hash Slots & Sharding

### How Keys Are Mapped

```
slot = CRC16(key) mod 16384
```

Every key maps to one of 16,384 hash slots, and each slot is assigned to exactly one master node.

### Hash Tags

Keys with the same hash tag are guaranteed to be on the same slot:

```redis
# These keys map to the same slot (hash tag = {user:1001})
SET {user:1001}:name "Alice"
SET {user:1001}:email "alice@example.com"
SET {user:1001}:prefs '{"theme":"dark"}'

# Multi-key operations work on same-slot keys
MGET {user:1001}:name {user:1001}:email
```

Hash tag syntax: only the content inside the first `{...}` is hashed.

```redis
# These all hash on "order"
{order}:5001
{order}:5002
{order}:items:5001

# WRONG — different hash tags
order:{5001}         # Hashes on "5001"
order:{5002}         # Hashes on "5002" — different slot!
```

### Multi-Key Limitations

```redis
# Works — same hash tag
MGET {user:1}:name {user:1}:email

# FAILS — different slots
MGET user:1:name user:2:name
# (error) CROSSSLOT Keys in request don't hash to the same slot
```

Operations that span multiple keys MUST use hash tags to ensure same-slot placement:
- `MGET`, `MSET`, `DEL` (multiple keys)
- `SUNION`, `SINTER`, `SDIFF`
- `ZUNIONSTORE`, `ZINTERSTORE`
- Lua scripts accessing multiple keys

## Cluster Setup

### Minimum: 6 Nodes (3 Masters + 3 Replicas)

```bash
# Create directories for each node
for port in 7000 7001 7002 7003 7004 7005; do
    mkdir -p cluster/$port
done

# redis.conf for each node (adjust port)
cat > cluster/7000/redis.conf << 'EOF'
port 7000
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
EOF
# Repeat for 7001-7005 with adjusted port

# Start each node
for port in 7000 7001 7002 7003 7004 7005; do
    redis-server cluster/$port/redis.conf &
done
```

### Create the Cluster

```bash
redis-cli --cluster create \
    127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
    127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
    --cluster-replicas 1

# Output:
# >>> Performing hash slots allocation on 6 nodes...
# Master[0] -> Slots 0 - 5460
# Master[1] -> Slots 5461 - 10922
# Master[2] -> Slots 10923 - 16383
# [OK] All 16384 slots covered.
```

### Docker Compose Cluster

```yaml
services:
  redis-1:
    image: redis:8.6-alpine
    command: redis-server --port 6379 --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes
    ports: ["7001:6379"]
    networks: [redis-net]
  redis-2:
    image: redis:8.6-alpine
    command: redis-server --port 6379 --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes
    ports: ["7002:6379"]
    networks: [redis-net]
  # ... repeat for 4 more nodes
networks:
  redis-net:
```

## Cluster Operations

### Information & Monitoring

```redis
# Connect in cluster mode
redis-cli -c -p 7000

# Cluster status
CLUSTER INFO
# cluster_state:ok
# cluster_slots_assigned:16384
# cluster_slots_ok:16384
# cluster_known_nodes:6
# cluster_size:3

# List all nodes
CLUSTER NODES

# Show slot assignments
CLUSTER SLOTS

# Count keys in a specific slot
CLUSTER COUNTKEYSINSLOT 5000

# Find which slot a key belongs to
CLUSTER KEYSLOT mykey
```

### Adding Nodes

```bash
# Add as master (initially with 0 slots)
redis-cli --cluster add-node 127.0.0.1:7006 127.0.0.1:7000

# Add as replica of specific master
redis-cli --cluster add-node 127.0.0.1:7007 127.0.0.1:7000 \
    --cluster-slave --cluster-master-id <master-node-id>
```

### Removing Nodes

```bash
# Remove empty node (replica or master with no slots)
redis-cli --cluster del-node 127.0.0.1:7000 <node-id>

# To remove a master: first reshard its slots away, then delete
```

## Resharding

Move hash slots between masters without downtime:

```bash
# Interactive resharding
redis-cli --cluster reshard 127.0.0.1:7000

# Non-interactive
redis-cli --cluster reshard 127.0.0.1:7000 \
    --cluster-from <source-node-id> \
    --cluster-to <target-node-id> \
    --cluster-slots 1000 \
    --cluster-yes

# Rebalance slots evenly across masters
redis-cli --cluster rebalance 127.0.0.1:7000

# Check cluster health
redis-cli --cluster check 127.0.0.1:7000

# Fix cluster inconsistencies
redis-cli --cluster fix 127.0.0.1:7000
```

## Failover

### Automatic Failover

When a master becomes unreachable:

```
1. Replicas detect master is down (cluster-node-timeout)
2. Replica with most data starts election
3. Majority of masters vote for the replica
4. Winner promotes itself and takes over the master's slots
5. Other nodes update their routing tables
```

### Manual Failover

```redis
# On the replica you want to promote:
CLUSTER FAILOVER              # Graceful — waits for data sync
CLUSTER FAILOVER FORCE        # Immediate — don't wait for sync
CLUSTER FAILOVER TAKEOVER     # Forced without majority vote
```

### Replica Migration

Redis Cluster automatically migrates replicas from well-provisioned masters to orphaned masters:

```conf
# Minimum replicas a master keeps (others can migrate)
cluster-migration-barrier 1
```

## Client Connections

### MOVED and ASK Redirections

```redis
# Client sends command to wrong node
GET mykey
# -MOVED 5431 127.0.0.1:7001
# Client should reconnect to 127.0.0.1:7001

# During resharding, keys being migrated:
GET mykey
# -ASK 5431 127.0.0.1:7002
# Client should send ASKING, then retry on 127.0.0.1:7002
```

### Python (redis-py Cluster)

```python
from redis.cluster import RedisCluster

rc = RedisCluster(
    host="127.0.0.1",
    port=7000,
    password="password",
    decode_responses=True,
)

rc.set("key", "value")
rc.get("key")

# Pipeline (slot-aware)
pipe = rc.pipeline()
pipe.set("{user:1}:name", "Alice")
pipe.set("{user:1}:email", "alice@example.com")
pipe.execute()
```

### Node.js (ioredis Cluster)

```javascript
const Redis = require("ioredis");

const cluster = new Redis.Cluster([
  { host: "127.0.0.1", port: 7000 },
  { host: "127.0.0.1", port: 7001 },
  { host: "127.0.0.1", port: 7002 },
]);

await cluster.set("key", "value");
const value = await cluster.get("key");
```

## Consistency Guarantees

Redis Cluster provides **weak (eventual) consistency**:

- Writes are acknowledged before replication to replicas
- If master fails before replicating, writes are lost
- During network partitions, writes to minority partition are lost when partition heals

Use `WAIT` for stronger guarantees:

```redis
SET critical:data "important"
WAIT 1 5000       # Wait for at least 1 replica to acknowledge within 5s
```

## Common Pitfalls

1. **Cross-slot operations without hash tags** — Multi-key commands fail unless all keys are on the same slot.
2. **Lua scripts accessing keys on different slots** — All KEYS[] in a script must map to the same slot.
3. **Docker NAT issues** — Cluster nodes advertise internal IPs. Use `--cluster-announce-ip` and `--cluster-announce-port`.
4. **Only 3 nodes total** — Minimum is 3 masters. Without replicas, any single master failure causes data loss.
5. **Forgetting about database selection** — Cluster mode only supports database 0.
6. **Not monitoring cluster health** — Run `redis-cli --cluster check` regularly and monitor `cluster_state` in CLUSTER INFO.

## Related

- `10-replication-sentinel.md` — Sentinel for HA without sharding
- `09-persistence.md` — Persistence configuration per cluster node
- `12-client-libraries.md` — Cluster-aware client configuration
