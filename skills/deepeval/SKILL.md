---
name: deepeval
description: "Open-source LLM evaluation framework with 50+ metrics for testing AI agents, RAG pipelines, chatbots, and multimodal systems. MANDATORY TRIGGERS: deepeval, LLM evaluation, LLM testing, LLM metrics, AI eval, confident-ai, GEval, assert_test, LLMTestCase, faithfulness metric, answer relevancy. Also trigger when the user wants to evaluate LLM outputs, test AI agent quality, measure RAG accuracy, benchmark chatbot performance, or set up CI/CD for LLM applications. When in doubt about whether to use this skill for LLM evaluation tasks, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["python", "llm", "evaluation", "testing", "ai", "metrics", "rag", "agents"]
---

# DeepEval

> v3.9.9 | https://deepeval.com/docs | https://github.com/confident-ai/deepeval

## Reference Files

| File | Read When |
|------|-----------|
| [00-overview.md](references/00-overview.md) | Starting with DeepEval, understanding architecture, installation |
| [01-test-cases.md](references/01-test-cases.md) | Creating LLMTestCase, ConversationalTestCase, multimodal test cases |
| [02-metrics-overview.md](references/02-metrics-overview.md) | Choosing metrics, metric categories, threshold configuration |
| [03-custom-metrics.md](references/03-custom-metrics.md) | GEval, DAG, custom BaseMetric, ConversationalGEval, scoring |
| [04-rag-metrics.md](references/04-rag-metrics.md) | AnswerRelevancy, Faithfulness, ContextualPrecision/Recall/Relevancy |
| [05-agent-metrics.md](references/05-agent-metrics.md) | TaskCompletion, ToolCorrectness, StepEfficiency, PlanAdherence |
| [06-safety-metrics.md](references/06-safety-metrics.md) | Bias, Toxicity, PIILeakage, Misuse, RoleViolation, NonAdvice |
| [07-datasets.md](references/07-datasets.md) | Golden, EvaluationDataset, loading CSV/JSON, synthetic data |
| [08-tracing.md](references/08-tracing.md) | @observe decorator, spans, traces, component-level evaluation |
| [09-evaluation-modes.md](references/09-evaluation-modes.md) | End-to-end vs component-level, evaluate(), assert_test() |
| [10-ci-cd.md](references/10-ci-cd.md) | Pytest integration, GitHub Actions, deepeval test run, caching |
| [11-synthesizer.md](references/11-synthesizer.md) | Synthetic data generation, ConversationSimulator, generate CLI |
| [12-configuration.md](references/12-configuration.md) | CLI commands, model providers, environment variables, Confident AI |

## Installation

```bash
pip install -U deepeval
# With inspection TUI:
pip install -U "deepeval[inspect]"
# Authenticate (optional):
deepeval login
```

## Quick Reference

- [Official Docs](https://deepeval.com/docs)
- [GitHub Repository](https://github.com/confident-ai/deepeval)
- [PyPI Package](https://pypi.org/project/deepeval/)
- [Confident AI Platform](https://www.confident-ai.com)
