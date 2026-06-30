# Prometheus — Storage

> Source: [prometheus.io/docs/prometheus/latest/storage](https://prometheus.io/docs/prometheus/latest/storage/)

## Table of Contents

- [Local TSDB](#local-tsdb)
- [On-Disk Layout](#on-disk-layout)
- [Write-Ahead Log (WAL)](#write-ahead-log-wal)
- [Compaction](#compaction)
- [Retention](#retention)
- [Capacity Planning](#capacity-planning)
- [Remote Storage](#remote-storage)
- [Backfilling](#backfilling)
- [Operational Best Practices](#operational-best-practices)

## Local TSDB

Prometheus uses a custom, highly efficient on-disk time series database (TSDB). Key characteristics:

- Designed for append-heavy workloads with recent-data queries
- Average of **1–2 bytes per sample** (highly compressed)
- Single-node, no distributed storage
- Optimized for SSD storage
- Not POSIX-filesystem dependent features but requires POSIX-compliant filesystem

## On-Disk Layout

```
data/
├── 01BKGV7JBM69T2G1BGBGM6KB12/   # Two-hour block
│   ├── chunks/
│   │   └── 000001                  # Chunk segment (max 512MB)
│   ├── tombstones                  # Deletion markers
│   ├── index                       # Inverted index for series lookup
│   └── meta.json                   # Block metadata
├── 01BKGTZQ1SYQJTR4PB43C8PD98/   # Another block
│   └── ...
├── chunks_head/                    # In-memory head block overflow
│   └── 000001
├── wal/                            # Write-ahead log
│   ├── 00000001                    # WAL segment (128MB each)
│   ├── 00000002
│   └── checkpoint.00000000/        # WAL checkpoint
└── lock                            # File lock
```

### Blocks

- Ingested samples are grouped into **two-hour blocks**
- Each block is a self-contained directory with chunks, index, and metadata
- Blocks are immutable once written — only the head block is mutable
- The `meta.json` file contains block time range, compaction level, and stats

### Chunks

- Time series data is stored in chunk segments within each block
- Each segment is limited to **512 MB** by default
- Chunks use various compression algorithms (XOR encoding for floats, delta encoding for timestamps)

## Write-Ahead Log (WAL)

The WAL protects against data loss during crashes:

- Located in the `wal/` directory
- Segments are **128 MB** each
- Minimum 3 WAL files are retained
- On restart, the WAL is replayed to recover in-memory data
- WAL compression reduces size by ~50% with `--storage.tsdb.wal-compression`

```bash
# Enable WAL compression
prometheus --storage.tsdb.wal-compression

# Memory snapshot on shutdown (faster restart)
prometheus --enable-feature=memory-snapshot-on-shutdown
```

## Compaction

Background compaction merges smaller blocks into larger ones:

- Two-hour blocks are progressively merged
- Maximum block size: **10% of retention time or 31 days** (whichever is smaller)
- Compaction improves query performance and reduces disk usage
- Tombstones (deletion markers) are applied during compaction

```
Block Timeline:
[0h-2h] [2h-4h] [4h-6h] [6h-8h]
    └──────┘         └──────┘
     [0h-4h]          [4h-8h]
        └─────────────────┘
              [0h-8h]
```

## Retention

Two retention mechanisms — time-based and size-based. When both are set, whichever triggers first causes data removal.

### Time-Based Retention

```bash
# Keep data for 30 days (default: 15d)
prometheus --storage.tsdb.retention.time=30d
```

### Size-Based Retention

```bash
# Keep up to 50GB of data
prometheus --storage.tsdb.retention.size=50GB
```

When the size limit is reached, the oldest blocks are removed first. The oldest block's `minTime` is used as the effective time-based retention limit.

### Important Notes

- Retention size should not exceed **80–85%** of allocated disk space
- Minimum retention is the duration of the head block (2 hours) plus any WAL data
- Blocks are removed as whole units — you can't remove individual series

## Capacity Planning

### Storage Formula

```
needed_disk_space = retention_time_seconds × ingested_samples_per_second × bytes_per_sample
```

With an average of **1–2 bytes per sample**:

| Active Series | Scrape Interval | Samples/s | Daily Storage | 30-Day Storage |
|---------------|-----------------|-----------|---------------|----------------|
| 10,000 | 15s | 667 | ~57 MB | ~1.7 GB |
| 100,000 | 15s | 6,667 | ~576 MB | ~17 GB |
| 1,000,000 | 15s | 66,667 | ~5.7 GB | ~170 GB |
| 10,000,000 | 15s | 666,667 | ~57 GB | ~1.7 TB |

### Monitoring TSDB Health

```promql
# Total number of active time series
prometheus_tsdb_head_series

# Samples appended per second
rate(prometheus_tsdb_head_samples_appended_total[5m])

# Current storage size
prometheus_tsdb_storage_blocks_bytes

# Number of blocks
prometheus_tsdb_blocks_loaded

# WAL size
prometheus_tsdb_wal_storage_size_bytes

# Compaction duration
prometheus_tsdb_compaction_duration_seconds

# Head chunks memory
prometheus_tsdb_head_chunks_storage_size_bytes

# Out-of-order samples (indicates issues)
rate(prometheus_tsdb_out_of_order_samples_total[5m])
```

## Remote Storage

Prometheus supports sending and receiving data to/from external storage systems for long-term retention and global querying.

### Remote Write

Send ingested samples to a remote endpoint:

```yaml
remote_write:
  - url: "http://mimir:9009/api/v1/push"
    # Queue configuration for batching
    queue_config:
      capacity: 10000
      max_shards: 30
      max_samples_per_send: 5000
      batch_send_deadline: 5s
      min_backoff: 30ms
      max_backoff: 5s

    # Filter what gets sent
    write_relabel_configs:
      # Only send specific metrics
      - source_labels: [__name__]
        regex: "http_.*|node_.*|container_.*"
        action: keep

      # Drop high-cardinality labels
      - regex: "pod_template_hash"
        action: labeldrop
```

### Remote Read

Query historical data from external storage:

```yaml
remote_read:
  - url: "http://mimir:9009/api/v1/read"
    read_recent: true    # Also read recent data (not just beyond local retention)
```

### Compatible Remote Storage Systems

| System | Type | Use Case |
|--------|------|----------|
| **Thanos** | Sidecar + object storage | Multi-cluster, long-term, HA |
| **Cortex / Mimir** | Horizontally scalable | Multi-tenant, SaaS |
| **VictoriaMetrics** | Drop-in replacement | High cardinality, compression |
| **InfluxDB** | Time series DB | Existing InfluxDB infrastructure |
| **M3** | Distributed TSDB | Very large scale |
| **Grafana Cloud** | Managed service | No ops overhead |

## Backfilling

Import historical data into Prometheus TSDB.

### From OpenMetrics Format

```bash
# Create TSDB blocks from OpenMetrics data
promtool tsdb create-blocks-from openmetrics input.txt ./data/

# With custom block duration
promtool tsdb create-blocks-from openmetrics --max-block-duration=2h input.txt
```

**Constraint:** Do not backfill data from the last 3 hours — it may overlap with the active head block.

### From Recording Rules

```bash
# Generate historical recording rule data
promtool tsdb create-blocks-from rules \
  --start 2026-01-01T00:00:00Z \
  --end 2026-06-01T00:00:00Z \
  --url http://localhost:9090 \
  rules.yml
```

**Limitations:**
- No cross-rule references
- Alerting rules are excluded
- Repeated runs create duplicate blocks

## Operational Best Practices

### Backup

```bash
# Create a snapshot (requires --web.enable-admin-api)
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Snapshot location: data/snapshots/<snapshot-name>/

# Alternative: copy the data directory (exclude wal/ and chunks_head/)
rsync -av --exclude='wal' --exclude='chunks_head' data/ backup/
```

### Filesystem Requirements

| Requirement | Detail |
|-------------|--------|
| POSIX-compliant | Required — ext4, XFS recommended |
| NFS | **Not supported** — corruption risk (including AWS EFS) |
| Network filesystems | Generally not recommended |
| SSD | Strongly recommended for production |

### Key Flags

```bash
prometheus \
  --storage.tsdb.path=/data/prometheus \
  --storage.tsdb.retention.time=30d \
  --storage.tsdb.retention.size=100GB \
  --storage.tsdb.wal-compression \
  --storage.tsdb.min-block-duration=2h \
  --storage.tsdb.max-block-duration=36h \
  --enable-feature=memory-snapshot-on-shutdown
```

## Common Pitfalls

| Pitfall | Impact | Fix |
|---------|--------|-----|
| NFS / EFS storage | Data corruption | Use local SSD or block storage |
| No size-based retention | Disk fills up | Set `--storage.tsdb.retention.size` |
| Retention > disk capacity | OOM or disk full | Size to 80-85% of available disk |
| Missing WAL compression | 2× WAL disk usage | Enable `--storage.tsdb.wal-compression` |
| Backfilling into head block range | Data conflicts | Only backfill data > 3 hours old |
| No TSDB monitoring | Blind to storage issues | Monitor `prometheus_tsdb_*` metrics |

## Related Topics

- Configuration for remote write/read → `03-configuration.md`
- Capacity planning for targets → `12-deployment.md`
- TSDB monitoring metrics → `10-instrumentation.md`
