# Chroma — Overview

> Source: [docs.trychroma.com](https://docs.trychroma.com) | chromadb v1.5.9

## Table of Contents

- [What Is Chroma](#what-is-chroma)
- [When to Use Chroma](#when-to-use-chroma)
- [Core Capabilities](#core-capabilities)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Deployment Modes](#deployment-modes)
- [SDK Support](#sdk-support)
- [Related Topics](#related-topics)

## What Is Chroma

Chroma is the open-source data infrastructure for AI. It provides an embedding database with built-in retrieval, supporting dense vector search, full-text search, regex matching, and metadata filtering. Chroma is licensed under Apache 2.0 and has 27K+ GitHub stars with 15M+ monthly downloads.

Chroma is designed to be the simplest possible way to build AI applications that need vector storage and retrieval, with a four-function core API: create a collection, add documents, query, and get results.

## When to Use Chroma

**Good fit:**
- RAG (Retrieval-Augmented Generation) pipelines
- Semantic search over documents, code, or knowledge bases
- AI agent memory and context management
- Prototyping AI applications with minimal setup (runs in-process)
- Multi-modal search across text and images
- Production vector search with Chroma Cloud

**Consider alternatives when:**
- You need a general-purpose database with vector support (use PostgreSQL + pgvector)
- You need billion-scale vector search with strict latency SLAs (evaluate Milvus or Qdrant)
- You only need keyword search without vector capabilities (use Elasticsearch)

## Core Capabilities

| Capability | Description |
|------------|-------------|
| **Vector Search** | Dense KNN similarity search using HNSW index |
| **Full-Text Search** | Case-sensitive text matching with `$contains` |
| **Regex Search** | Pattern matching with `$regex` operator |
| **Metadata Filtering** | Filter by metadata fields with comparison/logical operators |
| **Multi-Modal** | Index and query text and images via OpenCLIP |
| **Auto-Embedding** | Built-in sentence-transformers; plug in OpenAI, Cohere, etc. |
| **Hybrid Search** | Combine dense + sparse vectors with RRF (Cloud) |
| **Collection Forking** | Branch collections for experimentation (Cloud) |

## Architecture

**Single-Node (Self-Hosted):**
- HNSW (Hierarchical Navigable Small World) index for approximate nearest neighbor search
- SQLite for metadata storage
- Runs embedded in-process or as a standalone HTTP server
- Supports persistent storage to local disk

**Distributed (Chroma Cloud):**
- SPANN (Spatial Approximate Nearest Neighbors) index
- Serverless, auto-scaling architecture
- Separate compute and storage layers
- SOC 2 Type II certified

## Installation

### Python

```bash
# Full package (includes embedded server)
pip install chromadb

# Thin client (HTTP only, minimal dependencies)
pip install chromadb-client
```

### TypeScript

```bash
npm install chromadb @chroma-core/default-embed
```

### Rust

```bash
cargo add chroma
```

### CLI

```bash
pip install chromadb
chroma run --path ./my-chroma-data
```

## Quick Start

### Python — In-Memory

```python
import chromadb

client = chromadb.Client()

collection = client.create_collection(name="docs")

collection.add(
    ids=["doc1", "doc2", "doc3"],
    documents=[
        "Chroma is an AI-native vector database",
        "It supports semantic search and filtering",
        "Embeddings are generated automatically",
    ],
    metadatas=[
        {"source": "readme", "page": 1},
        {"source": "docs", "page": 5},
        {"source": "tutorial", "page": 2},
    ],
)

results = collection.query(
    query_texts=["vector database for AI"],
    n_results=2,
)

print(results["documents"])
print(results["distances"])
```

### Python — Persistent Storage

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma-data")

collection = client.get_or_create_collection(name="docs")
collection.add(
    ids=["doc1"],
    documents=["This persists to disk automatically"],
)
```

### TypeScript

```typescript
import { ChromaClient } from "chromadb";

const client = new ChromaClient();

const collection = await client.createCollection({
  name: "docs",
});

await collection.add({
  ids: ["doc1", "doc2"],
  documents: [
    "Chroma is an AI-native vector database",
    "It supports semantic search and filtering",
  ],
});

const results = await collection.query({
  queryTexts: ["vector database for AI"],
  nResults: 2,
});
```

## Deployment Modes

| Mode | Client | Use Case |
|------|--------|----------|
| **In-Memory** | `chromadb.Client()` | Unit tests, experiments |
| **Persistent** | `chromadb.PersistentClient(path=...)` | Local dev, small apps |
| **Client-Server** | `chromadb.HttpClient(host=..., port=...)` | Multi-process, team sharing |
| **Docker** | `docker run chromadb/chroma` | Production self-hosted |
| **Chroma Cloud** | `chromadb.CloudClient(...)` | Managed, serverless production |

## SDK Support

| Language | Package | Status |
|----------|---------|--------|
| Python | `chromadb` / `chromadb-client` | Full support (sync + async) |
| TypeScript | `chromadb` | Full support |
| Rust | `chroma` | Full support |
| Kotlin | Community | Reference available |
| Swift | Community | Reference available |

## Related Topics

- `references/01-clients.md` — Client types and configuration
- `references/02-collections.md` — Collection management
- `references/06-embedding-functions.md` — Embedding provider setup
- `references/09-deployment.md` — Deployment guides
