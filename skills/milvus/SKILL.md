---
name: milvus
description: "High-performance cloud-native vector database for scalable AI applications. MANDATORY TRIGGERS: milvus, pymilvus, milvus-lite, zilliz, vector database, vector search, ANN search, similarity search, embedding storage. Also trigger when user wants to store and query vector embeddings at scale, build RAG retrieval pipelines with Milvus, implement hybrid sparse-dense search, set up full-text BM25 search alongside vectors, configure multi-tenancy for vector workloads, or deploy a distributed vector database on Kubernetes. When in doubt about whether to use this skill for vector database tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["milvus", "vector-database", "similarity-search", "embeddings", "rag", "hybrid-search", "bm25", "kubernetes"]
---

# Milvus — Skill Router

> Cloud-native vector database built for billion-scale ANN search with hybrid retrieval, full-text BM25, and multi-tenancy.

**Source:** [milvus.io](https://milvus.io/docs) v3.0-beta | **Package:** `pymilvus` | **License:** Apache 2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, architecture, installation, Milvus Lite, quickstart |
| **Schema Design** | `references/01-schema-design.md` | Field types, primary keys, vector fields, dynamic fields, nullable, defaults |
| **Collections** | `references/02-collections.md` | Create/manage collections, aliases, load/release, consistency levels, shards |
| **Data Operations** | `references/03-data-operations.md` | Insert, upsert, delete, batch ops, dynamic fields, partitioned inserts |
| **Indexing** | `references/04-indexing.md` | HNSW, IVF_FLAT, IVF_PQ, DiskANN, GPU indexes, index parameters, metrics |
| **Vector Search** | `references/05-vector-search.md` | ANN search, bulk search, filtered search, pagination, output fields, range search |
| **Hybrid Search** | `references/06-hybrid-search.md` | Multi-vector search, RRF reranker, weighted reranker, sparse+dense fusion |
| **Full-Text Search** | `references/07-full-text-search.md` | BM25, text analyzers, sparse vectors, keyword search alongside semantic |
| **Filtering** | `references/08-filtering.md` | Boolean expressions, comparison, logical, LIKE, IN, JSON/Array operators |
| **Partitions & Tenancy** | `references/09-partitions-tenancy.md` | Partitions, partition keys, multi-tenancy strategies, tenant isolation |
| **Security & RBAC** | `references/10-security.md` | Users, roles, privileges, TLS encryption, authentication |
| **Integrations** | `references/11-integrations.md` | LangChain, LlamaIndex, embedding models, RAG pipelines |
| **Deployment** | `references/12-deployment.md` | Milvus Lite, Docker Standalone, Kubernetes Distributed, Zilliz Cloud |

## Installation

```bash
# Python client (includes Milvus Lite for local dev)
pip install -U "pymilvus[milvus-lite]"

# Docker Standalone
wget https://github.com/milvus-io/milvus/releases/download/v3.0-beta/milvus-standalone-docker-compose.yml -O docker-compose.yml
docker compose up -d
```

## Quick Reference

- **Docs:** https://milvus.io/docs
- **GitHub:** https://github.com/milvus-io/milvus
- **PyPI:** https://pypi.org/project/pymilvus/
- **Web UI:** http://localhost:9091/webui/
