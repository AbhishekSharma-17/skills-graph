---
name: dspy
description: "Programming (not prompting) framework for building and optimizing LLM pipelines with declarative Python modules, typed signatures, and automatic prompt/weight optimization. MANDATORY TRIGGERS: dspy, dspy.Predict, dspy.ChainOfThought, dspy.ReAct, dspy.Signature, dspy.Module, dspy.Optimize, BootstrapFewShot, MIPRO, MIPROv2, dspy.Evaluate, dspy.Retrieve, dspy compile, dspy optimizer. Also trigger when user wants to replace hand-written prompts with structured modules, automatically tune few-shot examples, build typed LLM pipelines with assertions, optimize a pipeline against a metric, compile a DSPy program, or build multi-hop RAG with declarative modules. When in doubt about whether to use this skill for any DSPy or LLM-pipeline-compiling task, use it."
license: MIT
metadata:
  version: "1.0.0"
  author: Abhishek Sharma
  tags: ["dspy", "llm", "prompt-optimization", "agents", "rag", "stanford", "chain-of-thought", "react", "bootstrap", "mipro"]
---

# DSPy — Skill Router

> Program — don't prompt — foundation models. DSPy lets you define LLM pipelines as typed Python modules with declarative `Signatures`, then *compile* (optimize) them against a metric using optimizers like `BootstrapFewShot` and `MIPROv2`.

**Source:** [dspy.ai](https://dspy.ai) | **Python:** v2.5.x | **License:** MIT | **GitHub:** [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy)

## Reference Files

| Reference | File | Read When |
|-----------|------|-----------|
| **Overview & Quickstart** | `references/00-overview.md` | First install, core concepts, `dspy.configure`, the compile loop |
| **Signatures** | `references/01-signatures.md` | Inline `"q -> a"` strings, class-based signatures, `InputField`/`OutputField`, typed fields |
| **Modules (Predict, CoT, ReAct, PoT)** | `references/02-modules.md` | `dspy.Predict`, `ChainOfThought`, `ReAct`, `ProgramOfThought`, composing `dspy.Module` |
| **LM Configuration** | `references/03-lm-configuration.md` | `dspy.LM`, providers (OpenAI, Anthropic, Ollama, vLLM), caching, temperature, context settings |
| **Optimizers (Compilers)** | `references/04-optimizers.md` | `BootstrapFewShot`, `BootstrapFewShotWithRandomSearch`, `MIPROv2`, `COPRO`, `BootstrapFinetune` |
| **Metrics & Evaluation** | `references/05-metrics-evaluation.md` | Writing metric functions, `dspy.Evaluate`, answer-exact-match, LLM-as-judge metrics |
| **Retrieval & RAG** | `references/06-rag-retrieval.md` | `dspy.Retrieve`, ColBERTv2, Qdrant/Chroma/Weaviate integrations, multi-hop RAG patterns |
| **Assertions & Suggestions** | `references/07-assertions.md` | `dspy.Assert`, `dspy.Suggest`, self-refinement loops, constraint-driven retries |
| **Deployment & Production** | `references/08-deployment.md` | Saving/loading compiled programs, streaming, async, FastAPI serving, observability |

## Installation

```bash
# SDK
pip install dspy

# With optional integrations
pip install 'dspy[anthropic]'
pip install 'dspy[qdrant]'
pip install 'dspy[chromadb]'
```

## Quick Reference

- **Docs:** https://dspy.ai
- **GitHub:** https://github.com/stanfordnlp/dspy
- **PyPI:** https://pypi.org/project/dspy/
- **Tutorials:** https://dspy.ai/tutorials/
- **API Reference:** https://dspy.ai/api/
