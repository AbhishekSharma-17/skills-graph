# DeepEval Overview

> Source: https://deepeval.com/docs/introduction | https://github.com/confident-ai/deepeval

## What Is DeepEval

DeepEval is an open-source LLM evaluation framework for testing and benchmarking LLM applications. It provides 50+ plug-and-play metrics for evaluating AI agents, RAG pipelines, chatbots, and multimodal systems. Think of it as pytest for LLM outputs — you write test cases, attach metrics, and get scored results with pass/fail thresholds.

DeepEval is used by 150K+ developers with over 100 million daily evaluations. It integrates with pytest for CI/CD pipelines and optionally connects to Confident AI for cloud-based reporting and production monitoring.

## When to Use DeepEval

- **Testing LLM applications** — Unit test LLM outputs before deployment
- **RAG evaluation** — Measure retrieval quality and generation faithfulness
- **Agent evaluation** — Assess tool usage, task completion, and step efficiency
- **Chatbot benchmarking** — Evaluate multi-turn conversation quality
- **Safety auditing** — Detect bias, toxicity, PII leakage in outputs
- **CI/CD integration** — Automate LLM quality gates in pipelines
- **Production monitoring** — Online evaluation of live traces

## Architecture

DeepEval follows a test case → metric → evaluation pipeline:

```
Golden (input template)
  → Test Case (input + actual_output from your LLM)
    → Metric(s) score the test case (0-1)
      → Pass/fail based on threshold
```

**Core components:**

| Component | Purpose |
|-----------|---------|
| `LLMTestCase` | Single interaction with your LLM (input → output) |
| `ConversationalTestCase` | Multi-turn dialogue sequence |
| `Metric` | Scoring function (LLM-as-judge or algorithmic) |
| `EvaluationDataset` | Collection of Goldens for batch evaluation |
| `@observe` | Decorator for tracing and component-level eval |
| `Synthesizer` | Generates synthetic test data from docs or scratch |

## Installation

```bash
pip install -U deepeval
```

For the terminal inspection UI:

```bash
pip install -U "deepeval[inspect]"
```

### Environment Setup

DeepEval autoloads `.env` files with this precedence: process variables → `.env.local` → `.env`. Most metrics use LLM-as-a-judge evaluation requiring an API key:

```bash
export OPENAI_API_KEY="sk-..."
```

For Confident AI cloud reporting (optional):

```bash
deepeval login
# Or in CI environments:
deepeval login --api-key <your-key>
```

Disable dotenv autoloading:

```bash
export DEEPEVAL_DISABLE_DOTENV=1
```

## Quick Start

Create `test_example.py`:

```python
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, SingleTurnParams
from deepeval.metrics import GEval

def test_correctness():
    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine if the 'actual output' is correct based on the 'expected output'.",
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        threshold=0.5
    )
    test_case = LLMTestCase(
        input="What is your return policy?",
        actual_output="We offer a 30-day full refund at no extra cost.",
        expected_output="All customers are eligible for a 30-day full refund at no extra cost."
    )
    assert_test(test_case, [correctness_metric])
```

Run:

```bash
deepeval test run test_example.py
```

## Evaluation Approaches

DeepEval supports three evaluation modes:

### End-to-End (Black Box)

Treats your LLM system as a black box — evaluates observable inputs and outputs:

```python
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric

test_case = LLMTestCase(
    input="How do I reset my password?",
    actual_output=my_llm_app("How do I reset my password?")
)
evaluate(test_cases=[test_case], metrics=[AnswerRelevancyMetric()])
```

### Component-Level (With Tracing)

Evaluates individual components (retriever, generator, tools) by attaching metrics to traced spans:

```python
from deepeval.tracing import observe, update_current_span
from deepeval.metrics import ContextualRelevancyMetric

@observe(metrics=[ContextualRelevancyMetric()])
def retriever(query: str) -> list[str]:
    chunks = vector_store.search(query)
    update_current_span(
        test_case=LLMTestCase(input=query, retrieval_context=chunks)
    )
    return chunks
```

### One-Off (Debugging)

Execute a single metric for quick iteration:

```python
metric = AnswerRelevancyMetric(threshold=0.5)
metric.measure(test_case)
print(f"Score: {metric.score}, Reason: {metric.reason}")
```

## Metric Categories

| Category | Metrics | Use Case |
|----------|---------|----------|
| Custom | GEval, DAG, ConversationalGEval, ArenaGEval | Any criteria |
| RAG | AnswerRelevancy, Faithfulness, ContextualPrecision/Recall/Relevancy | RAG pipelines |
| Agent | TaskCompletion, ToolCorrectness, StepEfficiency, PlanAdherence | AI agents |
| Chatbot | KnowledgeRetention, RoleAdherence, ConversationCompleteness | Multi-turn bots |
| Safety | Bias, Toxicity, PIILeakage, Misuse, RoleViolation, NonAdvice | Safety auditing |
| Image | ImageCoherence, ImageHelpfulness, TextToImage, ImageEditing | Multimodal |
| Other | Hallucination, JsonCorrectness, Summarization | General purpose |

## Framework Integrations

DeepEval provides drop-in integrations for 12+ frameworks:

| Framework | Integration Method |
|-----------|-------------------|
| LangChain / LangGraph | `CallbackHandler()` |
| OpenAI | `from deepeval.openai import OpenAI` |
| Anthropic | `from deepeval.anthropic import Anthropic` |
| Pydantic AI | `DeepEvalInstrumentationSettings()` |
| LlamaIndex | Event handler registration |
| CrewAI | Agent shim |
| Google ADK | Instrumentation function |
| OpenAI Agents | Instrumentation function |

## Key Terminology

| Term | Definition |
|------|------------|
| **Golden** | Test template with input and optional expected output |
| **Test Case** | Golden + actual LLM output, ready for scoring |
| **Trace** | Full execution path of an LLM application call |
| **Span** | Individual component within a trace |
| **LLM-as-Judge** | Using an LLM to evaluate another LLM's output |
| **Threshold** | Score cutoff (0-1) for pass/fail determination |
| **Confident AI** | Optional cloud platform for reports and monitoring |
