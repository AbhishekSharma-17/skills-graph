# Turso Vector Similarity Search

> Source: [docs.turso.tech/features/ai-and-embeddings](https://docs.turso.tech/features/ai-and-embeddings) | [docs.turso.tech/guides/vector-search](https://docs.turso.tech/guides/vector-search)

## Table of Contents
- [Overview](#overview)
- [Vector Types](#vector-types)
- [Creating Vector Columns](#creating-vector-columns)
- [Inserting Embeddings](#inserting-embeddings)
- [Similarity Search](#similarity-search)
- [Vector Indexes (DiskANN)](#vector-indexes-diskann)
- [Distance Metrics](#distance-metrics)
- [Utility Functions](#utility-functions)
- [RAG Pattern](#rag-pattern)
- [Performance Considerations](#performance-considerations)
- [Common Pitfalls](#common-pitfalls)

## Overview

Turso provides native vector similarity search built into libSQL — no extensions required. Use it for semantic search, RAG workflows, recommendation systems, and AI memory.

## Vector Types

| Type | Storage per Dimension | Use Case |
|------|----------------------|----------|
| `FLOAT64` / `F64_BLOB` | 8 bytes | Maximum precision (IEEE 754 double) |
| `FLOAT32` / `F32_BLOB` | 4 bytes | **Recommended default** for most ML embeddings |
| `FLOAT16` / `F16_BLOB` | 2 bytes | Balance of speed and precision |
| `FLOATB16` / `FB16_BLOB` | 2 bytes | Faster operations, lower precision |
| `FLOAT8` / `F8_BLOB` | 1 byte | 4x compression via single-byte quantization |
| `FLOAT1BIT` / `F1BIT_BLOB` | 1/8 byte | 32x compression (binary quantization) |

**Start with `FLOAT32`** for most applications. Quantize to `FLOAT8` or `FLOAT1BIT` for large-scale deployments where storage and speed matter more than precision.

### Sparse Vectors

```sql
-- For TF-IDF, bag-of-words, or high-dimensional sparse data
CREATE TABLE docs (
    id INTEGER PRIMARY KEY,
    features BLOB  -- Use vector32_sparse type
);
```

## Creating Vector Columns

```sql
-- Specify type and dimensions
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    embedding F32_BLOB(1536)   -- OpenAI text-embedding-3-small dimensions
);

-- Multiple vector columns
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    text_embedding F32_BLOB(1536),
    image_embedding F32_BLOB(512)
);

-- With other quantized types
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    data TEXT,
    embedding F16_BLOB(768)    -- Smaller model, half precision
);
```

## Inserting Embeddings

```sql
-- Insert with vector conversion function
INSERT INTO documents (title, content, embedding)
VALUES (
    'Introduction to RAG',
    'Retrieval-augmented generation combines...',
    vector32('[0.1, 0.5, -0.3, 0.8, ...]')  -- JSON array string
);

-- Batch insert
INSERT INTO documents (title, content, embedding) VALUES
    ('Doc A', 'Content A', vector32('[0.1, 0.2, 0.3, 0.4]')),
    ('Doc B', 'Content B', vector32('[0.5, 0.6, 0.7, 0.8]')),
    ('Doc C', 'Content C', vector32('[0.9, 0.1, 0.2, 0.3]'));
```

### From Application Code (TypeScript)

```typescript
import OpenAI from "openai";

const openai = new OpenAI();

async function insertDocument(client: Client, title: string, content: string) {
  const response = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: content,
  });
  const embedding = JSON.stringify(response.data[0].embedding);

  await client.execute({
    sql: "INSERT INTO documents (title, content, embedding) VALUES (?, ?, vector32(?))",
    args: [title, content, embedding],
  });
}
```

### From Application Code (Python)

```python
import openai

def insert_document(db, title: str, content: str):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=content,
    )
    embedding = str(response.data[0].embedding)

    db.execute(
        "INSERT INTO documents (title, content, embedding) VALUES (?, ?, vector32(?))",
        (title, content, embedding),
    )
    db.commit()
```

## Similarity Search

### Brute-Force (Linear Scan)

```sql
-- Cosine distance (lower = more similar)
SELECT title,
       vector_distance_cos(embedding, vector32('[0.1, 0.5, -0.3, 0.8]')) AS distance
FROM documents
ORDER BY distance ASC
LIMIT 10;
```

### With Filtering

```sql
SELECT title, distance
FROM (
    SELECT title, category,
           vector_distance_cos(embedding, vector32(?)) AS distance
    FROM documents
    WHERE category = 'tech'
)
ORDER BY distance ASC
LIMIT 5;
```

## Vector Indexes (DiskANN)

For large datasets, create a DiskANN index for approximate nearest-neighbor (ANN) search:

### Create Index

```sql
-- Basic index
CREATE INDEX docs_embedding_idx ON documents(libsql_vector_idx(embedding));

-- With configuration
CREATE INDEX docs_embedding_idx ON documents(
    libsql_vector_idx(
        embedding,
        'metric=cosine',          -- cosine (default) or l2
        'compress_neighbors=float8',  -- Compress neighbor vectors
        'max_neighbors=64',       -- More neighbors = better recall, more storage
        'search_l=200',           -- Higher = better accuracy, slower queries
        'insert_l=70'             -- Higher = better index quality, slower inserts
    )
);
```

### Query with Index

```sql
-- Use vector_top_k() with the index
SELECT d.title, d.content
FROM vector_top_k('docs_embedding_idx', vector32('[0.1, 0.5, -0.3, 0.8]'), 10) AS v
JOIN documents d ON d.rowid = v.id;
```

The `vector_top_k(index_name, query_vector, k)` function:
- Returns the k approximate nearest neighbors
- Output columns: `id` (rowid) and `distance`
- Automatically stays in sync with base table inserts/updates/deletes

### Index Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `metric` | `cosine` | Distance function: `cosine` or `l2` |
| `max_neighbors` | `3√D` | Storage vs precision tradeoff |
| `compress_neighbors` | — | Compress stored neighbor vectors (e.g., `float8`) |
| `alpha` | `1.2` | DiskANN graph sparsity (≥1.0) |
| `search_l` | `200` | Query-time accuracy vs speed |
| `insert_l` | `70` | Insert-time quality vs speed |

## Distance Metrics

### Cosine Distance

```sql
SELECT vector_distance_cos(embedding, vector32('[...]')) AS distance FROM documents;
```

Range: 0 to 2 (0 = identical direction, 1 = orthogonal, 2 = opposite). Best for text embeddings where direction matters more than magnitude.

### Euclidean (L2) Distance

```sql
SELECT vector_distance_l2(embedding, vector32('[...]')) AS distance FROM documents;
```

Straight-line distance in n-dimensional space. Not available for `FLOAT1BIT` vectors.

### Dot Product

Computes negative sum of element products. Best for normalized embeddings and maximum inner product search (MIPS).

### Jaccard Distance

For sparse and binary vectors. Computes weighted ratio of min to max values.

## Utility Functions

```sql
-- Extract vector as JSON text
SELECT vector_extract(embedding) FROM documents WHERE id = 1;
-- Returns: '[0.1, 0.5, -0.3, 0.8]'

-- Concatenate two vectors
SELECT vector_concat(vector32('[1,2]'), vector32('[3,4]'));
-- Returns vector32 with 4 dimensions

-- Slice a vector (zero-based, end exclusive)
SELECT vector_slice(embedding, 0, 128) FROM documents;
-- Returns first 128 dimensions
```

## RAG Pattern

### Complete RAG Workflow

```typescript
import { createClient } from "@libsql/client";
import OpenAI from "openai";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});
const openai = new OpenAI();

// 1. Setup
await client.execute(`
  CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    source TEXT,
    embedding F32_BLOB(1536)
  )
`);
await client.execute(
  "CREATE INDEX IF NOT EXISTS knowledge_idx ON knowledge(libsql_vector_idx(embedding))"
);

// 2. Ingest documents
async function ingest(content: string, source: string) {
  const { data } = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: content,
  });
  await client.execute({
    sql: "INSERT INTO knowledge (content, source, embedding) VALUES (?, ?, vector32(?))",
    args: [content, source, JSON.stringify(data[0].embedding)],
  });
}

// 3. Retrieve and generate
async function askQuestion(question: string): Promise<string> {
  const { data } = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: question,
  });
  const queryVec = JSON.stringify(data[0].embedding);

  const { rows } = await client.execute({
    sql: `SELECT k.content, k.source
          FROM vector_top_k('knowledge_idx', vector32(?), 5) AS v
          JOIN knowledge k ON k.rowid = v.id`,
    args: [queryVec],
  });

  const context = rows.map((r) => r.content).join("\n\n");

  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    messages: [
      { role: "system", content: `Answer using this context:\n\n${context}` },
      { role: "user", content: question },
    ],
  });

  return response.choices[0].message.content!;
}
```

## Performance Considerations

- **Without index**: Linear scan — acceptable for <10K rows
- **With DiskANN index**: Sublinear ANN search — use for >10K rows
- **Quantization**: `FLOAT8` gives ~4x compression with minimal recall loss
- **Max dimensions**: 65,536 per vector
- **Index maintenance**: `vector_top_k()` auto-syncs with inserts/updates/deletes
- **Filter then search**: Use `WHERE` clauses to narrow the candidate set before similarity computation

## Common Pitfalls

1. **Mismatched types/dimensions** — `vector_distance_cos()` requires identical vector types and dimensionality on both sides
2. **Forgetting the conversion function** — Insert `vector32('[...]')`, not raw JSON strings
3. **No index for large datasets** — Linear scan degrades quickly past ~10K rows
4. **FLOAT1BIT cosine** — Returns Hamming distance, not standard cosine similarity
5. **Composite primary keys** — Vector indexes require ROWID or singular PRIMARY KEY tables
6. **Tiny negative distances** — Near-zero cosine distances may return values like -1e-9 due to floating-point precision; treat as 0
