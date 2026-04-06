# Changelog — litellm skill

## [1.0.0] — 2026-04-06

Initial release. Tracks `litellm` Python package v1.52.x.

### Added
- `SKILL.md` router with 13 reference entries and MANDATORY TRIGGERS.
- `references/00-overview.md` — Install, SDK vs Proxy modes, quickstart.
- `references/01-completion-api.md` — `completion()` signature, params, response shape, errors.
- `references/02-providers.md` — Provider prefix table, Azure/Bedrock/Vertex/Anthropic/Ollama setup.
- `references/03-streaming.md` — Sync/async streaming, chunk shape, stream_chunk_builder, tool-call streaming.
- `references/04-async.md` — `acompletion`, gather, semaphores, batching, custom httpx clients.
- `references/05-router.md` — Routing strategies, model groups, fallbacks, cooldowns, Redis.
- `references/06-proxy-server.md` — config.yaml, virtual keys, fallbacks, admin endpoints, deployment.
- `references/07-fallbacks-retries.md` — Retry policies, fallbacks, context-window fallbacks, layering pitfalls.
- `references/08-caching.md` — In-memory, Redis, S3, semantic caching, TTL, cache controls.
- `references/09-observability.md` — Callbacks, Langfuse/OTEL/Prometheus, custom loggers, metadata.
- `references/10-cost-tracking.md` — completion_cost, token_counter, register_model, proxy budgets.
- `references/11-structured-outputs.md` — JSON mode, schema-strict, Pydantic, function calling.
- `references/12-embeddings.md` — embedding(), image_generation(), transcription, speech, moderation, rerank.
- `VERSION.json` with per-reference source page tracking.
- `AUDIT-REPORT.md` quality self-assessment.
- `scripts/check-updates.py` for upstream version + integrity checks.

### Stats
- Routing entries: 13
- Reference files: 13
- Total lines: ~1750
- Source version tracked: litellm 1.52.0
