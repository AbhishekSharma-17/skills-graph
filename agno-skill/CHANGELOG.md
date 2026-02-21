# Agno Skill Changelog

## [1.2.0] — 2026-02-21

**Agno version tracked: 2.5.3** | **Author: Abhishek Sharma**

### Changed (Skills Architecture Enhancements)
- **SKILL.md frontmatter** — Pushier description with explicit trigger keywords, added `license: MIT`, `metadata` block (version, author, tags), `compatibility` hints
- **Multi-platform install instructions** — Added Smithery CLI, Agno native `Skills`/`LocalSkills` loading, and manual install paths for 7 platforms (Claude Code, Antigravity, Gemini CLI, Cursor, Codex, Windsurf, GitHub Copilot)
- **SKILL.md version** bumped to 1.2.0

### Split (Large Files → Routers + Sub-files)
- **database.md** (766 lines) → router + `database/backends.md`, `database/chat-history.md`, `database/session-memory.md`
- **workflow-patterns.md** (762 lines) → router + `workflow-patterns/sequential-parallel.md`, `workflow-patterns/conditional-loop-router.md`, `workflow-patterns/advanced-patterns.md`
- **input-output.md** (700 lines) → router + `input-output/structured-io.md`, `input-output/multimodal.md`, `input-output/streaming-reference.md`
- **memory.md** (667 lines) → router + `memory/core-concepts.md`, `memory/tools-manager.md`, `memory/patterns-best-practices.md`

### Added
- **Table of Contents** — Added `## Contents` with anchor links to 12 files >300 lines: `workflows.md`, `agents.md`, `teams.md`, `context-mgmt/chat-history.md`, `context-mgmt/dependency-injection.md`, `context-mgmt/system-message.md`, `tools/advanced.md`, `guardrails/builtin-guardrails.md`, `guardrails/usage-examples.md`, `agentos/config-security.md`, `agentos/setup-api.md`, `hooks/agent-hooks.md`
- **AUDIT-REPORT.md** — Cross-platform compatibility audit, progressive disclosure analysis, exemplary skills comparison

### Stats
- 34 routing entries in SKILL.md
- 116 reference files (+13 from splits)
- ~23,431 total lines

---

## [1.1.0] — 2026-02-21

**Agno version tracked: 2.5.3**

### Added
- **AgentOS** — Full reference with router + 2 sub-files (setup-api.md, config-security.md) covering 50+ API endpoints, streaming, control plane, YAML/class config, RBAC/JWT, background hooks, custom lifespan
- **Deploy** — Templates (Docker, Railway, AWS ECS), pre-built solutions (Dash, Scout, Gcode), 10+ agent apps, team/workflow apps, 6 interfaces (Slack, Discord, WhatsApp, Telegram, MCP, AG-UI)
- **Database Providers** — All 18 backends with classes, imports, connection strings, Docker quick-start commands (Postgres, MySQL, SQLite, MongoDB, Redis, DynamoDB, Firestore, SurrealDB, Neon, Supabase, SingleStore, GCS, JSON, In-Memory + async variants)
- **Vector Store Providers** — All 14+ vector databases (PgVector, Chroma, LanceDB, Pinecone, Qdrant, Weaviate, Milvus, MongoDB Atlas, SingleStore, Cassandra, ClickHouse, Upstash, AstraDB)
- **Embedder Providers** — All 12+ embedding providers (OpenAI, Azure, Google, Voyage, Cohere, Mistral, Ollama, HuggingFace, Together, Fireworks, SentenceTransformer, FastEmbed)
- **FAQs** — 10 common troubleshooting topics (env vars, Workflow vs Team, structured outputs, TPM, model switching, AgentOS connection, Docker, JWT, TablePlus)
- **Models** — Model providers (40+), model-as-string syntax, retries, response caching, multimodal compatibility matrix, OpenAI-compatible (OpenAILike, OpenResponses)
- **Observability** — 12 third-party platforms (AgentOps, Arize, Atla, LangDB, Langfuse, LangSmith, Langtrace, LangWatch, Maxim, OpenLIT, Traceloop, Weave)
- **Integrations** — Discord bot, Memori memory layer
- **Migrations** — Database migrations (MigrationManager), Workflows 2.0 migration guide
- **Evals** — 4 eval types (accuracy, performance, reliability, agent-as-judge) with router + sub-files
- **Hooks** — Agent and team hooks with router + sub-files
- **Tracing** — Setup and querying with router + sub-files
- **Run Cancellation** — Agent/team/workflow cancel patterns
- **Culture** — Experimental shared knowledge layer
- **Custom Logging** — configure_agno_logging() and named loggers

### Added (Tooling)
- `VERSION.json` — Machine-readable version tracking with per-file metadata, docs sitemap snapshot
- `scripts/check-updates.py` — Update checker (PyPI version, docs sitemap diff, stale file detection, integrity check)
- `CHANGELOG.md` — This file

### Fixed
- **AgentOS broken reference** — SKILL.md pointed to `references/agentos.md` which didn't exist; now created with full content

### Stats
- 34 routing entries in SKILL.md
- 103 reference files
- ~22,800 total lines

---

## [1.0.0] — 2026-02-18

**Agno version tracked: 2.5.2**

### Added (Initial Build)
- **Agents** — Creating agents, tools, structured output, storage, memory, knowledge, state, streaming
- **Teams** — Multi-agent coordination, 4 team modes, delegation, nested teams
- **Workflows** — Pipeline orchestration with 8 pattern types
- **Workflow Patterns** — Full code examples for all patterns
- **Input / Output** — Structured I/O, multimodal, streaming, output/parser models
- **Database** — 8 storage backends with connection patterns
- **Memory** — Automatic + agentic memory, MemoryManager, MemoryTools
- **Knowledge** — RAG pipelines, 20+ vector DBs, embedders, readers, chunking, search
- **Learning** — Learning Machines, 6 stores, 3 modes, custom schemas
- **Skills & Tools** — Agno Skills architecture, tool overview
- **Tools (Deep Dive)** — @tool decorator, custom Toolkits, 120+ built-in toolkits
- **Reasoning** — 3 approaches (models, tools, agents), split models
- **Multimodal** — Image/audio/video input/generation, media classes
- **Context & Sessions** — Sessions, chat history, summaries, context engineering, persistence
- **State Management** — Agent/team/workflow state, agentic state, hooks
- **Context Management** — System messages, enrichment, compression, DI, few-shot, caching
- **Guardrails** — PII, prompt injection, content moderation, custom guardrails
- **Human-in-the-Loop** — User confirmation, input, dynamic input, external execution

### Stats
- 25 routing entries
- 87 reference files
- ~18,000 total lines
