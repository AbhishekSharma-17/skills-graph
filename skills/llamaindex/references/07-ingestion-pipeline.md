# Ingestion Pipeline

> Source: [developers.llamaindex.ai — Ingestion Pipeline](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [Basic Pipeline](#basic-pipeline)
- [Transformations](#transformations)
- [Vector Store Integration](#vector-store-integration)
- [Caching](#caching)
- [Document Management](#document-management)
- [Parallel Processing](#parallel-processing)
- [Async Support](#async-support)
- [Common Patterns](#common-patterns)

## Overview

The `IngestionPipeline` provides a repeatable, cache-optimized workflow for processing documents into nodes. It applies a sequence of transformations and caches each node+transformation pair to avoid redundant computation on subsequent runs.

```
Documents → [Splitter → Extractor → Embedder] → Nodes → Vector Store
```

## Basic Pipeline

```python
from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor
from llama_index.embeddings.openai import OpenAIEmbedding

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=50),
        TitleExtractor(nodes=5),
        OpenAIEmbedding(),
    ]
)

documents = [Document(text="Your document content here...")]
nodes = pipeline.run(documents=documents)
```

Each transformation is applied sequentially. The output of one transformation feeds into the next.

## Transformations

### Text Splitters

Split documents into smaller chunks:

```python
from llama_index.core.node_parser import (
    SentenceSplitter,
    TokenTextSplitter,
    MarkdownNodeParser,
    HTMLNodeParser,
    CodeSplitter,
    SentenceWindowNodeParser,
    HierarchicalNodeParser,
)

# Sentence-aware splitting (recommended default)
SentenceSplitter(chunk_size=1024, chunk_overlap=20)

# Fixed token-length splitting
TokenTextSplitter(chunk_size=1024, chunk_overlap=20, separator=" ")

# Markdown header-aware splitting
MarkdownNodeParser()

# Code-aware splitting
CodeSplitter(language="python", chunk_lines=40, chunk_lines_overlap=15)

# Window-based splitting for auto-merging retrieval
SentenceWindowNodeParser(
    window_size=3,
    window_metadata_key="window",
    original_text_metadata_key="original_text",
)

# Hierarchical splitting for recursive retrieval
HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128])
```

### Metadata Extractors

Automatically extract metadata from node content:

```python
from llama_index.core.extractors import (
    TitleExtractor,
    SummaryExtractor,
    QuestionsAnsweredExtractor,
    KeywordExtractor,
)

# Extract document titles
TitleExtractor(nodes=5)

# Generate per-node summaries
SummaryExtractor(summaries=["self"])

# Generate questions each node can answer
QuestionsAnsweredExtractor(questions=3)

# Extract keywords
KeywordExtractor(keywords=10)
```

### Embedding Models

Generate vector embeddings as the final transformation:

```python
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# OpenAI embeddings
OpenAIEmbedding(model="text-embedding-3-small")

# Local HuggingFace embeddings
HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
```

### Custom Transformations

Create custom transformations by extending `TransformComponent`:

```python
from llama_index.core.ingestion import TransformComponent
from llama_index.core.schema import BaseNode

class CustomTransform(TransformComponent):
    def __call__(self, nodes: list[BaseNode], **kwargs) -> list[BaseNode]:
        for node in nodes:
            node.metadata["custom_field"] = "processed"
            node.text = node.text.lower()
        return nodes

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(),
        CustomTransform(),
        OpenAIEmbedding(),
    ]
)
```

## Vector Store Integration

Connect the pipeline directly to a vector store for automatic storage:

```python
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

client = qdrant_client.QdrantClient(location=":memory:")
vector_store = QdrantVectorStore(client=client, collection_name="docs")

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512),
        OpenAIEmbedding(),
    ],
    vector_store=vector_store,
)

pipeline.run(documents=documents)

# Build index from the populated vector store
from llama_index.core import VectorStoreIndex, StorageContext

storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(
    vector_store, storage_context=storage_context
)
```

When a vector store is attached, embeddings are required in the pipeline transformations.

### Supported Vector Stores

Pinecone, Qdrant, Weaviate, Chroma, Milvus, Elasticsearch, MongoDB Atlas, PGVector, LanceDB, Faiss, and 100+ more.

## Caching

### Local Cache (Disk)

```python
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(),
        OpenAIEmbedding(),
    ]
)

# First run processes everything
nodes = pipeline.run(documents=documents)

# Persist cache to disk
pipeline.persist("./pipeline_cache")

# Later: load cache and skip already-processed nodes
new_pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(),
        OpenAIEmbedding(),
    ]
)
new_pipeline.load("./pipeline_cache")
nodes = new_pipeline.run(documents=documents)  # Cached nodes returned instantly
```

### Remote Cache (Redis)

```python
from llama_index.core.ingestion import IngestionCache
from llama_index.storage.kvstore.redis import RedisKVStore as RedisCache

cache = IngestionCache(
    cache=RedisCache.from_host_and_port(host="127.0.0.1", port=6379),
    collection="my_cache",
)

pipeline = IngestionPipeline(
    transformations=[...],
    cache=cache,
)
```

### Other Cache Backends

```python
from llama_index.storage.kvstore.mongodb import MongoDBKVStore as MongoCache
from llama_index.storage.kvstore.firestore import FirestoreKVStore as FirestoreCache

# MongoDB cache
cache = IngestionCache(
    cache=MongoCache.from_uri(uri="mongodb://localhost:27017"),
    collection="pipeline_cache",
)

# Firestore cache
cache = IngestionCache(
    cache=FirestoreCache(),
    collection="pipeline_cache",
)
```

Caching works by hashing each node+transformation pair. On re-run, unchanged pairs return cached results, saving embedding API costs.

## Document Management

Track documents and detect duplicates using a document store:

```python
from llama_index.core.storage.docstore import SimpleDocumentStore

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(),
        OpenAIEmbedding(),
    ],
    docstore=SimpleDocumentStore(),
    vector_store=vector_store,
)

# First run: all documents processed
pipeline.run(documents=documents)

# Second run with same + new documents: only new ones processed
pipeline.run(documents=documents + new_documents)
```

The docstore tracks `doc_id` and document hashes. On re-run, it:
- Skips unchanged documents
- Re-processes changed documents (upserts to vector store)
- Does not remove deleted documents (handle manually)

## Parallel Processing

Distribute processing across CPU cores:

```python
nodes = pipeline.run(
    documents=documents,
    num_workers=4,
)
```

`num_workers` uses `multiprocessing.Pool` to distribute node batches across processors. Useful for CPU-intensive transformations like local embedding generation.

## Async Support

```python
nodes = await pipeline.arun(documents=documents)
```

Full async pipeline execution for non-blocking I/O operations.

## Common Patterns

### Production Ingestion Pipeline

```python
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor, KeywordExtractor
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.vector_stores.qdrant import QdrantVectorStore

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=50),
        TitleExtractor(nodes=3),
        KeywordExtractor(keywords=5),
        OpenAIEmbedding(model="text-embedding-3-small"),
    ],
    vector_store=vector_store,
    docstore=SimpleDocumentStore(),
)

nodes = pipeline.run(
    documents=documents,
    show_progress=True,
    num_workers=4,
)
```

### Incremental Ingestion

```python
# Process new documents without reprocessing existing ones
pipeline = IngestionPipeline(
    transformations=[...],
    vector_store=existing_vector_store,
    docstore=existing_docstore,
)

# Only new/changed documents are processed
pipeline.run(documents=all_documents)
```

### Embedding-Only Pipeline

```python
pipeline = IngestionPipeline(
    transformations=[
        OpenAIEmbedding(),
    ]
)
# Nodes already exist, just need embeddings
nodes = pipeline.run(nodes=existing_nodes)
```
