# Milvus — Hybrid Search

> Source: [milvus.io/docs/multi-vector-search.md](https://milvus.io/docs/multi-vector-search.md) | Version: 3.0-beta

## Overview

Hybrid search in Milvus combines results from multiple vector fields (or multiple search strategies) into a single ranked list. This enables powerful retrieval patterns like sparse+dense fusion, multi-modal search (text + image), and ensemble methods that outperform any single vector approach.

## Architecture

```
┌──────────────────────────────────────────────┐
│              Hybrid Search Pipeline          │
├──────────┬──────────┬───────────────────────┤
│  Dense   │  Sparse  │  Image Embedding      │
│  Search  │  Search  │  Search               │
│  (COSINE)│  (BM25)  │  (IP)                 │
├──────────┴──────────┴───────────────────────┤
│              Reranker                        │
│   RRF / Weighted / Model-based              │
├─────────────────────────────────────────────┤
│              Merged Top-K Results            │
└─────────────────────────────────────────────┘
```

## Setting Up Multi-Vector Collections

### Schema with Multiple Vector Fields

```python
from pymilvus import MilvusClient, DataType, Function, FunctionType

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")
schema = client.create_schema()

schema.add_field("id", DataType.INT64, is_primary=True, auto_id=True)

# Dense text embedding
schema.add_field("text_dense", DataType.FLOAT_VECTOR, dim=768)

# Sparse text embedding (BM25)
schema.add_field("text", DataType.VARCHAR, max_length=5000, enable_analyzer=True)
schema.add_field("text_sparse", DataType.SPARSE_FLOAT_VECTOR)

# Image embedding
schema.add_field("image_dense", DataType.FLOAT_VECTOR, dim=512)

# Scalar metadata
schema.add_field("title", DataType.VARCHAR, max_length=256)

# BM25 function
bm25_fn = Function(
    name="text_bm25",
    input_field_names=["text"],
    output_field_names=["text_sparse"],
    function_type=FunctionType.BM25,
)
schema.add_function(bm25_fn)
```

### Index Each Vector Field

```python
index_params = client.prepare_index_params()

index_params.add_index(
    field_name="text_dense",
    index_type="HNSW",
    metric_type="COSINE",
    params={"M": 16, "efConstruction": 256},
)

index_params.add_index(
    field_name="text_sparse",
    index_type="SPARSE_INVERTED_INDEX",
    metric_type="BM25",
    params={"inverted_index_algo": "DAAT_MAXSCORE"},
)

index_params.add_index(
    field_name="image_dense",
    index_type="HNSW",
    metric_type="COSINE",
    params={"M": 16, "efConstruction": 256},
)

client.create_collection(
    collection_name="multimodal_docs",
    schema=schema,
    index_params=index_params,
)
```

## Performing Hybrid Search

### Step 1: Create ANN Search Requests

```python
from pymilvus import AnnSearchRequest

# Dense semantic search
req_dense = AnnSearchRequest(
    data=[query_dense_vector],      # 768-dim dense vector
    anns_field="text_dense",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=20,
)

# Sparse keyword search (BM25)
req_sparse = AnnSearchRequest(
    data=["machine learning algorithms"],  # raw text for BM25
    anns_field="text_sparse",
    param={"metric_type": "BM25"},
    limit=20,
)

# Image similarity search
req_image = AnnSearchRequest(
    data=[query_image_vector],      # 512-dim image vector
    anns_field="image_dense",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=20,
)
```

### Step 2: Choose a Reranker

```python
from pymilvus import RRFRanker, WeightedRanker
```

### Step 3: Execute Hybrid Search

```python
results = client.hybrid_search(
    collection_name="multimodal_docs",
    reqs=[req_dense, req_sparse, req_image],
    ranker=RRFRanker(k=60),
    limit=10,
    output_fields=["title", "text"],
)
```

## Reranking Strategies

### RRF (Reciprocal Rank Fusion)

Merges ranked lists without needing score normalization. Each result's score is `1 / (k + rank)` where `k` is a smoothing constant.

```python
ranker = RRFRanker(k=60)  # default k=60
```

**When to use:** Default choice when vector fields use different metrics or scales. Works well when you don't know the relative importance of each field.

**Formula:** `score = Σ 1/(k + rank_i)` across all search requests

### Weighted Ranker

Assigns explicit weights to each search result set. Scores are normalized to [0, 1] before weighting.

```python
ranker = WeightedRanker(0.6, 0.3, 0.1)
# 60% dense, 30% sparse, 10% image
```

**When to use:** When you know the relative importance of each vector field (e.g., semantic meaning matters more than keyword matching).

**Weights must sum to 1.0** and match the order of `reqs`.

## Common Hybrid Search Patterns

### Pattern 1: Sparse + Dense Fusion (RAG)

The most common pattern for retrieval-augmented generation:

```python
# Dense embedding from a model like text-embedding-3-large
req_dense = AnnSearchRequest(
    data=[dense_query_vector],
    anns_field="text_dense",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=30,
)

# BM25 keyword search
req_sparse = AnnSearchRequest(
    data=["specific technical keyword"],
    anns_field="text_sparse",
    param={"metric_type": "BM25"},
    limit=30,
)

results = client.hybrid_search(
    collection_name="knowledge_base",
    reqs=[req_dense, req_sparse],
    ranker=WeightedRanker(0.7, 0.3),  # 70% semantic, 30% keyword
    limit=10,
    output_fields=["text", "source"],
)
```

### Pattern 2: Multi-Modal (Text + Image)

```python
req_text = AnnSearchRequest(
    data=[text_embedding],
    anns_field="text_dense",
    param={"metric_type": "COSINE"},
    limit=20,
)

req_image = AnnSearchRequest(
    data=[image_embedding],
    anns_field="image_dense",
    param={"metric_type": "COSINE"},
    limit=20,
)

results = client.hybrid_search(
    collection_name="products",
    reqs=[req_text, req_image],
    ranker=RRFRanker(),
    limit=10,
    output_fields=["name", "price", "image_url"],
)
```

### Pattern 3: Ensemble of Same-Field Searches

Use different search parameters on the same field for better recall:

```python
# Broad search (high ef, large nprobe)
req_broad = AnnSearchRequest(
    data=[query_vector],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 512}},
    limit=50,
)

# Narrow search with filter
req_filtered = AnnSearchRequest(
    data=[query_vector],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=20,
    expr="category == 'priority'",
)

results = client.hybrid_search(
    collection_name="docs",
    reqs=[req_broad, req_filtered],
    ranker=RRFRanker(),
    limit=10,
)
```

## Hybrid Search with Filters

Apply a global filter that applies to all search requests:

```python
results = client.hybrid_search(
    collection_name="products",
    reqs=[req_text, req_image],
    ranker=RRFRanker(),
    limit=10,
    filter="category in ['electronics', 'gadgets'] and price < 500",
    output_fields=["name", "price", "category"],
)
```

## Performance Considerations

| Factor | Impact | Recommendation |
|--------|--------|----------------|
| Number of requests | Linear latency increase | Keep ≤ 3-4 requests |
| Limit per request | Memory and compute | Set per-request limit 2-3× final limit |
| Reranker choice | RRF slightly faster than Weighted | Use RRF when weights unknown |
| Filter complexity | Can slow pre-filtering | Index filter fields |

## Common Pitfalls

- **Mismatched request count and weights** — `WeightedRanker` must have exactly as many weights as `reqs`
- **Per-request limit too low** — set each request's `limit` higher than the final `limit` for better reranking
- **Missing indexes on some vector fields** — all vector fields used in hybrid search need indexes
- **Not loading all partitions** — if using partition search, ensure all needed partitions are loaded
- **Assuming score comparability** — raw scores from different metrics (COSINE vs BM25) are not directly comparable; use RRF to avoid this issue
