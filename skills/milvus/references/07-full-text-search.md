# Milvus — Full-Text Search (BM25)

> Source: [milvus.io/docs/full-text-search.md](https://milvus.io/docs/full-text-search.md) | Version: 3.0-beta

## Table of Contents

- [How It Works](#how-it-works)
- [Setting Up Full-Text Search](#setting-up-full-text-search)
- [BM25 Parameters](#bm25-parameters)
- [Inserting Text Data](#inserting-text-data)
- [Performing Full-Text Search](#performing-full-text-search)
- [Combining BM25 with Dense Search](#combining-bm25-with-dense-search-hybrid)
- [Text Analyzers](#text-analyzers)
- [Common Pitfalls](#common-pitfalls)

## Overview

Milvus supports full-text search using the BM25 algorithm, enabling keyword-based document retrieval alongside vector similarity search. Text is automatically tokenized and converted to sparse vector representations internally — no external embedding model is needed for the keyword component.

## How It Works

```
Raw Text → Analyzer (tokenization) → BM25 Function → Sparse Vector → Inverted Index → Relevance Scoring
```

1. User provides plain text
2. Milvus analyzes text into terms using a configurable tokenizer
3. BM25 function converts terms into sparse vector representations
4. Sparse vectors are stored and indexed
5. At search time, query text undergoes the same pipeline and BM25 scores relevance

## Setting Up Full-Text Search

### Step 1: Define Schema

```python
from pymilvus import MilvusClient, DataType, Function, FunctionType

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")
schema = client.create_schema()

# Primary key
schema.add_field("id", DataType.INT64, is_primary=True, auto_id=True)

# Text field — enable_analyzer=True is required for tokenization
schema.add_field(
    field_name="text",
    datatype=DataType.VARCHAR,
    max_length=5000,
    enable_analyzer=True,
)

# Sparse vector field — stores BM25 representations
schema.add_field(
    field_name="sparse",
    datatype=DataType.SPARSE_FLOAT_VECTOR,
)

# Optional: dense vector for hybrid search
schema.add_field(
    field_name="dense",
    datatype=DataType.FLOAT_VECTOR,
    dim=768,
)
```

### Step 2: Define BM25 Function

```python
bm25_function = Function(
    name="text_bm25_emb",
    input_field_names=["text"],       # VARCHAR field with enable_analyzer=True
    output_field_names=["sparse"],    # SPARSE_FLOAT_VECTOR field
    function_type=FunctionType.BM25,
)

schema.add_function(bm25_function)
```

### Step 3: Configure Index

```python
index_params = client.prepare_index_params()

# BM25 sparse index
index_params.add_index(
    field_name="sparse",
    index_type="SPARSE_INVERTED_INDEX",
    metric_type="BM25",
    params={
        "inverted_index_algo": "DAAT_MAXSCORE",
        "bm25_k1": 1.2,
        "bm25_b": 0.75,
    },
)

# Dense vector index (for hybrid search)
index_params.add_index(
    field_name="dense",
    index_type="HNSW",
    metric_type="COSINE",
    params={"M": 16, "efConstruction": 256},
)
```

### Step 4: Create Collection

```python
client.create_collection(
    collection_name="search_docs",
    schema=schema,
    index_params=index_params,
)
```

## BM25 Parameters

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `bm25_k1` | 1.2 | 1.2–2.0 | Term frequency saturation — higher = more weight to repeated terms |
| `bm25_b` | 0.75 | 0–1.0 | Length normalization — 0 = ignore length, 1 = full normalization |

**Tuning guidelines:**
- `k1 = 1.2, b = 0.75` — good defaults for most text
- `k1 = 2.0, b = 0.75` — more weight to term frequency (long documents)
- `k1 = 1.2, b = 0.0` — ignore document length differences

## Inverted Index Algorithms

| Algorithm | Best For | Behavior |
|-----------|----------|----------|
| `DAAT_MAXSCORE` | Large `limit` (k > 100) | Optimized scoring, skips low-scoring docs |
| `DAAT_WAND` | Small `limit` (k ≤ 100) | Efficient early termination |
| `TAAT_NAIVE` | Adapting to collection changes | Brute-force, always correct after updates |

## Inserting Text Data

Just provide raw text — BM25 sparse vectors are generated automatically:

```python
docs = [
    {"text": "Information retrieval is a field of study focusing on search algorithms."},
    {"text": "Machine learning models can improve search relevance over time."},
    {"text": "Natural language processing enables understanding of human language."},
    {"text": "Deep learning has revolutionized computer vision and NLP."},
    {"text": "Vector databases store embeddings for fast similarity search."},
]

# Add dense vectors (from your embedding model)
for doc in docs:
    doc["dense"] = embedding_model.encode(doc["text"]).tolist()

client.insert(collection_name="search_docs", data=docs)
```

## Performing Full-Text Search

```python
results = client.search(
    collection_name="search_docs",
    data=["search algorithms and information retrieval"],
    anns_field="sparse",        # search the BM25 sparse field
    limit=5,
    output_fields=["text"],
)

for hits in results:
    for hit in hits:
        print(f"score={hit['distance']:.4f}: {hit['entity']['text'][:100]}")
```

## Search Parameters

```python
results = client.search(
    collection_name="search_docs",
    data=["machine learning search"],
    anns_field="sparse",
    limit=10,
    search_params={
        "metric_type": "BM25",
        "params": {
            "drop_ratio_search": 0.2,  # drop 20% of lowest-weight terms in query
        },
    },
    output_fields=["text"],
)
```

`drop_ratio_search` (0–1): Proportion of least-important query terms to ignore. Higher values = faster search, slightly lower recall. Default: 0 (use all terms).

## Combining BM25 with Dense Search (Hybrid)

The most powerful pattern — combine keyword precision with semantic understanding:

```python
from pymilvus import AnnSearchRequest, RRFRanker

# Semantic search
req_dense = AnnSearchRequest(
    data=[query_embedding],
    anns_field="dense",
    param={"metric_type": "COSINE", "params": {"ef": 128}},
    limit=20,
)

# Keyword search
req_sparse = AnnSearchRequest(
    data=["specific API function name"],
    anns_field="sparse",
    param={"metric_type": "BM25"},
    limit=20,
)

results = client.hybrid_search(
    collection_name="search_docs",
    reqs=[req_dense, req_sparse],
    ranker=RRFRanker(k=60),
    limit=10,
    output_fields=["text"],
)
```

## Text Analyzers

Configure how text is tokenized. Set analyzer type on the VARCHAR field:

```python
schema.add_field(
    field_name="text",
    datatype=DataType.VARCHAR,
    max_length=5000,
    enable_analyzer=True,
    analyzer_params={
        "type": "standard",  # default tokenizer
    },
)
```

### Built-In Analyzers

| Analyzer | Description | Use Case |
|----------|-------------|----------|
| `standard` | Unicode-aware word tokenizer + lowercase | General text (default) |
| `english` | Standard + English stemming + stop words | English documents |
| `chinese` | Jieba segmentation | Chinese text |

### Custom Dictionary (v3.0+)

```python
# Upload custom dictionary for tokenization
schema.add_field(
    field_name="text",
    datatype=DataType.VARCHAR,
    max_length=5000,
    enable_analyzer=True,
    analyzer_params={
        "type": "standard",
        "filter": ["lowercase", "stop"],
    },
)
```

## Limitations

- Sparse vectors generated by BM25 are **not directly accessible** — cannot be included in `output_fields`
- BM25 works on single VARCHAR fields — to search across multiple text fields, create separate BM25 functions for each
- Full-text search requires `enable_analyzer=True` on the input VARCHAR field
- The sparse field must be `SPARSE_FLOAT_VECTOR` type
- Text must be within the `max_length` limit of the VARCHAR field

## Complete Example: RAG Knowledge Base

```python
from pymilvus import MilvusClient, DataType, Function, FunctionType, AnnSearchRequest, RRFRanker

client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")

# Schema
schema = client.create_schema()
schema.add_field("id", DataType.INT64, is_primary=True, auto_id=True)
schema.add_field("text", DataType.VARCHAR, max_length=8000, enable_analyzer=True)
schema.add_field("text_sparse", DataType.SPARSE_FLOAT_VECTOR)
schema.add_field("text_dense", DataType.FLOAT_VECTOR, dim=1536)
schema.add_field("source", DataType.VARCHAR, max_length=512)

schema.add_function(Function(
    name="bm25", input_field_names=["text"],
    output_field_names=["text_sparse"], function_type=FunctionType.BM25,
))

# Indexes
index_params = client.prepare_index_params()
index_params.add_index(field_name="text_sparse", index_type="SPARSE_INVERTED_INDEX",
                       metric_type="BM25", params={"inverted_index_algo": "DAAT_MAXSCORE"})
index_params.add_index(field_name="text_dense", index_type="HNSW",
                       metric_type="COSINE", params={"M": 16, "efConstruction": 256})

client.create_collection("kb", schema=schema, index_params=index_params)

# Insert
chunks = [
    {"text": "Milvus is a vector database...", "text_dense": [...], "source": "docs"},
    {"text": "HNSW provides fast ANN search...", "text_dense": [...], "source": "blog"},
]
client.insert("kb", chunks)

# Hybrid retrieval
query = "How does Milvus handle vector indexing?"
req_semantic = AnnSearchRequest(data=[query_embedding], anns_field="text_dense",
                                param={"metric_type": "COSINE"}, limit=20)
req_keyword = AnnSearchRequest(data=[query], anns_field="text_sparse",
                               param={"metric_type": "BM25"}, limit=20)

results = client.hybrid_search("kb", reqs=[req_semantic, req_keyword],
                               ranker=RRFRanker(), limit=5, output_fields=["text", "source"])
```

## Common Pitfalls

- **Forgetting `enable_analyzer=True`** — BM25 silently fails without tokenization
- **Using wrong metric_type** — BM25 sparse fields must use `metric_type="BM25"`, not `IP`
- **Trying to output the sparse field** — BM25 sparse vectors cannot be in `output_fields`
- **Expecting stemming without specifying analyzer** — default `standard` analyzer does not stem
