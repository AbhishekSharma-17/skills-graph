# DeepEval Skill Changelog

## [1.0.0] — 2026-07-24

Source version tracked: deepeval 3.9.9

### Added

- **00-overview.md** — Architecture, installation, quick start, evaluation approaches, framework integrations
- **01-test-cases.md** — LLMTestCase, ConversationalTestCase, ToolCall, MLLMImage, parameter reference
- **02-metrics-overview.md** — 50+ metrics across 7 categories, metric selection strategy, execution patterns
- **03-custom-metrics.md** — GEval, ConversationalGEval, DAG, BaseMetric subclasses, composite metrics
- **04-rag-metrics.md** — AnswerRelevancy, Faithfulness, ContextualPrecision/Recall/Relevancy, component-level RAG eval
- **05-agent-metrics.md** — TaskCompletion, ToolCorrectness, StepEfficiency, PlanAdherence, sub-agent evaluation
- **06-safety-metrics.md** — Bias, Toxicity, NonAdvice, Misuse, PIILeakage, RoleViolation
- **07-datasets.md** — Golden, EvaluationDataset, loading from CSV/JSON/JSONL, Confident AI push/pull
- **08-tracing.md** — @observe decorator, span types, update_current_trace/span, framework integrations
- **09-evaluation-modes.md** — End-to-end vs component-level, evaluate() vs assert_test(), mixed evaluation
- **10-ci-cd.md** — Pytest integration, GitHub Actions workflow, deepeval test run flags, caching
- **11-synthesizer.md** — Synthesizer class, ConversationSimulator, deepeval generate CLI, vibe coding loop
- **12-configuration.md** — CLI commands, model provider setup, environment variables, Confident AI

### Stats

- Routing entries: 13
- Reference files: 13
- Total lines: ~4,300
