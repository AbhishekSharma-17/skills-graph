# Redis — Persistence

> Source: [redis.io/docs/management/persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/) — Redis 8.6

## Table of Contents

- [Overview](#overview)
- [RDB Snapshots](#rdb-snapshots)
- [AOF (Append Only File)](#aof-append-only-file)
- [Hybrid Persistence](#hybrid-persistence)
- [Choosing a Strategy](#choosing-a-strategy)
- [Backup Strategies](#backup-strategies)
- [Disaster Recovery](#disaster-recovery)
- [Common Pitfalls](#common-pitfalls)

## Overview

Redis stores data in memory but can persist to disk using four strategies:

| Strategy | Durability | Performance | Use Case |
|----------|-----------|-------------|----------|
| **None** | No persistence | Fastest | Pure cache, data is expendable |
| **RDB** | Periodic snapshots | Fast writes | Acceptable to lose minutes of data |
| **AOF** | Every write logged | Slight write overhead | Need durability, can't lose >1s |
| **RDB + AOF** | Both mechanisms | Most overhead | Maximum durability + fast recovery |

## RDB Snapshots

RDB creates point-in-time snapshots of the dataset as a compact binary file (`dump.rdb`).

### How It Works

```
1. Redis forks the process
2. Child process writes dataset to temporary RDB file
3. When complete, atomically replaces old RDB file
4. Parent process continues serving clients (copy-on-write)
```

### Configuration

```conf
# redis.conf

# Trigger RDB save:
# save <seconds> <changes>
save 3600 1         # After 3600s if at least 1 key changed
save 300 100        # After 300s if at least 100 keys changed
save 60 10000       # After 60s if at least 10000 keys changed

# Disable RDB
save ""

# RDB file name and directory
dbfilename dump.rdb
dir /var/lib/redis

# Compress RDB file (uses LZF)
rdbcompression yes

# Checksum at end of file
rdbchecksum yes

# Stop accepting writes if RDB save fails
stop-writes-on-bgsave-error yes
```

### Manual Triggers

```redis
# Background save (non-blocking, recommended)
BGSAVE

# Synchronous save (blocks ALL clients — avoid in production)
SAVE

# Check save status
LASTSAVE                                # Unix timestamp of last save
INFO persistence                        # Detailed persistence stats
```

### Advantages & Disadvantages

**Advantages:**
- Compact single file — perfect for backups
- Fast restarts (faster than AOF replay)
- Minimal performance impact during normal operations
- Good for disaster recovery (easy to ship to S3)

**Disadvantages:**
- Data loss: up to minutes of data between snapshots
- fork() can be slow with large datasets (blocks clients momentarily)
- Not suitable when you can't tolerate any data loss

## AOF (Append Only File)

AOF logs every write operation. On restart, Redis replays the log to reconstruct the dataset.

### Configuration

```conf
# Enable AOF
appendonly yes

# AOF filename
appendfilename "appendonly.aof"

# AOF directory (Redis 7.0+ uses multi-part AOF)
appenddirname "appendonlydir"

# Fsync policy
appendfsync everysec           # Recommended: fsync every second
# appendfsync always           # Fsync after every command (safest, slowest)
# appendfsync no               # Let OS decide (fastest, least safe)

# Auto-rewrite triggers
auto-aof-rewrite-percentage 100   # Rewrite when AOF is 100% larger than after last rewrite
auto-aof-rewrite-min-size 64mb    # Minimum size before triggering rewrite

# Load truncated AOF on startup (handles crash during write)
aof-load-truncated yes

# Use RDB preamble in AOF rewrites (hybrid format, faster loading)
aof-use-rdb-preamble yes
```

### Fsync Policies

| Policy | Data Loss Window | Performance | Recommendation |
|--------|-----------------|-------------|----------------|
| `always` | None (every command synced) | Slowest | Maximum safety required |
| `everysec` | ~1 second of writes | Good | **Default, recommended** |
| `no` | OS buffer (typically 30s) | Fastest | When data loss is acceptable |

### AOF Rewriting

AOF files grow over time. Rewriting compacts them by generating the minimum set of commands to recreate the current dataset.

```redis
# Manual rewrite
BGREWRITEAOF

# Check rewrite status
INFO persistence
# aof_rewrite_in_progress:0
# aof_last_rewrite_time_sec:2
# aof_last_bgrewrite_status:ok
```

### Multi-Part AOF (Redis 7.0+)

AOF files are split into:
- **Base file** — RDB or AOF format snapshot from last rewrite
- **Incremental files** — Commands since last base file
- **Manifest file** — Tracks all AOF files

```
appendonlydir/
├── appendonly.aof.1.base.rdb      # Base (RDB preamble)
├── appendonly.aof.1.incr.aof      # Incremental commands
├── appendonly.aof.2.incr.aof      # More incremental commands
└── appendonly.aof.manifest        # File manifest
```

### Advantages & Disadvantages

**Advantages:**
- Minimal data loss (1 second with `everysec`)
- Append-only — no corruption from partial writes
- Auto-rewriting compacts the file
- Human-readable format (can inspect/edit)
- Can recover from accidental FLUSHALL by editing AOF

**Disadvantages:**
- Larger files than RDB
- Slower restart (replay vs. load)
- Potential for higher write latency with `always` fsync

## Hybrid Persistence

Combine RDB and AOF for the best of both worlds:

```conf
# Enable both
save 3600 1 300 100 60 10000
appendonly yes
appendfsync everysec

# Use RDB preamble in AOF (recommended)
aof-use-rdb-preamble yes
```

**With hybrid mode:**
- AOF rewrite creates a file starting with RDB snapshot (fast load) followed by AOF commands (durability)
- Startup uses AOF (most complete data)
- RDB provides quick backup snapshots

## Choosing a Strategy

```
                 ┌─────────────────────────┐
                 │ Can you tolerate         │
                 │ any data loss?           │
                 └────────┬────────────────┘
                    ┌─────┴──────┐
                    │            │
                   Yes          No
                    │            │
            ┌───────▼──────┐  ┌─▼──────────────┐
            │ Acceptable    │  │ AOF + RDB       │
            │ loss window?  │  │ (appendfsync    │
            │               │  │  everysec)      │
            └───┬───────┬──┘  └─────────────────┘
                │       │
            Minutes   None
                │       │
         ┌──────▼──┐  ┌─▼──────────────┐
         │ RDB     │  │ AOF             │
         │ only    │  │ (appendfsync    │
         │         │  │  always)        │
         └─────────┘  └────────────────┘
```

| Scenario | Strategy |
|----------|----------|
| Pure cache (data reconstructable) | No persistence or RDB only |
| Database-like durability | RDB + AOF with `everysec` |
| Zero data loss tolerance | AOF with `appendfsync always` |
| Fast backup + disaster recovery | RDB + AOF |
| Development / testing | No persistence or RDB with relaxed saves |

## Backup Strategies

### RDB Backups

```bash
# Trigger background save
redis-cli BGSAVE

# Wait for completion
redis-cli LASTSAVE

# Copy the RDB file
cp /var/lib/redis/dump.rdb /backup/redis-$(date +%Y%m%d-%H%M).rdb

# Cron job: hourly backups, keep 48 hours
0 * * * * redis-cli BGSAVE && sleep 5 && cp /var/lib/redis/dump.rdb /backup/redis-hourly-$(date +\%H).rdb
```

### AOF Backups (Redis 7.0+)

```bash
# 1. Disable auto-rewrite temporarily
redis-cli CONFIG SET auto-aof-rewrite-percentage 0

# 2. Verify no rewrite in progress
redis-cli INFO persistence | grep aof_rewrite_in_progress
# aof_rewrite_in_progress:0

# 3. Copy the entire AOF directory
cp -r /var/lib/redis/appendonlydir /backup/aof-$(date +%Y%m%d)

# 4. Re-enable auto-rewrite
redis-cli CONFIG SET auto-aof-rewrite-percentage 100
```

### Offsite Backups

```bash
# Encrypt and upload to S3
gpg -c /backup/redis-latest.rdb
aws s3 cp /backup/redis-latest.rdb.gpg s3://my-backups/redis/

# Verify backup integrity
redis-check-rdb /backup/redis-latest.rdb
```

## Disaster Recovery

### Restore from RDB

```bash
# 1. Stop Redis
sudo systemctl stop redis

# 2. Replace dump.rdb
cp /backup/redis-latest.rdb /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb

# 3. Start Redis
sudo systemctl start redis

# 4. Verify
redis-cli DBSIZE
redis-cli INFO keyspace
```

### Restore from AOF

```bash
# 1. Stop Redis
sudo systemctl stop redis

# 2. Replace AOF directory (Redis 7.0+)
rm -rf /var/lib/redis/appendonlydir
cp -r /backup/aof-latest /var/lib/redis/appendonlydir
chown -R redis:redis /var/lib/redis/appendonlydir

# 3. Start Redis
sudo systemctl start redis
```

### Fix Corrupted AOF

```bash
# Check AOF integrity
redis-check-aof /var/lib/redis/appendonlydir/appendonly.aof.1.incr.aof

# Fix truncated AOF (removes incomplete last command)
redis-check-aof --fix /var/lib/redis/appendonlydir/appendonly.aof.1.incr.aof

# Fix corrupted RDB
redis-check-rdb /var/lib/redis/dump.rdb
```

### Enable AOF on Running Instance

```redis
# Switch from RDB-only to AOF without restart
CONFIG SET appendonly yes

# Wait for AOF rewrite to complete
INFO persistence
# aof_rewrite_in_progress:0
# aof_last_bgrewrite_status:ok

# Persist the change
CONFIG REWRITE
```

## Common Pitfalls

1. **No persistence configured** — Default `save` rules may not match your needs. Be explicit.
2. **fork() memory pressure** — RDB/AOF rewrite forks the process, temporarily doubling memory usage. Set `maxmemory` to leave headroom.
3. **Disabling persistence on master with replicas** — If master restarts with empty dataset, replicas wipe their data too. Always enable persistence on masters.
4. **Not monitoring persistence** — Watch `rdb_last_bgsave_status`, `aof_last_bgrewrite_status`, and `rdb_last_save_time` in INFO.
5. **Backups on same disk** — If the disk fails, both Redis data and backups are lost. Always ship backups offsite.
6. **AOF rewrite during peak traffic** — Can cause latency spikes. Schedule BGREWRITEAOF during low-traffic periods if possible.

## Related

- `00-overview.md` — Redis architecture and configuration basics
- `10-replication-sentinel.md` — Replication uses RDB for initial sync
- `11-cluster.md` — Persistence in cluster deployments
