---
name: qdrant
description: "High-performance vector search engine built in Rust for AI applications. MANDATORY TRIGGERS: qdrant, qdrant-client, vector search, vector database, similarity search, nearest neighbor search, ANN search, embedding search. Also trigger when user wants to store and query embeddings, build RAG retrieval pipelines, implement hybrid sparse+dense search, set up multitenancy for vector data, configure HNSW indexing or quantization, or manage vector collections. When in doubt about whether to use this skill for vector search tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["qdrant", "vector-database", "similarity-search", "embeddings", "hnsw", "rag", "hybrid-search", "rust"]
---

# Qdrant — Skill Router

> AI-native vector similarity search engine written in Rust with rich filtering, hybrid queries, and quantization.

**Source:** [qdrant.tech](https://qdrant.tech/documentation/) v1.17.1 | **Package:** `qdrant-client` (Python) | **License:** Apache 2.0

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, architecture, client initialization, quickstart |
| **Collections** | `references/01-collections.md` | Creating/managing collections, vector config, named vectors, aliases, distance metrics |
| **Points** | `references/02-points.md` | Upserting vectors, payloads, batch operations, scroll, delete, update payload |
| **Search & Query API** | `references/03-search-query.md` | Similarity search, query_points, search params, grouping, scoring |
| **Filtering** | `references/04-filtering.md` | Payload filters, match, range, geo, nested, boolean clauses, special conditions |
| **Indexing** | `references/05-indexing.md` | Payload indexes, HNSW config, full-text search, tenant/principal indexes |
| **Quantization** | `references/06-quantization.md` | Scalar, binary, product quantization, memory optimization, search tuning |
| **Hybrid Search** | `references/07-hybrid-search.md` | Sparse+dense fusion, prefetch, RRF, DBSF, multi-stage retrieval |
| **Recommendation & Discovery** | `references/08-recommendation.md` | Recommend API, positive/negative examples, discovery search, context pairs |
| **Optimizer & Performance** | `references/09-optimizer.md` | Optimizer config, bulk upload, memmap, segment management, monitoring |
| **Snapshots & Backups** | `references/10-snapshots.md` | Create/restore snapshots, S3 storage, full storage snapshots, recovery |
| **Multitenancy** | `references/11-multitenancy.md` | Tenant isolation, tenant indexes, tiered multitenancy, best practices |
| **Deployment** | `references/12-deployment.md` | Docker, Kubernetes, distributed mode, Qdrant Cloud, configuration |

## Installation

```bash
# Python client
pip install qdrant-client
pip install 'qdrant-client[fastembed]'  # with local embeddings

# Docker (primary development method)
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant
```

## Quick Reference

- **Docs:** https://qdrant.tech/documentation/
- **GitHub:** https://github.com/qdrant/qdrant
- **PyPI:** https://pypi.org/project/qdrant-client/
- **REST API:** http://localhost:6333/dashboard
