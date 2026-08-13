---
name: chroma
description: "Open-source AI-native vector database for embedding storage, similarity search, and retrieval. MANDATORY TRIGGERS: chroma, chromadb, chroma-core, ChromaClient, vector database python, embedding database. Also trigger when the user wants to store and query embeddings, build RAG pipelines with vector search, add semantic search to AI applications, or use a lightweight vector store for prototyping and production. When in doubt about whether to use this skill for vector database or embedding storage tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["vector-database", "embeddings", "ai", "rag", "semantic-search", "python"]
---

# Chroma

> Source: [docs.trychroma.com](https://docs.trychroma.com) — chromadb v1.5.9

## Reference Files

| File | Read When |
|------|-----------|
| `references/00-overview.md` | Starting with Chroma, need installation, architecture overview, or deciding if Chroma fits your use case |
| `references/01-clients.md` | Choosing a client type (Ephemeral, Persistent, HttpClient, CloudClient) or configuring connections |
| `references/02-collections.md` | Creating, listing, modifying, or deleting collections; configuring HNSW or distance functions |
| `references/03-data-operations.md` | Adding, updating, upserting, or deleting documents and embeddings in a collection |
| `references/04-querying.md` | Running similarity queries, fetching by ID, pagination, or understanding result formats |
| `references/05-metadata-filtering.md` | Filtering results by metadata fields, using comparison/logical operators, or where_document |
| `references/06-embedding-functions.md` | Choosing or configuring embedding providers (OpenAI, Cohere, HuggingFace, custom) |
| `references/07-full-text-search.md` | Using full-text search, regex matching, or combining text filters with vector search |
| `references/08-multimodal.md` | Storing and querying images alongside text, using OpenCLIP or data loaders |
| `references/09-deployment.md` | Running Chroma as client-server, Docker, or deploying to AWS/Azure/GCP |
| `references/10-chroma-cloud.md` | Using Chroma Cloud, the Search API, hybrid search with RRF, or collection forking |
| `references/11-integrations.md` | Integrating Chroma with LangChain, LlamaIndex, Haystack, MCP, or other AI frameworks |
| `references/12-performance.md` | Tuning HNSW parameters, optimizing queries, managing cold storage, or scaling |

## Installation

```bash
pip install chromadb          # Python (full)
pip install chromadb-client   # Python (thin HTTP client)
npm install chromadb          # TypeScript
cargo add chroma              # Rust
```

## Quick Reference

- [Official Docs](https://docs.trychroma.com)
- [GitHub](https://github.com/chroma-core/chroma)
- [PyPI](https://pypi.org/project/chromadb/)
- [Chroma Cloud](https://trychroma.com/signup)
- [Cookbook](https://cookbook.chromadb.dev/)
