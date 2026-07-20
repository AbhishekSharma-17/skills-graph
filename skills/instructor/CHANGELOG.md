# Instructor Skill Changelog

## [1.0.0] — 2026-07-21

Source version tracked: instructor v1.15.4

### Added

- **00-overview.md** — What Instructor is, installation, architecture, supported providers, quick start patterns
- **01-core-usage.md** — from_provider API, response models, create method, async clients, context parameter
- **02-modes.md** — TOOLS, JSON, MD_JSON, TOOLS_STRICT, PARALLEL_TOOLS, RESPONSES_TOOLS, JSON_O1, provider support matrix
- **03-validation.md** — Field constraints, field/model validators, validation context, semantic validation, error handling
- **04-retries.md** — Built-in retries, tenacity integration, backoff strategies, error-specific retries, attempt tracking
- **05-streaming.md** — Partial streaming, iterable streaming, async streaming, PartialLiteralMixin, real-time UI patterns
- **06-providers.md** — OpenAI, Anthropic, Ollama, Google Gemini, LiteLLM setup and provider-specific features
- **07-multimodal.md** — Image, PDF, audio extraction, loading methods, provider compatibility, caching
- **08-hooks.md** — Event types, registration, error classification, hook composition, testing with hooks
- **09-classification.md** — Enum and Literal patterns, multi-label, union types, boolean classification, confidence scores
- **10-batch-processing.md** — BatchProcessor, file-based and in-memory batches, result handling, provider notes
- **11-async-patterns.md** — Async clients, gather/as_completed, rate limiting, FastAPI integration, worker pools
- **12-advanced-patterns.md** — Jinja templating, nested schemas, chain of thought, dynamic models, testing, production patterns

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,500
