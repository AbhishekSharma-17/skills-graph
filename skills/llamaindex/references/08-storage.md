# Storage

> Source: [developers.llamaindex.ai — Storing](https://developers.llamaindex.ai/python/framework/module_guides/storing/) | Version: 0.14.22

## Table of Contents
- [Overview](#overview)
- [StorageContext](#storagecontext)
- [Vector Stores](#vector-stores)
- [Document Stores](#document-stores)
- [Index Stores](#index-stores)
- [Local Persistence](#local-persistence)
- [Supported Vector Store Backends](#supported-vector-store-backends)
- [Common Patterns](#common-patterns)

## Overview

LlamaIndex provides swappable storage components for persisting:
- **Vector stores** — Embedding vectors for semantic search
- **Document stores** — Ingested Node objects
- **Index stores** — Index metadata and structure
- **Chat stores** — Conversation histories
- **Key-value stores** — Foundation for document and index stores

```
StorageContext
├── Vector Store (embeddings)
├── Document Store (nodes)
├── Index Store (index metadata)
└── Key-Value Store (foundation layer)
```

## StorageContext

`StorageContext` is the configuration object that bundles all storage backends:

```python
from llama_index.core import StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore

# Default (in-memory)
storage_context = StorageContext.from_defaults()

# Custom backends
storage_context = StorageContext.from_defaults(
    docstore=SimpleDocumentStore(),
    vector_store=SimpleVectorStore(),
    index_store=SimpleIndexStore(),
)
```

Pass it to index construction:

```python
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
)
```

## Vector Stores

Vector stores hold embedding vectors and support similarity search. This is the most critical storage component for RAG applications.

### In-Memory (Default)

```python
from llama_index.core.vector_stores import SimpleVectorStore

vector_store = SimpleVectorStore()
```

Data is lost when the process exits unless explicitly persisted to disk.

### Pinecone

```python
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone

pc = Pinecone(api_key="your-key")
pinecone_index = pc.Index("my-index")

vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

### Qdrant

```python
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

client = qdrant_client.QdrantClient(
    url="http://localhost:6333",
    api_key="your-key",
)

vector_store = QdrantVectorStore(
    client=client,
    collection_name="my_collection",
)
```

### Chroma

```python
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_or_create_collection("my_collection")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
```

### Weaviate

```python
from llama_index.vector_stores.weaviate import WeaviateVectorStore
import weaviate

client = weaviate.connect_to_local()

vector_store = WeaviateVectorStore(
    weaviate_client=client,
    index_name="MyIndex",
)
```

### PGVector (PostgreSQL)

```python
from llama_index.vector_stores.postgres import PGVectorStore

vector_store = PGVectorStore.from_params(
    database="vectordb",
    host="localhost",
    password="password",
    port=5432,
    user="user",
    table_name="embeddings",
    embed_dim=1536,
)
```

### Loading from Existing Vector Store

When your data is already in a vector store, skip ingestion and create the index directly:

```python
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
index = VectorStoreIndex.from_vector_store(vector_store)
```

## Document Stores

Document stores persist the original Node objects (text + metadata):

```python
from llama_index.core.storage.docstore import SimpleDocumentStore

docstore = SimpleDocumentStore()

storage_context = StorageContext.from_defaults(docstore=docstore)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
```

### MongoDB Document Store

```python
from llama_index.storage.docstore.mongodb import MongoDocumentStore

docstore = MongoDocumentStore.from_uri(
    uri="mongodb://localhost:27017",
    db_name="llama_index",
)
```

### Redis Document Store

```python
from llama_index.storage.docstore.redis import RedisDocumentStore

docstore = RedisDocumentStore.from_host_and_port(
    host="localhost",
    port=6379,
    namespace="llama_index",
)
```

Many vector stores handle both vectors and document storage together, making a separate docstore unnecessary.

## Index Stores

Index stores persist index metadata (structure, node references):

```python
from llama_index.core.storage.index_store import SimpleIndexStore

index_store = SimpleIndexStore()
storage_context = StorageContext.from_defaults(index_store=index_store)
```

## Local Persistence

### Save to Disk

```python
# After building the index
index.storage_context.persist(persist_dir="./storage")
```

### Load from Disk

```python
from llama_index.core import StorageContext, load_index_from_storage

storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
```

This saves/loads all components: vector store, docstore, and index store as JSON files in the specified directory.

### Files Created

```
./storage/
├── docstore.json          # Document store data
├── index_store.json       # Index metadata
├── vector_store.json      # Vector embeddings (SimpleVectorStore only)
├── image__vector_store.json  # Image embeddings (if applicable)
└── graph_store.json       # Graph store (if applicable)
```

### Cloud Storage

LlamaIndex uses `fsspec` for storage abstraction, supporting:

```python
# AWS S3
storage_context.persist(persist_dir="s3://my-bucket/storage/")

# Cloudflare R2
storage_context.persist(persist_dir="r2://my-bucket/storage/")
```

## Supported Vector Store Backends

| Store | Package | Managed | Free Tier |
|-------|---------|---------|-----------|
| Pinecone | `llama-index-vector-stores-pinecone` | Yes | Yes |
| Qdrant | `llama-index-vector-stores-qdrant` | Both | Yes |
| Weaviate | `llama-index-vector-stores-weaviate` | Both | Yes |
| Chroma | `llama-index-vector-stores-chroma` | Self-hosted | N/A |
| Milvus | `llama-index-vector-stores-milvus` | Both | Yes |
| PGVector | `llama-index-vector-stores-postgres` | Self-hosted | N/A |
| Elasticsearch | `llama-index-vector-stores-elasticsearch` | Both | Trial |
| MongoDB Atlas | `llama-index-vector-stores-mongodb` | Yes | Yes |
| Faiss | `llama-index-vector-stores-faiss` | Self-hosted | N/A |
| LanceDB | `llama-index-vector-stores-lancedb` | Both | Yes |
| Deep Lake | `llama-index-vector-stores-deeplake` | Both | Yes |
| Neo4j | `llama-index-vector-stores-neo4j` | Both | Yes |

100+ total vector store integrations available.

## Common Patterns

### Development → Production Migration

```python
# Development: in-memory with disk persistence
storage_context = StorageContext.from_defaults()
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
storage_context.persist("./dev_storage")

# Production: external vector store
from llama_index.vector_stores.pinecone import PineconeVectorStore

prod_vector_store = PineconeVectorStore(pinecone_index=prod_index)
prod_storage = StorageContext.from_defaults(vector_store=prod_vector_store)
prod_index = VectorStoreIndex.from_documents(documents, storage_context=prod_storage)
```

### Multiple Indexes, Shared Storage

```python
storage_context = StorageContext.from_defaults(persist_dir="./shared_storage")

index_1 = VectorStoreIndex.from_documents(docs_a, storage_context=storage_context)
index_2 = SummaryIndex.from_documents(docs_b, storage_context=storage_context)

storage_context.persist("./shared_storage")
```

### Checking If Storage Exists

```python
import os
from llama_index.core import StorageContext, load_index_from_storage, VectorStoreIndex

PERSIST_DIR = "./storage"

if os.path.exists(PERSIST_DIR):
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)
else:
    documents = SimpleDirectoryReader("./data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
```
