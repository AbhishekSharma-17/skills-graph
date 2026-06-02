---
name: weaviate
description: "Open-source AI-native vector database for semantic search, hybrid search, RAG, and agent-driven workflows with multi-tenancy and model provider integrations. MANDATORY TRIGGERS: weaviate, Weaviate, weaviate-client, near_text, near_vector, hybrid search vector database, WeaviateClient, weaviate.connect, collections.create, query.near_text, query.hybrid, query.bm25. Also trigger when user wants to build semantic search, store vector embeddings, implement RAG pipelines, combine keyword and vector search, set up multi-tenant vector storage, use named vectors, or integrate vector DB with LLM providers. When in doubt about whether to use this skill for vector database or semantic search tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["weaviate", "vector-database", "semantic-search", "hybrid-search", "rag", "embeddings", "multi-tenancy", "agents", "reranking", "bm25"]
---

# Weaviate — Skill Router

> The AI-native vector database for semantic search, RAG, and intelligent agents.

**Source:** [weaviate.io](https://weaviate.io) | **Version:** v1.37 | **License:** BSD-3-Clause

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Setup** | `references/00-overview.md` | Getting started, installation, client setup, quickstart, architecture |
| **Collections & Schema** | `references/01-collections.md` | Creating collections, properties, data types, auto-schema, naming |
| **Vector Configuration** | `references/02-vector-config.md` | HNSW, flat, dynamic indexes, distance metrics, quantization, named vectors |
| **Data Operations** | `references/03-data-operations.md` | Insert, batch import, read, update, delete, custom vectors, cross-references |
| **Similarity Search** | `references/04-similarity-search.md` | near_text, near_vector, near_object, near_image, MMR diversity search |
| **Keyword Search** | `references/05-keyword-search.md` | BM25 search, property boosting, tokenization, AND/OR operators, fuzzy matching |
| **Hybrid Search** | `references/06-hybrid-search.md` | Combined vector+keyword, alpha parameter, fusion algorithms |
| **Filters** | `references/07-filters.md` | Filter operators, combining filters, nested, metadata, cross-reference filters |
| **RAG (Generative Search)** | `references/08-rag.md` | Single prompt, grouped task, multimodal RAG, provider configuration |
| **Reranking & Aggregation** | `references/09-reranking-aggregation.md` | Reranker models, aggregation queries, count, sum, groupBy |
| **Multi-Tenancy** | `references/10-multi-tenancy.md` | Tenant isolation, states, auto-creation, CRUD with tenants |
| **Model Providers** | `references/11-model-providers.md` | OpenAI, Cohere, Google, Anthropic, Ollama, HuggingFace integrations |
| **Weaviate Agents** | `references/12-agents.md` | Query Agent, Transformation Agent, natural language queries |

## Installation

```bash
# Python client
pip install -U weaviate-client

# TypeScript/JavaScript client
npm install weaviate-client

# Run Weaviate locally with Docker
docker run -d -p 8080:8080 -p 50051:50051 \
  cr.weaviate.io/semitechnologies/weaviate:1.37.7

# Or use Docker Compose (recommended)
# See references/00-overview.md for docker-compose.yml
```

## Quick Reference

- **Docs:** https://docs.weaviate.io/weaviate
- **GitHub:** https://github.com/weaviate/weaviate
- **PyPI:** https://pypi.org/project/weaviate-client/
- **npm:** https://www.npmjs.com/package/weaviate-client
- **Release Notes:** https://docs.weaviate.io/weaviate/release-notes
