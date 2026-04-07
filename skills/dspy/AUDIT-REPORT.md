# DSPy Skill — Audit Report

**Date:** 2026-04-07
**Skill version:** 1.0.0
**Source tracked:** dspy 2.5.43

## Scores (1–5)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Architecture | 5 | Pure router SKILL.md (<60 lines), 9 flat leaf references, no nested router needed at this scope. |
| Content Quality | 4 | Practical, runnable examples per reference; covers signatures, modules, optimizers, RAG, assertions, and deployment; includes pitfalls in every file. |
| Completeness | 4 | Covers the primary user-facing surface (signatures, modules, LM config, optimizers, metrics, RAG, assertions, deployment). Deep internals (custom optimizer authoring, the typed predictors beta API, advanced finetuning recipes) intentionally omitted to keep files focused. |
| Maintainability | 5 | VERSION.json maps every reference to its upstream source page; check-updates.py validates integrity and upstream version against PyPI. |
| Trigger Quality | 5 | MANDATORY TRIGGERS list covers product name, sub-products (Predict, ChainOfThought, ReAct), optimizer names (BootstrapFewShot, MIPRO, MIPROv2), and broader intents (compile, optimise pipeline, tune few-shot). |

**Overall:** 4.6 / 5

## Strengths

- Single-source-of-truth router with clear "Read When" triggers per file.
- Each reference file is self-contained and ~230–330 lines — easy to read, quick to load selectively.
- Every file ends with a "Common pitfalls" section capturing real gotchas (`.with_inputs` missing, metric returning 0, compiling MIPROv2 on tiny data, etc.).
- Covers the DSPy mental model (Signatures → Modules → Optimizers) as a single coherent graph.
- Deployment reference ties the pipeline back to practical FastAPI / Langfuse / OTEL / Docker patterns.

## Known gaps (acceptable for v1.0.0)

- No dedicated reference for DSPy's typed-predictors beta API (still stabilising upstream).
- Writing custom optimizers not covered; readers are expected to use the built-ins.
- BootstrapFinetune's provider-specific recipes (OpenAI vs local HF) covered only at a high level.
- DSPy's experimental multi-turn / chat-history modules intentionally omitted until stable.

## Maintenance

- `scripts/check-updates.py --version` compares `source_version_tracked` against the latest PyPI release of `dspy`.
- `scripts/check-updates.py --integrity` verifies every file in the SKILL.md routing table exists on disk.
- `scripts/check-updates.py --stale 90` flags references not updated in 90+ days.

## Next planned updates

- Track upstream 2.6.x release and refresh optimizer docs if `MIPROv2` gains new presets.
- Add a `09-typed-predictors.md` leaf once the typed predictors API leaves beta.
- Expand RAG reference with a dedicated reranker subsection if DSPy ships a first-class reranker class.
