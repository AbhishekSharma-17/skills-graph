# Changelog — Weaviate Skill

## [1.0.0] — 2026-06-03

**Source version tracked:** Weaviate v1.37 (v1.37.7)

### Added
- **00-overview.md** — Architecture, installation (Docker/Cloud/Embedded), client setup (Python/TS), quickstart
- **01-collections.md** — Collection CRUD, property data types, auto-schema, nested objects, naming conventions
- **02-vector-config.md** — HNSW/flat/dynamic indexes, distance metrics, PQ/BQ/SQ quantization, named vectors, multi-vectors
- **03-data-operations.md** — Insert, batch import (dynamic/fixed/rate-limited), read, update, delete, custom vectors, cross-references
- **04-similarity-search.md** — near_text, near_vector, near_object, near_image, MMR diversity search, distance thresholds
- **05-keyword-search.md** — BM25 search, AND/OR operators, property boosting, tokenization modes, fuzzy matching
- **06-hybrid-search.md** — Combined vector+keyword search, alpha parameter, fusion algorithms, concept steering
- **07-filters.md** — Filter operators, combining (AND/OR/NOT), nested filters, metadata filters, cross-reference filters, geo filters
- **08-rag.md** — Generative search, single prompt, grouped task, multimodal RAG, provider override, debug mode
- **09-reranking-aggregation.md** — Reranker models, aggregation queries (count, sum, avg, groupBy), search-based aggregation
- **10-multi-tenancy.md** — Tenant isolation, activity states (active/inactive/offloaded), auto-creation, CRUD with tenants
- **11-model-providers.md** — OpenAI, Cohere, Google, Anthropic, AWS, Ollama, HuggingFace, Voyage AI, Jina, NVIDIA integrations
- **12-agents.md** — Query Agent (ask/search modes, conversations), Transformation Agent (append/update), Personalization Agent

### Stats
- Routing entries: 13
- Reference files: 13
- Total lines: ~4,500
