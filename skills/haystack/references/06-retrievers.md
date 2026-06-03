# Haystack Retrievers

> Source: [docs.haystack.deepset.ai/docs/retrievers](https://docs.haystack.deepset.ai/docs/retrievers) | haystack-ai 2.30.0

## Table of Contents

- [What Are Retrievers](#what-are-retrievers)
- [Retriever Types](#retriever-types)
- [Keyword Retrieval (BM25)](#keyword-retrieval-bm25)
- [Embedding Retrieval](#embedding-retrieval)
- [Hybrid Retrieval](#hybrid-retrieval)
- [Multi-Query Retrieval](#multi-query-retrieval)
- [Specialized Retrievers](#specialized-retrievers)
- [Filter Policy](#filter-policy)
- [Choosing a Retriever](#choosing-a-retriever)
- [Common Pitfalls](#common-pitfalls)

## What Are Retrievers

Retrievers search through documents in a Document Store, score them by relevance, and return the top candidates. They are the core search component in any RAG pipeline.

Retrievers:
- Accept a query (text or embedding) plus optional filters
- Return a ranked list of `Document` objects with relevance scores
- Are tied to specific Document Store implementations
- Follow the naming convention: `[StoreName][Method]Retriever`

## Retriever Types

| Type | Method | Strengths | Weaknesses |
|------|--------|-----------|------------|
| **Sparse/Keyword** | BM25 | Fast, no training, language-agnostic | No semantic understanding |
| **Dense/Embedding** | Vector similarity | Semantic matching, handles synonyms | Needs embeddings, compute-heavy |
| **Sparse Embedding** | SPLADE | Best of keyword + semantic | Model-dependent |
| **Hybrid** | BM25 + Embedding | Combines both approaches | More complex setup |
| **Filter** | Metadata filters | Exact match on metadata | No text search |

## Keyword Retrieval (BM25)

BM25 (Best Matching 25) finds documents based on term frequency and inverse document frequency:

```python
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever

doc_store = InMemoryDocumentStore()
retriever = InMemoryBM25Retriever(
    document_store=doc_store,
    top_k=10,
)

result = retriever.run(query="machine learning frameworks")
documents = result["documents"]
```

### With Elasticsearch

```python
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchBM25Retriever

doc_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")
retriever = ElasticsearchBM25Retriever(
    document_store=doc_store,
    top_k=10,
    fuzziness="AUTO",
)
```

**When to use BM25**: Exact keyword matching, technical documentation search, code search, any case where specific terms matter more than semantic meaning.

## Embedding Retrieval

Uses vector representations for semantic similarity:

```python
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.embedders import OpenAITextEmbedder

# In a pipeline: embed query then retrieve
pipe = Pipeline()
pipe.add_component("embedder", OpenAITextEmbedder())
pipe.add_component("retriever", InMemoryEmbeddingRetriever(
    document_store=doc_store,
    top_k=5,
))
pipe.connect("embedder.embedding", "retriever.query_embedding")

result = pipe.run({"embedder": {"text": "How do neural networks learn?"}})
```

### With Qdrant

```python
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever

doc_store = QdrantDocumentStore(
    url="http://localhost:6333",
    index="documents",
    embedding_dim=1536,
)
retriever = QdrantEmbeddingRetriever(
    document_store=doc_store,
    top_k=5,
)
```

**When to use embedding retrieval**: Semantic search, question answering, finding conceptually similar content regardless of exact wording.

## Hybrid Retrieval

Combines keyword and embedding retrievers for the best of both:

```python
from haystack import Pipeline
from haystack.components.joiners import DocumentJoiner
from haystack.components.retrievers.in_memory import (
    InMemoryBM25Retriever,
    InMemoryEmbeddingRetriever,
)

pipe = Pipeline()
pipe.add_component("bm25", InMemoryBM25Retriever(
    document_store=doc_store, top_k=10
))
pipe.add_component("embedder", OpenAITextEmbedder())
pipe.add_component("embedding", InMemoryEmbeddingRetriever(
    document_store=doc_store, top_k=10
))
pipe.add_component("joiner", DocumentJoiner(
    join_mode="reciprocal_rank_fusion"
))

pipe.connect("embedder.embedding", "embedding.query_embedding")
pipe.connect("bm25.documents", "joiner.documents")
pipe.connect("embedding.documents", "joiner.documents")

result = pipe.run({
    "bm25": {"query": "transformer architecture"},
    "embedder": {"text": "transformer architecture"},
})
```

### DocumentJoiner Modes

| Mode | Description |
|------|-------------|
| `concatenate` | Simply concatenate all documents |
| `merge` | Merge by document ID, average scores |
| `reciprocal_rank_fusion` | RRF scoring — recommended for hybrid |

## Multi-Query Retrieval

Expand a single query into multiple variations for broader coverage:

```python
from haystack.components.retrievers import MultiQueryTextRetriever

retriever = MultiQueryTextRetriever(
    retriever=InMemoryBM25Retriever(document_store=doc_store),
    query_expander=QueryExpander(
        chat_generator=OpenAIChatGenerator(),
        count=3,  # Generate 3 query variations
    ),
)
```

Also available: `MultiQueryEmbeddingRetriever` for embedding-based retrievers, and `MultiRetriever` for running multiple text retrievers in parallel.

## Specialized Retrievers

### SentenceWindowRetriever

Retrieves surrounding context around matched sentences:

```python
from haystack.components.retrievers import SentenceWindowRetriever

retriever = SentenceWindowRetriever(
    document_store=doc_store,
    window_size=3,  # 3 sentences before and after
)
```

### AutoMergingRetriever

Merges small chunks back into larger parent documents when enough child chunks match:

```python
from haystack.components.retrievers import AutoMergingRetriever

retriever = AutoMergingRetriever(
    document_store=doc_store,
    threshold=0.5,  # Merge if 50%+ of child chunks match
)
```

### FilterRetriever

Retrieves documents purely by metadata filters (no text search):

```python
from haystack.components.retrievers.in_memory import InMemoryFilterRetriever

retriever = InMemoryFilterRetriever(document_store=doc_store)
result = retriever.run(
    filters={"field": "meta.category", "operator": "==", "value": "science"}
)
```

## Filter Policy

Controls how init-time and runtime filters interact:

```python
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.components.retrievers import FilterPolicy

# REPLACE (default): runtime filters override init filters
retriever = InMemoryBM25Retriever(
    document_store=doc_store,
    filter_policy=FilterPolicy.REPLACE,
    filters={"field": "meta.type", "operator": "==", "value": "article"},
)

# MERGE: runtime filters combine with init filters
retriever = InMemoryBM25Retriever(
    document_store=doc_store,
    filter_policy=FilterPolicy.MERGE,
    filters={"field": "meta.type", "operator": "==", "value": "article"},
)
```

## Choosing a Retriever

| Scenario | Recommended Retriever |
|----------|----------------------|
| Quick prototyping | `InMemoryBM25Retriever` |
| Exact keyword search | BM25 (Elasticsearch, OpenSearch) |
| Semantic search | Embedding retriever (Qdrant, Pinecone, Weaviate) |
| Production hybrid | BM25 + Embedding with `DocumentJoiner(join_mode="reciprocal_rank_fusion")` |
| Large-scale metadata filtering | Filter retriever + document store with good filter support |
| Context-aware retrieval | `SentenceWindowRetriever` or `AutoMergingRetriever` |

## Common Pitfalls

**Mismatched embeddings**: The document embedder and text embedder must use the same model. If documents are embedded with `text-embedding-3-small`, queries must use the same model.

**Missing embeddings in documents**: Embedding retrievers require documents to have embeddings. Run a `DocumentEmbedder` in your indexing pipeline before writing to the store.

**top_k too low**: Default is often 10. For complex queries or when using a ranker downstream, retrieve more (e.g., 50-100) then re-rank.

**Not using filters**: Filters dramatically improve precision when metadata is available. Always filter by document type, date range, or category when applicable.

## Related Topics

- Document Stores → `07-document-stores.md`
- Embedders → `08-embedders.md`
- RAG patterns → `11-rag-patterns.md`
