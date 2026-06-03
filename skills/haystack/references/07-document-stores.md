# Haystack Document Stores

> Source: [docs.haystack.deepset.ai/docs/document-store](https://docs.haystack.deepset.ai/docs/document-store) | haystack-ai 2.30.0

## Table of Contents

- [What Are Document Stores](#what-are-document-stores)
- [DocumentStore Protocol](#documentstore-protocol)
- [InMemoryDocumentStore](#inmemorydocumentstore)
- [Elasticsearch](#elasticsearch)
- [Qdrant](#qdrant)
- [Chroma](#chroma)
- [PgVector](#pgvector)
- [Other Document Stores](#other-document-stores)
- [DuplicatePolicy](#duplicatepolicy)
- [Filtering](#filtering)
- [Choosing a Document Store](#choosing-a-document-store)
- [Common Pitfalls](#common-pitfalls)

## What Are Document Stores

Document Stores are database adapters for persisting and retrieving documents. They are NOT pipeline components — they don't have a `run()` method. Instead, they're used by pipeline components like Retrievers and DocumentWriters.

```
Pipeline Component (Retriever) → uses → Document Store (database adapter)
```

## DocumentStore Protocol

Every Document Store implements four mandatory methods:

| Method | Signature | Description |
|--------|-----------|-------------|
| `count_documents` | `() → int` | Count stored documents |
| `filter_documents` | `(filters) → list[Document]` | Filter by metadata |
| `write_documents` | `(documents, policy) → int` | Write documents, return count |
| `delete_documents` | `(document_ids) → None` | Delete by ID |

```python
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore

store = InMemoryDocumentStore()

# Write
docs = [
    Document(content="Haystack overview", meta={"source": "docs"}),
    Document(content="Pipeline guide", meta={"source": "tutorial"}),
]
store.write_documents(docs)

# Count
print(store.count_documents())  # 2

# Filter
results = store.filter_documents(
    filters={"field": "meta.source", "operator": "==", "value": "docs"}
)

# Delete
store.delete_documents(document_ids=[docs[0].id])
```

## InMemoryDocumentStore

Built-in, zero dependencies. Perfect for prototyping and testing:

```python
from haystack.document_stores.in_memory import InMemoryDocumentStore

store = InMemoryDocumentStore(
    bm25_algorithm="BM25Plus",
    bm25_tokenization_regex=r"(?u)\b\w\w+\b",
    embedding_similarity_function="cosine",
)
```

Supports:
- BM25 keyword search
- Embedding similarity search
- Metadata filtering
- No persistence (data lost when process ends)

**Use for**: Prototyping, unit tests, small datasets (<10K documents).

## Elasticsearch

Production-grade full-text + vector search:

```bash
pip install elasticsearch-haystack
```

```python
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore

store = ElasticsearchDocumentStore(
    hosts="http://localhost:9200",
    index="haystack_docs",
    embedding_similarity_function="cosine",
)
```

Supports:
- BM25 keyword search (best-in-class)
- Dense vector search (kNN)
- Hybrid search
- Advanced filtering and aggregations
- Horizontal scaling

**Use for**: Production search with hybrid retrieval, existing Elasticsearch infrastructure.

## Qdrant

High-performance vector database:

```bash
pip install qdrant-haystack
```

```python
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

# Local (file-based)
store = QdrantDocumentStore(
    path="./qdrant_data",
    index="documents",
    embedding_dim=1536,
    similarity="cosine",
)

# Cloud
store = QdrantDocumentStore(
    url="https://xyz.qdrant.cloud:6333",
    api_key=Secret.from_env_var("QDRANT_API_KEY"),
    index="documents",
    embedding_dim=1536,
)
```

**Use for**: Semantic search at scale, pure vector search workloads.

## Chroma

Lightweight embedding database:

```bash
pip install chroma-haystack
```

```python
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

# Persistent local
store = ChromaDocumentStore(
    persist_path="./chroma_data",
    collection_name="documents",
)
```

**Use for**: Local development, small-medium datasets, embedded vector search.

## PgVector

PostgreSQL extension for vector search:

```bash
pip install pgvector-haystack
```

```python
from haystack_integrations.document_stores.pgvector import PgvectorDocumentStore

store = PgvectorDocumentStore(
    connection_string=Secret.from_env_var("PG_CONN_STR"),
    table_name="haystack_docs",
    embedding_dimension=1536,
    vector_function="cosine_similarity",
)
```

**Use for**: Teams already using PostgreSQL who want vector search without a separate database.

## Other Document Stores

| Store | Package | Best For |
|-------|---------|----------|
| OpenSearch | `opensearch-haystack` | AWS-native search, Elasticsearch alternative |
| Pinecone | `pinecone-haystack` | Managed vector search at scale |
| Weaviate | `weaviate-haystack` | AI-native vector search with modules |
| MongoDB Atlas | `mongodb-atlas-haystack` | Existing MongoDB infrastructure |
| Milvus | `milvus-haystack` | High-scale vector workloads |
| Neo4j | `neo4j-haystack` | Graph + vector hybrid |
| Astra DB | `astra-haystack` | Cassandra-based vector search |

## DuplicatePolicy

Controls behavior when writing documents with existing IDs:

```python
from haystack.document_stores.types import DuplicatePolicy
from haystack.components.writers import DocumentWriter

# OVERWRITE — replace existing documents (default for most stores)
writer = DocumentWriter(
    document_store=store,
    policy=DuplicatePolicy.OVERWRITE,
)

# SKIP — keep existing, ignore new duplicates
writer = DocumentWriter(
    document_store=store,
    policy=DuplicatePolicy.SKIP,
)

# FAIL — raise error on duplicate IDs
writer = DocumentWriter(
    document_store=store,
    policy=DuplicatePolicy.FAIL,
)
```

Document IDs are auto-generated from content hash if not provided. Set explicit IDs for upsert workflows:

```python
doc = Document(
    id="unique-doc-001",
    content="...",
)
```

## Filtering

Haystack uses a unified filter syntax across all document stores:

### Comparison Operators

```python
# Equals
filters = {"field": "meta.category", "operator": "==", "value": "science"}

# Not equals
filters = {"field": "meta.category", "operator": "!=", "value": "sports"}

# Greater than
filters = {"field": "meta.year", "operator": ">", "value": 2023}

# In list
filters = {"field": "meta.category", "operator": "in", "value": ["science", "tech"]}

# Not in list
filters = {"field": "meta.category", "operator": "not in", "value": ["sports"]}
```

### Logical Operators

```python
# AND
filters = {
    "operator": "AND",
    "conditions": [
        {"field": "meta.category", "operator": "==", "value": "science"},
        {"field": "meta.year", "operator": ">", "value": 2023},
    ],
}

# OR
filters = {
    "operator": "OR",
    "conditions": [
        {"field": "meta.source", "operator": "==", "value": "arxiv"},
        {"field": "meta.source", "operator": "==", "value": "pubmed"},
    ],
}

# Nested
filters = {
    "operator": "AND",
    "conditions": [
        {"field": "meta.year", "operator": ">=", "value": 2024},
        {
            "operator": "OR",
            "conditions": [
                {"field": "meta.topic", "operator": "==", "value": "AI"},
                {"field": "meta.topic", "operator": "==", "value": "ML"},
            ],
        },
    ],
}
```

## Choosing a Document Store

| Need | Recommendation |
|------|---------------|
| Prototyping / tests | InMemoryDocumentStore |
| Best full-text search | Elasticsearch / OpenSearch |
| Pure vector search at scale | Qdrant / Pinecone / Milvus |
| Hybrid search (text + vector) | Elasticsearch / Weaviate |
| Existing PostgreSQL | PgVector |
| Existing MongoDB | MongoDB Atlas |
| Managed, zero-ops | Pinecone / Weaviate Cloud |
| Graph + vector | Neo4j |

Performance differences within Haystack pipelines are often marginal. Choose based on existing infrastructure, scaling needs, and operational preferences.

## Common Pitfalls

**Using InMemoryDocumentStore in production**: Data is lost when the process restarts. Use a persistent store for production.

**Mismatched embedding dimensions**: The Document Store embedding dimension must match your embedder model's output dimension (e.g., 1536 for OpenAI `text-embedding-3-small`).

**Forgetting to create embeddings**: Embedding retrievers require documents to have embeddings. Run an embedding pipeline before retrieval.

**Not using filters**: Metadata filters significantly improve retrieval precision. Always store useful metadata (source, date, category) and filter when possible.

## Related Topics

- Retrievers → `06-retrievers.md`
- Embedders → `08-embedders.md`
- RAG patterns → `11-rag-patterns.md`
