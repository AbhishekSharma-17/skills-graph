# Changelog — dspy skill

All notable changes to this skill will be documented in this file.

## [1.0.0] — 2026-04-07

Initial release.

- **Source version tracked:** dspy 2.5.43
- **License:** MIT

### Added

- `SKILL.md` router with mandatory triggers for DSPy, Predict, ChainOfThought, ReAct, optimizers, and compile workflows.
- `references/00-overview.md` — install, core concepts, the compile loop, quickstart.
- `references/01-signatures.md` — inline and class-based signatures, Pydantic outputs, typing.
- `references/02-modules.md` — Predict, ChainOfThought, ProgramOfThought, ReAct, composing `dspy.Module`.
- `references/03-lm-configuration.md` — `dspy.LM`, providers, Ollama/vLLM, caching, async.
- `references/04-optimizers.md` — BootstrapFewShot, BootstrapFewShotWithRandomSearch, MIPROv2, COPRO, BootstrapFinetune.
- `references/05-metrics-evaluation.md` — metric functions, `dspy.Evaluate`, LLM-as-judge, error analysis.
- `references/06-rag-retrieval.md` — `dspy.Retrieve`, ColBERTv2, Qdrant/Chroma/Weaviate, multi-hop RAG.
- `references/07-assertions.md` — `dspy.Assert`, `dspy.Suggest`, backtracking, self-refinement.
- `references/08-deployment.md` — saving/loading, FastAPI, async, streaming, Langfuse/OTEL, containerisation.
- `VERSION.json` — maps every reference to its upstream source page and tracked version.
- `AUDIT-REPORT.md` — quality self-assessment (scores & notes).
- `scripts/check-updates.py` — PyPI version check, integrity validation, staleness report.

### Stats

- Routing entries: 9
- Reference files: 9
- Approximate total lines: ~2,300
