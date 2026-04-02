# Qdrant — Snapshots & Backups

> Source: [qdrant.tech/documentation/concepts/snapshots](https://qdrant.tech/documentation/concepts/snapshots/) | v1.17.1

## Overview

Snapshots are tar archives containing a collection's data and configuration at a specific point in time. They enable backup, restore, and migration workflows.

**Key facts:**
- Snapshots capture a single collection on a single node
- Full storage snapshots capture all collections + aliases (single-node only)
- Version compatibility: restore only to matching minor versions (v1.17.x → v1.17.x)
- In distributed deployments, create snapshots per node separately

## Creating Snapshots

### Collection Snapshot

```python
from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)

snapshot_info = client.create_snapshot(collection_name="my_collection")
print(f"Snapshot: {snapshot_info.name}")
print(f"Size: {snapshot_info.size}")
```

**REST:**
```http
POST /collections/my_collection/snapshots
```

### Full Storage Snapshot (All Collections)

```python
snapshot_info = client.create_full_snapshot()
print(f"Snapshot: {snapshot_info.name}")
```

**REST:**
```http
POST /snapshots
```

**Note:** Full storage snapshots work only on single-node deployments. They include all collections and aliases.

## Listing Snapshots

```python
# Collection snapshots
snapshots = client.list_snapshots(collection_name="my_collection")
for s in snapshots:
    print(f"{s.name} — {s.size} bytes — {s.creation_time}")

# Full storage snapshots
snapshots = client.list_full_snapshots()
for s in snapshots:
    print(f"{s.name} — {s.size} bytes")
```

## Downloading Snapshots

**REST (direct download):**
```http
GET /collections/my_collection/snapshots/{snapshot_name}
```

```bash
curl -o backup.snapshot \
  "http://localhost:6333/collections/my_collection/snapshots/my_collection-2024-01-15.snapshot"
```

## Deleting Snapshots

```python
client.delete_snapshot(
    collection_name="my_collection",
    snapshot_name="my_collection-2024-01-15.snapshot",
)

# Full storage snapshot
client.delete_full_snapshot(
    snapshot_name="full-snapshot-2024-01-15.snapshot",
)
```

## Restoring from Snapshots

### Recover from URL

```python
client.recover_snapshot(
    collection_name="my_collection",
    location="http://backup-server:6333/collections/my_collection/snapshots/backup.snapshot",
    priority=models.SnapshotPriority.SNAPSHOT,
)
```

### Upload Snapshot File

**REST:**
```http
POST /collections/my_collection/snapshots/upload?priority=snapshot
Content-Type: multipart/form-data

[binary snapshot file]
```

```bash
curl -X POST \
  "http://localhost:6333/collections/my_collection/snapshots/upload?priority=snapshot" \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@backup.snapshot"
```

### Recovery Priority

| Priority | Behavior |
|----------|----------|
| `replica` (default) | Preserve existing data, use snapshot as fallback |
| `snapshot` | Overwrite current data with snapshot data |
| `no_sync` | Skip replica synchronization (manual resolution) |

**Use `snapshot` priority** when restoring a backup — it ensures the snapshot data replaces any existing state.

## CLI Startup Recovery

Restore from snapshot when starting Qdrant:

```bash
# Restore single collection
./qdrant --snapshot /snapshots/my_collection.snapshot:my_collection

# Restore full storage
./qdrant --storage-snapshot /snapshots/full-snapshot.snapshot
```

**Format:** `--snapshot <path>:<collection_name>`

## S3 Storage (v1.10.0+)

Configure snapshot storage to S3 via Qdrant configuration:

```yaml
# config.yaml
storage:
  snapshots_config:
    s3_config:
      bucket: "my-qdrant-backups"
      region: "us-east-1"
      access_key: "${AWS_ACCESS_KEY_ID}"
      secret_key: "${AWS_SECRET_ACCESS_KEY}"
      # endpoint_url: "https://s3.custom.endpoint"  # for S3-compatible storage
```

With S3 configured, snapshot operations automatically use S3 as the storage backend.

## Backup Strategy

### Automated Backup Script

```python
import datetime
from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)

def backup_collection(collection_name: str, retain_count: int = 5):
    """Create snapshot and clean up old ones."""
    # Create new snapshot
    snapshot = client.create_snapshot(collection_name=collection_name)
    print(f"Created: {snapshot.name}")

    # Clean up old snapshots (keep last N)
    snapshots = client.list_snapshots(collection_name=collection_name)
    snapshots_sorted = sorted(snapshots, key=lambda s: s.creation_time, reverse=True)

    for old_snapshot in snapshots_sorted[retain_count:]:
        client.delete_snapshot(
            collection_name=collection_name,
            snapshot_name=old_snapshot.name,
        )
        print(f"Deleted old: {old_snapshot.name}")

# Backup all collections
collections = client.get_collections()
for collection in collections.collections:
    backup_collection(collection.name)
```

## Common Pitfalls

1. **Version mismatch** — Snapshots only restore to the same minor version. v1.16 snapshots won't restore to v1.17.
2. **Distributed snapshots** — In multi-node clusters, snapshots capture a single node. You must snapshot each node separately.
3. **No aliases in collection snapshots** — Collection snapshots don't include aliases. Recreate aliases after restoring.
4. **Large snapshot size** — Snapshots include full vector data. For 1M × 768-dim vectors, expect ~3GB+ snapshot files.
5. **Qdrant Cloud** — Cloud users should use the built-in Backup feature instead of snapshots.
6. **Concurrent writes** — Creating a snapshot during heavy writes is safe (copy-on-write), but the snapshot reflects a consistent point-in-time state.

## Related Topics

- Collections → `references/01-collections.md`
- Deployment → `references/12-deployment.md`
- Optimizer → `references/09-optimizer.md`
