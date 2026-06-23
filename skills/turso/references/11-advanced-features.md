# Turso Advanced Features

> Source: [docs.turso.tech/tursodb](https://docs.turso.tech/tursodb/cdc) | [docs.turso.tech/features](https://docs.turso.tech/features/branching)

## Table of Contents
- [Change Data Capture (CDC)](#change-data-capture-cdc)
- [Concurrent Writes (MVCC)](#concurrent-writes-mvcc)
- [Database Branching](#database-branching)
- [Point-in-Time Recovery](#point-in-time-recovery)
- [SQLite Extensions](#sqlite-extensions)
- [Common Pitfalls](#common-pitfalls)

## Change Data Capture (CDC)

CDC tracks all modifications (inserts, updates, deletes) to database tables. Changes are recorded in a dedicated tracking table that you can query.

### Enable CDC

```sql
-- Enable per connection with full capture
PRAGMA capture_data_changes_conn('full');

-- Disable CDC
PRAGMA capture_data_changes_conn('off');
```

### Capture Modes

| Mode | Records |
|------|---------|
| `id` | Only the primary key of modified rows |
| `before` | Row state before updates/deletes |
| `after` | Row state after inserts/updates |
| `full` | Both before and after states, plus per-column change details |

### Custom CDC Table

```sql
-- Use a custom table name instead of default 'turso_cdc'
PRAGMA capture_data_changes_conn('full,my_audit_log');
```

### CDC Table Structure

The `turso_cdc` table contains:

| Column | Type | Description |
|--------|------|-------------|
| `change_id` | INTEGER | Auto-incrementing unique identifier |
| `change_time` | INTEGER | Unix epoch timestamp |
| `change_txn_id` | INTEGER | Groups related changes in a transaction |
| `change_type` | INTEGER | 1 = INSERT, 0 = UPDATE, -1 = DELETE, 2 = COMMIT |
| `table_name` | TEXT | Affected table name |
| `before` | BLOB | Binary-encoded row before change |
| `after` | BLOB | Binary-encoded row after change |
| `updates` | BLOB | Column-level change details (full mode) |

### Querying Changes

```sql
-- All inserts
SELECT * FROM turso_cdc WHERE change_type = 1;

-- Changes to a specific table
SELECT * FROM turso_cdc WHERE table_name = 'users';

-- Decode binary data to JSON
SELECT
    change_type,
    table_name,
    bin_record_json_object(
        table_columns_json_array('users'),
        after
    ) AS after_state
FROM turso_cdc
WHERE table_name = 'users' AND change_type = 1;
```

### CDC Use Cases

```sql
-- Audit trail: who changed what
SELECT
    change_time,
    CASE change_type
        WHEN 1 THEN 'INSERT'
        WHEN 0 THEN 'UPDATE'
        WHEN -1 THEN 'DELETE'
    END AS operation,
    table_name,
    bin_record_json_object(table_columns_json_array(table_name), after) AS data
FROM turso_cdc
ORDER BY change_id DESC
LIMIT 50;

-- Replication trigger
SELECT * FROM turso_cdc
WHERE change_id > ?  -- Last processed ID
ORDER BY change_id ASC;
```

### CDC + Schema Changes

DDL operations (CREATE TABLE, DROP TABLE, CREATE INDEX) are recorded as modifications to the `sqlite_schema` table.

### CDC Limitations

- **CDC and MVCC are mutually exclusive** on the same connection
- Each connection maintains independent CDC configuration
- Binary `before`/`after` fields require helper functions to decode
- Rolled-back transactions produce no CDC entries

## Concurrent Writes (MVCC)

By default, Turso allows only one writer at a time. MVCC (Multi-Version Concurrency Control) enables multiple simultaneous writers.

### Enable MVCC

```sql
PRAGMA journal_mode = 'mvcc';
```

### BEGIN CONCURRENT

```sql
BEGIN CONCURRENT;
INSERT INTO counters (name, value) VALUES ('page_views', 1);
COMMIT;
```

Multiple connections can run `BEGIN CONCURRENT` transactions in parallel, as long as they modify non-overlapping data.

### Conflict Handling

When two transactions modify the same rows, one receives a conflict error:

```typescript
async function withRetry(db: Database, fn: () => Promise<void>, maxRetries = 5) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      await db.execute("BEGIN CONCURRENT");
      await fn();
      await db.execute("COMMIT");
      return;
    } catch (error) {
      await db.execute("ROLLBACK");
      if (isRetryable(error) && attempt < maxRetries - 1) {
        await new Promise((r) => setTimeout(r, Math.random() * 100 * (attempt + 1)));
        continue;
      }
      throw error;
    }
  }
}

function isRetryable(error: unknown): boolean {
  const msg = String(error);
  return msg.includes("conflict") || msg.includes("busy") || msg.includes("SQLITE_BUSY");
}
```

### Python Concurrent Writes

```python
import turso
import time
import random

def concurrent_insert(db_path: str, data: str, max_retries: int = 5):
    db = turso.connect(db_path)
    db.execute("PRAGMA journal_mode = 'mvcc'")

    for attempt in range(max_retries):
        try:
            db.execute("BEGIN CONCURRENT")
            db.execute("INSERT INTO events (data) VALUES (?)", (data,))
            db.commit()
            return
        except Exception as e:
            db.rollback()
            if "busy" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(random.random() * 0.1 * (attempt + 1))
                continue
            raise
```

### MVCC Limitations

- Cannot be used with CDC on the same connection
- Only benefits from concurrent writes to non-overlapping rows
- Conflicting writes require application-level retry logic
- Currently experimental

## Database Branching

Create isolated database copies for development and testing.

### Create a Branch

```bash
# CLI
turso db create staging-branch --from-db production

# API
curl -X POST "https://api.turso.tech/v1/organizations/{org}/databases" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "staging-branch",
    "group": "default",
    "seed": { "type": "database", "name": "production" }
  }'
```

### Branch from Point-in-Time

```bash
# Branch from a specific timestamp
turso db create recovery-branch --from-db production --timestamp "2026-06-15T12:00:00Z"
```

### Development Workflow

```bash
# 1. Create branch
turso db create feature-auth --from-db production

# 2. Get connection info
turso db show feature-auth --url
turso db tokens create feature-auth

# 3. Run migrations on branch
# ... apply schema changes ...

# 4. Test thoroughly

# 5. Apply migrations to production
# ... run same migrations on production ...

# 6. Clean up
turso db destroy feature-auth
```

### CI/CD Integration

```yaml
# GitHub Actions: create branch per PR
- name: Create preview database
  run: |
    DB_NAME="pr-${{ github.event.pull_request.number }}"
    turso db create "$DB_NAME" --from-db production
    echo "PREVIEW_DB_URL=$(turso db show $DB_NAME --url)" >> $GITHUB_ENV

# Cleanup on PR close
- name: Destroy preview database
  if: github.event.action == 'closed'
  run: turso db destroy "pr-${{ github.event.pull_request.number }}"
```

### Branching Limitations

- Branches are fully independent — no automatic merge back
- Schema changes must be applied manually to both branch and production
- Branches consume quota under your plan
- Group tokens work across branches in the same group

## Point-in-Time Recovery

Restore databases to a specific moment in time.

```bash
# Restore to a specific timestamp
turso db create recovered --from-db production --timestamp "2026-06-20T08:30:00Z"
```

Point-in-time recovery creates a new database from the source at the specified timestamp. The original database is unaffected.

## SQLite Extensions

Turso supports loading SQLite extensions:

```bash
# Enable extensions when creating a group
turso group create my-group --location iad --extensions all
```

### Available Extensions

- **math** — Advanced math functions
- **stats** — Statistical functions
- **text** — Additional text processing
- **crypto** — Cryptographic hash functions
- **regexp** — Regular expression support
- **uuid** — UUID generation
- **vector** — Built-in (no extension needed)
- **fts** — Built-in Tantivy FTS (no extension needed)

### Using Extensions in SQL

```sql
-- UUID generation (with uuid extension)
SELECT uuid();

-- Regex matching (with regexp extension)
SELECT * FROM users WHERE name REGEXP '^A.*';

-- Crypto hash (with crypto extension)
SELECT sha256('hello world');
```

## Common Pitfalls

1. **CDC + MVCC conflict** — Cannot enable both on the same connection. Choose one per use case
2. **MVCC retry logic required** — Applications must handle `SQLITE_BUSY` errors and retry conflicting transactions
3. **Branch isolation** — Branches don't auto-sync. Changes in a branch are not reflected in the source database
4. **CDC binary decoding** — `before`/`after` columns are binary. Use `bin_record_json_object()` and `table_columns_json_array()` to decode
5. **Extension availability** — Extensions must be enabled at the group level during creation. Not all extensions are available on all plans
6. **PITR window** — Point-in-time recovery has a retention window that depends on your plan. Check your plan's limits
