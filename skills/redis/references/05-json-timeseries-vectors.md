# Redis — JSON, TimeSeries & Vector Sets

> Source: [redis.io/docs/data-types](https://redis.io/docs/latest/develop/data-types/) — Redis 8.6

## Table of Contents

- [JSON Overview](#json-overview)
- [JSON Commands](#json-commands)
- [JSON Patterns](#json-patterns)
- [TimeSeries Overview](#timeseries-overview)
- [TimeSeries Commands](#timeseries-commands)
- [TimeSeries Patterns](#timeseries-patterns)
- [Vector Sets Overview](#vector-sets-overview)
- [Vector Set Commands](#vector-set-commands)
- [Vector Patterns](#vector-patterns)
- [Probabilistic Data Types](#probabilistic-data-types)
- [Common Pitfalls](#common-pitfalls)

## JSON Overview

Redis JSON provides native JSON document storage with support for nested objects, arrays, and partial updates using JSONPath. In Redis 8+, JSON is built-in — no separate module required.

## JSON Commands

### Set & Get

```redis
# Set full document
JSON.SET user:1001 $ '{"name":"Alice","age":30,"address":{"city":"NYC","zip":"10001"},"tags":["admin","premium"]}'

# Get full document
JSON.GET user:1001
JSON.GET user:1001 $                           # With JSONPath

# Get nested field
JSON.GET user:1001 $.name                      # '"Alice"'
JSON.GET user:1001 $.address.city              # '"NYC"'

# Get multiple paths
JSON.GET user:1001 $.name $.age $.address.city

# Get with formatting
JSON.GET user:1001 INDENT "\t" NEWLINE "\n" SPACE " "

# Get from multiple keys
JSON.MGET user:1001 user:1002 $.name
```

### Update

```redis
# Update nested field
JSON.SET user:1001 $.age 31
JSON.SET user:1001 $.address.city '"San Francisco"'

# Set new nested field
JSON.SET user:1001 $.address.state '"CA"'

# Set only if path does NOT exist
JSON.SET user:1001 $.phone '"+1-555-0123"' NX

# Set only if path EXISTS
JSON.SET user:1001 $.age 32 XX
```

### Numeric Operations

```redis
JSON.SET stats:page $ '{"views":0,"clicks":0,"bounce_rate":0.45}'

JSON.NUMINCRBY stats:page $.views 1            # Increment
JSON.NUMINCRBY stats:page $.clicks 5
JSON.NUMMULTBY stats:page $.bounce_rate 0.9    # Multiply
```

### Array Operations

```redis
JSON.SET user:1001 $.tags '["admin"]'

# Append to array
JSON.ARRAPPEND user:1001 $.tags '"premium"' '"beta"'

# Insert at index
JSON.ARRINSERT user:1001 $.tags 0 '"superadmin"'

# Get array length
JSON.ARRLEN user:1001 $.tags                   # 4

# Find element index
JSON.ARRINDEX user:1001 $.tags '"admin"'       # 1

# Pop element
JSON.ARRPOP user:1001 $.tags                   # Last element
JSON.ARRPOP user:1001 $.tags 0                 # First element

# Trim array
JSON.ARRTRIM user:1001 $.tags 0 2              # Keep first 3
```

### String Operations

```redis
JSON.STRLEN user:1001 $.name                   # String length
JSON.STRAPPEND user:1001 $.name '" Johnson"'   # Append to string
```

### Delete & Type

```redis
JSON.DEL user:1001 $.address.zip               # Delete field
JSON.CLEAR user:1001 $.tags                    # Clear to empty ([] or 0)
JSON.TYPE user:1001 $.name                     # "string"
JSON.TYPE user:1001 $.tags                     # "array"
```

## JSON Patterns

### Document Storage

```redis
# Product catalog
JSON.SET product:5001 $ '{
  "name": "Wireless Mouse",
  "price": 29.99,
  "category": "electronics",
  "specs": {"dpi": 1600, "connectivity": "bluetooth", "battery": "AA"},
  "reviews": [],
  "stock": 150
}'

# Add review
JSON.ARRAPPEND product:5001 $.reviews '{"user":"alice","rating":5,"text":"Great mouse!"}'

# Update stock
JSON.NUMINCRBY product:5001 $.stock -1

# Get product summary
JSON.GET product:5001 $.name $.price $.stock
```

### Nested Configuration

```redis
JSON.SET config:app $ '{
  "database": {"host": "localhost", "port": 5432, "pool_size": 10},
  "cache": {"ttl": 3600, "max_size": "256mb"},
  "features": {"dark_mode": true, "beta_ui": false}
}'

# Toggle feature flag
JSON.SET config:app $.features.beta_ui true
```

## TimeSeries Overview

Redis TimeSeries provides native support for timestamped data points, including automatic downsampling, aggregation, and retention policies. Built-in to Redis 8+.

## TimeSeries Commands

### Create & Add

```redis
# Create time series with labels
TS.CREATE sensor:temp:room1 \
  RETENTION 86400000 \
  LABELS location "room1" type "temperature" unit "celsius"

# Add data point (timestamp, value)
TS.ADD sensor:temp:room1 * 23.5          # * = current timestamp
TS.ADD sensor:temp:room1 1719014400000 23.5

# Add to non-existing key (auto-create)
TS.ADD sensor:humidity:room1 * 45.2 \
  RETENTION 86400000 \
  LABELS location "room1" type "humidity"

# Add multiple samples
TS.MADD sensor:temp:room1 * 23.5 sensor:temp:room2 * 22.1 sensor:humidity:room1 * 45.2
```

### Query

```redis
# Get latest value
TS.GET sensor:temp:room1

# Range query
TS.RANGE sensor:temp:room1 1719014400000 1719100800000

# Last 1 hour
TS.RANGE sensor:temp:room1 - + COUNT 100

# Reverse range (newest first)
TS.REVRANGE sensor:temp:room1 - +

# Aggregation (downsample)
TS.RANGE sensor:temp:room1 - + AGGREGATION avg 3600000
# Average per hour (3600000ms)

# Available aggregations: avg, sum, min, max, range, count, first, last, std.p, std.s, var.p, var.s
```

### Downsampling Rules

```redis
# Create compacted series
TS.CREATE sensor:temp:room1:hourly RETENTION 2592000000    # 30 days
TS.CREATE sensor:temp:room1:daily RETENTION 31536000000    # 1 year

# Create automatic downsampling rules
TS.CREATERULE sensor:temp:room1 sensor:temp:room1:hourly AGGREGATION avg 3600000
TS.CREATERULE sensor:temp:room1 sensor:temp:room1:daily AGGREGATION avg 86400000
```

### Multi-Key Queries

```redis
# Query by labels across multiple keys
TS.MRANGE - + FILTER type=temperature location=room1
TS.MRANGE - + AGGREGATION avg 3600000 FILTER type=temperature
TS.MREVRANGE - + FILTER location=room1

# Get latest from multiple series
TS.MGET FILTER type=temperature
```

## TimeSeries Patterns

### IoT Sensor Monitoring

```redis
TS.CREATE sensor:temp RETENTION 604800000 LABELS device "sensor-1"
TS.ADD sensor:temp * 23.5
TS.RANGE sensor:temp - + AGGREGATION avg 60000    # 1-minute averages
```

### Application Metrics

```redis
TS.ADD api:latency:p99 * 45.2 LABELS endpoint "/api/users" method "GET"
TS.ADD api:requests * 1 LABELS endpoint "/api/users"
TS.RANGE api:latency:p99 - + AGGREGATION max 60000
```

## Vector Sets Overview

Vector sets store high-dimensional vectors with fast approximate nearest-neighbor search using HNSW (Hierarchical Navigable Small World) algorithm. Ideal for AI/ML embeddings, semantic search, and recommendation systems.

## Vector Set Commands

```redis
# Add vector with element name
VADD embeddings VALUES 3 0.1 0.2 0.3 "doc:1001"
VADD embeddings VALUES 3 0.4 0.5 0.6 "doc:1002"
VADD embeddings VALUES 3 0.15 0.25 0.35 "doc:1003"

# Search for nearest neighbors
VSIM embeddings VALUES 3 0.12 0.22 0.32 COUNT 5
# Returns: ["doc:1001", "doc:1003", "doc:1002"] (ordered by similarity)

# Search with element as query
VSIM embeddings ELE "doc:1001" COUNT 5

# Get vector dimension info
VCARD embeddings                              # Number of vectors
VDIM embeddings                               # Dimensionality
VRANDMEMBER embeddings 3                      # Random members

# Delete vector
VREM embeddings "doc:1001"

# Check if element exists
VISMEMBER embeddings "doc:1001"

# Get element info
VEMB embeddings "doc:1001"                    # Get stored vector
```

## Vector Patterns

### Semantic Search

```python
import redis
import numpy as np

r = redis.Redis()

# Store embeddings from an LLM
embedding = get_embedding("How to use Redis caching")  # [0.1, 0.2, ...]
r.execute_command("VADD", "docs", "VALUES", len(embedding), *embedding, "doc:redis-caching")

# Search
query_vec = get_embedding("caching best practices")
results = r.execute_command("VSIM", "docs", "VALUES", len(query_vec), *query_vec, "COUNT", 5)
```

### RAG Pipeline

```redis
# Store document chunks with embeddings
VADD knowledge_base VALUES 1536 <...1536 floats...> "chunk:doc1:p1"
VADD knowledge_base VALUES 1536 <...1536 floats...> "chunk:doc1:p2"

# Retrieve relevant chunks
VSIM knowledge_base VALUES 1536 <...query embedding...> COUNT 5
# Use retrieved chunks as context for LLM
```

## Probabilistic Data Types

### HyperLogLog — Cardinality Estimation

```redis
# Count unique visitors (uses only 12KB per key regardless of count)
PFADD visitors:2026-06-22 "user:1001" "user:1002" "user:1003"
PFADD visitors:2026-06-22 "user:1001"              # Duplicate, not counted

PFCOUNT visitors:2026-06-22                          # ~3 (approximate)

# Merge multiple HyperLogLogs
PFMERGE visitors:week visitors:2026-06-22 visitors:2026-06-21 visitors:2026-06-20
PFCOUNT visitors:week                                # Unique visitors across all days
```

### Bloom Filter

```redis
# Create bloom filter
BF.RESERVE usernames 0.001 1000000                   # 0.1% error rate, 1M capacity

# Add elements
BF.ADD usernames "alice"
BF.MADD usernames "bob" "charlie" "diana"

# Check membership (may have false positives, never false negatives)
BF.EXISTS usernames "alice"                           # 1 (definitely or probably exists)
BF.EXISTS usernames "unknown"                         # 0 (definitely does NOT exist)
BF.MEXISTS usernames "alice" "unknown"                # [1, 0]
```

### Geospatial

```redis
# Add locations (longitude, latitude, member)
GEOADD stores -73.935242 40.730610 "store:nyc"
GEOADD stores -118.243685 34.052234 "store:la"
GEOADD stores -87.629798 41.878113 "store:chicago"

# Distance between locations
GEODIST stores "store:nyc" "store:la" km              # ~3940 km

# Find stores within radius
GEOSEARCH stores FROMLONLAT -73.9 40.7 BYRADIUS 100 km ASC COUNT 5
GEOSEARCH stores FROMMEMBER "store:nyc" BYRADIUS 500 km ASC

# Get coordinates
GEOPOS stores "store:nyc"                             # [lng, lat]
```

## Common Pitfalls

1. **JSON.GET without JSONPath** — Returns entire document. Use specific paths for large documents.
2. **TimeSeries without RETENTION** — Data accumulates forever. Always set retention policies.
3. **Vector dimension mismatch** — All vectors in a set must have the same dimensionality.
4. **HyperLogLog precision** — Estimates have ~0.81% standard error. Don't use for exact counts.
5. **Bloom filter false positives** — Design error rate and capacity before inserting data. Cannot remove elements (use Cuckoo filter instead).

## Related

- `01-strings.md` — Simple key-value storage
- `10-replication-sentinel.md` — Replicating JSON and TimeSeries data
- `12-client-libraries.md` — Client support for these data types
