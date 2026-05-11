# Upstash Vector — Serverless Vector Database

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Setup](#setup)
- [Initialization](#initialization)
- [Index Types](#index-types)
- [Built-in Embedding Models](#built-in-embedding-models)
- [Similarity Functions](#similarity-functions)
- [Upsert Operations](#upsert-operations)
- [Query Operations](#query-operations)
- [Metadata Filtering](#metadata-filtering)
- [Namespaces](#namespaces)
- [Other Operations](#other-operations)
- [Resumable Queries](#resumable-queries)
- [Framework Integrations](#framework-integrations)
- [RAG Pattern Example](#rag-pattern-example)
- [Common Pitfalls](#common-pitfalls)

## Overview

Upstash Vector is a serverless vector database for AI/ML and LLM applications.

- Serverless — no infrastructure to manage, scales automatically
- HTTP/REST based — no persistent connections needed
- Built-in embedding models — upsert raw text, no external embedding API required
- Supports dense, sparse, and hybrid search
- Metadata filtering with SQL-like operators
- Namespaces for logical data isolation
- Pay-per-request pricing, no idle costs

## Installation

```typescript
npm install @upstash/vector
```

```bash
pip install upstash-vector
```

## Setup

1. Create a Vector Index at console.upstash.com
2. Choose index type: Dense, Sparse, or Hybrid
3. Select an embedding model (or bring your own embeddings)
4. Set dimensions and similarity function (auto-configured with built-in models)
5. Set environment variables:

```bash
export UPSTASH_VECTOR_REST_URL="https://your-index-url.upstash.io"
export UPSTASH_VECTOR_REST_TOKEN="your-token-here"
```

## Initialization

```typescript
import { Index } from "@upstash/vector";

// From environment variables
const index = Index.fromEnv();

// Direct configuration
const index = new Index({
  url: "https://your-index-url.upstash.io",
  token: "your-token-here",
});
```

```python
from upstash_vector import Index

index = Index(url="https://your-index-url.upstash.io", token="your-token-here")
# Or from env:
index = Index.from_env()
```

## Index Types

- **Dense**: Semantic search using dense vector embeddings. Best for finding conceptually similar content even when exact words differ. Supports cosine, euclidean, and dot product similarity.
- **Sparse**: Keyword/full-text search using sparse vectors (BM25). Best for exact term matching and traditional information retrieval.
- **Hybrid**: Combined dense + sparse for best relevance. Control weighting between semantic similarity and keyword match at query time.

## Built-in Embedding Models

When using a built-in model, Upstash generates embeddings server-side. You upsert raw text instead of pre-computed vectors.

| Model | Dimensions | Max Seq Length | Notes |
|-------|-----------|----------------|-------|
| `mixedbread-ai/mxbai-embed-large-v1` | 1024 | 512 | Best overall quality |
| `BAAI/bge-large-en-v1.5` | 1024 | 512 | English-focused |
| `BAAI/bge-m3` | 1024 | 8192 | Multilingual, long context |
| `WhereIsAI/UAE-Large-V1` | 1024 | 512 | Strong general-purpose |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | 256 | Lightweight, fast |
| `BM25` | — | — | Sparse/keyword search only |

## Similarity Functions

- **Cosine**: Measures angle between vectors. Range `[0, 1]`. Most common for text embeddings.
- **Euclidean**: Measures spatial distance. Smaller = more similar.
- **Dot Product**: Measures vector alignment. Requires normalized vectors. Fastest.

Set at index creation time in the console; affects how scores are calculated.

## Upsert Operations

### With Built-in Embeddings (Data Upsert)

```typescript
await index.upsert([
  {
    id: "doc-1",
    data: "Upstash is a serverless data platform for modern applications",
    metadata: { source: "docs", category: "overview", version: 2 },
  },
  {
    id: "doc-2",
    data: "Redis is an in-memory data store used for caching",
    metadata: { source: "docs", category: "redis", version: 1 },
  },
]);
```

### With Custom Embeddings

```typescript
await index.upsert([{
  id: "vec-1",
  vector: [0.1, 0.2, 0.3, 0.4, 0.5],
  metadata: { title: "Document 1" },
}]);
```

### Sparse Vectors (Hybrid/Keyword Search)

```typescript
await index.upsert([{
  id: "sparse-1",
  data: "Serverless vector database for AI",
  sparseVector: { indices: [0, 3, 5, 12, 48], values: [0.5, 0.3, 0.2, 0.8, 0.1] },
  metadata: { title: "Sparse document" },
}]);
```

## Query Operations

### Semantic Search (Built-in Embeddings)

```typescript
const results = await index.query({
  data: "serverless database platform",
  topK: 5,
  includeMetadata: true,
  includeData: true,
});
// results: [{ id, score, metadata, data }, ...]
```

### Vector Search (Custom Embeddings)

```typescript
const results = await index.query({
  vector: [0.1, 0.2, 0.3, 0.4, 0.5],
  topK: 10,
  includeMetadata: true,
});
```

### Hybrid Search

```typescript
const results = await index.query({
  data: "serverless database platform",
  topK: 5,
  includeMetadata: true,
  weightDense: 0.7,   // 70% semantic similarity
  weightSparse: 0.3,  // 30% keyword match
});
```

Requires a hybrid index. Higher `weightDense` favors meaning; higher `weightSparse` favors exact terms.

## Metadata Filtering

SQL-like filter expressions narrow query results by metadata fields:

```typescript
const results = await index.query({
  data: "serverless platform",
  topK: 10,
  filter: "category = 'redis' AND version > 1",
  includeMetadata: true,
});
```

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `category = 'redis'` |
| `!=` | Not equals | `status != 'archived'` |
| `<`, `<=`, `>`, `>=` | Comparison | `version > 1` |
| `AND`, `OR`, `NOT` | Logical | `a = 1 AND b = 2` |
| `GLOB` | Wildcard matching | `title GLOB '*serverless*'` |
| `CONTAINS` | String contains | `tags CONTAINS 'ai'` |
| `HAS` | Field existence | `HAS author` |

### Complex Filters

```typescript
// Combined conditions
const results = await index.query({
  data: "database",
  topK: 10,
  filter: "(category = 'redis' OR category = 'vector') AND version >= 2",
  includeMetadata: true,
});
```

Metadata per vector is limited to **48 KB**.

## Namespaces

Namespaces provide logical isolation within a single index. Vectors in one namespace are invisible to queries in another.

```typescript
const ns = index.namespace("production");

// Upsert into the namespace
await ns.upsert([
  { id: "doc-1", data: "Production document content" },
]);

// Query within the namespace
const results = await ns.query({
  data: "production documents",
  topK: 5,
  includeMetadata: true,
});

// Delete all vectors in this namespace only
await ns.deleteAll();
```

Use cases: multi-tenancy, environment separation (dev/staging/prod), content type isolation.

## Other Operations

### Fetch by ID

```typescript
const vectors = await index.fetch(["doc-1", "doc-2"], {
  includeMetadata: true,
  includeData: true,
});
// Returns null for IDs that do not exist
```

### Delete

```typescript
await index.delete(["doc-1", "doc-2"]);
await index.reset();  // Delete ALL vectors (use with caution)
```

### Update

```typescript
await index.update({
  id: "doc-1",
  metadata: { category: "updated" },
});

// Update data (re-generates embedding with built-in model)
await index.update({
  id: "doc-1",
  data: "Updated document content",
});
```

### Range (Paginated Retrieval)

```typescript
let cursor = "0";
do {
  const result = await index.range({
    cursor,
    limit: 100,
    includeMetadata: true,
  });
  for (const vector of result.vectors) {
    console.log(vector.id, vector.metadata);
  }
  cursor = result.nextCursor;
} while (cursor !== "");
```

### Index Info

```typescript
const info = await index.info();
// { vectorCount, pendingVectorCount, indexSize, dimension,
//   similarityFunction, namespaces }
```

`pendingVectorCount` indicates vectors upserted but not yet indexed for search.

## Resumable Queries

Paginate through large result sets with a server-side cursor:

```typescript
const { result, fetchNext } = await index.resumableQuery({
  data: "serverless database",
  topK: 100,
  includeMetadata: true,
  maxIdle: 3600,  // Cursor alive for 1 hour (seconds)
});

for (const item of result) { console.log(item.id, item.score); }
const nextBatch = await fetchNext(100);
await nextBatch.stop();  // Release cursor when done
```

## Framework Integrations

### LangChain

```typescript
import { UpstashVectorStore } from "@langchain/community/vectorstores/upstash";
import { Index } from "@upstash/vector";

const index = Index.fromEnv();
const store = new UpstashVectorStore(embeddings, { index });

await store.addDocuments(documents);
const results = await store.similaritySearch("query text", 5);
```

### Vercel AI SDK

Built-in Upstash Vector provider available via `@ai-sdk/upstash`.

### Mastra

Upstash Vector integrates as a vector store provider for agent memory and knowledge bases.

## RAG Pattern Example

```typescript
import { Index } from "@upstash/vector";

const index = Index.fromEnv();

// 1. Index documents
await index.upsert([
  { id: "doc-1", data: "Upstash provides serverless Redis and Kafka...", metadata: { source: "docs" } },
  { id: "doc-2", data: "QStash is a serverless message queue...", metadata: { source: "docs" } },
]);

// 2. Retrieve relevant context
const results = await index.query({
  data: userQuestion,
  topK: 3,
  includeData: true,
});

// 3. Build augmented prompt for LLM
const context = results.map((r) => r.data).join("\n");
const prompt = `Context:\n${context}\n\nQuestion: ${userQuestion}\nAnswer:`;
```

### Python Example

```python
from upstash_vector import Index

index = Index.from_env()

# Upsert
index.upsert([
    {"id": "doc-1", "data": "Serverless vector database", "metadata": {"source": "docs"}},
    {"id": "doc-2", "data": "AI application platform", "metadata": {"source": "blog"}},
])

# Query with filtering
results = index.query(data="serverless database", top_k=5,
    include_metadata=True, include_data=True,
    filter="source = 'docs'")

# Namespaces
ns = index.namespace("production")
ns.upsert([{"id": "prod-1", "data": "Production content"}])
results = ns.query(data="production", top_k=3)
```

## Common Pitfalls

1. **Eventual consistency** — Newly upserted vectors may not appear immediately in queries. Check `pendingVectorCount` in `info()` to see indexing backlog.

2. **Similarity function mismatch** — Most text embedding models are trained for cosine similarity. Using dot product with unnormalized vectors produces meaningless scores.

3. **Metadata filter syntax** — SQL-like but not full SQL. No subqueries, joins, or aggregations.

4. **Sequence length limits** — Built-in models truncate text exceeding max sequence length silently. Chunk long documents before upserting.

5. **Index type constraints** — Dense and sparse vectors cannot be mixed in a non-hybrid index. Create a hybrid index from the start if you need both.

6. **Namespace isolation is logical** — Namespaces share the same underlying index and billing. Data isolation only, not performance isolation.

7. **Metadata size limit** — 48 KB per vector. Store large payloads externally and reference via metadata.

8. **ID uniqueness** — Upserting with an existing ID overwrites the previous vector silently.

9. **Rate limits** — Free tier has daily request limits. Monitor usage via the console.

10. **topK vs results** — If fewer vectors match your filter than `topK`, you get fewer results. Empty results mean no vectors passed the filter, not that the index is empty.
