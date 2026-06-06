# Indexing

> Source: [developers.llamaindex.ai — Indexing](https://developers.llamaindex.ai/python/framework/module_guides/indexing/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [VectorStoreIndex](#vectorstoreindex)
- [SummaryIndex](#summaryindex)
- [TreeIndex](#treeindex)
- [KeywordTableIndex](#keywordtableindex)
- [PropertyGraphIndex](#propertygraphindex)
- [Index Selection Guide](#index-selection-guide)
- [Document Management](#document-management)
- [Metadata Filtering](#metadata-filtering)
- [Performance Tuning](#performance-tuning)

## Overview

An Index is a data structure built from Documents/Nodes that enables efficient retrieval. The index converts raw content into a queryable format — typically vector embeddings for semantic search.

```
Documents → Node Parser → Nodes → Embedding Model → Index (Vector Store)
```

LlamaIndex provides multiple index types optimized for different retrieval patterns.

## VectorStoreIndex

The most commonly used index. Stores nodes as vector embeddings and retrieves by semantic similarity.

### From Documents

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(documents)
```

This automatically:
1. Splits documents into nodes using the default `SentenceSplitter`
2. Generates embeddings for each node
3. Stores nodes and embeddings in memory

### From Nodes

```python
from llama_index.core.schema import TextNode

nodes = [
    TextNode(text="First chunk of text.", id_="node-1"),
    TextNode(text="Second chunk of text.", id_="node-2"),
]
index = VectorStoreIndex(nodes=nodes)
```

### Using a Custom Embedding Model

```python
from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
index = VectorStoreIndex.from_documents(documents)
```

### With External Vector Store

```python
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone

pc = Pinecone(api_key="...")
pinecone_index = pc.Index("my-index")

vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
)
```

### Querying

```python
query_engine = index.as_query_engine(similarity_top_k=5)
response = query_engine.query("What is the main finding?")

retriever = index.as_retriever(similarity_top_k=10)
nodes = retriever.retrieve("relevant context")
```

## SummaryIndex

Stores all nodes and returns ALL of them during retrieval (no embedding needed). Useful when you want the LLM to consider all documents.

```python
from llama_index.core import SummaryIndex

index = SummaryIndex.from_documents(documents)
query_engine = index.as_query_engine(
    response_mode="tree_summarize"
)
response = query_engine.query("Summarize the key points.")
```

Best for: summarization tasks, small document sets, when all context is needed.

## TreeIndex

Builds a hierarchical tree of summaries from bottom up. Queries traverse the tree to find relevant branches.

```python
from llama_index.core import TreeIndex

index = TreeIndex.from_documents(documents)
query_engine = index.as_query_engine(
    child_branch_factor=2,
)
```

Best for: hierarchical summarization, large document sets where only parts are relevant.

## KeywordTableIndex

Extracts keywords from nodes and builds a keyword-to-node mapping for keyword-based retrieval.

```python
from llama_index.core import KeywordTableIndex

index = KeywordTableIndex.from_documents(documents)
query_engine = index.as_query_engine()
```

Best for: keyword search, when semantic similarity is not needed, structured data.

## PropertyGraphIndex

Builds a knowledge graph with entities and relationships extracted from documents.

```python
from llama_index.core.indices.property_graph import PropertyGraphIndex

index = PropertyGraphIndex.from_documents(documents)
query_engine = index.as_query_engine()
```

Best for: entity relationship queries, knowledge graph construction, graph-based reasoning.

## Index Selection Guide

| Index Type | Retrieval Method | Embedding Required | Best For |
|------------|-----------------|-------------------|----------|
| `VectorStoreIndex` | Semantic similarity | Yes | General-purpose RAG, semantic search |
| `SummaryIndex` | Return all nodes | No | Summarization, small doc sets |
| `TreeIndex` | Tree traversal | Partial | Hierarchical summarization |
| `KeywordTableIndex` | Keyword matching | No | Keyword-based lookup |
| `PropertyGraphIndex` | Graph traversal | Optional | Entity/relationship queries |
| `LlamaCloudIndex` | Managed service | Managed | Enterprise, managed RAG |

**Default recommendation:** Start with `VectorStoreIndex` — it handles most use cases well.

## Document Management

Indexes support insert, delete, update, and refresh operations:

### Insert New Documents

```python
index.insert(new_document)

new_nodes = [TextNode(text="New content", id_="new-1")]
index.insert_nodes(new_nodes)
```

### Delete Documents

```python
index.delete_ref_doc("doc-id-to-remove", delete_from_docstore=True)
```

### Refresh (Upsert Changed Documents)

```python
refreshed_docs = index.refresh_ref_docs(documents)
```

`refresh_ref_docs` compares document hashes and only re-processes changed documents, avoiding redundant embedding calls.

### Update Documents

```python
index.update_ref_doc(updated_document)
```

## Metadata Filtering

Filter retrieval results based on document metadata:

```python
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

filters = MetadataFilters(
    filters=[
        MetadataFilter(key="category", value="research", operator=FilterOperator.EQ),
        MetadataFilter(key="year", value=2024, operator=FilterOperator.GTE),
    ]
)

query_engine = index.as_query_engine(
    similarity_top_k=5,
    filters=filters,
)
```

Supported operators: `EQ`, `NE`, `GT`, `GTE`, `LT`, `LTE`, `IN`, `NIN`, `CONTAINS`, `TEXT_MATCH`.

Metadata filtering availability depends on the vector store backend.

## Performance Tuning

### Batch Insertion

```python
index = VectorStoreIndex.from_documents(
    documents,
    insert_batch_size=1024,
    show_progress=True,
)
```

Default batch size is 2048 nodes. Lower for rate-limited APIs.

### Chunk Size and Overlap

```python
from llama_index.core import Settings
Settings.chunk_size = 512
Settings.chunk_overlap = 50
```

Smaller chunks improve precision but may lose context. Larger chunks preserve context but reduce specificity.

### Composable Indexes

Create an index over other indexes for multi-level retrieval:

```python
from llama_index.core.schema import IndexNode

sub_engine = sub_index.as_query_engine()
index_node = IndexNode(
    text="Description of sub-index content",
    obj=sub_engine,
    index_id="sub-index-1",
)
top_index = VectorStoreIndex(nodes=other_nodes, objects=[index_node])
```

When the `IndexNode` is retrieved, its embedded query engine is automatically executed.
