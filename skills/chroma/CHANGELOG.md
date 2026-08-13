# Changelog — chroma

## [1.0.0] — 2026-08-13

Source version tracked: chromadb 1.5.9

### Added

- `references/00-overview.md` — What Chroma is, architecture, installation, quick start, deployment modes
- `references/01-clients.md` — Client types: Ephemeral, Persistent, HTTP, Async, Cloud, TypeScript, Rust
- `references/02-collections.md` — Collection management, HNSW configuration, distance functions, naming rules
- `references/03-data-operations.md` — add(), update(), upsert(), delete() with IDs, documents, embeddings, metadata
- `references/04-querying.md` — query(), get(), result format, include parameter, pagination, peek/count
- `references/05-metadata-filtering.md` — Where clauses, comparison/logical/array operators, where_document
- `references/06-embedding-functions.md` — Built-in, OpenAI, Cohere, HuggingFace, Ollama, custom functions
- `references/07-full-text-search.md` — $contains, $regex, combining text and vector search
- `references/08-multimodal.md` — OpenCLIP, image storage/querying, data loaders, cross-modal search
- `references/09-deployment.md` — CLI server, Docker, Docker Compose, AWS/Azure/GCP, thin client, env vars
- `references/10-chroma-cloud.md` — Cloud setup, Search API, K expressions, hybrid search with RRF, forking
- `references/11-integrations.md` — LangChain, LlamaIndex, Haystack, MCP, Streamlit, Mem0
- `references/12-performance.md` — HNSW tuning, batch operations, embedding strategy, scaling

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,400
