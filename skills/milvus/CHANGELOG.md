# Changelog — milvus

## [1.0.0] — 2026-06-29

**Source version tracked:** Milvus 3.0-beta / pymilvus 3.0.0

### Added

- **00-overview.md** — Architecture, installation (Lite/Standalone/Distributed), quickstart, key concepts, consistency levels
- **01-schema-design.md** — Field types (vector, scalar, composite), primary keys, auto_id, nullable, defaults, dynamic fields, BM25 functions
- **02-collections.md** — Create/manage collections, aliases, load/release, consistency levels, shards, blue-green reindexing
- **03-data-operations.md** — Insert, upsert, delete, query, batch operations, bulk import, aggregation
- **04-indexing.md** — HNSW, IVF_FLAT, IVF_SQ8, IVF_PQ, DiskANN, GPU indexes, sparse indexes, scalar indexes, similarity metrics
- **05-vector-search.md** — ANN search, bulk search, filtered search, pagination, range search, grouping, order by, iterators
- **06-hybrid-search.md** — Multi-vector search, RRF reranker, weighted reranker, sparse+dense fusion, multi-modal patterns
- **07-full-text-search.md** — BM25 algorithm, text analyzers, sparse vector generation, hybrid BM25+dense retrieval
- **08-filtering.md** — Boolean expressions, comparison, logical, LIKE, IN, JSON/Array operators, precedence
- **09-partitions-tenancy.md** — Partitions, partition keys, four multi-tenancy strategies with trade-offs
- **10-security.md** — Users, roles, RBAC, privilege groups, TLS encryption, authentication
- **11-integrations.md** — LangChain, LlamaIndex, Haystack, embedding models (OpenAI, Sentence Transformers, Cohere)
- **12-deployment.md** — Milvus Lite, Docker Standalone, Kubernetes Distributed, Zilliz Cloud, environment portability

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,800
