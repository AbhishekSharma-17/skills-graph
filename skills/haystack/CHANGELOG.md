# Changelog

## [1.0.0] — 2026-06-04

Source version tracked: haystack-ai 2.30.0

### Added

- **00-overview.md** — Framework introduction, architecture, installation, first RAG pipeline, first agent
- **01-components.md** — Component protocol, custom components, @component decorator, lifecycle, serialization
- **02-pipelines.md** — Pipeline creation, connecting, branching, loops, async pipelines, serialization
- **03-agents.md** — Agent component, state management, streaming, human-in-the-loop, multi-agent, MCP
- **04-tools.md** — Tool class, @tool decorator, ComponentTool, PipelineTool, MCPTool, Toolset
- **05-generators.md** — Chat generators, 20+ providers (OpenAI, Anthropic, Ollama, etc.), streaming
- **06-retrievers.md** — BM25, embedding, hybrid, multi-query, specialized retrievers, filter policy
- **07-document-stores.md** — DocumentStore protocol, 15+ backends, filtering, DuplicatePolicy
- **08-embedders.md** — Text/document embedders, 20+ providers, indexing vs querying patterns
- **09-converters-preprocessors.md** — File converters (PDF, HTML, DOCX, etc.), DocumentSplitter, DocumentCleaner
- **10-prompt-building.md** — PromptBuilder, ChatPromptBuilder, Jinja2 templates, routers
- **11-rag-patterns.md** — End-to-end RAG, indexing pipeline, hybrid retrieval, self-correcting, conversational RAG
- **12-evaluation.md** — Faithfulness, context relevance, MRR, MAP, recall, SAS, LLM evaluator, Ragas/DeepEval

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,500
